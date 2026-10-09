# Dependencies: build time vs runtime

## Runtime (what the running solution needs and contacts)

| Component | Version | Licence | Needed by | Contacts the network? |
|---|---|---|---|---|
| Python | 3.12 (any ≥ 3.9 works) | PSF | everything | no |
| Python standard library | n/a | PSF | ingest, mining, lock, guards, re-ask, scoring, replay, certification, emit, UI | only `sl.ingest` / `fed.ingest` when *you* run them, to fetch the public feeds |
| `lxml` | 6.0.2 (hash-pinned) | BSD-3 | XLIFF validation against the OASIS XSD | no |
| `llama-cpp-python` | 0.3.35 (offline image; hash-pinned with numpy 2.2.6, typing-extensions 4.16.0, diskcache 5.6.3, jinja2 3.1.6, markupsafe 3.0.3) | MIT | local CPU inference of the 8B GGUF; the version the build certificate is bound to | no |
| Apertus v1.5 8B GGUF Q4_K_M | sha256 `a037df8d…f299`, 5,059,027,136 bytes; **certified build** (`eval/certificates/8b-q4_k_m-fresh166.json`) | Apache-2.0 (Apertus weights) | **the default drafting lane** for SL conditions (passes the pre-registered rule, R1) and for statutes (every draft reviewed), air-gapped | no (file on disk) |
| Apertus v1.5 70B | served by an endpoint the user controls, certified (`make certify-endpoint`) | Apache-2.0 | **optional** SL "fewer edits" lane (42.4% vs 20.9% fewer edits than rules-only) | **yes: that endpoint only**. Per request it receives the German old/new text and the French or Italian text of one limitation, with numbers replaced by slot codes |
| Guard resources (`frozen/g3/*.json`) | frozen, sha256 in `eval/prereg/freeze.json` | derived from official SL publications | guards G5–G7 | no |
| XSD files (`data/schemas/`) | vendored | see `data/schemas/README` | XLIFF validation | no |

External services contacted at runtime: **none** in the default lane (the local 8B, SL and Fedlex); **one** (the user's
own 70B endpoint) in the optional SL "fewer edits" lane. The public BAG feed (`epl.bag.admin.ch`) is read only in shadow
mode and by the audit. No personal data is processed: every input is an official federal publication.

Hardware for the default lane: **4 CPU cores and 8 GiB RAM** (one requirement for the whole box; the audit and the 70B
lane need less), about 8 GB disk. Measured: 153.4 s per item on 4 cores, about 2.4 h a month at today's volume
(`docs/operations.md` §1).

## Build time / development only (never contacted by the running solution)

| Item | Used for |
|---|---|
| Docker base image `python:3.12-slim` (pinned by digest), PyPI (every file hash-pinned) | building the images |
| Hugging Face (`Colby/apertus-v1.5-8b-text-Q4_K_M-GGUF`) | one-time download of the GGUF, sha256-checked (`make run-offline`, `gleichlaut fetch-gguf`) |
| Public AI API (`api.publicai.co`) through a budget gateway | **evaluation only**: the recorded 70B runs. Public AI may route requests outside Switzerland, so it is not a runtime target |
| Wayback Machine captures of the 2025 SL XMLPublications | building the fresh test set (done; items are in `data/items/`) |
| GitHub Actions | CI and the CPU runs of the 8B GGUF (M1/M2) |
| Claude Code (Anthropic) | coding assistant and hand-check labelling during development; not part of the solution |

## GGUF provenance (the offline 8B lane)

The file `make run-offline` and `gleichlaut fetch-gguf` download is pinned by sha256. **That sha256 is the file the
evaluation used**: the 8B GGUF evaluation on the fresh 166 (`.github/workflows/m1.yml`, PREREG R1, CPU runners, same URL
and sha256) and the offline workflow (`.github/workflows/offline.yml`). Any other file, including a re-quantisation of the same
weights, is a different model build and has to be evaluated again (m1 workflow) before its results can be quoted.

| Step | Repository (Hugging Face) | What it is |
|---|---|---|
| 1 | `swiss-ai/Apertus-v1.5-8B` | the official weights (safetensors, 18.4 GB; multimodal: text, image, audio) |
| 2 | `andreasmartin/apertus-v1.5-8b-text` (revision `c0e7eeb6`, card `base_model: swiss-ai/Apertus-v1.5-8B`) | a third-party **text-only** extraction: the vision and audio towers removed, so llama.cpp can convert it |
| 3 | `Colby/apertus-v1.5-8b-text-Q4_K_M-GGUF` (revision `248ec68a`, 5 Sep 2026) | `apertus-v1.5-8b-text-q4_k_m.gguf`, made from step 2 with llama.cpp through ggml.ai's GGUF-my-repo space (its card says so; tag `gguf-my-repo`) |
| pin | `GLEICHLAUT_MODEL_SHA256` | `a037df8d87ff6caacee794ee85f55342f2152e0d359b7389033300c3bee5f299`, 5,059,027,136 bytes |

