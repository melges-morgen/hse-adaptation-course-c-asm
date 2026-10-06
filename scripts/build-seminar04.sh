#!/bin/sh
set -eu
case "${1:-}" in
    handbook)
        sh scripts/build-tex-handbook.sh seminar04 \
            build/html/seminar04 build/pdf/seminar04/seminar04.pdf
        sh scripts/build-tex-handbook.sh seminar04_factorial \
            build/html/seminar04/factorial build/pdf/seminar04/seminar04-factorial.pdf
        ;;
    *) printf '%s\n' 'Usage: sh scripts/build-seminar04.sh handbook' >&2; exit 2 ;;
esac
