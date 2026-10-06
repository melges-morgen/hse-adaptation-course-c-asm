"""Day assignments and reproducible per-student permutations."""

import csv
import hashlib
import json
import random
import re
from dataclasses import dataclass
from pathlib import Path

from scripts.lecture04_quiz.bank import day_questions

LETTERS = 'АБВГ'


def load_roster(path):
    fields = ['student_id', 'group', 'subgroup', 'full_name']
    with Path(path).open(encoding='utf-8-sig', newline='') as source:
        reader = csv.DictReader(source)
        if reader.fieldnames != fields:
            raise ValueError('CSV: требуются student_id,group,subgroup,full_name')
        students = list(reader)
    ids = set()
    names = set()
    for student in students:
        sid, group, subgroup, name = (student[field].strip() for field in fields)
        if (not re.fullmatch(r'BPI\d+-\d{3,}', sid) or
                not re.fullmatch(r'БПИ\d+', group) or subgroup not in ('1', '2') or
                not name or not sid.startswith('BPI' + group[3:] + '-')):
            raise ValueError(f'Некорректная строка CSV: {student}')
        if sid in ids or (group, name) in names:
            raise ValueError(f'Повторный student_id или ФИО: {student}')
        ids.add(sid)
        names.add((group, name))
        student.update(student_id=sid, group=group, subgroup=subgroup, full_name=name)
    return students


@dataclass(frozen=True)
class ShuffledQuestion:
    id: str
    prompt: str
    options: tuple[str, str, str, str]
    answer: str


@dataclass(frozen=True)
class Form:
    code: str
    day: int
    lab: str
    questions: tuple[ShuffledQuestion, ...]


def load_schedule(path):
    def unique_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f'Повтор подгруппы в расписании: {key}')
            result[key] = value
        return result

    return json.loads(Path(path).read_text(encoding='utf-8'), object_pairs_hook=unique_pairs)


def validate_schedule(schedule, roster):
    actual = {student['group'] + '-' + student['subgroup'] for student in roster}
    if set(schedule) != actual:
        raise ValueError(f'Расписание подгрупп: отсутствуют {sorted(actual - set(schedule))}; '
                         f'лишние {sorted(set(schedule) - actual)}')
    if any(type(day) is not int or day not in range(1, 6) for day in schedule.values()):
        raise ValueError('Дни подгрупп должны быть целыми числами от 1 до 5')


def assign_form(student, day, lab, seed):
    if not seed:
        raise ValueError('Нужен непустой seed выпуска')
    identity = f'lecture04-quiz-v1|{seed}|{student["student_id"]}|{day}|{lab}'
    rng = random.Random(int(hashlib.sha256(identity.encode('utf-8')).hexdigest(), 16))
    questions = list(day_questions(day, lab))
    common, special = questions[:6], questions[6:]
    rng.shuffle(common)
    rng.shuffle(special)
    shuffled = []
    for question in common + special:
        indices = list(range(4))
        rng.shuffle(indices)
        options = tuple(question.options[indices[i]] for i in range(4))
        shuffled.append(ShuffledQuestion(question.id, question.prompt,
                                         (options[0], options[1], options[2], options[3]),
                                         LETTERS[indices.index(question.correct)]))
    signature = hashlib.sha256(repr([(q.id, q.options) for q in shuffled]).encode('utf-8')).hexdigest()[:8]
    return Form(f'{student["student_id"]}-D{day}-{lab}-{signature}', day, lab, tuple(shuffled))
