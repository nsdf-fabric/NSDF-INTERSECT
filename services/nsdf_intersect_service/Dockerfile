FROM python:3.10-slim
COPY --from=ghcr.io/astral-sh/uv:0.7.19 /uv /uvx /bin/

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV BOKEH_ALLOW_WS_ORIGIN="*"

WORKDIR /usr/src/dashboard_service
COPY ./pyproject.toml ./
COPY ./uv.lock ./
RUN uv sync --locked

COPY src/nsdf_intersect_service/dashboard_service.py .
COPY ./src/nsdf_intersect_service/config_dashboard.yaml /config/config_dashboard_default.yaml
COPY ./src/nsdf_intersect_service/config_service.yaml /config/config_default.yaml

EXPOSE 10043

CMD ["uv", "run", "dashboard_service.py"]
