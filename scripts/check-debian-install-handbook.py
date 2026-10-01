"""Check the Debian lab in HTML, standalone A4 PDF and the course PDF."""

from html.parser import HTMLParser
from pathlib import Path
import re
import subprocess
import sys
import xml.etree.ElementTree as ET


class VisibleText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def normalized(text):
    return " ".join(text.split())


root = Path(sys.argv[1] if len(sys.argv) > 1 else "build")
source = Path("supplementary/debian-install/README.md").read_text(encoding="utf-8")
assert "чернов" not in source.casefold(), "Student guide still mentions the draft"
html = (root / "html/debian-install/index.html").read_text(encoding="utf-8")
assert 'lang="ru"' in html, "HTML language declaration missing"
parser = VisibleText()
parser.feed(html)
pdf = root / "pdf/debian-install/debian-install.pdf"
course_pdf = root / "pdf/adaptation_course.pdf"
pdf_text = lambda path: normalized(subprocess.check_output(["pdftotext", str(path), "-"], text=True))
editions = (normalized(" ".join(parser.parts)), pdf_text(pdf), pdf_text(course_pdf))
for marker in (
    "Установка Debian и знакомство с терминалом", "VirtualBox", "UTM",
    "Windows x86-64", "Mac с Apple Silicon", "Debian второй системой",
    "Mac Apple Silicon: Debian второй системой",
    "Плюсы", "Минусы", "Hello from C!", "PDF или HTML",
):
    assert all(marker.casefold() in edition.casefold() for edition in editions), f"Missing {marker!r} in an edition"

info = subprocess.check_output(["pdfinfo", str(pdf)], text=True)
match = re.search(r"Page size:\s+([\d.]+) x ([\d.]+) pts", info)
assert match and abs(float(match[1]) - 595.28) < 1 and abs(float(match[2]) - 841.89) < 1, "PDF must be A4"

ns = "{http://www.w3.org/1999/xhtml}"
pages = ET.fromstring(subprocess.check_output(["pdftotext", "-bbox-layout", str(pdf), "-"])).findall(
    ".//" + ns + "page"
)
outside = [word.text for page in pages for word in page.findall(".//" + ns + "word")
           if float(word.attrib["xMax"]) > float(page.attrib["width"]) - 56.7 + 4]
assert not outside, f"Text crosses standalone PDF's 2cm right margin: {outside[:10]}"

course = editions[2]
start = course.index("Дополнительные материалы")
assert course.index("Установка Debian и знакомство с терминалом", start) < course.index(
    "Загрузка Ubuntu и первые шаги в терминале", start
) < course.index("Используемая литература", start), "Supplementary chapter order is wrong"

log = (root / "latex/adaptation_course.log").read_text(encoding="utf-8", errors="replace")
section = log.split("(./build/latex/debian_install_body.tex", 1)[1].split(
    "(./tex/supplementary/ubuntu_terminal.tex", 1
)[0]
assert "Overfull \\hbox" not in section, "Course PDF has overfull text in the Debian lab"
assert "multiply defined" not in log and "duplicate ignored" not in log, "Duplicate PDF anchors"
print("debian-install: HTML, A4 PDF and course PDF contain the lab — OK")
