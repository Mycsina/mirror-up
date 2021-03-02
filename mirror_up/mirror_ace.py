# coding=utf-8
"""Main module."""
import logging
import math
import mimetypes
from os import PathLike, getenv, path
from pathlib import Path
from typing import Dict, List, Optional, Union

import httpx
import trio
import typer
from alive_progress import alive_bar
from dotenv import load_dotenv
from format_byte import format_byte
from httpx._utils import peek_filelike_length

if __name__ == "__main__":
    from _utils import (archive_directory, read_in_chunks,  # type: ignore
                        split_directory)
else:
    from ._utils import archive_directory, read_in_chunks, split_directory

time_format = r"%d-%m-%Y %H:%M:%S"
# Enable if you want to try to automatize this and wish to save logs
logging.basicConfig(
    # filename=f"/logs/main-{datetime.now().strftime(time_format)}",
    format="%(message)s",
    # datefmt=time_format,
    level=logging.DEBUG,
)
load_dotenv()

app = typer.Typer(help="Use MirrorAce commands")


class MirrorAceConnection:
    def __init__(self, api_key: str, api_token: str) -> None:
        params = {"api_key": api_key, "api_token": api_token}  # noqa: F841
        # Way to avoid typing each assignment manually
        self.__dict__.update({k: v for k, v in locals().items() if k != "self"})
        # Make client persistent throughout the instance
        self.Client = httpx.AsyncClient(verify=True)
        trio.run(self.get_upload)

    async def __call__(self, file_path: PathLike, password: Optional[str] = None) -> None:
        async def upload_chunks():
            chunk_size = int(self.params["max_chunk_size"])
            file_size = peek_filelike_length(f)
            chunks = math.ceil(file_size / chunk_size)
            last_range = False
            i = 0
            with alive_bar(chunks, bar="smooth", spinner="dots_waves") as bar:
                while i < chunks:
                    range_start = 0
                    range_end = min(chunk_size, file_size - 1)
                    if last_range is not False:
                        range_start = last_range + 1
                        range_end = min(range_start + chunk_size, file_size - 1)
                    last_range = range_end
                    chunk = next(read_in_chunks(int(self.params["max_chunk_size"]), f))
                    files = {"files": (file_name, chunk)}
                    headers = {
                        "Content-Range": "bytes" + str(range_start) + "-" + str(range_end) + "/" + str(file_size)
                    }
                    if password is not None:
                        req = await self.Client.post(
                            self.params["server_file"],
                            files=files,
                            data=self.params.update({"file_password": password}),
                            headers=headers,
                            timeout=1800,
                        )
                    else:
                        req = await self.Client.post(
                            self.params["server_file"], files=files, data=self.params, headers=headers, timeout=1800
                        )
                    i += 1
                    bar()
            return req

        if path.isfile(file_path):
            with open(file_path, "rb") as f:
                content_size = peek_filelike_length(f)
                file_name = Path(file_path).name
                logging.info(f"[I] File being uploaded: {file_name}")
                logging.debug(f"[D] File size: {format_byte(content_size)}")
                if content_size > int(self.params["max_file_size"]):
                    logging.info(f"[I] Splitting {file_name} into multi-volume archive")
                    split_directory(Path(file_path), int(self.params["max_file_size"]))  # noqa
                    url_list = []
                    for entry in Path(f"{getenv('ZIP_SAVE') + Path(file_path).stem}").iterdir():  # noqa
                        with open(entry, "rb") as f:
                            req = await upload_chunks()
                        url_list.append(req.json()["result"]["url"] + "\n")
                        await self.get_upload()
                        if self._check_success(req.json()):
                            logging.info(f"[I] {file_name} has been uploaded")
                            logging.info(f"[I] File has been uploaded to: {req.json()['result']['url']}")
                        else:
                            print("Error: ", req)
                    await self.Client.aclose()
                    return req
                if content_size < int(self.params["max_chunk_size"]):
                    payload = {"files": (file_name, f, mimetypes.guess_type(file_path)[0])}
                    if password is not None:
                        req = await self.Client.post(
                            self.params["server_file"],
                            files=payload,
                            data=self.params.update({"file_password": password}),
                        )
                    else:
                        req = await self.Client.post(self.params["server_file"], files=payload, data=self.params)
                    await self.Client.aclose()
                    if self._check_success(req.json()):
                        logging.info(f"[I] {file_name} has been uploaded")
                        logging.info(f"[I] File has been uploaded to: {req.json()['result']['url']}")
                    else:
                        print("Error: ", req)
                    return req
                else:
                    req = await upload_chunks()
                    if self._check_success(req.json()):
                        logging.info(f"[I] {file_name} has been uploaded")
                        logging.info(f"[I] File has been uploaded to: {req.json()['result']['url']}")
                    await self.Client.aclose()

        if path.isdir(file_path):
            logging.info(f"[I] Archiving {Path(file_path).name}")
            archive_directory(file_path)
            req = await self.__call__(f"{getenv('ZIP_SAVE') + Path(file_path).name}.tar")
            await self.Client.aclose()
            return req

    def _check_success(self, response: dict) -> bool:
        if response["status"] == "success":
            logging.debug("[D] Successful response")
            return True
        else:
            return False

    async def get_upload(self) -> None:
        # Regular httpx async request
        upload_data = await self.Client.post("https://mirrorace.com/api/v1/file/upload", data=self.params)
        if self._check_success(upload_data.json()):
            # Add every entry in the json to the class __dict__
            self.params.update({key: value for key, value in upload_data.json()["result"].items()})
            self.params["mirrors[]"] = self.params["default_mirrors"]
            del self.params["default_mirrors"]
            del self.params["mirrors"]

    async def get_file_info(self, file_slugs: List[str]) -> Dict:
        # Turn all list entries into a str with comma separations
        slugs_str = ",".join(map(str, file_slugs))
        file_info = await self.Client.post(
            "https://mirrorace.com/api/v1/file/info", data=self.params.update({"files": slugs_str})
        )
        result = file_info.json()
        if self._check_success(result):
            return result["result"]

    async def upload_remote(self, url: str, password: Union[str, None] = None) -> None:
        self.params["url"] = url
        if password is not None:
            req = await self.Client.post(
                self.params["server_file"], data=self.params.update({"file_password": password}), timeout=900000
            )
        else:
            req = await self.Client.post(self.params["server_file"], data=self.params, timeout=900000)
        if self._check_success(req.json()):
            logging.info(f"[I] {url} has been uploaded")
            logging.info(f"[I] File has been uploaded to: {req.json()['result']['url']}")
        else:
            print("Error: ", req)
        await self.Client.aclose()
        return req


