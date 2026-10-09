"""Look up an issued exam by its printed student ID and individual seed."""

import hashlib
import json
from pathlib import Path

from scripts.test1.generator import generate


def verify_assignment(manifest_path, student_id, seed):
    path = Path(manifest_path).resolve()
    manifest = json.loads(path.read_text(encoding='utf-8'))
    for entry in manifest['assignments']:
        if entry['student']['student_id'] != student_id:
            continue
        if entry['variant']['seed'] != seed:
            raise ValueError('seed не совпадает с выданным вариантом')
        regenerated = generate(student_id, entry['variant']['level'], manifest['parameters']['seed'])
        if regenerated.seed != seed or regenerated.fingerprint != entry['variant']['fingerprint']:
            raise ValueError('Данные варианта не совпадают с seed выпуска и сохранёнными заданиями')
        exam = path.parent / 'students' / f'{student_id}-L{entry["variant"]["level"]}.tex'
        digest = hashlib.sha256(exam.read_bytes()).hexdigest()
        if digest != entry['student_tex_sha256']:
            raise ValueError('Архивный TEX отличается от сохранённой контрольной суммы')
        return entry
    raise ValueError(f'В выданном выпуске нет студента {student_id}')
