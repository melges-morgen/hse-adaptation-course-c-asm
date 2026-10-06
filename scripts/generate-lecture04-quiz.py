#!/usr/bin/env python3
"""Generate named lecture 4 quizzes for every subgroup."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.lecture04_quiz.publish import produce


def main():
    parser = argparse.ArgumentParser(description='Именные тесты лекции и лабораторной № 4')
    parser.add_argument('--roster', type=Path, default=Path('groups/students.csv'))
    parser.add_argument('--schedule', type=Path, default=Path('assessments/lecture04/days.json'))
    parser.add_argument('--seed', required=True, help='Seed выпуска для воспроизводимой перестановки')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--tex-only', action='store_true', help='Не собирать PDF')
    args = parser.parse_args()
    release = produce(args.roster, args.schedule, args.seed, args.output, not args.tex_only)
    print(f'Выпуск: {len(release["subgroups"])} подгрупп, {len(release["students"])} студентов, '
          f'{len(release["files"])} документов; {args.output}')


if __name__ == '__main__':
    main()
