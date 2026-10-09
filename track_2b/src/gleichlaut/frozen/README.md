# Frozen code (do not edit)

Every file in this directory is a **byte-identical copy** of the research code that produced the
reported numbers. The sha256 of each file is recorded in `eval/prereg/freeze.json`, and the hashes of the
guard stack, its resources and the fresh test items match the freeze record written on 9 Oct 2026
*before* any fresh-set output existed (see `docs/provenance.md`).

`gleichlaut.core` verifies these hashes at import and refuses to run on a mismatch. It does not import the
research scripts as modules (several of them read files at import time or need MLX). It parses them with
`ast` and executes only the named definitions (prompts, cleaners, the drafting loop, the guard checks, the
re-ask) with the model backend injected. That way the shipped pipeline runs the frozen source itself, not a
re-implementation.

| File | Origin (research tree) | Role at runtime |
|---|---|---|
| `s2/lock.py` | `spikes/gleichlaut/s2/lock.py` | edit windows, lock check, slot guard |
| `s2/gl2.py` | `spikes/gleichlaut/s2/gl2.py` | rules arm, planning, number slots |
| `s2/s2b.py` | `spikes/gleichlaut/s2/s2b.py` | source of the prompt `PA`, `RETRY`, `clean`, `chk` (8B runner; never imported) |
| `s2/s2.py` | `spikes/gleichlaut/s2/s2.py` | window-only arm (naive contrast; reference only) |
| `s2/score2.py` | `spikes/gleichlaut/s2/score2.py` | source of `edits`, `f1`, `chrf`, `score_one`, `boot_diff` |
| `gl/guards.py` | `spikes/rescue70b/gl/guards.py` | guards G1-G4 (V2) |
| `gl/gl70.py` | `spikes/rescue70b/gl/gl70.py` | source of `run_2b` (draft, lock check, one retry) |
| `gl/reask.py` | `spikes/rescue70b/gl/reask.py` | source of `FIX`, `full_check`, `complaints`, `run` (one guarded re-ask) |
| `g3/guards3.py` + `*.json` | `spikes/rescue70b/g3/` | guards G5-G7 and their resources (built from the Jun 2025 capture) |
| `g3/build_resources.py` | `spikes/rescue70b/g3/build_resources.py` | how the resources were built (reference) |
| `common.py`, `run_v2.py` | `spikes/rescue70b/`, `spikes/rescue70b/fresh/` | the gateway client and the substitutions used in the fresh run (reference) |
| `score_fresh.py`, `build_fresh.py` | `spikes/rescue70b/fresh/` | the fresh-set scorer and item builder (reference) |

Some files contain absolute paths of the machine they ran on. Those lines are inert here: `gleichlaut.core`
puts this directory on `sys.path` first and pre-imports `lock` and `gl2`, so the copies in this directory are
the ones that run.
