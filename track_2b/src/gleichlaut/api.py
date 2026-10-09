"""Gleichlaut as a library: run the frozen checks on your own drafts, audit an item, see the exact prompt.

    from gleichlaut import api
    item = {"lang": "fr", "de_old": "...", "de_new": "...", "tgt_old": "..."}
    for c in api.check(item, my_draft):
        print(c["check"], c["ok"], c["severity"], c["sentence"])
    api.verdict(item, my_draft)   # {"status": "ready" | "flagged", "flag": bool, "checks": [...]}
    api.audit_item(item)          # pre-existing DE <-> FR/IT divergences of the old texts (gleichlaut.audit.audit_item)
    api.dry_run(item)             # routing, slot map and the exact first prompt; nothing is sent

check() runs the frozen guard stack (core.Pipeline.check: lock, slots, G1-G7; the same code the pre-registered results
were measured with) and returns one dict per check:
    check     id: lock | slot | g1 ... g7 | corrects (an informational note, see below)
    name      short English name (e.g. "G2 change applied")
    ok        True if the check passes
    severity  "flag" (the check fails: the draft is flagged) | "ok" | "info" (corrects note)
    sentence  one sentence in the item's language (fr / it) from gleichlaut.emit.explain when that module is importable,
              else English
    detail    the raw technical finding (English)
A draft is "ready" only if every check passes. "corrects" (severity info) says the draft also moves a number the German
does not touch towards the German (a pre-existing divergence corrected); it never changes the verdict.

Custom resources: if GLEICHLAUT_RESOURCES is set, the G5-G7 checks use the resources in that directory (gleichlaut
resources build); the results are then uncertified. Items need lang (fr | it), de_old, de_new, tgt_old; key is optional.
docs/api.md has worked examples."""
from . import core, resources

CHECKS = [("lock", "Lock: edits stay inside the change"), ("slot", "Slots: numbers, negation, modal verbs mirror the German change"),
          ("g1", "G1 no German left"), ("g2", "G2 change applied"), ("g3", "G3 nothing dropped"), ("g4", "G4 no duplication"),
          ("g5", "G5 nothing copied from the German"), ("g6", "G6 terminology"), ("g7", "G7 vocabulary")]
OK = {"fr": "Contrôle «\u00a0{n}\u00a0» réussi.", "it": "Controllo «{n}» superato.", "en": "Check passed: {n}."}
_P = {}
_RES = {"done": False}


def _pipeline(stack="g3"):
    if not _RES["done"]:
        resources.apply(); _RES["done"] = True       # GLEICHLAUT_RESOURCES, once per process
    if stack not in _P: _P[stack] = core.check_only(stack)
    return _P[stack]


def _item(item):
    if not isinstance(item, dict): raise TypeError("item must be a dict with lang, de_old, de_new, tgt_old")
    miss = [k for k in ("lang", "de_old", "de_new", "tgt_old") if not isinstance(item.get(k), str)]
    if miss: raise ValueError(f"item is missing text field(s) {miss} (docs/item-schema.json)")
    if item["lang"] not in ("fr", "it"): raise ValueError(f"item lang must be 'fr' or 'it', got {item['lang']!r}")
    x = dict(item); x.setdefault("key", "item")
    return x


def _explain():
    try:
        from .emit import explain
        return explain
    except Exception:                                 # emit is optional for library users
        return None


def _details(x, out, fc, g14):
    """id -> (ok, English detail), the per-guard verdicts of the frozen stack (as emit.lights computes them)."""
    g = fc["g"]
    return {"lock": (fc["lock"]["ok"], "; ".join(f"«{u}» -> «{v}»" for u, v in fc["lock"]["outside"][:4])),
            "slot": (not fc["slot"] and not fc["unknown"],
                     ", ".join(fc["slot"]) + (f"; {fc['unknown']} unknown slot code(s)" if fc["unknown"] else "")),
            "g1": (not g14["g1"], ", ".join(sorted(set(g14["g1"]))[:8])),
            "g2": (not g["g2"], "; ".join(de for _, de in g["g2"])),
            "g3": (not g["g3"], "; ".join(("lost: " if d[0] == "outside-lost" else f"near {d[1]}: ") + str(d[2]) for d in g["g3"])),
            "g4": (not g["g4"], "; ".join(f"«{n}»" for n in g["g4"][:3])),
            "g5": (not g.get("g5"), ", ".join(g.get("g5", [])[:8])),
            "g6": (not g.get("g6"), ", ".join(g.get("g6", [])[:8])),
            "g7": (not g.get("g7"), ", ".join(g.get("g7", [])[:8]))}


