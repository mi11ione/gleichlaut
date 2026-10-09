"""python3 -m gleichlaut.ui.build [--run fresh166 | --records R.jsonl --items I.json] [--out PATH] [--fragment]

One self-contained HTML review page (inline CSS/JS/data and embedded fonts; no request at view time; works from
file://): a register of German changes on the left and the case under review on the right (German change, FR/IT drafts
editable in place, checks ledger, decision). Diffs, number provenance and the plain-language guard findings are computed
here in Python from the same per-item views the emitters use (gleichlaut.emit.load); the header figures come from
score.score_run(run)["summary"]["all"] (counts only for --records). Reviewer decisions stay in the browser
(localStorage) and leave it only through Export XLIFF 2.1 / Export JSON / Copy decisions.
--fragment writes the page without <!doctype>/<html>/<head>/<body> (title + style + content + script) for publishing as
a claude.ai artifact; the default output is a complete standalone HTML document."""
import argparse, base64, difflib, html, json, os, re
from collections import Counter
from .. import core, score
from ..emit import explain, load

OUT = os.path.join(core.ROOT, "out", "ui", "index.html")
FONTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
TOK = re.compile(core.gl2.NUMRX.pattern + r"|\w+|\s+|[^\w\s]")        # numbers first: a number is one token
SENT_END = re.compile(r"[.;:!?](\s+)(?=[A-ZÄÖÜÀÂÉÈÊÎÔÛÇ0-9(«\"–-])")
WHOLE = 0.40          # a sentence block with more than this share of changed words is shown old-struck / new-underlined
LABEL = {"fresh166": "fresh 2025 held-out set", "m3_seed1": "fresh 2025 held-out set, seed 1", "oos242": "out-of-sample 2026 set",
         "dev120": "development set (in-sample)", "dev120_8b": "development set, 8B"}
GLUE = 2              # changed runs separated by at most this many unchanged words merge into one phrase


def _toks(s): return [(m.start(), m.group(0)) for m in TOK.finditer(s)]


def sentences(s):
    """-> [(start, end)] sentence spans covering s (the trailing space belongs to the sentence)."""
    out, a = [], 0
    for m in SENT_END.finditer(s):
        out.append((a, m.end(1))); a = m.end(1)
    if a < len(s) or not out: out.append((a, len(s)))
    return out


class _Segs:
    """Collects [kind, text(, who, slot)] segments; kind e(qual) | i(nserted) | d(eleted). Numbers of the new text whose
    start is in `chip` become their own segment carrying who placed them."""
    def __init__(self, new, nums):
        self.new, self.S = new, []
        self.chip = {s: (e, who, slot) for s, e, t, who, slot in nums}

    def put(self, kind, text):
        if not text: return
        if self.S and self.S[-1][0] == kind and len(self.S[-1]) == 2: self.S[-1][1] += text
        else: self.S.append([kind, text])

    def new_range(self, kind, a, b):
        """new[a:b] as kind (e or i), with number chips."""
        pos = a
        for s in sorted(k for k in self.chip if a <= k < b):
            e, who, slot = self.chip[s]
            self.put(kind, self.new[pos:s]); self.S.append([kind, self.new[s:e], who, slot]); pos = e
        self.put(kind, self.new[pos:b])


def _words(toks): return sum(1 for _, t in toks if re.match(r"\w", t))


def _changed(o, n):
    """Share of words (old + new) in changed runs of a word diff of o -> n."""
    A, B = _toks(o), _toks(n)
    ops = difflib.SequenceMatcher(None, [t for _, t in A], [t for _, t in B], autojunk=False).get_opcodes()
    return sum(_words(B[j1:j2]) + _words(A[i1:i2]) for op, i1, i2, j1, j2 in ops if op != "equal") / max(1, _words(A) + _words(B))


