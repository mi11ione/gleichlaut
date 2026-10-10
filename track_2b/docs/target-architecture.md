# Target architecture

Gleichlaut targets **(a) on-premise** and **(b) air-gapped** for every lane by default: the 8B on a CPU passes the
pre-registered rule for SL conditions (R1). Offices that want fewer edits add the 70B on their own GPUs (on-premise) or
on **(c) a sovereign Swiss cloud** endpoint. Sources for every provider fact:
`docs/sources.md` §5.

## Deployment rows

| Lane | Model and where it runs | Hardware | External services at runtime | Data that leaves the user's environment |
|---|---|---|---|---|
| SL limitations, **default** | Apertus v1.5 8B, GGUF Q8_0, llama.cpp on CPU, in process: a **certified build** (passes the pre-registered rule on the held-out 166: 0 meaning errors, 0 stale changes, 0 German left among its 62 ready drafts; build certificate bound to the GGUF sha256, llama-cpp-python 0.3.35 and the frozen code). Q4_K_M is the certified option for an 8 GiB box (`BUILD=q4_k_m`) | any x86-64/ARM server: **4 CPU cores, 16 GiB RAM**, ~12 GB disk; 200.5 s per item on 4 cores, about 3.2 h a month (32.0 h at 10×). Q4_K_M: 8 GiB RAM, ~8 GB disk, 153.4 s per item, about 2.4 h a month | none | none |
| Fedlex statutes (every draft reviewed) | the same 8B | same | none | none |
| SL limitations, optional "fewer edits" | Apertus v1.5 70B on an endpoint the user controls, **after `make certify-endpoint` passes on it** and with a monthly canary (ready drafts needing a fix: 3 of 66 vs 25 of 62 for the 8B Q8_0; 42.4% vs 33.1% fewer edits) | own GPUs (bf16 144.6 GB, FP8 76.2 GB; vLLM, tensor-parallel 4 in the official example) or a Swiss-resident provider | that endpoint only | per request: one limitation text in German (old and new) and in French or Italian, numbers replaced by slot codes; before publication this is BAG's confidential draft, so the endpoint must be one BAG controls |

Everything else (mining, lock, guards, re-ask control, certification, XLIFF/FHIR output, the review page) is
Python standard library plus `lxml`, runs on the same box, and has no network dependency.

## Swiss-resident 70B endpoints (sovereign cloud option)

The Apertus project lists these providers as serving the 70B from a data centre in Switzerland (Sept 2026):
Swisscom, Infomaniak, PHOENIQS (kvant.cloud), Safe Swiss Cloud, OnPrem.ai. Published per-token prices: Infomaniak
CHF 0.70 / 2.50 per million input / output tokens; Safe Swiss Cloud CHF 0.712 / 2.553. Gleichlaut talks to any of them
through the OpenAI-compatible `LLM_BASE_URL`; no provider-specific code exists, so there is no lock-in.

**Certification is the gate, not the brand.** For the default lane, a build certificate binds the measured result to
one GGUF file, one llama-cpp-python version and the frozen code (`make certify` imports the recorded M2 run of Q8_0, or
with `BUILD=q4_k_m` the M1 run, in seconds; `make certify-build` re-runs the suite on your own CPU, about 9 h for Q8_0); the gate hashes the loaded GGUF before every SL run,
and without a valid certificate every draft goes to review. For the 70B, a different provider, quantisation or serving
stack can change outputs. `make certify-endpoint` re-runs the frozen 166-item suite on the endpoint and writes a certificate (endpoint, models that actually
served the calls, hashes of code and items, pass-rule metrics, status). `gleichlaut draft --corpus sl` refuses an endpoint
without a PASS certificate that still verifies (stored records re-scored, hashes, expiry after 90 days, optional HMAC).
A 40-item canary (`make canary`, `certify --canary`, default 40) detects drift against the certified run, and drafting
also refuses when the latest canary failed or is more than 31 days old (`docs/operations.md` §3–4).

