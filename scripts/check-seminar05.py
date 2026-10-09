"""Compile and exercise the student-facing seminar 5 programs on Linux."""

import re
import shutil
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "demos/seminar05"


def run(*args, **kwargs):
    return subprocess.run(args, text=True, capture_output=True, timeout=20, **kwargs)


with tempfile.TemporaryDirectory(prefix="seminar05-") as directory:
    executable = Path(directory)
    for name in ("status_demo", "isolation_demo"):
        subprocess.run(
            ["gcc", "-std=c11", "-Wall", "-Wextra", "-Werror", "-O0",
             str(SOURCES / f"{name}.c"), "-o", str(executable / name)],
            check=True, timeout=30,
        )

    status = executable / "status_demo"
    for argument, expected in (("--code=0", 0), ("--code=7", 7),
                               ("--code=125", 125), ("--code=oops", 2),
                               ("--code=-1", 2)):
        result = run(str(status), argument)
        assert result.returncode == expected, (argument, result)
        if expected == 2:
            assert "ошибка" in result.stderr.lower(), result
        else:
            assert f"код {expected}" in result.stdout, result

    isolated = executable / "isolation_demo"
    result = run(str(isolated))
    assert result.returncode == 0, result
    parent = re.search(r"parent-before pid=(\d+) address=(0x[\da-f]+) value=(\d+)", result.stdout)
    child = re.search(r"child pid=(\d+) address=(0x[\da-f]+) value=(\d+)", result.stdout)
    after = re.search(r"parent-after pid=(\d+) address=(0x[\da-f]+) value=(\d+)", result.stdout)
    assert parent and child and after, result.stdout
    assert parent[1] == after[1] != child[1], result.stdout
    assert parent[2] == after[2] == child[2], result.stdout
    assert (parent[3], child[3], after[3]) == ("41", "99", "41"), result.stdout
    assert "child-exit=7" in result.stdout, result.stdout

    observing = subprocess.Popen([str(isolated), "--observe"], stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, text=True)
    try:
        assert observing.stdout is not None
        lines = [observing.stdout.readline() for _ in range(3)]
        observed_child = re.search(r"child pid=(\d+)", "".join(lines))
        assert observed_child, lines
        child_pid = int(observed_child[1])
        assert observing.poll() is None, "Observation window closed before ps"
        processes = run("ps", "-p", str(child_pid), "-o", "pid=,ppid=,stat=,comm=")
        assert processes.returncode == 0 and str(child_pid) in processes.stdout, processes
        stdout, stderr = observing.communicate(timeout=20)
        assert observing.returncode == 0 and "child-exit=7" in stdout, (lines, stdout, stderr)
    finally:
        if observing.poll() is None:
            observing.kill()
            observing.communicate()

    project = executable / "student-project"
    project.mkdir()
    for name in ("README.md", "status_demo.c", "isolation_demo.c"):
        source = SOURCES / "materials" / name if name == "README.md" else SOURCES / name
        shutil.copyfile(source, project / name)
    (project / ".gitignore").write_text("/status_demo\n/isolation_demo\n/input.txt\n/result.txt\n/error.txt\n*.o\n")

    def git_at(directory, *arguments):
        return subprocess.run(["git", *arguments], cwd=directory, check=True,
                              capture_output=True, text=True, timeout=20).stdout

    def git(*arguments):
        return git_at(project, *arguments)

    git("init", "-q")
    git("config", "--local", "user.name", "Lab Student")
    git("config", "--local", "user.email", "student@example.invalid")
    git("add", "README.md", "status_demo.c", "isolation_demo.c", ".gitignore")
    git("commit", "-qm", "Add starting files for lab 5")
    subprocess.run(["gcc", "-std=c11", "-Wall", "-Wextra", "-O0",
                    "isolation_demo.c", "-o", "isolation_demo"], cwd=project, check=True)
    assert not git("status", "--short"), "Build product should be ignored"

    (project / "scratch.txt").write_text("temporary\n")
    (project / "debug.log").write_text("debug\n")
    git("add", "scratch.txt")
    assert "scratch.txt" in git("status", "--short")
    git("rm", "--cached", "scratch.txt")
    assert (project / "scratch.txt").exists()
    with (project / ".gitignore").open("a") as ignored:
        ignored.write("/scratch.txt\n*.log\n")
    assert "scratch.txt" in git("check-ignore", "scratch.txt", "debug.log")
    with (project / "README.md").open("a") as readme:
        readme.write("Trial line\n")
    git("restore", "README.md")
    assert "Trial line" not in (project / "README.md").read_text()

    base_branch = git("branch", "--show-current").strip()
    assert base_branch
    git("switch", "-c", "feature-notes")
    (project / "notes.txt").write_text("Git and processes\n")
    git("add", "notes.txt", ".gitignore")
    git("commit", "-qm", "Add notes and ignore temporary files")
    git("switch", base_branch)
    assert not (project / "notes.txt").exists()
    git("merge", "--no-ff", "feature-notes", "-m", "Merge feature notes")
    git("branch", "-d", "feature-notes")
    assert (project / "notes.txt").read_text() == "Git and processes\n"

    remote = executable / "lab05-remote.git"
    clone = executable / "lab05-copy"
    git("init", "--bare", str(remote))
    git("remote", "add", "origin", str(remote))
    git("push", "-u", "origin", base_branch)
    git("clone", "-b", base_branch, str(remote), str(clone))
    git_at(clone, "config", "--local", "user.name", "Lab Student")
    git_at(clone, "config", "--local", "user.email", "student@example.invalid")
    with (clone / "notes.txt").open("a") as note:
        note.write("Copied work\n")
    git_at(clone, "add", "notes.txt")
    git_at(clone, "commit", "-qm", "Update note in clone")
    git_at(clone, "push", "origin", base_branch)
    git("pull", "--ff-only", "origin", base_branch)
    assert "Copied work" in (project / "notes.txt").read_text()

    source = project / "isolation_demo.c"
    text = source.read_text()
    assert text.count("value = 99;") == 1
    source.write_text(text.replace("value = 99;", "value = 73;"))
    assert "99" in git("diff") and "73" in git("diff")
    git("add", "isolation_demo.c")
    git("commit", "-qm", "Change child value in isolation experiment")
    subprocess.run(["gcc", "-std=c11", "-Wall", "-Wextra", "-O0",
                    "isolation_demo.c", "-o", "isolation_demo"], cwd=project, check=True)
    changed = run(str(project / "isolation_demo"))
    assert changed.returncode == 0 and "value=73" in changed.stdout and "value=41" in changed.stdout
    messages = git("log", "--format=%s").splitlines()
    assert messages[:3] == ["Change child value in isolation experiment", "Update note in clone",
                            "Merge feature notes"], messages
    assert len(messages) == 5 and set(messages[3:]) == {
        "Add notes and ignore temporary files", "Add starting files for lab 5"}, messages
    assert not git("status", "--short")

    with (project / "README.md").open("a") as readme:
        readme.write("Temporary note\n")
    git("stash", "push", "-m", "Temporary note", "--", "README.md")
    assert not git("status", "--short")
    git("stash", "pop")
    assert "Temporary note" in (project / "README.md").read_text()
    git("restore", "README.md")

    recovery = executable / "lab05-recovery"
    git("clone", ".", str(recovery))
    git_at(recovery, "config", "--local", "user.name", "Lab Student")
    git_at(recovery, "config", "--local", "user.email", "student@example.invalid")
    original_note = (recovery / "notes.txt").read_text()
    with (recovery / "notes.txt").open("a") as note:
        note.write("Trial\n")
    git_at(recovery, "add", "notes.txt")
    git_at(recovery, "commit", "-qm", "Trial note")
    git_at(recovery, "reset", "HEAD~1")
    assert "notes.txt" in git_at(recovery, "status", "--short")
    git_at(recovery, "add", "notes.txt")
    git_at(recovery, "commit", "-qm", "Trial again")
    git_at(recovery, "revert", "--no-edit", "HEAD")
    assert (recovery / "notes.txt").read_text() == original_note

print("seminar05: return codes, memory isolation, ps, branch/merge and local clone/push/pull — OK")
