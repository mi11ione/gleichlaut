# Operations runbook

For the person who runs Gleichlaut each month: install, configure, certify the model endpoint, run the month, hand the
XLIFF to the translators, and know what each exit code and file means. The research and evaluation background is in the
[README](../README.md) and the [technical report](../technical_report.md).

All commands run from `track_2b/`. `make` targets run in Docker. The same commands without Docker are
`PYTHONPATH=src python3 -m gleichlaut <command>`.

## 1. Install

**Docker (recommended).** Docker 24+ on any x86-64 or arm64 Linux/macOS host, 2 CPU cores, 4 GB RAM, about 1 GB disk
plus about 16 MB for each feed date you keep.

```bash
git clone <repo> && cd gleichlaut/track_2b
make run        # builds the image (base pinned by digest in the Dockerfile) and checks the reproduction offline
make test
```

`make run` must end with `make run: reproduction PASSED; live slice SKIPPED` (with no endpoint configured) or
`... live slice PASSED`. A failing endpoint prints `LIVE SLICE FAILED: <reason>` and
`reproduction PASSED; live slice FAILED`. The reproduction still counts in that case: fix the endpoint before you draft.

**Plain Python.** Python 3.9 or newer and `pip install -r requirements.txt` (lxml, used only for XLIFF/FHIR validation).
Then use `make local-run` / `make local-test`, or `PYTHONPATH=src python3 -m gleichlaut ...`.

**Air-gapped 8B lane (optional).** `make run-offline` builds the `offline` image with llama-cpp-python and downloads the
pinned Apertus 8B GGUF once into `./models` (sha256-checked). On the SL lane the 8B is not certified, so every item it
drafts goes to review.

## 2. Configuration (`.env` / environment)

Copy `.env.example` to `.env` and export it (`set -a; . ./.env; set +a`). `make` passes the `LLM_*` variables into the
container. The key is never written to any file Gleichlaut creates.

| Variable | Meaning | Default |
|---|---|---|
| `LLM_BASE_URL` | OpenAI-compatible endpoint serving Apertus 70B, e.g. `https://llm.internal.example/v1` | unset: no live calls |
| `LLM_API_KEY` | bearer key for that endpoint | empty |
| `LLM_NAME` | model id to request | `swiss-ai/apertus-v1.5-70b` |
| `GLEICHLAUT_STATE` | certificates, certification runs, canary reports | `./state` (gitignored; mounted by `make`) |
| `GLEICHLAUT_OUT` | outputs of `run` | `./out` |
| `GLEICHLAUT_HIST` | feed snapshots (compact JSON per date and language) | `./out/hist` |
| `GLEICHLAUT_HTTP_TIMEOUT` / `_RETRIES` / `_BACKOFF` | per-request timeout (s), attempts, back-off step (s) on 429/5xx/unreachable | 300 / 8 / 10 |
| `SKIP_MODEL=1` | skip the live slice in `make run` | |
| `GLEICHLAUT_GATEWAY_DIR` | development gateway to Public AI. Evaluation only, never in production | unset |
| `GLEICHLAUT_DEBUG=1` | show Python tracebacks instead of one-line errors | |

## 3. Certify the endpoint (once per endpoint and model, and again after every change)

The SL lane drafts only through an endpoint that has a **PASS endpoint certificate** for exactly that endpoint
(scheme, host, port and path of `LLM_BASE_URL`) and exactly that `LLM_NAME`, made with the current frozen code and
suite. A model that merely calls itself `apertus-v1.5-70b` is not enough. Neither are the certificates shipped in
`eval/certificates/`: those are evaluation evidence (`kind: replay` or `kind: evaluation`) and never authorise drafting.

```bash
make certify                     # 166 items, about 285 requests, under an hour (2 workers); ~CHF 0.40
PYTHONPATH=src python3 -m gleichlaut certify --list      # what is in ./state/certificates
```

Results go to `./state/`:

| Path | Contents |
|---|---|
| `state/certificates/<name>.json` | `kind` (`endpoint`), `endpoint` (no key), `model_requested`, `models_served`, `system_fingerprints`, `seeds`, `freeze_sha256`, suite sha256, metrics, `status`, `needs_review` |
| `state/certificates/<name>.calls.jsonl` | the call log of the certification run |
| `state/runs/certify_<name>.jsonl` | the 166 suite records (what the canary compares against) |
| `state/cache/<name>/` | every raw response, addressed by the sha256 of its request |

