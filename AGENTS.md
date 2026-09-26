# AGENTS.md

## Project Overview

This repository contains materials for an adaptation course for first-year Software Engineering students at HSE.

The course is intended to close gaps left after school and prepare students for the course "Algorithms and Algorithmic Languages", which uses C and NASM assembly.

The materials are written in Russian. Keep the language of course content Russian unless explicitly asked otherwise.

## Repository Structure

- `pud_adaptation_course.tex` is the authoritative programme for section 2,
  including lectures and seminars 4--8 and their learning outcomes.
- `adaptation_course.tex` is the main LaTeX entry point for the full course
  handbook; `tex/` contains its canonical content.
- `tex/preamble.tex` contains shared packages, page geometry, spacing, and LaTeX settings.
- `tex/frontmatter.tex` contains the title page, annotation, usage notes, and table of contents.
- `tex/chapters/chapter1_math_foundations.tex` contains the first chapter content.
- `tex/chapters/chapter2_arch_os_tools.tex` includes the prepared lecture 4
  from `tex/lectures/lecture04_*.tex` and the outlines for subsequent sessions.
- `tex/backmatter/references.tex` contains the bibliography / used literature section.
- `tex/appendices/appendices.tex` contains appendices and compact reference material.
- `slides/lecture02-original/index.html` is an active alternative presentation
  for lecture 2. It preserves the structure of the lecture that was already
  delivered and is built and published alongside the main presentation.
- `examples/` contains external methodological examples and is not a source of
  course requirements.
- `demos/lecture04/` contains executable C/NASM examples for lecture 4;
  `make lecture4-check` verifies them in a Linux x86-64 Docker container.
- `slides/lecture04-journal/` presents computer architecture through a
  bare-metal gradebook running in QEMU. Its companion
  `demos/lecture04-journal/` contains six 16-bit NASM/BIOS/QEMU checkpoints;
  C in this presentation explains algorithms only.
  `tex/lectures/lecture04_journal.tex` is a supplementary handbook section.
- `legacy/` contains historical or superseded materials. It is for explicit
  historical comparison only and must not be used as an active source.
- `Dockerfile` defines the Docker image used for LaTeX builds.
- `Makefile` provides the local Docker-based build target.
- `.github/workflows/build-pdf.yml` builds the PDF in GitHub Actions, uploads versioned artifacts, publishes the latest master PDF to GitHub Pages, and attaches release PDFs to GitHub Releases.

### Source of truth

When sources disagree, use this order:

1. `pud_adaptation_course.tex` for the programme and outcomes of section 2.
2. The canonical files under `tex/` and the main entry point
   `adaptation_course.tex` for the handbook text.
3. `slides/lectureNN/index.html` for editable lecture presentations.
4. `slides/theme/`, `slides/presentations.json`, and `Makefile` for the
   presentation system and build contract.
5. `docs/superpowers/` for historical design decisions and implementation
   plans, not for current course requirements.

Do not use files under `legacy/` to decide current content. If a legacy file is
needed for historical comparison, state that explicitly in the change or plan.

## Content Guidelines

- Target beginners who may lack confidence with number systems, memory representation, architecture, OS basics, Linux, build tools, and version control.
- Explain concepts step by step, but keep the connection to programming, C, memory, CPU behavior, and NASM visible.
- Prefer precise, concrete examples over abstract exposition.
- Verify all numerical examples, bit manipulations, floating-point examples, and base conversions before changing them.
- Do not silently remove uncertain or draft fragments. If a section is incomplete or questionable, either fix it with verification or mark the issue clearly.
- Preserve the lecture/seminar structure where possible.
- Use Russian terminology with English equivalents when it helps students recognize programming literature and tooling.

## LaTeX Style

The main document uses:

- `\documentclass[a4paper,14pt]{extreport}`

Shared LaTeX settings live in `tex/preamble.tex` and currently use:

- UTF-8 input with Russian Babel
- `T2A` font encoding
- `amsmath`, `amssymb`, `amsthm`
- `graphicx`, `hyperref`, `geometry`, `listings`, `xcolor`, `setspace`
- `\onehalfspacing`
- `\setcounter{secnumdepth}{-3}`

Keep the existing style unless there is a clear reason to change it.

Chapter files under `tex/chapters/` are included fragments. Do not add `\documentclass`, `\usepackage`, `\begin{document}`, `\maketitle`, `\tableofcontents`, or `\end{document}` to chapter files.

Use consistent notation:

- `$1010_2$`, `$A9_{16}$`, `$250_{10}$` for bases.
- `\texttt{...}` for code, bit patterns, commands, and machine representations.
- `float32`, `double`, `IEEE 754`, `CF`, `OF`, `ZF`, `SF` consistently.

## Build Policy

Do not require a local TeX installation on the host machine.

Builds must run inside Docker containers, including local builds, so contributors do not need to install a heavy TeX environment directly into the system.

Use `make pdf` to build the full document locally through Docker.

The intended full-document build target is `adaptation_course.tex`. The PUD and
practice handbook have separate targets, `pud-pdf` and `practice-pdf`.
Nothing under `legacy/` is a build target.

The Docker build uses `latexmk` and a TeX environment with Russian language support.

Generated artifacts such as PDFs, `.aux`, `.log`, `.toc`, `.out`, `.fls`, `.fdb_latexmk`, and temporary build directories should not be committed unless the user explicitly asks to publish generated PDFs.

## Lecture Presentations

For every lecture, prepare a presentation in both formats: Reveal.js HTML and PDF.

- Treat the Reveal.js version as the editable source of the lecture slides.
- Export the PDF from the same Reveal.js source so the content, order, and visual style stay synchronized.
- Keep lecture presentations in the shared course style: 16:9 layout, dark blue background, light text, turquoise accents, Carlito for prose, and a monospace font for code, bit patterns, commands, and machine representations.
- Reuse the common assets and theme under `slides/theme/` (`course.css`, `course.js`, title/content frames) instead of duplicating presentation-specific styling.
- Preserve readability for first-year students: large text, concise slide content, concrete examples, and speaker notes for detailed explanations.
- Ensure the static PDF remains useful on its own: important content must be visible without relying only on Reveal.js interactions or hidden fragments.
- Keep tables, formulas, code blocks, bit layouts, callouts, slide footers, and optional/supplementary slides visually consistent with the shared theme.
- When changing lecture slides, rebuild and verify both the Reveal.js HTML and the PDF through the Docker-based slide build.

## Verification

Verify LaTeX changes by building in Docker with `make pdf`.

Check at least:

- LaTeX exits successfully.
- Table of contents is generated correctly.
- Russian text renders correctly.
- There are no obvious broken formulas, listings, or encoding issues.
- Important warnings are reviewed, especially missing references, missing files, and overfull boxes in edited areas.

For subject-matter changes, verify calculations manually or with small scripts/calculations. Do not trust generated mathematical examples without checking.

## Editing Rules

- Make small, focused changes.
- Read the relevant surrounding section before editing.
- Do not rewrite large parts of the course unless explicitly asked.
- Preserve the educational intent for first-year students.
- Ask the user before deleting, merging, or declaring one `.tex` file obsolete.
- When adding new chapters, place them under `tex/chapters/` and input them from `adaptation_course.tex`.
- Keep used literature in `tex/backmatter/references.tex` and compact reference material in `tex/appendices/appendices.tex`.
- Do not expose or duplicate editor-access external links in new files unless the user explicitly asks.
