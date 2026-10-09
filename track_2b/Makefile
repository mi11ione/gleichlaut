# Judges run `make run` from this directory on a clean checkout. Everything runs in Docker on CPU.
#   make run            replay + re-score (offline, --network none unless LLM_BASE_URL is set), live slice via
#                       LLM_BASE_URL if set, emit FHIR/XLIFF with validation, build the review page. Outputs -> ./out
#   make run-offline    the same plus the live slice on a local CPU Apertus 8B GGUF (downloads ~5 GB once into ./models)
#   make test           unit and reproduction tests (in Docker)
#   make certify        certify the endpoint in LLM_BASE_URL on the frozen 166-item suite (SL lane gate)
#   make local-run      the same as `make run` without Docker (Python >= 3.9; lxml optional)
.PHONY: run run-offline test certify local-run local-test backtest ui clean
IMAGE   ?= gleichlaut
NAME    ?= gleichlaut-run-$(shell date +%s)
ENVS     = -e LLM_NAME -e LLM_BASE_URL -e LLM_API_KEY -e SKIP_MODEL
NET      = $(if $(LLM_BASE_URL),,--network none)

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
	docker run --rm $(ENVS) $(IMAGE) python -m gleichlaut certify --backend openai

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
