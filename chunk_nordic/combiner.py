import asyncio
import logging
import uuid
import weakref

from aiohttp import web
from .constants import SERVER, BUFSIZE, Way


class Joint:  # pylint: disable=too-few-public-methods
    def __init__(self, dst_host, dst_port, timeout=None, loop=None):
        loop = loop if loop is not None else asyncio.get_event_loop()
        self._conn = asyncio.ensure_future(
            asyncio.wait_for(
                asyncio.open_connection(dst_host, dst_port, loop=loop),
                timeout,
                loop=loop),
            loop=loop)
        self._logger = logging.getLogger("Joint")
        self._writer_done = False
        self._reader_done = False

    async def _patch_upstream(self, req):
        try:
            await self._conn
            _, writer = self._conn.result()
        except asyncio.CancelledError:  # pragma: no cover pylint: disable=try-except-raise
            raise
        except Exception as exc:
            self._writer_done = True
            return web.Response(text=("Connect error: %s" % str(exc)),
                                status=503,
                                headers={"Server": SERVER})
        try:
            while True:
                data = await req.content.read(BUFSIZE)
                if not data:
                    break
                writer.write(data)
                await writer.drain()
        except asyncio.CancelledError:  # pylint: disable=try-except-raise
            raise
        except Exception as exc:  # pragma: no cover
            self._logger.exception("_patch_upstream exception: %s", str(exc))
            return web.Response(status=204, headers={"Server": SERVER})
        else:
            return web.Response(status=204, headers={"Server": SERVER})
        finally:
            self._writer_done = True

    async def _patch_downstream(self, req):
        try:
            await self._conn
            reader, _ = self._conn.result()
        except asyncio.CancelledError:  # pragma: no cover pylint: disable=try-except-raise
            raise
        except Exception as exc:
            self._reader_done = True
            return web.Response(text=("Connect error: %s" % str(exc)),
                                status=503,
                                headers={"Server": SERVER})

        resp = web.StreamResponse(
            headers={'Content-Type': 'application/octet-stream',
                     'Server': SERVER,})
        resp.enable_chunked_encoding()
        await resp.prepare(req)

        try:
            while True:
                data = await reader.read(BUFSIZE)
                if not data:
                    break
                await resp.write(data)
        except asyncio.CancelledError:  # pylint: disable=try-except-raise
            raise
        except Exception as exc:  # pragma: no cover
            self._logger.exception("_patch_downstream exception: %s", str(exc))
            return resp
        else:
            return resp
        finally:
            self._reader_done = True


    async def patch_in(self, req, way):
        try:
            if way is Way.upstream:
                return await self._patch_upstream(req)
            elif way is Way.downstream:
                return await self._patch_downstream(req)
        finally:
            if self._writer_done and self._reader_done and self._conn is not None:
                try:
                    _, writer = self._conn.result()
                except Exception:  # pragma: no cover
                    pass
                else:
                    writer.close()
                    self._conn = None


class Combiner:  # pylint: disable=too-many-instance-attributes
    SHUTDOWN_TIMEOUT = 0

    def __init__(self, *, address=None, port=8080, ssl_context=None,
                 uri="/chunk-nordic", dst_host, dst_port, timeout=None,
                 loop=None):
        self._loop = loop if loop is not None else asyncio.get_event_loop()
        self._logger = logging.getLogger(self.__class__.__name__)
        self._address = address
        self._port = port
        self._uri = uri
        self._dst_host = dst_host
        self._dst_port = dst_port
        self._timeout = timeout
        self._ssl_context = ssl_context
        self._joints = weakref.WeakValueDictionary()
        self._server = None
        self._runner = None
        self._site = None

    async def stop(self):
        await self._server.shutdown(self.SHUTDOWN_TIMEOUT)
        await self._site.stop()
        await self._runner.cleanup()

    async def _dispatch_req(self, req, sid, way):
        try:
            joint = self._joints[sid]
        except KeyError:
            self._logger.debug("Creating joint for session=%s", sid)
            joint = Joint(self._dst_host, self._dst_port, self._timeout, self._loop)
            self._joints[sid] = joint
        return await joint.patch_in(req, way)

    async def handler(self, request):
        peer_addr = request.transport.get_extra_info('peername')
        if request.path != self._uri:
            return web.Response(status=404, text="NOT FOUND\n",
                                headers={"Server": SERVER})
        try:
            sid = uuid.UUID(hex=request.headers["X-Session-ID"])
            way = Way(int(request.headers["X-Session-Way"]))
            self._logger.info("Client connected: addr=%s, sid=%s, way=%s.",
                              str(peer_addr), sid, way)
        except Exception:
            return web.Response(status=400, text="INVALID REQUEST\n",
                                headers={"Server": SERVER})
        try:
            return await self._dispatch_req(request, sid, way)
        finally:
            self._logger.info("Client left: addr=%s, sid=%s, way=%s.", str(peer_addr), sid, way)

    async def start(self):
        self._server = web.Server(self.handler)
        self._runner = web.ServerRunner(self._server)
        await self._runner.setup()
        self._site = web.TCPSite(self._runner, self._address, self._port,
                                 ssl_context=self._ssl_context,
                                 shutdown_timeout=self.SHUTDOWN_TIMEOUT)
        await self._site.start()
        self._logger.info("Server ready.")
