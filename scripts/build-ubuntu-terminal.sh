#!/bin/sh
set -eu

source=supplementary/ubuntu-terminal/README.md
case "${1:-}" in
    fragment)
        mkdir -p build/latex
        pandoc "$source" --from=gfm --to=latex --no-highlight \
            --lua-filter=tex/supplementary/ubuntu_terminal_fragment.lua \
            --output=build/latex/ubuntu_terminal_body.tex
        ;;
    handbook)
        mkdir -p build/html/ubuntu-terminal build/pdf/ubuntu-terminal
        pandoc "$source" --from=gfm --standalone --to=html5 --toc --no-highlight \
            --self-contained --css=tex/seminars/seminar04.css \
            --metadata=lang:ru \
            --metadata='pagetitle:Загрузка Ubuntu и первые шаги в терминале' \
            --output=build/html/ubuntu-terminal/index.html
        pandoc "$source" --from=gfm --standalone --toc \
            --pdf-engine=xelatex --variable=documentclass:extarticle \
            --variable=fontsize:14pt --variable=lang:ru \
            --variable=mainfont:Carlito --variable='monofont:DejaVu Sans Mono' \
            --variable=papersize:a4 --variable=geometry:margin=2cm \
            --output=build/pdf/ubuntu-terminal/ubuntu-terminal.pdf
        ;;
    *)
        printf '%s\n' 'Usage: sh scripts/build-ubuntu-terminal.sh fragment|handbook' >&2
        exit 2
        ;;
esac
