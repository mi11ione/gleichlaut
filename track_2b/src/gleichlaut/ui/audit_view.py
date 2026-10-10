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
             term and where BAG already corrected it (explain.term_parts).
  what       per issue, the list line: for a number finding with values on one side only, the other side shows the value it
             writes at that place (the audit's display-only 'counterpart', round 5; else counterpart() from the snippets:
             Nemluvio 'DE 8 · IT 4'), '—' when there is none.
  exp        the round-5 findings (operator, negation, number word; findings_r5, every kind off by default) that both blind
             annotators confirmed (eval/labels/audit_r15_<date>.tsv): a separate read-only group, outside the headline."""
import hashlib, json, os, re
from .. import core

AUDIT = os.path.join(core.ROOT, "data", "audit", "audit_20261006.json")
RESULTS = os.path.join(core.ROOT, "eval", "results", "audit.json")
MORE = os.path.join(core.ROOT, "eval", "results", "audit_more.json")        # terminology findings and their blind check
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
    return _render(plain, lang, hot, marks)


def _render(plain, lang, hot, marks):
    """plain text + [(start, end, 2)] spans -> [[text, 0|1|2]] (numbers outside the spans: 2 when in `hot`, else 1)."""
    marks = list(marks)
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


def _ctxs(f, kind, L):
    """[(lang, context)] of a finding: the '[x]' contexts the audit wrote, in the language they quote."""
    out = []
    for x in f.get("de_only") or []: out += [("de", c) for c in (x.get("context") or [])[:1]]
    for x in f.get("tgt_only") or []: out += [(L, c) for c in (x.get("context") or [])[:1]]
    top = f.get("context")
    if kind in ("editorial", "terminology", "unit") and L in LANGS and isinstance(top, (list, tuple)) and top and isinstance(top[0], str):
        out.append((L, top[0]))
    return [(k, c) for k, c in out if isinstance(c, str) and "[" in c]


def _passage(c):
    return re.sub(r"\s+", " ", re.sub(r"[…\[\]]", "", c)).strip().lower()


def conflict_key(f, kind, L, V, term=None):
    """What a finding says is different, independent of the limitation (and, for number and unit findings, of the
    target language): two findings with the same key on sibling texts are the same issue."""
    if kind == "number":
        tgt = sorted(set(V.get("fr", ())) | set(V.get("it", ()))) if not (f.get("de_only") or f.get("tgt_only")) else \
            sorted({_canon(x.get("value")) for x in f.get("tgt_only") or []})
        de = sorted(V.get("de", ())) if not (f.get("de_only") or f.get("tgt_only")) else sorted({_canon(x.get("value")) for x in f.get("de_only") or []})
        return ("number", tuple(de), tuple(tgt))
    if kind == "unit": return ("unit", str(f.get("value") or ""), str(f.get("de_unit") or ""), str(f.get("tgt_unit") or ""))
    if kind == "language": return ("language", L or "", str(f.get("detected") or f.get("found") or ""))
    if kind == "editorial": return ("editorial", L or "", str(f.get("surface") or ""), str(f.get("suggestion") or ""))
    if kind == "terminology":
        o = f.get("old_phrase") or (term[0] if term else "") or ""; n = f.get("new_phrase") or (term[1] if term else "") or ""
        return ("terminology", L or "", _passage(o), _passage(n))
    return (kind, L or "", re.sub(r"\s+", " ", str(f.get("description") or ""))[:120])


def dating(first, seen, snaps):
    """What the audit's dating says about one finding (audit.date_findings: first_seen = the first of the usable snapshots
    of the year in which it is present, seen_in = in how many it is present): first, prev (the snapshot before first,
    where it was absent; None when first is the earliest snapshot checked), n (present in n snapshots) of m (snapshots
    from first on), earliest (first is the earliest snapshot checked)."""
    if not first: return None
    snaps = sorted(snaps or [])
    if first not in snaps: return dict(first=first, prev=None, n=seen, m=None, earliest=False)
    i = snaps.index(first)
    return dict(first=first, prev=snaps[i - 1] if i > 0 else None, n=seen, m=len(snaps) - i, earliest=i == 0)


def rows(F, hist=None, date="20261006", snaps=None):
    by = {}
    for f in F: by.setdefault((f.get("id"), f.get("lang")), []).append(f)
    out, seen = [], set()
    for fi, f in enumerate(F):
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
        brands = [str(x).split()[0].lower() for x in (f.get("product") if isinstance(f.get("product"), (list, tuple)) else [prod]) if str(x).strip()]
        anchors = {"lim:" + str(lim)} | {"brand:" + b for b in brands} | {"ctx:" + _passage(c) for _, c in _ctxs(f, kind, L)}
        out.append(dict(rid=rid, sig=sig, eq=_eq(f) if kind == "number" else None, fid=f.get("fid") or "", fi=fi,
                        vals={k: sorted(v) for k, v in V.items() if v}, gk=list(conflict_key(f, kind, L, V, term)), anchors=sorted(anchors),
                        dating=dating(f.get("first_seen"), f.get("seen_in"), snaps),
                        term=dict(old=term[0], new=term[1], where=term[2]) if term else None, rank=f.get("rank"), no=f.get("fid") or (str(f["rank"]) if f.get("rank") is not None else ""),
                        lim=lim, product=prod, kind=kind, lang=L, langs=langs, known=bool(f.get("known")),
                        odd=odd, sug=ACTIONS.get(f.get("suggested_action") or "", f.get("suggested_action") or ""), desc=f.get("description") or f.get("detail") or "",
                        twin=bool(twin), found=f.get("detected"), expl=f.get("explained_by") or [],
                        fix=[f.get("surface"), f.get("suggestion")] if f.get("surface") and f.get("suggestion") else None,
                        since=f.get("first_seen"), seen=f.get("seen_in"),
                        cp={k: [_canon(x.get("value")) for x in v] for k, v in f["counterpart"].items()} if isinstance(f.get("counterpart"), dict) else None,
                        snip={k: highlight(_clip(s) if src.get(k) != "context" else s, k, V[k] or hot) for k, s in snip.items()},
                        src=src))
    order = {k: i for i, k in enumerate(KINDS)}
    out.sort(key=lambda r: (not r["known"], order.get(r["kind"], 9), r["rank"] if isinstance(r["rank"], int) else 10 ** 6, r["lim"] or "", r["lang"] or ""))
    return out


GROUPING = ("Findings are one issue when they name the same difference (same kind and same conflicting values: the German "
            "and target values of a number, the unit, the detected language, the typo and its correction, the old and new "
            "term) on the same text: the same limitation, a sibling limitation of the same product, or the same quoted "
            "passage; a typo that the audit says explains a number difference joins that difference; a terminology "
            "notice is one issue per language and term pair, wherever the old term still stands.")


# unit words of the three languages by what they measure, so that "acht Wochen" and "quattro settimane" are compared
_UNIT_KIND = (("day", r"tag|täg|jour|giorn"), ("week", r"woche|wöch|semaine|settiman"), ("month", r"monat|mois|mes[ei]"),
              ("year", r"jahr|jähr|\ban(?:s|née)|ann[oi]"))


def _unit_of(seg, lang):
    """'acht Wochen' -> 'week', '30 mg' -> 'mg', '16' -> '' (the unit after the number of a highlighted segment)."""
    m = _num_rx(lang).match(seg.strip())
    rest = seg.strip()[m.end():].strip(" -.").lower() if m else ""
    if not rest: return ""
    return next((k for k, rx in _UNIT_KIND if re.match(rx, rest)), rest)


def counterpart(r, L, other):
    """The value language L writes where the finding's values of language `other` stand, when the audit names none for L
    (a number finding of the kind 'DE has 8 (Wochen), IT does not') and the finding carries no counterpart of its own
    (the audit's display-only 'counterpart' field, round 5, is used when present): the one number with the same unit in L's passage
    (the row's snippet aligned with the German context) that the other language's passage does not also have. None when
    there is no such number or more than one: the list then shows '—' (L has no counterpart at that place)."""
    S = r.get("snip") or {}
    if not S.get(L) or not S.get(other): return None
    hot = [(x[0], _unit_of(x[0], other)) for x in S[other] if x[1] == 2]
    units = {u for _, u in hot if u}
    if not units: return None
    def val(seg, lang):
        v = _values_in(seg.strip(), lang); return v[0][1] if v else None
    there = {val(x[0], other) for x in S[other] if x[1]}
    cand = {val(x[0], L) for x in S[L] if x[1] and _unit_of(x[0], L) in units} - there - {None}
    return next(iter(cand)) if len(cand) == 1 else None


def issues(R):
    """Group the rows of one audit into issues (GROUPING): -> [dict(iid, key, rows=[row indexes], ...)] in row order.
    Deterministic: depends only on the findings, not on any decision or on the order of the input."""
    up = list(range(len(R)))
    def root(i):
        while up[i] != i: up[i] = up[up[i]]; i = up[i]
        return i
    def join(i, j):
        a, b = root(i), root(j)
        if a != b: up[max(a, b)] = min(a, b)
    for i, r in enumerate(R):
        for j in range(i + 1, len(R)):
            q = R[j]
            if r["gk"] != q["gk"]: continue
            if r["kind"] == "terminology" or set(r["anchors"]) & set(q["anchors"]): join(i, j)
        for j, q in enumerate(R):
            if q["lim"] == r["lim"] and q["fid"] and (q["fid"] in r["expl"] or r["fid"] in q["expl"]): join(i, j)
    G = {}
    for i in range(len(R)): G.setdefault(root(i), []).append(i)
    out = []
    for n, (_, ix) in enumerate(sorted(G.items(), key=lambda kv: kv[1][0])):
        M = [R[i] for i in ix]
        uniq = lambda xs: list(dict.fromkeys(x for x in xs if x))
        odd = uniq(r["odd"] for r in M)
        langs = [L for L in LANGS if any(r["lang"] == L for r in M)]
        vals = {L: sorted(set().union(*[set(r["vals"].get(L, ())) for r in M])) for L in LANGS}
        dt = [r["dating"] for r in M if r["dating"]]
        what = []
        for r in M:
            k, L, f = r["kind"], r["lang"], r
            if k == "number":
                de, tg = " ".join(r["vals"].get("de", [])), " ".join(r["vals"].get(L, []))
                cp = r.get("cp")             # the audit's own counterpart (round 5, from the full texts), else from the snippets
                if de and not tg: tg = " ".join(cp.get(L, [])) if cp is not None else counterpart(r, L, "de") or ""
                elif tg and not de: de = " ".join(cp.get("de", [])) if cp is not None else counterpart(r, "de", L) or ""
                w = [k, L, de or "—", tg or "—"]
            elif k == "editorial" and r["fix"]: w = [k, L, r["fix"][0], r["fix"][1]]
            elif k == "terminology" and r["term"]: w = [k, L, r["term"]["old"] or "", r["term"]["new"] or ""]
            elif k == "language": w = [k, L, str(r["found"] or ""), ""]
            else: w = [k, L, r["desc"], ""]
            if w not in what: what.append(w)
        out.append(dict(iid=f"{n + 1:02d}", key=hashlib.sha1("\n".join(sorted(r["sig"] for r in M)).encode()).hexdigest()[:10],
                        rows=ix, fids=[r["no"] or r["fid"] for r in M], lims=uniq(r["lim"] for r in M),
                        products=uniq(r["product"] for r in M), kinds=uniq(r["kind"] for r in M), langs=langs,
                        known=any(r["known"] for r in M), eq=all(r["eq"] is not None for r in M) and not any(r["known"] for r in M),
                        term=all(r["kind"] == "terminology" for r in M), odd=odd[0] if len(odd) == 1 else "unclear",
                        vals={L: v for L, v in vals.items() if v}, what=what, dating=min(dt, key=lambda d: d["first"]) if dt else None))
    return out


def _locate(full, c):
    """(start, end) in `full` of the '[x]' part of an audit context, or None when the context is not found verbatim."""
    s = c.strip().strip("…").strip()
    i = s.find("["); j = s.find("]", i)
    if i < 0 or j < 0: return None
    plain = s[:i] + s[i + 1:j] + s[j + 1:]
    at = full.find(plain)
    if at < 0: return None
    return (at + i, at + j - 1)


def full_texts(F, R, hist=None, date="20261006"):
    """{limitation: {lang: [[text, 0|1|2]]}}: the full DE/FR/IT texts of every limitation with a finding (snapshot files,
    else data/audit/audit_texts_<date>.json), the passages the findings quote and their conflicting values marked 2 as in
    the excerpts, other numbers 1."""
    out = {}
    for lim in dict.fromkeys(r["lim"] for r in R):
        full = _hist_texts(hist, date, lim)
        if not full: continue
        spans = {L: [] for L in LANGS}; hot = set()
        for r in R:
            f = F[r["fi"]]
            if f.get("id") != lim: continue
            if r["kind"] == "number": hot |= set().union(*[set(v) for v in r["vals"].values()])
            if r["kind"] == "editorial" and isinstance(f.get("values"), (list, tuple)) and f["values"]: hot.add(_canon(f["values"][0]))
            for L, c in _ctxs(f, r["kind"], r["lang"]):
                sp = _locate(full.get(L, ""), c) if L in full else None
                if sp: spans[L].append(sp)
            dt = f.get("de_term")
            if r["kind"] == "terminology" and isinstance(dt, str) and dt and "de" in full:
                k = full["de"].lower().find(dt.lower())
                if k >= 0: spans["de"].append((k, k + len(dt)))
        # a quoted passage is marked where the finding quotes it; in a language without one (the third language of a
        # number finding), the conflicting values are marked as in the excerpts
        out[lim] = {L: _render(full[L], L, set() if spans[L] else hot, [(a, b, 2) for a, b in sorted(set(spans[L]))]) for L in LANGS if full.get(L)}
    return out


R15_LABELS = os.path.join(core.ROOT, "eval", "labels", "audit_r15_{date}.tsv")
CONFIRMED = ("real", "minor")


def _mark(s, words):
    """A sentence with the given words in '[...]' (for highlight): the negation words of a negation finding."""
    for w in sorted({w for w in words if w}, key=len, reverse=True):
        tail = "" if w[-1] in "’'" else r"(?![\w\]])"                  # an elided n’ / l’ is followed by a letter
        s = re.sub(r"(?<![\w\[])" + re.escape(w) + tail, "[" + w + "]", s, count=1)
    return s


def experimental(A, date, labels=None):
    """Round-5 findings (operator, negation, number word: findings_r5, PREREG R15) that both blind annotators confirmed
    (final label real or minor in eval/labels/audit_r15_<date>.tsv). Every round-5 kind ships off (summary.round5.on): they
    are shown apart, read-only, and never counted in the headline or the issues. None without round-5 findings or labels.
    Each row: fid, lim, product, kind, lang, label, what [kind, lang, DE, target] and the excerpts (DE, target) with the
    finding's words highlighted."""
    F5 = A.get("findings_r5") if isinstance(A, dict) else None
    p = labels or R15_LABELS.format(date=date)
    if not F5 or not os.path.exists(p): return None
    lines = open(p, encoding="utf-8").read().splitlines(); hdr = lines[0].split("\t")
    lab = {c["fid"]: c for c in (dict(zip(hdr, l.split("\t"))) for l in lines[1:] if l.strip())}
    out = []
    for f in F5:
        L, k, fl = f.get("lang"), f.get("kind"), (lab.get(f.get("fid")) or {}).get("final")
        if fl not in CONFIRMED: continue
        ctx = [c for c in (f.get("context") or []) if isinstance(c, str)]
        if k == "operator":
            what = [k, L, f"{f.get('de_op')} {f.get('value')}", f"{f.get('tgt_op')} {f.get('value')}"]; de, tg = (ctx + ["", ""])[:2]
        elif k == "negation":
            neg = " ".join(f.get("negations") or []); de, tg = (ctx + ["", ""])[:2]
            what = [k, L, neg, "—"] if f.get("side") == "de" else [k, L, "—", neg]
            if f.get("side") == "de": de = _mark(de, f.get("negations") or [])
            else: tg = _mark(tg, f.get("negations") or [])
        else:
            dv = " ".join(str(x.get("value")) for x in f.get("de_only") or []); tv = " ".join(str(x.get("value")) for x in f.get("tgt_only") or [])
            what = [k, L, dv or "—", tv or "—"]
            de = next((c for x in f.get("de_only") or [] for c in x.get("context") or []), "")
            tg = next((c for x in f.get("tgt_only") or [] for c in x.get("context") or []), "")
        prod = f.get("product"); prod = ", ".join(prod) if isinstance(prod, (list, tuple)) else (prod or "")
        out.append(dict(fid=f.get("fid"), lim=f.get("id"), product=prod, kind=k, lang=L, label=fl, what=what, desc=f.get("description") or "",
                        snip={"de": highlight(de, "de", set()) if de else None, L: highlight(tg, L, set()) if tg else None}))
    S = A.get("summary", {}).get("round5") or {}
    return dict(n=len(F5), confirmed=len(out), on=S.get("on") or {}, labels=os.path.relpath(p, core.ROOT), rows=out)


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
    snaps = S.get("snapshots_dated") or sorted({f.get("first_seen") for f in F if f.get("first_seen")})
    meta = dict(date=date, snapshots=snaps, grouping=GROUPING, file=os.path.relpath(path, core.ROOT), results=os.path.relpath(results, core.ROOT) if R else None,
                n_limitations=S.get("n_limitations") or R.get("summary", {}).get("n_limitations"),
                findings=R.get("findings", len(F)), limitations=R.get("limitations_found", S.get("limitations_with_finding")),
                known_found=R.get("known_found", rec.get("limitations")), known_of=rec.get("of"), known_ids=known_ids,
                known_rows=sum(1 for f in F if f.get("known")), total=len(F),
                by_kind={k: sum(1 for f in F if _kind(f) == k) for k in KINDS if any(_kind(f) == k for f in F)},
                precision=R.get("precision_pct"), ci=R.get("precision_wilson95"), real=R.get("real"),
                held=R.get("held_findings"), held_real=R.get("held_real"), model_calls=S.get("model_calls", 0),
                hist=bool(_hist_texts(hist, date, next(iter(known_ids), ""))))
    # The headline as the README states it: findings of every kind except terminology (number, unit, language, editorial;
    # eval/results/audit.json v2) and, counted separately, terminology notices (eval/results/audit_more.json), each with
    # how many a blind annotator confirmed. The results files are used only when they describe this audit file (same
    # counts); otherwise the counts come from the rows and no confirmation figure is shown.
    nterm = sum(1 for f in F if _kind(f) == "terminology"); nmain = len(F) - nterm
    V2 = R.get("v2") or {}
    TM = (json.load(open(MORE, encoding="utf-8")).get("terminology") or {}) if results == RESULTS and os.path.exists(MORE) else {}
    same = V2.get("findings_all_kinds") == nmain
    meta.update(main=V2["findings_all_kinds"] if same else nmain, main_real=V2.get("real_all_kinds") if same else None,
                main_new_real=V2.get("real_new_beyond_known") if same else None,
                term=TM["findings"] if TM.get("findings") == nterm else nterm, term_real=TM.get("real") if TM.get("findings") == nterm else None,
                more=os.path.relpath(MORE, core.ROOT) if TM else None)
    R = rows(F, hist, date, snaps)
    I = issues(R)
    meta.update(issues=len(I))
    return dict(meta=meta, rows=R, issues=I, texts=full_texts(F, R, hist, date), exp=experimental(A, date))
