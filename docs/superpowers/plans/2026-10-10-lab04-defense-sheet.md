# Lab04 Defense Sheet Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a local LibreOffice Calc ODS sheet for recording defense grades of students whose lab 4 reports were collected.

**Architecture:** Extract dates from the preserved file mtimes, match surnames against `groups/students.csv`, use manually confirmed QEMU/Factorial classifications, and write an editable ODS spreadsheet in the Git-ignored semester directory. Keep grade cells empty and mark uncertain identities and filenames on a notes sheet.

**Tech Stack:** Python 3 standard library (`csv`, `pathlib`, `zipfile`, `xml.etree.ElementTree`), ODF 1.2 Spreadsheet XML.

## Global Constraints

- Input: 26 report files in `results/2026-autumn/*/ЛБ-4/source/`; exclude editor lock files.
- Output: `results/2026-autumn/ЛБ-4-ведомость-защиты.ods`, entirely ignored by Git.
- Table: one row per student; name, group, QEMU/Factorial, local file date `ДД.ММ.ГГГГ`, blank defense grade.
- Explicitly distinguish file metadata dates from Telegram message dates, and mark unknown identity and mismatched report filenames.

---

### Task 1: Create and validate the editable spreadsheet

**Files:**
- Create: `results/2026-autumn/ЛБ-4-ведомость-защиты.ods` (local only)
- Temporary generator: `/home/melges/.opencode/tmp/opencode/lab04-defense-sheet-ods.py` (not tracked)

**Interfaces:**
- Consumes: report basenames/mtimes and `groups/students.csv`.
- Produces: one ODS file with 26 table rows and no grades.

- [ ] **Step 1: Confirm inputs and existing destination**

Inspect `results/2026-autumn/` and list the 26 regular PDF/DOCX/ODT reports under group-specific `ЛБ-4/source/`; check whether the intended output filename already exists, to avoid overwriting it.

- [ ] **Step 2: Implement a one-off generator**

Use a filename-to-surname-and-variant mapping for all 26 reports, resolve unique full names by group from `groups/students.csv`, keep the unassigned «антон» as an explicit exception, and read the date with `datetime.fromtimestamp(path.stat().st_mtime)`. Build ODS ZIP members `mimetype`, `META-INF/manifest.xml`, `content.xml`, and `styles.xml` using Python standard library; use ODF spreadsheet cells with borders, repeatable header, native date values, and blank fifth cell. Place caveats on a second sheet.

- [ ] **Step 3: Produce ODS**

Run `python3 /home/melges/.opencode/tmp/opencode/lab04-defense-sheet-ods.py` from the repository root. Expect a single spreadsheet in `results/2026-autumn/` with 26 student rows, sorted by group and surname.

- [ ] **Step 4: Check document contents and integrity**

Open ODS ZIP, parse `content.xml` and `styles.xml`, count rows and headers on the first sheet, compare names/variant/date against each input file's mapping and mtime, check that grade text is blank, and run `git check-ignore -v 'results/2026-autumn/ЛБ-4-ведомость-защиты.ods'`. Once validated and confirmed the ODT is the unchanged draft from this task, remove the obsolete ODT.
