import asyncio
import weakref
import logging
import uuid

import aiohttp

from .constants import BUFSIZE, Way


class AsyncReaderIterable:
    def __init__(self, reader):
        self._reader = reader
        self._exhausted = False

    def __aiter__(self):
        return self

    async def __anext__(self):
        if not self._exhausted:
            data = await self._reader.read(BUFSIZE)
            if not data:
                self._exhausted = True
                raise StopAsyncIteration
            return data
        else:
            raise StopAsyncIteration


class Fork:
    def __init__(self, url, ssl_context=None, timeout=None, loop=None):
        self._loop = loop if loop is not None else asyncio.get_event_loop()
        self._url = url
        self._ssl_context = ssl_context
        self._timeout = aiohttp.ClientTimeout(connect=timeout)
        self._logger = logging.getLogger(self.__class__.__name__)
        self._uuid = uuid.uuid4()

    async def _upstream(self, reader):
        headers = {
            'Content-Type': 'application/octet-stream',
            'X-Session-ID': self._uuid.hex,
            'X-Session-Way': str(Way.upstream.value),
        }
        async with aiohttp.ClientSession(timeout=self._timeout) as session:
            await session.post(self._url,
                               data=AsyncReaderIterable(reader),
                               headers=headers,
                               ssl=self._ssl_context,
                               compress=False)

    async def _downstream(self, writer):
        headers = {
            'Content-Type': 'application/octet-stream',
            'X-Session-ID': self._uuid.hex,
            'X-Session-Way': str(Way.downstream.value),
        }
        async with aiohttp.ClientSession(timeout=self._timeout) as session:
            async with session.post(self._url,
                                    headers=headers,
                                    ssl=self._ssl_context,
                                    compress=False) as resp:
                while True:
                    data = await resp.content.read(BUFSIZE)
                    if not data:
                        break
                    writer.write(data)
                    await writer.drain()

    async def split(self, reader, writer):
        await asyncio.gather(self._upstream(reader),
                             self._downstream(writer))


class Splitter:
    def __init__(self, *,
                 address,
                 port,
                 url,
                 ssl_context=None,
                 timeout=None,
                 loop=None):
        self._loop = loop if loop is not None else asyncio.get_event_loop()
        self._logger = logging.getLogger(self.__class__.__name__)
        self._address = address
        self._port = port
        self._url = url
        self._ssl_context = ssl_context
        self._timeout = timeout
        self._children = weakref.WeakSet()

    async def stop(self):
        self._server.close()
        await self._server.wait_closed()
        while self._children:
            children = list(self._children)
            self._children.clear()
            self._logger.debug("Cancelling %d client handlers...",
                               len(children))
            for task in children:
                task.cancel()
            await asyncio.wait(children)
            # workaround for TCP server keeps spawning handlers for a while
            # after wait_closed() completed
            asyncio.sleep(.5) 

    async def handler(self, reader, writer):
        peer_addr = writer.transport.get_extra_info('peername')
        self._logger.info("Client %s connected", str(peer_addr))
        try:
            fork = Fork(self._url, self._ssl_context, self._timeout, self._loop)
            await fork.split(reader, writer)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            self._logger.exception("Connection handler stopped with exception:"
                                   " %s", str(e))
        finally:
            self._logger.info("Client %s disconnected", str(peer_addr))
            writer.close()

    async def start(self):
        def _spawn(reader, writer):
            self._children.add(
                self._loop.create_task(self.handler(reader, writer)))

        self._server = await asyncio.start_server(_spawn,
                                                  self._address,
                                                  self._port)
        self._logger.info("Server ready.")
