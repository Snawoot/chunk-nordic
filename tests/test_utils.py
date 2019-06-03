import asyncio

import pytest

import chunk_nordic.utils as utils

@pytest.mark.asyncio
async def test_heartbeat():
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(utils.heartbeat(), 1.5)

