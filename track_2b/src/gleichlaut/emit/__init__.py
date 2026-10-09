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


def _source_raw(f):
    """The model text the final output was unmasked from (None: rules only, no model call)."""
    if f["rule_only"]: return None
    if f.get("replaced"): return f["reask_raw"]
    if f.get("retried") and f["out"] == f.get("out2"): return f["raw2"]
    if f["out"] == f.get("out1"): return f["raw1"]
    raise AssertionError(f"{f['key']}: cannot tell which model answer produced the output")


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


def load(run="fresh166"):
    """-> (run meta, [view]) for every item of a recorded run, in item order."""
    if run not in MODEL: raise SystemExit(f"emit: no recorded model id for run {run!r} (known: {', '.join(MODEL)})")
    core.verify_freeze(strict=True)
    R = score.RUNS[run]; I = score.load_items(R["items"]); F = score.load_jsonl(R["final"]); P = core.check_only(R["stack"])
    views = []
    for x in I:
        f = F[x["key"]]; out = f["out"]; fc = P.check(x, out)
        if R.get("recorded_flag", True) and fc["flag"] != f["guard_flag"]:
            raise AssertionError(f"{x['key']}: re-guarded flag {fc['flag']} != recorded {f['guard_flag']}")
        views.append(dict(
            key=x["key"], pair=x["pair"], lang=x["lang"], product=x.get("product") or "(product not recorded)",
            cud_id=cud_id(x), snap_old=x.get("snap_old", "?"), snap_new=x.get("snap_new", "?"), family=x["cluster"],
            de_old=x["de_old"], de_new=x["de_new"], tgt_old=x["tgt_old"], draft=out,
            status="flagged" if fc["flag"] else "ready", lights=lights(x, out, fc, f, R["stack"]),
            complaint=P.complaints(x, out) if fc["flag"] else "", rule_only=f["rule_only"], reasked=bool(f.get("reasked")),
            replaced=bool(f.get("replaced")), slots=f.get("slots") or {},
            numbers=numbers(out, _source_raw(f), x["lang"], f.get("slots"))))
    meta = dict(run=run, what=R["what"], stack=R["stack"], model=MODEL[run], pipeline=pipeline_id(R["stack"]),
                items_sha256=core.sha256(os.path.join(score.DATA, R["items"])), run_sha256=core.sha256(os.path.join(score.DATA, R["final"])))
    return meta, views


def select(views, n):
    """n items, deterministic: alternate ready and flagged in key order (both verdicts and both languages show up)."""
    if not n or n >= len(views): return list(views)
    r = [v for v in views if v["status"] == "ready"]; fl = [v for v in views if v["status"] == "flagged"]
    out = []
    while len(out) < n and (r or fl):
        for q in (r, fl):
            if q and len(out) < n: out.append(q.pop(0))
    return sorted(out, key=lambda v: v["key"])


def sha256_bytes(b): return hashlib.sha256(b).hexdigest()


def dump_json(obj, path):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh: json.dump(obj, fh, ensure_ascii=False, indent=1); fh.write("\n")
