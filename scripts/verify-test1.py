#!/usr/bin/env python3
"""Find the archived original of a printed exam."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.test1.verify import verify_assignment


def main():
    parser = argparse.ArgumentParser(description='Проверить код и seed выданного варианта')
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--student', required=True)
    parser.add_argument('--seed', required=True)
    args = parser.parse_args()
    entry = verify_assignment(args.manifest, args.student, args.seed)
    student = entry['student']
    print(f'{student["full_name"]} — {student["group"]}-{student["subgroup"]}')
    print(f'Seed совпадает; SHA-256 архивного TEX: {entry["student_tex_sha256"]}')
    print(f'Оригинал: {args.manifest.parent / "students" / (args.student + "-L" + str(entry["variant"]["level"]) + ".pdf")}')
    print('Сверьте содержание предъявленного листа с этим оригиналом.')


if __name__ == '__main__':
    main()
