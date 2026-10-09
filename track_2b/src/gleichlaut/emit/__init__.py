"""Hand-off formats for recorded Gleichlaut runs: FHIR (BAG's ePL format, fhir.py) and XLIFF 2.1 (translators' tools,
xliff.py), validated by validate.py; the review page (gleichlaut.ui) reads the same per-item views.

No model is called here. Drafts are the recorded run outputs; every verdict is recomputed with the frozen guard stack and
must equal the flag the record carries. The official FR/IT text of the item (tgt_new) is evaluation data and never read."""
import hashlib, json, os, re
from .. import __version__, core, score

SCHEMAS = os.path.join(core.ROOT, "data", "schemas")
# The model each recorded run requested (the run records carry outputs, not the model name; see score.RUNS["..."]["what"]).
MODEL = {"fresh166": core.M70, "oos242": core.M70, "dev120": core.M70}
GUARDS = [("lock", "Lock", "only the amended part changed"), ("slot", "Slots", "numbers, negation, modals mirror the DE change"),
          ("g1", "G1", "no German left in the target"), ("g2", "G2", "the DE change is carried over"),
          ("g3", "G3", "no text lost outside the change (G3a) or removed beyond it (G3c)"),
          ("g4", "G4", "no duplicated clause"), ("g5", "G5", "no word copied from the DE"),
          ("g6", "G6", "terminology map respected"), ("g7", "G7", "no out-of-vocabulary word")]
WORDRX = {L: re.compile(r"\b(?:" + "|".join(core.gl2.NUMW[L][2:]) + r")\b", re.I) for L in ("de", "fr", "it")}


def pipeline_id(stack):
    """Pipeline version string: package version, guard stack, sha256 of the pre-registration freeze record."""
    return f"gleichlaut {__version__}; guards {stack}; freeze sha256:{core.sha256(core.FREEZE)}"


def cud_id(x):
    """The ePL ClinicalUseDefinition id of the limitation: the SL limitation code with every character outside
    [A-Za-z0-9.-] replaced by '-' and cut at 64 (BAG's own rule, read off the feed: NINLARO_01 -> NINLARO-01).
    Old-format 2026 keys ('RA:<uuid>#i') are not limitation codes, so the 2025 code is used for them. Items mined from
    the new-format feed carry the CUD id itself (cud_new); items without any code get 'GL-<pair>' (not an ePL id)."""
    new = x.get("cud_new") or x.get("code_new") or ""
    c = new if new and not new.startswith("RA:") else (x.get("code_old") or x.get("cud_old") or "GL-" + x["pair"])
    return re.sub(r"[^A-Za-z0-9\-.]", "-", c)[:64]


def _old_id(x):
    """The previous limitation code of the item (None when not recorded): code_old / cud_old, ePL id rule."""
    c = x.get("code_old") or x.get("cud_old")
    return re.sub(r"[^A-Za-z0-9\-.]", "-", c)[:64] if c else None


def _source_raw(f):
    """The model text the final output was unmasked from (None: rules only, no model call)."""
    if f["rule_only"]: return None
    if f.get("replaced"): return f["reask_raw"]
    if f.get("retried") and f["out"] == f.get("out2"): return f["raw2"]
    if f["out"] == f.get("out1"): return f["raw1"]
    raise AssertionError(f"{f['key']}: cannot tell which model answer produced the output")


def _source_raw_any(f):
    """For records written outside the recorded runs: the exact source answer when it can be told, else every model
    answer of the record together (conservative: a number in any of them counts as written by the model)."""
    try: return _source_raw(f)
    except (AssertionError, KeyError):
        raw = "\n".join(str(f[k]) for k in ("raw1", "raw2", "reask_raw", "raw") if f.get(k))
        return raw or None


