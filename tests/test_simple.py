import asyncio
import uuid
import os
import hashlib

import pytest

LONGTEST_LEN = 10 * 1024 * 1024

@pytest.mark.asyncio
@pytest.mark.timeout(5)
async def test_simple_echo(plaintext_splitter):
    data = uuid.uuid4().bytes
    reader, writer = await asyncio.open_connection("127.0.0.1", 1940)
    writer.write(data)
    buf = b''
    while True:
        rd = await reader.read(4096)
        assert rd
        buf += rd
        if len(buf) >= len(data):
            break
    assert buf == data

@pytest.mark.asyncio
@pytest.mark.timeout(5)
async def test_long_echo(plaintext_splitter):
    reader, writer = await asyncio.open_connection("127.0.0.1", 1940)
    async def read_coro(reader):
        rd_hash = hashlib.sha256()
        while True:
            data = await reader.read(4096)
            if not data:
                break
            rd_hash.update(data)
        return rd_hash.digest()
    async def write_coro(writer):
        wr_hash = hashlib.sha256()
        written = 0
        while written < LONGTEST_LEN:
            data = os.urandom(128)
            wr_hash.update(data)
            writer.write(data)
            written += len(data)
            await writer.drain()
        return wr_hash.digest()
    try:
        rt = asyncio.ensure_future(read_coro(reader))
        wt = asyncio.ensure_future(write_coro(writer))
        wr_hash = await wt
        await asyncio.sleep(1)
        writer.close()
        rd_hash = await rt
        assert rd_hash == rd_hash
    except:
        writer.close()
        raise

@pytest.mark.asyncio
@pytest.mark.timeout(5)
async def test_conn_close(plaintext_splitter_close):
    reader, writer = await asyncio.open_connection("127.0.0.1", 1941)
    buf = b''
    while True:
        data = await reader.read(4096)
        if not data:
            break
        buf += data
    assert buf == b"MAGIC!"
