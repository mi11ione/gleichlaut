"""Gleichschritt lock + slot guard + code lane. Pure stdlib (runs on the Air inside the model loop and locally for scoring).
Window: each DE edit span (DE_old token range) is projected onto the target via monotone anchors shared by DE_old and
target_old (numbers, identical tokens unique in both, ; and :), interpolated by position, padded by a fixed margin.
Margin was fixed before any model output was seen: max(3, 15% of the anchor gap)."""
import re, difflib, math
from collections import Counter

TOK = re.compile(r"\d+(?:[.,'’]\d+)*|\w+|[^\w\s]")


def tok(s): return TOK.findall(s)


def tok_spans(s):
    return [(m.group(0), m.start(), m.end()) for m in TOK.finditer(s)]


def norm(s):
    s = s.replace(" ", " ").replace(" ", " ").replace("’", "'").replace("­", "")
    return re.sub(r"\s+", " ", s).strip()


def de_ops(de_old, de_new):
    a, b = tok(de_old), tok(de_new)
    return a, b, [o for o in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes() if o[0] != "equal"]


def anchors(a, t):
    """monotone (i, j) pairs: DE_old token i == target_old token j for anchor-eligible tokens."""
    ca, ct = Counter(a), Counter(t)
    def key(x, cnt_self, cnt_other):
        if re.search(r"\d", x): return x
        if x in (";", ":", "(", ")") and ca[x] == ct[x]: return x
        if len(x) >= 2 and cnt_self[x] == 1 and cnt_other[x] == 1: return x
        return None
    ka = [key(x, ca, ct) or f"\0a{i}" for i, x in enumerate(a)]
    kt = [key(x, ct, ca) or f"\0t{j}" for j, x in enumerate(t)]
    sm = difflib.SequenceMatcher(None, ka, kt, autojunk=False)
    pairs = [(-1, -1)]
    for m in sm.get_matching_blocks():
        for k in range(m.size): pairs.append((m.a + k, m.b + k))
    pairs.append((len(a), len(t)))
    return sorted(set(pairs))


def windows(de_old, de_new, tgt_old):
    """list of allowed target-token ranges [lo, hi) (insertions allowed at positions lo..hi)."""
    a, b, ops = de_ops(de_old, de_new)
    t = tok(tgt_old)
    P = anchors(a, t)
    W = []
    for op, i1, i2, j1, j2 in ops:
        left = max((p for p in P if p[0] < i1), key=lambda p: p[0])
        right = min((p for p in P if p[0] >= i2), key=lambda p: p[0])
        il, jl = left; ir, jr = right
        gap_i, gap_j = max(1, ir - il), max(0, jr - jl)
        s = jl + (i1 - il) * gap_j / gap_i
        e = jl + (i2 - il) * gap_j / gap_i
        m = max(3, math.ceil(0.15 * gap_j))
        lo = max(jl + 1, math.floor(s - m)); hi = min(jr, math.ceil(e + m))
        # anchors themselves that are part of the DE edit (e.g. a changed number) must be editable
        for (pi, pj) in P:
            if i1 <= pi < i2 and 0 <= pj < len(t): lo, hi = min(lo, pj), max(hi, pj + 1)
        W.append((max(0, lo), min(len(t), max(hi, lo))))
    return W, t


def tgt_edits(tgt_old, out):
    t, o = tok(tgt_old), tok(out)
    return t, o, [x for x in difflib.SequenceMatcher(None, t, o, autojunk=False).get_opcodes() if x[0] != "equal"]


def check(de_old, de_new, tgt_old, out):
    """-> dict(ok, outside_chars, outside_spans)"""
    W, t = windows(de_old, de_new, tgt_old)
    _, o, E = tgt_edits(tgt_old, out)
    bad, chars = [], 0
    for op, j1, j2, k1, k2 in E:
        if op == "insert":
            inside = any(lo <= j1 <= hi for lo, hi in W)
        else:
            inside = any(lo <= j1 and j2 <= hi for lo, hi in W)
        if not inside:
            old_s, new_s = " ".join(t[j1:j2]), " ".join(o[k1:k2])
            chars += max(len(old_s), len(new_s)); bad.append((old_s, new_s))
    return dict(ok=not bad, outside_chars=chars, outside=bad[:6], n_windows=len(W))


# ------------------------------------------------------------------ slot lexicons (per language)
NEG = {"de": r"\bnicht\b|\bkein\w*|\bweder\b|\bnie\b|\bniemand\w*|\bnichts\b",
       "fr": r"\bne\b|\bn'|\bpas\b|\baucun\w*|\bni\b|\bjamais\b|\bnul\w*\b|\bpersonne\b|\brien\b",
       "it": r"\bnon\b|\bné\b|\bnessun\w*|\bmai\b|\bnulla\b|\bniente\b",
       "rm": r"\bbetg\b|\bnagin\w*|\bni\b|\bmai\b|\bnagut\b|\bnagin\b|\bna\b"}
