# Stage 1: build
FROM python:3.13-slim-bookworm AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /opt/skhema
COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --frozen --no-install-project
COPY . .
RUN uv sync --no-dev --frozen --no-editable

# Stage 2: PlantUML + Structurizr CLI extraction
FROM python:3.13-slim-bookworm AS tools
RUN apt-get update && apt-get install -y --no-install-recommends unzip curl \
    && rm -rf /var/lib/apt/lists/*
ADD https://github.com/plantuml/plantuml/releases/download/v1.2025.4-native/plantuml-headless-linux-amd64-1.2025.4.zip \
    /tmp/plantuml.zip
RUN unzip /tmp/plantuml.zip -d /opt/plantuml && \
    chmod +x /opt/plantuml/plantuml-headless

ARG STRUCTURIZR_CLI_VERSION=2025.03.30
ADD https://github.com/structurizr/cli/releases/download/v${STRUCTURIZR_CLI_VERSION}/structurizr-cli-${STRUCTURIZR_CLI_VERSION}.zip \
    /tmp/structurizr-cli.zip
RUN unzip /tmp/structurizr-cli.zip -d /opt/structurizr-cli && \
    chmod +x /opt/structurizr-cli/structurizr.sh

# Stage 3: runtime
FROM python:3.13-slim-bookworm

# graphviz: PlantUML layout. default-jre-headless: Structurizr CLI (Java).
RUN apt-get update && apt-get install -y --no-install-recommends \
    graphviz \
    default-jre-headless \
    && apt-get purge -y --auto-remove && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

COPY --from=tools /opt/plantuml /opt/plantuml
COPY --from=tools /opt/structurizr-cli /opt/structurizr-cli
RUN ln -s /opt/plantuml/plantuml-headless /usr/local/bin/plantuml && \
    ln -s /opt/structurizr-cli/structurizr.sh /usr/local/bin/structurizr-cli

COPY --from=builder /opt/skhema /opt/skhema
COPY --from=builder /opt/skhema/.venv /opt/skhema/.venv

# Symlinks so relative PlantUML !include paths in client diagrams resolve to src/skhema/{lib,models}
RUN ln -s /opt/skhema/src/skhema/lib /opt/skhema/lib && \
    ln -s /opt/skhema/src/skhema/models /opt/skhema/models

ENV PATH="/opt/skhema/.venv/bin:$PATH"
ENV PLANTUML_BIN=/usr/local/bin/plantuml
ENV STRUCTURIZR_CLI=/usr/local/bin/structurizr-cli
WORKDIR /workspace
