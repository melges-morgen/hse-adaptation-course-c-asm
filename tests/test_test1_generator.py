import csv
import re
import struct
import tempfile
import unittest
from fractions import Fraction as F
from pathlib import Path

from scripts.roster_to_csv import read_ods, write_roster
from scripts.test1.generator import generate, load_roster
from scripts.test1.render import render_document, truth_table
from scripts.test1.publish import produce
from scripts.test1.verify import verify_assignment


ROOT = Path(__file__).resolve().parents[1]


class RosterTest(unittest.TestCase):
    def test_color_based_subgroups_and_stable_ids(self):
        roster = read_ods(ROOT / 'groups/Пофамильный список групп.ods')
        self.assertEqual((len(roster), len({s['student_id'] for s in roster})), (len(roster), len(roster)))
        for group, counts in [('БПИ265', (17, 16)), ('БПИ2610', (15, 16))]:
            members = [s for s in roster if s['group'] == group]
            self.assertEqual(tuple(sum(s['subgroup'] == str(n) for s in members) for n in (1, 2)), counts)
            self.assertEqual(members[0]['student_id'], 'BPI' + group[3:] + '-001')
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'roster.csv'
            write_roster(path, roster)
            self.assertEqual(load_roster(path), roster)

    def test_duplicate_roster_id_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'roster.csv'
            with path.open('w', encoding='utf-8', newline='') as out:
                writer = csv.DictWriter(out, fieldnames=['student_id', 'group', 'subgroup', 'full_name'])
                writer.writeheader()
                writer.writerow(dict(student_id='BPI265-001', group='БПИ265', subgroup='1', full_name='А'))
                writer.writerow(dict(student_id='BPI265-001', group='БПИ265', subgroup='2', full_name='Б'))
            with self.assertRaisesRegex(ValueError, 'student_id'):
                load_roster(path)


