#!/usr/bin/env python3
"""Generate per-student and print-ready control-work PDFs."""

import argparse
import secrets
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.test1.publish import produce


def main():
    parser = argparse.ArgumentParser(description='Индивидуальная контрольная № 1 из CSV')
    parser.add_argument('--roster', type=Path, required=True)
    parser.add_argument('--group', action='append', required=True)
    parser.add_argument('--subgroup', choices=('1', '2'))
    parser.add_argument('--level', type=int, choices=(1, 2, 3), required=True)
    parser.add_argument('--seed', help='Seed выпуска; без него создаётся новый случайный')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--tex-only', action='store_true')
    parser.add_argument('--duplex', action='store_true')
    args = parser.parse_args()
    release_seed = args.seed if args.seed is not None else secrets.token_hex(16)
    result = produce(args.roster, args.group, args.subgroup, args.level, release_seed,
                     args.output, args.tex_only, args.duplex)
    print(f'Seed выпуска: {release_seed}')
    print(f'Создано {len(result["assignments"])} вариантов, {len(result["files"])} TEX/PDF: {args.output}')


if __name__ == '__main__':
    main()
