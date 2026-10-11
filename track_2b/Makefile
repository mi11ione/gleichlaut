# Judges run `make run` from this directory on a clean checkout. Everything runs in Docker on CPU.
#   make run            replay + re-score (offline, --network none unless LLM_BASE_URL is set), live slice via
#                       LLM_BASE_URL if set, emit FHIR/XLIFF with validation, build the review page. Outputs -> ./out
#                       A failing live endpoint does not fail the reproduction: "reproduction PASSED; live slice FAILED".
#   make run-offline    the same plus the live slice on a local CPU Apertus 8B GGUF (downloads the selected BUILD once into
#                       ./models: 8.6 GB for the default q8_0, 5.1 GB for BUILD=q4_k_m)
#   make test           unit and reproduction tests (in Docker)
#   make audit          DE<->FR/IT congruence audit of the whole register on the latest feed (AUDIT_DATE=YYYYMMDD for another
#                       date). No model, no endpoint: fetches the public feed if missing -> ./out/audit
#   make feeds          list the published BAG feed dates (public resources API + polite HEAD probes)
# The SL default lane is the local Apertus 8B GGUF on CPU (offline image, air-gapped; PREREG R1). The 70B on a certified
# endpoint is the optional "fewer edits" lane (targets ending in -70b / -endpoint, and the canary).
#   make fetch-gguf     download the pinned 8B GGUF once into ./models (sha256-checked)
#   make certify        build certificate for the pinned 8B GGUF from its recorded run (M2 for q8_0, M1 for q4_k_m;
#                       seconds, no model, no network)
#                       -> ./state, HMAC-signed when GLEICHLAUT_CERT_KEY is set
#   make certify-build  the same certificate by running the frozen 166 suite on THIS machine's CPU (offline image; on 4
#                       cores ~9.2 h for q8_0 at the measured 200.5 s per item, ~7.1 h for q4_k_m at 153.4 s)
#   make certify-endpoint  certify the 70B endpoint in LLM_BASE_URL on the frozen 166-item suite -> ./state
#   make canary         re-run CANARY_N suite items on that endpoint and compare with its certified run (exit 3 on drift)
#   make month                              one month of the public feed in shadow mode with the local 8B (offline image,
#                                           models/ and state/ mounted): FROM=previous TO=latest by default
#   make month FROM=20260901 TO=20261001    a given pair of published feed dates (`make feeds` lists them)
#   make month ITEMS=/path/items.json       pre-publication mode on the SL team's own German changes, --network none
#                                           (the confidential German never leaves the container; run make fetch-gguf first)
#   make month-offline  the same as make month (the name the error message of a missing llama-cpp-python points to)
#   make month-70b      one month through the certified 70B endpoint in LLM_BASE_URL (base image; FROM/TO/ITEMS as above)
#   MONTH_ARGS="--emit ..."  extra arguments for gleichlaut month (e.g. --emit writes XLIFF/FHIR + the review register)
#   make fake-endpoint  an OpenAI-compatible fake on 127.0.0.1:8099 for test environments (FAKE_MODE=recorded|echo|...)
#   make local-run      the same as `make run` without Docker (Python >= 3.9; lxml optional)
#   make pilot-pack     the phase-1 pilot pack (Variante A) as one checksummed, reproducible zip in ./dist (gitignored):
#                       offline register, Fallblätter MD + PDF, Entscheidvorlage, Management-Notiz, Schutzbedarfsanalyse,
#                       Projektauftrag, SHA256SUMS. Fails when the Fallblätter or their PDFs are not current. No model, no network
#   make pilot-pdf      re-render docs/pilot/pdf/ (python-markdown + headless Chrome; dev step, then commit the PDFs)
#   make install-dev    pip install -e . (the `gleichlaut` console script; library: docs/api.md)
#   make lock / sbom    re-lock the hash-pinned requirements (network: PyPI JSON API) / regenerate docs/sbom.json
# Behind a proxy / internal CA: HTTPS_PROXY, HTTP_PROXY, NO_PROXY are passed into the containers; SSL_CERT_FILE and
# REQUESTS_CA_BUNDLE (host paths) are mounted read-only and passed. GLEICHLAUT_CERT_KEY (host path of the certificate HMAC
# key) is mounted read-only. Operator runbook: docs/operations.md. Certificates live in ./state (gitignored), mounted.
.PHONY: run run-offline test certify certify-build certify-endpoint canary month month-offline month-70b fetch-gguf audit feeds \
        fake-endpoint local-run local-test local-audit backtest ui pilot-pack pilot-pdf clean install-dev lock sbom
IMAGE   ?= gleichlaut
NAME    ?= gleichlaut-run-$(shell date +%s)
PROXY    = -e HTTPS_PROXY -e HTTP_PROXY -e NO_PROXY -e https_proxy -e http_proxy -e no_proxy
CA       = $(if $(SSL_CERT_FILE),-v $(abspath $(SSL_CERT_FILE)):/etc/gleichlaut/ca.pem:ro -e SSL_CERT_FILE=/etc/gleichlaut/ca.pem) \
           $(if $(REQUESTS_CA_BUNDLE),-v $(abspath $(REQUESTS_CA_BUNDLE)):/etc/gleichlaut/ca-bundle.pem:ro -e REQUESTS_CA_BUNDLE=/etc/gleichlaut/ca-bundle.pem)
