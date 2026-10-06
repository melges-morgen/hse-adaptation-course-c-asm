import tempfile
import unittest
import re
from pathlib import Path

from scripts.lecture04_quiz.bank import COMMON, LAB, day_questions, validate_bank
from scripts.lecture04_quiz.generator import assign_form, load_roster, load_schedule, validate_schedule
from scripts.lecture04_quiz.publish import produce
from scripts.lecture04_quiz.render import render_student, render_key


ROOT = Path(__file__).resolve().parents[1]
ROSTER = ROOT / 'groups/students.csv'
SCHEDULE = ROOT / 'assessments/lecture04/days.json'


class QuestionBankTest(unittest.TestCase):
    def test_each_day_has_ten_questions_and_five_changed_questions(self):
        validate_bank()
        self.assertEqual(len(COMMON), 18)
        self.assertEqual({lab: len(pool) for lab, pool in LAB.items()}, {'C': 12, 'NASM': 12})
        for lab in LAB:
            sets = [day_questions(day, lab) for day in range(1, 6)]
            for questions in sets:
                self.assertEqual(len(questions), 10)
                self.assertEqual(len({q.id for q in questions}), 10)
                self.assertTrue(all(len(q.options) == 4 and q.correct in range(4) for q in questions))
            for i in range(5):
                for j in range(i + 1, 5):
                    self.assertEqual(len({q.id for q in sets[i]} & {q.id for q in sets[j]}), 5)

    def test_question_latex_contains_no_unescaped_comment_markers_or_tabs(self):
        for question in COMMON + sum(LAB.values(), ()):
            for text in (question.prompt, *question.options):
                self.assertNotIn('\t', text, question.id)
                self.assertIsNone(re.search(r'(?<!\\)%', text), question.id)


class AssignmentTest(unittest.TestCase):
    def test_all_subgroups_have_exactly_one_day(self):
        schedule = load_schedule(SCHEDULE)
        roster = load_roster(ROSTER)
        validate_schedule(schedule, roster)
        self.assertEqual(len(schedule), 20)
        self.assertEqual(set(schedule.values()), set(range(1, 6)))
        self.assertEqual(schedule['БПИ268-2'], 1)
        self.assertEqual(schedule['БПИ264-1'], 1)
        self.assertEqual(schedule['БПИ264-2'], 2)
        with self.assertRaisesRegex(ValueError, 'подгрупп'):
            validate_schedule({k: v for k, v in schedule.items() if k != 'БПИ268-2'}, roster)

    def test_shuffling_is_repeatable_but_student_specific_and_key_tracks_choices(self):
        students = load_roster(ROSTER)
        first, second = students[0], students[1]
        a = assign_form(first, 1, 'C', 'quiz-2026')
        b = assign_form(first, 1, 'C', 'quiz-2026')
        c = assign_form(second, 1, 'C', 'quiz-2026')
        self.assertEqual(a, b)
        self.assertNotEqual(a.code, c.code)
        self.assertEqual(len(a.questions), 10)
        self.assertEqual(len({q.id for q in a.questions}), 10)
        self.assertEqual({q.id for q in a.questions}, {q.id for q in c.questions})
        self.assertEqual(len([q for q in a.questions if q.id.startswith('G')]), 6)
        for q in a.questions:
            original = next(source for source in day_questions(1, 'C') if source.id == q.id)
            self.assertEqual(set(q.options), set(original.options))
            self.assertEqual(q.options['АБВГ'.index(q.answer)], original.options[original.correct])

    def test_rendered_student_forms_have_names_and_no_answer_key(self):
        student = dict(student_id='BPI264-001', group='БПИ264', subgroup='1',
                       full_name='Тестов & Проверяющий')
        forms = [assign_form(student, 1, lab, 'quiz-2026') for lab in ('C', 'NASM')]
        student_tex = render_student([(student, forms)])
        key_tex = render_key([(student, forms)], 'БПИ264-1')
        self.assertIn(r'Тестов \& Проверяющий', student_tex)
        self.assertIn('C, GCC', student_tex)
        self.assertIn('NASM, BIOS', student_tex)
        self.assertEqual(student_tex.count(r'\answergrid'), 2)
        self.assertNotIn('Ключ преподавателя', student_tex)
        self.assertIn(forms[0].code, key_tex)
        self.assertIn(''.join(q.answer for q in forms[1].questions), key_tex)

    def test_release_has_one_print_file_and_one_key_per_subgroup(self):
        with tempfile.TemporaryDirectory() as tmp:
            release = produce(ROSTER, SCHEDULE, 'quiz-2026', Path(tmp) / 'release', pdf=False)
            self.assertEqual(len(release['subgroups']), 20)
            self.assertEqual(len(release['students']), len(load_roster(ROSTER)))
            self.assertEqual(len(list((Path(tmp) / 'release' / 'print').glob('*.tex'))), 20)
            self.assertEqual(len(list((Path(tmp) / 'release' / 'keys').glob('*.tex'))), 20)
            for subgroup, entries in release['subgroups'].items():
                self.assertEqual(len(entries), sum(s['group'] + '-' + s['subgroup'] == subgroup
                                                  for s in load_roster(ROSTER)))
                self.assertTrue(all(set(student['forms']) == {'C', 'NASM'} for student in entries))

    def test_release_inside_repo_records_docker_relative_source_paths(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            release = produce(ROSTER, SCHEDULE, 'quiz-2026', Path(tmp) / 'release', pdf=False)
            self.assertTrue(all(not Path(item['path']).is_absolute() for item in release['files']))
            self.assertTrue(all((ROOT / item['path']).is_file() for item in release['files']))


if __name__ == '__main__':
    unittest.main()
