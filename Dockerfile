# Stage 1: build
FROM python:3.13-slim-bookworm AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /opt/skhema
COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --frozen --no-install-project
COPY . .
RUN uv sync --no-dev --frozen --no-editable

# Stage 2: PlantUML JAR + Structurizr CLI extraction.
# We use the JAR rather than the GraalVM-native binary because the native
# build has a known Brotli-decompression bug that breaks stdlib includes
# (`!include <C4/C4_Context>` and similar) — critical for Structurizr-
# exported diagrams. The JAR is slower to cold-start but fully functional.
FROM python:3.13-slim-bookworm AS tools
RUN apt-get update && apt-get install -y --no-install-recommends unzip curl \
    && rm -rf /var/lib/apt/lists/*
ARG PLANTUML_VERSION=1.2025.4
ADD https://github.com/plantuml/plantuml/releases/download/v${PLANTUML_VERSION}/plantuml-${PLANTUML_VERSION}.jar \
    /opt/plantuml/plantuml.jar

ARG STRUCTURIZR_CLI_VERSION=2025.11.09
ADD https://github.com/structurizr/cli/releases/download/v${STRUCTURIZR_CLI_VERSION}/structurizr-cli.zip \
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
RUN printf '#!/bin/sh\nexec java -jar /opt/plantuml/plantuml.jar "$@"\n' > /usr/local/bin/plantuml && \
    chmod +x /usr/local/bin/plantuml && \
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
