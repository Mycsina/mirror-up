"""CLI configuration"""

from concurrent.futures import ThreadPoolExecutor
from os import PathLike, getenv
from pathlib import Path
from typing import List, Optional

import pyperclip
import trio
import typer
from dotenv import load_dotenv
from httpx import Response
from notifypy import Notify

from mirror_up.mirror_ace import MirrorAceConnection

load_dotenv()

app = typer.Typer(help="Use MirrorAce commands")


@app.command(help="Upload files/folders to MirrorAce.")
def upload(
    path: List[Path] = typer.Argument(..., help="Path to files/folders."),
    notify: Optional[bool] = typer.Option(False, help="Specify if you want to be notified when it concludes."),
    password: Optional[str] = typer.Option(None, help="Provide a password for the download."),
    clipboard: Optional[bool] = typer.Option(True, help="Specify if you want to save the result to the clipboard."),
) -> None:
    with ThreadPoolExecutor() as executor:
        for filepath in path:
            if filepath.exists():
                executor.submit(upload_logic, filepath, notify, password, clipboard)
            else:
                typer.echo(f"This path does not exist: {filepath}")


def upload_logic(filepath: PathLike, notify: bool, password: str, clipboard: bool):
    obj = MirrorAceConnection(getenv("API_KEY"), getenv("API_TOKEN"))
    if password is not None:
        req = trio.run(obj, filepath, password)
    else:
        req = trio.run(obj, filepath)
    if isinstance(req, Response):
        typer.echo(req.json()["result"]["url"])
        if notify:
            notification = Notify()
            notification.title = f'{req.json()["result"]["name"]} has been uploaded.'
            notification.message = f"The link has been copied to your clipboard"
            notification.send()
        if clipboard:
            pyperclip.copy(req.json()["result"]["url"])
    if isinstance(req, list):
        typer.echo("File was too large for direct upload; it as been split into multiple files.")
        with open("results.txt", "a+") as f:
            for line in req:
                typer.echo(f"{line.json()['result']['name']} : {line.json()['result']['url']}")
                f.write(f"{line.json()['result']['name']} : {line.json()['result']['url']}\n")


@app.command(help="Upload all files/folders within the given folders to MirrorAce.")
def folder(
    path: List[Path] = typer.Argument(..., help="Path to folder containing files"),
    password: Optional[str] = typer.Option(None, help="Provide a password for the download"),
) -> None:  # noqa
    with ThreadPoolExecutor() as executor:
        for filepath in path:
            if filepath.exists():
                for entry in Path(filepath).iterdir():
                    executor.submit(upload_logic, entry, password)
            else:
                typer.echo(f"This path does not exist: {filepath}")


# #Remote file upload currently not working
# @app.command(help="Upload remote files to MirrorAce")
# def remote(
#     url: List[str] = typer.Argument(..., help="URLs to upload"),
#     password: Optional[str] = typer.Option(None, help="Provide a password for the download"),
# ) -> None:
#     for link in url:
#         obj = MirrorAceConnection(getenv("API_KEY"), getenv("API_TOKEN"))
#         if password is not None:
#             req = trio.run(obj.upload_remote, link, password)
#         else:
#             req = trio.run(obj.upload_remote, link)
#         if isinstance(req, httpx.Response):
#             print(req.json())
#             typer.echo(req.json()["result"]["url"])


@app.command(help="Get info on files uploaded to MirrorAce")
def info(slugs: List[str]) -> None:
    """
    Get file information from MirrorAce slugs

    Args:
        slugs: List[str]
    """
    obj = MirrorAceConnection(getenv("API_KEY"), getenv("API_TOKEN"))
    req = trio.run(obj.get_file_info, slugs)
    typer.echo(req)
