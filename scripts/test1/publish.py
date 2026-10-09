"""Create the four document sets from a single immutable variant assignment."""

import csv
import hashlib
import json
import subprocess
from dataclasses import asdict
from pathlib import Path

from scripts.test1.generator import generate, load_roster
from scripts.test1.render import render_document

ROOT = Path(__file__).resolve().parents[2]


def produce(roster_path, groups, subgroup, level, seed, output, tex_only=False, duplex=False):
    roster = load_roster(roster_path)
    if not groups:
        raise ValueError('Укажите хотя бы одну группу')
    if len(set(groups)) != len(groups):
        raise ValueError('Группа повторяется в аргументах')
    if subgroup is not None and str(subgroup) not in ('1', '2'):
        raise ValueError('Подгруппа должна быть 1 или 2')
    selected = [s for s in roster if s['group'] in groups and (subgroup is None or s['subgroup'] == str(subgroup))]
    selected.sort(key=lambda s: (groups.index(s['group']), s['subgroup']))
    if not selected or {s['group'] for s in selected} != set(groups):
        raise ValueError('Не найдены студенты каждой запрошенной группы')
    output = Path(output).resolve()
    try:
        relative = output.relative_to(ROOT)
    except ValueError as error:
        raise ValueError('Для сборки в Docker каталог результатов должен находиться внутри репозитория') from error
    parameters = dict(generator_version=3, groups=groups, subgroup=subgroup,
                      level=level, seed=seed, students=[s['student_id'] for s in selected], duplex=duplex)
    manifest_path = output / 'manifest.json'
    if output.exists() and any(output.iterdir()):
        if not manifest_path.exists() or json.loads(manifest_path.read_text(encoding='utf-8'))['parameters'] != parameters:
            raise ValueError('Каталог уже содержит другой выпуск; выберите новый --output')
    output.mkdir(parents=True, exist_ok=True)
    (output / 'students').mkdir(exist_ok=True)
    (output / 'students-with-solutions').mkdir(exist_ok=True)
    pairs = []
    fingerprints = set()
    files = []
    assignments = []
    for student in selected:
        variant = generate(student['student_id'], level, seed)
        if variant.fingerprint in fingerprints:
            raise ValueError('Совпали задания разных студентов; выберите другой seed')
        fingerprints.add(variant.fingerprint)
        pairs.append((student, variant))
        name = f'{student["student_id"]}-L{level}'
        for teacher in (False, True):
            dest = output / ('students-with-solutions' if teacher else 'students') / (name + ('-answers' if teacher else '') + '.tex')
            dest.write_text(render_document([(student, variant)], teacher), encoding='utf-8')
            files.append(str(dest.relative_to(ROOT)))
        assignments.append(dict(student_id=student['student_id'], group=student['group'],
                                subgroup=student['subgroup'], full_name=student['full_name'],
                                level=str(level), variant=name, seed=variant.seed,
                                fingerprint=variant.fingerprint))
    for teacher in (False, True):
        dest = output / ('all-students-with-solutions.tex' if teacher else 'all-students.tex')
        dest.write_text(render_document(pairs, teacher, duplex), encoding='utf-8')
        files.append(str(dest.relative_to(ROOT)))
    with (output / 'assignments.csv').open('w', encoding='utf-8', newline='') as out:
        writer = csv.DictWriter(out, fieldnames=assignments[0].keys())
        writer.writeheader()
        writer.writerows(assignments)
    manifest = dict(parameters=parameters, files=files,
                    assignments=[dict(student=student, variant=asdict(variant),
                                      student_tex_sha256=hashlib.sha256(
                                          (output / 'students' / f'{student["student_id"]}-L{level}.tex').read_bytes()
                                      ).hexdigest()) for student, variant in pairs])
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    if not tex_only:
        subprocess.run(['docker', 'build', '-t', 'adaptation-course-tex', '.'], check=True, cwd=ROOT)
        subprocess.run(['docker', 'run', '--rm', '-v', f'{ROOT}:/workspace', '-w', '/workspace',
                        'adaptation-course-tex', 'python3', 'scripts/test1/build.py',
                        str((relative / 'manifest.json'))], check=True, cwd=ROOT)
    return manifest
