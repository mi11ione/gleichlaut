# Research record (verbatim lines): which model the API serves; GGUF vs bf16

Lines copied from `spikes/live/results.md` (sha256 `c2e422b5690dbb45b2b017fb89ef47e6935f91280d3031b668f19c4ade63e05a`) and `spikes/gguf/results.md` (sha256 `10587afacab912c8114b6bb20bbe4b8376a0837924b08746cf75ebf7b5dc6a43`); plus the MMLU verdict from `loop/learnings.md`.

> Note (10 Oct 2026): these are verbatim research-log lines. "The shared model is the 70B" is an inference from MMLU
> against the v1 8B (which mixes version and size), not an established fact; see report §3.1.
>
> Note (11 Oct 2026), reading these lines correctly (sources quoted below):
> - **Which builds.** "bf16 DPO" is the bf16 weights of `swiss-ai/Apertus-v1.5-8B-DPO`, an intermediate post-training
>   checkpoint (the stage before the final SDPO stage released as `swiss-ai/Apertus-v1.5-8B`), downloaded with
>   `hf download` without a revision: the revision is not recorded. "MLX 4-bit final" / "MLX 4-bit g64" is our own
>   `mlx_lm.convert -q --q-bits 4 --q-group-size 64` of the final checkpoint: 548 of 648 is this build. The research arms
>   (dev 120, statutes / R5, the failure-mode tests) ran the third-party `m1rkocasu/Apertus-v1.5-8B-text-MLX-4bit-DWQ`;
>   on the same 648 probes it disagrees with bf16 DPO on 38, i.e. agrees on **610 of 648** (mean |Δ| 7.5 nats; the DWQ
>   trace is assembled from four runs with byte-identical questions).
> - **"All 1584 calls were served by the 8B vLLM backend"** is about the `swiss-ai/apertus-v1.5-8b` name on the battery
>   (792 forced-choice and 792 generation calls, all on `vllm-0.23.1rc1…-tp8-pp2`). It says nothing about the 70B name or
>   about any drafting run. The 70B name was answered by `fp1-nes` on the battery (792 of 792) and by `fp1-nes` or `tp2`
>   elsewhere. The MMLU 84.4% was measured on the `apertus-v1.5-8b` name; its calls kept the served model name, not the
>   backend.

## live/results.md

   - The 70B name is answered by a backend called `fp1-nes`. Its greedy outputs are **byte-identical to the 8B endpoint's in 760 of 792 battery cells**. Decisions agree in 787/792.
     - against the 8B endpoint, r = 0.975, mean |Δ| = 2.3 nats, decisions 760/792;
- The battery question strings are asserted byte-identical to the `stage9.py` meta stored in `stage_bf16_DPO.json`. R4 is byte-identical to `spike8.py` / `spike9.py`.
| `swiss-ai/apertus-8b-instruct` | `fp1-nst-nes` | none | **Apertus v1 8B**: self-reports "Apertus, SwissAI, Stichtag 31. März 2024", different default system prompt, verbose. Agrees with the v1.5 references only 430–459/520 on parsed decisions; 192/792 were unparseable at 24 tokens. Different model; not analysed further. |
| Battery free-generation text identical | **760/792** | n/a |
| Battery decisions | 787/792 | 760/792 (forced choice), r = 0.975, mean \|Δ\| 2.30 nats |
All 1584 calls were served by the 8B vLLM backend. Measured prefill-vs-decode drift (stack noise σ): the forced-choice log-odds against the decode-path top-20 log-odds give an sd of **0.26 nats** (max 1.5) over 365 conv cells. Free-generation decisions match forced choice in 789/792.
`apertus-v1.5-70b` on fp1-nes (free generation, 792/792 parsed) gives the 8B's decisions in 787/792. The tp2 backend (exact forced choice via the `apertus-70b-instruct` alias) is listed alongside.
  - It routes between fp1-nes and tp2. In the seeded tests the split was 14/6, 13/7 and 5/15; in the battery run it was 792/0.

## gguf/results.md