def numbers(out, raw, lang, slots):
    """-> [(start, end, text, who, slot)] for every number in the draft (digits per gl2.NUMRX, number words 2-12).
    who = "code" unless the model text itself contained that number (then "model"): slot codes are the only way a
    number reaches the draft from the model, and code writes their values back."""
    spans = [(m.start(), m.end(), m.group(0)) for m in core.gl2.NUMRX.finditer(out)]
    spans += [(m.start(), m.end(), m.group(0)) for m in WORDRX[lang].finditer(out)]
    spans.sort()
    left = {}
    if raw:
        for m in list(core.gl2.NUMRX.finditer(raw)) + list(WORDRX[lang].finditer(raw)):
            k = core.gl2.nval(m.group(0)).lower(); left[k] = left.get(k, 0) + 1
    inv = {}
    for c, v in (slots or {}).items():
        if isinstance(v, str): inv.setdefault(core.gl2.nval(v), c)
    res = []
    for a, b, t in spans:
        k = core.gl2.nval(t).lower()
        if left.get(k): left[k] -= 1; who = "model"
        else: who = "code"
        res.append((a, b, t, who, inv.get(core.gl2.nval(t), "")))
    return res


def lights(x, out, fc, f, stack):
    """Per-guard traffic lights: [(id, label, state, detail)], state in pass | fail | off."""
    g = fc["g"]; g14 = core.guards.run(x, out)                     # frozen G1-G4 alone (guards3 merges G5-G7 into g1)
    det = {"lock": (fc["lock"]["ok"], "; ".join(f"«{u}» -> «{v}»" for u, v in fc["lock"]["outside"][:4])),
           "slot": (not fc["slot"] and not fc["unknown"],
                    ", ".join(fc["slot"]) + (f"; {fc['unknown']} unknown slot code(s)" if fc["unknown"] else "")),
           "g1": (not g14["g1"], ", ".join(sorted(set(g14["g1"]))[:8])),
           "g2": (not g["g2"], "; ".join(de for _, de in g["g2"])),
           "g3": (not g["g3"], "; ".join(("G3a lost: " if d[0] == "outside-lost" else f"G3c near {d[1]}: ") + str(d[2]) for d in g["g3"])),
           "g4": (not g["g4"], "; ".join(f"«{n}»" for n in g["g4"][:3]))}
    for k in ("g5", "g6", "g7"):
        det[k] = (not g.get(k), ", ".join(g.get(k, [])[:8])) if stack == "g3" else (None, "not in the v2 stack")
    res = [(i, lab, "off" if det[i][0] is None else ("pass" if det[i][0] else "fail"), det[i][1] or what) for i, lab, what in GUARDS]
    if f["rule_only"]: ra = ("off", "no model call: rules covered every change")
    elif not f.get("reasked"): ra = ("off", "not needed: the first draft passed")
    elif f.get("replaced"): ra = ("pass", "used and kept: the re-asked draft passed every guard")
    else: ra = ("fail", "used, not kept: the re-asked draft still failed; the first draft stays, flagged")
    return res + [("reask", "Re-ask", ra[0], ra[1])]


HUMAN_RATIO = 0.6     # items whose German is rewritten beyond this go to a translator without a draft (records status "human")