def _block(S, old, new, a0, a1, b0, b1):
    """A changed block old[a0:a1] -> new[b0:b1]: whole-sentence when most of it changed, else phrase-level."""
    A = [(s, t) for s, t in _toks(old[a0:a1])]; B = [(s, t) for s, t in _toks(new[b0:b1])]
    sm = difflib.SequenceMatcher(None, [t for _, t in A], [t for _, t in B], autojunk=False)
    ops = sm.get_opcodes()
    changed = sum(_words(B[j1:j2]) + _words(A[i1:i2]) for op, i1, i2, j1, j2 in ops if op != "equal")
    total = max(1, _words(A) + _words(B))
    if changed / total > WHOLE:
        o = old[a0:a1].rstrip()
        if o: S.S.append(["d", o, "s"])                           # whole old sentence(s), struck
        S.new_range("i", b0, b1)
        return
    groups, cur = [], None                                     # merge changed runs separated by <= GLUE words
    for k, (op, i1, i2, j1, j2) in enumerate(ops):
        if op == "equal":
            short = _words(A[i1:i2]) <= GLUE and 0 < k < len(ops) - 1
            if cur and short: cur[1], cur[3] = i2, j2; cur[4].append((i1, i2, j1, j2)); continue
            if cur: groups.append(cur); cur = None
            groups.append(("eq", i1, i2, j1, j2)); continue
        if cur: cur[1], cur[3] = i2, j2
        else: cur = [i1, i2, j1, j2, []]
    if cur: groups.append(cur)
    def off(T, i, base, text): return base + (T[i][0] if i < len(T) else len(text))
    for g in groups:
        if g[0] == "eq":
            _, i1, i2, j1, j2 = g; S.new_range("e", off(B, j1, b0, new[b0:b1]), off(B, j2, b0, new[b0:b1])); continue
        i1, i2, j1, j2, _ = g
        oa, ob = off(A, i1, a0, old[a0:a1]), off(A, i2, a0, old[a0:a1])
        na, nb = off(B, j1, b0, new[b0:b1]), off(B, j2, b0, new[b0:b1])
        d, n = old[oa:ob], new[na:nb]
        if d.strip() == "" and n.strip() == "": S.new_range("e", na, nb); continue
        lead = len(n) - len(n.lstrip()) if d.strip() else 0       # keep a shared leading space outside the marks
        if d.strip(): S.put("d", d.strip())
        if d.strip() and n[:lead]: S.new_range("e", na, na + lead)
        S.new_range("i", na + lead, nb)


def diff(old, new, nums=()):
    """-> [[kind, text, (who, slot) | ("s",)]]: sentence-aligned, phrase-level diff. Unchanged sentences are kept;
    changed sentence blocks are shown word-phrase by phrase, or as old sentence struck + new sentence underlined when
    more than WHOLE of their words changed. A 3-element d segment ["d", text, "s"] marks a whole struck sentence."""
    S = _Segs(new, nums)
    A, B = sentences(old), sentences(new)
    key = lambda s, sp: re.sub(r"\s+", " ", s[sp[0]:sp[1]]).strip()
    sm = difflib.SequenceMatcher(None, [key(old, x) for x in A], [key(new, x) for x in B], autojunk=False)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        a0 = A[i1][0] if i1 < len(A) else len(old); a1 = A[i2 - 1][1] if i2 > i1 else a0
        b0 = B[j1][0] if j1 < len(B) else len(new); b1 = B[j2 - 1][1] if j2 > j1 else b0
        if op == "equal": S.new_range("e", b0, b1)
        elif op == "delete": S.S.append(["d", old[a0:a1].rstrip(), "s"])
        elif op == "insert": S.new_range("i", b0, b1)
        else: _replace(S, old, new, A[i1:i2], B[j1:j2])
    return S.S


def _ratio(a, b):
    return difflib.SequenceMatcher(None, [t for _, t in _toks(a)], [t for _, t in _toks(b)], autojunk=False).ratio()


