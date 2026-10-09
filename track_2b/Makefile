# Judges run `make run` from this directory on a clean checkout. Everything runs in Docker on CPU.
#   make run            replay + re-score (offline, --network none unless LLM_BASE_URL is set), live slice via
#                       LLM_BASE_URL if set, emit FHIR/XLIFF with validation, build the review page. Outputs -> ./out
#                       A failing live endpoint does not fail the reproduction: "reproduction PASSED; live slice FAILED".
#   make run-offline    the same plus the live slice on a local CPU Apertus 8B GGUF (downloads ~5 GB once into ./models)
#   make test           unit and reproduction tests (in Docker)
#   make audit          DE<->FR/IT congruence audit of the whole register on the latest feed (AUDIT_DATE=YYYYMMDD for another
#                       date). No model, no endpoint: fetches the public feed if missing -> ./out/audit
#   make feeds          list the published BAG feed dates (public resources API + polite HEAD probes)
#   make certify        certify the endpoint in LLM_BASE_URL on the frozen 166-item suite (SL lane gate) -> ./state
#   make canary         re-run CANARY_N suite items on that endpoint and compare with its certified run (exit 3 on drift)
#   make month                              one month of the public feed in shadow mode: FROM=previous TO=latest by default
#   make month FROM=20260901 TO=20261001    a given pair of published feed dates (`make feeds` lists them)
#   make month ITEMS=/path/items.json       pre-publication mode on the SL team's own German changes
#   make fake-endpoint  an OpenAI-compatible fake on 127.0.0.1:8099 for test environments (FAKE_MODE=recorded|echo|...)
#   make local-run      the same as `make run` without Docker (Python >= 3.9; lxml optional)
# Behind a proxy / internal CA: HTTPS_PROXY, HTTP_PROXY, NO_PROXY are passed into the containers; SSL_CERT_FILE and
# REQUESTS_CA_BUNDLE (host paths) are mounted read-only and passed. GLEICHLAUT_CERT_KEY (host path of the certificate HMAC
# key) is mounted read-only. Operator runbook: docs/operations.md. Certificates live in ./state (gitignored), mounted.
.PHONY: run run-offline test certify canary month audit feeds fake-endpoint local-run local-test local-audit backtest ui clean
IMAGE   ?= gleichlaut
NAME    ?= gleichlaut-run-$(shell date +%s)
PROXY    = -e HTTPS_PROXY -e HTTP_PROXY -e NO_PROXY -e https_proxy -e http_proxy -e no_proxy
CA       = $(if $(SSL_CERT_FILE),-v $(abspath $(SSL_CERT_FILE)):/etc/gleichlaut/ca.pem:ro -e SSL_CERT_FILE=/etc/gleichlaut/ca.pem) \
           $(if $(REQUESTS_CA_BUNDLE),-v $(abspath $(REQUESTS_CA_BUNDLE)):/etc/gleichlaut/ca-bundle.pem:ro -e REQUESTS_CA_BUNDLE=/etc/gleichlaut/ca-bundle.pem)
CERTKEY  = $(if $(GLEICHLAUT_CERT_KEY),-v $(abspath $(GLEICHLAUT_CERT_KEY)):/run/secrets/gleichlaut-cert.key:ro -e GLEICHLAUT_CERT_KEY=/run/secrets/gleichlaut-cert.key)
TUNING   = -e GLEICHLAUT_TIMEOUT -e GLEICHLAUT_RETRIES -e GLEICHLAUT_BACKOFF -e GLEICHLAUT_DEADLINE -e GLEICHLAUT_CERT_DAYS \
           -e GLEICHLAUT_CANARY_MAX_AGE_DAYS -e GLEICHLAUT_THREADS -e GLEICHLAUT_DEBUG
ENVS     = -e LLM_NAME -e LLM_BASE_URL -e LLM_API_KEY -e SKIP_MODEL $(TUNING) $(PROXY) $(CA) $(CERTKEY)
NET      = $(if $(LLM_BASE_URL),,--network none)
AS_ME    = --user $$(id -u):$$(id -g)
STATE    = -v $(CURDIR)/state:/app/state -e GLEICHLAUT_STATE=/app/state
CANARY_N ?= 40
BACKEND  ?= openai
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
	docker run --rm $(ENVS) -e GLEICHLAUT_MODEL_URL -e GLEICHLAUT_MODEL_SHA256 -e GLEICHLAUT_MODELS=/models \
	  $(AS_ME) -v $(CURDIR)/models:/models -v $(CURDIR)/out:/app/out $(IMAGE)-offline

test:
	docker build --target base -t $(IMAGE) .
	docker run --rm --network none $(IMAGE) python tests/run.py

certify:
	docker build --target base -t $(IMAGE) .
	mkdir -p state
	docker run --rm $(ENVS) $(AS_ME) $(STATE) $(IMAGE) python -m gleichlaut certify --backend openai

canary:
	docker build --target base -t $(IMAGE) .
	mkdir -p state
	docker run --rm $(ENVS) $(AS_ME) $(STATE) $(IMAGE) python -m gleichlaut certify --backend openai --canary $(CANARY_N)

month:
	docker build --target base -t $(IMAGE) .
	mkdir -p state out/month out/hist
	docker run --rm $(ENVS) $(AS_ME) $(STATE) -v $(CURDIR)/out:/app/out $(if $(ITEMS),-v $(abspath $(ITEMS)):/app/in/items.json:ro) \
	  $(IMAGE) python -m gleichlaut month --backend $(BACKEND) $(if $(ALLOW_STALE_CANARY),--allow-stale-canary) \
	  $(if $(ITEMS),--items /app/in/items.json --out /app/out/month/$(basename $(notdir $(ITEMS))),--from $(FROM) --to $(TO) --fetch)

# The audit needs no model and no endpoint: only the public feed of one date (fetched once, ~3 x 90 MB streamed into
# ~3 x 5.5 MB snapshots under out/hist). AUDIT_ARGS is passed through to `gleichlaut audit`.
audit:
	docker build --target base -t $(IMAGE) .
	mkdir -p out/hist out/audit
	docker run --rm $(PROXY) $(CA) $(AS_ME) -v $(CURDIR)/out:/app/out $(IMAGE) sh -c '\
	  d=$(AUDIT_DATE); if [ "$$d" = latest ]; then d=$$(python -m gleichlaut feeds --latest) || exit 6; fi; \
	  for L in de fr it; do [ -f out/hist/$$d-$$L.json ] || python -m gleichlaut.sl.ingest $$d --langs $$L || exit 6; done; \
	  python -m gleichlaut audit --hist out/hist --date $$d --out out/audit $(AUDIT_ARGS)'

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

clean:
	rm -rf out
