FROM python:3.10-slim AS base


RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*


# Tweak Python to run better in Docker
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1


# Build stage: dev & build dependencies
FROM base AS build

COPY --from=ghcr.io/astral-sh/uv:0.7.19 /uv /uvx /bin/

# UV_COMPILE_BYTECODE=1 is an important startup time optimization
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

WORKDIR /app 

COPY uv.lock pyproject.toml ./
RUN --mount=type=cache,target=/root/.cache/uv \
  uv sync --frozen --no-install-project --no-dev

COPY . .
RUN --mount=type=cache,target=/root/.cache/uv \
  uv sync --frozen --no-dev

# Runtime stage: only venv

FROM base AS runtime

WORKDIR /app

# Create user and group
RUN addgroup --gid 1001 --system nonroot && \
    adduser --no-create-home --shell /bin/false \
    --disabled-password --uid 1001 --system --group nonroot

# Switch to non-root user
USER nonroot:nonroot

ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

ENV BOKEH_ALLOW_WS_ORIGIN="*"

COPY --from=build --chown=nonroot:nonroot /app ./
COPY ./src/nsdf_intersect_dashboard/config_dashboard.yaml /config/config_dashboard_default.yaml

EXPOSE 10042

CMD ["panel", "serve", "/app/src/nsdf_intersect_dashboard/dashboard.py", "--address", "0.0.0.0", "--allow-websocket-origin", "*", "--port", "10042"]
