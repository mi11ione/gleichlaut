# Backtest over the 2026 SL snapshots (M6, pre-registered rule R3)

This is a shadow-mode replay over the monthly snapshots of the BAG Spezialitätenliste (SL), using CPU only and no model calls.
The rule it follows is `eval/prereg/PREREG.md` R3, written before the code ran. Every number below comes from a file in
`data/backtest/`; the JSON path is given in brackets.

**Regenerate** (from `track_2b/`, about 40 s):
```
PYTHONPATH=src python3 -m gleichlaut.sl.ingest 20260219 20260304 20260401 20260601 20260701 20260801 20260901 20261001 20261006   # or reuse existing snapshots
PYTHONPATH=src python3 -m gleichlaut.backtest --hist <snapshot dir> --wb2025 <dir with 20250611/ and 20250731/Preparations.xml>
PYTHONPATH=src python3 -m unittest tests.test_mine      # the port reproduces the research mining (skips without the research data)
```
`inputs.sha256` in each JSON pins the 27 snapshot files and the 2 XML captures that were used. The outputs are identical
under different `PYTHONHASHSEED` values.

## Data

- **2026 snapshots.** Nine usable official ePL FHIR snapshots, 19 Feb to 6 Oct 2026, in DE/FR/IT.
  - The 4 May snapshot is excluded: the publisher dropped every `<…>` span in it.
  - The Feb–Apr files use the old export format, which has the same bug. A DE change pair from these files that contains `<` is dropped (the `sl.mine` rule).
- **2025 captures.** The two Wayback captures of the 2025 XML (releases of 1 Jun and 1 Jul 2025).
- **Mining.** `gleichlaut.sl.mine` is a port of the research miner. It reproduces the research step statistics and the 216 DE change pairs exactly.

## 1. Lag: does FR/IT trail the German? (`lag.json`)

**No lag was found.**

| | DE changes (≤60%) | FR changed same step | IT changed same step | changed later | never, within window |
|---|---|---|---|---|---|
| count | 216 [`summary.draft.units`] | 212 | 208 | 0 (FR and IT) | FR 4, IT 8 [`summary.draft.{fr,it}.status`] |

- **The 8 "never" cases** [`draft_not_same_step`] are all German-only corrections:
  - a deleted bullet (Fasenra);
  - typo fixes "follikuläremN on", "posftivem" in 3 rituximab biosimilars (IT only);
  - bullet and spacing fixes (Tezspire ×2);
  - a re-joined hyphenation (Rosuvastax);
  - a closing bracket (Opdivo).

  None of them needs a FR/IT change. The `de_edit` field shows each edit.
- **Rewrites of more than 60%** (the human lane): 27 distinct. In 26 of them FR and IT changed in the same step; 1 cannot be judged because of the `<` bug [`summary.human`].
- **Caveat.** "Same step" means the FR/IT text under the same key changed in that step. The backtest does not check that the change correctly implements the German.

**Figures quoted in the vision, checked** [`vision_figures_check`]:
- **"216 DE changes over 7 monthly steps."** The window has 8 steps, not 7, and spans 229 days (7.5 months):
  - 6 steps of about one month;
  - 1 step of 2 months (Apr→Jun, May excluded);
  - 1 step of 5 days (1→6 Oct).

  216 is correct. "About 31 a month" is 216/7; over the real span it is 28.7 a month.
- **"About 14 rewrites of more than 60% a month."** This is 97/7, but 97 counts matched product occurrences: 72 of them fall in Jun→Jul, where one rewrite repeats across many products. The number of distinct rewrites is **27**, about **3.6 a month**.

## 2. "Had it run since February" (`since_feb.json`): DEV numbers

Basis:
- **Outputs:** the recorded 70B outputs (whole-paragraph locked rewrite, guards v2, one re-ask) on the 362-item 2026 pool.
- **Placement:** each item sits on the transition where its DE change first qualified.
- **Flags:** re-computed with the frozen v2 stack, and equal to the recorded flags.

**These are dev numbers.** Guards v2 was shaped on 120 of these items, and guards3 was designed on the other 242.

| Step | DE changes ≤60% | >60% rewrites | in pool | FR/IT items | ready | flagged |
|---|---|---|---|---|---|---|
| 19.02→04.03 | 13 | 1 | 6 | 12 | 4 | 8 |
| 04.03→01.04 | 10 | 0 | 7 | 14 | 5 | 9 |
| 01.04→01.06 | 41 | 3 | 32 | 64 | 38 | 26 |
| 01.06→01.07 | 49 | 15 | 45 | 90 | 40 | 50 |
| 01.07→01.08 | 51 | 1 | 48 | 96 | 27 | 69 |
| 01.08→01.09 | 14 | 5 | 11 | 22 | 9 | 13 |
| 01.09→01.10 | 24 | 2 | 18 | 36 | 9 | 27 |
| 01.10→06.10 | 14 | 0 | 14 | 28 | 0 | 28 |
| **Total** | **216** | **27** | **181** | **362** | **132** | **230** |