def check(item, draft, stack="g3"):
    """-> [dict(check, name, ok, severity, sentence, detail)] for one draft of one item (see the module doc)."""
    x = _item(item)
    if not isinstance(draft, str): raise TypeError("draft must be a string")
    P = _pipeline(stack); fc = P.check(x, draft); g14 = core.guards.run(x, draft)
    det = _details(x, draft, fc, g14)
    ex = _explain(); L = x["lang"]
    fs = ex.findings(x, draft, fc, g14) if ex else []
    by = {}
    for f in fs: by.setdefault("slot" if f["gid"] == "unknown" else f["gid"], []).append(f)
    res = []
    for cid, name in CHECKS:
        ok, detail = det[cid]
        if stack != "g3" and cid in ("g5", "g6", "g7"): continue
        if ok:
            sent = OK[L].format(n=ex.name(cid, L)) if ex else OK["en"].format(n=name)
        elif by.get(cid):
            sent = " ".join(f["text"] for f in by[cid])
        else:
            sent = f"{name}: failed ({detail})." if detail else f"{name}: failed."
        res.append(dict(check=cid, name=name, ok=bool(ok), severity="ok" if ok else "flag", sentence=sent,
                        detail=detail or ("" if ok else "failed")))
    for f in by.get("corr", []):
        res.append(dict(check="corrects", name="Corrects a pre-existing divergence", ok=True, severity="info",
                        sentence=f["text"], detail=f["detail"]))
    if fc["flag"] and not any(c["severity"] == "flag" for c in res):   # never report ready when the frozen verdict flags
        res.append(dict(check="verdict", name="Frozen guard verdict", ok=False, severity="flag",
                        sentence="The frozen checks flag this draft.", detail="full_check flag"))
    return res


def verdict(item, draft, stack="g3"):
    """-> dict(status 'ready' | 'flagged', flag, checks): the frozen verdict with its checks."""
    cs = check(item, draft, stack)
    flag = any(c["severity"] == "flag" for c in cs)
    return dict(status="flagged" if flag else "ready", flag=flag, checks=cs,
                certified=resources.active() is None,
                note=None if resources.active() is None else resources.review_reason())


def audit_item(item, **kw):
    """pre-existing problems of the item's old texts (numbers / units / language / editorial): gleichlaut.audit.audit_item."""
    from . import audit
    return audit.audit_item(_item(item), **kw)


class _Captured(Exception):
    def __init__(self, prompt, max_tokens): self.prompt, self.max_tokens = prompt, max_tokens


def dry_run(item, corpus="sl", prompt_domain=None):
    """-> dict(route, reason, model_call, prompt, max_tokens, slots, code_output) without sending anything: what draft
    would do with this item (routing, the slot map, the exact first prompt or the code lane's output)."""
    from . import backends, cli
    x = _item(item)
    if "change_ratio" not in x: x["change_ratio"] = cli.change_ratio(x["de_old"], x["de_new"])
    rt, why = cli.route(x, corpus)
    res = dict(key=x["key"], route=rt, reason=why, change_ratio=x["change_ratio"], model_call=False, prompt=None,
               max_tokens=None, slots={}, code_output=None)
    if rt == "human": return res
    def cap(prompt, tag, c, max_tokens): raise _Captured(prompt, max_tokens)
    ask = backends.DomainAsk(cap, prompt_domain) if prompt_domain else cap
    try:
        if corpus == "sl": r = core.Pipeline(ask, "g3").draft(x)
        else:
            from .fed import lane
            r = lane.fed_draft(x, ask)
    except _Captured as c:
        res.update(model_call=True, prompt=c.prompt, max_tokens=c.max_tokens)
        if corpus == "sl":
            S = core.gl2.Slots(x["tgt_old"]); S.mask(x["de_old"], "de"); S.mask(x["de_new"], "de"); S.mask(x["tgt_old"], x["lang"])
            res["slots"] = {k: (v if isinstance(v, str) else f"number word {v['w']}") for k, v in S.surf.items()}
        return res
    res["code_output"] = r["out"]
    return res
