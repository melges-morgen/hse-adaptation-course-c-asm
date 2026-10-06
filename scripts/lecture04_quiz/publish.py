"""Create a release with one printable PDF and one key per subgroup."""

import json
import subprocess
from collections import defaultdict
from pathlib import Path
from typing import Any

from scripts.lecture04_quiz.bank import validate_bank
from scripts.lecture04_quiz.generator import assign_form, load_roster, load_schedule, validate_schedule
from scripts.lecture04_quiz.render import render_key, render_student

ROOT = Path(__file__).resolve().parents[2]


def produce(roster_path, schedule_path, seed, output, pdf=True):
    validate_bank()
    roster = load_roster(roster_path)
    schedule = load_schedule(schedule_path)
    validate_schedule(schedule, roster)
    if not seed:
        raise ValueError('Укажите непустой seed выпуска')
    output = Path(output).resolve()
    if output.exists() and any(output.iterdir()):
        raise ValueError('Каталог выпуска уже содержит файлы; выберите новый --output')
    relative_output = None
    if pdf:
        try:
            relative_output = output.relative_to(ROOT)
        except ValueError as error:
            raise ValueError('Для Docker-сборки --output должен быть внутри репозитория') from error
    (output / 'print').mkdir(parents=True, exist_ok=True)
    (output / 'keys').mkdir(exist_ok=True)
    by_subgroup = defaultdict(list)
    for student in roster:
        subgroup = student['group'] + '-' + student['subgroup']
        by_subgroup[subgroup].append(student)

    release: dict[str, Any] = dict(version=1, seed=seed, schedule=schedule,
                                   students=[], subgroups={}, files=[])
    sorted_subgroups = sorted(by_subgroup, key=lambda value: (int(value.split('-')[0][3:]),
                                                                int(value.split('-')[1])))
    for subgroup in sorted_subgroups:
        day = schedule[subgroup]
        entries = []
        records = []
        for student in sorted(by_subgroup[subgroup], key=lambda item: item['student_id']):
            forms = [assign_form(student, day, lab, seed) for lab in ('C', 'NASM')]
            entries.append((student, forms))
            record = dict(student_id=student['student_id'], full_name=student['full_name'],
                          group=student['group'], subgroup=student['subgroup'], day=day,
                          forms={form.lab: dict(code=form.code,
                                                questions=[q.id for q in form.questions],
                                                answers=''.join(q.answer for q in form.questions))
                                 for form in forms})
            records.append(record)
            release['students'].append(record)
        release['subgroups'][subgroup] = records
        latin = 'BPI' + subgroup[3:]
        for category, text in (('print', render_student(entries)),
                               ('keys', render_key(entries, subgroup))):
            path = output / category / (latin + '.tex')
            path.write_text(text, encoding='utf-8')
            try:
                source_path = path.relative_to(ROOT)
            except ValueError:
                source_path = path
            release['files'].append(dict(path=str(source_path), category=category,
                                         subgroup=subgroup, students=len(entries)))
    (output / 'manifest.json').write_text(json.dumps(release, ensure_ascii=False, indent=2) + '\n',
                                          encoding='utf-8')
    if pdf:
        assert relative_output is not None
        subprocess.run(['docker', 'build', '-t', 'adaptation-course-tex', '.'], cwd=ROOT, check=True)
        subprocess.run(['docker', 'run', '--rm', '-v', f'{ROOT}:/workspace', '-w', '/workspace',
                        'adaptation-course-tex', 'python3', 'scripts/lecture04_quiz/build.py',
                        str(relative_output / 'manifest.json')], cwd=ROOT, check=True)
    return release
