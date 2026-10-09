"""Pre-existing DE<->FR / DE<->IT congruence audit of every current SL limitation. Deterministic, stdlib, no model calls.

Gleichlaut's guards check that an amendment mirrors the German change; a divergence already present in the old French or
Italian is carried forward. This audit looks for those: for each CUD id it compares the numeric values of the German text
with those of the French and of the Italian text and reports values present in one and absent in the other.

Values: digits (62.5 = 62,5; 1'000 = 1 000 = 1000; ranges 15-30 / 15 - < 60 give both ends; 6% -> 6), dates dd.mm.yyyy
(-> day, year), and the cardinal number words 2..12 of each language (core.gl2.NUMW; also inside DE compounds such as
'zweimal', 'vierwöchentlich'). Rules (written before any measurement; docs/audit.md):
  R1 list numbering ('1) ', '2. ' after a sentence end or at the start) is structure, not content: dropped on both sides.
  R2 only values bound to a unit or quantity noun (mg, kg, %, Wochen/semaines/settimane, Jahre/ans/anni, Zyklen, x ...)
     on the side where they occur become findings; a range '15 - < 30 kg' binds both ends. Unbound differences (codes,
     article numbers, table cells, years) are counted, not reported.
  R3 value 1 is never reported (articles ein/un/uno carry it).
  R4 reconciliation before reporting: '1.000' may be 1000; '0,2' glued in one language may be '0, 2' in the other (and the
     reverse); N days = N/7 weeks, N months = N/12 years, N g = 1000N mg; DE 'N. Lebensjahr' may be FR/IT 'N-1 ans/anni';
     a value given as an ordinal word ('deuxième', 'terza', 'zweite') on the other side.
  R5 values present in both languages with different counts are a separate 'count' list, not findings (repetition style).
A second signal (DE<->FR/IT term pairs mined from the aligned corpus, term_pairs()) was measured and is off: docs/audit.md.

usage: python3 -m gleichlaut.audit [--hist DIR] [--date 20261006] [--out data/audit] [--items data/items/items_fresh.json]
                                   [--worklist DIR]"""
import argparse, hashlib, json, os, random, re, sys
from collections import Counter, defaultdict
from . import core
from .sl import hist_dir
from .sl.ingest import nrm

NUMW = core.gl2.NUMW
DEST = os.path.join(core.ROOT, "data", "audit")
SEED = 20261009
KNOWN = {"NEMLUVIO.01": [("it", "lacks", "8")], "DIAPHIN.6-": [("it", "adds", "12"), ("it", "lacks", "6")],
         "NEPEXTO": [("fr", "adds", "62.5")], "BENEPALI4": [("fr", "adds", "62.5")], "ERELZI2": [("fr", "adds", "62.5")],
         "CRESE.Kps.IM": [("fr", "lacks", "16")], "DUPIXENT.02P": [("fr", "lacks", "15")], "DUPIXENT.02": [("fr", "lacks", "15")],
         "DUPIXENT.05a": [("fr", "adds", "30"), ("fr", "lacks", "15")], "DUPIXENT.05P": [("fr", "adds", "30"), ("fr", "lacks", "15")]}
KNOWN_BONUS = "KEYTRUDA.07---Inj-L-s---Urothelkarzinom--Monotherapie--KN045"    # IT slot carries French: not numeric
# (the KNOWN tests are data/backtest/targeted5.json 'tests', copied; used only for evaluation, never by the rules)

# ------------------------------------------------------------------ lexicons
U_COMMON = (r"%|‰|mg|µg|μg|mcg|ng|g|kg|ml|mL|dl|l|IE|I\.E\.|UI|U\.I\.|IU|E|U|mmol|µmol|μmol|nmol|mol|mval|mEq|mm|cm|m²|m2|"
            r"Gy|MBq|GBq|kcal|mmHg|x|×|G/l|/µl|/μl|/µL|/μL|/mm3|/mm³|Mio\.?")
