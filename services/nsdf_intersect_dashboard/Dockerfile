FROM python:3.10-slim
COPY --from=ghcr.io/astral-sh/uv:0.7.19 /uv /uvx /bin/

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV BOKEH_ALLOW_WS_ORIGIN="*"

WORKDIR /app
COPY . /app
RUN uv sync --locked

# Expose the port
EXPOSE 10042

# Run the FastAPI app
CMD ["uv", "run", "panel", "serve", "dashboard.py", "--address", "0.0.0.0", "--allow-websocket-origin", "*", "--port", "10042"]