CERTKEY  = $(if $(GLEICHLAUT_CERT_KEY),-v $(abspath $(GLEICHLAUT_CERT_KEY)):/run/secrets/gleichlaut-cert.key:ro -e GLEICHLAUT_CERT_KEY=/run/secrets/gleichlaut-cert.key)
TUNING   = -e GLEICHLAUT_TIMEOUT -e GLEICHLAUT_RETRIES -e GLEICHLAUT_BACKOFF -e GLEICHLAUT_DEADLINE -e GLEICHLAUT_CERT_DAYS \
           -e GLEICHLAUT_CANARY_MAX_AGE_DAYS -e GLEICHLAUT_THREADS -e GLEICHLAUT_DEBUG
ENVS     = -e LLM_NAME -e LLM_BASE_URL -e LLM_API_KEY -e SKIP_MODEL $(TUNING) $(PROXY) $(CA) $(CERTKEY)
# the 8B lane gets no LLM_* variables: it never talks to an endpoint
ENVS8B   = $(TUNING) $(PROXY) $(CA) $(CERTKEY) -e GLEICHLAUT_BUILD=$(BUILD) -e GLEICHLAUT_MODEL_URL -e GLEICHLAUT_MODEL_SHA256 -e GLEICHLAUT_MODELS=/models
NET      = $(if $(LLM_BASE_URL),,--network none)
AS_ME    = --user $$(id -u):$$(id -g)
STATE    = -v $(CURDIR)/state:/app/state -e GLEICHLAUT_STATE=/app/state
CANARY_N ?= 40
# BUILD picks the certified 8B GGUF: q8_0 (8.6 GB, 16 GiB RAM; the default; PREREG R1, M2) or q4_k_m (5.1 GB, 8 GiB RAM;
# M1, for an 8 GiB box). Both pass the pre-registered rule; Q8_0 saves 12.2 points more edits (eval/results/size_compare.json)
BUILD    ?= q8_0
SHA_q8_0   = dea904ad80cd725ec89962abae464477f5d8114d1f4377514f381f7dc2ed202d
SHA_q4_k_m = a037df8d87ff6caacee794ee85f55342f2152e0d359b7389033300c3bee5f299
GGUF_SHA ?= $(SHA_$(BUILD))
GGUF     ?= /models/apertus-v1.5-8b-text-$(BUILD).gguf
MONTH_ARGS ?=
MONTH_SEL = $(if $(ITEMS),--items /app/in/items.json --out /app/out/month/$(basename $(notdir $(ITEMS))),--from $(FROM) --to $(TO) --fetch)
ITEMS_MOUNT = $(if $(ITEMS),-v $(abspath $(ITEMS)):/app/in/items.json:ro)
FROM     ?= previous
TO       ?= latest
AUDIT_DATE ?= latest
FAKE_MODE  ?= recorded

run:
	docker build --target base -t $(IMAGE) .
	docker create --name $(NAME) $(NET) $(ENVS) $(IMAGE) > /dev/null
	docker start -a $(NAME); rc=$$?; mkdir -p out; docker cp $(NAME):/app/out/. out/ > /dev/null 2>&1; \
	  docker rm $(NAME) > /dev/null; exit $$rc

# The GGUF is cached in ./models (sha256-checked); outputs go to ./out, never into the model cache.
run-offline:
	docker build --target offline -t $(IMAGE)-offline .
	mkdir -p models out
	docker run --rm $(ENVS) -e GLEICHLAUT_BUILD=$(BUILD) -e GLEICHLAUT_MODEL_URL -e GLEICHLAUT_MODEL_SHA256 -e GLEICHLAUT_MODELS=/models \
	  $(AS_ME) -v $(CURDIR)/models:/models -v $(CURDIR)/out:/app/out $(IMAGE)-offline

test:
	docker build --target base -t $(IMAGE) .
	docker run --rm --network none $(IMAGE) python tests/run.py

# The build certificate of the pinned 8B GGUF, from its recorded run (PREREG R1; M2 for q8_0, M1 for q4_k_m): re-scored
# here with the frozen checks and that run's labels; PASS only if the pre-registered rule holds. No model, no network. Signed if GLEICHLAUT_CERT_KEY is set.
certify:
	docker build --target base -t $(IMAGE) .
	mkdir -p state
	docker run --rm --network none $(TUNING) $(CERTKEY) $(AS_ME) $(STATE) $(IMAGE) python -m gleichlaut certify \
	  --import-run data/runs/8b_$(BUILD)_fresh166_g3_final.jsonl --gguf-sha256 $(GGUF_SHA) --labels eval/labels/m1_$(BUILD)_fresh166.tsv

# The same certificate from a run of the frozen 166 suite on this machine's CPU (offline image; slow: ~7-9 h on 4 cores).
certify-build:
	docker build --target offline -t $(IMAGE)-offline .
	mkdir -p state models
	docker run --rm $(ENVS8B) $(AS_ME) $(STATE) -v $(CURDIR)/models:/models $(IMAGE)-offline sh -c \
	  'python -m gleichlaut fetch-gguf && exec python -m gleichlaut certify --backend llamacpp --gguf $(GGUF)'