@app.command(help="Upload files/folders to MirrorAce.")
def upload(
    path: List[Path] = typer.Argument(..., help="Path to files/folders"),
    password: Optional[str] = typer.Option(None, help="Provide a password for the download"),
) -> None:
    for filepath in path:
        if filepath.exists():
            obj = MirrorAceConnection(getenv("API_KEY"), getenv("API_TOKEN"))
            if password is not None:
                req = trio.run(obj, filepath, password)
            else:
                req = trio.run(obj, filepath)
            if isinstance(req, httpx.Response):
                typer.echo(req.json()["result"]["url"])
            if isinstance(req, list):
                for line in req:
                    typer.echo(line)
        else:
            typer.echo(f"This path does not exist: {filepath}")


@app.command(help="Upload all files/folders within the given folders to MirrorAce.")
def folder(
    path: List[Path] = typer.Argument(..., help="Path to folder containing files"),
    password: Optional[str] = typer.Option(None, help="Provide a password for the download"),
) -> None:  # noqa
    for filepath in path:
        if filepath.exists():
            for entry in Path(filepath).iterdir():
                obj = MirrorAceConnection(getenv("API_KEY"), getenv("API_TOKEN"))
                if password is not None:
                    req = trio.run(obj, entry, password)
                else:
                    req = trio.run(obj, entry)
                if isinstance(req, httpx.Response):
                    typer.echo(req.json()["result"]["url"])
                if isinstance(req, list):
                    for line in req:
                        typer.echo(line)
        else:
            typer.echo(f"This path does not exist: {filepath}")


@app.command(help="Upload remote files to MirrorAce")
def remote(
    url: List[str] = typer.Argument(..., help="URLs to upload"),
    password: Optional[str] = typer.Option(None, help="Provide a password for the download"),
) -> None:
    for link in url:
        obj = MirrorAceConnection(getenv("API_KEY"), getenv("API_TOKEN"))
        if password is not None:
            req = trio.run(obj.upload_remote, link, password)
        else:
            req = trio.run(obj.upload_remote, link)
        if isinstance(req, httpx.Response):
            typer.echo(req.json()["result"]["url"])


@app.command(help="Get info on files uploaded to MirrorAce")
def info(slugs: List[str]) -> None:
    obj = MirrorAceConnection(getenv("API_KEY"), getenv("API_TOKEN"))
    req = trio.run(obj.get_file_info, slugs)
    typer.echo(req)

# TODO Documentation
