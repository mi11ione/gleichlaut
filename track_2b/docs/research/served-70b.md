# The served "70B": identity record

Moved verbatim from the technical report §3.1 to keep the report within six pages. Sources: `eval/results/identity_r19.json`,
`eval/results/fresh166_by_backend.json`, [model-identity-and-quantisation.md](model-identity-and-quantisation.md),
[chat-template.md](chat-template.md), PREREG R16 and R19.

We do not control which weights Public AI serves, and the 70B rows are a mix of backends whose identity is uncertain.
The `apertus-v1.5-70b` name is answered by two backends, `tp2` and `fp1-nes`. The headline fresh-166 run did not log the
backend (285 calls); its seeded rerun on the same items (R2, which also passes R0) did: 202 calls `tp2`, 81 `fp1-nes`.
On a 792-cell research battery `fp1-nes` answered the 70B name and gave byte-identical greedy text to the
`apertus-v1.5-8b` name in 760 of 792 cells; the research log's "all 1584 calls were served by the 8B vLLM backend" refers
to that 8B name (a third backend, `tp8-pp2`), not to the 70B name or to any drafting run. The research inferred one
shared model behind both names and called it the 70B from MMLU on the 8B name (84.4% on 250 questions, against 70.8% for
the v1 8B route; that comparison mixes model version and size): evidence, not proof. After an Apertus-team juror asked,
we scored the certified local v1.5 8B Q8_0 on the same probes (PREREG R19, CPU runners, prompts and decoding as
recorded): **78.4% on the 250 MMLU questions** (196; 6.0 points below the shared model [1.6, 10.4], 7.6 above the v1 8B
[2.0, 13.6]), so part of the gap the 70B inference rested on is model version, not size. On the battery its greedy text
equals `fp1-nes`'s in 322 of 792 cells (40.7%; it never closes "Ja" or "Nein" with the period the served model writes in
382), and its decisions agree with `fp1-nes` (88.6%) no more than with `tp2` (90.4%, forced choice). Under the rule
stated before the run this is **inconclusive**: 78.4% sits just above the 78% line below which the MMLU gap would have
counted, and neither backend matches the local 8B. Post hoc, on the 648 cells of the parity battery the local Q8_0
agrees with `tp2` on 605 decisions and with the 8B name on 603, where it agreed with the bf16 8B DPO checkpoint on 638:
the served model departs from a v1.5 8B by more than quantisation does, but its size remains unproven
(`eval/results/identity_r19.json`). Re-scored by backend (post hoc,
descriptive, below; `eval/results/fresh166_by_backend.json`), the rerun's `fp1-nes`-only items come out with more
ready drafts and more edits saved than its `tp2`-only items; the router, not we, assigned the items, so the classes
differ in items (and in how often the re-ask ran) as well as in backend. So every 8B number here comes
from local runs, and the 70B rows describe "the 70B as Public AI served it"; the 8B rows carry a digit and number-word
logit mask that Public AI's API does not offer for the 70B (an OpenAI-compatible server such as vLLM could, via `logit_bias`) (the 70B's 3 number-word drafts were all flagged). The 8B GGUF builds come from a third-party text-only extraction of `swiss-ai/Apertus-v1.5-8B` (`docs/dependencies.md`); llama.cpp applies the chat template embedded in the GGUF, which is byte-identical to the official `swiss-ai/Apertus-v1.5-8B` template (sha256 `d23af285…`, both builds; `docs/research/chat-template.md`). Before our user message it adds the template's default system turn ("You are Apertus […] Omni, a multimodal assistant developed by the Swiss AI Initiative […]", full text in that note) and the developer turn "Deliberation: disabled / Tool Capabilities: disabled". Asked to continue each held-out answer word for word from its first half (PREREG R16), neither the 70B nor the 8B reproduced the next ten words of any of the 160 (0 of 62 for texts first published in Aug and Sep 2026; v1.5's training-data cutoff is not documented, 3 of 120 for the 70B on texts unchanged since before 2023): no evidence of memorisation, from a probe that recalls little even of long-standing texts.

| 70B arm, items by backend of their calls (post hoc) | items | exact | ready | re-asked | edits saved vs rules-only |
|---|---|---|---|---|---|
| headline run: backend not logged | 154 | 21 (13.6%) | 59 (38.3%) | 98 | 42.6% |
| R2 rerun: every call `tp2` | 88 | 14 (15.9%) | 40 (45.5%) | 49 | 39.3% |
| R2 rerun: every call `fp1-nes` | 27 | 5 (18.5%) | 19 (70.4%) | 8 | 51.3% |
| R2 rerun: calls on both | 39 | 3 (7.7%) | 3 (7.7%) | 39 | 33.8% |

Both arms also have 12 rule-only items (no model call).

