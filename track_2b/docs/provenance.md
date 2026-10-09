# Provenance: how every reported number can be re-derived

## 1. The code that produced the numbers is the code that ships

The research pipeline was written and run between 8 and 9 Oct 2026 (research tree `spikes/`, not part of this repo).
Its files are vendored **byte-identical** into `src/gleichlaut/frozen/`. `eval/prereg/freeze.json` lists their sha256;
for 15 of them it also repeats the hash from the freeze record that was written on 9 Oct 2026 **before any output of the
fresh 2025 test existed** (guards3, its six resource files, guards.py, gl70.py, reask.py, run_v2.py, common.py,
lock.py, gl2.py and the fresh items). `tools/freeze.py` refuses to write a freeze file if any of those 15 differ.

`gleichlaut.core` does not re-implement the pipeline. It parses the frozen files with `ast` and executes only the named
definitions (the prompt `PA`, `RETRY`, `clean`, `chk`, `run_2b`, `FIX`, `full_check`, `complaints`, `run`, and the
scorer's `score_one` and `boot_diff`) with the model call injected. This is the same mechanism the original fresh run
used (`frozen/run_v2.py`).

## 2. Re-execution from recorded responses

Every model request is identified by the sha256 of its exact payload `{model, messages, max_tokens, temperature}`. The
development gateway stored each response under that key. `data/cache/responses/` holds the responses of the recorded
70B runs under the same keys, and the `cache` backend serves them. A request whose payload was not recorded raises an
error; it never falls through to a live call.

`make run` re-executes the whole pipeline (draft, lock check, retry, guards, re-ask) over the recorded item sets:

| Run | Items | Model calls rebuilt and found | Final records identical |
|---|---|---|---|
| fresh 2025 set, guards3 (the headline) | 166 | 285 / 285 | 166 / 166 |
| dev set, guards v2 | 120 | 242 / 242 | 120 / 120 |
| out-of-sample 2026 set, guards v2 (failed run) | 242 | 431 / 431 (323 distinct) | 238 / 242, see §3 |

A cache hit is a proof that the prompt was rebuilt byte-for-byte from the items by the frozen code.

## 3. The four out-of-sample records that do not re-execute

Numbers become slot codes before the model sees them, so two items that differ only in their numbers send the
**same** request. In the out-of-sample run, 4 items (all091-it, all095-it, all098-it, all161-it) shared a request with
another item that was in flight at the same time (two worker threads). The provider answered the two identical
requests differently, and the gateway cache kept one answer per request. Re-execution therefore returns the other
item's answer for these 4. Every other record matches.

This is also a measurement: at temperature 0, the same request to `swiss-ai/apertus-v1.5-70b` does not always return
the same text (consistent with `spikes/live/results.md`: two serving backends with different numerics). The reported
out-of-sample numbers are computed from the recorded outputs, which `make run` re-guards and re-scores exactly.

## 4. Re-scoring

`make run` re-guards every recorded output with the frozen stack and requires the flag to equal the recorded flag, then
recomputes every metric (exact, edit-F1, chrF, flag and ready rates, the paired cluster bootstrap over DE pairs, the
Wilson bounds) and requires the result to equal `eval/results/*.json`. The research summaries
(`spikes/rescue70b/{fresh,oos}/oos_scores.json`) were used as the oracle when this scorer was written: every field of
every group (all, unseen/seen families, FR, IT) matches.

## 5. Labels

Labels are the hand checks of the research runs (`eval/labels/`): every unflagged non-exact output was read in full
against the old and new German and the official French/Italian, plus a seeded sample of 20 flagged outputs (seed
20261009). They were made by Claude Code agents during the research and are declared as such; disagreement-adjudicated
second labels by the team lead are part of the remaining work (see `technical_report.md` §6).

## 6. What the model field shows and does not show

The recorded runs predate the discovery that the provider can silently answer from another model when a request
contains a system message or a prefilled assistant turn. Every recorded request is a single plain user message, the
condition under which that fallback was never observed; the recorded responses do not carry the `model` field. All new
calls (the stability rerun, certification, the live slice) log and check the served model on every response and refuse
a non-Apertus answer.
