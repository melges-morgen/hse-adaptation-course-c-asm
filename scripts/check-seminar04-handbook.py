"""Check the three student-facing editions of the seminar 4 handbook."""

import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path


class VisibleText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def normalized(text):
    return " ".join(text.split())


def pdf_text(path):
    return normalized(subprocess.check_output(["pdftotext", str(path), "-"], text=True))


root = Path(sys.argv[1] if len(sys.argv) > 1 else "build")
html_path = root / "html/seminar04/index.html"
pdf_path = root / "pdf/seminar04/seminar04.pdf"
course_path = root / "pdf/adaptation_course.pdf"
html = html_path.read_text(encoding="utf-8")
assert 'lang="ru"' in html and "reveal.js" not in html.lower(), "Expected a readable Russian handbook"
parser = VisibleText()
parser.feed(html)
editions = (normalized(" ".join(parser.parts)), pdf_text(pdf_path), pdf_text(course_path))
for marker in ("Семинар №4", "Создайте образ пустой дискеты", "Форма отчёта для каждого изменения"):
    assert all(marker in edition for edition in editions), f"Missing {marker!r} in an edition"

info = subprocess.check_output(["pdfinfo", str(pdf_path)], text=True)
match = re.search(r"Page size:\s+([\d.]+) x ([\d.]+) pts", info)
assert match and abs(float(match[1]) - 595.28) < 1 and abs(float(match[2]) - 841.89) < 1, "Seminar PDF must be A4"

html_materials = root / "html/seminar04/materials"
pdf_materials = root / "pdf/seminar04/materials"
html_files = {path.relative_to(html_materials) for path in html_materials.rglob("*") if path.is_file()}
pdf_files = {path.relative_to(pdf_materials) for path in pdf_materials.rglob("*") if path.is_file()}
expected_files = {Path(name) for name in ("README.md", "hello.asm", "boot16.asm", "journal.asm", "memory.c", "memory.gdb")}
assert html_files == pdf_files == expected_files, f"Unexpected seminar materials: {html_files}, {pdf_files}"
for source in pdf_files:
    assert (html_materials / source).read_bytes() == (pdf_materials / source).read_bytes(), source
assert b"hello.asm" in (html_materials / "README.md").read_bytes()

basic_html = root / "html/seminar04/factorial/index.html"
basic_pdf = root / "pdf/seminar04/seminar04-factorial.pdf"
basic_parser = VisibleText()
html = basic_html.read_text(encoding="utf-8")
assert 'lang="ru"' in html
basic_parser.feed(html)
basic_editions = (normalized(" ".join(basic_parser.parts)), pdf_text(basic_pdf), editions[2])
for marker in ("вариант 1 (базовый)", "Напишите первую версию в nano", "Найдите ошибку в GDB"):
    assert all(marker.casefold() in edition.casefold() for edition in basic_editions), f"Missing {marker!r} in a basic edition"
for marker in ("Шаг 1. Остановитесь в функции", "Шаг 2. Выполняйте строки",
               "Шаг 3. Следите за произведением", "Шаг 4. Исследуйте стек и память",
               "Шаг 5. Найдите ошибку в условии"):
    assert all(marker.casefold() in edition.casefold() for edition in basic_editions), (
        f"Missing GDB walkthrough {marker!r} in a basic edition"
    )
for marker in ("вариант 2 (усложнённый)", "Создайте образ пустой дискеты"):
    assert all(marker.casefold() in edition.casefold() for edition in editions), f"Missing {marker!r} in an advanced edition"
for variant, variant_editions in (("basic", basic_editions), ("advanced", editions)):
    for marker in ("Порядок сдачи лабораторных работ", "На занятии", "К следующей лабораторной",
                   "В начале следующей лабораторной", "Во время следующей лабораторной",
                   "Последняя лабораторная"):
        assert all(marker.casefold() in edition.casefold() for edition in variant_editions), (
            f"Missing submission step {marker!r} in a {variant} edition"
        )
    assert all("PDF или HTML" in edition for edition in variant_editions), (
        f"Missing report delivery format in a {variant} edition"
    )
info = subprocess.check_output(["pdfinfo", str(basic_pdf)], text=True)
match = re.search(r"Page size:\s+([\d.]+) x ([\d.]+) pts", info)
assert match and abs(float(match[1]) - 595.28) < 1 and abs(float(match[2]) - 841.89) < 1, "Basic PDF must be A4"

pages = ET.fromstring(subprocess.check_output(["pdftotext", "-bbox-layout", str(basic_pdf), "-"])).findall(
    ".//{http://www.w3.org/1999/xhtml}page"
)
word_tag = ".//{http://www.w3.org/1999/xhtml}word"
table_start = next(i for i, page in enumerate(pages) if any(word.text == "Флаг" for word in page.findall(word_tag)))
table_top = min(float(word.attrib["yMin"]) for word in pages[table_start].findall(word_tag) if word.text == "Флаг")
table_end, table_bottom = next(
    (i, min(float(word.attrib["yMin"]) for word in page.findall(word_tag)
            if word.text == "-o" and (i > table_start or float(word.attrib["yMin"]) > table_top)) + 18)
    for i, page in enumerate(pages[table_start:], table_start)
    if any(word.text == "-o" and (i > table_start or float(word.attrib["yMin"]) > table_top)
           for word in page.findall(word_tag))
)
outside = []
for i in range(table_start, table_end + 1):
    page = pages[i]
    right_edge = float(page.attrib["width"]) - 56.7  # 2 cm right margin of the A4 PDF
    first_y = table_top if i == table_start else 0
    last_y = table_bottom if i == table_end else float(page.attrib["height"])
    outside.extend(word.text for word in page.findall(word_tag)
                   if first_y <= float(word.attrib["yMin"]) <= last_y
                   and float(word.attrib["xMax"]) > right_edge + 1)
assert not outside, f"GCC table crosses the standalone PDF's right margin: {outside}"

for format in ("html", "pdf"):
    folder = root / format / "seminar04/factorial/materials"
    assert {p.name for p in folder.iterdir()} == {"README.md", "input.txt"}
    assert (folder / "input.txt").read_text().strip() == "5"
assert (root / "html/seminar04/factorial/materials/input.txt").read_bytes() == (
    root / "pdf/seminar04/factorial/materials/input.txt"
).read_bytes()
with tempfile.TemporaryDirectory(prefix="seminar04-extract-") as temporary:
    for variant, expected in (("seminar04", expected_files),
                              ("seminar04/factorial", {Path("README.md"), Path("input.txt")})):
        for format in ("html", "pdf"):
            source = root / format / variant / "materials"
            name = variant.replace("/", "-") + "-" + format
            archive = shutil.make_archive(str(Path(temporary) / name), "zip", source)
            extracted = Path(temporary) / name
            shutil.unpack_archive(archive, extracted)
            assert {p.relative_to(extracted) for p in extracted.rglob("*") if p.is_file()} == expected
            for file in expected:
                assert (extracted / file).read_bytes() == (source / file).read_bytes()
log = (root / "latex/adaptation_course.log").read_text(encoding="utf-8", errors="replace")
assert "multiply defined" not in log and "duplicate ignored" not in log, "Duplicate labels in course PDF"
basic_log = log.split("(./build/latex/seminar04_factorial_body.tex", 1)[1].split(
    "(./build/latex/seminar04_body.tex", 1
)[0]
assert "Overfull \\hbox" not in basic_log, "Factorial variant has overfull lines in course PDF"
print("seminar04: both variants appear in HTML, A4 PDFs and course PDF; student bundles match — OK")