class GenerationTest(unittest.TestCase):
    def test_reproducible_distinct_valid_levels(self):
        for level in (1, 2, 3):
            a = generate('BPI265-001', level, 'seed')
            b = generate('BPI265-001', level, 'seed')
            c = generate('BPI265-002', level, 'seed')
            self.assertEqual(a, b)
            self.assertNotEqual(a.fingerprint, c.fingerprint)
            self.assertNotEqual(a.seed, c.seed)
            self.assertRegex(a.seed, r'^[0-9a-f]{24}$')
            self.assertEqual(len(a.tasks), 8)
            self.assertEqual(sum(task.weight for task in a.tasks), 10)
            self.assertTrue(all(task.answer and task.solution and task.question for task in a.tasks))
            self.assertNotIn('разряда(ов)', a.tasks[5].question)

    def test_level_three_structural_properties(self):
        rounded_results = set()
        float_signs = set()
        sources, targets, integer_bases, fraction_bases, arithmetic_bases = set(), set(), set(), set(), set()
        given_codes, answer_codes, shifted_codes = set(), set(), set()
        for n in range(1, 65):
            variant = generate(f'BPI265-{n:03}', 3, 'seed')
            data = [task.data for task in variant.tasks]
            sources.add(data[0]['source_radix'])
            targets.add(data[0]['target_radix'])
            integer_bases.add(data[1]['radix'])
            fraction_bases.add(data[2]['radix'])
            arithmetic_bases.add(data[3]['radix'])
            given_codes.add(data[4]['given_radix'])
            answer_codes.add(data[4]['answer_radix'])
            shifted_codes.add(data[5]['answer_radix'])
            self.assertTrue(variant.tasks[2].data['rounded'].endswith('00'))
            rounded_results.add(variant.tasks[2].data['rounded'])
            self.assertEqual(variant.tasks[6].data['fraction_bits'], '0' * 23)
            float_signs.add(variant.tasks[6].data['sign'])
            self.assertEqual(variant.tasks[7].data['inputs'], 4)
            self.assertEqual(len(variant.tasks[7].data['truth']), 16)
            self.assertNotRegex(variant.tasks[7].data['formula'], r'\\(?:oplus|lor|land)[A-D]')
            self.assertIn('следующая цифра', variant.tasks[2].solution)
        self.assertGreaterEqual(len(rounded_results), 4)
        self.assertTrue(any(not value.endswith('.000') for value in rounded_results))
        self.assertGreaterEqual(len(sources), 3)
        self.assertGreaterEqual(len(targets), 3)
        self.assertGreaterEqual(len(integer_bases), 6)
        self.assertGreaterEqual(len(fraction_bases), 4)
        self.assertGreaterEqual(len(arithmetic_bases), 6)
        self.assertEqual(given_codes, {2, 8, 16})
        self.assertEqual(answer_codes, {2, 8, 16})
        self.assertEqual(shifted_codes, {2, 8, 16})
        self.assertEqual(float_signs, {'0', '1'})

    def test_independently_check_generated_numerical_answers(self):
        for level in (1, 2, 3):
            for n in range(1, 65):
                tasks = generate(f'BPI265-{n:03}', level, 'seed').tasks
                a, b, c, d, e, f, g, logic = (t.data for t in tasks)
                source_integer, source_fraction = a['representation'].split('.')
                self.assertEqual(F(int(source_integer, a['source_radix'])) +
                                 F(int(source_fraction, a['source_radix']), a['source_radix']**len(source_fraction)),
                                 F(a['integer']) + F(a['fraction']))
                target_integer, target_fraction = a['answer'].split('.')
                self.assertEqual(F(int(target_integer, a['target_radix'])) +
                                 F(int(target_fraction, a['target_radix']), a['target_radix']**len(target_fraction)),
                                 F(a['integer']) + F(a['fraction']))
                self.assertEqual(int(b['digits'], b['radix']), b['decimal'])
                frac = F(c['fraction'])
                whole, digits = c['rounded'].split('.')
                self.assertEqual(int(whole, c['radix']) * c['radix']**c['places'] + int(digits, c['radix']),
                                 round(frac * c['radix']**c['places']))
                radix = d['radix']
                def parse(number):
                    integer, fractional = number.split('.')
                    return F(int(integer, radix)) + F(int(fractional, radix), radix**len(fractional))
                self.assertEqual(parse(d['first']) - parse(d['second']), parse(d['result']))
                self.assertEqual(e['a'] + e['b'], e['result'])
                self.assertEqual(e['result'] & 65535, int(e['result_hex'], 16))
                self.assertEqual(e['result'] & 65535, int(e['given_code'], e['given_radix']))
                self.assertEqual(e['b'] & 65535, int(e['answer_code'], e['answer_radix']))
                self.assertEqual((f['a'] >> f['shift_a']) - (f['b'] << f['shift_b']), f['result'])
                self.assertEqual(f['result'] & 65535, int(f['code'], 16))
                self.assertEqual(f['a'], -int(f['a_digits'], f['a_radix']))
                self.assertEqual(f['b'], int(f['b_digits'], f['b_radix']))
                self.assertEqual(f['result'] & 65535, int(f['answer_code'], f['answer_radix']))
                self.assertEqual(struct.unpack('>I', struct.pack('>f', float(F(g['decimal']))))[0], int(g['word'], 16))
                self.assertEqual(len(logic['truth']), 2**logic['inputs'])

    def test_multidigit_subscripts_are_braced_in_generated_tex(self):
        unbraced = r'(?<!\\)[_^](?:[+-]?\d{2,}|[+-]\d+)'
        checked_radices = set()
        for level in (1, 2, 3):
            for number in range(1, 65):
                student_id = f'BPI265-{number:03}'
                variant = generate(student_id, level, 'kr1-2026-v3')
                radix = variant.tasks[3].data['radix']
                if radix >= 10:
                    checked_radices.add(radix)
                    marker = f'_{{{radix}}}'
                    self.assertEqual(variant.tasks[3].question.count(marker), 2)
                    self.assertIn(marker, variant.tasks[3].answer)
                    self.assertIn(marker, variant.tasks[3].solution)
                student = dict(student_id=student_id, group='БПИ265', subgroup='1', full_name='Тестовый Студент')
                for teacher in (False, True):
                    tex = render_document([(student, variant)], teacher)
                    self.assertNotRegex(tex, unbraced)
        self.assertEqual(checked_radices, {11, 12, 16})

    def test_document_variants_share_questions_and_include_real_schemes(self):
        student = dict(student_id='BPI265-001', group='БПИ265', subgroup='1', full_name='Тестовый Студент')
        variant = generate(student['student_id'], 3, 'seed')
        plain = render_document([(student, variant)], False)
        teacher = render_document([(student, variant)], True)
        self.assertEqual(plain.count('\\item'), 8)
        self.assertNotIn('уровень', plain.lower())
        self.assertNotIn('балл', plain.lower())
        self.assertNotIn('-L3', plain)
        self.assertIn(variant.seed, plain)
        self.assertIn(variant.seed, teacher)
        self.assertIn('16-ричной', variant.tasks[6].question)
        self.assertRegex(variant.tasks[6].answer, r'\\texttt\{[0-9A-F]{8}\}')
        self.assertIn('таблицу истинности', variant.tasks[7].question)
        self.assertNotIn('Запишите логическую функцию', variant.tasks[7].question)
        self.assertEqual(plain.count(r'\rule{6mm}{0pt}'), 16)
        self.assertNotIn(r'\rule{6mm}{0pt}', teacher)
        self.assertIn('уровень 3', teacher)
        self.assertIn('балла', teacher)
        self.assertIn('\\begin{tikzpicture}', plain)
        for task in variant.tasks:
            self.assertIn(task.question, plain)
            self.assertIn(task.question, teacher)
            self.assertIn(task.answer, teacher)
        self.assertNotIn('Краткие ответы и решения', plain)
        combined = render_document([(student, variant), (dict(student, student_id='BPI265-002'),
                                                        generate('BPI265-002', 3, 'seed'))], False)
        self.assertEqual(combined.count('\\clearpage'), 1)
        self.assertEqual(combined.count('\n\\begingroup\n'), 2)
        self.assertEqual(combined.count('\\end{enumerate}\n\\endgroup'), 2)
        duplex = render_document([(student, variant), (dict(student, student_id='BPI265-002'),
                                                      generate('BPI265-002', 3, 'seed'))], False, duplex=True)
        self.assertIn(r'\documentclass[a4paper,10pt,twoside]', duplex)
        self.assertEqual(duplex.count(r'\cleardoublepage'), 1)

    def test_truth_table_uses_alphabetical_inputs_and_correct_output(self):
        for level in (1, 2, 3):
            data = generate('BPI265-001', level, 'seed').tasks[7].data
            labels = sorted(data['labels'])
            table = truth_table(data, solutions=True)
            self.assertIn(' & '.join(labels + ['F'] + labels + ['F']), table)
            lines = [line for line in table.splitlines() if ' & ' in line][1:]
            self.assertEqual(len(lines), 2 ** (data['inputs'] - 1))
            for first, line in enumerate(lines):
                cells = [cell.strip() for cell in line.split(r'\\')[0].split('&')]
                for offset, index in enumerate((first, first + len(lines))):
                    row = cells[offset * (data['inputs'] + 1):(offset + 1) * (data['inputs'] + 1)]
                    self.assertEqual(row[:data['inputs']],
                                     [str((index >> (data['inputs'] - 1 - bit)) & 1)
                                      for bit in range(data['inputs'])])
                    self.assertEqual(row[-1], str(data['truth_alphabetical'][index]))

    def test_release_produces_four_document_sets_and_manifest(self):
        with tempfile.TemporaryDirectory(dir=ROOT / 'tests') as tmp:
            roster = Path(tmp) / 'students.csv'
            with roster.open('w', encoding='utf-8', newline='') as out:
                writer = csv.DictWriter(out, fieldnames=['student_id', 'group', 'subgroup', 'full_name'])
                writer.writeheader()
                writer.writerows([
                    dict(student_id='BPI265-001', group='БПИ265', subgroup='1', full_name='Первый Студент'),
                    dict(student_id='BPI2610-001', group='БПИ2610', subgroup='2', full_name='Второй Студент'),
                ])
            output = Path(tmp) / 'release'
            produce(roster, ['БПИ265', 'БПИ2610'], None, 3, 'seed', output, tex_only=True)
            self.assertEqual(len(list((output / 'students').glob('*.tex'))), 2)
            self.assertEqual(len(list((output / 'students-with-solutions').glob('*.tex'))), 2)
            self.assertEqual(len(list(output.glob('*.tex'))), 2)
            with (output / 'assignments.csv').open(encoding='utf-8') as inp:
                self.assertEqual(len(list(csv.DictReader(inp))), 2)
            self.assertIn('Контрольная работа', (output / 'all-students.tex').read_text())
            self.assertNotIn('Краткие ответы', (output / 'all-students.tex').read_text())
            self.assertIn('Краткие ответы', (output / 'all-students-with-solutions.tex').read_text())
            item = verify_assignment(output / 'manifest.json', 'BPI265-001',
                                     generate('BPI265-001', 3, 'seed').seed)
            self.assertEqual(item['student']['full_name'], 'Первый Студент')
            with self.assertRaisesRegex(ValueError, 'seed'):
                verify_assignment(output / 'manifest.json', 'BPI265-001', 'incorrect-seed')
            original = output / 'students/BPI265-001-L3.tex'
            original.write_text(original.read_text(encoding='utf-8') + '\n% altered\n', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'SHA-256|контрольной суммы'):
                verify_assignment(output / 'manifest.json', 'BPI265-001',
                                  generate('BPI265-001', 3, 'seed').seed)


if __name__ == '__main__':
    unittest.main()
