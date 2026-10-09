# Using the checks in your own tool

For a developer who wants Gleichlaut's deterministic checks now, without running the monthly pipeline: check drafts made
by any translator or tool, audit an item's old texts, see the exact prompt, rebuild the check resources from your own
corpus, or draft another kind of text. Everything here runs on the Python standard library (lxml only for XLIFF/FHIR
validation) and calls no model.

## Install

```bash
git clone <repo> && cd gleichlaut
python3 -m pip install -e track_2b            # Python >= 3.9; gives the `gleichlaut` command (= python -m gleichlaut)
python3 -m pip install -e "track_2b[xliff]"   # plus lxml (pinned 6.0.2) for the XLIFF / FHIR validation
```

Install **editable** (`-e`): the package reads its test items, recorded runs, results and certificates from the checkout
(`gleichlaut.core.ROOT` is the `track_2b/` directory, resolved from the installed source). The frozen checks and their
resources ship as package data. Without installing: `PYTHONPATH=track_2b/src python3 ...`.

## An item

One amendment, one target language (the full schema with optional fields is [item-schema.json](item-schema.json)):

```python
item = {
    "lang": "fr",                                                       # fr | it
    "de_old": "Verrechnungspreis pro Applikation und Patient 230.27 (Teilung 7.5).",
    "de_new": "Verrechnungspreis pro Applikation und Patient 222.41 (Teilung 7.5).",
    "tgt_old": "Prix de facturation par application et patient 230.27 (Division 7.5).",
}
```

## `api.check(item, draft)`: the frozen checks on any draft

```python
from gleichlaut import api

for c in api.check(item, "Prix de facturation par application et patient 230.27 (Division 7.5)."):
    print(c["check"], c["ok"], c["severity"], c["sentence"])
# lock True ok Contrôle « Modifications limitées au changement » réussi.
# slot False flag Les nombres ne suivent pas l'allemand : allemand ajoute 222.41, retire 230.27 ; brouillon aucun changement.
# g1 True ok Contrôle « Allemand resté » réussi.
# ... g2 to g7
```

One dict per check, in a fixed order:

| Key | Value |
|---|---|
| `check` | `lock` (edits stay inside the change), `slot` (numbers, negation and modal verbs mirror the German change), `g1` (no German left), `g2` (the change is applied), `g3` (nothing dropped), `g4` (no duplication), `g5` (nothing copied from the German), `g6` (terminology), `g7` (vocabulary); plus `corrects` (see below) |
| `name` | short English name |
| `ok` | `True` if the check passes |
| `severity` | `flag` (fails: the draft is flagged), `ok`, or `info` (`corrects`) |
| `sentence` | one sentence in the item's language (French or Italian) when `gleichlaut.emit.explain` is importable (it is in this repository), else English |
| `detail` | the raw technical finding, English |

The checks are the frozen guard stack the pre-registered results were measured with (`core.Pipeline.check`; the
re-guarding of all 166 recorded 70B drafts through `api.check` gives the recorded verdict for every one). A draft is
**ready only if every check passes**. `corrects` (severity `info`) notes that the draft also moves a number the German
does not touch towards the German, i.e. it corrects a pre-existing divergence; it never changes the verdict.

```python
api.verdict(item, "Prix de facturation par application et patient 222.41 (Division 7.5).")
# {'status': 'ready', 'flag': False, 'checks': [...], 'certified': True, 'note': None}
```

`certified` is `False` when custom resources are in use (below).

## `api.audit_item(item)`: pre-existing divergences of the old texts

```python
api.audit_item(item)       # [] or [{kind: number|unit|language|editorial, lang, detail, text, ...}, ...]
```

A pass-through to `gleichlaut.audit.audit_item`: numbers or units on which the old French/Italian disagrees with the old
German, a target field written in another language, editorial problems next to numbers. Deterministic, no model.

## `api.dry_run(item)`: what drafting would send

```python
d = api.dry_run(item)
d["route"], d["model_call"], d["code_output"]
# ('draft', False, 'Prix de facturation par application et patient 222.41 (Division 7.5).')   numbers only: code applies it
```

