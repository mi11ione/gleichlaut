"""The "Register audit" tab of the review page: one row per finding of the pre-existing DE/FR/IT congruence audit
(data/audit/audit_<date>.json, written by gleichlaut.audit), headline figures from eval/results/audit.json.

Reads both the current finding shape (kind 'numeric', lang, de_only / tgt_only with '[value]' contexts, known) and the
extended one (kind number | unit | language | editorial, langs, odd_one_out, snippets, suggested_action); anything absent
is derived or left empty, never invented:
  snippets   f["snippets"][lang] when given; else the audit's own contexts (DE from de_only, the finding's language from
             tgt_only, the other target language from that language's finding on the same limitation); else, when the SL
             snapshot files are at hand (--hist / $GLEICHLAUT_HIST / out/hist), the passage of that language around the
             number that shares the most other numbers with the reference context (else at the same relative position).
  odd one out  f["odd_one_out"] when given; else: the finding's language when the other target language has no finding
             on that limitation (it agrees with the German), "de" when both target languages have the same finding
             against the German, "unclear" otherwise.
Values are highlighted in each snippet: conflicting values (the finding's values, or '[...]' in a context) as 2, other
numbers as 1, each with its unit when one follows.
  sig        the finding's signature, limitation id + kind + language + values (the conflicting numbers; surface ->
             suggestion; detected language; old -> new term): the page keys the officer's decisions by it, not by the
             audit date, so a decision carries over to the next audit run where the same finding reappears.
  eq         a number finding the audit marks likely_equivalent (probably a paraphrase): its reason (shown collapsed under
             "probably equivalent wording", never dropped).
  term       a finding of kind 'terminology' (BAG corrected term X -> Y elsewhere, this text still says X): old term, new
             term and where BAG already corrected it (explain.term_parts)."""
import hashlib, json, os, re
from .. import core

AUDIT = os.path.join(core.ROOT, "data", "audit", "audit_20261006.json")
RESULTS = os.path.join(core.ROOT, "eval", "results", "audit.json")
KINDS = ("number", "unit", "language", "editorial", "terminology")
ACTIONS = {"Berichtigung": "exofficio", "GÄL": "holder", "GAEL": "holder", "none": "none", "unclear": "unclear"}
LANGS = ("de", "fr", "it")
NUMW = core.gl2.NUMW
try:
    from ..audit import UNIT_RX as _UNIT_RX
except Exception:                       # the audit module is being extended by a teammate: degrade to no unit binding
    _UNIT_RX = {}
SENT = re.compile(r"[^.;!?]*(?:[.;!?](?=\s|$)|$)")


def _kind(f):
    k = str(f.get("kind") or "").lower()
    if k in ("term", "terms", "term_pair"): return "terminology"
    return k if k in KINDS else "number" if k in ("numeric", "num", "numbers", "") else k


def _eq(f):
    """The likely_equivalent reason of a number finding ('' when flagged without a reason), None when not flagged."""
    e = f.get("likely_equivalent")
    if not e: return None
    if isinstance(f.get("equivalence"), str) and f["equivalence"].strip(): return f["equivalence"].strip()
    if isinstance(e, str): return e
    if isinstance(e, dict): return str(e.get("reason") or e.get("why") or e.get("detail") or "")
    return str(f.get("equivalent_reason") or f.get("likely_equivalent_reason") or f.get("reason") or "")


def signature(f, lim, L, kind, V, term=None):
    """limitation id | kind | language | values: the key a decision is stored under across audit runs."""
    if kind == "editorial" and f.get("surface"): vals = [f"{f.get('surface')}>{f.get('suggestion') or ''}"]
    elif kind == "language": vals = [str(f.get("detected") or f.get("found") or "")]
    elif kind == "terminology" and term and (term[0] or term[1]): vals = [f"{term[0] or ''}>{term[1] or ''}"]
    else:
        vals = sorted(set().union(*V.values())) if V else []
        if not vals: vals = [re.sub(r"\s+", " ", str(f.get("description") or f.get("detail") or ""))[:120]]
    return "|".join([str(lim or ""), kind, str(L or ""), ",".join(vals)])


