#!/bin/sh
set -eu
case "${1:-}" in
    handbook)
        sh scripts/build-tex-handbook.sh lab_report \
            build/html/lab-report build/pdf/lab-report/demo-lab.pdf
        sh scripts/build-tex-handbook.sh lab_report_example \
            build/html/lab-report build/pdf/lab-report/example-report.pdf report
        ;;
    *) printf '%s\n' 'Usage: sh scripts/build-lab-report.sh handbook' >&2; exit 2 ;;
esac
