FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libc6-dev gdb python3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace
