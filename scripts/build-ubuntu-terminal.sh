#!/bin/sh
set -eu

case "${1:-}" in
    handbook)
        sh scripts/build-tex-handbook.sh ubuntu_terminal \
            build/html/ubuntu-terminal build/pdf/ubuntu-terminal/ubuntu-terminal.pdf
        ;;
    *)
        printf '%s\n' 'Usage: sh scripts/build-ubuntu-terminal.sh handbook' >&2
        exit 2
        ;;
esac
