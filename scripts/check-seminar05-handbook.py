"""Verify that all student editions of seminar 5 contain the complete lab."""

import re
import shutil
import subprocess
import sys
import tempfile
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


root = Path(sys.argv[1] if len(sys.argv) > 1 else "build")
html = (root / "html/seminar05/index.html").read_text(encoding="utf-8")
assert re.search(r"lang=['\"]ru['\"]", html), "Expected a Russian HTML handbook"
parser = VisibleText()
parser.feed(html)
standalone_pdf = root / "pdf/seminar05/seminar05.pdf"
editions = (
    normalized(" ".join(parser.parts)),
    normalized(subprocess.check_output(["pdftotext", str(standalone_pdf), "-"], text=True)),
    normalized(subprocess.check_output(["pdftotext", str(root / "pdf/adaptation_course.pdf"), "-"], text=True)),
)
for marker in ("Часть I. Первый локальный репозиторий Git",
               "Ветка и слияние", "Локальный удалённый репозиторий",
               "Часть II. Коды возврата, процессы и изоляция",
               "Отчёт", "Почему одинаковое число виртуального адреса"):
    assert all(marker.casefold() in edition.casefold() for edition in editions), marker

info = subprocess.check_output(["pdfinfo", str(standalone_pdf)], text=True)
match = re.search(r"Page size:\s+([\d.]+) x ([\d.]+) pts", info)
assert match and abs(float(match[1]) - 595.28) < 1 and abs(float(match[2]) - 841.89) < 1

expected = {"README.md", "status_demo.c", "isolation_demo.c"}
with tempfile.TemporaryDirectory(prefix="seminar05-extract-") as temp:
    for format in ("html", "pdf"):
        materials = root / format / "seminar05/materials"
        assert {p.name for p in materials.iterdir()} == expected
        archive = shutil.make_archive(str(Path(temp) / format), "zip", materials)
        extracted = Path(temp) / format
        shutil.unpack_archive(archive, extracted)
        assert {p.name for p in extracted.iterdir()} == expected
        for filename in expected:
            assert (extracted / filename).read_bytes() == (materials / filename).read_bytes()
            other = root / ("pdf" if format == "html" else "html") / "seminar05/materials" / filename
            assert (materials / filename).read_bytes() == other.read_bytes()

log = (root / "latex/adaptation_course.log").read_text(encoding="utf-8", errors="replace")
section = log.split("(./tex/seminars/seminar05_body.tex", 1)[1].split(")", 1)[0]
assert "Overfull \\hbox" not in section, "Overfull box in seminar 5"
print("seminar05: standalone HTML/PDF, course PDF and extracted student bundles — OK")
