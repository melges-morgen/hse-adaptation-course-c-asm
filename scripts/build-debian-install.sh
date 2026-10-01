#!/bin/sh
set -eu

source=supplementary/debian-install/README.md
case "${1:-}" in
    fragment)
        mkdir -p build/latex
        pandoc "$source" --from=gfm --to=latex --no-highlight \
            --lua-filter=tex/supplementary/ubuntu_terminal_fragment.lua \
            --lua-filter=tex/supplementary/debian_install_tables.lua \
            --output=build/latex/debian_install_body.tex
        ;;
    handbook)
        mkdir -p build/html/debian-install build/pdf/debian-install
        pandoc "$source" --from=gfm --standalone --to=html5 --toc --no-highlight \
            --self-contained --css=tex/seminars/seminar04.css \
            --metadata=lang:ru \
            --metadata='pagetitle:Установка Debian и знакомство с терминалом' \
            --output=build/html/debian-install/index.html
        pandoc "$source" --from=gfm --standalone --toc \
            --lua-filter=tex/supplementary/debian_install_tables.lua \
            --pdf-engine=xelatex --variable=documentclass:extarticle \
            --variable=fontsize:14pt --variable=lang:ru \
            --variable=mainfont:Carlito --variable='monofont:DejaVu Sans Mono' \
            --variable=papersize:a4 --variable=geometry:margin=2cm \
            --output=build/pdf/debian-install/debian-install.pdf
        ;;
    *)
        printf '%s\n' 'Usage: sh scripts/build-debian-install.sh fragment|handbook' >&2
        exit 2
        ;;
esac
