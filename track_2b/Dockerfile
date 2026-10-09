# Gleichlaut. Two images from one file:
#   base    (default, what `make run` uses): Python + lxml. No model weights, no network needed at runtime.
#   offline (`make run-offline`): adds llama-cpp-python for the local CPU Apertus 8B GGUF lane (air-gapped target).
# Build-time dependencies (PyPI wheels/sdists, the base image) are fetched here; runtime dependencies are listed in
# docs/dependencies.md. No secrets are baked in: the model endpoint comes from LLM_* environment variables at run time.
# Base image pinned by digest (the multi-arch index of python:3.12-slim as published on Docker Hub, looked up 9 Oct 2026
# via the registry API; its linux/amd64 manifest is sha256:2b4f19dae3a777dfc3b76730bda1e82e1f66ab2a2686fa93ca78edbfb4f04ffe).
# Pulled through Google's public Docker Hub mirror by default: the same digest, no Docker Hub login or rate limit, so a
# Docker Hub outage cannot break `make run`. Override with `--build-arg BASE=python:3.12-slim@sha256:...` (or a registry
# you control); the digest pins the exact image either way.
# To upgrade: look up the new index digest (docs/operations.md, "Upgrade"), replace it here, run `make run` and `make test`.
ARG BASE=mirror.gcr.io/library/python:3.12-slim@sha256:a6e34c598f2467ed0e9a8d349809fcd8b5c603269512df273a0bb1784edc11b1
FROM ${BASE} AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app/src PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt && useradd --create-home --uid 10001 app
WORKDIR /app
COPY --chown=app:app . /app
RUN mkdir -p /app/out /app/state && chown app:app /app /app/out /app/state
USER app
CMD ["python", "-m", "gleichlaut", "run"]

FROM base AS offline
# llama-cpp-python 0.3.35 is built from source for a generic x86-64/arm64 CPU (GGML_NATIVE=OFF: the image runs on any CPU of
# the architecture, not only the build host's). libgomp1 is installed explicitly so that removing the compilers afterwards
# keeps the OpenMP runtime the library links against; the import check fails the build if anything is missing.
# The GGUF is not in the image: it is downloaded at run time into the mounted /models and sha256-checked (fetch_gguf).
USER root
RUN apt-get update && apt-get install -y --no-install-recommends build-essential cmake libgomp1 \
 && CMAKE_ARGS="-DGGML_NATIVE=OFF -DLLAMA_CURL=OFF -DLLAMA_BUILD_TESTS=OFF -DLLAMA_BUILD_EXAMPLES=OFF" \
    pip install -r /app/requirements-offline.txt \
 && apt-get purge -y build-essential cmake && apt-get autoremove -y && rm -rf /var/lib/apt/lists/* \
 && python -c "import llama_cpp, numpy; print('llama-cpp-python', llama_cpp.__version__, 'numpy', numpy.__version__)"
USER app
# GLEICHLAUT_GGUF=1: `run` takes the live slice from the local GGUF (n_threads = the CPUs of the container; GLEICHLAUT_THREADS
# overrides). GLEICHLAUT_MODELS: where the GGUF is cached (mount it).
ENV GLEICHLAUT_GGUF=1 GLEICHLAUT_MODELS=/models
CMD ["python", "-m", "gleichlaut", "run"]