Exit codes: `0` PASS, `5` FAIL (do not use this endpoint for the SL lane), `7` PENDING_REVIEW. PENDING_REVIEW means
the automatic criteria are met, but some ready outputs differ from every output already hand-labelled. Label each key in
`needs_review` (classes: `equivalent preexisting cosmetic minor german stale REAL garble`) in a TSV file with the
header `key<TAB>class`, then:

```bash
PYTHONPATH=src python3 -m gleichlaut certify --resolve state/certificates/<name>.json --labels my-labels.tsv
```

The newest certificate for an endpoint and model decides. A later FAIL revokes an earlier PASS. A change to the frozen
code or the suite invalidates every certificate, and you must certify again.

**When to re-certify:** a new endpoint URL, a new `LLM_NAME`, a model or serving-stack upgrade announced by the
provider, a canary failure, or a Gleichlaut upgrade that changes `eval/prereg/freeze.json`.

## 4. Canary (monthly, before drafting)

```bash
make canary                      # CANARY_N=40 by default: about 70 requests, a few minutes
```

The canary re-runs the first N suite items and compares them with this endpoint's certified run. At temperature 0 the
70B lane is not byte-deterministic. A seeded re-run of the fresh 166 gave 69.9% identical outputs but flag agreement of
163/166 (κ 0.963), with exact 17.5% → 18.1% (`eval/results/m3.json`). So byte identity is reported as information only.
The canary **fails (exit 3)** if:

