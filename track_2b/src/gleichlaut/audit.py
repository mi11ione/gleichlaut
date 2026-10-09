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
Round 3 adds three kinds (pre-registered, see 'round 3' below and docs/audit.md); every finding has kind
'number' | 'unit' | 'language' | 'editorial':
  language   a DE/FR/IT field predominantly in another language (function words + register trigram profiles)
  unit       the same value with a different unit in the same dimension (4 Wochen vs 4 mois; 15 kg vs 15 mg)
  editorial  conservative typo rules (E1 '1 .4', E2 'de15 kg', E3 '4Wochen', E4 'almeno se mesi', E5 '6 Monte')
A second signal (DE<->FR/IT term pairs mined from the aligned corpus, term_pairs()) was measured and is off: docs/audit.md.

usage: python3 -m gleichlaut.audit [--hist DIR] [--date 20261006] [--out data/audit] [--items data/items/items_fresh.json]
                                   [--worklist DIR] [--worklist-new DIR] [--no-dating]"""
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


# ================================================================== round 3: language, unit, editorial (PRE-REGISTERED)
# Everything from here to 'END OF ROUND-3 RULES' was written in full before it was first run on any snapshot or item.
# Thresholds are a-priori choices, not fitted. Not used to write them: the blind labels of round 2, the known cases,
# Keytruda, Myoview (docs/audit.md, 'How the rules were made').
LANGS = ("de", "fr", "it")
NAME = {"de": "German", "fr": "French", "it": "Italian", "en": "English"}
WORD = re.compile(r"[^\W\d_]+")
# closed-class function words; a word listed for two languages counts for neither, and a few words that are also common
# in another of the four languages are left out by hand (_FW_DROP)
_FW_RAW = {
    "de": "der die das den dem und oder nicht mit von für bei auf aus nach ist sind wird werden wurde wurden einer eine "
          "einem einen eines zur zum im am vom bis ab nur auch sowie durch als wenn kann können muss müssen darf dürfen "
          "sich ihre ihrer seine bzw gemäss gemäß unter über vor wie zu ein",
    "fr": "les du une et ou pour par avec sans dans sur chez au aux est sont être été qui que dont pas plus selon lors "
          "après avant jusqu entre ces cette ce son sa ses leur leurs doit doivent peut peuvent elle ils elles en qu à "
          "dès de",
    "it": "il lo gli della delle degli dello dei del nel nella nelle negli al alla alle agli allo dal dalla dalle dai e ed "
          "o od di con per su sul sulla tra fra che sono è essere deve devono può possono dopo prima entro ogni come più "
          "anche solo questo questa loro una",
    "en": "the and or of with for to by is are be been not from at which that this as who whose has have must may can "
          "only after before"}
_FW_DROP = {"fr": {"ne", "on", "la", "le"}, "it": {"se", "non", "da"}, "en": {"an", "on", "in"}}
_amb = Counter(w for s in _FW_RAW.values() for w in set(s.split()))
FW = {L: frozenset(w for w in s.split() if _amb[w] == 1 and w not in _FW_DROP.get(L, ())) for L, s in _FW_RAW.items()}
# prepositions that can stand right before a number (editorial E2: 'de15 kg')
PREP = {"de": "ab bis von mit für über unter alle je pro zu um", "fr": "de dès à par pour sur sous des les",
        "it": "di da a per su ogni al dal fino oltre entro"}
# value + unit classes for the unit check (fullmatch, case-insensitive): time, mass, volume
UCLS = {"de": [("d", r"Tag|Tage|Tagen|Tages|tägig\w*"), ("w", r"Woche|Wochen|wöchig\w*|wöchentl\w*"),
               ("m", r"Monat|Monate|Monaten|Monats|monatig\w*|monatl\w*"), ("y", r"Jahr|Jahre|Jahren|Jahres|jährig\w*|jährl\w*"),
               ("h", r"Std|Stunde|Stunden|stündig\w*"), ("min", r"Minute|Minuten|min")],
        "fr": [("d", r"jours?|journées?"), ("w", r"semaines?"), ("m", r"mois"), ("y", r"ans?|années?"), ("h", r"heures?|h"),
               ("min", r"minutes?|min")],
        "it": [("d", r"giorn[oi]|giornat[ae]"), ("w", r"settiman[ae]"), ("m", r"mes[ei]"), ("y", r"ann[oi]"), ("h", r"or[ae]|h"),
               ("min", r"minut[oi]|min")]}
UMASS = {"µg": "ug", "μg": "ug", "mcg": "ug", "mg": "mg", "g": "g", "kg": "kg", "ml": "ml", "mL": "ml", "dl": "dl", "l": "l"}
DIM = {"d": "time", "w": "time", "m": "time", "y": "time", "h": "time", "min": "time",
       "ug": "mass", "mg": "mass", "g": "mass", "kg": "mass", "ml": "vol", "dl": "vol", "l": "vol"}
UWORD = {"d": "days", "w": "weeks", "m": "months", "y": "years", "h": "hours", "min": "minutes", "ug": "µg", "mg": "mg",
         "g": "g", "kg": "kg", "ml": "ml", "dl": "dl", "l": "l"}
TIMEW = {L: "|".join(p for k, p in UCLS[L] if k in "dwmy") for L in LANGS}     # E3: digit glued to a time word
# thresholds (a priori)
LID_MIN, LID_RATIO = 3, 3          # A: >= 3 function words of X and >= 3x those of the field's own language
LID_EN_MIN = 5                     # English has no register profile: >= 5 and >= 5x
LID_NTRI, LID_MARGIN = 12, 0.5     # B: >= 12 character trigrams left after shared names; mean log-ratio >= 0.5 nat
E4_MIN, E4_MAX = 5, 2              # E4: the corrected trigram in >= 5 register texts, the observed one in <= 2
E5_MIN = 20                        # E5: the corrected unit word follows a digit in >= 20 register texts
STATS = os.path.join(DEST, "lang_stats_20261006.json.gz")


def words(t): return [w.lower() for w in WORD.findall(t)]


def fw_hits(ws): return {L: sum(w in FW[L] for w in ws) for L in FW}


def tri(ws):
    c = Counter()
    for w in ws:
        w = " " + w + " "
        for i in range(len(w) - 2): c[w[i:i + 3]] += 1
    return c


def lev1(a, b):
    """True when a and b are at Levenshtein distance exactly 1."""
    if a == b or abs(len(a) - len(b)) > 1: return False
    if len(a) == len(b): return sum(x != y for x, y in zip(a, b)) == 1
    if len(a) > len(b): a, b = b, a
    i = next((k for k in range(len(a)) if a[k] != b[k]), len(a))
    return a[i:] == b[i + 1:]


def _ucls(u, lang):
    """unit surface -> class (d/w/m/y/h/min, ug/mg/g/kg, ml/dl/l) or None."""
    if not u: return None
    if u in UMASS: return UMASS[u]
    for k, rx in UCLS[lang]:
        if re.fullmatch(rx, u, flags=re.I): return k
    return None


def _is_unit_word(w, lang):
    return len(w) >= 3 and w.isalpha() and re.fullmatch(r"(?:" + UNIT[lang] + r")", w, flags=re.I) is not None


def build_stats(J):
    """register statistics, mechanically from one snapshot. Per language field, over distinct texts, leaving out texts
    whose function words vote for another language (majority language per field):
      tri        character trigram counts (count >= 2) -> the n-gram profile of the language
      vocab      words in >= 3 texts (E5: a word not in it is rare)
      after      words that follow a number, with their text counts (>= 2) (E5)
      utri       'p w u' word trigrams where u is a unit word and w a number word 2..12 or one edit from one (E4)"""
    st = dict(tri={}, ntri={}, vocab={}, after={}, utri={})
    for L in LANGS:
        T = sorted(set(nrm(t) for t in J[L]["lim"].values() if t))
        tc, wc, ac, uc = Counter(), Counter(), Counter(), Counter()
        nw = NUMW[L][2:]
        for t in T:
            ws = words(t); h = fw_hits(ws)
            if any(h[X] >= max(LID_MIN, LID_RATIO * h[L]) for X in h if X != L): continue
            tc.update(tri(ws)); wc.update(set(ws))
            ac.update(set(m.group(1).lower() for m in re.finditer(r"(?<![\w.,])\d+(?:[.,]\d+)?\s([^\W\d_]{2,})", t)))
            u3 = set()
            for p, w, u in zip(ws, ws[1:], ws[2:]):
                if _is_unit_word(u, L) and (w in nw or any(lev1(w, n) for n in nw)): u3.add(p + " " + w + " " + u)
            uc.update(u3)
        st["tri"][L] = {k: v for k, v in tc.items() if v >= 2}; st["ntri"][L] = sum(st["tri"][L].values())
        st["vocab"][L] = sorted(w for w, c in wc.items() if c >= 3)
        st["after"][L] = {w: c for w, c in ac.items() if c >= 2}
        st["utri"][L] = dict(uc)
    st["V"] = len(set(k for L in LANGS for k in st["tri"][L]))
    return st


_STATS = {}


def load_stats(path=STATS):
    if path not in _STATS:
        try:
            import gzip
            s = json.load(gzip.open(path, "rt", encoding="utf-8")); s["_vocab"] = {L: set(v) for L, v in s["vocab"].items()}
            _STATS[path] = s
        except (OSError, ValueError):
            _STATS[path] = None
    return _STATS[path]


def _prep(st):
    if st is not None and "_vocab" not in st: st["_vocab"] = {L: set(v) for L, v in st["vocab"].items()}
    return st


def _ll(c, st, L):
    import math
    P, N, V = st["tri"][L], st["ntri"][L], st["V"]
    return sum(n * math.log((P.get(t, 0) + 1) / (N + V)) for t, n in c.items())


def lang_check(text, L, shared=(), st=None):
    """Is the text of field L predominantly in another language X? -> dict(detected, fw, margin, ntri, judged).
    A (function words): X has >= 3 hits and >= 3x the hits of L (English: >= 5 and >= 5x).
    B (character trigrams, register profiles; not for English): after removing the words in `shared` (names, INNs, codes
      shared with the other texts of the limitation), >= 12 trigrams are left and their mean log-likelihood ratio X:L
      is >= 0.5 nat. Without register profiles B cannot run and only English (A alone) can be detected.
    Both A and B must name the same X. Texts with fewer than 3 function words in total are not judged."""
    ws = words(text); h = fw_hits(ws)
    res = dict(detected=L, fw={k: v for k, v in h.items() if v}, margin=None, ntri=0, judged=sum(h.values()) >= LID_MIN)
    if not res["judged"]: return res
    X = sorted((Y for Y in h if Y != L), key=lambda Y: (-h[Y], Y))[0]
    if X == "en":
        if h[X] >= max(LID_EN_MIN, LID_EN_MIN * h[L]): res["detected"] = "en"
        return res
    if h[X] < max(LID_MIN, LID_RATIO * h[L]) or not st: return res
    c = tri([w for w in ws if w not in shared]); n = sum(c.values()); res["ntri"] = n
    if n < LID_NTRI: return res
    d = (_ll(c, st, X) - _ll(c, st, L)) / n; res["margin"] = round(d, 3)
    if d >= LID_MARGIN: res["detected"] = X
    return res


def unit_diff(de, tgt, lang):
    """R-U: a value present in both texts whose unit classes differ in both directions within one dimension
    (4 Wochen vs 4 mois; 15 kg vs 15 mg). -> [dict(value, de, tgt, de_units, tgt_units, context_de, context_tgt)]."""
    de, tgt = nrm(de), nrm(tgt)
    A, B = values(de, "de"), values(tgt, lang)
    out = []
    for v in sorted(set(x["v"] for x in A) & set(x["v"] for x in B)):
        xa = [x for x in A if x["v"] == v and _ucls(x["unit"], "de")]; xb = [x for x in B if x["v"] == v and _ucls(x["unit"], lang)]
        ca = set(_ucls(x["unit"], "de") for x in xa); cb = set(_ucls(x["unit"], lang) for x in xb)
        oa, ob = ca - cb, cb - ca
        pairs = [(a, b) for a in sorted(oa) for b in sorted(ob) if DIM[a] == DIM[b]]
        if not pairs: continue
        a, b = pairs[0]
        ea = next(x for x in xa if _ucls(x["unit"], "de") == a); eb = next(x for x in xb if _ucls(x["unit"], lang) == b)
        out.append(dict(value=v, de=a, tgt=b, de_unit=ea["unit"], tgt_unit=eb["unit"], de_units=sorted(ca), tgt_units=sorted(cb),
                        de_phrase=de[ea["s"]:ea["e"]] + " " + ea["unit"], tgt_phrase=tgt[eb["s"]:eb["e"]] + " " + eb["unit"],
                        context_de=ctx(de, ea), context_tgt=ctx(tgt, eb)))
    return out


def unit_one_sided(de, tgt, lang):
    """diagnostic, not a finding: a shared value whose unit classes differ in one direction only (DE '12 Wochen' and
    '12 Monate', FR only '12 semaines'); repetition and moved values make these unreliable (cf. R5)."""
    de, tgt = nrm(de), nrm(tgt); A, B = values(de, "de"), values(tgt, lang); out = []
    for v in sorted(set(x["v"] for x in A) & set(x["v"] for x in B)):
        ca = set(_ucls(x["unit"], "de") for x in A if x["v"] == v) - {None}; cb = set(_ucls(x["unit"], lang) for x in B if x["v"] == v) - {None}
        oa, ob = ca - cb, cb - ca
        if ca and cb and bool(oa) != bool(ob) and any(DIM[c] in set(DIM[k] for k in ca & cb) for c in oa | ob):
            out.append(dict(value=v, de_units=sorted(ca), tgt_units=sorted(cb)))
    return out


def editorial(text, L, st=None):
    """Conservative typo rules on one text. -> [dict(rule, surface, suggestion, values, context)].
    E1 stray space inside a decimal before a unit: '1 .4 mmol/l' -> '1.4'.
    E2 a preposition glued to a number before a unit: 'de15 kg' -> 'de 15'.
    E3 a number glued to a time word: '4Wochen' -> '4 Wochen'.
    E4 one edit from a number word 2..12, right before a unit word, where the corrected word trigram (previous word,
       number word, unit word) is in >= 5 register texts and the observed one in <= 2: 'almeno se mesi' -> 'sei'.
    E5 a word after a number that is in < 3 register texts, follows a number in < 2, and is one edit from a unit word
       that follows a number in >= 20 register texts: '6 Monte' -> 'Monate'.
    E4 and E5 need the register statistics (st)."""
    t = nrm(text); out = []; urx = UNIT_RX[L]

    def add(rule, m, sug, vals):
        x = dict(s=m.start(), e=m.end())
        out.append(dict(rule=rule, surface=m.group(0), suggestion=sug, values=vals, context=ctx(t, x, 50)))
    for m in re.finditer(r"(?<![\d.,'’])(\d+) ([.,])(\d+)(?![\d])", t):
        if urx.match(t, m.end()): add("E1", m, m.group(1) + m.group(2) + m.group(3), [canon(m.group(1) + "." + m.group(3))[0], m.group(1), m.group(3)])
    preps = set(PREP[L].split()) | set(_FW_RAW[L].split())
    for m in re.finditer(r"(?<![\w])([^\W\d_]{1,})(\d+(?:[.,]\d+)?)(?![\w])", t):
        if m.group(1) in preps and urx.match(t, m.end()):
            add("E2", m, m.group(1) + " " + m.group(2), [canon(m.group(2))[0]])
    for m in re.finditer(r"(?<![\w.,])(\d+)(" + TIMEW[L] + r")(?![\w])", t, flags=re.I):
        add("E3", m, m.group(1) + " " + m.group(2), [m.group(1)])
    if not st: return out
    nw = NUMW[L][2:]; U = st["utri"][L]
    toks = [(m.group(0).lower(), m.start(), m.end()) for m in WORD.finditer(t)]
    for (p, _, _), (w, ws_, we), (u, us, ue) in zip(toks, toks[1:], toks[2:]):
        if w in nw or not _is_unit_word(u, L) or t[we:us].strip(): continue
        for n in nw:
            if lev1(w, n) and U.get(p + " " + n + " " + u, 0) >= E4_MIN and U.get(p + " " + w + " " + u, 0) <= E4_MAX:
                m = re.compile(re.escape(t[ws_:ue])).search(t, ws_)
                add("E4", m, n + " " + t[us:ue], [str(nw.index(n) + 2)]); break
    A, Vc = st["after"][L], st["_vocab"][L]
    for m in re.finditer(r"(?<![\w.,])(\d+(?:[.,]\d+)?)\s([^\W\d_]{4,})(?![\w])", t):
        w = m.group(2).lower()
        if w in Vc or A.get(w, 0) >= 2: continue
        c = sorted((u for u, k in A.items() if k >= E5_MIN and lev1(w, u) and _is_unit_word(u, L)), key=lambda u: -A[u])
        if c: add("E5", m, m.group(1) + " " + c[0], [canon(m.group(1))[0]])
    return out
# ------------------------------------------------------------------ END OF ROUND-3 RULES


LOC = {"lang": {"fr": "l'ancien texte français est en {x}", "it": "il vecchio testo italiano è in {x}",
                "de": "der alte deutsche Text ist auf {x}"},
       "lname": {"fr": {"de": "allemand", "fr": "français", "it": "italien", "en": "anglais"},
                 "it": {"de": "tedesco", "fr": "francese", "it": "italiano", "en": "inglese"},
                 "de": {"de": "Deutsch", "fr": "Französisch", "it": "Italienisch", "en": "Englisch"}},
       "edit": {"fr": "coquille probable dans l'ancien texte{w} : «{s}» (sans doute «{g}»)",
                "it": "probabile refuso nel vecchio testo{w}: «{s}» (forse «{g}»)",
                "de": "wahrscheinlicher Tippfehler im alten Text{w}: «{s}» (wohl «{g}»)"},
       "edit_de": {"fr": " allemand", "it": " tedesco", "de": " (Deutsch)"}}


def audit_item(x, stats=None, kinds=("number", "unit", "language", "editorial")):
    """For the review UI: pre-existing problems of an item's old texts. x: dict with de_old, tgt_old, lang.
    -> [] or a list of dicts, each with kind ('number'|'unit'|'language'|'editorial'), lang, detail (one English
    sentence), values (optional), odd_one_out (optional), and 'text' (one phrase in the item's language).
    Number findings keep the round-2 shape (side 'de'|lang, value, n, unit, src, context); unit findings carry the same
    keys for the target side. Language findings judge the old target only; editorial findings both old texts.
    stats: register statistics (default: the shipped data/audit/lang_stats_20261006.json.gz)."""
    L = x["lang"]; st = _prep(stats) if stats is not None else load_stats(); out = []
    T = {"fr": "French", "it": "Italian"}.get(L, L)
    if "number" in kinds:
        r = compare(x["de_old"], x["tgt_old"], L)
        for y in r["de_only"]:
            out.append(dict(kind="number", lang=L, side="de", values=[y["value"]],
                            detail=f"The old German has {y['value']} ({y['unit']}); the old {T} does not.", **y))
        for y in r["tgt_only"]:
            out.append(dict(kind="number", lang=L, side=L, values=[y["value"]],
                            detail=f"The old {T} has {y['value']} ({y['unit']}); the old German does not.", **y))
    if "unit" in kinds:
        for u in unit_diff(x["de_old"], x["tgt_old"], L):
            out.append(dict(kind="unit", lang=L, side=L, value=u["tgt_phrase"], unit=u["tgt_unit"], context=[u["context_tgt"]],
                            values=[u["value"]], de_context=u["context_de"],
                            detail=f"Both old texts have {u['value']}, but the German says {UWORD[u['de']]} ({u['de_phrase']}) "
                                   f"and the {T} says {UWORD[u['tgt']]} ({u['tgt_phrase']})."))
    if "language" in kinds:
        dw = set(words(nrm(x["de_old"]))); tw = words(nrm(x["tgt_old"]))
        sh = dw if len([w for w in tw if w not in dw]) >= 0.5 * len(tw) else set()
        r = lang_check(nrm(x["tgt_old"]), L, sh, st)
        if r["detected"] != L:
            X = r["detected"]
            out.append(dict(kind="language", lang=L, detected=X, odd_one_out=L, fw=r["fw"], margin=r["margin"],
                            detail=f"The old {T} text is written in {NAME[X]}.",
                            text=LOC["lang"][L].format(x=LOC["lname"][L][X])))
    if "editorial" in kinds:
        for side, txt in (("de", x["de_old"]), (L, x["tgt_old"])):
            for e in editorial(txt, side, st):
                out.append(dict(kind="editorial", lang=side, rule=e["rule"], surface=e["surface"], suggestion=e["suggestion"],
                                values=e["values"], context=[e["context"]],
                                detail=f"Probable typo in the old {NAME[side]} text: '{e['surface']}' (likely '{e['suggestion']}').",
                                text=LOC["edit"][L].format(w=LOC["edit_de"][L] if side == "de" else "", s=e["surface"], g=e["suggestion"])))
    return out


# ------------------------------------------------------------------ the whole snapshot
def half(i): return "dev" if int(hashlib.md5(i.encode()).hexdigest(), 16) % 2 == 0 else "held"


def load(hist, date):
    J = {L: json.load(open(os.path.join(hist, f"{date}-{L}.json"), encoding="utf-8")) for L in ("de", "fr", "it")}
    if any(k.startswith("RA:") for k in J["de"]["lim"]):
        # old format (to April 2026): RA ids differ per language; align FR/IT to DE by (product, position), as sl.mine.tkey
        for L in ("fr", "it"):
            m = {}
            for pid, p in J["de"]["prod"].items():
                kt = J[L]["prod"].get(pid, {}).get("keys", [])
                if len(kt) == len(p["keys"]): m.update(zip(kt, p["keys"]))
            J[L] = dict(J[L], lim={m[k]: t for k, t in J[L]["lim"].items() if k in m})
    names = defaultdict(list)
    for p in J["de"]["prod"].values():
        for k in p["keys"]: names[k].append(p["name"])
    return J, names


def run(hist, date, J=None, names=None):
    if J is None: J, names = load(hist, date)
    F, cnt, unb, sup = [], 0, 0, Counter()
    for i in sorted(J["de"]["lim"]):
        de = J["de"]["lim"][i]
        for L in ("fr", "it"):
            t = J[L]["lim"].get(i)
            if t is None: continue
            r = compare(de, t, L); cnt += len(r["count"]); unb += r["unbound"]; sup.update(r["suppressed"])
            if not (r["de_only"] or r["tgt_only"]): continue
            g = hashlib.sha1((nrm(de) + "\0" + nrm(t)).encode()).hexdigest()[:10]
            F.append(dict(id=i, product=sorted(set(n.split(" ")[0] for n in names.get(i, [])))[:3], lang=L, kind="number",
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


def _third(L): return "it" if L == "fr" else "fr"


def _has(text, lang, v):
    return any(x["v"] == v or x["alt"] == v for x in values(nrm(text), lang))


def odd_number(f, J):
    """majority vote of the three texts for a DE<->L number finding: which language is the odd one out (None: mixed)."""
    i, L = f["id"], f["lang"]; M = _third(L); tm = J[M]["lim"].get(i)
    if tm is None: return None, M
    dm = set(x["value"] for x in compare(J["de"]["lim"][i], tm, M)["de_only"])
    votes = set()
    for x in f["de_only"]: votes.add("de" if x["value"] in dm else L)
    for x in f["tgt_only"]: votes.add("de" if _has(tm, M, x["value"]) else L)
    return (votes.pop() if len(votes) == 1 else None), M


def run_all(hist, date, J=None, names=None, st=None):
    """every kind on one snapshot -> (findings, number stats, extra stats). Number findings are exactly run()'s."""
    if J is None: J, names = load(hist, date)
    F, S = run(hist, date, J, names)
    st = _prep(st or build_stats(J))
    pname = lambda i: sorted(set(n.split(" ")[0] for n in names.get(i, [])))[:3]
    for f in F:
        f["fid"] = f"N{f['rank']:02d}"; f["languages"] = ["de", f["lang"]]
        f["odd_one_out"], f["third"] = odd_number(f, J); f["suggested_action"] = None
        f["context"] = [c for x in f["de_only"] + f["tgt_only"] for c in x["context"][:1]]
    U, Lg, E, one = [], [], [], []; judged = Counter(); short = Counter()
    for i in sorted(J["de"]["lim"]):
        T = {L: nrm(J[L]["lim"].get(i) or "") for L in LANGS}; W = {L: set(words(T[L])) for L in LANGS}
        det = {}
        for L in LANGS:
            if not T[L]: continue
            o = [M for M in LANGS if M != L]
            r = lang_check(T[L], L, W[o[0]] & W[o[1]], st); det[L] = r
            (judged if r["judged"] else short)[L] += 1
        for L in LANGS:
            if L not in det or det[L]["detected"] == L: continue
            X = det[L]["detected"]; r = det[L]
            agree = [M for M in LANGS if M != L and M in det and (det[M]["detected"] == X or M == X)]
            same = [M for M in LANGS if M != L and T[M] == T[L]]
            Lg.append(dict(id=i, product=pname(i), lang=L, kind="language", detected=X, languages=[L, X], odd_one_out=L,
                           agrees_with=agree, identical_to=same, fw=r["fw"], margin=r["margin"], ntri=r["ntri"], half=half(i),
                           context=[T[L][:160] + ("…" if len(T[L]) > 160 else "")],
                           description=f"The {NAME[L]} field is written in {NAME[X]}" + (f" (identical to the {', '.join(NAME[M] for M in same)} text)" if same else "")
                                       + f"; function words {X}={r['fw'].get(X, 0)} vs {L}={r['fw'].get(L, 0)}"
                                       + (f", trigram margin {r['margin']}" if r["margin"] is not None else "") + ".",
                           suggested_action=None))
        for L in ("fr", "it"):
            if not T[L] or det.get(L, {}).get("detected", L) != L: continue      # a text in the wrong language: see 'language'
            M = _third(L)
            for u in unit_one_sided(T["de"], T[L], L): one.append(dict(id=i, lang=L, **u))
            for u in unit_diff(T["de"], T[L], L):
                cm = set(_ucls(x["unit"], M) for x in values(T[M], M) if x["v"] == u["value"]) if T[M] else set()
                odd = L if u["de"] in cm and u["tgt"] not in cm else "de" if u["tgt"] in cm and u["de"] not in cm else None
                U.append(dict(id=i, product=pname(i), lang=L, kind="unit", languages=["de", L], odd_one_out=odd, third=M,
                              half=half(i), value=u["value"], de_unit=u["de_unit"], tgt_unit=u["tgt_unit"],
                              context=[u["context_de"], u["context_tgt"]],
                              description=f"Both texts have {u['value']}, but DE says {UWORD[u['de']]} ({u['de_phrase']}) and "
                                          f"{L.upper()} says {UWORD[u['tgt']]} ({u['tgt_phrase']}).", suggested_action=None))
        for L in LANGS:
            if not T[L] or det.get(L, {}).get("detected", L) != L: continue
            for e in editorial(T[L], L, st):
                others = [M for M in LANGS if M != L and T[M] and _has(T[M], M, e["values"][0])]
                E.append(dict(id=i, product=pname(i), lang=L, kind="editorial", languages=[L], odd_one_out=L if len(others) == 2 else None,
                              rule=e["rule"], surface=e["surface"], suggestion=e["suggestion"], values=e["values"],
                              others_have_value=others, half=half(i), context=[e["context"]],
                              description=f"Probable typo in the {NAME[L]} text: '{e['surface']}' (likely '{e['suggestion']}', rule {e['rule']}).",
                              suggested_action=None))
    Lg.sort(key=lambda f: (-(f["margin"] or 0), f["id"], f["lang"]))
    U.sort(key=lambda f: (f["id"], f["lang"], f["value"]))
    E.sort(key=lambda f: (f["rule"], f["id"], f["lang"], f["surface"]))
    for pre, G in (("L", Lg), ("U", U), ("E", E)):
        for n, f in enumerate(G): f["rank"] = n + 1; f["fid"] = f"{pre}{n + 1:02d}"
    ed = {}
    for e in E: ed.setdefault(e["id"], []).append(e)
    for f in F:                                     # a number finding that an editorial defect explains (LEQVIO '1 .4')
        vs = set(x["value"] for x in f["de_only"] + f["tgt_only"])
        f["explained_by"] = [e["fid"] for e in ed.get(f["id"], []) if e["lang"] in ("de", f["lang"]) and vs & set(e["values"])]
    X = dict(language_fields_judged=dict(judged), language_fields_too_short=dict(short), unit_one_sided=one)
    return F + U + Lg + E, S, X


def fkeys(f):
    """identity of a finding across snapshots (for dating): by limitation id, and by content (the early 2026 snapshots
    use other limitation ids, 'RA:<uuid>#n'), so a finding counts as present when either matches."""
    k = (f["lang"], f["kind"])
    if f["kind"] == "number":
        sig = (tuple(sorted(x["value"] for x in f["de_only"])), tuple(sorted(x["value"] for x in f["tgt_only"])))
        con = tuple(sorted(c for x in f["de_only"] + f["tgt_only"] for c in x["context"][:1]))
    elif f["kind"] == "unit": sig = (f["value"], f["de_unit"], f["tgt_unit"]); con = tuple(f["context"])
    elif f["kind"] == "language": sig = (f["detected"],); con = (f["context"][0],)
    else: sig = (f["rule"], f["surface"]); con = (f["context"][0],)
    return [("id", f["id"]) + k + sig, ("text",) + k + sig + con]


def snapshots(hist, upto):
    """usable snapshots of the same year up to `upto`: all three languages present."""
    ds = sorted(set(f.split("-")[0] for f in os.listdir(hist) if re.fullmatch(r"\d{8}-(de|fr|it)\.json", f)))
    return [d for d in ds if d[:4] == upto[:4] and d <= upto and all(os.path.exists(os.path.join(hist, f"{d}-{L}.json")) for L in LANGS)]


def date_findings(F, hist, date, st=None):
    """first snapshot (of the usable ones of the year) in which each finding appears, and in how many it appears. The
    earlier snapshots are checked with the register statistics of `date` (st), so a defect is dated by its presence,
    not by when the register counts crossed a threshold."""
    seen = defaultdict(list); ds = snapshots(hist, date); per, lang_any = {}, {}
    for d in ds:
        G = F if d == date else run_all(hist, d, st=st)[0]
        per[d] = {k: sum(g["kind"] == k for g in G) for k in ("number", "unit", "language", "editorial")}
        for g in G:
            if g["kind"] == "language":
                e = lang_any.setdefault((g["id"], g["lang"], g["detected"]), dict(id=g["id"], product=g["product"], lang=g["lang"],
                                                                                  detected=g["detected"], snapshots=[]))
                e["snapshots"].append(d)
            for k in fkeys(g):
                if not seen[k] or seen[k][-1] != d: seen[k].append(d)
    for f in F:
        s = sorted(set(d for k in fkeys(f) for d in seen.get(k, []))) or [date]; f["first_seen"] = s[0]; f["seen_in"] = len(s)
    return dict(snapshots=ds, per_snapshot=per, language_any_snapshot=list(lang_any.values()))


QUESTION = {
    "language": "Is the text of field 'lang' written (predominantly) in a language other than the one that field should "
                "hold? Answer real / minor (only partly) / not.",
    "unit": "Do the German and the 'lang' text attach a different unit to the value named in 'finding' (a different "
            "condition)? Answer real / minor / not (same condition: conversion, different place, parser artefact).",
    "editorial": "Is the passage named in 'finding' a typing or formatting error in the 'lang' text that BAG would want "
                 "fixed? Answer real / minor (cosmetic) / not (correct as written, or parser artefact)."}


def worklist_new(F, hist, date, d):
    """all non-number findings, shuffled (seed), blind: no rank, no rule names, no first-seen date."""
    J, _ = load(hist, date)
    pool = [f for f in F if f["kind"] != "number"]
    S = random.Random(SEED + 1).sample(pool, len(pool))
    os.makedirs(d, exist_ok=True); W, K = [], {}; w = 2 if len(S) <= 100 else 3
    for j, f in enumerate(S):
        b = f"B{j:0{w}d}"
        W.append(dict(id=b, kind=f["kind"], lang=f["lang"], de=nrm(J["de"]["lim"][f["id"]]), fr=nrm(J["fr"]["lim"].get(f["id"]) or ""),
                      it=nrm(J["it"]["lim"].get(f["id"]) or ""), finding=re.sub(r",? ?rule E\d\)", ")", f["description"]),
                      question=QUESTION[f["kind"]]))
        K[b] = dict(cud=f["id"], fid=f["fid"], kind=f["kind"], lang=f["lang"], rank=f["rank"], half=f["half"],
                    rule=f.get("rule"), detected=f.get("detected"), first_seen=f.get("first_seen"))
    json.dump(W, open(os.path.join(d, "worklist.json"), "w"), ensure_ascii=False, indent=1)
    json.dump(K, open(os.path.join(d, "key_map_DO_NOT_SHOW.json"), "w"), ensure_ascii=False, indent=1)
    return len(pool)


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


def fresh(items, st=None):
    """audit_item on every item of a set (old texts). An item counts as having a pre-existing divergence when it has a
    number, unit or language finding; editorial findings are counted separately."""
    X = json.load(open(items, encoding="utf-8")); hits = []
    for x in X:
        r = audit_item(x, stats=st)
        if r: hits.append(dict(key=x["key"], lang=x["lang"], kinds=sorted(set(f["kind"] for f in r)), findings=r))
    div = [h for h in hits if set(h["kinds"]) & {"number", "unit", "language"}]
    by = {k: sorted(h["key"] for h in hits if k in h["kinds"]) for k in ("number", "unit", "language", "editorial")}
    return dict(items=len(X), with_preexisting=len(div), with_language_or_number=len(div),
                with_editorial=len(by["editorial"]), with_any=len(hits),
                pairs=len(set(h["key"].split("-")[0] for h in div)), by_kind=by, hits=hits)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="gleichlaut.audit", description=__doc__.split("\n\n")[0])
    ap.add_argument("--hist", help="snapshot dir (default: $GLEICHLAUT_HIST or track_2b/out/hist)")
    ap.add_argument("--date", default="20261006")
    ap.add_argument("--out", default=DEST)
    ap.add_argument("--items", default=os.path.join(core.ROOT, "data", "items", "items_fresh.json"))
    ap.add_argument("--worklist", help="write the blind round-2 worklist (number findings) + key map to this dir")
    ap.add_argument("--worklist-new", help="write the blind round-3 worklist (all unit/language/editorial findings) + key map")
    ap.add_argument("--no-dating", action="store_true", help="skip the run over the earlier snapshots of the year")
    a = ap.parse_args(argv)
    H = hist_dir(a.hist)
    if not os.path.exists(os.path.join(H, f"{a.date}-de.json")): sys.exit(f"no snapshot {a.date} in {H}")
    J, names = load(H, a.date); st = build_stats(J)
    ALL, S, XS = run_all(H, a.date, J, names, st)
    F = [f for f in ALL if f["kind"] == "number"]
    R = recall(F)
    DT = dict(snapshots=[a.date]) if a.no_dating else date_findings(ALL, H, a.date, st); ds = DT["snapshots"]
    os.makedirs(a.out, exist_ok=True)
    import gzip
    sp = os.path.join(a.out, f"lang_stats_{a.date}.json.gz")
    with gzip.GzipFile(sp, "wb", mtime=0) as g: g.write(json.dumps({k: v for k, v in st.items() if k != "_vocab"}, ensure_ascii=False, sort_keys=True).encode("utf-8"))
    fr = fresh(a.items, st) if a.items and os.path.exists(a.items) else None
    terms = dict(status="off: not precise enough (docs/audit.md)", fr=term_pairs(J, "fr"), it=term_pairs(J, "it"),
                 probe=term_probe(J))
    K = Counter(f["kind"] for f in ALL)
    kt = [f for f in ALL if f["id"] == KNOWN_BONUS]
    summ = dict(generated_by="python3 -m gleichlaut.audit --hist <dir> --date " + a.date, date=a.date, model_calls=0,
                findings=len(F), findings_note="'findings' counts the number findings (round 2); all kinds: by_kind",
                by_kind={k: K.get(k, 0) for k in ("number", "unit", "language", "editorial")},
                by_kind_lang={k: dict(Counter(f["lang"] for f in ALL if f["kind"] == k)) for k in ("number", "unit", "language", "editorial")},
                editorial_by_rule=dict(sorted(Counter(f["rule"] for f in ALL if f["kind"] == "editorial").items())),
                findings_all=len(ALL), limitations_with_any_finding=len(set(f["id"] for f in ALL)),
                by_lang=dict(Counter(f["lang"] for f in F)), by_half=dict(Counter(f["half"] for f in F)),
                limitations_with_finding=len(set(f["id"] for f in F)), distinct_text_pairs=len(set(f["group"] for f in F)),
                swaps=sum(1 for f in F if f["score"] >= 11), **S, **XS,
                number_explained_by_editorial={f["fid"]: f["explained_by"] for f in F if f["explained_by"]},
                recall=dict(limitations=sum(r["hit"] for r in R.values()), of=len(R),
                            tests=sum(t["hit"] for r in R.values() for t in r["tests"]),
                            of_tests=sum(len(r["tests"]) for r in R.values()), cases=R),
                keytruda_bonus=dict(found=any(f["kind"] == "language" for f in kt), findings=[
                    dict(fid=f["fid"], kind=f["kind"], lang=f["lang"], detected=f.get("detected"), first_seen=f.get("first_seen")) for f in kt]),
                language_findings=[dict(fid=f["fid"], id=f["id"], product=f["product"], lang=f["lang"], detected=f["detected"],
                                        identical_to=f["identical_to"], first_seen=f.get("first_seen"), seen_in=f.get("seen_in"))
                                   for f in ALL if f["kind"] == "language"],
                snapshots_dated=ds, per_snapshot=DT.get("per_snapshot"), language_any_snapshot=DT.get("language_any_snapshot"),
                first_seen_by_kind={k: dict(sorted(Counter(f.get("first_seen") for f in ALL if f["kind"] == k).items()))
                                                        for k in ("number", "unit", "language", "editorial")},
                stats_file=os.path.relpath(sp, core.ROOT) if sp.startswith(core.ROOT) else sp,
                s1_census_reference=dict(precision="3/50 = 6% (all categories)", num="3/15 = 20% strict",
                                         source="spikes/gleichlaut/results.md (research, not shipped)"),
                term_pairs=terms,
                fresh=dict((k, v) for k, v in fr.items() if k != "hits") if fr else None)
    json.dump(dict(summary=summ, findings=ALL, fresh_items=fr["hits"] if fr else None),
              open(os.path.join(a.out, f"audit_{a.date}.json"), "w"), ensure_ascii=False, indent=0)
    if a.worklist: summ["worklist"] = dict(zip(("pool", "n"), worklist(F, H, a.date, a.worklist)))
    if a.worklist_new: summ["worklist_new"] = dict(pool=worklist_new(ALL, H, a.date, a.worklist_new))
    json.dump(summ, open(os.path.join(a.out, f"audit_{a.date}_summary.json"), "w"), ensure_ascii=False, indent=1)
    print(f"{len(ALL)} findings {summ['by_kind']} on {summ['limitations_with_any_finding']} of {S['n_limitations']} limitations; "
          f"recall {summ['recall']['limitations']}/{len(R)} known limitations; Keytruda {'found' if summ['keytruda_bonus']['found'] else 'not found'}; "
          f"fresh items with a language/number problem: {fr['with_language_or_number'] if fr else '-'} of {fr['items'] if fr else '-'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
