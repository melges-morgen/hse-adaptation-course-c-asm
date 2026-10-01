"""Verify the calculated constants against actual VGA, keyboard and disk I/O."""

import argparse
import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory


spec = importlib.util.spec_from_file_location("journal_checks", "demos/lecture04-journal/check.py")
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
Machine = module.Machine


def run(images: Path) -> None:
    with TemporaryDirectory() as location:
        tmp = Path(location)
        disk = tmp / "grades.img"
        with disk.open("wb") as stream:
            stream.truncate(1024 * 1024)
        m = Machine(6, tmp / "monitor.sock", disk, image_root=images)
        try:
            title = "COURSE GRADES - BIOS / NASM 16-BIT"
            location_vga = 0xb8000 + (80 * 2 + 5) * 2
            actual_title = m.vga_text(location_vga, len(title))
            assert actual_title == title, f"Заголовок: ожидалось {title!r}, получено {actual_title!r}"
            actual_attr = m.vga_bytes(location_vga, 1)[1]
            assert actual_attr == 0x1e, f"Цвет: ожидалось 1Eh, получено {actual_attr:02X}h"
            m.key("a", "GRADE S1 W1=12 AVG=12.00")
            m.key("right", "GRADE S1 W2=-- AVG=12.00")
            m.key("0", "GRADE S1 W2=0 AVG=6.00")
            m.key("q", "SAVED")
        finally:
            m.close()
        sector = disk.read_bytes()[4096:4608]
        assert sector[:4] == b"GR16", "Сигнатура должна находиться в секторе LBA 8"
        assert sector[8:10] == bytes([12, 0]), "На диск должны уйти оценки 12 и 0"
        assert disk.read_bytes()[512:516] != b"GR16", "Лишняя запись в старый сектор LBA 1"
        m = Machine(6, tmp / "monitor.sock", disk, image_root=images)
        try:
            assert "LOADED" in m.boot_data, "На старте должны загрузиться сохранённые оценки"
            m.key("right", "GRADE S1 W2=0 AVG=6.00")
            m.key("left", "GRADE S1 W1=12 AVG=6.00")
            m.key("1", "GRADE S1 W1=1 AVG=0.50")
            m.key("e", "LOADED")
            m.key("right", "GRADE S1 W2=0 AVG=6.00")
        finally:
            m.close()
    print("Лабораторная: позиция, цвет, ввод, среднее и LBA 8 — OK")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--image-root", type=Path, required=True)
    args = parser.parse_args()
    run(args.image_root)
