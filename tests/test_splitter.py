import pytest

from chunk_nordic.splitter import AsyncReaderIterable

@pytest.mark.asyncio
async def test_asyncreader_reenter():
    class EmptyReader:
        async def read(self, _):
            return b''
    ari = AsyncReaderIterable(EmptyReader())
    async for _ in ari:
        assert 0
    async for _ in ari:
        assert 0
