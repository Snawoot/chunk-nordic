import sys
import argparse
import asyncio
import logging
import ssl
import signal
from functools import partial
from urllib.parse import urlparse

from .asdnotify import AsyncSystemdNotifier
from .splitter import Splitter
from .constants import LogLevel
from .utils import check_port, check_positive_float, check_loglevel, \
    setup_logger, enable_uvloop, exit_handler, heartbeat


def parse_args():
    parser = argparse.ArgumentParser(
        description="Yet another TCP-over-HTTP(S) tunnel. "
        "Client-side component.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("server_url",
                        help="target hostname")
    parser.add_argument("-v", "--verbosity",
                        help="logging verbosity",
                        type=check_loglevel,
                        choices=LogLevel,
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


async def amain(args, loop):  # pragma: no cover
    logger = logging.getLogger('MAIN')

    if args.cert or args.cafile or args.no_hostname_check:
        if urlparse(args.server_url).scheme.lower() != 'https':
            logger.fatal("https:// scheme in URI required for TLS operation. "
                         "Terminating program.")
            sys.exit(2)
        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        if args.cafile:
            context.load_verify_locations(cafile=args.cafile)
        if args.no_hostname_check:
            if not args.cafile:
                logger.fatal("CAfile option is required when hostname check "
                             "is disabled. Terminating program.")
                sys.exit(2)
            context.check_hostname = False
        if args.cert:
            context.load_cert_chain(certfile=args.cert, keyfile=args.key)
    else:
        context = None


    server = Splitter(address=args.bind_address,
                      port=args.bind_port,
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
    async with AsyncSystemdNotifier() as notifier:
        await notifier.notify(b"READY=1")
        await exit_event.wait()

        logger.debug("Eventloop interrupted. Shutting down server...")
        await notifier.notify(b"STOPPING=1")
    beat.cancel()
    await server.stop()


def main():  # pragma: no cover
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
