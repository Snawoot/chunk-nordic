#!/usr/bin/env python3

import sys
import argparse
import asyncio
import logging
import ssl
import http
import functools
import signal
from .enums import LogLevel, Protocol
from .utils import *


def parse_args():
    parser = argparse.ArgumentParser(
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
                        default=LogLevel.warn)
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


async def amain(args):
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
    # instantiate server here


def main():
    args = parse_args()
    logger = setup_logger('MAIN', args.verbosity)
    #pumpLogger = setup_logger(Pump.__name__, args.verbosity)

    logger.info("Starting eventloop...")
    if not args.disable_uvloop:
        if enable_uvloop():
            logger.info("uvloop enabled.")
        else:
            logger.info("uvloop is not available. "
                        "Falling back to built-in event loop.")

    loop = asyncio.get_event_loop()
    loop.run_until_complete(amain(args))
