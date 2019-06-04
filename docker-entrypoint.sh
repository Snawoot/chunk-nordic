#!/bin/sh

set -e

bad_arg () {
    >&2 echo "First argument must be either \"server\" or \"client\"."
    exit 2
}

[ "$#" -lt 1 ] && bad_arg
CMD="$1"
shift

case "$CMD" in
    server)
        chunk-server -a 0.0.0.0 "$@"
        ;;
    client)
        chunk-client -a 0.0.0.0 "$@"
        ;;
    *)
        bad_arg
        ;;
esac