def _canon(v):
    v = re.sub(r"[ '’  ]", "", str(v)).replace(",", ".")
    try:
        x = float(v); return str(int(x)) if x == int(x) else repr(x).rstrip("0").rstrip(".")
    except ValueError: return v.lower()


def _vals(f):
    """-> {lang: set(canonical values)} the finding names as conflicting."""
    res = {L: set() for L in LANGS}
    V = f.get("values")
    if isinstance(V, dict):
        for L, xs in V.items():
            if L in res: res[L] |= {_canon(x) for x in (xs if isinstance(xs, (list, tuple, set)) else [xs])}
    elif isinstance(V, (list, tuple)):
        for L in LANGS: res[L] |= {_canon(x) for x in V}
    for x in f.get("de_only") or []: res["de"].add(_canon(x.get("value")))
    for x in f.get("tgt_only") or []:
        if f.get("lang") in res: res[f["lang"]].add(_canon(x.get("value")))
    return res


def _num_rx(lang):
    w = NUMW.get(lang, NUMW["de"])[2:]
    return re.compile(r"\d+(?:[.,'’]\d+)*|\b(?:" + "|".join(w) + r")\b", re.I)


def highlight(text, lang, hot):
    """-> [[text, 0|1|2]]: '[x]' marks and values in `hot` as 2, other numbers as 1 (unit included when one follows)."""
    marks, plain, pos = [], "", 0
    for m in re.finditer(r"\[([^\]]{1,240})\]", text):
        plain += text[pos:m.start()]; marks.append((len(plain), len(plain) + len(m.group(1)), 2)); plain += m.group(1); pos = m.end()
    plain += text[pos:]
    words = NUMW.get(lang, NUMW["de"])
    for m in _num_rx(lang).finditer(plain):
        if any(a <= m.start() < b for a, b, _ in marks): continue
        t = m.group(0).lower()
        v = str(words.index(t)) if t in words else _canon(t)
        marks.append((m.start(), m.end(), 2 if v in hot else 1))
    out, pos = [], 0
    for a, b, k in sorted(marks):
        if a < pos: continue
        u = _UNIT_RX.get(lang).match(plain, b) if _UNIT_RX.get(lang) else None
        if u and u.group(0).strip(" -."): b = u.end()
        if a > pos: out.append([plain[pos:a], 0])
        out.append([plain[a:b], k]); pos = b
    if pos < len(plain): out.append([plain[pos:], 0])
    return out


def _clip(s, n=300):
    s = re.sub(r"\s+", " ", s).strip()
    return s if len(s) <= n else s[:n].rsplit(" ", 1)[0] + " …"


_HIST = {}
def _bundled_texts(date, lim):
    """the texts shipped in data/audit/audit_texts_<date>.json (every limitation with a finding), for builds without
    the snapshot files, e.g. the published Pages build."""
    p = os.path.join(os.path.dirname(AUDIT), f"audit_texts_{date}.json")
    if p not in _HIST: _HIST[p] = json.load(open(p, encoding="utf-8"))["texts"] if os.path.exists(p) else {}
    return dict(_HIST[p].get(lim, {}))


def _hist_texts(hist, date, lim):
    """{lang: full text} of one limitation from the SL snapshot files (empty when they are not at hand)."""
    out = {}
    for L in LANGS:
        p = os.path.join(hist, f"{date}-{L}.json") if hist else ""
        if not p or not os.path.exists(p): return _bundled_texts(date, lim)
        if p not in _HIST: _HIST[p] = json.load(open(p, encoding="utf-8"))["lim"]
        if lim in _HIST[p]: out[L] = re.sub(r"\s+", " ", _HIST[p][lim]).strip()
    return out