UNIT = {"de": U_COMMON + r"|Prozent|\w*[Tt]ag(?:e|en|es)?\b\w*|tägig\w*|täglich\w*|\w*[Ww]oche\w*|wöch\w*|\w*[Mm]onat\w*|"
                         r"\w*[Jj]ahr\w*|jährig\w*|jährlich\w*|Std\.?|Stunde\w*|Minute\w*|\w*[Zz]ykl\w*|Dos[ie]\w*|"
                         r"Injektion\w*|Infusion\w*|Tablette\w*|Kapsel\w*|Packung\w*|Pen\w*|Spritze\w*|Ampulle\w*|Mal|mal|"
                         r"Punkt\w*|Zellen|Millionen|Kalenderjahr\w*",
        "fr": U_COMMON + r"|pour ?cent|jours?|semaines?|mois|ans?|années?|heures?|h|minutes?|cycles?|doses?|injections?|"
                         r"perfusions?|comprimés?|capsules?|gélules?|emballages?|boîtes?|stylos?|seringues?|ampoules?|fois|"
                         r"points?|cellules|millions?",
        "it": U_COMMON + r"|per ?cento|giorn[oi]|settiman[ae]|mes[ei]|ann[oi]|or[ae]|h|minut[oi]|cicl[oi]|dos[ei]|"
                         r"iniezion[ei]|infusion[ei]|compress[ae]|capsul[ae]|confezion[ei]|penn[ae]|siring[ae]|fial[ae]|"
                         r"volt[ae]|punt[oi]|cellule|milion[ei]"}
UNIT_RX = {L: re.compile(r"\.?\s?-?\s?(?:" + u + r")(?![\w])") for L, u in UNIT.items()}
# a range '15 - < 30 kg', '15–30 kg', '15 bis 30 kg', 'da 15 a 30 kg': the first end takes the unit of the second
RANGE = {"de": r"bis(?: unter| zu)?|-|–|—|,|und|oder|bzw\.|resp\.", "fr": r"à|a|-|–|—|,|et|ou", "it": r"a|al|-|–|—|,|e|o|ed|od"}
TIME = {"de": {"d": r"Tag\w*|tägig\w*", "w": r"Woche\w*|wöch\w*", "m": r"Monat\w*", "y": r"Jahr\w*|jährig\w*"},
        "fr": {"d": r"jours?", "w": r"semaines?", "m": r"mois", "y": r"ans?|années?"},
        "it": {"d": r"giorn[oi]", "w": r"settiman[ae]", "m": r"mes[ei]", "y": r"ann[oi]"}}
ORD = {"de": ["", "", r"zweit", r"dritt", r"viert(?!el)", r"fünft", r"sechst", r"siebt", r"achte", r"neunt", r"zehnt", r"elft", r"zwölft"],
       "fr": ["", "", r"deuxi|second", r"troisi", r"quatri", r"cinqui", r"sixi", r"septi", r"huiti", r"neuvi", r"dixi", r"onzi", r"douzi"],
       "it": ["", "", r"second", r"terz", r"quart", r"quint", r"sest", r"settim", r"ottav", r"non[oaie]\b", r"decim", r"undicesim", r"dodicesim"]}
DE_COMPOUND = r"(?:mal\w*|wöch\w*|monat\w*|jährig\w*|jährlich\w*|tägig\w*|täglich\w*|stündlich\w*|fach\w*)"
PERIOD = {("2", "m"): r"\bbimestr", ("3", "m"): r"\btrimestr|vierteljährl|\bquartal", ("6", "m"): r"\bsemestr|halbjährl",
          ("14", "d"): r"\bquindicinal|\bzweiwöchentl", ("2", "w"): r"\bquindicinal|\bzweiwöchentl"}
ONE = {"de": r"\bein\w*\b|\beins\b", "fr": r"\bun\b|\bune\b|\bpremi", "it": r"\bun[oa']?\b|\bprim[oa]"}

NUMTOK = re.compile(r"(?<![\w.,'’])\d{1,3}(?:[  ]\d{3})+(?![\d.,]\d)|(?<![^\W\d_])\d+(?:[.,'’]\d+)*")   # not glued to letters (FEV1, HER2)
DATE = re.compile(r"^(\d{1,2})\.(\d{1,2})\.(\d{4})$")
ENUM = re.compile(r"(?:^|[.:;!?•]\s|\s[•\-–]\s)\s*\(?(\d{1,2})[.)](?=\s+\S)")


