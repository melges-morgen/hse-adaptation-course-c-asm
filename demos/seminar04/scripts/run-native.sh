#!/bin/sh
set -eu
kind="${1:-journal}"
work="${SEMINAR4_WORK:-work/seminar04}"
case "$kind" in
    hello)
        sh demos/seminar04/scripts/build-hello.sh
        image="$work/hello.img"
        qemu-system-i386 -machine pc -m 16M -boot order=a \
            -drive "file=$image,format=raw,if=floppy" -display gtk -no-reboot
        ;;
    journal)
        sh demos/seminar04/scripts/build-journal.sh
        image="$work/artifacts/stage6/boot.img"
        disk="${SEMINAR4_DISK:-$work/grades.img}"
        if [ ! -f "$disk" ]; then
            if [ "$disk" != "$work/grades.img" ]; then
                printf 'Нет указанной копии диска: %s\n' "$disk" >&2
                exit 2
            fi
            python3 -c 'from pathlib import Path; import sys; p=Path(sys.argv[1]); p.open("wb").truncate(1024*1024)' "$disk"
            printf 'Создан новый отдельный диск оценок: %s\n' "$disk"
        fi
        qemu-system-i386 -machine pc -m 16M -boot order=a \
            -drive "file=$image,format=raw,if=floppy" \
            -drive "file=$disk,format=raw,if=ide,index=0,media=disk" \
            -display gtk -serial stdio -monitor none -no-reboot
        ;;
    *) printf '%s\n' 'Укажите hello или journal' >&2; exit 2 ;;
esac
