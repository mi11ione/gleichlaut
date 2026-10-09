"""Deterministic post-guards for the Gleichlaut whole-paragraph arm (2b). Stdlib only; uses gleichlaut/s2/lock.py.
G1 untranslated: tokens the output ADDS relative to the old FR/IT (multiset difference) that are German: a German
   function-word stoplist (words that do not exist in FR/IT), umlaut/ß, or a German -ung/-ungen noun. ALL-CAPS tokens
   (product names) are ignored.
G2 stale change: for every DE op, its lock window in the old FR/IT (lock.windows) must contain target edits that mirror
   it: if the DE op adds content (content word / number), the target must add content in that window; if it removes
   content, the target must remove content there.
G3 dropped content: (a) content tokens of the old FR/IT outside every DE-op window must survive in the output (multiset);
   (b) inside each window, the target's net content loss may exceed the DE op's net content loss by at most 1 token.
Content token = number, or alphabetic token of >= 4 letters not in the FR/IT/DE function-word lists.
Thresholds fixed as written here (designed after reading the 2b hand check, so the evaluation on the same 120 items is
in-sample)."""
import re, sys, difflib
from collections import Counter
sys.path.insert(0, "/Users/mi11ion/Desktop/hackapertus/spikes/gleichlaut/s2")
import lock
from lock import tok, norm

DE_ONLY = set("""der die das den dem des_DE und oder mit von vom für fuer bei auf zur zum nach nicht ist wird werden wurde
eine einer einem eines ein im am gemäss gemäß durch sowie bzw beziehungsweise als wie auch zu dieser diese dieses
nur sind kann können muss müssen soll sollen darf dürfen wenn sofern über unter ohne gegen""".split()) - {"des_DE"}
STOP = {
 "fr": set("""le la les l un une des du de d et ou en au aux à a par pour sur dans avec sans chez qui que qu ce cette ces
ne pas est sont être été sera doit doivent peut peuvent lors leur leurs son sa ses il elle ils elles se s y si
plus moins tout tous toute toutes ainsi selon entre après avant comme dont même autre autres""".split()),
 "it": set("""il lo la i gli le l un uno una di del della dello dei degli delle d e ed o od in nel nella nei negli nelle a
al alla ai agli alle da dal dalla dai dagli dalle per con su sul sulla tra fra che chi non è sono essere stato
viene vengono deve devono può possono se si ci come anche più meno tutto tutti tutta tutte così secondo dopo prima
quale quali questo questa questi queste suo sua suoi sue loro dell dall nell sull all coll quell""".split()),
 "de": DE_ONLY | set("""ein eine es sie er sich so da dass daß an in aus bis""".split())}


V2 = False   # v2: proportional G2 (target adds/removes >= PROP x the DE op's content tokens) + G4 duplication
PROP = 0.5
UNJ = (3, 1)  # v2 G3c: target content removed in a window <= 3 x DE content removed + 1 (German compounds)
NG = 6       # G4: an n-gram repeated in the output more often than in the old text
G3B = None   # optional in-window net-loss check (factor, slack); None = off (primary = coordinator spec)


def is_num(t): return bool(re.match(r"^\d", t)) or bool(re.match(r"^⟨[A-Z]{1,2}⟩$", t))
def content(t, lang):
    if is_num(t): return False   # numbers / slot codes are mirrored by the existing slot guard (lock.guard 'nums')
    w = t.lower()
    return w.isalpha() and len(w) >= 4 and w not in STOP[lang] and w not in STOP["de"]


def g1(old, out):
    o, n = Counter(tok(norm(old))), Counter(tok(norm(out)))
    added = [t for t, c in (n - o).items() for _ in range(c)]
    bad = [t for t in added if not t.isupper() and (t.lower() in DE_ONLY or re.search(r"[äöüßÄÖÜ]", t)
                                                   or re.search(r"[a-zäöü]ung(en)?$", t))]
    return bad


def tgt_ops(old, out):
    t, o = tok(old), tok(out)
    return t, o, [x for x in difflib.SequenceMatcher(None, t, o, autojunk=False).get_opcodes() if x[0] != "equal"]


def in_win(op, lo, hi):
    _, j1, j2, _, _ = op
    return (lo <= j1 <= hi) if j1 == j2 else (j1 <= hi and j2 >= lo)


def g23(de_old, de_new, old, out, lang):
    old, out = norm(old), norm(out)
    a, b, dops = lock.de_ops(de_old, de_new)
    W, t = lock.windows(de_old, de_new, old)
    _, o, E = tgt_ops(old, out)
    stale, dropped = [], []
    for (op, i1, i2, j1, j2), (lo, hi) in zip(dops, W):
        da = Counter(x.lower() for x in b[j1:j2] if content(x, "de")); dr = Counter(x.lower() for x in a[i1:i2] if content(x, "de"))
        da, dr = da - dr, dr - da
        ta, tr = Counter(), Counter()
        for e in E:
            if in_win(e, lo, hi):
                _, k1, k2, m1, m2 = e
                ta += Counter(x.lower() for x in o[m1:m2] if content(x, lang)); tr += Counter(x.lower() for x in t[k1:k2] if content(x, lang))
        ta, tr = ta - tr, tr - ta
        de_txt = f"«{' '.join(a[i1:i2])}» -> «{' '.join(b[j1:j2])}»"
        nda, ndr, nta, ntr = sum(da.values()), sum(dr.values()), sum(ta.values()), sum(tr.values())
        if nda and nta < (PROP * nda if V2 else 1): stale.append(("add", de_txt))
        elif ndr and ntr < (PROP * ndr if V2 else 1): stale.append(("remove", de_txt))
        if V2 and ntr > UNJ[0] * ndr + UNJ[1]:
            dropped.append(("unjustified-removal", de_txt, " ".join(tr.elements())))
        if G3B is not None and (sum(tr.values()) - sum(ta.values())) > G3B[0] * max(0, sum(dr.values()) - sum(da.values())) + G3B[1]:
            dropped.append(("net-loss", de_txt, " ".join(tr.elements())))
    # G3a: content outside all windows survives
    inside = set()
    for lo, hi in W: inside.update(range(lo, hi))
    outside = Counter(x.lower() for j, x in enumerate(t) if j not in inside and content(x, lang))
    lost = outside - Counter(x.lower() for x in o if content(x, lang))
    if lost: dropped.append(("outside-lost", "", " ".join(lost.elements())))
    return stale, dropped


def g4(old, out):
    def grams(s):
        w = [x.lower() for x in tok(norm(s)) if re.match(r"\w", x)]
        return Counter(tuple(w[i:i + NG]) for i in range(len(w) - NG + 1))
    go, gn = grams(old), grams(out)
    return [" ".join(g) for g, c in gn.items() if c >= 2 and c > go[g]][:3]


def run(x, out):
    G1 = g1(x["tgt_old"], out); st, dr = g23(x["de_old"], x["de_new"], x["tgt_old"], out, x["lang"])
    G4 = g4(x["tgt_old"], out) if V2 else []
    return dict(g1=G1, g2=st, g3=dr, g4=G4, flag=bool(G1 or st or dr or G4))
