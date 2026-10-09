# Judges run `make run` from this directory on a clean checkout. Everything runs in Docker on CPU.
#   make run            replay + re-score (offline, --network none unless LLM_BASE_URL is set), live slice via
#                       LLM_BASE_URL if set, emit FHIR/XLIFF with validation, build the review page. Outputs -> ./out
#                       A failing live endpoint does not fail the reproduction: "reproduction PASSED; live slice FAILED".
#   make run-offline    the same plus the live slice on a local CPU Apertus 8B GGUF (downloads ~5 GB once into ./models)
#   make test           unit and reproduction tests (in Docker)
#   make certify        certify the endpoint in LLM_BASE_URL on the frozen 166-item suite (SL lane gate) -> ./state
#   make canary         re-run CANARY_N suite items on that endpoint and compare with its certified run (exit 3 on drift)
#   make month FROM=YYYYMMDD TO=YYYYMMDD   one month of the public feed in shadow mode (fetches the feeds) -> ./out/month
#   make month ITEMS=/path/items.json      pre-publication mode on the SL team's own German changes
#   make local-run      the same as `make run` without Docker (Python >= 3.9; lxml optional)
# Operator runbook: docs/operations.md. Certificates and their logs live in ./state (gitignored), mounted into the container.
.PHONY: run run-offline test certify canary month local-run local-test backtest ui clean
IMAGE   ?= gleichlaut
NAME    ?= gleichlaut-run-$(shell date +%s)
ENVS     = -e LLM_NAME -e LLM_BASE_URL -e LLM_API_KEY -e SKIP_MODEL
NET      = $(if $(LLM_BASE_URL),,--network none)
AS_ME    = --user $$(id -u):$$(id -g)
STATE    = -v $(CURDIR)/state:/app/state -e GLEICHLAUT_STATE=/app/state
CANARY_N ?= 40
BACKEND  ?= openai

run:
	docker build --target base -t $(IMAGE) .
	docker create --name $(NAME) $(NET) $(ENVS) $(IMAGE) > /dev/null
	docker start -a $(NAME); rc=$$?; mkdir -p out; docker cp $(NAME):/app/out/. out/ > /dev/null 2>&1; \
	  docker rm $(NAME) > /dev/null; exit $$rc

run-offline:
	docker build --target offline -t $(IMAGE)-offline .
	mkdir -p models
	docker run --rm $(ENVS) -e GLEICHLAUT_MODEL_URL -e GLEICHLAUT_MODEL_SHA256 -e GLEICHLAUT_MODELS=/models \
	  -e GLEICHLAUT_OUT=/models/out --user $$(id -u):$$(id -g) -v $(CURDIR)/models:/models $(IMAGE)-offline

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
	  $(IMAGE) python -m gleichlaut month --backend $(BACKEND) \
	  $(if $(ITEMS),--items /app/in/items.json --out /app/out/month/$(basename $(notdir $(ITEMS))),--from $(FROM) --to $(TO) --fetch)

local-run:
	PYTHONPATH=src python3 -m gleichlaut run

local-test:
	PYTHONPATH=src python3 tests/run.py

backtest:
	PYTHONPATH=src python3 -m gleichlaut backtest

ui:
	PYTHONPATH=src python3 -m gleichlaut ui --out out/ui/index.html

clean:
	rm -rf out
