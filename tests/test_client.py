import sys
import asyncio
import argparse

import pytest

import chunk_nordic.client as client
import chunk_nordic.constants as constants

class MockCmdline:
    def __init__(self, *args):
        self._cmdline = args

    def __enter__(self):
        self._old_cmdline = sys.argv
        sys.argv = list(self._cmdline)

    def __exit__(self, exc_type, exc_value, traceback):
        sys.argv = self._old_cmdline

def test_parse_args():
    with MockCmdline("chunk-client", "-v", "info", "http://localhost"):
        args = client.parse_args()
    assert args.server_url == 'http://localhost'
    assert not args.disable_uvloop
    assert args.verbosity == constants.LogLevel.info

def test_bad_args():
    with MockCmdline("chunk-client", "-v", "xxx", "localhost"):
        with pytest.raises(SystemExit):
            args = client.parse_args()
