#!/bin/sh
set -eu
stage="${1:-6}"
case "$stage" in 1|2|3|4|5|6) ;; *) exit 2 ;; esac
out="build/lecture04-journal/stage$stage"
mkdir -p "$out"
nasm -f bin demos/lecture04-journal/boot16.asm -o "$out/boot.bin"
nasm -f bin -DSTAGE="$stage" demos/lecture04-journal/journal16.asm -o "$out/journal.bin"
python3 -c '
from pathlib import Path
import sys
boot, payload, target = (Path(s) for s in sys.argv[1:])
b, p = boot.read_bytes(), payload.read_bytes()
assert len(b) == 512 and b[-2:] == b"\x55\xaa"
assert len(p) <= 17 * 512, f"Journal exceeds boot loader track: {len(p)} bytes"
image = bytearray(1440 * 1024)
image[:512] = b
image[512:512+len(p)] = p
target.write_bytes(image)
print(f"stage: {target} ({len(p)} bytes of NASM)")
' "$out/boot.bin" "$out/journal.bin" "$out/boot.img"
