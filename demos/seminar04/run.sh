#!/bin/sh
set -eu
stage="${1:-6}"
case "$stage" in 1|2|3|4|5|6) ;; *) exit 2 ;; esac
source="work/seminar04/stages/stage$stage/journal.asm"
test -f "$source" || { echo 'Нет исходника этапа; см. demos/lecture04-journal/README.md' >&2; exit 2; }
image_dir="build/seminar04/stage$stage"
JOURNAL_SOURCE="$source" JOURNAL_OUT="$image_dir" sh demos/lecture04-journal/build.sh "$stage"
disk="${SEMINAR4_DISK:-build/seminar04/grades.img}"
if [ ! -f "$disk" ]; then
    if [ "$disk" != 'build/seminar04/grades.img' ]; then
        echo "Нет выбранной копии диска: $disk" >&2
        exit 2
    fi
    python3 -c 'from pathlib import Path; p=Path("build/seminar04/grades.img"); p.parent.mkdir(parents=True, exist_ok=True); p.open("wb").truncate(1024*1024)'
fi
websockify --web /usr/share/novnc 0.0.0.0:6080 127.0.0.1:5900 &
proxy=$!
trap 'kill "$proxy" 2>/dev/null || true' EXIT INT TERM
qemu-system-i386 -machine pc -m 16M -boot order=a \
    -drive "file=$image_dir/boot.img,format=raw,if=floppy" \
    -drive "file=$disk,format=raw,if=ide,index=0,media=disk" \
    -vnc 127.0.0.1:0 -display none -serial stdio -monitor none -no-reboot