def canon(s):
    """surface -> (value, alt or None). 1'000 / 1 000 -> 1000; 62,5 -> 62.5; 2.50 -> 2.5; '1.000' -> ('1', '1000');
    several separators (SR 832.112.31, codes) -> the digits joined by '.'."""
    s = re.sub(r"[ '’  ]", "", s)
    parts = re.split(r"[.,]", s)
    if len(parts) == 1: return str(int(s)), None
    if len(parts) > 2: return ".".join(parts), None
    a, b = parts
    d = (str(int(a)) + "." + b).rstrip("0").rstrip(".")
    return d, (str(int(a + b)) if len(b) == 3 else None)


def values(text, lang):
    """-> list of dict(v, alt, bound, unit, start, end, src) for every numeric value in text (R1 list numbers removed)."""
    out = []; urx = UNIT_RX[lang]
    enum = set(m.start(1) for m in ENUM.finditer(text))
    for m in NUMTOK.finditer(text):
        if m.start() in enum: continue
        sf = m.group(0); d = DATE.match(sf)
        if d:
            for g in (1, 3): out.append(dict(v=str(int(d.group(g))), alt=None, s=m.start(), e=m.end(), src="date"))
            continue
        v, alt = canon(sf)
        out.append(dict(v=v, alt=alt, s=m.start(), e=m.end(), src="digit"))
    words = NUMW[lang][2:]
    wrx = r"\b(" + "|".join(words) + r")" + (r"(?:" + DE_COMPOUND + r")?\b" if lang == "de" else r"\b")
    for m in re.finditer(wrx, text, flags=re.I):
        out.append(dict(v=str(NUMW[lang].index(m.group(1).lower())), alt=None, s=m.start(), e=m.end(), src="word"))
    out.sort(key=lambda x: x["s"])
    for i in range(len(out) - 1, -1, -1):           # R2: unit binding, right to left (ranges and lists '2, 4 und 6 Wochen')
        x = out[i]
        u = urx.match(text, x["e"]) or (re.match(r"[\w-]*" + DE_COMPOUND, text[x["e"]:]) if x["src"] == "word" else None)
        x["unit"] = u.group(0).strip(" -.") if u else None
        if not u and i + 1 < len(out) and out[i + 1]["unit"]:
            gap = text[x["e"]:out[i + 1]["s"]]
            if re.fullmatch(r"\.?\s*(?:" + UNIT[lang] + r")?\s*(?:" + RANGE[lang] + r")\s*[<≤>≥]?\s*", gap): x["unit"] = out[i + 1]["unit"]
    for x in out:
        lb = text[x["e"]:x["e"] + 14]
        x["ordlj"] = lang == "de" and re.match(r"\.\s?Lebensjahr", lb) is not None
        x["ord"] = x["src"] == "digit" and re.match(r"\.(?!\d)|e\b|er\b|ère|ème|°|ª|[ao]\b", lb) is not None
    return out


def ctx(text, x, w=60):
    a, b = max(0, x["s"] - w), min(len(text), x["e"] + w)
    return ("…" if a else "") + text[a:x["s"]] + "[" + text[x["s"]:x["e"]] + "]" + text[x["e"]:b] + ("…" if b < len(text) else "")


def _unit_class(u, lang):
    if not u: return None
    for k, rx in TIME[lang].items():
        if re.fullmatch(rx, u, flags=re.I): return k
    if u in ("g",): return "g"
    if u in ("mg",): return "mg"
    return None


def _num(v):
    try: return float(v)
    except ValueError: return None


