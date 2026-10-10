# Research record (verbatim lines): which model the API serves; GGUF vs bf16

Lines copied from `spikes/live/results.md` (sha256 `c2e422b5690dbb45b2b017fb89ef47e6935f91280d3031b668f19c4ade63e05a`) and `spikes/gguf/results.md` (sha256 `10587afacab912c8114b6bb20bbe4b8376a0837924b08746cf75ebf7b5dc6a43`); plus the MMLU verdict from `loop/learnings.md`.

> Note (10 Oct 2026): these are verbatim research-log lines. "The shared model is the 70B" is an inference from MMLU
> against the v1 8B (which mixes version and size), not an established fact; see report §3.1.

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
