# Lab04 Results PDF Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a KR1-style PDF results report for the 32 members of BPI264 from the saved lab04 ODS.

**Architecture:** Read the ODS and roster, validate cached score cells against defense grade and report status, aggregate only numeric results, and generate a standalone XeLaTeX report. Build inside the existing Docker TeX image; leave source scores untouched and keep personal output under ignored `results/`.

**Tech Stack:** Python 3 standard library for ODF ZIP/XML, XeLaTeX in Docker, `pdfinfo`/`pdftotext` for verification.

## Global Constraints

- Source: `results/2026-autumn/ЛБ-4-ведомость-защиты-актуальная.ods` and local `groups/students.csv`.
- Scope: BPI264 only; 32 students, exclude BPI261.
- Grade categories: 0–3 «неуд.», 4–5 «удовл.», 6–7 «хор.», 8–10 «отл.».
- `results/` is ignored by Git; no personal data or generated PDF outside it.
- Docker-based TeX only; use the shared KR1 report colors and fonts.

---

### Task 1: Validate source and numerical summary

**Files:**
- Create: `scripts/build-lab04-results.py`
- Create: `tests/test_lab04_results.py`

**Interfaces:**
- Consumes: UTF-8 roster and ODF 1.2 spreadsheet with `table:number-columns-repeated`.
- Produces: parsed rows with group, subgroup, variant, date, report status, defense grade, and capped final grade.

- [ ] **Step 1:** Write tests for ODF repeated blank cells, blank grades, final-score cap, category boundaries, roster membership, and excluding the BPI261 row.
- [ ] **Step 2:** Run `python3 -m unittest discover -s tests -p test_lab04_results.py -v`; verify failures for missing parser/aggregator.
- [ ] **Step 3:** Implement parsing, validation, and aggregation in `scripts/build-lab04-results.py` with no hard-coded student data.
- [ ] **Step 4:** Rerun the focused unittest; verify all cases pass.

### Task 2: Render the PDF in Docker

**Files:**
- Modify: `scripts/build-lab04-results.py`
- Create locally: `results/2026-autumn/БПИ264/ЛБ-4/reports/ЛБ-4-results.tex` and `.pdf`

**Interfaces:**
- Consumes: validated rows/aggregates from Task 1 and the visual reference `groups/БПИ264/КР-1-results.tex`.
- Produces: report PDF with student register, categorical distribution, and subgroup/variant summary.

- [ ] **Step 1:** Generate standalone TeX in the local reports folder using the KR1 palette, Carlito and text escaped for LaTeX.
- [ ] **Step 2:** Run XeLaTeX inside the existing `adaptation-course-tex` Docker image; keep all output inside `results/`.
- [ ] **Step 3:** Verify the PDF with `pdfinfo`, `pdftotext`, source-to-PDF name checks, and images of the pages; review XeLaTeX warnings in edited areas.
