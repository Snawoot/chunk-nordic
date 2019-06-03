import asyncio
import os

import pytest
from async_generator import yield_, async_generator

from chunk_nordic.splitter import Splitter
from chunk_nordic.combiner import Combiner
from chunk_nordic.utils import enable_uvloop

@pytest.fixture(scope="session")
def event_loop():
    uvloop_test = os.environ['TOXENV'].endswith('-uvloop')
    uvloop_enabled = enable_uvloop()
    assert uvloop_test == uvloop_enabled
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
@async_generator
async def plaintext_splitter(event_loop):
    server = Splitter(address="127.0.0.1",
                      port=1940,
                      ssl_context=None,
                      url="http://127.0.0.1:8080/chunk-nordic",
                      loop=event_loop)
    await server.start()
    try:
        await yield_(server)
    finally:
        await server.stop()

@pytest.fixture(scope="session")
@async_generator
async def plaintext_combiner(event_loop):
    server = Combiner(address="127.0.0.1",
                      port=8080,
                      ssl_context=None,
                      uri="/chunk-nordic",
                      dst_host="127.0.0.1",
                      dst_port=7,
                      loop=event_loop)
    await server.start()
    try:
        await yield_(server)
    finally:
        await server.stop()