def _view(x, f, P, stack, check_recorded=True, any_raw=False):
    """One per-item view: the draft, its verdict, lights, findings in plain language.
    Verdict: ready ONLY if every frozen guard passes AND the record's own status (when present) is "ready". A record
    with status "flagged" (air-gapped mode, statute lane, uncertified local model, ...) stays flagged and its
    review_reason is shown as a finding; status "human" (or no draft) = routed to a translator."""
    from . import explain
    base = dict(key=x["key"], pair=x["pair"], lang=x["lang"], product=x.get("product") or "(product not recorded)",
                cud_id=cud_id(x), old_id=_old_id(x), snap_old=x.get("snap_old", "?"), snap_new=x.get("snap_new", "?"), family=x.get("cluster", "-"),
                de_old=x["de_old"], de_new=x["de_new"], tgt_old=x["tgt_old"], change_ratio=x.get("change_ratio", x.get("de_ratio")),
                divergence=explain.divergence(x), record_status=(f or {}).get("status"))
    base["banner"] = explain.banner(x, base["divergence"], None if f is None else f.get("out"))
    if f is None or f.get("status") == "human" or f.get("out") is None:
        return dict(base, draft="", status="human", lights=[], complaint="", findings=[], rule_only=False, reasked=False,
                    replaced=False, slots={}, numbers=[], reason=(f or {}).get("reason") or "")
    f = dict(f); f.setdefault("rule_only", False); out = f["out"]; fc = P.check(x, out)
    rs = f.get("status")
    if rs not in (None, "ready", "flagged"): raise AssertionError(f"{x['key']}: unknown record status {rs!r}")
    if check_recorded and "guard_flag" in f and fc["flag"] != f["guard_flag"] and not f.get("review_reason"):
        raise AssertionError(f"{x['key']}: re-guarded flag {fc['flag']} != recorded {f['guard_flag']}")
    rec_flag = rs == "flagged" and (bool(f.get("review_reason")) or not fc["flag"])
    flagged = fc["flag"] or rs == "flagged"
    fs = explain.findings(x, out, fc, core.guards.run(x, out))
    if not fc["flag"]: fs = [d for d in fs if d["gid"] == "corr"]
    L = lights(x, out, fc, f, stack)
    if rec_flag:
        rf = explain.record_finding(f.get("review_reason"), x["lang"], f["rule_only"])
        fs.insert(1 if fs and fs[0]["gid"] == "corr" else 0, rf)
        L = [("record", "Record", "fail", f"record status flagged: {f.get('review_reason') or '(no reason recorded)'}")] + L
    complaint = P.complaints(x, out) if fc["flag"] else ""
    if rec_flag: complaint = "\n".join(c for c in (f"- {explain.review_text(f.get('review_reason'), 'en', f['rule_only'])}", complaint) if c)
    return dict(base, draft=out, status="flagged" if flagged else "ready", lights=L, complaint=complaint, findings=fs,
                rule_only=f["rule_only"], reasked=bool(f.get("reasked")), replaced=bool(f.get("replaced")),
                slots=f.get("slots") or {}, numbers=numbers(out, _source_raw_any(f) if any_raw else _source_raw(f), x["lang"], f.get("slots")))


def load(run="fresh166", records=None, items=None):
    """-> (run meta, [view]) for every item of a recorded run (or of a records + items pair), in item order."""
    if records or items: return load_records(records, items)
    if run not in MODEL: raise SystemExit(f"emit: no recorded model id for run {run!r} (known: {', '.join(MODEL)})")
    core.verify_freeze(strict=True)
    R = score.RUNS[run]; I = score.load_items(R["items"]); F = score.load_jsonl(R["final"]); P = core.check_only(R["stack"])
    views = [_view(x, F[x["key"]], P, R["stack"], R.get("recorded_flag", True)) for x in I]
    meta = dict(run=run, what=R["what"], stack=R["stack"], model=MODEL[run], pipeline=pipeline_id(R["stack"]),
                items_sha256=core.sha256(os.path.join(score.DATA, R["items"])), run_sha256=core.sha256(os.path.join(score.DATA, R["final"])),
                custom=False, has_tgt_new=True)
    return meta, views


def _read_items(path):
    """A JSON list, a JSON object (with an items list, one record, or records by key) or JSONL."""
    txt = open(path, encoding="utf-8").read().strip()
    try: d = json.loads(txt)
    except json.JSONDecodeError: return [json.loads(l) for l in txt.splitlines() if l.strip()]
    if isinstance(d, list): return d
    if isinstance(d.get("items"), list): return d["items"]
    return [d] if "key" in d else list(d.values())


