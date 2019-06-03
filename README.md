chunk-nordic
============

[![Build Status](https://travis-ci.org/Snawoot/chunk-nordic.svg?branch=master)](https://travis-ci.org/Snawoot/chunk-nordic) [![Coverage](https://img.shields.io/badge/coverage-100%25-4dc71f.svg)](https://travis-ci.org/Snawoot/chunk-nordic) [![PyPI - Downloads](https://img.shields.io/pypi/dm/chunk-nordic.svg?color=4dc71f&label=PyPI%20downloads)](https://pypistats.org/packages/chunk-nordic) [![PyPI](https://img.shields.io/pypi/v/chunk-nordic.svg)](https://pypi.org/project/chunk-nordic/) [![PyPI - Status](https://img.shields.io/pypi/status/chunk-nordic.svg)](https://pypi.org/project/chunk-nordic/) [![PyPI - License](https://img.shields.io/pypi/l/chunk-nordic.svg?color=4dc71f)](https://pypi.org/project/chunk-nordic/)

Yet another TCP-over-HTTP(S) tunnel.

Client component accepts TCP connections and forwards them to server component via pair of HTTP(S) connections in streaming mode (`Content-Encoding: chunked`). Server component forwards connections to target host and port (e.g. to VPN daemon).

## Features

* Multi-link full asynchronous operation.
* Client support operation via proxy server (via HTTP\_PROXY, HTTPS\_PROXY environment variables and .netrc file).
* Advanced TLS support:
  * Supports custom CAs for client and server.
  * Supports mutual TLS authentication between client and server with certificates.

For TLS reference see "TLS options" group in invokation synopsis.

## Requirements

* Python 3.5.3+
* aiohttp
* sdnotify

## Installation

With basic Python event loop:

```
pip3 install chunk-nordic
```

With high performance uvloop event loop:

```
pip3 install chunk-nordic[uvloop]
```

## Synopsis

Server:

```
$ chunk-server --help
usage: chunk-server [-h] [-u URI] [-v {debug,info,warn,error,fatal}]
                    [--disable-uvloop] [-a BIND_ADDRESS] [-p BIND_PORT]
                    [-w TIMEOUT] [-c CERT] [-k KEY] [-C CAFILE]
                    dst_host dst_port

Yet another TCP-over-HTTP(S) tunnel. Server-side component.

positional arguments:
  dst_host              target hostname
  dst_port              target port

optional arguments:
  -h, --help            show this help message and exit
  -u URI, --uri URI     path where connections served (default: /chunk-nordic)
  -v {debug,info,warn,error,fatal}, --verbosity {debug,info,warn,error,fatal}
                        logging verbosity (default: info)
  --disable-uvloop      do not use uvloop even if it is available (default:
                        False)

listen options:
  -a BIND_ADDRESS, --bind-address BIND_ADDRESS
                        bind address (default: 127.0.0.1)
  -p BIND_PORT, --bind-port BIND_PORT
                        bind port (default: 8080)

timing options:
  -w TIMEOUT, --timeout TIMEOUT
                        backend connect timeout (default: 4)

TLS options:
  -c CERT, --cert CERT  enable TLS and use certificate (default: None)
  -k KEY, --key KEY     key for TLS certificate (default: None)
  -C CAFILE, --cafile CAFILE
                        require client TLS auth using specified CA certs
                        (default: None)
```

Client:

```
$ chunk-client --help
usage: chunk-client [-h] [-v {debug,info,warn,error,fatal}] [--disable-uvloop]
                    [-a BIND_ADDRESS] [-p BIND_PORT] [-w TIMEOUT] [-c CERT]
                    [-k KEY] [-C CAFILE] [--no-hostname-check]
                    server_url

Yet another TCP-over-HTTP(S) tunnel. Client-side component.

positional arguments:
  server_url            target hostname

optional arguments:
  -h, --help            show this help message and exit
  -v {debug,info,warn,error,fatal}, --verbosity {debug,info,warn,error,fatal}
                        logging verbosity (default: info)
  --disable-uvloop      do not use uvloop even if it is available (default:
                        False)

listen options:
  -a BIND_ADDRESS, --bind-address BIND_ADDRESS
                        bind address (default: 127.0.0.1)
  -p BIND_PORT, --bind-port BIND_PORT
                        bind port (default: 1940)

timing options:
  -w TIMEOUT, --timeout TIMEOUT
                        server connect timeout (default: 4)

TLS options:
  -c CERT, --cert CERT  use certificate for client TLS auth (default: None)
  -k KEY, --key KEY     key for TLS certificate (default: None)
  -C CAFILE, --cafile CAFILE
                        override default CA certs by set specified in file
                        (default: None)
  --no-hostname-check   do not check hostname in cert subject. This option is
                        useful for private PKI and available only together
                        with "--cafile" (default: False)
```

## Example

Let's assume we have OpenVPN instance on TCP port 1194 at server gate.example.com.

Server command:

```
chunk-server 127.0.0.1 1194
```

Client command:

```
chunk-client http://gate.example.com:8080/chunk-nordic
```

Fragment of client's OpenVPN config:

```
<connection>
remote 127.0.0.1 1940 tcp
</connection>
```
