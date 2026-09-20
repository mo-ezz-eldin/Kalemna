
FROM python:3.11-slim AS builder

WORKDIR /build


COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /uvx /bin/


RUN uv venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"


COPY requirements.txt .
ENV UV_CACHE_DIR=/root/.cache/uv
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install -v --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt



FROM python:3.11-slim AS runner

WORKDIR /kalemna_app

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"


COPY . .

EXPOSE 8000

CMD ["uvicorn", "src.presentation.api.app:app", "--host", "0.0.0.0", "--port", "8000"]


