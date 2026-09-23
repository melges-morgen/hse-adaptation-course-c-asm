FROM node:22-bookworm-slim
ENV PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium fonts-crosextra-carlito=20220224-1 fonts-dejavu-core=2.37-6 ca-certificates \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /opt/slides
COPY package.json package-lock.json ./
RUN npm ci --omit=dev
COPY build.mjs ./
WORKDIR /workspace
ENTRYPOINT ["node", "/opt/slides/build.mjs"]
