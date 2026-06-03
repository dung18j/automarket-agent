FROM mcr.microsoft.com/devcontainers/base:trixie

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    pkg-config \
    libssl-dev \
    cmake \
    curl \
    rustup \
    gcc \
    ripgrep \
    python3 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

USER vscode
RUN rustup default stable
RUN rustup target add wasm32-unknown-unknown
RUN curl -fsSL https://opencode.ai/install | bash