MODAL = {"de": {"MAY": r"\bkann\b|\bkönnen\b|\bdarf\b|\bdürfen\b", "MUST": r"\bmuss\b|\bmüssen\b|\bhat\b[^.;]*\bzu\b\w*", "SHALL": r"\bsoll\b|\bsollen\b"},
         "fr": {"MAY": r"\bpeut\b|\bpeuvent\b|\bpourra\w*", "MUST": r"\bdoit\b|\bdoivent\b|\bdevra\w*|\best tenu\w*|\bsont tenu\w*", "SHALL": r"\bdevrait\b|\bdevraient\b"},
         "it": {"MAY": r"\bpuò\b|\bpossono\b|\bpotrà\b|\bpotranno\b", "MUST": r"\bdeve\b|\bdevono\b|\bdovrà\b|\bdovranno\b|\bè tenut\w*|\bsono tenut\w*", "SHALL": r"\bdovrebbe\w*"},
         "rm": {"MAY": r"\bpo\b|\bpon\b|\bpudair\b|\bpoda\b|\bpodan\b", "MUST": r"\bsto\b|\bston\b|\bstuair\b|\bstoppa\b|\bè obligà\w*|\bèn obligà\w*", "SHALL": r"\bduai\b|\bduain\b|\bduess\w*"}}
NUM = re.compile(r"\d+(?:[ '’  ]\d{3})*(?:[.,]\d+)*")


def nums(s):
    return Counter(re.sub(r"[ '’  ]", "", m.group(0)) for m in NUM.finditer(s))


def slots(s, lang):
    s2 = s.lower().replace("’", "'")
    return dict(neg=len(re.findall(NEG[lang], s2)),
                modal={k: len(re.findall(v, s2)) for k, v in MODAL[lang].items()},
                nums=nums(s))


def slot_diff(a, b):
    """differences between two slot dicts (b relative to a)."""
    d = []
    if a["neg"] != b["neg"]: d.append(f"neg {a['neg']}->{b['neg']}")
    for k in a["modal"]:
        if a["modal"][k] != b["modal"][k]: d.append(f"modal:{k} {a['modal'][k]}->{b['modal'][k]}")
    if a["nums"] != b["nums"]:
        d.append(f"nums -{dict(a['nums'] - b['nums'])} +{dict(b['nums'] - a['nums'])}")
    return d


def guard(de_old, de_new, tgt_old, out, lang):
    """runtime slot guard: the slot change DE_old->DE_new must be mirrored by tgt_old->out (neg count delta, modal deltas, numbers added/removed)."""
    so, sn, to, tn = slots(de_old, "de"), slots(de_new, "de"), slots(tgt_old, lang), slots(out, lang)
    bad = []
    if (sn["neg"] - so["neg"]) != (tn["neg"] - to["neg"]): bad.append("neg")
    for k in so["modal"]:
        if (sn["modal"][k] - so["modal"][k]) != (tn["modal"][k] - to["modal"][k]): bad.append("modal:" + k)
    if (sn["nums"] - so["nums"]) != (tn["nums"] - to["nums"]) or (so["nums"] - sn["nums"]) != (to["nums"] - tn["nums"]): bad.append("nums")
    return bad


# ------------------------------------------------------------------ code lane
MONTHS = {"de": "Januar Februar März April Mai Juni Juli August September Oktober November Dezember".split(),
          "fr": "janvier février mars avril mai juin juillet août septembre octobre novembre décembre".split(),
          "it": "gennaio febbraio marzo aprile maggio giugno luglio agosto settembre ottobre novembre dicembre".split(),
          "rm": "schaner favrer mars avrigl matg zercladur fanadur avust settember october november december".split()}
ISNUM = re.compile(r"^\d+(?:[.,'’]\d+)*$")


def code_lane(de_old, de_new, tgt_old, lang):
    """numbers / dates (month names) / SR- and article-number changes by rule. Returns (applicable, output or None)."""
    a, b, ops = de_ops(de_old, de_new)
    if not ops: return False, None
    subs = []
    for op, i1, i2, j1, j2 in ops:
        O, N = a[i1:i2], b[j1:j2]
        if op != "replace" or len(O) != len(N): return False, None
        for x, y in zip(O, N):
            if ISNUM.match(x) and ISNUM.match(y): subs.append((x, y))
            elif x in MONTHS["de"] and y in MONTHS["de"]:
                subs.append((MONTHS[lang][MONTHS["de"].index(x)], MONTHS[lang][MONTHS["de"].index(y)]))
            elif x == y: continue
            else: return False, None
    out = tgt_old
    cnt_de = Counter(a)
    for x, y in subs:
        pat = re.compile(r"(?<![\w.,'’])" + re.escape(x) + r"(?![\w]|[.,'’]\d)")
        hits = pat.findall(out)
        if len(hits) != 1 and not (ISNUM.match(x) and len(hits) == cnt_de[x]): return True, None
        out = pat.sub(y, out)
    return True, out
