#!/bin/sh
set -eu

name=$1
html_dir=$2
pdf_file=$3
jobname=${4:-index}
mkdir -p "build/tex4ht/$name" "$html_dir" "build/latex/standalone/$name"
(
    cd "build/tex4ht/$name"
    TEXINPUTS=/workspace/: make4ht -x -f html5 -j "$jobname" \
        -d "/workspace/$html_dir" "/workspace/tex/standalone/$name.tex"
)
cp tex/seminars/seminar04.css "$html_dir/course.css"
python3 scripts/finish-tex4ht-html.py "$html_dir/$jobname.html"
latexmk -xelatex -interaction=nonstopmode -halt-on-error -quiet \
    -outdir="build/latex/standalone/$name" "tex/standalone/$name.tex"
install -Dm644 "build/latex/standalone/$name/$name.pdf" "$pdf_file"
