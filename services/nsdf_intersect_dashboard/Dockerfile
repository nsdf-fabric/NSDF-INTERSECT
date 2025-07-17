FROM python:3.10-slim
COPY --from=ghcr.io/astral-sh/uv:0.7.19 /uv /uvx /bin/

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV BOKEH_ALLOW_WS_ORIGIN="*"

WORKDIR /usr/src/dashboard
COPY ./pyproject.toml ./
COPY ./uv.lock ./
RUN uv sync --locked

COPY src/nsdf_intersect_dashboard/ .
COPY ./src/nsdf_intersect_dashboard/config_dashboard.yaml /config/config_dashboard_default.yaml

EXPOSE 10042

CMD ["uv", "run", "panel", "serve", "dashboard.py", "--address", "0.0.0.0", "--allow-websocket-origin", "*", "--port", "10042"]
