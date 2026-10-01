FROM debian:bookworm-slim
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
RUN apt-get update && apt-get install -y --no-install-recommends \
    nasm qemu-system-x86 python3 novnc websockify gcc libc6-dev gdb file ca-certificates \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /workspace
