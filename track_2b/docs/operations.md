# Operations runbook

For the person who runs Gleichlaut each month: install, configure, certify the model endpoint, run the month, hand the
XLIFF to the translators, and know what each exit code and file means. **If you can do only one thing tomorrow, run the
audit (§0): it needs no model, no endpoint and no IT approval.** The research and evaluation background is in the
[README](../README.md) and the [technical report](../technical_report.md).

All commands run from `track_2b/`. `make` targets run in Docker. The same commands without Docker are
`PYTHONPATH=src python3 -m gleichlaut <command>`.

## 0. Use it tomorrow: the congruence audit (monthly or quarterly, no model)

```bash
make audit                         # Docker: fetch the latest public feed if missing, audit every limitation -> out/audit/
make audit AUDIT_DATE=20261001     # a given feed date (`make feeds` lists the published ones)
PYTHONPATH=src python3 -m gleichlaut audit --hist out/hist --date 20261006 --out out/audit    # without Docker
```

`gleichlaut audit` compares the numbers of every German limitation with its French and Italian text and lists the
divergences that are already published (a dose, a duration, an age that differs between the languages). It is
deterministic, uses only the public feed (three plain GET requests to `epl.bag.admin.ch`, or none if the snapshots are
already in `out/hist/`), sends nothing anywhere, and calls no model, so it needs no endpoint, no certificate and no
approval for a new IT service. Run it after each monthly publication, or at least once a quarter before the triennial
review. Output: `out/audit/audit_<date>.json` (every finding with its context) and `audit_<date>_summary.json`. The
rules and their measured precision are in [docs/audit.md](audit.md). All arguments of `gleichlaut audit` are passed
through unchanged (`AUDIT_ARGS=...` with `make`).

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

Copy `.env.example` to `.env` and export it (`set -a; . ./.env; set +a`). `make` passes the `LLM_*`, `GLEICHLAUT_*` tuning
and proxy variables into the container. The key is never written to any file Gleichlaut creates.

| Variable | Meaning | Default |
|---|---|---|
| `LLM_BASE_URL` | OpenAI-compatible endpoint serving Apertus 70B, e.g. `https://llm.internal.example/v1` | unset: no live calls |
| `LLM_API_KEY` | bearer key for that endpoint | empty |
| `LLM_NAME` | model id to request | `swiss-ai/apertus-v1.5-70b` |
| `GLEICHLAUT_STATE` | certificates, certification runs, canary reports | `./state` (gitignored; mounted by `make`) |
| `GLEICHLAUT_OUT` | outputs of `run` | `./out` |
| `GLEICHLAUT_HIST` | feed snapshots (compact JSON per date and language) | `./out/hist` |
| `GLEICHLAUT_TIMEOUT` | seconds per attempt of one model request | 120 |
| `GLEICHLAUT_RETRIES` | attempts per request on 429 / 5xx / unreachable / timeout | 4 |
| `GLEICHLAUT_BACKOFF` | back-off step in seconds, doubled after each attempt (5, 10, 20) | 5 |
| `GLEICHLAUT_DEADLINE` | at most this many seconds for one request over all its attempts: a dead endpoint fails within about 5 minutes (exit 6) | 300 |
| `GLEICHLAUT_CERT_DAYS` | validity of a new certificate, and the maximum age the gate accepts | 90 |
| `GLEICHLAUT_CANARY_MAX_AGE_DAYS` | the SL lane refuses to draft when the latest canary (or the certification) is older | 31 |
| `GLEICHLAUT_CERT_KEY` | path of a file with a secret key (≥ 16 bytes): certificates and canary reports are HMAC-signed, unsigned ones refused. Keep it outside `state/` | unset |
| `HTTPS_PROXY`, `HTTP_PROXY`, `NO_PROXY` | outgoing proxy for the endpoint, the BAG feed and the GGUF download (`make` passes them into the containers) | unset |
| `SSL_CERT_FILE` (or `REQUESTS_CA_BUNDLE`) | PEM file of an internal / TLS-inspecting proxy CA, trusted in addition to the system store. `make` mounts the host file read-only into the container | unset |
| `GLEICHLAUT_THREADS` | llama.cpp threads for the local 8B (default: the CPUs of the container) | CPU count |
| `SKIP_MODEL=1` | skip the live slice in `make run` | |
| `GLEICHLAUT_GATEWAY_DIR` | development gateway to Public AI. Evaluation only, never in production | unset |
| `GLEICHLAUT_DEBUG=1` | show Python tracebacks instead of one-line errors | |

