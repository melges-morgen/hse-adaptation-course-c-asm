FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libc6-dev nasm binutils ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace
CMD ["sh", "-c", "set -eu; nasm -f elf64 demos/lecture04/add_middle.asm -o /tmp/lecture04.o; gcc -std=c11 -Wall -Wextra -Werror -O2 -no-pie demos/lecture04/memory.c /tmp/lecture04.o -o /tmp/lecture04; /tmp/lecture04; objdump -d -Mintel /tmp/lecture04.o"]
