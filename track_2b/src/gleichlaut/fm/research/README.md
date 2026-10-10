# Failure-mode research code and data (PREREG R8, do not edit)

Byte-identical copies from the research tree `~/Desktop/hackapertus/spikes/` (copied 10 Oct 2026, before any R8 run);
sha256 in `SHA256SUMS` (`shasum -a 256 -c SHA256SUMS`). `gleichlaut.fm` checks them at import and refuses to run on a
mismatch. The SL tests T1, T2 and T5 need nothing from here: their prompts and loops are `frozen/s2/s2.py` and
`frozen/s2/s2b.py`, already in the repository.

| Path | Research path | Role in R8 |
|---|---|---|
| `round7/fedlex_items.json` | `round7/fedlex_items.json` | T3: the 9 known Fedlex divergences + 36 controls (DE/FR/IT) |
| `round7b/spike7b.py` | `round7b/spike7b.py` | T3: the pairwise prompt `PAIR["de"]` (lines 67-72), `PAIRS` (92) and the two orders of `pair_score` (94-103); only the assignments are executed (MLX lines are inert here) |
| `round7b/analyze7b.py` | `round7b/analyze7b.py` | T3: scorer of the log-probability arm (hits, false flags, AUROC, argmax), executed whole on a staged copy |
| `round7b/results/fedlex7b_A.json` | same | T3: the MLX 4-bit run (recorded log-probabilities), re-scored beside the Q8_0 run |
| `rescue70b/fx/fx.py` | `rescue70b/fx/fx.py` | T3: generation arm (`Q` = `PAIR["de"]["q"]`, `parse`, localisation), executed whole with the recorded answers |
| `rescue70b/fx/fx_raw.json` | same | T3: the 70B answers, re-scored |
| `dreiklang/scripts/s1.py` | `dreiklang/scripts/s1.py` | T4: `INSTR`, `TAIL`, `PREFIX`, `OPTIONS` (lines 16-42); the scoring loop (67-117) is followed with llama.cpp instead of MLX |
| `dreiklang/s1_items.json`, `s1_candmap.json`, `items.json`, `gold_raw.txt`, `gold.tsv`, `gold_flags.tsv` | same | T4: the 885 prompts, the candidate map, items and the gold |
| `dreiklang/scripts/{analyze,correlation,gold,compare,cands,regex_v2,gold_flags}.py` | same | T4: the scorers, executed on a staged copy in a subprocess |
| `dreiklang/raw/{s1_scores.jsonl,s1_meta.json,threshold.json}` | same | T4: the MLX 4-bit run, re-scored beside the Q8_0 run |
| `gleichlaut/scripts/census.py` | `gleichlaut/scripts/census.py` | T4: lexicons imported by `cands.py` and `regex_v2.py` |

Known inert lines: `spike7b.py` imports `mlx` at top level and `fx.py` reads its items from an absolute path and imports
`common` (the gateway client); `cands.py` and `regex_v2.py` add `~/Desktop/hackapertus/spikes/gleichlaut/scripts` to
`sys.path`. None of these runs here as written: the staging puts `census.py` next to the scripts, `fx.py` gets the
vendored items and a replay `ask`.
