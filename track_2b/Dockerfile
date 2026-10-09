# Gleichlaut. Two images from one file:
#   base    (default, what `make run` uses): Python + lxml. No model weights, no network needed at runtime.
#   offline (`make run-offline`): adds llama-cpp-python for the local CPU Apertus 8B GGUF lane (air-gapped target).
# Build-time dependencies (PyPI wheels/sdists, the base image) are fetched here; runtime dependencies are listed in
# docs/dependencies.md. No secrets are baked in: the model endpoint comes from LLM_* environment variables at run time.
FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app/src PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt && useradd --create-home --uid 10001 app
WORKDIR /app
COPY --chown=app:app . /app
USER app
CMD ["python", "-m", "gleichlaut", "run"]

FROM base AS offline
USER root
RUN apt-get update && apt-get install -y --no-install-recommends build-essential cmake && rm -rf /var/lib/apt/lists/* \
 && CMAKE_ARGS="-DGGML_NATIVE=OFF" pip install -r /app/requirements-offline.txt \
 && apt-get purge -y build-essential cmake && apt-get autoremove -y
USER app
ENV GLEICHLAUT_GGUF=1
CMD ["python", "-m", "gleichlaut", "run"]