def _values_in(s, lang):
    words = NUMW.get(lang, NUMW["de"]); out = []
    for m in _num_rx(lang).finditer(s):
        t = m.group(0).lower(); out.append((m.start(), str(words.index(t)) if t in words else _canon(t)))
    return out


def _window(full_ref, ctx_ref, ref_lang, full, lang, w=70):
    """The passage of `full` that corresponds to the German context: the window around a number of `full` that shares the
    most other numbers with the German context (ties: closest relative position); without shared numbers, the window
    at the German context's relative position. Written like the audit's contexts: '…' + about 2*w characters + '…'."""
    core_ref = re.sub(r"[…\[\]]", "", ctx_ref).strip()
    pos = full_ref.find(core_ref[:40]); rel = (pos + len(core_ref) / 2) / max(1, len(full_ref)) if pos >= 0 else 0.5
    anchors = {v for _, v in _values_in(core_ref, ref_lang)} - {"1"}
    V = _values_in(full, lang); best, at = (0, 0.0), int(rel * len(full))
    for p, _ in V:
        win = {v for q, v in V if abs(q - p) <= w}
        sc = (len(win & anchors), -abs(p / max(1, len(full)) - rel))
        if sc > best: best, at = sc, p
    a, b = max(0, at - w), min(len(full), at + w)
    a = full.rfind(" ", 0, a) + 1 if a > 0 else 0
    b = (full.find(" ", b) if full.find(" ", b) > 0 else len(full)) if b < len(full) else b
    return ("…" if a > 0 else "") + full[a:b].strip() + ("…" if b < len(full) else "")


def rows(F, hist=None, date="20261006"):
    by = {}
    for f in F: by.setdefault((f.get("id"), f.get("lang")), []).append(f)
    out, seen = [], set()
    for f in F:
        lim, L, kind = f.get("id"), f.get("lang"), _kind(f)
        langs = f.get("languages") or f.get("langs") or (["de", L] if L else [])
        other = {"fr": "it", "it": "fr"}.get(L)
        V = _vals(f); hot = set().union(*V.values())
        twin = [g for g in by.get((lim, other), []) if _kind(g) == kind]
        snip, src = {}, {}
        S = f.get("snippets")
        if isinstance(S, dict):
            for k, s in S.items():
                s = s[0] if isinstance(s, (list, tuple)) and s else s
                if k in LANGS and isinstance(s, str) and s.strip(): snip[k] = s; src[k] = "audit"
        def ctx(xs): return next((x["context"][0] for x in xs or [] if x.get("context")), None)
        top = f.get("context")
        top = top[0] if isinstance(top, (list, tuple)) and top else top if isinstance(top, str) else None
        if top and L in LANGS and L not in snip and kind in ("language", "editorial", "terminology"): snip[L] = top; src[L] = "context"
        if "de" not in snip and ctx(f.get("de_only")): snip["de"] = ctx(f.get("de_only")); src["de"] = "context"
        if L and L not in snip and ctx(f.get("tgt_only")): snip[L] = ctx(f.get("tgt_only")); src[L] = "context"
        for g in twin:
            if other not in snip and ctx(g.get("tgt_only")): snip[other] = ctx(g.get("tgt_only")); src[other] = "context"
            if "de" not in snip and ctx(g.get("de_only")): snip["de"] = ctx(g.get("de_only")); src["de"] = "context"
        full = _hist_texts(hist, date, lim)
        ref = next((k for k in LANGS if k in snip and k in full), None)
        if full and ref:                           # fill a missing language from the snapshot, near the reference context
            for k in LANGS:
                if k in snip or k not in full: continue
                snip[k] = _window(full[ref], snip[ref], ref, full[k], k); src[k] = "snapshot"
        odd = f.get("odd_one_out")
        if odd not in LANGS + ("unclear",) and kind == "terminology" and L in LANGS: odd = L
        if odd not in LANGS + ("unclear",):
            sig = lambda g: ({_canon(x.get("value")) for x in g.get("de_only") or []}, {_canon(x.get("value")) for x in g.get("tgt_only") or []})
            odd = "unclear" if not other else L if not twin else "de" if any(sig(g) == sig(f) for g in twin) else "unclear"
        prod = f.get("product")
        prod = ", ".join(prod) if isinstance(prod, (list, tuple)) else (prod or "")
        term = None
        if kind == "terminology":
            from ..emit.explain import term_parts
            term = term_parts(f, L)
        sig = signature(f, lim, L, kind, V, term)
        rid = hashlib.sha1("\0".join(map(str, (lim, L, kind, f.get("description") or f.get("detail") or ""))).encode()).hexdigest()[:10]
        while rid in seen: rid = hashlib.sha1(rid.encode()).hexdigest()[:10]
        seen.add(rid)
        n = 2
        while any(r["sig"] == sig for r in out): sig = sig.split("#")[0] + f"#{n}"; n += 1
        out.append(dict(rid=rid, sig=sig, eq=_eq(f) if kind == "number" else None,
                        term=dict(old=term[0], new=term[1], where=term[2]) if term else None, rank=f.get("rank"), no=f.get("fid") or (str(f["rank"]) if f.get("rank") is not None else ""),
                        lim=lim, product=prod, kind=kind, lang=L, langs=langs, known=bool(f.get("known")),
                        odd=odd, sug=ACTIONS.get(f.get("suggested_action") or "", f.get("suggested_action") or ""), desc=f.get("description") or f.get("detail") or "",
                        twin=bool(twin), found=f.get("detected"), expl=f.get("explained_by") or [],
                        fix=[f.get("surface"), f.get("suggestion")] if f.get("surface") and f.get("suggestion") else None,
                        since=f.get("first_seen"), seen=f.get("seen_in"),
                        snip={k: highlight(_clip(s) if src.get(k) != "context" else s, k, V[k] or hot) for k, s in snip.items()},
                        src=src))
    order = {k: i for i, k in enumerate(KINDS)}
    out.sort(key=lambda r: (not r["known"], order.get(r["kind"], 9), r["rank"] if isinstance(r["rank"], int) else 10 ** 6, r["lim"] or "", r["lang"] or ""))
    return out


