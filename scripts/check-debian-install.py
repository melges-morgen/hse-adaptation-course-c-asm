"""Exercise the terminal lab's C program without installing an operating system."""

from pathlib import Path
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "supplementary/debian-install/reference/hello.c"
GUIDE = ROOT / "tex/supplementary/debian_install_body.tex"

code = SOURCE.read_text(encoding="utf-8")
text = GUIDE.read_text(encoding="utf-8")
assert "\\begin{verbatim}\n" + code.rstrip() + "\n\\end{verbatim}" in text, "The typed C program differs from the checked source"

with tempfile.TemporaryDirectory(prefix="debian-install-") as directory:
    binary = Path(directory) / "hello_c"
    subprocess.run(
        ["gcc", "-std=c11", "-Wall", "-Wextra", "-Werror", str(SOURCE), "-o", str(binary)],
        check=True, capture_output=True, text=True,
    )
    result = subprocess.run([str(binary)], check=True, capture_output=True, text=True)
    assert result.stdout == "Hello from C!\n" and not result.stderr and result.returncode == 0

print("debian-install: hello.c compiles, prints expected line and exits 0 — OK")