def compare(de, tgt, lang):
    """DE text vs one target text -> dict(de_only=[...], tgt_only=[...], count=[...], unbound=n, suppressed={rule: n})."""
    de, tgt = nrm(de), nrm(tgt)
    A, B = values(de, "de"), values(tgt, lang)
    ca, cb = Counter(x["v"] for x in A), Counter(x["v"] for x in B)
    va, vb = set(ca), set(cb)
    onlyA = [x for x in A if x["v"] not in vb]; onlyB = [x for x in B if x["v"] not in va]
    sup = Counter()

    def drop(lst, keep, rule):
        k = [x for x in lst if keep(x)]; sup[rule] += len(set(x["v"] for x in lst)) - len(set(x["v"] for x in k)); return k
    # R4a: '1.000' read as decimal on one side, thousand on the other
    altA, altB = set(x["alt"] for x in A if x["alt"]), set(x["alt"] for x in B if x["alt"])
    onlyA = drop(onlyA, lambda x: not (x["alt"] and x["alt"] in vb) and x["v"] not in altB, "thousands")
    onlyB = drop(onlyB, lambda x: not (x["alt"] and x["alt"] in va) and x["v"] not in altA, "thousands")
    # R4b: glued '0,2' vs '0, 2' (either side): every part present on the other side; the parts are consumed there too
    def parts(x, text): return [str(int(q)) for q in re.split(r"[.,'’  ]", text[x["s"]:x["e"]]) if q]
    gA = [x for x in onlyA if x["src"] == "digit" and len(parts(x, de)) > 1 and all(q in vb for q in parts(x, de))]
    gB = [x for x in onlyB if x["src"] == "digit" and len(parts(x, tgt)) > 1 and all(q in va for q in parts(x, tgt))]
    pA = set(q for x in gA for q in parts(x, de)); pB = set(q for x in gB for q in parts(x, tgt))
    onlyA = drop(onlyA, lambda x: x not in gA and x["v"] not in pB, "glued")
    onlyB = drop(onlyB, lambda x: x not in gB and x["v"] not in pA, "glued")
    # R4c: unit conversions between the two unmatched lists
    def conv(x, others, xl, ol):
        a, ua = _num(x["v"]), _unit_class(x["unit"], xl)
        if a is None or not ua: return False
        for y in others:
            b, ub = _num(y["v"]), _unit_class(y["unit"], ol)
            if b is None or not ub: continue
            for (p, q, f) in (("d", "w", 7), ("m", "y", 12), ("mg", "g", 1000), ("w", "d", 1 / 7), ("y", "m", 1 / 12), ("g", "mg", 1 / 1000)):
                if ua == p and ub == q and abs(a - b * f) < 1e-9: return True
        return False
    cA = [x for x in onlyA if conv(x, onlyB, "de", lang)]; cB = [x for x in onlyB if conv(x, onlyA, lang, "de")]
    onlyA = drop(onlyA, lambda x: x not in cA, "unit_conversion"); onlyB = drop(onlyB, lambda x: x not in cB, "unit_conversion")
    # R4d: DE 'N. Lebensjahr' vs 'N-1 ans/anni'
    lj = [x for x in onlyA if x["ordlj"] and _num(x["v"]) and str(int(_num(x["v"])) - 1) in vb]
    onlyB = drop(onlyB, lambda y: not any(_num(y["v"]) == _num(x["v"]) - 1 for x in lj), "lebensjahr")
    onlyA = drop(onlyA, lambda x: x not in lj, "lebensjahr")
    # R4e: ordinal word on the other side
    def ordw(x, text, L):
        n = _num(x["v"])
        if n is None or n != int(n) or not 2 <= n <= 12: return False
        return re.search(r"\b(?:" + ORD[L][int(n)] + r")", text, flags=re.I) is not None
    onlyA = drop(onlyA, lambda x: not (x["ord"] and ordw(x, tgt, lang)), "ordinal_word")
    onlyB = drop(onlyB, lambda x: not (x["ord"] and ordw(x, de, "de")), "ordinal_word")
    # R4f: period adjectives on the other side ('alle 2 Monate' = 'bimestrale', 'vierteljährlich' = 'tous les 3 mois')
    def period(x, xl, text):
        k = (x["v"], _unit_class(x["unit"], xl)); return k in PERIOD and re.search(PERIOD[k], text, flags=re.I) is not None
    onlyA = drop(onlyA, lambda x: not period(x, "de", tgt), "period_word")
    onlyB = drop(onlyB, lambda x: not period(x, lang, de), "period_word")
    # R3: value 1 with an article / 'premier' on the other side
    onlyA = drop(onlyA, lambda x: not (x["v"] == "1" and re.search(ONE[lang], tgt, flags=re.I)), "one")
    onlyB = drop(onlyB, lambda x: not (x["v"] == "1" and re.search(ONE["de"], de, flags=re.I)), "one")
    # R2: only unit-bound values become findings
    def group(lst, text):
        g = defaultdict(list)
        for x in lst: g[x["v"]].append(x)
        res, unb = [], 0
        for v, xs in g.items():
            b = [x for x in xs if x["unit"]]
            if not b: unb += 1; continue
            res.append(dict(value=v, n=len(xs), unit=b[0]["unit"], src=b[0]["src"], context=[ctx(text, x) for x in xs[:3]]))
        return res, unb
    fa, ua = group(onlyA, de); fb, ub = group(onlyB, tgt)
    cnt = [dict(value=v, de=ca[v], tgt=cb[v]) for v in sorted(va & vb) if ca[v] != cb[v]]
    return dict(de_only=fa, tgt_only=fb, count=cnt, unbound=ua + ub, suppressed={k: n for k, n in sup.items() if n})