certify-endpoint:
	docker build --target base -t $(IMAGE) .
	mkdir -p state
	docker run --rm $(ENVS) $(AS_ME) $(STATE) $(IMAGE) python -m gleichlaut certify --backend openai

canary:
	docker build --target base -t $(IMAGE) .
	mkdir -p state
	docker run --rm $(ENVS) $(AS_ME) $(STATE) $(IMAGE) python -m gleichlaut certify --backend openai --canary $(CANARY_N)

fetch-gguf:
	docker build --target base -t $(IMAGE) .
	mkdir -p models
	docker run --rm $(PROXY) $(CA) -e GLEICHLAUT_MODEL_URL -e GLEICHLAUT_MODEL_SHA256 -e GLEICHLAUT_MODELS=/models $(AS_ME) \
	  -v $(CURDIR)/models:/models $(IMAGE) python -m gleichlaut fetch-gguf

# The SL default lane: the local 8B GGUF (certified build) in the offline image. models/ holds the GGUF (fetched once,
# sha256-checked), state/ the certificates (`make certify` once; needed only with GLEICHLAUT_CERT_KEY, because the image
# carries the shipped certificate). ITEMS mode runs with --network none.
month:
	docker build --target offline -t $(IMAGE)-offline .
	mkdir -p state out/month out/hist models
	docker run --rm $(if $(ITEMS),--network none) $(ENVS8B) $(AS_ME) $(STATE) -v $(CURDIR)/models:/models \
	  -v $(CURDIR)/out:/app/out $(ITEMS_MOUNT) $(IMAGE)-offline sh -c \
	  '$(if $(ITEMS),,python -m gleichlaut fetch-gguf && )exec python -m gleichlaut month --backend llamacpp --gguf $(GGUF) $(MONTH_SEL) $(MONTH_ARGS)'

month-offline: month

# The optional "fewer edits" lane: the 70B through the certified endpoint in LLM_BASE_URL (make certify-endpoint first).
month-70b:
	docker build --target base -t $(IMAGE) .
	mkdir -p state out/month out/hist
	docker run --rm $(ENVS) $(AS_ME) $(STATE) -v $(CURDIR)/out:/app/out $(ITEMS_MOUNT) \
	  $(IMAGE) python -m gleichlaut month --backend openai $(if $(ALLOW_STALE_CANARY),--allow-stale-canary) $(MONTH_SEL) $(MONTH_ARGS)

# The audit needs no model and no endpoint: only the public feed of one date (fetched once, ~3 x 90 MB streamed into
# ~3 x 5.5 MB snapshots under out/hist). AUDIT_ARGS is passed through to `gleichlaut audit`.
audit:
	docker build --target base -t $(IMAGE) .
	mkdir -p out/hist out/audit
	docker run --rm $(PROXY) $(CA) $(AS_ME) -v $(CURDIR)/out:/app/out $(IMAGE) sh -c '\
	  d=$(AUDIT_DATE); if [ "$$d" = latest ]; then d=$$(python -m gleichlaut feeds --latest) || exit 6; fi; \
	  for L in de fr it; do [ -f out/hist/$$d-$$L.json ] || python -m gleichlaut.sl.ingest $$d --langs $$L || exit 6; done; \
	  T=; [ $$(ls out/hist/*-de.json 2>/dev/null | wc -l) -lt 2 ] && { T="--terms data/audit/term_pairs_20261006.json"; \
	    echo "one snapshot only: terminology uses the term pairs learned from the 2026 snapshots (data/audit/term_pairs_20261006.json)"; }; \
	  python -m gleichlaut audit --hist out/hist --date $$d --out out/audit $$T $(AUDIT_ARGS)'

feeds:
	docker build --target base -t $(IMAGE) .
	mkdir -p out/hist
	docker run --rm $(PROXY) $(CA) $(AS_ME) -v $(CURDIR)/out:/app/out $(IMAGE) python -m gleichlaut feeds $(FEEDS_ARGS)

fake-endpoint:
	PYTHONPATH=src python3 -m gleichlaut.fake_endpoint --port 8099 --mode $(FAKE_MODE)

local-run:
	PYTHONPATH=src python3 -m gleichlaut run

local-test:
	PYTHONPATH=src python3 tests/run.py

local-audit:
	PYTHONPATH=src python3 -m gleichlaut audit $(AUDIT_ARGS)

backtest:
	PYTHONPATH=src python3 -m gleichlaut backtest

ui:
	PYTHONPATH=src python3 -m gleichlaut ui --out out/ui/index.html

pilot-pack:
	python3 tools/pilot_pack.py

pilot-pdf:
	python3 tools/pilot_sheets.py && python3 tools/pilot_pdf.py

install-dev:
	python3 -m pip install -e .

lock:
	python3 tools/supply_chain.py lock
	python3 tools/supply_chain.py sbom

sbom:
	python3 tools/supply_chain.py sbom

clean:
	rm -rf out
