chunk-nordic
============

[![Build Status](https://travis-ci.org/Snawoot/chunk-nordic.svg?branch=master)](https://travis-ci.org/Snawoot/chunk-nordic) [![Coverage](https://img.shields.io/badge/coverage-100%25-4dc71f.svg)](https://travis-ci.org/Snawoot/chunk-nordic) [![PyPI - Downloads](https://img.shields.io/pypi/dm/chunk-nordic.svg?color=4dc71f&label=PyPI%20downloads)](https://pypistats.org/packages/chunk-nordic) [![PyPI](https://img.shields.io/pypi/v/chunk-nordic.svg)](https://pypi.org/project/chunk-nordic/) [![PyPI - Status](https://img.shields.io/pypi/status/chunk-nordic.svg)](https://pypi.org/project/chunk-nordic/) [![PyPI - License](https://img.shields.io/pypi/l/chunk-nordic.svg?color=4dc71f)](https://pypi.org/project/chunk-nordic/) [![chunk-nordic](https://snapcraft.io//chunk-nordic/badge.svg)](https://snapcraft.io/chunk-nordic)

Yet another TCP-over-HTTP(S) tunnel.

Client component accepts TCP connections and forwards them to server component via pair of HTTP(S) connections in streaming mode (`Content-Encoding: chunked`). Server component forwards connections to target host and port (e.g. to VPN daemon).

---

:heart: :heart: :heart:

You can say thanks to the author by donations to these wallets:

- ETH: `0xB71250010e8beC90C5f9ddF408251eBA9dD7320e`
- BTC:
  - Legacy: `1N89PRvG1CSsUk9sxKwBwudN6TjTPQ1N8a`
  - Segwit: `bc1qc0hcyxc000qf0ketv4r44ld7dlgmmu73rtlntw`

---

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

## Installation

With basic Python event loop:

```
pip3 install chunk-nordic
```

With high performance uvloop event loop:

```
pip3 install chunk-nordic[uvloop]
```

If you prefer distribution via Docker image see Docker Example section below.

Also chunk-nordic is available on Snap Store:

[![Get it from the Snap Store](https://snapcraft.io/static/images/badges/en/snap-store-black.svg)](https://snapcraft.io/chunk-nordic)

```
sudo snap install chunk-nordic
```

Note that binaries installed by snap are named `chunk-nordic.client` and `chunk-nordic.server`.

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

## Docker Example

For environment same as in example above:

Server:

```bash
docker run -dit \
    -p 8080:8080 \
    --restart unless-stopped \
    --name chunk-nordic-server yarmak/chunk-nordic \
    server 127.0.0.1 1194
```

Client:

```bash
docker run -dit \
    -p 1940:1940 \
    --restart unless-stopped \
    --name chunk-nordic-server yarmak/chunk-nordic \
    client http://gate.example.com:8080/chunk-nordic
```