Neither step 2 nor step 3 is published by swiss-ai, and no official GGUF exists (`docs/sources.md` §5.3). The chain was
read from the repositories' model cards and the Hugging Face API on 9 Oct 2026. Step 2 is gated: accept the Apertus
Acceptable Use Policy there.

**Quantising it yourself** with llama.cpp, from the text-only weights:

```bash
git clone https://github.com/ggml-org/llama.cpp && cd llama.cpp
pip install -r requirements/requirements-convert_hf_to_gguf.txt
cmake -B build -DGGML_NATIVE=OFF -DLLAMA_CURL=OFF && cmake --build build --config Release -j --target llama-quantize
hf download andreasmartin/apertus-v1.5-8b-text --revision c0e7eeb69c55c7810c91de3a1f97dde4d4b14b01 --local-dir apertus-v1.5-8b-text
python convert_hf_to_gguf.py apertus-v1.5-8b-text --outtype bf16 --outfile apertus-v1.5-8b-text-bf16.gguf
./build/bin/llama-quantize apertus-v1.5-8b-text-bf16.gguf apertus-v1.5-8b-text-q4_k_m.gguf Q4_K_M
sha256sum apertus-v1.5-8b-text-q4_k_m.gguf
```

To start from the official `swiss-ai/Apertus-v1.5-8B` instead, first extract the text model, as step 2 did, because the
multimodal checkpoint carries the vision and audio towers. Gleichlaut does not ship an extraction script. To use your
own file, put it in `models/` under the base name of `GLEICHLAUT_MODEL_URL` and set `GLEICHLAUT_MODEL_SHA256` to its
sha256. `fetch_gguf` finds a verified file and downloads nothing. Expect a different sha256 from the pin unless the
llama.cpp version matches the one GGUF-my-repo used. Before relying on the file, run the m1 workflow on it and
import the run as a build certificate (`gleichlaut certify --import-run RECORDS --gguf-sha256 SHA --labels TSV`), or run
`gleichlaut certify --backend llamacpp --gguf FILE`: without a build certificate every SL draft of that file goes to review.

## Supply chain

- **Hash-pinned Python dependencies.** `requirements.in` / `requirements-offline.in` hold the human-edited pins;
  `python3 tools/supply_chain.py lock` (`make lock`) writes `requirements.txt` / `requirements-offline.txt` with every
  sha256 PyPI lists for each pinned version (PyPI JSON API). The Dockerfile, CI and the deploy instructions install with
  `pip install --require-hashes`, so a file with any other hash (a re-uploaded or tampered wheel) is refused, and every
  transitive dependency must be pinned. Known gap: the build backend of the llama-cpp-python sdist (scikit-build-core,
  installed by pip's build isolation) is not hash-checked; pre-building the wheel once and pinning its hash closes it.
- **Base image by digest.** `python:3.12-slim@sha256:a6e34c59…` in the Dockerfile (the multi-arch index; the
  linux/amd64 manifest is named in the comment), pulled through Google's Docker Hub mirror.
- **GGUF by sha256** (`GLEICHLAUT_MODEL_SHA256`), checked after every download and before the gate accepts a build
  certificate (the loaded file is hashed).
- **SBOM.** `docs/sbom.json` (CycloneDX 1.5 JSON) is generated by `python3 tools/supply_chain.py sbom` (`make sbom`) from
  the hash-pinned requirements, the base image digest and the GGUF sha256: one component per package with its purl,
  licence and allowed hashes, the base image as a container component, the GGUF as a machine-learning-model component,
  and the optional 70B endpoint as a service. CI fails when it is stale (`sbom --check`).
- **Next step: signed images.** The images are built locally by `make` and are not signed yet. A registry deployment
  should sign each pushed digest with cosign (keyless from CI with the GitHub OIDC identity, or a key in the
  organisation's KMS), attach the SBOM as an attestation (`cosign attest --type cyclonedx --predicate docs/sbom.json`),
  and admit only verified images (Sigstore policy-controller or Kyverno `verifyImages`).
