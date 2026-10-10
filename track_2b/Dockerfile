# Gleichlaut. Two images from one file:
#   base    (what `make run`, `make audit`, `make certify` and `make month-70b` use): Python + lxml. No model weights, no
#           network needed at runtime.
#   offline (`make month`, `make run-offline`, `make certify-build`): adds llama-cpp-python for the local CPU Apertus 8B
#           GGUF lane, the SL default (air-gapped; certified builds: Q8_0 by default, eval/certificates/8b-q8_0-fresh166.json,
#           16 GiB RAM; Q4_K_M for an 8 GiB box, eval/certificates/8b-q4_k_m-fresh166.json).
# Supply chain: every Python package is installed with `pip --require-hashes` from the hash-pinned locks
# (requirements*.txt, generated from requirements*.in by tools/supply_chain.py lock); the SBOM is docs/sbom.json.
# Build-time dependencies (PyPI wheels/sdists, the base image) are fetched here; runtime dependencies are listed in
# docs/dependencies.md. No secrets are baked in: the model endpoint comes from LLM_* environment variables at run time.
# Base image pinned by digest (the multi-arch index of python:3.12-slim as published on Docker Hub, looked up 9 Oct 2026
# via the registry API; its linux/amd64 manifest is sha256:2b4f19dae3a777dfc3b76730bda1e82e1f66ab2a2686fa93ca78edbfb4f04ffe).
# Pulled through Google's public Docker Hub mirror by default: the same digest, no Docker Hub login or rate limit, so a
# Docker Hub outage cannot break `make run`. Override with `--build-arg BASE=python:3.12-slim@sha256:...` (or a registry
# you control); the digest pins the exact image either way.
# To upgrade: look up the new index digest (docs/operations.md, "Upgrade"), replace it here, run `make run` and `make test`.
#
# Closed network (every default below is today's behaviour; docs/deploy/README.md, "Building inside a closed network"):
#   --build-arg BASE=registry.internal.example.ch/library/python:3.12-slim@sha256:a6e34c59...   your registry, same digest
#   --build-arg PIP_INDEX_URL=https://pypi.internal.example.ch/simple    a PyPI mirror (Nexus, Artifactory, devpi); it also
#                                                                        serves pip's build isolation (scikit-build-core)
#   --build-arg PIP_TRUSTED_HOST=pypi.internal.example.ch                only for a plain-HTTP mirror
#   --build-arg APT_MIRROR=http://apt.internal.example.ch                a Debian mirror serving /debian and /debian-security
#                                                                        (replaces http://deb.debian.org; offline image only)
#   --build-arg APT_BUILD=                                               with a prebuilt llama-cpp-python wheel: no compilers
# --require-hashes applies whatever index serves the files: a mirror can only serve the pinned bytes.
ARG BASE=mirror.gcr.io/library/python:3.12-slim@sha256:a6e34c598f2467ed0e9a8d349809fcd8b5c603269512df273a0bb1784edc11b1
FROM ${BASE} AS base
ARG PIP_INDEX_URL=
ARG PIP_TRUSTED_HOST=
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app/src PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
COPY requirements.txt /tmp/requirements.txt
# an empty build arg is unset, so pip keeps its default index (pypi.org); build args are not kept in the image
RUN [ -n "$PIP_INDEX_URL" ] || unset PIP_INDEX_URL; [ -n "$PIP_TRUSTED_HOST" ] || unset PIP_TRUSTED_HOST; \
    pip install --require-hashes -r /tmp/requirements.txt && useradd --create-home --uid 10001 app
WORKDIR /app
COPY --chown=app:app . /app
RUN mkdir -p /app/out /app/state && chown app:app /app /app/out /app/state
USER app
CMD ["python", "-m", "gleichlaut", "run"]

FROM base AS offline
# llama-cpp-python 0.3.35 (the version of the build certificate) is built from source for a generic x86-64/arm64 CPU
# (GGML_NATIVE=OFF: the image runs on any CPU of the architecture, not only the build host's). Its runtime dependencies are
# hash-pinned; its build backend (scikit-build-core, via pip's build isolation) is not covered by --require-hashes.
# APT_RUNTIME (libgomp1) is installed explicitly so that removing the compilers (APT_BUILD) afterwards keeps the OpenMP
# runtime the library links against; the import check fails the build if anything is missing. Both lists are read by
# tools/supply_chain.py into the SBOM. With a prebuilt, hash-pinned llama-cpp-python wheel (docs/deploy/README.md) pip
# compiles nothing: build with --build-arg APT_BUILD= and no compiler or scikit-build-core is fetched.
# The GGUF is not in the image: it is downloaded at run time into the mounted /models and sha256-checked (fetch_gguf).
# (build args end with their stage: the closed-network ones are declared again here)
ARG PIP_INDEX_URL=
ARG PIP_TRUSTED_HOST=
ARG APT_MIRROR=
ARG APT_BUILD="build-essential cmake"
ARG APT_RUNTIME="libgomp1"
USER root
RUN [ -n "$PIP_INDEX_URL" ] || unset PIP_INDEX_URL; [ -n "$PIP_TRUSTED_HOST" ] || unset PIP_TRUSTED_HOST; \
    if [ -n "$APT_MIRROR" ]; then for f in /etc/apt/sources.list.d/debian.sources /etc/apt/sources.list; do \
      if [ -f "$f" ]; then sed -i "s|http://deb.debian.org|$APT_MIRROR|g" "$f"; fi; done; fi; \
    apt-get update && apt-get install -y --no-install-recommends $APT_BUILD $APT_RUNTIME \
 && CMAKE_ARGS="-DGGML_NATIVE=OFF -DLLAMA_CURL=OFF -DLLAMA_BUILD_TESTS=OFF -DLLAMA_BUILD_EXAMPLES=OFF" \
    pip install --require-hashes -r /app/requirements-offline.txt \
 && { [ -z "$APT_BUILD" ] || apt-get purge -y $APT_BUILD; } && apt-get autoremove -y && rm -rf /var/lib/apt/lists/* \
 && python -c "import llama_cpp, numpy; print('llama-cpp-python', llama_cpp.__version__, 'numpy', numpy.__version__)"
USER app
# GLEICHLAUT_GGUF=1: `run` takes the live slice from the local GGUF (n_threads = the CPUs of the container; GLEICHLAUT_THREADS
# overrides). GLEICHLAUT_MODELS: where the GGUF is cached (mount it).
ENV GLEICHLAUT_GGUF=1 GLEICHLAUT_MODELS=/models
CMD ["python", "-m", "gleichlaut", "run"]
