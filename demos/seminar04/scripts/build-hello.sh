#!/bin/sh
set -eu
out="${SEMINAR4_WORK:-work/seminar04}"
mkdir -p "$out"
source="${SEMINAR4_HELLO_SOURCE:-$out/hello.asm}"
test -f "$source" || { printf '%s\n' 'Скопируйте hello.asm в рабочий каталог; команды приведены в demos/seminar04/README.md' >&2; exit 2; }
nasm -f bin "$source" -o "$out/hello.bin"
python3 -c '
from pathlib import Path
import sys
source, image = map(Path, sys.argv[1:])
boot = source.read_bytes()
assert len(boot) == 512 and boot[-2:] == bytes.fromhex("55 aa")
data = bytearray(1440 * 1024)
data[:512] = boot
image.write_bytes(data)
print(f"BIOS-сектор: {source} (512 байтов, подпись 55 AA)")
print(f"Дискета для QEMU: {image}")
' "$out/hello.bin" "$out/hello.img"
