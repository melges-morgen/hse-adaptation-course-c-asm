# Student Results Storage Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a local, Git-ignored storage tree for source grade sheets and reports by semester, group, and assessment.

**Architecture:** Ignore the whole `results/` directory from the root `.gitignore`; create a sample empty tree locally and document its convention in a tracked root README. Keep shared generators, question templates, existing `groups/` data, and `dist/` unchanged.

**Tech Stack:** Git ignore rules, Markdown documentation, local directories.

## Global Constraints

- Semester names: `YYYY-spring` or `YYYY-autumn` (calendar year of the semester).
- Directory hierarchy: `results/<semester>/<group>/<assessment>/source/` and `reports/`.
- `results/` is entirely excluded from Git, including documentation placed inside it.
- No student submissions; no moves or edits to `groups/`, `dist/`, `assessments/`, or `scripts/`.

---

### Task 1: Local results tree and tracked instructions

**Files:**
- Modify: `.gitignore` (add `results/`)
- Modify: `README.md` (add a concise results section)
- Create locally (ignored): `results/2026-spring/БПИ264/КР-1/source/`, `results/2026-spring/БПИ264/КР-1/reports/`

**Interfaces:**
- Consumes: existing root documentation and Git ignore rules.
- Produces: documented local folder convention; no software API.

- [ ] **Step 1: Confirm precondition**

Run: `git status --short`
Expected: pre-existing user changes remain identifiable; no existing `results/` files to overwrite.

- [ ] **Step 2: Add ignore rule**

Append this line to `.gitignore`:

```gitignore
results/
```

- [ ] **Step 3: Document how to use the storage**

Add a `## Учёт успеваемости` section to `README.md` describing this example, `source/` as inputs, `reports/` as outputs, and the full Git exclusion:

```text
results/2026-spring/БПИ264/КР-1/{source,reports}/
```

Specify that `YYYY` is the calendar year of the semester and that work submissions are excluded; shared generators and templates stay in `scripts/` and `assessments/`.

- [ ] **Step 4: Create the empty example directories**

Use `mkdir -p` for `results/2026-spring/БПИ264/КР-1/source/` and `results/2026-spring/БПИ264/КР-1/reports/` after verifying their parent directory. Do not create example grades or placeholder student records.

- [ ] **Step 5: Verify exclusion and final diff**

Run: `git check-ignore -v 'results/2026-spring/БПИ264/КР-1/source/sheet.ods' 'results/2026-spring/БПИ264/КР-1/reports/summary.pdf' && git diff --check && git status --short`

Expected: both example paths match `.gitignore` `results/`; no whitespace errors; unrelated user edits are untouched. Confirm both actual directories exist via directory read.
