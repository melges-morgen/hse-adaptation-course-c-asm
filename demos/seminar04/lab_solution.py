"""Build the instructor's constant-only solution from the complete journal."""

from pathlib import Path
import argparse


REFERENCE = Path("demos/lecture04-journal/stages/stage6/journal.asm")
SOLUTION = Path("demos/seminar04/solutions/lab/journal.asm")
CHANGES = (
    ("mov ah, 0x0f                ; AH = атрибут цвета, AL = символ",
     "mov ah, 0x1e                ; жёлтый (Eh) на синем фоне (1h)"),
    ("mov bx, 0x0001\n    mov si, title_text",
     "mov bx, 0x0205             ; строка 2, столбец 5\n    mov si, title_text"),
    ("cmp al, 0x1f                ; S",
     "cmp al, 0x10                ; Q: сохранить (scan set 1)"),
    ("cmp al, 0x26                ; L",
     "cmp al, 0x12                ; E: загрузить (scan set 1)"),
    (".ten:\n    mov al, 10",
     ".ten:\n    mov al, 12                 ; новая максимальная оценка"),
    (".check:\n    lodsb\n    cmp al, UNSET\n    je .valid\n    cmp al, 10",
     ".check:\n    lodsb\n    cmp al, UNSET\n    je .valid\n    cmp al, 12                 ; принимать сохранённую оценку 12"),
    ("dq 1                       ; LBA 1 на отдельном HDD",
     "dq 8                       ; байт 4096 = LBA 8 на HDD"),
    ("arrows:select 0-9/A:grade Backspace:clear S:save L:load",
     "arrows:select 0-9/A:12 Backspace:clear Q:save E:load"),
)


def solution(root: Path) -> str:
    text = (root / REFERENCE).read_text(encoding="utf-8")
    for old, new in CHANGES:
        if text.count(old) != 1:
            raise ValueError(f"Контрольный фрагмент найден не ровно один раз: {old!r}")
        text = text.replace(old, new, 1)
    return text


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generate", action="store_true")
    args = parser.parse_args()
    root = Path.cwd()
    expected = solution(root)
    path = root / SOLUTION
    if args.generate:
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            raise FileExistsError(path)
        path.write_text(expected, encoding="utf-8")
    elif path.read_text(encoding="utf-8") != expected:
        raise SystemExit(f"Решение {path} расходится с этапом 6")
    print(f"Решение соответствует этапу 6: {path}")
