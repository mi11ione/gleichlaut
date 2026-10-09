# Dependencies: build time vs runtime

## Runtime (what the running solution needs and contacts)

| Component | Version | Licence | Needed by | Contacts the network? |
|---|---|---|---|---|
| Python | 3.12 (any ≥ 3.9 works) | PSF | everything | no |
| Python standard library | n/a | PSF | ingest, mining, lock, guards, re-ask, scoring, replay, certification, emit, UI | only `sl.ingest` / `fed.ingest` when *you* run them, to fetch the public feeds |
| `lxml` | 6.0.2 | BSD-3 | XLIFF validation against the OASIS XSD | no |
| `llama-cpp-python` | 0.3.35 (offline image only) | MIT | local CPU inference of the 8B GGUF | no |
| Apertus v1.5 8B GGUF Q4_K_M | sha256 `a037df8d…f299`, 5,059,027,136 bytes | Apache-2.0 (Apertus weights) | Fedlex lane; SL air-gapped fallback | no (file on disk) |
| Apertus v1.5 70B | served by an endpoint the user controls | Apache-2.0 | SL default lane | **yes: that endpoint only**. Per request it receives the public German old/new text and the public French or Italian text of one limitation, with numbers replaced by slot codes |
| Guard resources (`frozen/g3/*.json`) | frozen, sha256 in `eval/prereg/freeze.json` | derived from official SL publications | guards G5–G7 | no |
| XSD files (`data/schemas/`) | vendored | see `data/schemas/README` | XLIFF validation | no |

External services contacted at runtime: **none** in the Fedlex lane and in the air-gapped SL fallback; **one** (the
user's own 70B endpoint) in the SL default lane. No personal data is processed: every input is an official federal
publication.

## Build time / development only (never contacted by the running solution)

| Item | Used for |
|---|---|
| Docker base image `python:3.12-slim`, PyPI | building the images |
| Hugging Face (`Colby/apertus-v1.5-8b-text-Q4_K_M-GGUF`) | one-time download of the GGUF, sha256-checked (`make run-offline`, `gleichlaut fetch-gguf`) |
| Public AI API (`api.publicai.co`) through a budget gateway | **evaluation only**: the recorded 70B runs. Public AI may route requests outside Switzerland, so it is not a runtime target |
| Wayback Machine captures of the 2025 SL XMLPublications | building the fresh test set (done; items are in `data/items/`) |
| GitHub Actions | CI and the CPU runs of the 8B GGUF (M1/M2) |
| Claude Code (Anthropic) | coding assistant and hand-check labelling during development; not part of the solution |
