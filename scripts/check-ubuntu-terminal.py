"""Check that the supplementary Ubuntu guide appears in all three editions."""

import re
import subprocess
import sys
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
html_path = root / "html/ubuntu-terminal/index.html"
pdf_path = root / "pdf/ubuntu-terminal/ubuntu-terminal.pdf"
course_path = root / "pdf/adaptation_course.pdf"

html = html_path.read_text(encoding="utf-8")
assert re.search(r"lang=['\"]ru['\"]", html), "HTML must declare Russian"
parser = VisibleText()
parser.feed(html)
editions = (normalized(" ".join(parser.parts)), pdf_text(pdf_path), pdf_text(course_path))

for marker in (
    "Загрузка Ubuntu и первые шаги в терминале",
    "Выбор Ubuntu в GRUB 2",
    "Сохраните файл в nano",
    "Самостоятельная практика",
):
    assert all(marker in edition for edition in editions), f"Missing {marker!r} in an edition"

course = editions[2]
assert course.index("Дополнительные материалы", course.index("Основы Git")) < course.index(
    "Используемая литература", course.index("Дополнительные материалы", course.index("Основы Git"))
), "Supplementary materials must precede references"

info = subprocess.check_output(["pdfinfo", str(pdf_path)], text=True)
match = re.search(r"Page size:\s+([\d.]+) x ([\d.]+) pts", info)
assert match and abs(float(match[1]) - 595.28) < 1 and abs(float(match[2]) - 841.89) < 1, "Guide must be A4"

log = (root / "latex/adaptation_course.log").read_text(encoding="utf-8", errors="replace")
guide_log = log.split("(./tex/supplementary/ubuntu_terminal_body.tex", 1)[1].split(
    "(./tex/backmatter/references.tex", 1
)[0]
assert "Overfull \\hbox" not in guide_log, "Supplementary guide has overfull lines in the course PDF"
print("ubuntu-terminal: HTML, A4 PDF and course PDF contain the guide — OK")
