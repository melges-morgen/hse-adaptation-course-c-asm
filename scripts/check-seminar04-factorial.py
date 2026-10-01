"""Exercise the C example and its documented GDB inspection in Linux."""

from pathlib import Path
import re
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "demos/seminar04/factorial/reference/factorial.c"
GUIDE = ROOT / "demos/seminar04/factorial/README.md"


with tempfile.TemporaryDirectory(prefix="seminar04-factorial-") as directory:
    binary = Path(directory) / "factorial"
    text = GUIDE.read_text(encoding="utf-8")
    assert text.count("```c\n" + SOURCE.read_text(encoding="utf-8").rstrip() + "\n```") == 1, (
        "The C block students type must match the checked C source"
    )
    subprocess.run(
        ["gcc", "-std=c11", "-Wall", "-Wextra", "-Wpedantic", "-Werror", "-g", "-O0", str(SOURCE), "-o", str(binary)],
        check=True,
    )
    for supplied, expected in (("0\n", "1"), ("1\n", "1"), ("5\n", "120"),
                               ("10\n", "3628800"), ("20\n", "2432902008176640000")):
        result = subprocess.run([str(binary)], input=supplied, text=True, capture_output=True, check=True)
        assert expected in result.stdout and not result.stderr, (supplied, result)
    for supplied in ("-1\n", "21\n", "abc\n", ""):
        result = subprocess.run([str(binary)], input=supplied, text=True, capture_output=True)
        assert result.returncode != 0 and result.stderr and not result.stdout, (supplied, result)

    gdb = subprocess.run(
        ["gdb", "-q", "--batch", "-ex", "break factorial", "-ex", 'run < "' + str(ROOT / "demos/seminar04/factorial/materials/input.txt") + '"',
         "-ex", "print n", "-ex", "next", "-ex", "print result", "-ex", "continue", str(binary)],
        text=True, capture_output=True, check=True,
    )
    assert "Breakpoint" in gdb.stdout and "120" in gdb.stdout, gdb.stdout

    trace = subprocess.run(
        ["gdb", "-q", "--batch", "-ex", "break factorial", "-ex", 'run < "' + str(ROOT / "demos/seminar04/factorial/materials/input.txt") + '"',
         "-ex", "print n", "-ex", "next", "-ex", "print result", "-ex", "info args", "-ex", "backtrace",
         "-ex", "watch result", "-ex", "continue", "-ex", "print result", "-ex", "continue",
         "-ex", "continue", "-ex", "continue", "-ex", "print sizeof(result)",
         "-ex", "x/8xb &result", "-ex", "continue", str(binary)],
        text=True, capture_output=True, check=True,
    )
    assert all(f"New value = {value}" in trace.stdout for value in (2, 6, 24, 120)), trace.stdout
    assert re.search(r"#0\s+factorial.*#1\s+.*main", trace.stdout, re.S), trace.stdout
    assert re.search(r"\$\d+ = 8\b", trace.stdout) and "0x78" in trace.stdout, trace.stdout

    broken = Path(directory) / "factorial.c"
    broken.write_text(SOURCE.read_text(encoding="utf-8").replace("i <= n", "i < n"), encoding="utf-8")
    broken_binary = Path(directory) / "factorial-broken"
    subprocess.run(["gcc", "-std=c11", "-Wall", "-Wextra", "-g", "-O0", str(broken), "-o", str(broken_binary)], check=True)
    result = subprocess.run([str(broken_binary)], input="5\n", text=True, capture_output=True, check=True)
    assert "factorial(5) = 24" in result.stdout, result.stdout
    broken_trace = subprocess.run(
        ["gdb", "-q", "--batch", "-ex", "break factorial.c:7",
         "-ex", 'run < "' + str(ROOT / "demos/seminar04/factorial/materials/input.txt") + '"',
         "-ex", "print i", "-ex", "continue", "-ex", "print i", "-ex", "continue",
         "-ex", "print i", "-ex", "continue", "-ex", "print i", "-ex", "continue", str(broken_binary)],
        text=True, capture_output=True, check=True,
    )
    assert re.findall(r"\$\d+ = (\d+)", broken_trace.stdout) == ["1", "2", "3", "4"], broken_trace.stdout
    assert "factorial(5) = 24" in broken_trace.stdout, broken_trace.stdout

    for heading in ("### Шаг 1. Остановитесь в функции", "### Шаг 2. Выполняйте строки",
                    "### Шаг 3. Следите за произведением", "### Шаг 4. Исследуйте стек и память",
                    "### Шаг 5. Найдите ошибку в условии"):
        assert heading in text, f"GDB walkthrough is missing {heading}"

print("seminar04 factorial: GCC, cases, stderr and GDB — OK")
