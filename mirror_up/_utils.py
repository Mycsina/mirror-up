import shutil
from io import BytesIO
from os import PathLike, getenv
from pathlib import Path
from typing import BinaryIO

import multivolumefile
from dotenv.main import load_dotenv

load_dotenv()


def split_directory(directory: PathLike, volume_size: int) -> None:
    """
    Split a file into multivolume zip files.

    Args:
        directory: PathLike = Directory of the file
        volume_size: int = Size of each file
    """
    if Path(f"{getenv('ZIP_SAVE') + Path(directory).stem}/").is_dir():
        with multivolumefile.open(  # noqa: SIM117
            f"{getenv('ZIP_SAVE') + Path(directory).stem}/{Path(directory).stem}", mode="wb", volume=volume_size
        ) as target_archive:
            with open(f"{Path(directory)}", "rb") as f:
                for entry in read_in_chunks(10000000, f):
                    target_archive.write(entry)
    else:
        Path(f"{getenv('ZIP_SAVE') + Path(directory).stem}/").mkdir()
        split_directory(directory, volume_size)


def archive_directory(directory: PathLike) -> None:
    """Archive folder and save it on the folder specified in .env."""
    shutil.make_archive(f"{getenv('ZIP_SAVE') + Path(directory).name}", "tar", directory)


def read_in_chunks(chunk_size: int, file_object: BinaryIO) -> BytesIO:
    """Generator that yields a file chunk by chunk."""
    while True:
        data = file_object.read(chunk_size)
        if not data:
            break
        yield data
