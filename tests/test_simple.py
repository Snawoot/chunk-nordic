import asyncio
import uuid

import pytest

@pytest.mark.asyncio
async def test_simple_echo(plaintext_splitter, plaintext_combiner):
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
