"""Compile a release in a single Docker container, failing on the first error."""

import json
import subprocess
import sys
from pathlib import Path


def main():
    manifest = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    for index, filename in enumerate(manifest['files'], 1):
        path = Path(filename)
        command = ['latexmk', '-pdf', '-interaction=nonstopmode', '-halt-on-error',
                   '-quiet', f'-outdir={path.parent}', str(path)]
        result = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if result.returncode:
            print(result.stdout, file=sys.stderr)
            raise SystemExit(f'Не удалось собрать {path}')
        if not path.with_suffix('.pdf').is_file():
            raise SystemExit(f'Не создан PDF: {path}')
        if index % 10 == 0 or index == len(manifest['files']):
            print(f'PDF: {index}/{len(manifest["files"])}', flush=True)


if __name__ == '__main__':
    main()
