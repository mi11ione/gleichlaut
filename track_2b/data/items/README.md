# Items and recorded runs: provenance

Only the Fedlex files are described here (the SL items are covered by `eval/prereg/freeze.json` and `docs/provenance.md`).
All four inputs are verbatim copies of the Gleichschritt S1 research tree (`spikes/gleichschritt/`, 8 Oct 2026);
the test `tests/test_fedlex.py::test_vendored_byte_identical_to_research` compares them when that tree is present.

| File | sha256 | Copied from | Content |
|---|---|---|---|
| `data/items/fedlex_items.json` | `2055820d111f87187c13d9fdff21d141efdfc117db1437eb4f1d088faabc73ad` | `items.json` | 155 items: 60 federal paragraphs x FR/IT (26 acts, new version applicable 2025-01-01..2026-10-08), 10 federal RM, 20 Graubuenden RM, 5 S3 (arm B only). `items_run.json` is the same 155 items in run order (sha256 `3419c78b...`), not copied |
| `data/items/fedlex_rm_contamination.json` | `8b0330f1a0b127bf4d7d60158062ff996c4097fd8bfd40ca286e519ad2a75154` | `results/s2_contamination.json` | 13-gram containment of the RM items in `swiss-ai/apertus-pretrain-romansh` (the RM clean / contaminated rows) |
| `data/runs/8b_dwq_fedlex_A.jsonl` | `a211e116357a6296f55f884628744ab95f0dbf1581b26d76037c20cbacb33a77` | `results/A.jsonl` | arm A, 150 records: `raw1`, `out1`, `check1`, retry `raw2`/`out2`/`check2`, timings. Apertus v1.5 8B text, MLX 4-bit DWQ (`m1rkocasu/Apertus-v1.5-8B-text-MLX-4bit-DWQ`), greedy, M2 Air. Prompts were not recorded (they are rebuilt from `gleich.py`; see the replay test) |
| `data/runs/8b_dwq_fedlex_B.jsonl` | `9aa645bd104f3208493adbc6053a01277e74d114c1355327e49bd3095a531239` | `results/B.jsonl` | arm B (free translation), 155 records |
| `data/items/fedlex_live5.json` | written by `gleichlaut.fed.lane.build_live5()` | derived | the 5 items of the `make run` live slice, with the selection rule and the recorded 8B outcome on each |

Licence of the texts: official federal texts, not protected by copyright (URG Art. 5); Graubuenden texts from GR-lex.
