# Target architecture

Gleichlaut targets **(a) on-premise** for every lane and **(b) air-gapped** for the lanes that run the 8B. The SL
default lane can alternatively use **(c) a sovereign Swiss cloud** endpoint for the 70B. Sources for every provider fact:
`docs/sources.md` §5.

## Deployment rows

| Lane | Model and where it runs | Hardware | External services at runtime | Data that leaves the user's environment |
|---|---|---|---|---|
| Fedlex statutes | Apertus v1.5 8B, GGUF Q4_K_M, llama.cpp on CPU, in process | any x86-64/ARM server, ≥ 8 GB RAM, ~5.1 GB disk | none | none |
| SL limitations, air-gapped | the same 8B; **every draft goes to review** (the 8B does not pass the SL pass rule) | same | none | none |
| SL limitations, default | Apertus v1.5 70B on an endpoint the user controls, **after `make certify` passes on it** | own GPUs (bf16 144.6 GB, FP8 76.2 GB; vLLM, tensor-parallel 4 in the official example) or a Swiss-resident provider | that endpoint only | per request: one public limitation text in German (old and new) and in French or Italian, numbers replaced by slot codes |

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
without a PASS certificate. A 5-item canary (`certify --canary 5`) detects drift against the certified run.

## What we used during development, and why it is not a target

Public AI (`api.publicai.co`) served the 70B for our evaluation. Its own documentation says requests are routed
"regardless of which country's compute is serving the query", and we measured that its 70B name silently answers from a
different model when a request carries a system message. It is therefore **evaluation-only**. Every runtime backend
checks the `model` field of each response and refuses a non-Apertus answer.

## Licences and terms

Apertus weights are Apache-2.0 with the Apertus Acceptable Use Policy v1.5 (users accept it on the Hugging Face gate;
it requires indemnifying ETH Zurich and EPFL, and back-to-back terms on redistribution). Gleichlaut does not redistribute
weights: `make run-offline` downloads a public GGUF and verifies its sha256. Code Apache-2.0, report CC-BY-4.0. The SL and
Fedlex texts are official federal publications (Fedlex: not protected, URG Art. 5; an explicit reuse licence for the SL
feed was not found, see `docs/sources.md` §2.3).

## Not yet demonstrated

- The 70B has not been self-hosted by us; the public 70B GGUF is an unofficial text-only test quant (43.72 GB).
- The 8B GGUF build that ships has not yet been run on the SL fresh set (workflow `m1.yml`, CPU runners).
- `make run-offline` (llama.cpp in Docker) has not been run yet; it needs a Linux runner (no Docker on the team machine).