def _replace(S, old, new, As, Bs):
    """Changed run of sentences: pair each new sentence with the most similar remaining old one (in order, ratio >= .5)
    and diff the pair; unpaired old sentences are struck, unpaired new ones underlined."""
    i = 0
    for b0, b1 in Bs:
        best, bi = 0.0, None
        for k in range(i, len(As)):
            r = _ratio(old[As[k][0]:As[k][1]], new[b0:b1])
            if r > best: best, bi = r, k
        if bi is None or best < 0.5:
            S.new_range("i", b0, b1); continue
        if bi > i and _changed(old[As[i][0]:As[bi][1]], new[b0:b1]) <= WHOLE:      # unpaired old sentences join the pair
            _block(S, old, new, As[i][0], As[bi][1], b0, b1); i = bi + 1; continue
        for a0, a1 in As[i:bi]: S.S.append(["d", old[a0:a1].rstrip(), "s"])
        _block(S, old, new, As[bi][0], As[bi][1], b0, b1); i = bi + 1
    for a0, a1 in As[i:]: S.S.append(["d", old[a0:a1].rstrip(), "s"])


def summary(segs, n=110):
    """One-line description of the first change of a diff: 'old → new', '+ new' or '− old'."""
    d, i, started = "", "", False
    for s in segs:
        if s[0] == "e":
            if started and (d or i) and s[1].strip(): break
            continue
        started = True
        if s[0] == "d": d += (" " if d else "") + s[1]
        else: i += s[1]
    d, i = re.sub(r"\s+", " ", d).strip(), re.sub(r"\s+", " ", i).strip()
    t = f"{d} → {i}" if d and i else f"+ {i}" if i else f"− {d}" if d else "(no textual change)"
    return t if len(t) <= n else t[:n].rsplit(" ", 1)[0] + " …"


def _date(s):
    return f"{s[6:8]}.{s[4:6]}.{s[:4]}" if re.fullmatch(r"\d{8}", s or "") else (s or "?")


def _ledger(v):
    """Checks ledger rows for one draft: [gid, name, state, finding sentences, raw detail, g-id label]."""
    L = v["lang"]; by = {}
    for f in v["findings"]:
        if f["gid"] != "corr": by.setdefault("slot" if f["gid"] == "unknown" else f["gid"], []).append(f)
    rows = []
    for gid, lab, state, detail in v["lights"]:
        fs = by.get(gid, [])
        txt = [dict(t=f["text"], c=f["corrects"]) for f in fs]
        if gid == "reask": txt = [dict(t=explain.reask_text(v), c=False)]
        rows.append([gid, explain.name(gid, L), state, txt, detail if state == "fail" else "", lab])
    return rows


