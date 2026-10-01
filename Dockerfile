FROM debian:bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        latexmk \
        texlive-latex-base \
        texlive-latex-recommended \
        texlive-latex-extra \
        texlive-fonts-recommended \
        texlive-lang-cyrillic \
        texlive-xetex \
        pandoc \
        python3 \
        poppler-utils \
        lmodern \
        fonts-crosextra-carlito \
        fonts-dejavu-core \
        cm-super \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace
