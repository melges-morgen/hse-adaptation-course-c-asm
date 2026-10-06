"""Compile and check release PDFs inside the repository TeX Docker image."""

import json
import re
import subprocess
import sys
from pathlib import Path


def main():
    manifest = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    for index, item in enumerate(manifest['files'], 1):
        source = Path(item['path'])
        pdf = source.with_suffix('.pdf')
        result = subprocess.run(['latexmk', '-pdf', '-interaction=nonstopmode', '-halt-on-error',
                                 '-quiet', f'-outdir={source.parent}', str(source)],
                                capture_output=True, text=True)
        if result.returncode or not pdf.is_file():
            raise SystemExit(f'Ошибка сборки {source}:\n{result.stdout}\n{result.stderr}')
        if item['category'] == 'print':
            info = subprocess.run(['pdfinfo', str(pdf)], capture_output=True, text=True, check=True)
            match = re.search(r'^Pages:\s+(\d+)$', info.stdout, re.MULTILINE)
            if not match or int(match.group(1)) != 4 * item['students']:
                raise SystemExit(f'Неверное число страниц в {pdf}: ожидается {4 * item["students"]}')
        print(f'PDF: {index}/{len(manifest["files"])} — {pdf}', flush=True)


if __name__ == '__main__':
    main()