def data(run="fresh166", records=None, items=None):
    meta, views = load(run, records, items)
    if meta["custom"]:
        from ..emit import _read_items
        summ = None; I = {x["key"]: x for x in _read_items(meta["items_path"])} if meta["has_tgt_new"] else {}
    else:
        summ = score.score_run(run)["summary"]; I = {}
    groups = {}
    for v in views:
        g = groups.setdefault(v["pair"], dict(pair=v["pair"], product=v["product"], code=v["cud_id"], snap_old=_date(v["snap_old"]),
                                              snap_new=_date(v["snap_new"]), family=v["family"], de=diff(v["de_old"], v["de_new"]), items={}))
        g["sum"] = summary(g["de"])
        corr = next((f for f in v["findings"] if f["gid"] == "corr"), None)
        it = dict(key=v["key"], lang=v["lang"], status=v["status"], rule_only=v["rule_only"], cud=v["cud_id"],
                  banner=v.get("banner"), corr=corr["text"] if corr else None, corr_note=explain.corr_note(v["lang"]) if corr else None,
                  findings=[[f["gname"], f["text"], f["corrects"]] for f in v["findings"] if f["gid"] != "corr"])
        if v["status"] == "human":
            r = v.get("change_ratio")
            it.update(segs=[["e", v["tgt_old"]]], ledger=[], ratio=(round(100 * float(r)) if r not in (None, "") else None),
                      reason=v.get("reason") or "")
        else:
            it.update(segs=diff(v["tgt_old"], v["draft"], v["numbers"]), ledger=_ledger(v),
                      model_numbers=sum(n[3] == "model" for n in v["numbers"]))
            if I: it["exact"] = core.lock.norm(v["draft"]) == core.lock.norm(I[v["key"]].get("tgt_new", ""))
        g["items"][v["lang"]] = it
    fam = Counter(v["family"] for v in views)
    counts = dict(items=len(views), changes=len(groups), ready=sum(v["status"] == "ready" for v in views),
                  flagged=sum(v["status"] == "flagged" for v in views), human=sum(v["status"] == "human" for v in views),
                  divergent=sum(bool(v.get("banner")) or any(f["gid"] == "corr" for f in v["findings"]) for v in views),
                  code_numbers=sum(n[3] == "code" for v in views for n in v["numbers"]),
                  model_numbers=sum(n[3] == "model" for v in views for n in v["numbers"]))
    if I: counts["exact"] = sum(1 for g in groups.values() for it in g["items"].values() if it.get("exact"))
    m = {k: meta[k] for k in ("run", "what", "stack", "model", "pipeline", "items_sha256", "run_sha256", "custom", "has_tgt_new")}
    m["label"] = LABEL.get(meta["run"], meta["what"]) if not meta["custom"] else "records " + meta["run"]
    return dict(meta=m, all=summ["all"] if summ else None, groups=list(groups.values()),
                families=sorted(fam.items(), key=lambda kv: (-kv[1], kv[0])), counts=counts)


def fonts_css():
    """@font-face rules with the vendored woff2 files inlined (base64), real fallback stacks in the CSS below."""
    rules = []
    for fam, fn, w in (("Source Sans 3", "SourceSans3-latin-wght.woff2", "400 600"), ("IBM Plex Mono", "IBMPlexMono-400-latin.woff2", "400"),
                       ("IBM Plex Mono", "IBMPlexMono-500-latin.woff2", "500")):
        p = os.path.join(FONTS, fn)
        if not os.path.exists(p): continue
        b64 = base64.b64encode(open(p, "rb").read()).decode()
        rules.append(f"@font-face{{font-family:'{fam}';font-style:normal;font-weight:{w};font-display:swap;"
                     f"src:url(data:font/woff2;base64,{b64}) format('woff2')}}")
    return "\n".join(rules)


def build(run="fresh166", out=OUT, records=None, items=None, fragment=False):
    D = data(run, records, items)
    blob = json.dumps(D, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    body = BODY.replace("__DATA__", blob)
    head = HEAD.replace("__FONTS__", fonts_css())
    page = (head + body) if fragment else ("<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
           "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n" + head + "</head>\n<body>\n" + body + "</body>\n</html>\n")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f: f.write(page)
    return out, D


from .page import HEAD, BODY          # noqa: E402  (the template lives in page.py)


def main(argv=None):
    ap = argparse.ArgumentParser(description="build the static translator review page")
    ap.add_argument("--run", default="fresh166"); ap.add_argument("--out", default=OUT)
    ap.add_argument("--records", help="records JSONL (gleichlaut month / draft) instead of a recorded run; needs --items")
    ap.add_argument("--items", help="items file for --records")
    ap.add_argument("--fragment", action="store_true", help="no doctype/html/head/body (for a claude.ai artifact)")
    a = ap.parse_args(argv)
    p, D = build(a.run, a.out, a.records, a.items, a.fragment)
    c = D["counts"]
    print(f"ui: {c['items']} drafts in {c['changes']} German changes ({c['ready']} ready, {c['flagged']} flagged"
          + (f", {c['human']} routed to a translator" if c["human"] else "") + f") -> {p} ({os.path.getsize(p) // 1024} KB)")


if __name__ == "__main__":
    main()