- flag agreement < **0.85** (the measured disagreement is 1.8%; 15% means the guards are seeing a different model), or
- exact match drops by more than **5 points** against the certified run on the same items (measured change +0.6; 5 is
  also the pass rule's minimum gain over rules-only), or
- a served model id was not seen at certification.

Reports go to `state/canary/<name>.json` (agreement, exact now/then, flag rates, byte identity, fingerprints now/then).
On a failure, stop: re-certify, or draft with `--air-gapped` (every item goes to review).

## 5. The monthly procedure

There are two modes. Both write to `out/month/<run>/` and resume where they stopped.

### 5a. Pre-publication: the SL team's own German changes (the real use)

The SL team exports the month's German amendments as an item file: a JSON array, or JSON Lines, following
[`docs/item-schema.json`](item-schema.json). Required: `key`, `lang` (`fr`|`it`), `de_old`, `de_new`, `tgt_old`.
Optional: `product`, `cud_old`, `cud_new`, `mpd`, `snap_old`, `snap_new`, `note`, `change_ratio`. There is one item
per target language. `tgt_new` is left out (nothing is published yet).

```bash
make month ITEMS=/path/to/sl-team-2026-11.json        # mounted read-only into the container
# or: PYTHONPATH=src python3 -m gleichlaut month --items sl-team-2026-11.json --out out/month/2026-11
```

### 5b. Shadow mode: the public feed (validation, monthly regression check)

After BAG publishes a month, run the same pipeline on what changed between two feed dates. FR/IT texts that BAG already
published become `tgt_new`. They are never shown to the model and are used only to score the drafts (`shadow_exact`).

```bash
make month FROM=20261001 TO=20261101          # downloads the six de/fr/it feeds of both dates if missing
# or: PYTHONPATH=src python3 -m gleichlaut month --from 20261001 --to 20261101 --fetch [--snapshots DIR]
```

Feeds are streamed into compact snapshots (`out/hist/<YYYYMMDD>-<lang>.json`, about 5.5 MB each). The raw NDJSON is
not kept unless you pass `--keep-raw DIR` to `gleichlaut.sl.ingest`. `ingest latest` stores the 'latest' feed under its
real publication date (feed timestamp, else HTTP Last-Modified as a Zurich date), with a `latest-<lang>.json` alias.
`out/hist/latest.json` records the date and how it was established. The 4 May 2026 feed is refused (publisher bug).

### What a month run does

1. **Items.** It reads the item file, or mines every German change between the two dates. For a feed run it also
   writes `unmatched.json`, which lists changes with no old FR/IT text under the same id. It validates the items
   against the schema and computes `change_ratio` where it is missing (the `sl.mine` rule).
2. **Routing.** If more than 60% of the German tokens changed, or the German is longer than 2500 characters, the item
   goes to `status: human` with a reason and is not drafted. A spacing-only change also goes to a human.
3. **Gate.** On the SL lane through `openai`, the run continues only with a PASS endpoint certificate (else exit 4).
4. **Drafting.** Items are drafted one at a time through the backend. After each item, one JSON line is appended to
   `records.jsonl` and flushed. After a crash or Ctrl-C, run the same command again: finished keys are skipped and a
   torn last line is cut off. `--restart` sets the old records aside.
5. **Summary.** `summary.json` and a printed digest hold: counts by status and language, reasons, rule-only and
   re-asked counts, the shadow comparison (identical-to-published, and every *ready* draft that differs, to check),
   calls, tokens, the CHF estimate, models served and fingerprints.

Record `status`: `ready` (every guard passed: the translator accepts or edits it), `flagged` (a guard named a problem,
or a review policy applies: `review_reason` says which, e.g. air-gapped, stub, statute lane), `human` (not drafted).
`guard_status` keeps the guards' own verdict.

Check before a run, with no request sent: `--dry-run` prints, per item, the routing, the slot map (which number each
⟨code⟩ stands for) and the exact first prompt. It also says whether the certification gate would pass.

Backends: `openai` (production), `llamacpp` (local 8B, review-only on SL), `cache` (recorded responses), and `stub`
(returns the old text unchanged; for wiring tests only; every stub record is marked for review).

### 5c. From records to the translators

`month` and `draft` write records and items. The XLIFF, FHIR and the review page are made from them:

```bash
gleichlaut emit --records out/month/<run>/records.jsonl --items out/month/<run>/items.json --n 0 --out out/month/<run>/emit
gleichlaut ui   --records out/month/<run>/records.jsonl --items out/month/<run>/items.json --out out/month/<run>/ui/index.html
# or add --emit to the month/draft command
```

- `emit/xliff/*.xlf` is **XLIFF 2.1** (one file per target language, validated against the OASIS XSD). A `*.xliff12.xlf`
  copy is written for CAT tools that only import XLIFF 1.2. Put the files on the share or in the job queue the
  translation service already uses. The translators open them in their own CAT tool: ready drafts arrive as
  translated segments to accept, flagged ones with the guard complaint as a note, and human-routed items without a
  target. Gleichlaut does not push anything anywhere.
- `emit/fhir/*.fhir.json` holds ClinicalUseDefinition bundles in the shape of BAG's ePL feed (validated against the
  CH EPL profile).
- `ui/index.html` is one self-contained review page (works from `file://`, makes no requests). Reviewer decisions stay
  in the browser until "Export decisions".

## 6. Exit codes

| Code | Meaning | What to do |
|---|---|---|
| 0 | success | |
| 1 | reproduction or validation failed (`run`, `replay`, `emit`) | do not use this build; see the step that failed |
| 2 | usage error, bad item file (message lists the schema problems), missing configuration (`LLM_BASE_URL` unset, gateway dir unset), missing snapshots | fix the input or the configuration |
| 3 | canary outside tolerance | re-certify, or `--air-gapped` |
| 4 | refused: endpoint not certified for this model | `make certify` |
| 5 | certificate FAIL | do not use the endpoint for the SL lane |
| 6 | endpoint or feed failed (unreachable, timeout, HTTP error after retries, non-Apertus model served, served model not seen at certification). For `live`: the live slice failed | records so far are kept; fix and re-run to resume |
| 7 | certificate PENDING_REVIEW | label `needs_review`, then `certify --resolve` |
| 130 | interrupted | re-run to resume |

Errors are one line on stderr, with no traceback (`GLEICHLAUT_DEBUG=1` shows it). `make run` exits 0 when the
reproduction passes, even if the live slice failed. Look for `LIVE SLICE FAILED`.

## 7. Logs

Every live call appends one JSON line to `calls.jsonl` (in the month directory, in `state/certificates/` for
certification, in `state/canary/` for the canary, and `out/live_calls.jsonl` for the live slice):

