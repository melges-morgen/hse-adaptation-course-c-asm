"""Prepare an editable copy of the complete journal without losing edits."""

from pathlib import Path
import shutil
import sys


STAGES = Path("demos/lecture04-journal/stages")
STARTERS = Path("demos/seminar04/starters")
TASKS = {
    1: ("first_record: db 'S01  grade 07', 0",
        "first_record: db 'S01  grade --', 0 ; ЗАДАНИЕ 1: вывести 07"),
    3: ("cmp al, 0x1e                ; A=10",
        "cmp al, 0x7f                ; ЗАДАНИЕ 3: скан-код A"),
    4: ("    call handle_scan\n    jmp .loop",
        "    nop                         ; ЗАДАНИЕ 4: обработать AL из очереди\n    jmp .loop"),
    5: ("    shr cl, 1", "    xor cl, cl                  ; ЗАДАНИЕ 5: прибавить count/2"),
    6: ("cmp al, 0x1f                ; S",
        "cmp al, 0x7f                ; ЗАДАНИЕ 6: скан-код S"),
}


def generate_solutions(root: Path) -> None:
    stage2 = (root / STAGES / "stage2/journal.asm").read_text(encoding="utf-8")
    stage2 = stage2.replace(
        "    rep stosb                   ; повторить запись AL в ES:DI 64 раза\n",
        "    rep stosb                   ; повторить запись AL в ES:DI 64 раза\n"
        "    mov byte [grades+1], 7     ; S01 W2: один числовой байт оценки\n", 1)
    stage6 = (root / STAGES / "stage6/journal.asm").read_text(encoding="utf-8")
    stage6 = stage6.replace("    cmp al, 0x1f                ; S\n",
        "    cmp al, 0x2e                ; C: очистить все оценки выбранного студента\n"
        "    je .clear_student\n"
        "    cmp al, 0x1f                ; S\n", 1)
    stage6 = stage6.replace(".erase:\n", ".clear_student:\n"
        "    mov bl, [student]          ; индекс студента, начиная с 0\n"
        "    xor bh, bh                  ; BX = индекс студента\n"
        "    shl bx, 2                   ; четыре оценки на студента\n"
        "    mov cx, WORKS              ; очистить четыре байта\n"
        "    mov al, UNSET               ; FF = нет оценки\n"
        ".clear_next:\n"
        "    mov [grades+bx], al        ; очистить текущее поле\n"
        "    inc bx                      ; следующий байт\n"
        "    loop .clear_next            ; повторить четыре раза\n"
        "    jmp .changed                ; обновить статистику и VGA\n"
        ".erase:\n", 1)
    stage6 = stage6.replace("Backspace:clear S:save L:load", "Backspace:clear C:row S:save L:load", 1)
    for name, contents in (("stage2/journal.asm", stage2),
                           ("stage6-homework/journal.asm", stage6)):
        path = root / "demos/seminar04/solutions" / name
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(contents, encoding="utf-8")


def generate_starters(root: Path) -> None:
    for stage in range(1, 7):
        reference = root / STAGES / f"stage{stage}" / "journal.asm"
        target = root / STARTERS / f"stage{stage}" / "journal.asm"
        if target.exists():
            continue
        text = reference.read_text(encoding="utf-8")
        if stage == 2:
            needle = "    rep stosb                   ; повторить запись AL в ES:DI 64 раза\n"
            replacement = needle + "    ; ЗАДАНИЕ 2: grades+1 = оценка 7 для S01 W2\n"
        else:
            needle, replacement = TASKS[stage]
        if needle not in text:
            raise ValueError(f"Could not prepare stage {stage}: {needle!r}")
        text = text.replace(needle, replacement, 1 if stage != 5 else 2)
        if stage == 5 and "    shr cl, 1" in text:
            raise ValueError("Both averaging paths must have a gap")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")


def initialize(root: Path, work: Path) -> None:
    source = root / STAGES / "stage6/journal.asm"
    target = work / "journal.asm"
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        shutil.copyfile(source, target)
        print(f"Создано: {target}")
    else:
        print(f"Сохранены ваши изменения: {target}")


def initialize_hello(root: Path, work: Path) -> None:
    target = work / "hello.asm"
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        shutil.copyfile(root / "demos/seminar04/hello.asm", target)
        print(f"Создано: {target}")
    else:
        print(f"Сохранены ваши изменения: {target}")


if __name__ == "__main__":
    if sys.argv[1:] == ["--generate-starters"]:
        generate_starters(Path.cwd())
        generate_solutions(Path.cwd())
    elif sys.argv[1:] == ["--hello"]:
        initialize_hello(Path.cwd(), Path("work/seminar04"))
    elif not sys.argv[1:]:
        initialize(Path.cwd(), Path("work/seminar04"))
    else:
        raise SystemExit("usage: python3 demos/seminar04/prepare.py [--hello|--generate-starters]")
