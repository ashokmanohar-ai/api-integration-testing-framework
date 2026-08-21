FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN addgroup --system acme && adduser --system --ingroup acme acme
WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY config ./config
COPY framework ./framework
COPY demo_system ./demo_system
RUN python -m pip install --upgrade pip && python -m pip install ".[postgres,messaging]"

USER acme
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=3s --retries=10 CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"
CMD ["uvicorn", "demo_system.main:app", "--host", "0.0.0.0", "--port", "8000"]

