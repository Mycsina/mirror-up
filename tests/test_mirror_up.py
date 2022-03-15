#!/usr/bin/env python
"""Tests for `mirror_up` package."""
# pylint: disable=redefined-outer-name

from os import getenv
from pathlib import Path
from re import search

import hypothesis
import trio
from dotenv import load_dotenv
from mirror_up import mirror_up

load_dotenv()


def test_mirrorace_keys():
    connection = mirror_up.MirrorAceConnection(getenv("API_KEY"), getenv("API_TOKEN"))
    assert isinstance(connection.params["server"], str)
    assert isinstance(connection.params["server_file"], str)
    assert isinstance(connection.params["server_remote"], str)
    assert isinstance(connection.params["cTracker"], str)
    assert isinstance(connection.params["mirrors"], dict)
    assert isinstance(connection.params["default_mirrors"], list)
    assert isinstance(connection.params["max_chunk_size"], str)
    assert isinstance(connection.params["max_file_size"], str)
    assert isinstance(connection.params["max_mirrors"], str)
    assert isinstance(connection.params["upload_key"], str)
    assert isinstance(connection.params["upload_key_expiry"], str)


def test_mirrorace_file_remote():
    connection = mirror_up.MirrorAceConnection(getenv("API_KEY"), getenv("API_TOKEN"))
    req = trio.run(connection.upload_remote, "https://source.unsplash.com/random")
    assert connection.check_success(req.json())
    assert isinstance(req.json()["result"]["url"], str)


def test_mirrorace_file_info():
    connection = mirror_up.MirrorAceConnection(getenv("API_KEY"), getenv("API_TOKEN"))
    req = trio.run(connection.upload_remote, "https://source.unsplash.com/random")
    assert connection.check_success(req.json())
    slug = search(r"\/m\/(.*)", req.json()["result"]["url"])[0]
    connection.get_file_info([slug, "0101"])
    assert isinstance(req.json()["result"]["id"], str)
    assert isinstance(req.json()["result"]["name"], str)
    assert isinstance(req.json()["result"]["slug"], str)
    assert isinstance(req.json()["result"]["size"], str)
    assert isinstance(req.json()["result"]["url"], str)


def test_mirrorace_file_upload():
    connection = mirror_up.MirrorAceConnection(getenv("API_KEY"), getenv("API_TOKEN"))
    req = trio.run(connection, Path("test.tmp"))
    pass


# TODO Finish writing tests
