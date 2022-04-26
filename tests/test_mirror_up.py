#!/usr/bin/env python
"""Tests for `mirror_up` package."""
# pylint: disable=redefined-outer-name

from os import getenv, remove
from pathlib import Path

import trio
from dotenv import load_dotenv

from mirror_up.mirror_ace import MirrorAceConnection

load_dotenv()


def test_mirrorace_keys() -> None:  # noqa: D103
    connection = MirrorAceConnection(getenv("API_KEY"), getenv("API_TOKEN"))
    assert isinstance(connection.params["server"], str)
    assert isinstance(connection.params["server_file"], str)
    assert isinstance(connection.params["server_remote"], str)
    assert isinstance(connection.params["cTracker"], str)
    assert isinstance(connection.params["mirrors[]"], list)
    assert isinstance(connection.params["max_chunk_size"], str)
    assert isinstance(connection.params["max_file_size"], str)
    assert isinstance(connection.params["max_mirrors"], str)
    assert isinstance(connection.params["upload_key"], str)
    assert isinstance(connection.params["upload_key_expiry"], str)


# # Remote file upload currently not working.
# def test_mirrorace_file_remote():
#     connection = mirror_ace.MirrorAceConnection(getenv("API_KEY"), getenv("API_TOKEN"))
#     req = trio.run(connection.upload_remote, "http://google.com/favicon.ico")
#     assert connection._check_success(req.json())
#     assert isinstance(req.json()["result"]["url"], str)


def test_mirrorace_file_info() -> None:  # noqa: D103
    connection = MirrorAceConnection(getenv("API_KEY"), getenv("API_TOKEN"))
    # Create small file
    with open("test.tmp", "w") as f:
        f.truncate(10**5)
    req = trio.run(connection, Path("test.tmp"))
    remove("test.tmp")
    assert connection._check_success(req)
    # Get slug from update url
    slug = req.json()["result"]["slug"]
    # Renew connection
    connection = connection.clone()
    req = trio.run(connection.get_file_info, [slug, "0101"])
    assert isinstance(req.json()["result"][slug]["id"], str)
    assert isinstance(req.json()["result"][slug]["name"], str)
    assert isinstance(req.json()["result"][slug]["slug"], str)
    assert req.json()["result"][slug]["slug"] == slug
    assert isinstance(req.json()["result"][slug]["size"], str)
    assert isinstance(req.json()["result"][slug]["url"], str)
    assert isinstance(req.json()["result"][slug]["status"], str)
    assert not isinstance(req.json()["result"]["0101"]["id"], str)
    assert not isinstance(req.json()["result"]["0101"]["name"], str)
    assert not isinstance(req.json()["result"]["0101"]["slug"], str)
    assert not isinstance(req.json()["result"]["0101"]["size"], str)
    assert not isinstance(req.json()["result"]["0101"]["url"], str)
    assert not isinstance(req.json()["result"]["0101"]["status"], str)


def test_mirrorace_part_upload() -> None:  # noqa: D103
    file = "testP.tmp"
    connection = MirrorAceConnection(getenv("API_KEY"), getenv("API_TOKEN"))
    # Create chonky file for testing
    with open(file, "w") as f:
        f.truncate(int(1.05 * int(connection.params["max_file_size"])))
    req = trio.run(connection, Path(file))
    remove(file)
    assert connection._check_success(req)


def test_mirrorace_chunk_upload() -> None:  # noqa: D103
    file = "testC.tmp"
    connection = MirrorAceConnection(getenv("API_KEY"), getenv("API_TOKEN"))
    # Create chonky file for testing
    with open(file, "w") as f:
        f.truncate(int(1.05 * int(connection.params["max_chunk_size"])))
    req = trio.run(connection, Path(file))
    remove(file)
    assert connection._check_success(req)


def test_mirrorace_simple_upload() -> None:  # noqa: D103
    file = "testS.tmp"
    connection = MirrorAceConnection(getenv("API_KEY"), getenv("API_TOKEN"))
    # Create small file for testing
    with open(file, "w") as f:
        f.truncate(10**5)
    req = trio.run(connection, Path(file))
    remove(file)
    assert connection._check_success(req)


# TODO Finish writing tests