## Sizing an on-premise 70B

The full Apertus v1.5 70B checkpoint is 144.6 GB in bf16, including the vision and audio towers. Two configurations hold
it with room for the KV cache:

- **2 × H100 80 GB** serving an FP8 checkpoint (76.2 GB of weights; `onprem-ai/Apertus-v1.5-70B-FP8` is a third-party
  quantisation), tensor-parallel 2.
- **4 × A100 80 GB** serving bf16, tensor-parallel 4, like the official vLLM example.

Either needs the swiss-ai vLLM build until upstream support lands (`docs/sources.md` §5). Throughput is not the
constraint. At about 57 FR/IT items a month (`eval/results/economics.json`), with about 1.7 requests per item (285
requests for the 166-item suite), a month is roughly 100 requests: about 0.3 model-hours run one after another (2.7 at
10×). A certification is 285 requests, and a canary about 70. One GPU node shared with other workloads is enough, and the
choice is about memory, not speed. Whatever is chosen (quantisation, serving stack, GPU count) must pass `make
certify-endpoint` on that exact endpoint, because each of these can change outputs.

**What a self-hosted 70B costs for this job.** The job uses the node for about 0.3 hours a month (2.7 at 10×), plus
roughly one more hour for each certification and a few minutes per monthly canary. A dedicated 2 × H100 or 4 × A100 node
therefore sits idle for more than 99% of the month on Gleichlaut alone: buying one for this job does not pay; it pays
only as a slice of a node the organisation already runs for other models, where Gleichlaut's share is about 0.3 GPU-node
hours a month. Renting the same capacity per token from a Swiss-resident provider costs CHF 0.14 a month at today's
volume and CHF 1.36 at 10× (Infomaniak's published price, `eval/results/economics.json`). The default 8B lane needs
neither: it runs in about 3.2 hours a month on 4 CPU cores of an existing server (Q8_0; 2.4 hours for Q4_K_M). We did not price GPU hardware or
hosting (no sourced figure), so this paragraph compares usage, not purchase prices.

## What we used during development, and why it is not a target

Public AI (`api.publicai.co`) served the 70B for our evaluation. Its own documentation says requests are routed
"regardless of which country's compute is serving the query". It is therefore **evaluation-only**. Every runtime backend
checks the `model` field of each response and refuses a non-Apertus answer.

## Licences and terms

Apertus weights are Apache-2.0 with the Apertus Acceptable Use Policy v1.5 (users accept it on the Hugging Face gate;
it requires indemnifying ETH Zurich and EPFL, and back-to-back terms on redistribution). Gleichlaut does not redistribute
weights: `make run-offline` downloads a public GGUF and verifies its sha256. Code Apache-2.0, report CC-BY-4.0. The SL and
Fedlex texts are official federal publications (Fedlex: not protected, URG Art. 5; an explicit reuse licence for the SL
feed was not found, see `docs/sources.md` §2.3).

## Demonstrated on CPU runners, no model endpoint

- **Shadow mode on a live month** (`.github/workflows/shadow.yml`, monthly on the 2nd and on demand): the month
  1 Sep → 1 Oct 2026 of BAG's public feed, drafted by both certified 8B builds under `--network none`, graded against
  BAG's publication (`data/shadow/`, PREREG R7).
- **`make run-offline`** (llama.cpp in Docker, `.github/workflows/offline.yml`, ubuntu-24.04 CPU): builds the `offline`
  image, fetches the pinned GGUF (sha256-checked, cached) and ends with `reproduction PASSED; live slice PASSED`.
- **The 70B lane is endpoint-agnostic:** any OpenAI-compatible endpoint serving Apertus 70B that the office controls is
  admitted by certificate (`make certify-endpoint`); the public 70B GGUF is an unofficial text-only quant (43.72 GB), so
  the lane is specified by certificate rather than by a file we pin.