**Answer:** no. Martin's Q8_0 matches bf16 on 638 of 648 decisions, which is as close as the DPO and final checkpoints are to each other. The Q4_K_M matches on 622 of 648. The build that drifts is our own MLX 4-bit g64 (548/648).
| `gguf_q4` | **Colby/apertus-v1.5-8b-text-Q4_K_M-GGUF**, `apertus-v1.5-8b-text-q4_k_m.gguf` | 5,059,027,136 B | `a037df8d87ff6caacee794ee85f55342f2152e0d359b7389033300c3bee5f299` (verified) |
| **Martin's Q8_0** vs bf16 DPO | **638/648** | **0.98** | 0.47 | 48 | 162/162 | 160/162 | 162/162 | 154/162 |
| **Colby Q4_K_M** vs bf16 DPO | **622/648** | **3.79** | 2.69 | 394 | 162/162 | 151/162 | 162/162 | 147/162 |
| *MLX 4-bit final vs bf16 DPO* | *548/648* | *9.92* | 8.75 | 603 | 119 | 132 | 162 | 135 |
| Q4_K_M vs Q8_0 | 622/648 | 4.15 | 2.57 | 396 | 162 | 153 | 162 | 145 |

## loop/learnings.md

- **VERDICT (9 Oct, 19:45): the shared model is the 70B.** Same 250 MMLU questions: shared model 84.4% (211/250) vs `apertus-8b-instruct` (v1 8B) 70.8% (177/250); 16-GPU deployment; 4× slower decoding. Public AI's `apertus-v1.5-8b` name serves the 70B.

## stage/results.md (sha256 `c08ef6aa625e607d9845cf901ff2568e2163619e8e51e6dcbfb8a07658e0b7ca`)

| base (stage 0) | swiss-ai/Apertus-v1.5-8B-base (ungated; shards hardlinked from the other agent's download, HF LFS sha256 verified) | text branch → `mlx_lm.convert -q --q-bits 4 --q-group-size 64` |
| SFT, RLVR, DPO | swiss-ai/Apertus-v1.5-8B-{SFT,RLVR,DPO} (gated, Roman's HF token) | same |
| final (SDPO) | swiss-ai/Apertus-v1.5-8B via the cpral/Apertus-V1.5-8B-ungated mirror; all 4 shards, tokenizer, template and config match the official swiss-ai sha256 published on ModelScope | same |
| final_dwq | m1rkocasu/Apertus-v1.5-8B-text-MLX-4bit-DWQ (the round-7 model) | forced choice only; reproduces round 7 exactly (max abs. lp diff 0.0) |

## linie9/bf16.md (sha256 `6ef3f17ef681210621a469ca30863b59cfc637ad2776c69ea089de389d1aaaa2`)

- **Stages:** `swiss-ai/Apertus-v1.5-8B-RLVR` and `-DPO`.
  - Only the omni text shards (`model-apertus-model-*`) were downloaded, about 16 GB each, with the HF token piped from the Air.

(The download script `linie9/bf16_scripts/chain.sh` runs `hf download swiss-ai/Apertus-v1.5-8B-$st --include 'model-apertus-model-*.safetensors'` with no `--revision`.)

## inversions/results.md (sha256 `f68302ca42923ca25f0405db01ee295d6b5756b6375eb9a96a338238feb8303f`)

| final 4-bit DWQ | Assembled from four runs with byte-identical question strings (checked): conv_R0 ladder `round7/linie.json`; conv_R3 ladder `round8/ladder.json` R3; conv R0/R3 never `round8/never.json`; ver_R0 ladder `round8/polarity.json`; ver_R3 ladder and ver R0/R3 never `linie9/apertus.json` |
- **No final bf16.** The 3-way task below uses **DPO bf16 as a stand-in for final bf16**. This is justified because DPO → final at g64 changes only 13/648 decisions, with a mean |Δ| of 0.9 nats, against 100–125 decisions for any quantisation step. It is still a proxy.
Each cell shows decision disagreements out of 648 probes / mean |Δ log-odds| in nats.
| | RLVR bf16 | RLVR g64 | DPO bf16 | DPO g64 | final g64 | final DWQ |
| DPO bf16 | | | – | **103 / 9.9** | 100 / 9.9 | 38 / 7.5 |
- DWQ sits much closer to (DPO-)bf16 than g64 does: 38 vs 100 flips.
