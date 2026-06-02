FROM python:3.11-slim AS base

RUN pip install --no-cache-dir uv

WORKDIR /app

COPY pyproject.toml .
COPY config.yaml .
COPY datasets/ datasets/
COPY src/ src/

RUN uv pip install --system -e .

EXPOSE 8089

ENTRYPOINT ["trace-replay"]