def rank(r):
    """swap of same-unit values (8 vs 4 weeks, 6% vs 12%) > one-sided bound value; fewer unmatched values first."""
    a, b = r["de_only"], r["tgt_only"]
    ua = set(x["unit"].lower() for x in a); ub = set(x["unit"].lower() for x in b)
    n = len(a) + len(b)
    return (2 if ua & ub else 1) * 10 - min(n, 9)


def describe(r, lang):
    L = lang.upper(); p = []
    for x in r["de_only"]: p.append(f"DE has {x['value']} ({x['unit']}), {L} does not")
    for x in r["tgt_only"]: p.append(f"{L} has {x['value']} ({x['unit']}), DE does not")
    return "; ".join(p)


def audit_item(x):
    """For the review UI: pre-existing numeric divergences between an item's old German and old target text.
    x: dict with de_old, tgt_old, lang. -> [] or a list of dict(side 'de'|lang, value, unit, context)."""
    r = compare(x["de_old"], x["tgt_old"], x["lang"])
    return [dict(side="de", **y) for y in r["de_only"]] + [dict(side=x["lang"], **y) for y in r["tgt_only"]]


# ------------------------------------------------------------------ the whole snapshot
def half(i): return "dev" if int(hashlib.md5(i.encode()).hexdigest(), 16) % 2 == 0 else "held"


def load(hist, date):
    J = {L: json.load(open(os.path.join(hist, f"{date}-{L}.json"), encoding="utf-8")) for L in ("de", "fr", "it")}
    names = defaultdict(list)
    for p in J["de"]["prod"].values():
        for k in p["keys"]: names[k].append(p["name"])
    return J, names


def run(hist, date):
    J, names = load(hist, date)
    F, cnt, unb, sup = [], 0, 0, Counter()
    for i in sorted(J["de"]["lim"]):
        de = J["de"]["lim"][i]
        for L in ("fr", "it"):
            t = J[L]["lim"].get(i)
            if t is None: continue
            r = compare(de, t, L); cnt += len(r["count"]); unb += r["unbound"]; sup.update(r["suppressed"])
            if not (r["de_only"] or r["tgt_only"]): continue
            g = hashlib.sha1((nrm(de) + "\0" + nrm(t)).encode()).hexdigest()[:10]
            F.append(dict(id=i, product=sorted(set(n.split(" ")[0] for n in names.get(i, [])))[:3], lang=L, kind="numeric",
                          score=rank(r), half=half(i), group=g, de_only=r["de_only"], tgt_only=r["tgt_only"],
                          description=describe(r, L), known=i in KNOWN and any(k[0] == L for k in KNOWN[i])))
    F.sort(key=lambda f: (-f["score"], f["id"], f["lang"]))
    for n, f in enumerate(F): f["rank"] = n + 1
    return F, dict(count_only_differences=cnt, unbound_differences=unb, suppressed=dict(sup), n_limitations=len(J["de"]["lim"]))