The pool leaves out 30 DE changes longer than 2,500 characters and 5 where FR/IT did not change. Sources: `per_transition[].de_changes`, `totals`, `pool_stats`.

**"Ready" does not mean correct.** Of the 132 unflagged items [`totals.ready_v2_by_label`, hand labels in `eval/labels/`]:

| Hand label | Items |
|---|---|
| exact | 61 |
| equivalent | 47 |
| cosmetic | 9 |
| minor | 4 |
| German left in (the failure that made guards3) | 10 |
| real meaning error | 1 |

Re-guarded with guards3, 113 stay unflagged. That is the same outputs re-checked, not a guards3 run.

Single edit families dominate some steps [`per_transition[].largest_family`]:
- **01.04→01.06:** 28 of 64 items come from one edit family. This step also holds 38 of the pool's 42 rule-only items.
- **01.10→06.10:** 24 of 28 items come from one family. The slot guard flags every one of them, including the 17 that are exact.

## 3. The hand-verified divergences (`targeted5.json`, texts in `known_errors_texts.json`)

**(a) When did each divergence appear?** All ten limitations are already divergent in their earliest capture [`cases[].a`]. **None was introduced by a German amendment inside the 2026 window.**

| Limitation | Earliest capture, divergent | How it was found |
|---|---|---|
| Diaphin, Nepexto, Benepali, Erelzi, Dupixent .02/.05a | Jun 2025 | by code |
| Dupixent .02P/.05P | Jun 2025 | Split from .02/.05a in Jun 2026 with only the indication code changed; the 2025 text was found by nearest text in the same product. |
| Cresemba | Jul 2025 | No limitation in the Jun 2025 capture. |
| Nemluvio | Jul 2025 | Code `NEMLUVIO`, matched by nearest text (26% of tokens differ from the 2026 text). |

**Keytruda KN045 (bonus):**
- It is new in Aug 2026, for new products, with French in the Italian slot from its first publication.
- Its nearest existing limitation (`KEYTRUDA.07`, 1% different) has a correct Italian text.
- Context only, outside R3 [`origin_context`]: an amendment-style draft from that text would have been an Italian rule-only draft.

**(b) What the checks say about today's FR/IT against the DE** [`cases[].b_current.catches`]:
- **The numbers-not-in-DE check flags** the FR/IT numbers that the DE lacks:
  - Diaphin 12%;
  - the etanercept 62.5 kg (×3);
  - Dupixent .05a/.05P 30 kg.
- **It does not flag** numbers the target *drops*. Those are visible only in the slot comparison (`slot_diff`):
  - Cresemba 16 kg;
  - Dupixent .02/.02P 15 kg.
- **Neither check sees:**
  - Nemluvio: "acht" vs "quattro" are number words, and 4 also occurs elsewhere in the DE;
  - Keytruda: there is no numeric signal.

Note that numbers-not-in-DE is a scoring check. It is not part of the guard flag, and the guards compare old→new deltas, not static texts.

**(c) DE changes inside the window** [`cases[].c_de_changes_in_window`]:
- **DUPIXENT.02P (Apr→Jun).** The only real change: the indication code 20819.02 → 21258.02.
  - Gleichlaut handles it by rule, without the model. The draft is unflagged and equals the official new FR/IT exactly.
  - It therefore carries the existing French error forward unchanged. The locked rewrite preserves untouched text by design, and the guards check only the change.
  - The DE is 2,597 characters long, so it was not in the item pool.
- **DUPIXENT.05a/.05P (Apr→Jun).** Both are artefacts of the `<` bug (April lost a "< 60 kg …" span), not real changes.

**Conclusion, as R3 requires:** the backtest finds no lag, so the problem evidence rests on the verified divergences. All of them predate the window. Gleichlaut prevents the number class only in text it drafts; it does not repair errors already present in the old FR/IT.

## Limitations

- **Short window, so long lags would be invisible.** The window is 7.5 months. A change in the last steps has only 0–2 later snapshots.
- **Old-format snapshots (Feb–Apr) are less reliable.**
  - FR/IT keys are aligned by product and position.
  - Texts may be truncated by the `<` bug: Dupixent .05a/.05P carry a `caveat` field for this.
- **Nearest-text matches are not code matches.** Some captures (Nemluvio 2025, Dupixent .02P/.05P 2025) were located by nearest text, not by code. Each `methods` field says which.
- **The divergence tests come from the hand check.** They are the hand-checked values (`tests` per case), not a general detector. The research census precision was 6%, so no error count is claimed.
