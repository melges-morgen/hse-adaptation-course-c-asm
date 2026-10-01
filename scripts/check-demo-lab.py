"""Verify the demonstrated mistake, GDB observations and corrected sums."""

from pathlib import Path
import re
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / "supplementary/lab-report"
BROKEN = (BASE / "reference/sum-error.c").read_text(encoding="utf-8")
FIXED = (BASE / "reference/sum.c").read_text(encoding="utf-8")
GUIDE = (BASE / "README.md").read_text(encoding="utf-8")
REPORT = (BASE / "report.md").read_text(encoding="utf-8")
assert "```c\n" + BROKEN.rstrip() + "\n```" in GUIDE, "The typed example differs from the checked source"
assert FIXED == BROKEN.replace("a - b", "a + b"), "The fix must change only the operation"

with tempfile.TemporaryDirectory(prefix="demo-lab-") as directory:
    work = Path(directory)
    source = work / "sum.c"
    binary = work / "sum"

    def compile_and_run(code):
        source.write_text(code, encoding="utf-8")
        subprocess.run(
            ["gcc", "-std=c11", "-Wall", "-Wextra", "-g", "-O0", "sum.c", "-o", "sum"],
            cwd=work, check=True, capture_output=True, text=True,
        )
        return subprocess.run([str(binary)], cwd=work, check=True, capture_output=True, text=True)

    first = compile_and_run(BROKEN)
    assert first.stdout.strip() == "Сумма: 2" and first.returncode == 0 and not first.stderr
    gdb = subprocess.run(
        ["gdb", "-q", "--batch", "-ex", "break sum.c:7", "-ex", "run",
         "-ex", "print a", "-ex", "print b", "-ex", "next", "-ex", "print result", str(binary)],
        cwd=work, check=True, capture_output=True, text=True,
    )
    assert re.findall(r"\$\d+ = (-?\d+)", gdb.stdout) == ["7", "5", "2"], gdb.stdout

    for a, b, expected in ((7, 5, 12), (0, 5, 5), (-3, 5, 2)):
        code = FIXED.replace("int a = 7;", f"int a = {a};").replace("int b = 5;", f"int b = {b};")
        result = compile_and_run(code)
        assert result.stdout.strip() == f"Сумма: {expected}" and result.returncode == 0 and not result.stderr
        assert f"Сумма: {expected}" in REPORT

assert "Сумма: 2" in REPORT and "print result" in REPORT
print("demo lab: wrong answer, GDB observations and corrected cases — OK")
