FROM python:3.10-slim
COPY --from=ghcr.io/astral-sh/uv:0.7.19 /uv /uvx /bin/

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV BOKEH_ALLOW_WS_ORIGIN="*"

WORKDIR /usr/src/storage_service
COPY pyproject.toml ./
COPY uv.lock ./
RUN uv sync --locked

COPY src/nsdf_intersect_storage/storage_service.py .

COPY ./src/nsdf_intersect_storage/config_storage.yaml /config/config_storage.yaml

WORKDIR /usr/src/storage_service/src/nsdf_intersect_service

EXPOSE 10044

CMD ["uv", "run", "storage_service.py"]
