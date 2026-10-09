"""Build the lecture 5 example and verify its observable process interfaces."""
from pathlib import Path
import os
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "demos/lecture05/process_demo.c"


def run(name, command, **kwargs):
    result = subprocess.run(command, text=True, capture_output=True, **kwargs)
    if result.returncode != 0:
        raise AssertionError(
            f"{name}: exit {result.returncode}\nstdout={result.stdout!r}\nstderr={result.stderr!r}"
        )
    print(f"OK: {name}")
    return result


with tempfile.TemporaryDirectory(prefix="lecture05-") as temp:
    program = Path(temp) / "process-demo"
    run("compile with warnings", ["gcc", "-std=c11", "-Wall", "-Wextra", "-Werror", str(SOURCE), "-o", str(program)])

    env = os.environ.copy()
    env["COURSE_MESSAGE"] = "test environment"
    result = run("arguments and environment", [str(program), "first", "two words"], input="", env=env)
    assert "argv[1]=first\n" in result.stdout
    assert "argv[2]=two words\n" in result.stdout
    assert "COURSE_MESSAGE=test environment\n" in result.stdout
    assert "завершение с кодом 0" in result.stderr
    print("OK: stdout and stderr are separate")

    result = run("stdin copied to stdout", [str(program)], input="строка 1\nстрока 2\n")
    assert result.stdout.endswith("строка 1\nстрока 2\n")

    result = subprocess.run([str(program), "--status=7"], text=True, capture_output=True)
    assert result.returncode == 7, result.returncode
    assert "завершение с кодом 7" in result.stderr
    print("OK: requested non-zero exit status")

    result = subprocess.run([str(program), "--status=126"], text=True, capture_output=True)
    assert result.returncode == 2, result.returncode
    assert "ожидается код от 0 до 125" in result.stderr
    print("OK: invalid status rejected")

print("Лекция №5: проверки демонстрационной программы пройдены.")
