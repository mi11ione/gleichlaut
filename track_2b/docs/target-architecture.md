# Target architecture

Gleichlaut targets **(a) on-premise** and **(b) air-gapped** for every lane by default: the 8B on a CPU passes the
pre-registered rule for SL conditions (R1). Offices that want fewer edits add the 70B on their own GPUs (on-premise) or
on **(c) a sovereign Swiss cloud** endpoint. Sources for every provider fact:
`docs/sources.md` §5.

## Deployment rows

| Lane | Model and where it runs | Hardware | External services at runtime | Data that leaves the user's environment |
|---|---|---|---|---|
| Fedlex statutes (every draft reviewed) | Apertus v1.5 8B, GGUF Q4_K_M, llama.cpp on CPU, in process | any x86-64/ARM server, ≥ 8 GB RAM, ~5.1 GB disk | none | none |
| SL limitations, default | the same 8B (passes the pre-registered rule on the held-out 166: 0 meaning errors among ready drafts; 153.4 s per draft on 4 cores) | same | none | none |
| SL limitations, fewer edits | Apertus v1.5 70B on an endpoint the user controls, **after `make certify` passes on it** (ready drafts needing a fix: 3 of 66 vs 33 of 60 for the 8B) | own GPUs (bf16 144.6 GB, FP8 76.2 GB; vLLM, tensor-parallel 4 in the official example) or a Swiss-resident provider | that endpoint only | per request: one limitation text in German (old and new) and in French or Italian, numbers replaced by slot codes; before publication this is BAG's confidential draft, so the endpoint must be one BAG controls |

Everything else (mining, lock, guards, re-ask control, certification, XLIFF/FHIR output, the review page) is
Python standard library plus `lxml`, runs on the same box, and has no network dependency.

## Swiss-resident 70B endpoints (sovereign cloud option)

The Apertus project lists these providers as serving the 70B from a data centre in Switzerland (Sept 2026):
Swisscom, Infomaniak, PHOENIQS (kvant.cloud), Safe Swiss Cloud, OnPrem.ai. Published per-token prices: Infomaniak
CHF 0.70 / 2.50 per million input / output tokens; Safe Swiss Cloud CHF 0.712 / 2.553. Gleichlaut talks to any of them
through the OpenAI-compatible `LLM_BASE_URL`; no provider-specific code exists, so there is no lock-in.

**Certification is the gate, not the brand.** A different provider, quantisation or serving stack can change outputs.
`make certify` re-runs the frozen 166-item suite on the endpoint and writes a certificate (endpoint, models that actually
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
requests for the 166-item suite), a month is roughly 100 requests: about 0.3 model-hours run one after another. A
certification is 285 requests, and a canary about 70. One GPU node shared with other workloads is enough, and the
choice is about memory, not speed. Whatever is chosen (quantisation, serving stack, GPU count) must pass `make certify`
on that exact endpoint, because each of these can change outputs.

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

## Not yet demonstrated

- The 70B has not been self-hosted by us; the public 70B GGUF is an unofficial text-only test quant (43.72 GB).
- The 8B GGUF Q8_0 build (M2) is running on the same CPU workflow; the Q4_K_M build is the measured default.
- `make run-offline` (llama.cpp in Docker) is wired as the manual workflow `.github/workflows/offline.yml` (ubuntu-24.04,
  CPU). It builds the `offline` image, fetches the pinned GGUF (cached), and must end with `reproduction PASSED; live
  slice PASSED`. It has not been run from this checkout yet.