def recall(F):
    """known case hit = a finding in the right language that names the hand-verified value on the right side."""
    by = {(f["id"], f["lang"]): f for f in F}; out = {}
    for i, tests in KNOWN.items():
        res = []
        for L, kind, v in tests:
            f = by.get((i, L))
            lst = (f["de_only"] if kind == "lacks" else f["tgt_only"]) if f else []
            res.append(dict(lang=L, test=kind, value=v, hit=any(x["value"] == v for x in lst), rank=f["rank"] if f else None))
        out[i] = dict(tests=res, hit=any(r["hit"] for r in res), all=all(r["hit"] for r in res))
    return out


def worklist(F, hist, date, d, n=40):
    """seeded uniform sample of n findings (all of them, shuffled, when there are fewer), blind: no rank, no known flag.
    The key map keeps the half (design looked at 'dev' findings only), so precision can be reported on 'held' alone."""
    J, _ = load(hist, date)
    pool = list(F)
    S = random.Random(SEED).sample(pool, min(n, len(pool)))
    os.makedirs(d, exist_ok=True); W, K = [], {}
    for j, f in enumerate(S):
        a = f"A{j:02d}"
        W.append(dict(id=a, de=nrm(J["de"]["lim"][f["id"]]), target=nrm(J[f["lang"]]["lim"][f["id"]]), lang=f["lang"],
                      finding=f["description"],
                      question="Do the German and the " + {"fr": "French", "it": "Italian"}[f["lang"]] + " text state a "
                               "different condition for at least one of the values named in 'finding'? Answer real / "
                               "minor / not (same condition: formatting, rephrasing, unit conversion, parser artefact)."))
        K[a] = dict(cud=f["id"], lang=f["lang"], rank=f["rank"], known=f["known"], score=f["score"], half=f["half"])
    json.dump(W, open(os.path.join(d, "worklist.json"), "w"), ensure_ascii=False, indent=1)
    json.dump(K, open(os.path.join(d, "key_map_DO_NOT_SHOW.json"), "w"), ensure_ascii=False, indent=1)
    return len(pool), len(S)


# ------------------------------------------------------------------ optional second signal: term pairs (measured, off)
STOP = {"fr": set("les des une dans pour avec sont être cette leur leurs plus mais aussi entre après avant ainsi lors doit "
                  "doivent peut sous chez dont elle elles ont tous toutes tout comme".split()),
        "it": set("della delle degli dello dei del nella nelle negli con per sono essere questa questo loro più anche tra "
                  "dopo prima così deve devono può sotto presso cui".split())}


def term_pairs(J, lang, p=0.9, support=10):
    """DE term (word or hyphen compound, >= 8 letters) <-> target word or word bigram that co-occur in >= p of the aligned
    distinct text pairs in both directions; exceptions = pairs where one is present and the other is not."""
    de_t = lambda t: set(w.lower() for w in re.findall(r"[^\W\d_]\w*(?:-\w+)*", t) if len(w) >= 8)
    def tg_t(t):
        w = [x.lower() for x in re.findall(r"[^\W\d_]+", t)]; w = [x for x in w if len(x) >= 5 and x not in STOP[lang]]
        return set(w) | set(a + " " + b for a, b in zip(w, w[1:]))
    uniq = {}
    for i in J["de"]["lim"]: uniq.setdefault((nrm(J["de"]["lim"][i]), nrm(J[lang]["lim"].get(i, ""))), i)
    docs = [(i, de_t(a), tg_t(b)) for (a, b), i in uniq.items()]
    nd = Counter(w for _, d, _ in docs for w in d); nt = Counter(w for _, _, t in docs for w in t); co = defaultdict(Counter)
    for _, d, t in docs:
        for w in d:
            if nd[w] >= support: co[w].update(f for f in t if nt[f] >= support)
    P = []
    for w, c in co.items():
        f = max(c, key=lambda f: c[f] * c[f] / (nd[w] * nt[f]))
        if c[f] / nd[w] >= p and c[f] / nt[f] >= p: P.append((w, f))
    exc = [(i, w, f) for i, d, t in docs for w, f in P if (w in d) != (f in t)]
    return dict(p=p, support=support, distinct_pairs=len(docs), term_pairs=len(P), exceptions=len(exc),
                ids_with_exception=len(set(e[0] for e in exc)), examples=[list(x) for x in sorted(P, key=lambda x: -nd[x[0]])[:10]])