The older names `GLEICHLAUT_HTTP_TIMEOUT` / `_HTTP_RETRIES` / `_HTTP_BACKOFF` still work. TLS verification is never
switched off: behind a TLS-inspecting proxy, give its CA in `SSL_CERT_FILE`.

## 3. Certify the endpoint (once per endpoint and model, and again after every change)

The SL lane drafts only through an endpoint that has a **PASS endpoint certificate** for exactly that endpoint
(scheme, host, port and path of `LLM_BASE_URL`) and exactly that `LLM_NAME`, made with the current frozen code and
suite. A model that merely calls itself `apertus-v1.5-70b` is not enough. Neither are the certificates shipped in
`eval/certificates/`: those are evaluation evidence (`kind: replay` or `kind: evaluation`) and never authorise drafting.

```bash
make certify                     # 166 items, about 285 requests, under an hour (2 workers); ~CHF 0.40
PYTHONPATH=src python3 -m gleichlaut certify --list      # what is in ./state/certificates, each one re-verified
```

Results go to `./state/`:

| Path | Contents |
|---|---|
| `state/certificates/<name>.json` | `kind` (`endpoint`), `endpoint` (no key), `model_requested`, `models_served`, `system_fingerprints`, `seeds`, `freeze_sha256`, suite sha256, metrics, `status`, `needs_review`, `expires`, `run_records_sha256`, `calls_log_sha256` (and `labels_sha256` after `--resolve`), `hmac_sha256` if a key is set |
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

**A certificate is re-checked every time it is used.** The gate does not trust the `status` field. Before every
`draft`/`month` on the SL lane (and in `certify --list` and `--canary`) it checks that the certificate:

- is not expired. `expires` is the certification date plus `GLEICHLAUT_CERT_DAYS` (default 90; `certify --valid-days`).
  The validity configured at check time also applies, whichever ends first.
- was made with the current frozen code (`freeze_sha256`) and suite.
- still matches its stored files. These are the 166 suite records (`state/runs/`), the call log, and the review
  labels, each against its sha256 in the certificate.
- still gives PASS, with the same metrics, when those records are re-scored with the frozen guards and the reference
  labels. A record whose stored guard verdict differs from the frozen checks is refused.
- has a call log that names this endpoint and the models served.

A hand-edited `"status": "PASS"` therefore opens nothing: to pass the gate, someone would have to produce suite records
that really pass the frozen checks. Without a key, someone who can write to `state/` could still re-date a certificate
or copy records that pass. Set `GLEICHLAUT_CERT_KEY` to close that gap. Every certificate and canary report is then
HMAC-SHA256-signed, and an unsigned or altered one is refused. Create the key once
(`head -c 32 /dev/urandom > /etc/gleichlaut/cert.key; chmod 400 /etc/gleichlaut/cert.key`) and keep it outside `state/`:
a root-owned file, or a Kubernetes Secret. `make` mounts it read-only. Certificates made before this release have no
integrity fields and are refused: certify again.

**When to re-certify:** a new endpoint URL, a new `LLM_NAME`, a model or serving-stack upgrade announced by the
provider, a canary failure, or a Gleichlaut upgrade that changes `eval/prereg/freeze.json`.

## 4. Canary (monthly, before drafting; it gates drafting)

```bash
make canary                      # CANARY_N=40 by default: about 70 requests, a few minutes
```

**The canary gates the SL lane.** `draft` and `month` (backend `openai`, corpus `sl`, not `--air-gapped`) refuse with
exit 3 when:

- the latest canary for the certificate in use **failed**. Only a later passing canary or a new certification lifts
  this, and no flag overrides it.
- the latest check is **older than 31 days** (`GLEICHLAUT_CANARY_MAX_AGE_DAYS`). The latest check is the newest
  canary, or the certification itself when no canary has run since.

`--allow-stale-canary` (`make month ALLOW_STALE_CANARY=1`) overrides the age check only. Each override is appended to
`state/gate-overrides.jsonl` and recorded under `gate` in the run's `summary.json`. `--dry-run` shows what the gate
would decide.

The canary re-runs the first N suite items and compares them with this endpoint's certified run. At temperature 0 the
70B lane is not byte-deterministic. A seeded re-run of the fresh 166 gave 69.9% identical outputs but flag agreement of
163/166 (κ 0.963), with exact 17.5% → 18.1% (`eval/results/m3.json`). So byte identity is reported as information only.
The canary **fails (exit 3)** if:

