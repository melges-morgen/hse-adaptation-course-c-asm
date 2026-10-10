"""Checks for the local lab 4 PDF generator, using invented students only."""

import importlib.util
from pathlib import Path
import unittest


MODULE = Path(__file__).resolve().parents[1] / "scripts/build-lab04-results.py"


def generator():
    if not MODULE.exists():
        raise AssertionError("PDF generator has not been implemented")
    spec = importlib.util.spec_from_file_location("lab04_results", MODULE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SHEET = '''<?xml version="1.0" encoding="UTF-8"?>
<office:document-content xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
 xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0"
 xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0">
<office:body><office:spreadsheet><table:table table:name="Защита ЛБ4">
<table:table-row>
 <table:table-cell><text:p>Альфа Тестовый</text:p></table:table-cell>
 <table:table-cell><text:p>БПИ264</text:p></table:table-cell>
 <table:table-cell table:number-columns-repeated="2"><text:p/></table:table-cell>
 <table:table-cell office:value-type="float" office:value="9"><text:p>9</text:p></table:table-cell>
 <table:table-cell><text:p>Не сдан</text:p></table:table-cell>
 <table:table-cell office:value-type="float" office:value="5"><text:p>5</text:p></table:table-cell>
</table:table-row>
<table:table-row>
 <table:table-cell><text:p>Бета Тестовая</text:p></table:table-cell>
 <table:table-cell><text:p>БПИ264</text:p></table:table-cell>
 <table:table-cell><text:p>QEMU</text:p></table:table-cell>
 <table:table-cell><text:p>09.10.2026</text:p></table:table-cell>
 <table:table-cell><text:p/></table:table-cell>
 <table:table-cell><text:p>Сдан</text:p></table:table-cell>
 <table:table-cell><text:p/></table:table-cell>
</table:table-row>
<table:table-row>
 <table:table-cell><text:p>Гамма Чужая</text:p></table:table-cell>
 <table:table-cell><text:p>БПИ261</text:p></table:table-cell>
 <table:table-cell><text:p>Factorial</text:p></table:table-cell>
 <table:table-cell><text:p>10.10.2026</text:p></table:table-cell>
 <table:table-cell office:value-type="float" office:value="8"><text:p>8</text:p></table:table-cell>
 <table:table-cell><text:p>Сдан</text:p></table:table-cell>
 <table:table-cell office:value-type="float" office:value="8"><text:p>8</text:p></table:table-cell>
</table:table-row>
</table:table></office:spreadsheet></office:body></office:document-content>'''.encode('utf-8')


class Lab04ResultsTest(unittest.TestCase):
    def test_odf_repeated_cells_and_capped_scores(self):
        rows = generator().parse_rows(SHEET)
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0]["name"], "Альфа Тестовый")
        self.assertEqual(rows[0]["variant"], "")
        self.assertEqual(rows[0]["date"], "")
        self.assertEqual((rows[0]["defense"], rows[0]["final"]), (9, 5))
        self.assertIsNone(rows[1]["defense"])
        self.assertIsNone(rows[1]["final"])

    def test_group_filter_keeps_unevaluated_students_and_excludes_other_group(self):
        mod = generator()
        roster = {
            "Альфа Тестовый": ("БПИ264", "1"),
            "Бета Тестовая": ("БПИ264", "2"),
        }
        rows = mod.select_group(mod.parse_rows(SHEET), roster, "БПИ264")
        self.assertEqual([(row["name"], row["subgroup"]) for row in rows],
                         [("Альфа Тестовый", "1"), ("Бета Тестовая", "2")])

    def test_all_category_edges_and_missing_scores(self):
        rows = [{"final": value, "report": "Сдан", "variant": "Factorial"}
                for value in (0, 3, 4, 5, 6, 7, 8, 10, None)]
        result = generator().summarize(rows)
        self.assertEqual(result["bins"], (2, 2, 2, 2))
        self.assertEqual((result["total"], result["graded"], result["ungraded"]), (9, 8, 1))
        self.assertAlmostEqual(result["mean"], 5.375)
        self.assertEqual(result["median"], 5.5)

    def test_inconsistent_cached_result_fails_instead_of_silent_misgrading(self):
        bad = SHEET.replace(b'office:value="5"><text:p>5', b'office:value="6"><text:p>6', 1)
        with self.assertRaisesRegex(ValueError, "Альфа"):
            generator().parse_rows(bad)


if __name__ == "__main__":
    unittest.main()
