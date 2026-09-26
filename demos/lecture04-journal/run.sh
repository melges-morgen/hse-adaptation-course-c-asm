#!/bin/sh
set -eu
stage="${1:-6}"
case "$stage" in 1|2|3|4|5|6) ;; *) exit 2 ;; esac
image="build/lecture04-journal/stage$stage/boot.img"
disk="build/lecture04-journal/grades.img"
if [ ! -f "$image" ]; then
    sh demos/lecture04-journal/build.sh "$stage"
fi
if [ ! -f "$disk" ]; then
    python3 -c 'from pathlib import Path; p=Path("build/lecture04-journal/grades.img"); p.parent.mkdir(parents=True, exist_ok=True); p.open("wb").truncate(1024*1024)'
fi
websockify --web /usr/share/novnc 0.0.0.0:6080 127.0.0.1:5900 &
proxy=$!
trap 'kill "$proxy" 2>/dev/null || true' EXIT INT TERM
qemu-system-i386 -machine pc -m 16M -boot order=a \
    -drive "file=$image,format=raw,if=floppy" \
    -drive "file=$disk,format=raw,if=ide,index=0,media=disk" \
    -vnc 127.0.0.1:0 -display none -serial stdio -monitor none -no-reboot