def term_probe(J, lang="fr"):
    """the motivating case: how often FR says 'récepteurs ... angiotensine' where DE says 'Angiotensin-II-Antagonist'."""
    ids = [i for i, t in J["de"]["lim"].items() if "Angiotensin-II-Antagonist" in t]
    ok = [i for i in ids if re.search(r"récepteurs? de l.angiotensine", J[lang]["lim"].get(i, ""))]
    return dict(de_ids=len(ids), fr_with_receptor_antagonist=len(ok), wrong_class=sorted(set(ids) - set(ok)))


def fresh(items):
    X = json.load(open(items, encoding="utf-8")); hits = []
    for x in X:
        r = audit_item(x)
        if r: hits.append(dict(key=x["key"], lang=x["lang"], findings=r))
    return dict(items=len(X), with_preexisting=len(hits), pairs=len(set(h["key"].split("-")[0] for h in hits)), hits=hits)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="gleichlaut.audit", description=__doc__.split("\n\n")[0])
    ap.add_argument("--hist", help="snapshot dir (default: $GLEICHLAUT_HIST or track_2b/out/hist)")
    ap.add_argument("--date", default="20261006")
    ap.add_argument("--out", default=DEST)
    ap.add_argument("--items", default=os.path.join(core.ROOT, "data", "items", "items_fresh.json"))
    ap.add_argument("--worklist", help="write the blind 40-finding precision worklist + key map to this dir")
    a = ap.parse_args(argv)
    H = hist_dir(a.hist)
    if not os.path.exists(os.path.join(H, f"{a.date}-de.json")): sys.exit(f"no snapshot {a.date} in {H}")
    F, S = run(H, a.date)
    R = recall(F)
    fr = fresh(a.items) if a.items and os.path.exists(a.items) else None
    J, _ = load(H, a.date)
    terms = dict(status="off: not precise enough (docs/audit.md)", fr=term_pairs(J, "fr"), it=term_pairs(J, "it"),
                 probe=term_probe(J))
    summ = dict(generated_by="python3 -m gleichlaut.audit --hist <dir> --date " + a.date, date=a.date, model_calls=0,
                findings=len(F), by_lang=dict(Counter(f["lang"] for f in F)), by_half=dict(Counter(f["half"] for f in F)),
                limitations_with_finding=len(set(f["id"] for f in F)), distinct_text_pairs=len(set(f["group"] for f in F)),
                swaps=sum(1 for f in F if f["score"] >= 11), **S,
                recall=dict(limitations=sum(r["hit"] for r in R.values()), of=len(R),
                            tests=sum(t["hit"] for r in R.values() for t in r["tests"]),
                            of_tests=sum(len(r["tests"]) for r in R.values()), cases=R),
                keytruda_bonus=dict(found=any(f["id"] == KNOWN_BONUS for f in F),
                                    note="not numeric (the IT slot carries French text); out of scope for this check"),
                s1_census_reference=dict(precision="3/50 = 6% (all categories)", num="3/15 = 20% strict",
                                         source="spikes/gleichlaut/results.md (research, not shipped)"),
                term_pairs=terms,
                fresh=dict((k, v) for k, v in fr.items() if k != "hits") if fr else None)
    os.makedirs(a.out, exist_ok=True)
    json.dump(dict(summary=summ, findings=F, fresh_items=fr["hits"] if fr else None),
              open(os.path.join(a.out, f"audit_{a.date}.json"), "w"), ensure_ascii=False, indent=0)
    if a.worklist: summ["worklist"] = dict(zip(("pool", "n"), worklist(F, H, a.date, a.worklist)))
    json.dump(summ, open(os.path.join(a.out, f"audit_{a.date}_summary.json"), "w"), ensure_ascii=False, indent=1)
    print(f"{len(F)} findings ({summ['by_lang']}) on {summ['limitations_with_finding']} of {S['n_limitations']} limitations; "
          f"recall {summ['recall']['limitations']}/{len(R)} known limitations; fresh items with a pre-existing divergence: "
          f"{fr['with_preexisting'] if fr else '-'} of {fr['items'] if fr else '-'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