def load_records(records, items):
    """Records written by `gleichlaut month` / `draft` (record format of data/runs/70b_fresh166_g3_final.jsonl) over an
    items file (key, lang, de_old, de_new, tgt_old, optional tgt_new, product, change_ratio). Every draft is re-guarded
    with the frozen guards3 stack; a recorded guard_flag, when present, must equal the recomputed one. Records with
    status "human" (or without out) are items routed to a translator without a draft."""
    if not (records and items): raise SystemExit("emit: --records and --items go together")
    core.verify_freeze(strict=True)
    I = _read_items(items); F = {r["key"]: r for r in _read_items(records)}; P = core.check_only("g3")
    for x in I:
        x.setdefault("pair", re.sub(r"-(fr|it|rm)$", "", x["key"]))
        x.setdefault("cluster", x.get("family") or "-")
    missing = [x["key"] for x in I if x["key"] not in F]
    if missing: raise SystemExit(f"emit: no record for {len(missing)} item(s), e.g. {missing[:3]}")
    views = [_view(x, F[x["key"]], P, "g3", True, any_raw=True) for x in I]
    stem = os.path.splitext(os.path.basename(records))[0]
    if stem == "records": stem = os.path.basename(os.path.dirname(os.path.abspath(records))) or stem      # out/<run>/records.jsonl
    stem = re.sub(r"[^A-Za-z0-9_.-]+", "-", stem).strip("-") or "records"
    model = records_model(F.values(), records) or os.environ.get("LLM_NAME") or None
    meta = dict(run=stem, what=f"records {os.path.basename(records)} over items {os.path.basename(items)}", stack="g3",
                model=model or "not recorded", model_known=bool(model),
                pipeline=pipeline_id("g3"), items_sha256=core.sha256(items), run_sha256=core.sha256(records), custom=True,
                has_tgt_new=all(x.get("tgt_new") for x in I), items_path=items, records_path=records)
    return meta, views


def records_model(recs, records_path=None):
    """The model id of a records file: a record's model / model_id field; else the call log next to the records
    (calls.jsonl or live_calls.jsonl: the requested model, else the served one, most frequent first); else the model
    named in a record's backend label ('openai <endpoint> <model>', 'llamacpp <model>'); None when nothing names it."""
    from collections import Counter
    for r in recs:
        for k in ("model", "model_id", "llm"):
            if isinstance(r.get(k), str) and r[k].strip(): return r[k].strip()
    if records_path:
        d = os.path.dirname(os.path.abspath(records_path)); c = Counter()
        for fn in ("calls.jsonl", "live_calls.jsonl"):
            p = os.path.join(d, fn)
            if not os.path.exists(p): continue
            for line in open(p, encoding="utf-8"):
                try: rec = json.loads(line)
                except ValueError: continue
                m = rec.get("model") or rec.get("model_served") if isinstance(rec, dict) else None
                if isinstance(m, str) and m.strip(): c[m.strip()] += 1
        if c: return c.most_common(1)[0][0]
    for r in recs:
        b = r.get("backend")
        if isinstance(b, str):
            p = b.split()
            if len(p) >= 3 and p[0] == "openai": return p[-1]
            if len(p) >= 2 and p[0] == "llamacpp": return p[1]
            if p and p[0] == "stub": return "stub (no model)"
    return None


def model_label(meta):
    """The model id for notes and headers; 'recorded run <run>' when the records do not name the model."""
    return meta["model"] if meta.get("model_known", True) else f"recorded run {meta['run']}"


def select(views, n):
    """n items, deterministic: alternate ready and flagged in key order (both verdicts and both languages show up)."""
    if not n or n >= len(views): return list(views)
    r = [v for v in views if v["status"] == "ready"]; fl = [v for v in views if v["status"] == "flagged"]
    h = [v for v in views if v["status"] == "human"]
    out = []
    while len(out) < n and (r or fl or h):
        for q in (r, fl, h):
            if q and len(out) < n: out.append(q.pop(0))
    return sorted(out, key=lambda v: v["key"])


def sha256_bytes(b): return hashlib.sha256(b).hexdigest()


def dump_json(obj, path):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh: json.dump(obj, fh, ensure_ascii=False, indent=1); fh.write("\n")