For an item that needs the model, `model_call` is `True`, `prompt` is the exact first prompt, `max_tokens` its limit,
and `slots` the slot map (`⟨A⟩ -> 200`, ...): numbers reach the model only as slot codes and code writes them back.
`route` is `human` (with `reason`) for rewrites (> 60% of the German tokens changed) and long texts that need the model.
Nothing is sent. `api.dry_run(item, prompt_domain="...")` shows the prompt with a replaced first sentence (below).

## Your own check resources: `gleichlaut resources build`

G5–G7 use three resources per language: a whitelist of product, substance and ATC names (G5, G7), a vocabulary of the
target-language texts with document counts (G5, G7), and a German → French/Italian abbreviation map (G6). The frozen
ones were built from the SL register (`src/gleichlaut/frozen/g3/build_resources.py`). To build them from your texts:

`my_texts.jsonl`, one aligned text unit per line (any language may be missing; `names_fr` / `names_it` / `names` optional):

```json
{"de": "Die Behandlung erfordert eine Kostengutsprache des KVG-Versicherers.", "fr": "Le traitement nécessite une garantie de prise en charge de l'assureur LAMal.", "names_fr": ["Dupixent"]}
```

```bash
gleichlaut resources build --corpus my_texts.jsonl --out my-resources [--fhir fr=feed-fr.ndjson --fhir it=feed-it.ndjson] [--names fr=names.txt]
GLEICHLAUT_RESOURCES=my-resources python3 my_tool.py          # api.check / api.verdict use them
GLEICHLAUT_RESOURCES=my-resources gleichlaut draft --items x.json --out out/x
gleichlaut resources show
```

The rules are those of `build_resources.py` without its fixed paths: whitelist tokens ≥ 3 letters from the names;
vocabulary = number of distinct target texts containing each token; an abbreviation pair is kept when seen ≥ 2 times, ≥
60% of that abbreviation's pairings, A ≠ B, and A itself used in fewer than 5 target-language texts. A directory may hold
only some of the six files (`whitelist_/vocab_/terms_{fr,it}.json`); the others stay frozen. `manifest.json` records the
sources and hashes.

**Uncertified.** The frozen resources are part of what was measured and what every certificate is bound to. With
`GLEICHLAUT_RESOURCES` set, every certificate is void (the gate refuses them), `draft`/`month` mark every item for review
(`review_reason: custom check resources ...`), and `api.verdict` reports `certified: False`. `make run` and `replay`
ignore the variable. The switch is a hook in `gleichlaut.resources` that replaces the frozen module's dictionaries at
load time; the frozen files are never written.

## Another kind of text: `--prompt-domain`

The drafting prompt is frozen; its first sentence names the SL ("A Swiss reimbursement limitation (Spezialitätenliste,
BAG) was amended in German."). For other bilingual amendment work:

```bash
gleichlaut draft --items ordinance.json --out out/ord --backend llamacpp --prompt-domain "paragraph of a cantonal ordinance"
# -> "A paragraph of a cantonal ordinance was amended in German. Apply exactly the same amendment ..."
gleichlaut draft --items ordinance.json --out out/ord --dry-run --prompt-domain "An article of a federal ordinance was amended in German."
```

A noun phrase becomes "A <phrase> was amended in German."; a full sentence (ending in `.`) is used as given. Only the
first sentence changes ("Use the established terminology of the Spezialitätenliste" stays), the prompt string is
rewritten on its way to the model (`backends.DomainAsk`), the frozen files are untouched. **Uncertified:** every draft
goes to review, any backend may be used, and the certification gates do not apply. Only `--corpus sl` (the statute lane
has its own prompt).

## The pipeline as a library

`gleichlaut.core.Pipeline(ask)` is the full drafting loop (locked rewrite, lock retry, guards, one re-ask) with your own
model call `ask(prompt, tag, cap, max_tokens) -> (text, meta)`; `gleichlaut.backends` has the OpenAI-compatible,
llama.cpp and replay backends. `gleichlaut draft --items FILE --out DIR --backend stub` wires everything without a model.
