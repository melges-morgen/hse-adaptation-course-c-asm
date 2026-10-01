#!/bin/sh
set -eu

lab=supplementary/lab-report/README.md
report=supplementary/lab-report/report.md
case "${1:-}" in
    fragment)
        mkdir -p build/latex
        pandoc "$lab" --from=gfm --to=latex --no-highlight \
            --lua-filter=tex/supplementary/ubuntu_terminal_fragment.lua \
            --lua-filter=tex/supplementary/lab_report_tables.lua \
            --output=build/latex/lab_report_body.tex
        pandoc "$report" --from=gfm --to=latex --no-highlight \
            --lua-filter=tex/supplementary/ubuntu_terminal_fragment.lua \
            --lua-filter=tex/supplementary/lab_report_tables.lua \
            --output=build/latex/lab_report_example_body.tex
        ;;
    handbook)
        mkdir -p build/html/lab-report build/pdf/lab-report
        pandoc "$lab" --from=gfm --standalone --to=html5 --toc --no-highlight \
            --self-contained --css=tex/seminars/seminar04.css \
            --metadata=lang:ru \
            --metadata='pagetitle:Демонстрационная лабораторная · сумма двух чисел' \
            --output=build/html/lab-report/index.html
        pandoc "$report" --from=gfm --standalone --to=html5 --toc --no-highlight \
            --self-contained --css=tex/seminars/seminar04.css \
            --metadata=lang:ru \
            --metadata='pagetitle:Пример отчёта · сумма двух чисел' \
            --output=build/html/lab-report/report.html
        pandoc "$lab" --from=gfm --standalone --toc \
            --lua-filter=tex/supplementary/lab_report_tables.lua \
            --pdf-engine=xelatex --variable=documentclass:extarticle \
            --variable=fontsize:14pt --variable=lang:ru \
            --variable=mainfont:Carlito --variable='monofont:DejaVu Sans Mono' \
            --variable=papersize:a4 --variable=geometry:margin=2cm \
            --output=build/pdf/lab-report/demo-lab.pdf
        pandoc "$report" --from=gfm --standalone \
            --lua-filter=tex/supplementary/lab_report_tables.lua \
            --pdf-engine=xelatex --variable=documentclass:extarticle \
            --variable=fontsize:14pt --variable=lang:ru \
            --variable=mainfont:Carlito --variable='monofont:DejaVu Sans Mono' \
            --variable=papersize:a4 --variable=geometry:margin=2cm \
            --output=build/pdf/lab-report/example-report.pdf
        ;;
    *)
        printf '%s\n' 'Usage: sh scripts/build-lab-report.sh fragment|handbook' >&2
        exit 2
        ;;
esac
