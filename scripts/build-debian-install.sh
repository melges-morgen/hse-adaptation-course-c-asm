#!/bin/sh
set -eu
case "${1:-}" in
    handbook)
        sh scripts/build-tex-handbook.sh debian_install \
            build/html/debian-install build/pdf/debian-install/debian-install.pdf
        ;;
    *) printf '%s\n' 'Usage: sh scripts/build-debian-install.sh handbook' >&2; exit 2 ;;
esac
