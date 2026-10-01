"""Inspect a GR16 sector by LBA; optionally damage only a new disk copy."""

from pathlib import Path
import argparse


def inspect(image: Path, lba: int = 1) -> dict:
    disk = image.read_bytes()
    offset = lba * 512
    if lba < 0 or len(disk) < offset + 512:
        raise ValueError(f"В образе нет сектора LBA {lba}")
    sector = disk[offset:offset + 512]
    return {
        "lba": lba, "byte_offset": offset,
        "signature": sector[:4].decode("ascii", errors="replace"),
        "version": sector[4], "students": sector[5], "works": sector[6],
        "first_grades": list(sector[8:12]),
        "stored_checksum": int.from_bytes(sector[72:74], "little"),
        "computed_checksum": sum(sector[:72]) & 0xffff,
    }


def corrupt_copy(source: Path, destination: Path, lba: int = 1) -> None:
    if source.resolve() == destination.resolve():
        raise ValueError("Источник и копия должны иметь разные имена")
    disk = bytearray(source.read_bytes())
    offset = lba * 512
    if lba < 0 or len(disk) < offset + 512 or disk[offset:offset + 4] != b"GR16":
        raise ValueError(f"Сначала сохраните оценки: нужен сектор GR16 по LBA {lba}")
    disk[offset + 8] ^= 1  # изменить первую оценку, оставив прежнюю сумму
    with destination.open("xb") as result:
        result.write(disk)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument("--lba", type=int, default=1)
    parser.add_argument("--corrupt-copy", type=Path, metavar="NEW_IMAGE")
    args = parser.parse_args()
    if args.corrupt_copy:
        corrupt_copy(args.image, args.corrupt_copy, lba=args.lba)
        print(f"Испорчена только новая копия: {args.corrupt_copy}")
    for name, value in inspect(args.image, lba=args.lba).items():
        print(f"{name}: {value}")
