"""Corruption exercises operate only on a new copy of the disk image."""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from demos.seminar04.scripts.inspect_disk import corrupt_copy, inspect


class DiskInspectionTest(unittest.TestCase):
    def test_corrupts_only_a_copy_and_makes_checksum_invalid(self):
        with TemporaryDirectory() as location:
            original = Path(location) / "grades.img"
            damaged = Path(location) / "damaged.img"
            disk = bytearray(1024 * 1024)
            sector = bytearray(512)
            sector[:8] = b"GR16\x01\x10\x04\x00"
            sector[8:72] = bytes([0xff] * 64)
            sector[8] = 0
            sector[72:74] = sum(sector[:72]).to_bytes(2, "little")
            disk[512:1024] = sector
            original.write_bytes(disk)
            report = inspect(original)
            self.assertEqual(report["signature"], "GR16")
            self.assertEqual(report["first_grades"], [0, 255, 255, 255])
            self.assertEqual(report["computed_checksum"], report["stored_checksum"])
            corrupt_copy(original, damaged)
            self.assertEqual(original.read_bytes(), disk)
            self.assertNotEqual(damaged.read_bytes()[520], disk[520])
            damaged_report = inspect(damaged)
            self.assertNotEqual(damaged_report["computed_checksum"], damaged_report["stored_checksum"])
            with self.assertRaises(FileExistsError):
                corrupt_copy(original, damaged)

    def test_inspects_and_corrupts_only_the_selected_lba(self):
        with TemporaryDirectory() as location:
            original = Path(location) / "grades.img"
            damaged = Path(location) / "damaged.img"
            disk = bytearray(1024 * 1024)
            sector = bytearray(512)
            sector[:8] = b"GR16\x01\x10\x04\x00"
            sector[8:72] = bytes([0xff] * 64)
            sector[8] = 12
            sector[72:74] = sum(sector[:72]).to_bytes(2, "little")
            disk[4096:4608] = sector
            original.write_bytes(disk)
            self.assertEqual(inspect(original, lba=8)["first_grades"][0], 12)
            corrupt_copy(original, damaged, lba=8)
            self.assertEqual(original.read_bytes()[4096:4608], sector)
            self.assertEqual(damaged.read_bytes()[520:524], b"\x00\x00\x00\x00")
            report = inspect(damaged, lba=8)
            self.assertNotEqual(report["stored_checksum"], report["computed_checksum"])


if __name__ == "__main__":
    unittest.main()
