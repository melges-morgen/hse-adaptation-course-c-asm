FROM debian:bookworm-slim
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    nasm qemu-system-x86 \
    python3 novnc websockify ca-certificates && rm -rf /var/lib/apt/lists/*
WORKDIR /workspace
