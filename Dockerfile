# Reproducible local FastAPI demo runtime.
# Base: concrete Python patch + Debian tag, pinned by multi-arch index digest.
FROM python:3.12.13-slim-bookworm@sha256:d50fb7611f86d04a3b0471b46d7557818d88983fc3136726336b2a4c657aa30b

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md LICENSE ./
COPY src ./src
COPY fixtures/offline_mvp ./fixtures/offline_mvp

RUN pip install --no-cache-dir -e . \
    && useradd --create-home --uid 10001 --shell /usr/sbin/nologin appuser \
    && chown -R appuser:appuser /app

USER 10001

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3).read()"

CMD ["uvicorn", "steuerberater_copilot.api.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
