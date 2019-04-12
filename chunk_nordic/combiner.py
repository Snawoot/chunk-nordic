import asyncio
import logging
import uuid

from aiohttp import web
from .constants import SERVER, Way


class Combiner:
    SHUTDOWN_TIMEOUT = 1

    def __init__(self, *, address=None, port=8080, ssl_context=None,
                 uri="/chunk-nordic", dst_host, dst_port, loop=None):
        self._loop = loop if loop is not None else asyncio.get_event_loop()
        self._logger = logging.getLogger(self.__class__.__name__)
        self._address = address
        self._port = port
        self._uri = uri
        self._dst_host = dst_host
        self._dst_port = dst_port
        self._ssl_context = ssl_context

    async def stop(self):
        await self._server.shutdown()
        await self._site.stop()
        await self._runner.cleanup()

    async def _dispatch_req(self, req, sid, way):
        return web.Response(text="OK\n", headers={"Server": SERVER})

    async def handler(self, request):
        peer_addr = request.transport.get_extra_info('peername')
        if request.path != self._uri:
            return web.Response(status=404, text="NOT FOUND\n",
                                headers={"Server": SERVER})
        try:
            sid = uuid.UUID(hex=request.headers["X-Session-ID"])
            way = Way(int(request.headers["X-Session-Way"]))
            self._logger.info("Client connected: addr=%s, sid=%s, way=%s.", str(peer_addr), sid, way)
        except:
            return web.Response(status=400, text="INVALID REQUEST\n",
                                headers={"Server": SERVER})
        return await self._dispatch_req(request, sid, way)

        #resp = web.StreamResponse(
        #    headers={'Content-Type': 'application/octet-stream'})
        #resp.enable_chunked_encoding()
        #await resp.prepare(request)
        #await self._guarded_run(resp.write(self.ZEROES))
        #return resp

    async def start(self):
        self._server = web.Server(self.handler)
        self._runner = web.ServerRunner(self._server)
        await self._runner.setup()
        self._site = web.TCPSite(self._runner, self._address, self._port,
                                 ssl_context=self._ssl_context,
                                 shutdown_timeout=self.SHUTDOWN_TIMEOUT)
        await self._site.start()
        self._logger.info("Server ready.")
