import asyncio
import os
import ssl

import pytest

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
async def plaintext_splitter(event_loop, plaintext_combiner):
    server = Splitter(address="127.0.0.1",
                      port=1940,
                      ssl_context=None,
                      url="http://127.0.0.1:8080/chunk-nordic",
                      loop=event_loop)
    await server.start()
    try:
        yield server
    finally:
        await server.stop()

@pytest.fixture(scope="session")
async def plaintext_splitter_deadend(event_loop, plaintext_combiner_deadend):
    server = Splitter(address="127.0.0.1",
                      port=1942,
                      ssl_context=None,
                      url="http://127.0.0.1:8082/chunk-nordic",
                      loop=event_loop)
    await server.start()
    try:
        yield server
    finally:
        await server.stop()

@pytest.fixture(scope="session")
async def plaintext_splitter_close(event_loop, plaintext_combiner_close):
    server = Splitter(address="127.0.0.1",
                      port=1941,
                      ssl_context=None,
                      url="http://127.0.0.1:8081/chunk-nordic",
                      loop=event_loop)
    await server.start()
    try:
        yield server
    finally:
        await server.stop()

@pytest.fixture(scope="session")
async def plaintext_combiner(event_loop, echo_server):
    server = Combiner(address="127.0.0.1",
                      port=8080,
                      ssl_context=None,
                      uri="/chunk-nordic",
                      dst_host="127.0.0.1",
                      dst_port=7777,
                      loop=event_loop)
    await server.start()
    try:
        yield server
    finally:
        await server.stop()

@pytest.fixture(scope="session")
async def plaintext_combiner_deadend(event_loop):
    server = Combiner(address="127.0.0.1",
                      port=8082,
                      ssl_context=None,
                      uri="/chunk-nordic",
                      dst_host="127.0.0.1",
                      dst_port=8888,
                      loop=event_loop)
    await server.start()
    try:
        yield server
    finally:
        await server.stop()

@pytest.fixture(scope="session")
async def plaintext_combiner_close(event_loop, conn_closing_server):
    server = Combiner(address="127.0.0.1",
                      port=8081,
                      ssl_context=None,
                      uri="/chunk-nordic",
                      dst_host="127.0.0.1",
                      dst_port=1313,
                      loop=event_loop)
    await server.start()
    try:
        yield server
    finally:
        await server.stop()

@pytest.fixture(scope="session")
async def echo_server(event_loop):
    async def handle_echo(reader, writer):
        try:
            while True:
                data = await reader.read(4096)
                if not data:
                    break
                writer.write(data)
                await writer.drain()
        finally:
            writer.close()
    server = await asyncio.start_server(handle_echo, '127.0.0.1', 7777, loop=event_loop)
    try:
        yield server
    finally:
        server.close()

@pytest.fixture(scope="session")
async def conn_closing_server(event_loop):
    async def handle_echo(reader, writer):
        try:
            writer.write(b"MAGIC!")
            await writer.drain()
        finally:
            writer.close()
    server = await asyncio.start_server(handle_echo, '127.0.0.1', 1313, loop=event_loop)
    try:
        yield server
    finally:
        server.close()

@pytest.fixture(scope="session")
async def tls_combiner_close(event_loop, conn_closing_server):
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(certfile='/tmp/certs/localhost.pem',
                            keyfile='/tmp/certs/localhost.key')
    server = Combiner(address="127.0.0.1",
                      port=1443,
                      ssl_context=context,
                      uri="/chunk-nordic",
                      dst_host="127.0.0.1",
                      dst_port=1313,
                      loop=event_loop)
    await server.start()
    try:
        yield server
    finally:
        await server.stop()

@pytest.fixture(scope="session")
async def tls_splitter_close(event_loop, tls_combiner_close):
    server = Splitter(address="127.0.0.1",
                      port=1943,
                      ssl_context=None,
                      url="https://localhost:1443/chunk-nordic",
                      loop=event_loop)
    await server.start()
    try:
        yield server
    finally:
        await server.stop()

@pytest.fixture(scope="session")
async def tls_auth_combiner_close(event_loop, conn_closing_server):
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(certfile='/tmp/certs/localhost.pem',
                            keyfile='/tmp/certs/localhost.key')
    context.load_verify_locations(cafile='/tmp/client-certs/ca.pem')
    context.verify_mode = ssl.CERT_REQUIRED
    server = Combiner(address="127.0.0.1",
                      port=1444,
                      ssl_context=context,
                      uri="/chunk-nordic",
                      dst_host="127.0.0.1",
                      dst_port=1313,
                      loop=event_loop)
    await server.start()
    try:
        yield server
    finally:
        await server.stop()

@pytest.fixture(scope="session")
async def tls_auth_splitter_close(event_loop, tls_auth_combiner_close):
    context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    context.load_cert_chain(certfile='/tmp/client-certs/client1.pem',
                            keyfile='/tmp/client-certs/client1.key')
    server = Splitter(address="127.0.0.1",
                      port=1944,
                      ssl_context=context,
                      url="https://localhost:1444/chunk-nordic",
                      loop=event_loop)
    await server.start()
    try:
        yield server
    finally:
        await server.stop()

@pytest.fixture(scope="session")
async def tls_local_combiner_echo(event_loop, echo_server):
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(certfile='/tmp/local-certs/localhost.pem',
                            keyfile='/tmp/local-certs/localhost.key')
    server = Combiner(address="127.0.0.1",
                      port=1445,
                      ssl_context=context,
                      uri="/chunk-nordic",
                      dst_host="127.0.0.1",
                      dst_port=7777,
                      loop=event_loop)
    await server.start()
    try:
        yield server
    finally:
        await server.stop()

@pytest.fixture(scope="session")
async def tls_local_splitter_echo(event_loop, tls_local_combiner_echo):
    context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    context.load_verify_locations(cafile='/tmp/local-certs/ca.pem')
    server = Splitter(address="127.0.0.1",
                      port=1945,
                      ssl_context=context,
                      url="https://localhost:1445/chunk-nordic",
                      loop=event_loop)
    await server.start()
    try:
        yield server
    finally:
        await server.stop()

