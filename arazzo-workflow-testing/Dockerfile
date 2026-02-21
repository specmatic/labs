FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS build

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
WORKDIR /app

COPY uv.lock pyproject.toml ./
RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen --no-install-project

COPY common ./common
COPY services ./services
COPY scripts ./scripts

FROM python:3.13-slim-bookworm

ARG SERVICE_NAME

ENV SERVICE_NAME=${SERVICE_NAME}
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app"

RUN groupadd --system --gid 999 nonroot && useradd --system --gid 999 --uid 999 --create-home nonroot
WORKDIR /app

COPY --from=build --chown=nonroot:nonroot /app/.venv /app/.venv
COPY --from=build --chown=nonroot:nonroot /app/common /app/common
COPY --from=build --chown=nonroot:nonroot /app/services /app/services
COPY --from=build --chown=nonroot:nonroot /app/scripts /app/scripts

USER nonroot
CMD ["sh", "-c", "fastapi run --host 0.0.0.0 --port ${PORT:-3000} services/$SERVICE_NAME"]
