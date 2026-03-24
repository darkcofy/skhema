# Stage 1: build
FROM python:3.13-slim-bookworm AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /opt/skhema
COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --frozen --no-install-project
COPY . .
RUN uv sync --no-dev --frozen --no-editable

# Stage 2: runtime
FROM python:3.13-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    wkhtmltopdf \
    graphviz \
    unzip \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# PlantUML native binary (GraalVM-compiled, no JRE needed)
ADD https://github.com/plantuml/plantuml/releases/download/v1.2025.4-native/plantuml-headless-linux-amd64-1.2025.4.zip \
    /tmp/plantuml.zip
RUN unzip /tmp/plantuml.zip -d /opt/plantuml && \
    chmod +x /opt/plantuml/plantuml-headless && \
    ln -s /opt/plantuml/plantuml-headless /usr/local/bin/plantuml && \
    rm /tmp/plantuml.zip

COPY --from=builder /opt/skhema /opt/skhema
COPY --from=builder /opt/skhema/.venv /opt/skhema/.venv

# Symlinks so relative includes from diagrams (e.g. ../../../../lib/theme.puml) resolve
RUN ln -s /opt/skhema/skhema/lib /opt/skhema/lib && \
    ln -s /opt/skhema/skhema/models /opt/skhema/models

ENV PATH="/opt/skhema/.venv/bin:/opt/skhema/bin:$PATH"
ENV PLANTUML_BIN=/usr/local/bin/plantuml
WORKDIR /workspace
