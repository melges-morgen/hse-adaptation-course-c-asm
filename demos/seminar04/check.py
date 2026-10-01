"""Check observable results of seminar exercises on the actual QEMU machine."""

from pathlib import Path
import argparse
import importlib.util
import tempfile


ROOT = Path("build/seminar04")
loader = importlib.util.spec_from_file_location(
    "journal_checks", "demos/lecture04-journal/check.py")
assert loader and loader.loader
journal_checks = importlib.util.module_from_spec(loader)
loader.loader.exec_module(journal_checks)
Machine = journal_checks.Machine


def boot(stage, tmp, images, disk=None):
    return Machine(stage, tmp / "monitor.sock", disk, image_root=images)


def check_stage(stage, images, tmp, reference=False):
    disk = tmp / "grades.img"
    if stage == 6:
        with disk.open("wb") as stream:
            stream.truncate(1024 * 1024)
    m = boot(stage, tmp, images, disk if stage == 6 else None)
    try:
        if stage == 1:
            expected = "S01  grade 07"
            actual = m.vga_text(0xb8000, len(expected))
            assert actual == expected, f"First VGA record: expected {expected!r}, got {actual!r}"
        elif stage == 2:
            # VGA row 4, column 14: W2 of S01; each cell uses two bytes.
            expected = "--" if reference else "07"
            actual = m.vga_text(0xb8000 + 4 * 160 + 14 * 2, 2)
            assert actual == expected, f"S01 W2 on VGA: expected {expected!r}, got {actual!r}"
        elif stage in (3, 4):
            m.key("a", "GRADE S1 W1=10")
        elif stage == 5:
            m.key("0", "GRADE S1 W1=0 AVG=0.00")
            m.key("right", "GRADE S1 W2=-- AVG=0.00")
            m.key("1", "GRADE S1 W2=1 AVG=0.50")
            m.key("right", "GRADE S1 W3=-- AVG=0.50")
            m.key("1", "GRADE S1 W3=1 AVG=0.67")
            actual = m.vga_text(0xb8000 + 4 * 160 + 31 * 2, 5)
            assert actual == "00.67", f"S01 VGA average: expected '00.67', got {actual!r}"
        else:
            m.key("0", "GRADE S1 W1=0 AVG=0.00")
            m.key("right", "GRADE S1 W2=-- AVG=0.00")
            m.key("a", "GRADE S1 W2=10 AVG=5.00")
            m.key("s", "SAVED")
    finally:
        m.close()
    if stage == 6:
        assert disk.read_bytes()[512:516] == b"GR16"
        m = boot(6, tmp, images, disk)
        try:
            assert "LOADED" in m.boot_data
            m.key("right", "GRADE S1 W2=10 AVG=5.00")
        finally:
            m.close()
    print(f"Практика, этап {stage}: результат подтверждён в QEMU")


def check_homework(images, tmp):
    disk = tmp / "homework.img"
    with disk.open("wb") as stream:
        stream.truncate(1024 * 1024)
    m = boot(6, tmp, images, disk)
    try:
        m.key("0", "GRADE S1 W1=0 AVG=0.00")
        m.key("right", "GRADE S1 W2=-- AVG=0.00")
        m.key("a", "GRADE S1 W2=10 AVG=5.00")
        m.key("down", "GRADE S2 W2=-- AVG=--.--")
        m.key("1", "GRADE S2 W2=1 AVG=1.00")
        m.key("up", "GRADE S1 W2=10 AVG=5.00")
        m.key("c", "GRADE S1 W2=-- AVG=--.--")
        m.key("s", "SAVED")
    finally:
        m.close()
    m = boot(6, tmp, images, disk)
    try:
        assert "LOADED" in m.boot_data
        m.key("right", "GRADE S1 W2=-- AVG=--.--")
        m.key("down", "GRADE S2 W2=1 AVG=1.00")
    finally:
        m.close()
    print("Домашняя работа: очищена только выбранная строка, сохранение пережило перезапуск")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", type=int, choices=range(1, 7))
    parser.add_argument("--solution", action="store_true")
    parser.add_argument("--homework", action="store_true")
    args = parser.parse_args()
    images = ROOT / "solutions" if args.solution else ROOT
    if args.homework and not args.solution:
        parser.error("--homework requires --solution")
    if not args.homework and args.stage is None:
        parser.error("specify --stage or --homework")
    ROOT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=ROOT) as location:
        tmp = Path(location)
        if args.homework:
            check_homework(images, tmp)
        else:
            check_stage(args.stage, images, tmp)
