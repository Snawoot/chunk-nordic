import asyncio
import socket
import weakref
import logging

class Splitter:
    SHUTDOWN_TIMEOUT = 5

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
            self._logger.debug("Cancelling %d client handlers...",
                               len(self._children))
            for task in self._children:
                task.cancel()
            await asyncio.wait(self._children)
            # workaround for TCP server spawning handlers for a while
            # after wait_closed() completed
            asyncio.sleep(.5) 

    async def handler(self, reader, writer):
        pass
        #writer.transport.pause_reading()
        #sock = writer.transport.get_extra_info('socket')
        #if sock is not None:
        #    try:
        #        sock.shutdown(socket.SHUT_RD)
        #    except TypeError:
        #        direct_sock = socket.socket(sock.family, sock.type, sock.proto, sock.fileno())
        #        try:
        #            direct_sock.shutdown(socket.SHUT_RD)
        #        finally:
        #            direct_sock.detach()
        #peer_addr = writer.transport.get_extra_info('peername')
        #self._logger.info("Client %s connected", str(peer_addr))
        #try:
        #    while True:
        #        await asyncio.sleep(self._interval)
        #        writer.write(b'%.8x\r\n' % random.randrange(2**32))
        #        await writer.drain()
        #except (ConnectionResetError, RuntimeError, TimeoutError) as e:
        #    self._logger.debug('Terminating handler coro with error: %s',
        #                       str(e))
        #except OSError as e:
        #    self._logger.debug('Terminating handler coro with error: %s',
        #                       str(e))
        #    if e.errno == 107:
        #        pass
        #    else:
        #        raise
        #finally:
        #    self._logger.info("Client %s disconnected", str(peer_addr))

    async def start(self):
        def _spawn(reader, writer):
            self._children.add(
                self._loop.create_task(self.handler(reader, writer)))

        self._server = await asyncio.start_server(_spawn,
                                                  self._address,
                                                  self._port,
                                                  reuse_address=True)
        self._logger.info("Server ready.")
