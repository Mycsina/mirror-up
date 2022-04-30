#!/usr/bin/python
# coding=utf-8
"""MirrorAce's main module."""
import logging
import math
import mimetypes
from concurrent.futures import ThreadPoolExecutor
from os import PathLike, getenv, path
from pathlib import Path
from typing import Dict, List, Optional

import httpx
import trio

# from alive_progress import alive_bar
#           with alive_bar(chunks, bar="smooth", spinner="dots_waves") as bar:
#                    bar()
from dotenv import load_dotenv
from format_byte import format_byte
from httpx._utils import peek_filelike_length

from mirror_up._utils import archive_directory, read_in_chunks, split_directory

load_dotenv()


class MirrorAceConnection:
    """
    Methods to use on a MirrorAce connection

    Args:
        api_key : str = MirrorAce's API key
        api_token: str = MirrorAce's API token

    Attributes:
        api_key : str = MirrorAce's API key
        api_token: str = MirrorAce's API token
    """

    def __init__(self, api_key: str, api_token: str) -> None:  # noqa
        self.params: dict = {"api_key": api_key, "api_token": api_token}
        self.api_key = api_key
        self.api_token = api_token
        # Make client persistent throughout the instance
        self.Client = httpx.AsyncClient(verify=True)
        trio.run(self._get_upload)

    async def __call__(self, file_path: PathLike, password: Optional[str] = None) -> None:
        """
        General file/folder upload method.

        Depending on file size, it may upload the file directly, in multiple POST requests or splitting it into multivolume zip files.

        Args:
            file_path: PathLike = The file/folder's path
            password: Optional[str] = Upload's password, if desired.
        """

        async def _upload_chunks(file: PathLike) -> httpx.Response:
            """Use to upload file in chunks."""
            file_name = Path(file).name
            with open(file, "rb") as file:
                chunk_size = int(self.params["max_chunk_size"])
                file_size = peek_filelike_length(file)
                chunks = math.ceil(file_size / chunk_size)
                last_range = False
                i = 0
                while i < chunks:
                    range_start = 0
                    range_end = min(chunk_size, file_size - 1)
                    if last_range is not False:
                        range_start = last_range + 1
                        range_end = min(range_start + chunk_size, file_size - 1)
                    last_range = range_end
                    chunk = next(read_in_chunks(int(self.params["max_chunk_size"]), file))
                    files = {"files": (file_name, chunk)}
                    # Required headers
                    headers = {
                        "Content-Range": "bytes" + str(range_start) + "-" + str(range_end) + "/" + str(file_size)
                    }
                    if password is not None:
                        self.params.update({"file_password": password})
                    req = await self.Client.post(
                        self.params["server_file"], files=files, data=self.params, headers=headers, timeout=1800
                    )
                    i += 1
            return req

        async def part_upload(part: PathLike) -> None:
            file_name = Path(part).name
            req = await _upload_chunks(part)
            await self._get_upload()
            if self._check_success(req):
                logging.info(f"[I] {file_name} has been uploaded")
                logging.info(f"[I] File has been uploaded to: {req.json()['result']['url']}")
            else:
                logging.error("Error: ", req.json())
            return req

        if path.isfile(file_path):
            with open(file_path, "rb") as file:
                content_size = peek_filelike_length(file)
                file_name = Path(file_path).name
                logging.info(f"[I] File being uploaded: {file_name}")
                # File size formatted into readable format.
                logging.debug(f"[D] File size: {format_byte(content_size)}")
                if content_size > int(self.params["max_file_size"]):
                    if not Path(getenv("ZIP_SAVE")).is_dir():
                        logging.info(f"[D] Creating tar save folder")
                        Path(getenv("ZIP_SAVE")).mkdir()
                    logging.info(f"[D] Splitting {file_name} into multi-volume archive")
                    split_directory(Path(file_path), int(self.params["max_file_size"]))
                    with ThreadPoolExecutor() as executor:
                        futures = [
                            executor.submit(part_upload, path)
                            for path in Path(f"{getenv('ZIP_SAVE') + Path(file_path).stem}/").iterdir()
                        ]
                        result = [await future.result() for future in futures]
                    await self.Client.aclose()
                    return result
                if content_size < int(self.params["max_chunk_size"]):
                    payload = {"files": (file_name, file, mimetypes.guess_type(file_path)[0])}
                    if password is not None:
                        self.params.update({"file_password": password})
                    req = await self.Client.post(self.params["server_file"], files=payload, data=self.params)
                    if self._check_success(req):
                        logging.info(f"[I] {file_name} has been uploaded")
                        logging.info(f"[I] File has been uploaded to: {req.json()['result']['url']}")
                    else:
                        logging.error("Error: ", req)
                    await self.Client.aclose()
                    return req
                else:
                    req = await _upload_chunks(file)
                    if self._check_success(req):
                        logging.info(f"[I] {file_name} has been uploaded")
                        logging.info(f"[I] File has been uploaded to: {req.json()['result']['url']}")
                    await self.Client.aclose()
                    return req
        if path.isdir(file_path):
            if not Path(getenv("ZIP_SAVE")).is_dir():
                logging.info(f"[D] Creating tar save folder")
                Path(getenv("ZIP_SAVE")).mkdir()
            logging.info(f"[D] Archiving {Path(file_path).name}")
            archive_directory(file_path)
            req = await self.__call__(f"{getenv('ZIP_SAVE') + Path(file_path).name}.tar")
            await self.Client.aclose()
            return req

    def _check_success(self, response: httpx.Response) -> bool:
        if response.json()["status"] == "success":
            logging.debug("[D] Successful response")
            return True
        else:
            return False

    async def _get_upload(self) -> None:
        # Regular httpx async request
        upload_data = await self.Client.post("https://mirrorace.com/api/v1/file/upload", data=self.params)
        if self._check_success(upload_data):
            # Add every entry in the json to the class __dict__
            self.params.update({key: value for key, value in upload_data.json()["result"].items()})
            self.params["mirrors[]"] = self.params["default_mirrors"]
            del self.params["default_mirrors"]
            del self.params["mirrors"]

    async def get_file_info(self, file_slugs: List[str]) -> Dict:
        """
        Get the information of a file uploaded to MirrorAce.

        Args:
            file_slugs: List[str] = Slugs of the requested files
        """
        # Turn all list entries into a str with comma separations
        slugs_str = ",".join(map(str, file_slugs))
        self.params.update({"files": slugs_str})
        result = await self.Client.post("https://mirrorace.com/api/v1/file/info", data=self.params)
        if self._check_success(result):
            return result

    # TODO Currently not working
    # async def upload_remote(self, url: str, password: Union[str, None] = None) -> None:
    #     self.params["url"] = url
    #     if password is not None:
    #         req = await self.Client.post(
    #             self.params["server_file"], data=self.params.update({"file_password": password}), timeout=900000
    #         )
    #     else:
    #         req = await self.Client.post(self.params["server_file"], data=self.params, timeout=900000)
    #     if self._check_success(req):
    #         logging.info(f"[I] {url} has been uploaded")
    #         logging.info(f"[I] File has been uploaded to: {req.json()['result']['url']}")
    #     else:
    #         logging.error("Error: ", req)
    #     await self.Client.aclose()
    #     return req

    def clone(self) -> "MirrorAceConnection":
        """Recreate the connection. Use when it has been closed (after any upload operation)"""
        return MirrorAceConnection(self.api_key, self.api_token)
