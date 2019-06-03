import sys
import asyncio
import argparse

import pytest

import chunk_nordic.server as server
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
    with MockCmdline("chunk-server", "-v", "info", "localhost", "1234"):
        args = server.parse_args()
    assert args.dst_host == 'localhost'
    assert args.dst_port == 1234
    assert not args.disable_uvloop
    assert args.verbosity == constants.LogLevel.info
    assert args.uri == '/chunk-nordic'

def test_bad_args():
    with MockCmdline("chunk-server", "-v", "xxx", "a", "1"):
        with pytest.raises(SystemExit):
            args = server.parse_args()
