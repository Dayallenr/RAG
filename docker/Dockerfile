# Serving image for the due-diligence API.
#
# Two-stage build so the wheel-building toolchain does not ship to
# production. The dependency layer is installed before the application code
# is copied, so editing a Python file rebuilds one small layer rather than
# reinstalling torch — which is by far the largest dependency here.
#
# CPU-only torch on purpose: the image is for serving, where the models are
# a 33M-parameter embedder and a 22M-parameter cross-encoder. The CUDA
# builds of torch add gigabytes for hardware that neither the local
# environment (Apple Silicon) nor a modest cloud node would use.

FROM python:3.13-slim AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build

# build-essential is needed to compile any sdist-only dependency; it stays
# in this stage and never reaches the runtime image.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --upgrade pip \
    && /opt/venv/bin/pip install \
        --extra-index-url https://download.pytorch.org/whl/cpu \
        -r requirements.txt


FROM python:3.13-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    # Model weights are downloaded at startup into a writable cache. Pointing
    # HF_HOME at an explicit path lets Kubernetes mount a volume here so
    # every pod restart does not re-download from the Hub.
    HF_HOME=/app/.cache/huggingface

# curl is for the container healthcheck below; without it HEALTHCHECK cannot
# run in a slim image.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Non-root: the API needs no privileged access, and running as root in a
# container is an unnecessary escalation path if the process is compromised.
RUN useradd --create-home --uid 1000 appuser

WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY duediligence/ ./duediligence/
COPY config/ ./config/
# Structured XBRL facts are read from disk by the exact-lookup route, so
# they are part of the application, not external data. The narrative chunks
# are not copied — those live in OpenSearch.
COPY data/facts/ ./data/facts/

RUN mkdir -p /app/.cache/huggingface && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=90s --retries=3 \
    CMD curl -fsS http://localhost:8000/healthz || exit 1

# Single worker by default: each worker loads its own copy of both models,
# so workers multiply memory rather than sharing it. Scale with replicas
# (horizontally) instead of workers (vertically).
CMD ["uvicorn", "duediligence.api.app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