- flag agreement < **0.85** (the measured disagreement is 1.8%; 15% means the guards are seeing a different model), or
- exact match drops by more than **5 points** against the certified run on the same items (measured change +0.6; 5 is
  also the pass rule's minimum gain over rules-only), or
- a served model id was not seen at certification.

A `system_fingerprint` (the serving build the endpoint reports) that was not seen at certification is a **warning**. It
is printed, listed under `warnings`, and recorded as `fingerprint_changed: true`. It is not a failure, because providers
rotate builds. Consider re-certifying when it appears.

Each run writes its own report: `state/canary/canary-<endpoint>--<model>-<UTC time>.json`, with `-2`, `-3` added if
that name already exists. Nothing is overwritten. A report holds the agreement, exact now and then, flag rates, byte
identity, fingerprints now and then, the certificate it was compared against, and the sha256 of its call log. On a
failure, stop: re-certify, or draft with the local 8B (`--backend llamacpp`), the air-gapped default lane.

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

**Integration point for BAG's ePL team: items straight from ePL FHIR exports.** The ePL editor exports in the same FHIR
format as the public feed: NDJSON, one product Bundle per line, CH EPL profile. `gleichlaut items` turns two such exports
into the item file:

```bash
# last publication vs the month's draft export (only the German changed): pre-publication items, no tgt_new
gleichlaut items --from-fhir foph-sl-publication-20261001-de.ndjson draft-2026-11.json --out sl-team-2026-11.json
# two publications (FR/IT siblings -fr/-it next to the -de file are picked up): shadow items with tgt_new
gleichlaut items --from-fhir foph-sl-publication-20260901-de.ndjson foph-sl-publication-20261001-de.ndjson --lang fr,it --out items.json
```

Each side can be one German NDJSON file whose `-fr`/`-it` siblings sit next to it, a comma-separated list of
per-language files, or one file carrying French and Italian as FHIR translation extensions (`_text`, `lang` `fr-CH` /
`it-CH`). The new side may be a single draft Bundle in JSON, or a Bundle of product Bundles, in which only the German
changed. Changes are paired per product: the draft must keep the MedicinalProductDefinition id. Keys are
`<CUD id>-<6 hex>-<lang>`, so the same change always gets the same key. Changes without an old FR/IT text go to
`<out>.unmatched.json`. Nothing is sent anywhere (module `gleichlaut.sl.epl`).

### 5b. Shadow mode: the public feed (validation, monthly regression check)

After BAG publishes a month, run the same pipeline on what changed between two feed dates. FR/IT texts that BAG already
published become `tgt_new`. They are never shown to the model and are used only to score the drafts (`shadow_exact`).

```bash
make feeds                                    # which feed dates BAG has published (and which are already local)
make month                                    # FROM=previous TO=latest: the month since the last run, fetched if missing
make month FROM=20260901 TO=20261001          # a given pair of published dates
# or: PYTHONPATH=src python3 -m gleichlaut month --from 20260901 --to 20261001 --fetch [--snapshots DIR]
```

`--to latest` asks BAG's resources API for the newest feed. If the API is unreachable, it uses the date the last
`feeds`/`ingest latest` run recorded. `--from previous` is where the last completed month run ended
(`out/month/*/summary.json`), so consecutive runs leave no gap, including across mid-month republications such as
6 Oct 2026. With no earlier run, it is the feed published before `--to`. `gleichlaut feeds` lists the published dates
from the resources API and from polite HEAD probes of the known file pattern: the 1st of each of the last 12 months, the
research dates, and the dates already local. Add `--scan FROM TO` to probe every day of a range. Every request is spaced
≥ 1 s apart and carries the User-Agent `hackapertus-research/0.1`. The results are kept in `out/hist/feeds.json`, so a
published date is never probed twice. A feed that is not yet published is a clear error (exit 6), not an empty month.

Feeds are streamed into compact snapshots (`out/hist/<YYYYMMDD>-<lang>.json`, about 5.5 MB each). The raw NDJSON is
not kept unless you pass `--keep-raw DIR` to `gleichlaut.sl.ingest`. `ingest latest` stores the 'latest' feed under its
real publication date (feed timestamp, else HTTP Last-Modified as a Zurich date), with a `latest-<lang>.json` alias.
`out/hist/latest.json` records the date and how it was established. The 4 May 2026 feed is refused (publisher bug).

### What a month run does

1. **Items.** It reads the item file, or mines every German change between the two dates. For a feed run it also
   writes `unmatched.json`, which lists changes with no old FR/IT text under the same id. It validates the items
   against the schema and computes `change_ratio` where it is missing (the `sl.mine` rule).
2. **Routing.** If more than 60% of the German tokens changed, the item goes to `status: human` with a reason and is not
   drafted. So does a spacing-only change. The 2500-character limit (the evaluated range of the model lane) applies only
   to items that need the model. A change the code lane applies by itself (numbers or months only, e.g. a Dupixent
   "16 → 24 weeks") is drafted whatever its length, with `route_note` saying so, and no model is called for it.
3. **Gate.** On the SL lane through `openai`, the run continues only with a PASS endpoint certificate that verifies (§3;
   else exit 4) and a passing, recent canary (§4; else exit 3).
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
| 3 | canary outside tolerance; or `draft`/`month` refused because the latest canary failed or is older than 31 days | `make canary`; on a failure re-certify, or `--air-gapped`; a stale canary can be overridden with `--allow-stale-canary` (logged) |
| 4 | refused: no certificate for this endpoint and model that verifies (missing, FAIL, expired, other frozen code, files or HMAC do not match, records do not re-score to PASS) | `make certify`; the message names the reason |
| 5 | certificate FAIL | do not use the endpoint for the SL lane |
| 6 | endpoint or feed failed (unreachable, timeout or `GLEICHLAUT_DEADLINE` reached after retries, HTTP error, non-Apertus model served, served model not seen at certification, feed not published yet). For `live`: the live slice failed | records so far are kept; fix and re-run to resume |
| 7 | certificate PENDING_REVIEW | label `needs_review`, then `certify --resolve` |
| 130 | interrupted | re-run to resume |

Errors are one line on stderr, with no traceback (`GLEICHLAUT_DEBUG=1` shows it). `make run` exits 0 when the
reproduction passes, even if the live slice failed. Look for `LIVE SLICE FAILED`.

**Scheduling and alerting.** [docs/deploy/](deploy/) has a systemd service and timer set (canary, month, audit) and a
Kubernetes CronJob. The CronJob mounts a PVC for `state/` and `out/`, runs as a non-root user on a read-only root
filesystem, and runs the canary as an init container before the month. It also lists which exit code should page whom:
2 and 4 are configuration (operator), 3 is model drift (operator, stop drafting), 6 is an outage (retry next run, page if
it repeats), and 1 is a broken build (developer).

## 6b. Test environments: a fake endpoint

```bash
python -m gleichlaut.fake_endpoint --port 8099 --mode recorded      # or: make fake-endpoint FAKE_MODE=echo
export LLM_BASE_URL=http://127.0.0.1:8099/v1
```

An OpenAI-compatible fake for staging and acceptance tests. It calls no model and binds to 127.0.0.1. Modes:

- `recorded` answers with the recorded 70B responses. `certify` against it reproduces the recorded PASS, so the whole
  path (`certify`, then `canary`, then `month`/`draft`) can be exercised without a model.
- `echo` returns the old text unchanged, so the canary fails.
- `non-apertus` answers as a non-Apertus model, which every backend refuses (exit 6).
- `error` returns HTTP 500.
- `hang` never answers, to test timeouts and `GLEICHLAUT_DEADLINE`.

`--fingerprint` changes the reported `system_fingerprint`, which triggers the canary warning. The operations tests use
the same server in process.

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
- **To BAG (`epl.bag.admin.ch`), only with `--fetch`, `--to latest`, `gleichlaut feeds` / `gleichlaut.sl.ingest`, `make audit`:**
  plain GET/HEAD requests for the public feeds and the public resources API, at most one per second.
- **Nothing else.** There is no telemetry and no update check. The review page makes no requests. With no
  `LLM_BASE_URL`, `make run` runs with `--network none`. The air-gapped lanes (8B GGUF on CPU) contact nothing after
  the one-time model download.
- At build time only: the Docker base image (pinned by digest) and PyPI wheels (`docs/dependencies.md`).
- Every outgoing request goes through `HTTPS_PROXY`/`HTTP_PROXY` unless `NO_PROXY` matches, and is verified against the
  system CA store plus `SSL_CERT_FILE`.

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
make audit                                     # the no-model congruence audit of the whole register (monthly / quarterly)
make certify                                   # once per endpoint + model, and every 90 days; exit 0 / 5 / 7
make canary                                    # monthly, before drafting; exit 3 on drift; drafting refuses without it
make feeds                                     # published BAG feed dates
make month ITEMS=sl-team.json                  # pre-publication drafting
gleichlaut items --from-fhir OLD-de.ndjson DRAFT.json --out sl-team.json    # items from ePL exports
make month                                     # shadow mode: --from previous --to latest
make month FROM=20260901 TO=20261001           # shadow mode on a given pair of published feeds
PYTHONPATH=src python3 -m gleichlaut month --items sl-team.json --dry-run     # prompts, slot maps, routing; no request
PYTHONPATH=src python3 -m gleichlaut draft --items x.json --out out/x --backend stub   # wiring test, no model
```
