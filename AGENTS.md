# AGENTS.md

## Project Overview

This repository contains materials for an adaptation course for first-year Software Engineering students at HSE.

The course is intended to close gaps left after school and prepare students for the course "Algorithms and Algorithmic Languages", which uses C and NASM assembly.

The materials are written in Russian. Keep the language of course content Russian unless explicitly asked otherwise.

## Repository Structure

- `Программа курса.md` contains the high-level course outline.
- `adaptation_course.tex` is the main LaTeX entry point for the full course document.
- `tex/preamble.tex` contains shared packages, page geometry, spacing, and LaTeX settings.
- `tex/frontmatter.tex` contains the title page, annotation, usage notes, and table of contents.
- `tex/chapters/chapter1_math_foundations.tex` contains the first chapter content.
- `tex/chapters/chapter2_arch_os_tools.tex` contains the second chapter outline and draft structure.
- `tex/backmatter/references.tex` contains the bibliography / used literature section.
- `tex/appendices/appendices.tex` contains appendices and compact reference material.
- `drafts/adaptation_course_combined_draft.tex` is a shorter combined draft. Do not treat it as canonical unless the user explicitly says so.
- `Dockerfile` defines the Docker image used for LaTeX builds.
- `Makefile` provides the local Docker-based build target.
- `.github/workflows/build-pdf.yml` builds the PDF in GitHub Actions, uploads versioned artifacts, publishes the latest master PDF to GitHub Pages, and attaches release PDFs to GitHub Releases.

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

The intended full-document build target is `adaptation_course.tex`. Draft files under `drafts/` are not build targets.

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
