# Stage 1: build
FROM python:3.13-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /opt/skhema
COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --frozen --no-editable
COPY . .

# Stage 2: runtime
FROM python:3.13-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    wkhtmltopdf \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

ADD https://github.com/plantuml/plantuml/releases/download/v1.2024.8/plantuml-linux-amd64-v1.2024.8 \
    /usr/local/bin/plantuml
RUN chmod +x /usr/local/bin/plantuml

COPY --from=builder /opt/skhema /opt/skhema
COPY --from=builder /opt/skhema/.venv /opt/skhema/.venv

ENV PATH="/opt/skhema/.venv/bin:/opt/skhema/bin:$PATH"
ENV PLANTUML_BIN=/usr/local/bin/plantuml
WORKDIR /workspace
