# Gleichlaut. Two images from one file:
#   base    (default, what `make run` uses): Python + lxml. No model weights, no network needed at runtime.
#   offline (`make run-offline`): adds llama-cpp-python for the local CPU Apertus 8B GGUF lane (air-gapped target).
# Build-time dependencies (PyPI wheels/sdists, the base image) are fetched here; runtime dependencies are listed in
# docs/dependencies.md. No secrets are baked in: the model endpoint comes from LLM_* environment variables at run time.
# Base image pinned by digest (the multi-arch index of python:3.12-slim as published on Docker Hub, looked up 9 Oct 2026
# via the registry API; its linux/amd64 manifest is sha256:2b4f19dae3a777dfc3b76730bda1e82e1f66ab2a2686fa93ca78edbfb4f04ffe).
# To upgrade: look up the new index digest (docs/operations.md, "Upgrade"), replace it here, run `make run` and `make test`.
FROM python:3.12-slim@sha256:a6e34c598f2467ed0e9a8d349809fcd8b5c603269512df273a0bb1784edc11b1 AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app/src PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt && useradd --create-home --uid 10001 app
WORKDIR /app
COPY --chown=app:app . /app
RUN mkdir -p /app/out /app/state && chown app:app /app /app/out /app/state
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