| Field | Meaning |
|---|---|
| `ts` | UTC time of the answer |
| `endpoint` | scheme://host[:port]/path (never the key) |
| `model` / `model_served` | requested / reported by the endpoint (non-Apertus answers are refused) |
| `system_fingerprint` (`backend`: same value, older name) | serving build reported by the endpoint |
| `seed` | request seed (none in production) |
| `prompt_tokens`, `completion_tokens`, `secs` | usage and latency |
| `key` | sha256 of the exact request payload: the file name of the raw response in `cache/` |
| `tag` | which step: `gl-70b-v2` (draft or lock retry), `gl-70b-guard` (re-ask) |
| `cached` | false for live calls |

The log carries no prompt and no answer text. Answers are in `cache/<key[:2]>/<key>.json`, and the final text is in
`records.jsonl`. Prompts are rebuilt deterministically from the items (`--dry-run`).

## 8. Retention

| What | Where | Suggested retention |
|---|---|---|
| Certificates, their call logs and suite records | `state/certificates/`, `state/runs/` | keep for as long as any draft made under them is kept (they are the evidence the endpoint was fit) |
| Canary reports | `state/canary/` | 2 years |
| Month records, items, summary, emitted XLIFF/FHIR, review page | `out/month/<run>/` | the organisation's records-retention rule for translation work |
| Raw responses | `out/month/<run>/cache/`, `state/cache/` | until the month's review is closed; needed only to re-check or replay a draft |
| Feed snapshots | `out/hist/` | the two most recent dates are enough for operation; keep more only for backtests |
| Raw feeds | not stored (unless `--keep-raw`) | |

The data are official federal publications. The SL team's pre-publication German is internal until BAG publishes it,
so treat `out/month/` of a pre-publication run accordingly. No personal data is processed.

## 9. What leaves the network

- **To the model endpoint (`LLM_BASE_URL`), and only there:** per request, the German old and new text of one
  limitation and its current French or Italian text, with every number replaced by a slot code, plus the bearer key.
  In pre-publication mode the German is **not yet public**, so use an endpoint you control (own hardware or a
  contracted Swiss-resident provider). Public AI was used for evaluation only. It may route outside Switzerland, so it
  is not a production endpoint.
- **To BAG (`epl.bag.admin.ch`), only with `--fetch` / `gleichlaut.sl.ingest`:** plain GET requests for the public feeds.
- **Nothing else.** There is no telemetry and no update check. The review page makes no requests. With no
  `LLM_BASE_URL`, `make run` runs with `--network none`. The air-gapped lanes (8B GGUF on CPU) contact nothing after
  the one-time model download.
- At build time only: the Docker base image (pinned by digest) and PyPI wheels (`docs/dependencies.md`).

## 10. Upgrade

1. Read the release notes. Check whether `eval/prereg/freeze.json` changed. If it did, every certificate stops
   counting.
2. `git pull` (or unpack the release), then `make test` and `make run`. Both must pass (`reproduction PASSED`).
3. Base image: the Dockerfile pins `python:3.12-slim` by digest. To move to a newer patch, look up the index digest
   (`curl -sI -H "Authorization: Bearer $(curl -s 'https://auth.docker.io/token?service=registry.docker.io&scope=repository:library/python:pull' | python3 -c 'import json,sys;print(json.load(sys.stdin)["token"])')" -H 'Accept: application/vnd.oci.image.index.v1+json' https://registry-1.docker.io/v2/library/python/manifests/3.12-slim | grep -i docker-content-digest`),
   replace it, and run `make test` and `make run` again.
4. If the frozen code, the endpoint, or its model changed, run `make certify` again, then `make canary`.
5. Keep `state/` across upgrades. It is outside the source tree and mounted into the container.

## 11. Quick reference

```bash
make certify                                   # once per endpoint + model; exit 0 / 5 / 7
make canary                                    # monthly; exit 3 on drift
make month ITEMS=sl-team.json                  # pre-publication drafting
make month FROM=20261001 TO=20261101           # shadow mode on the public feed
PYTHONPATH=src python3 -m gleichlaut month --items sl-team.json --dry-run     # prompts, slot maps, routing; no request
PYTHONPATH=src python3 -m gleichlaut draft --items x.json --out out/x --backend stub   # wiring test, no model
```
