import shutil
from io import BytesIO
from os import PathLike, getenv
from pathlib import Path
from typing import BinaryIO

import multivolumefile
from dotenv.main import load_dotenv

load_dotenv()


def split_directory(directory: PathLike, volume_size: int) -> None:
    if Path(f"{getenv('ZIP_SAVE') + Path(directory).stem}/").is_dir():
        with multivolumefile.open(f"{getenv('ZIP_SAVE') + Path(directory).stem}/{Path(directory).stem}", mode='wb', volume=volume_size) as target_archive: # noqa
            with open(f"{Path(directory)}", "rb") as f:
                for entry in read_in_chunks(10000000, f):
                    target_archive.write(entry)
    else:
        Path(f"{getenv('ZIP_SAVE') + Path(directory).stem}/").mkdir(exist_ok=True)
        split_directory(directory, volume_size)


def archive_directory(directory: PathLike) -> None:
    shutil.make_archive(f"{getenv('ZIP_SAVE') + Path(directory).name}", 'tar', directory)


def read_in_chunks(chunk_size: int, file_object: BinaryIO) -> BytesIO:
    while True:
        data = file_object.read(chunk_size)
        if not data:
            break
        yield data

# TODO Documentation
