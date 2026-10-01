"""The student's full journal must survive repeated preparation."""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from demos.seminar04.prepare import initialize, initialize_hello


ROOT = Path(__file__).resolve().parents[2]


class PreparationTest(unittest.TestCase):
    def test_copies_hello_without_overwriting_edits(self):
        with TemporaryDirectory() as temp:
            work = Path(temp) / "seminar04"
            initialize_hello(ROOT, work)
            hello = work / "hello.asm"
            self.assertIn("HELLO BIOS", hello.read_text(encoding="utf-8"))
            hello.write_text("; мой вариант\n", encoding="utf-8")
            initialize_hello(ROOT, work)
            self.assertEqual(hello.read_text(encoding="utf-8"), "; мой вариант\n")

    def test_copies_complete_journal_without_overwriting_edits(self):
        with TemporaryDirectory() as temp:
            work = Path(temp) / "seminar04"
            initialize(ROOT, work)
            journal = work / "journal.asm"
            original = journal.read_text(encoding="utf-8")
            self.assertIn("save_grades:", original)
            self.assertIn("redraw:", original)
            journal.write_text(original + "\n; МОЯ ПРАВКА\n", encoding="utf-8")
            initialize(ROOT, work)
            self.assertTrue(journal.read_text(encoding="utf-8").endswith("; МОЯ ПРАВКА\n"))
            self.assertFalse(journal.is_symlink())


if __name__ == "__main__":
    unittest.main()
