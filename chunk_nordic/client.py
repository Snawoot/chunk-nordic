import sys
import argparse
import asyncio
import logging
import ssl
import functools
import signal
import os
from functools import partial
from urllib.parse import urlparse

from sdnotify import SystemdNotifier

from .splitter import Splitter
from .constants import LogLevel
from .utils import *


def parse_args():
    parser = argparse.ArgumentParser(
        description="Yet another TCP-over-HTTP(S) tunnel. "
        "Client-side component.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("server_url",
                        help="target hostname")
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
                              default=1940,
                              type=check_port,
                              help="bind port")

    timing_group = parser.add_argument_group('timing options')
    timing_group.add_argument("-w", "--timeout",
                              default=4,
                              type=check_positive_float,
                              help="server connect timeout")

    tls_group = parser.add_argument_group('TLS options')
    tls_group.add_argument("-c", "--cert",
                           help="use certificate for client TLS auth")
    tls_group.add_argument("-k", "--key",
                           help="key for TLS certificate")
    tls_group.add_argument("-C", "--cafile",
                           help="override default CA certs "
                           "by set specified in file")
    tls_group.add_argument("--no-hostname-check",
                           action="store_true",
                           help="do not check hostname in cert subject. "
                           "This option is useful for private PKI and "
                           "available only together with \"--cafile\"")
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

    if args.cert or args.cafile or args.no_hostname_check:
        assert urlparse(args.url).scheme.lower() == 'https', "https:// scheme required"
        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        if args.cafile:
            context.load_verify_locations(cafile=args.cafile)
        if args.no_hostname_check:
            assert args.cafile, ("CAfile option is required when "
                                 "hostname check is disabled")
            context.check_hostname = False
        if args.cert:
            context.load_cert_chain(certfile=args.cert, keyfile=args.key)
    else:
        context=None


    server = Splitter(address = args.bind_address,
                      port = args.bind_port,
                      ssl_context=context,
                      url=args.server_url,
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
    setup_logger('Splitter', args.verbosity)
    setup_logger('Fork', args.verbosity)

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
