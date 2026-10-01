#!/bin/sh
set -eu

source=demos/seminar04/README.md
basic=demos/seminar04/factorial/README.md
case "${1:-}" in
    fragment)
        mkdir -p build/latex
        pandoc "$source" --from=gfm --to=latex --no-highlight \
            --lua-filter=tex/seminars/seminar04-fragment.lua \
            --lua-filter=tex/seminars/seminar04-tables.lua \
            --output=build/latex/seminar04_body.tex
        pandoc "$basic" --from=gfm --to=latex --no-highlight \
            --lua-filter=tex/seminars/seminar04-fragment.lua \
            --lua-filter=tex/seminars/seminar04-tables.lua \
            --output=build/latex/seminar04_factorial_body.tex
        ;;
    handbook)
        mkdir -p build/html/seminar04 build/html/seminar04/factorial build/pdf/seminar04
        pandoc "$source" --from=gfm --standalone --to=html5 --toc --no-highlight \
            --self-contained --css=tex/seminars/seminar04.css \
            --metadata-file=tex/seminars/seminar04.yaml \
            --output=build/html/seminar04/index.html
        pandoc "$source" --from=gfm --standalone --toc \
            --lua-filter=tex/seminars/seminar04-tables.lua \
            --pdf-engine=xelatex --variable=documentclass:extarticle \
            --variable=fontsize:14pt --variable=lang:ru \
            --variable=mainfont:Carlito --variable='monofont:DejaVu Sans Mono' \
            --variable=papersize:a4 \
            --variable=geometry:margin=2cm \
            --output=build/pdf/seminar04/seminar04.pdf
        pandoc "$basic" --from=gfm --standalone --to=html5 --toc --no-highlight \
            --self-contained --css=tex/seminars/seminar04.css \
            --metadata=lang:ru \
            --metadata='pagetitle:Семинар №4 · вариант 1 · факториал на C' \
            --output=build/html/seminar04/factorial/index.html
        pandoc "$basic" --from=gfm --standalone --toc \
            --lua-filter=tex/seminars/seminar04-tables.lua \
            --pdf-engine=xelatex --variable=documentclass:extarticle \
            --variable=fontsize:14pt --variable=lang:ru \
            --variable=mainfont:Carlito --variable='monofont:DejaVu Sans Mono' \
            --variable=papersize:a4 \
            --variable=geometry:margin=2cm \
            --output=build/pdf/seminar04/seminar04-factorial.pdf
        ;;
    *)
        printf '%s\n' 'Usage: sh scripts/build-seminar04.sh fragment|handbook' >&2
        exit 2
        ;;
esac
