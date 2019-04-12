import sys
import argparse
import asyncio
import logging
import ssl
import functools
import signal
import os
from functools import partial

from sdnotify import SystemdNotifier

from .combiner import Combiner
from .constants import LogLevel
from .utils import *


def parse_args():
    parser = argparse.ArgumentParser(
        description="Yet another TCP-over-HTTP(S) tunnel. "
        "Server-side component.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("dst_host",
                        help="target hostname")
    parser.add_argument("dst_port",
                        type=check_port,
                        help="target port")
    parser.add_argument("-u", "--uri",
                        default="/chunk-nordic",
                        help="path where connections served")
    parser.add_argument("-v", "--verbosity",
                        help="logging verbosity",
                        type=LogLevel.__getitem__,
                        choices=list(LogLevel),
                        default=LogLevel.info)
    parser.add_argument("--disable-uvloop",
                        help="do not use uvloop even if it is available",
                        action="store_true")

    listen_group = parser.add_argument_group('listen options')
    listen_group.add_argument("-a", "--bind-address",
                              default="127.0.0.1",
                              help="bind address")
    listen_group.add_argument("-p", "--bind-port",
                              default=8080,
                              type=check_port,
                              help="bind port")

    timing_group = parser.add_argument_group('timing options')
    timing_group.add_argument("-w", "--timeout",
                              default=4,
                              type=check_positive_float,
                              help="backend connect timeout")

    tls_group = parser.add_argument_group('TLS options')
    tls_group.add_argument("-c", "--cert",
                           help="enable TLS and use certificate")
    tls_group.add_argument("-k", "--key",
                           help="key for TLS certificate")
    tls_group.add_argument("-C", "--cafile",
                           help="require client TLS auth using specified CA certs")
    return parser.parse_args()


def exit_handler(exit_event, signum, frame):
    logger = logging.getLogger('MAIN')
    if exit_event.is_set():
        logger.warning("Got second exit signal! Terminating hard.")
        os._exit(1)
    else:
        logger.warning("Got first exit signal! Terminating gracefully.")
        exit_event.set()


async def heartbeat():
    """ Hacky coroutine which keeps event loop spinning with some interval 
    even if no events are coming. This is required to handle Futures and 
    Events state change when no events are occuring."""
    while True:
        await asyncio.sleep(.5)


async def amain(args, loop):
    logger = logging.getLogger('MAIN')
    if args.cert:
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        context.load_cert_chain(certfile=args.cert, keyfile=args.key)
        if args.cafile:
            context.load_verify_locations(cafile=args.cafile)
            context.verify_mode = ssl.CERT_REQUIRED
    else:
        assert not args.cafile, "TLS auth required, but TLS is not enabled"
        context = None

    server = Combiner(address = args.bind_address,
                      port = args.bind_port,
                      ssl_context=context,
                      uri=args.uri,
                      dst_host=args.dst_host,
                      dst_port=args.dst_port,
                      timeout=args.timeout,
                      loop=loop)
    await server.start()
    logger.info("Server started.")

    exit_event = asyncio.Event()
    beat = asyncio.ensure_future(heartbeat())
    sig_handler = partial(exit_handler, exit_event)
    signal.signal(signal.SIGTERM, sig_handler)
    signal.signal(signal.SIGINT, sig_handler)
    notifier = await loop.run_in_executor(None, SystemdNotifier)
    await loop.run_in_executor(None, notifier.notify, "READY=1")
    await exit_event.wait()

    logger.debug("Eventloop interrupted. Shutting down server...")
    await loop.run_in_executor(None, notifier.notify, "STOPPING=1")
    beat.cancel()
    await server.stop()


def main():
    args = parse_args()
    logger = setup_logger('MAIN', args.verbosity)
    setup_logger('Combiner', args.verbosity)
    setup_logger('Joint', args.verbosity)

    logger.info("Starting eventloop...")
    if not args.disable_uvloop:
        if enable_uvloop():
            logger.info("uvloop enabled.")
        else:
            logger.info("uvloop is not available. "
                        "Falling back to built-in event loop.")

    loop = asyncio.get_event_loop()
    loop.run_until_complete(amain(args, loop))
    loop.close()
    logger.info("Server finished its work.")