def data(path=AUDIT, results=RESULTS, hist=None):
    """-> dict(meta, rows) for the page, or None when there is no audit file."""
    if not path or not os.path.exists(path): return None
    A = json.load(open(path, encoding="utf-8"))
    F = A.get("findings", A if isinstance(A, list) else [])
    S = A.get("summary", {}) if isinstance(A, dict) else {}
    date = S.get("date") or re.sub(r"\D", "", os.path.basename(path))[:8]
    R = json.load(open(results, encoding="utf-8")) if results and os.path.exists(results) else {}
    rec = S.get("recall") or R.get("summary", {}).get("recall") or {}
    known_ids = sorted({f.get("id") for f in F if f.get("known")})
    meta = dict(date=date, file=os.path.relpath(path, core.ROOT), results=os.path.relpath(results, core.ROOT) if R else None,
                n_limitations=S.get("n_limitations") or R.get("summary", {}).get("n_limitations"),
                findings=R.get("findings", len(F)), limitations=R.get("limitations_found", S.get("limitations_with_finding")),
                known_found=R.get("known_found", rec.get("limitations")), known_of=rec.get("of"), known_ids=known_ids,
                known_rows=sum(1 for f in F if f.get("known")), total=len(F),
                by_kind={k: sum(1 for f in F if _kind(f) == k) for k in KINDS if any(_kind(f) == k for f in F)},
                precision=R.get("precision_pct"), ci=R.get("precision_wilson95"), real=R.get("real"),
                held=R.get("held_findings"), held_real=R.get("held_real"), model_calls=S.get("model_calls", 0),
                hist=bool(_hist_texts(hist, date, next(iter(known_ids), ""))))
    return dict(meta=meta, rows=rows(F, hist, date))
