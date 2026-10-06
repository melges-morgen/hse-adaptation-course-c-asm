"""Check both standalone demo handbooks and their appearance in the course."""

from html.parser import HTMLParser
from pathlib import Path
import re
import subprocess
import sys


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
course = pdf_text(root / "pdf/adaptation_course.pdf")
for html_name, pdf_name, markers in (
    ("index.html", "demo-lab.pdf", ("Демонстрационная лабораторная: сумма двух чисел",
                                        "Отправьте преподавателю отчёт в формате PDF или HTML",
                                        "Сумма: 2", "Сумма: 12")),
    ("report.html", "example-report.pdf", ("Пример отчёта: сумма двух чисел",
                                             "Иванов Иван", "Сумма: 2", "Сумма: 12")),
):
    html = (root / "html/lab-report" / html_name).read_text(encoding="utf-8")
    assert re.search(r"lang=['\"]ru['\"]", html), html_name
    parser = VisibleText()
    parser.feed(html)
    pdf = root / "pdf/lab-report" / pdf_name
    editions = (normalized(" ".join(parser.parts)), pdf_text(pdf), course)
    for marker in markers:
        assert all(marker in edition for edition in editions), f"{marker!r} missing in {pdf_name} edition"
    assert all("PDF или HTML" in edition for edition in editions), f"Report format missing in {pdf_name} edition"
    info = subprocess.check_output(["pdfinfo", str(pdf)], text=True)
    match = re.search(r"Page size:\s+([\d.]+) x ([\d.]+) pts", info)
    assert match and abs(float(match[1]) - 595.28) < 1 and abs(float(match[2]) - 841.89) < 1, pdf_name

assert course.index("Демонстрационная лабораторная: сумма двух чисел", course.index("Дополнительные материалы")) < (
    course.index("Пример отчёта: сумма двух чисел", course.index("Дополнительные материалы"))
) < course.index("Используемая литература", course.index("Дополнительные материалы"))

log = (root / "latex/adaptation_course.log").read_text(encoding="utf-8", errors="replace")
assert "multiply defined" not in log and "duplicate ignored" not in log, "Duplicate section anchor in course PDF"
fragment = log.split("(./tex/supplementary/lab_report_body.tex", 1)[1].split(
    "(./tex/backmatter/references.tex", 1
)[0]
assert "Overfull \\hbox" not in fragment, "Demo/report fragment contains overfull text"
print("demo lab: HTML, A4 PDFs and course PDF contain the lab and sample report — OK")
