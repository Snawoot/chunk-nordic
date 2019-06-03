import asyncio
import argparse

import pytest

import chunk_nordic.utils as utils
import chunk_nordic.constants as constants

@pytest.mark.asyncio
async def test_heartbeat():
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(utils.heartbeat(), 1.5)

def test_setup_logger_stderr(capsys):
    logger = utils.setup_logger("test", constants.LogLevel.info)
    logger.info("Hello World!")
    captured = capsys.readouterr()
    assert "Hello World!" in captured.err


@pytest.mark.parametrize("value", [ "1", ".5", "1.", "1000" ])
def test_check_positive_float(value):
    assert utils.check_positive_float(value) == float(value)

@pytest.mark.parametrize("value", [ "-1", ".0", "0.", "aaaa" ])
def test_check_positive_float_negative(value):
    with pytest.raises(argparse.ArgumentTypeError):
        utils.check_positive_float(value)

@pytest.mark.parametrize("value", [ "1", "10", "100", "1000", "10000" ])
def test_check_port(value):
    assert utils.check_port(value) == int(value)

@pytest.mark.parametrize("value", [ "-1", "0", "100000", "aaaaa"])
def test_check_port_negative(value):
    with pytest.raises(argparse.ArgumentTypeError):
        utils.check_port(value)
