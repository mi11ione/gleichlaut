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
Round 4 (pre-registered block 'round 4'):
  terminology  the target still says a phrase that BAG itself replaced, for the same German term, in >= 2 other
               limitations (pairs mined from consecutive snapshots + recorded amendments; data/audit/term_pairs_<date>.json)
  likely_equivalent / equivalence  a triage field on number findings (Q1-Q5, typo link); never changes ids, ranks, counts
  --list migel|al --file PATH  the same checks on MiGeL / Analysenliste xlsx (gleichlaut.audit_lists)

usage: python3 -m gleichlaut.audit [--hist DIR] [--date 20261006] [--out data/audit] [--items data/items/items_fresh.json]
                                   [--worklist DIR] [--worklist-new DIR] [--worklist-terms DIR] [--no-dating]
                                   [--terms FILE] [--fail-on-findings]
       python3 -m gleichlaut.audit --list migel|al --file PATH [--date D] [--out data/audit] [--worklist DIR]"""
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


def compare(de, tgt, lang, bind_words=False):
    """DE text vs one target text -> dict(de_only=[...], tgt_only=[...], count=[...], unbound=n, suppressed={rule: n}).
    bind_words (round 5, number_word only): a value written as a number word counts as bound (R2) and carries its offsets."""
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
            b = [x for x in xs if x["unit"] or (bind_words and x["src"] == "word")]
            if not b: unb += 1; continue
            res.append(dict(value=v, n=len(xs), unit=b[0]["unit"] or ("word" if bind_words else None), src=b[0]["src"], context=[ctx(text, x) for x in xs[:3]]))
            if bind_words: res[-1]["spans"] = [(x["s"], x["e"]) for x in xs]
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


# ================================================================== round 4: terminology, likely_equivalent (PRE-REGISTERED)
# Written in full before the first run on any snapshot (docs/audit.md, 'Round 4'). Thresholds are a-priori choices.
#
# TERMINOLOGY from BAG's own corrections. Sources of corrections: consecutive usable snapshots (limitations aligned by
# product and position, as load() does across languages) and, optionally, a recorded set of BAG amendments
# (old/new DE and target texts, e.g. data/items/items_fresh.json, Jul 2025 -> Feb 2026).
#   T1 an edit is a token 'replace' between the old and the new target text (words lower-cased, ’ = ', punctuation
#      ignored) of 1..8 tokens on each side, with no digit, a word of >= 3 letters on each side, not an accent-only
#      change and not a one-word inflection (same first 4 letters). A text pair whose target token similarity is
#      < 0.5 is a retranslation, not a correction: no edits are taken from it.
#   T2 the German does not explain it: the German is unchanged, or it changed (similarity >= 0.5) only at places whose
#      relative position is more than 0.15 away from the target edit.
#   T3 a pair (lang, old, new) is kept when BAG applied it in >= 2 limitations (distinct new German texts) or in >= 2
#      snapshot transitions, and the reverse edit (new -> old) never occurs.
#   T4 the German term: the German word stems (lower-cased word or hyphen compound, one inflection suffix removed,
#      >= 6 letters, not a function word, not a word of the target text) present in the old and the new German of every
#      instance; the one with the highest Dice coefficient between 'stem in the German' and 'old or new phrase in the
#      target' over the distinct text pairs of the current register. Kept when Dice >= 0.5.
#   T5 the phrases are extended by the context tokens (up to 3 each side) that all instances share, so the matched
#      phrase is as specific as BAG's own corrections.
#   T6 flag: a current text whose target contains the old phrase, whose German contains the German term, and whose
#      target has fewer occurrences of the new phrase than the German has of the term.
TERM_MAXTOK, TERM_SIM, TERM_POS, TERM_MIN, TERM_MINLEN, TERM_DICE, TERM_CTX = 8, 0.5, 0.15, 2, 6, 0.5, 3
TERMS = os.path.join(DEST, "term_pairs_20261006.json")
TTOK = re.compile(r"[^\W\d_]+(?:['’][^\W\d_]+)*|\d+(?:[.,'’]\d+)*")
DTOK = re.compile(r"[^\W\d_]\w*(?:-\w+)*")


def ttoks(t): return [w.lower().replace("’", "'") for w in TTOK.findall(nrm(t or ""))]


def dstem(w):
    w = w.lower()
    for s in ("en", "es", "er", "n", "e", "s"):
        if w.endswith(s) and len(w) - len(s) >= 4: return w[:-len(s)]
    return w


def dstems(t): return Counter(dstem(w) for w in DTOK.findall(nrm(t or "")))


def _deacc(ws):
    import unicodedata
    return tuple("".join(c for c in unicodedata.normalize("NFD", w) if not unicodedata.combining(c)) for w in ws)


def term_edits(de0, t0, de1, t1):
    """T1+T2: BAG's target edits between two versions that the German does not explain -> [dict(old, new, l, r, nl, nr)]."""
    from difflib import SequenceMatcher
    a, b = ttoks(t0), ttoks(t1)
    if a == b: return []
    sm = SequenceMatcher(None, a, b, autojunk=False)
    if sm.ratio() < TERM_SIM: return []
    da, db = [w.lower() for w in DTOK.findall(nrm(de0 or ""))], [w.lower() for w in DTOK.findall(nrm(de1 or ""))]
    dch = []
    if da != db:
        dm = SequenceMatcher(None, da, db, autojunk=False)
        if dm.ratio() < TERM_SIM: return []
        n = max(1, len(db)); dch = [(j1 / n, j2 / n) for o, i1, i2, j1, j2 in dm.get_opcodes() if o != "equal"]
    out, nb = [], max(1, len(b))
    for o, i1, i2, j1, j2 in sm.get_opcodes():
        if o != "replace": continue
        old, new = tuple(a[i1:i2]), tuple(b[j1:j2])
        if not (1 <= len(old) <= TERM_MAXTOK and 1 <= len(new) <= TERM_MAXTOK): continue
        if any(re.search(r"\d", w) for w in old + new): continue
        if not (any(re.search(r"[^\W\d_]{3}", w) for w in old) and any(re.search(r"[^\W\d_]{3}", w) for w in new)): continue
        if _deacc(old) == _deacc(new) or (len(old) == len(new) == 1 and old[0][:4] == new[0][:4]): continue
        c, d = j1 / nb, j2 / nb
        if any(x <= d + TERM_POS and y >= c - TERM_POS for x, y in dch): continue
        out.append(dict(old=old, new=new, l=tuple(a[max(0, i1 - TERM_CTX):i1]), r=tuple(a[i2:i2 + TERM_CTX]),
                        nl=tuple(b[max(0, j1 - TERM_CTX):j1]), nr=tuple(b[j2:j2 + TERM_CTX])))
    return out


def _common(seqs, left):
    """the longest context shared by all instances (suffix of the left contexts, prefix of the right ones)."""
    out = []
    for k in range(1, TERM_CTX + 1):
        xs = set((s[-k:] if left else s[:k]) if len(s) >= k else None for s in seqs)
        if len(xs) != 1 or None in xs: break
        out = list(xs.pop())
    return tuple(out)


def _phr(ws): return " " + " ".join(ws) + " "


def _surface(text, phrase):
    """the phrase (token tuple) as written in text, or None."""
    rx = r"(?<![\w])" + r"[\W_]+".join(re.escape(w).replace("'", "['’]") for w in phrase) + r"(?![\w])"
    m = re.search(rx, nrm(text or ""), flags=re.I)
    return m


def term_units(hist, ds, load_fn=None):
    """aligned (d0, d1, id1, lang, de0, t0, de1, t1) over consecutive snapshots: by product and position (the ids of the
    early 2026 snapshots change from one snapshot to the next), and by id where the id is kept."""
    load_fn = load_fn or load
    prev = None
    for d in ds:
        J, _ = load_fn(hist, d)
        if prev is not None:
            d0, J0 = prev; m = {}
            for pid, p in J["de"]["prod"].items():
                q = J0["de"]["prod"].get(pid)
                if q and len(q["keys"]) == len(p["keys"]): m.update(zip(p["keys"], q["keys"]))
            for k in J["de"]["lim"]:
                if k in J0["de"]["lim"]: m[k] = k
            seen = set()
            for k1, k0 in sorted(m.items()):
                if k1 not in J["de"]["lim"] or k0 not in J0["de"]["lim"]: continue
                for L in ("fr", "it"):
                    t0, t1 = J0[L]["lim"].get(k0), J[L]["lim"].get(k1)
                    if not t0 or not t1: continue
                    u = (L, nrm(J0["de"]["lim"][k0]), nrm(t0), nrm(J["de"]["lim"][k1]), nrm(t1))
                    if u in seen or u[2] == u[4]: continue
                    seen.add(u); yield dict(d0=d0, d1=d, id=k1, lang=L, de0=u[1], t0=u[2], de1=u[3], t1=u[4], source="snapshots")
        prev = (d, J)


def item_units(items):
    """recorded BAG amendments (old/new German and target text) as correction units."""
    for x in items:
        if x.get("tgt_old") and x.get("tgt_new") and x.get("de_new") is not None:
            yield dict(d0=x.get("snap_old"), d1=x.get("snap_new"), id=x.get("code_new") or x.get("key"), lang=x["lang"],
                       de0=nrm(x["de_old"]), t0=nrm(x["tgt_old"]), de1=nrm(x["de_new"]), t1=nrm(x["tgt_new"]),
                       source="items:" + str(x.get("key")))


def mine_terms(units, J):
    """T3-T5 over the correction units; J = the current register (for the Dice of T4). -> list of pairs."""
    inst = defaultdict(list)
    for u in units:
        for e in term_edits(u["de0"], u["t0"], u["de1"], u["t1"]): inst[(u["lang"], e["old"], e["new"])].append((u, e))
    reg = {}
    for L in ("fr", "it"):
        if L not in J: reg[L] = []; continue
        reg[L] = [(set(dstems(J["de"]["lim"][i])), _phr(ttoks(J[L]["lim"][i]))) for i in sorted(J["de"]["lim"]) if J[L]["lim"].get(i)]
        reg[L] = list({(frozenset(s), t): None for s, t in reg[L]})
    P = []
    for (L, old, new), xs in sorted(inst.items()):
        if (L, new, old) in inst: continue
        nlim = len(set(u["de1"] for u, _ in xs)); nsnap = len(set((u["d0"], u["d1"]) for u, _ in xs))
        if nlim < TERM_MIN and nsnap < TERM_MIN: continue
        op = _common([e["l"] for _, e in xs], True) + old + _common([e["r"] for _, e in xs], False)
        np_ = _common([e["nl"] for _, e in xs], True) + new + _common([e["nr"] for _, e in xs], False)
        cand = None
        for u, _ in xs:
            s = set(dstems(u["de0"])) & set(dstems(u["de1"]))
            tw = set(ttoks(u["t0"])) | set(ttoks(u["t1"])); tw |= {dstem(w) for w in tw}       # names / INNs as stems too
            s = {w for w in s if len(re.sub(r"\W", "", w)) >= TERM_MINLEN and w not in FW["de"] and w not in tw}
            cand = s if cand is None else cand & s
        if not cand: continue
        po, pn = _phr(op), _phr(np_)
        B = [po in t or pn in t for _, t in reg[L]]; nB = sum(B)
        best = None
        for w in sorted(cand):
            A = [w in s for s, _ in reg[L]]; nA = sum(A)
            if not nA or not nB: continue
            dice = 2 * sum(x and y for x, y in zip(A, B)) / (nA + nB)
            if best is None or dice > best[0]: best = (round(dice, 3), w, nA)
        if not best or best[0] < TERM_DICE: continue
        u0 = xs[0][0]
        ms, mn = _surface(u0["t0"], op), _surface(u0["t1"], np_)
        dsur = Counter(m.group(0) for u, _ in xs for m in DTOK.finditer(u["de1"]) if dstem(m.group(0)) == best[1])
        ci = sorted({(u["id"], u["d0"], u["d1"], u["source"]) for u, _ in xs})
        P.append(dict(lang=L, old=" ".join(old), new=" ".join(new), old_phrase=" ".join(op), new_phrase=" ".join(np_),
                      old_surface=ms.group(0) if ms else " ".join(op), new_surface=mn.group(0) if mn else " ".join(np_),
                      de_term=best[1], de_surface=dsur.most_common(1)[0][0] if dsur else best[1], dice=best[0],
                      de_term_texts=best[2], n_limitations=nlim, n_transitions=nsnap, n_instances=len(xs),
                      sources=sorted(set("items" if u["source"].startswith("items") else u["source"] for u, _ in xs)),
                      corrected_in=[dict(id=i, before=a, after=b, source=s) for i, a, b, s in ci]))
    P.sort(key=lambda p: (p["lang"], -p["n_limitations"], p["old_phrase"]))
    return P


def term_check(de, tgt, lang, pairs):
    """T6 on one DE/target text pair -> [(pair, match)]."""
    if not pairs: return []
    tt = _phr(ttoks(tgt)); ds = None; out = []
    for p in pairs:
        if p["lang"] != lang or _phr(p["old_phrase"].split()) not in tt: continue
        ds = ds if ds is not None else dstems(de)
        if ds.get(p["de_term"], 0) > tt.count(_phr(p["new_phrase"].split())):
            out.append((p, _surface(tgt, p["old_phrase"].split())))
    return out


def load_terms(path=TERMS):
    try: return json.load(open(path, encoding="utf-8"))["pairs"]
    except (OSError, ValueError, KeyError): return []


def _fmt_date(d):
    return f"{d[6:8]}.{d[4:6]}.{d[:4]}" if isinstance(d, str) and re.fullmatch(r"\d{8}", d) else str(d)


def term_detail(p, L):
    T = NAME[L]; c = p["corrected_in"]; last = max((x["after"] or "" for x in c), default="")
    return (f"The {T} text says '{p['old_surface']}' where BAG replaced it with '{p['new_surface']}' for the German "
            f"'{p['de_surface']}' in {p['n_limitations']} other limitation{'s' if p['n_limitations'] != 1 else ''}"
            f" (latest {_fmt_date(last)}).")


LOC_TERM = {"fr": "l'ancien texte dit «{o}» ; l'OFSP a remplacé ce terme par «{n}» (allemand «{d}») dans {k} autres limitations",
            "it": "il vecchio testo dice «{o}»; l'UFSP ha sostituito questo termine con «{n}» (tedesco «{d}») in {k} altre limitazioni",
            "de": "der alte Text sagt «{o}»; das BAG hat den Begriff in {k} anderen Limitationen durch «{n}» ersetzt (deutsch «{d}»)"}


# LIKELY EQUIVALENT (number findings; display/triage only: never changes a finding's id, rank or any count).
# A number finding is likely equivalent when a typo explains it (explained_by), or when every one-sided value has one of:
#   Q1 conversion against any value of the other text: N days = N/7 weeks, N months = N/12 years, h/d 24, min/h 60,
#      µg/mg/g 1000, ml/l 1000, ml/dl 100 ('innerhalb von 14 Tagen' = 'dans les deux semaines');
#   Q2 interval with an ordinal on the other side: 'jeden zweiten Tag' = 'tous les deux jours' = 'ogni due giorni'
#      (ordinal word of N followed, within one word, by the same time unit), 'un jour sur deux', 'giorni alterni';
#   Q3 adults: 18 years on one side, 'Erwachsene / volljährig', 'adultes / majeurs', 'adulti / maggiorenni' on the other;
#   Q4 spelled out: the other side writes N (13..100) as a word (quinze, sechzehn, diciotto, vingt ...);
#   Q5 boundary: N on one side and N +/- one step (1, or one unit of the last decimal) on the other, same unit class or
#      unit, one written inclusive (ab, mindestens, ≥, dès, au moins, almeno, bis, ≤) and the other strict (über, >,
#      plus de, oltre, unter, <, moins de, meno di).
# ('6%' vs '6 pour cent' / 'per cento' and ranges written '15–30' / 'de 15 à 30' are reconciled by R2 already.)
EQ_CONV = (("d", "w", 7), ("m", "y", 12), ("h", "d", 24), ("min", "h", 60), ("ug", "mg", 1000), ("mg", "g", 1000),
           ("g", "kg", 1000), ("ml", "l", 1000), ("ml", "dl", 100), ("dl", "l", 10))
EQ_ALT2D = {"de": r"jeden anderen Tag|alle zwei Tage", "fr": r"un jour sur (?:deux|2)", "it": r"giorni alterni|un giorno sì e uno no"}
EQ_ADULT = {"de": r"\berwachsen\w*|\bvolljährig\w*", "fr": r"\badultes?\b|\bmajeur\w*", "it": r"\badult[oi]\b|\badulte?\b|\bmaggiorenn\w*"}
EQ_NUMX = {"de": {13: "dreizehn", 14: "vierzehn", 15: "fünfzehn", 16: "sechzehn", 17: "siebzehn", 18: "achtzehn", 19: "neunzehn",
                  20: "zwanzig", 30: "dreissig|dreißig", 40: "vierzig", 50: "fünfzig", 60: "sechzig", 70: "siebzig",
                  80: "achtzig", 90: "neunzig", 100: "hundert"},
           "fr": {13: "treize", 14: "quatorze", 15: "quinze", 16: "seize", 17: "dix-sept", 18: "dix-huit", 19: "dix-neuf",
                  20: "vingt", 30: "trente", 40: "quarante", 50: "cinquante", 60: "soixante", 70: "soixante-dix",
                  80: "quatre-vingts?", 90: "quatre-vingt-dix", 100: "cent"},
           "it": {13: "tredici", 14: "quattordici", 15: "quindici", 16: "sedici", 17: "diciassette", 18: "diciotto",
                  19: "diciannove", 20: "venti", 30: "trenta", 40: "quaranta", 50: "cinquanta", 60: "sessanta",
                  70: "settanta", 80: "ottanta", 90: "novanta", 100: "cento"}}
EQ_INCL = {"de": r"(?:\bab|\bmindestens|\bmin\.|≥|>=|\bbis|\bhöchstens|\bmax\.|≤|<=)",
           "fr": r"(?:\bdès|\bà partir de|\bau moins|\bminimum|≥|>=|\bjusqu'à|\bau maximum|\bmaximum|≤|<=)",
           "it": r"(?:\bda|\ba partire da|\balmeno|\bminimo|≥|>=|\bfino a|\bal massimo|\bmassimo|≤|<=)"}
EQ_STRICT = {"de": r"(?:\büber|\bmehr als|>|\bunter|\bweniger als|\bkleiner(?: als)?|\bgrösser(?: als)?|<)",
             "fr": r"(?:\bplus de|\bsupérieure? à|>|\bmoins de|\binférieure? à|<)",
             "it": r"(?:\bpiù di|\boltre|\bsuperiore a|>|\bmeno di|\binferiore a|<)"}


def _before(text, x, n=24): return text[max(0, x["s"] - n):x["s"]].replace("’", "'")


def equivalence(value, side_lang, own, other, other_lang):
    """why one one-sided value (with its unit) is likely the same condition as the other text says; None if no rule."""
    own_t, oth_t = nrm(own), nrm(other)
    X = [x for x in values(own_t, side_lang) if x["v"] == value]; Y = values(oth_t, other_lang)
    a = _num(value)
    for x in X:
        ca = _ucls(x["unit"], side_lang)
        for y in Y:                                                                     # Q1
            b, cb = _num(y["v"]), _ucls(y["unit"], other_lang)
            if a is None or b is None or not ca or not cb: continue
            for p, q, f in EQ_CONV:
                if (ca, cb) == (p, q) and abs(a - b * f) < 1e-9 or (ca, cb) == (q, p) and abs(b - a * f) < 1e-9:
                    return f"Q1 conversion: {value} {x['unit']} = {y['v']} {y['unit']}"
        if ca in ("d", "w", "m", "y") and a is not None and a == int(a) and 2 <= a <= 12:   # Q2
            rx = r"\b(?:" + ORD[other_lang][int(a)] + r")\w*\s+(?:\w+\s+)?(?:" + TIME[other_lang][ca] + r")\b"
            m = re.search(rx, oth_t, flags=re.I) or ((int(a), ca) == (2, "d") and re.search(EQ_ALT2D[other_lang], oth_t, flags=re.I))
            if m: return f"Q2 interval: '{value} {x['unit']}' = '{m.group(0)}'"
        if value == "18" and (ca == "y" or re.search(r"lebensjahr|ans?\b|ann[oi]", x["unit"] or "", flags=re.I)):   # Q3
            m = re.search(EQ_ADULT[other_lang], oth_t, flags=re.I)
            if m: return f"Q3 adults: '{value} {x['unit']}' = '{m.group(0)}'"
        if a is not None and a == int(a) and int(a) in EQ_NUMX[other_lang]:          # Q4
            m = re.search(r"\b(?:" + EQ_NUMX[other_lang][int(a)] + r")\b", oth_t, flags=re.I)
            if m: return f"Q4 spelled out: {value} = '{m.group(0)}'"
        if a is not None and x["unit"]:                                                  # Q5
            dec = len(value.split(".")[1]) if "." in value else 0; step = 10 ** -dec
            for y in Y:
                b = _num(y["v"])
                if b is None or not y["unit"] or abs(abs(a - b) - step) > 1e-9: continue
                same = (ca and ca == _ucls(y["unit"], other_lang)) or x["unit"].lower() == y["unit"].lower()
                if not same: continue
                pa, pb = _before(own_t, x), _before(oth_t, y)
                ia = re.search(EQ_INCL[side_lang] + r"\W*$", pa, flags=re.I); sa = re.search(EQ_STRICT[side_lang] + r"\W*$", pa, flags=re.I)
                ib = re.search(EQ_INCL[other_lang] + r"\W*$", pb, flags=re.I); sb = re.search(EQ_STRICT[other_lang] + r"\W*$", pb, flags=re.I)
                if (ia and sb and not sa and not ib) or (sa and ib and not ia and not sb):
                    return f"Q5 boundary: '{pa.strip()[-12:]} {value}' = '{pb.strip()[-12:]} {y['v']}'"
    return None


def likely_equivalent(f, de, tgt):
    """-> (bool, reason) for a number finding (dict with de_only, tgt_only, lang and optionally explained_by)."""
    if f.get("explained_by"):
        return True, "typo: " + ", ".join(f["explained_by"]) + " explains the difference"
    L, rs = f["lang"], []
    for x in f.get("de_only") or []:
        r = equivalence(x["value"], "de", de, tgt, L)
        if not r: return False, None
        rs.append(r)
    for x in f.get("tgt_only") or []:
        r = equivalence(x["value"], L, tgt, de, "de")
        if not r: return False, None
        rs.append(r)
    return (True, "; ".join(rs)) if rs else (False, None)
# ------------------------------------------------------------------ END OF ROUND-4 RULES


# ================================================================== round 5: operator, negation, number_word (PREREG R15)
# Written after PREREG R15 was committed (28fe22b), on the dev half only (half() == 'dev': register texts and planted
# copies of dev limitations, tools/audit_inject.py --protocol r15 --half dev). Reported apart from the kinds above: the
# number/unit/language/editorial/terminology findings are unchanged (run_all(..., r5=False) is the default).
#
# ALIGNMENT. Each text is cut into sentences ([.;!?] or ':' + capital, not after an abbreviation or an ordinal '12.').
# German and target sentences are aligned by a monotone dynamic programme (1-1, 1-2, 2-1, skips) whose cost is the
# length ratio (scaled by the whole texts' ratio) plus the mismatch of the digit values the sentences contain. A pair is
# judged only when its cost is <= ALIGN_MAX and, if the two texts have different sentence counts, <= ALIGN_MAX_UNEVEN.
# OPERATOR (O). Every value (digits or number word) with a comparison word right before it (only articles,
# prepositions or 'insgesamt/total' between) or right after it and its unit gets a direction: 'min' (lower bound:
# mindestens, ab, über, mehr als, ≥, > ...) or 'max' (upper bound: höchstens, bis (zu), unter, weniger als, ≤, < ...).
# A value is compared when both texts state it with a direction (same count of directed occurrences); a finding when
# the directions differ ('min' against 'max'; ≥ against > is the same direction). A range end ('15 bis 30 kg') has no
# direction. Values need not be bound to a unit (R15 said 'bound to a unit'; see docs/audit.md, round 5).
# NEGATION (G). Per aligned sentence pair, strong negation (nicht, kein / ne, pas, aucun, non / non, nessuno ...) on one
# side and no negation at all on the other: neither strong nor weak (lexical or morphological negation: ohne, sans,
# senza, un-/in- adjectives, ausser, absence, refraktär, nur / ne ... que ...). Negations inside a bound idiom ('nicht
# mehr als', 'n'excédant pas', 'non più di', 'non appena') and expletive ones ('avant que ... ne', 'finché ... non')
# do not count as negation.
# NUMBER_WORD (W). Per aligned sentence pair, compare() with number words bound (bind_words): a value that one sentence
# writes as a number word (2-12; not a '-fach' compound) and the other sentence lacks, or a value on one side whose
# missing counterpart on the other side is such a word. Reconciled as compare() does, plus: an ordinal word of the value
# on the other side; DE 'beide' / FR 'les deux', 'tous deux' / IT 'entrambi', 'ambedue' for 2; equivalence() Q1-Q5. A
# value an existing number finding already names (same limitation, language, side) is not repeated.
# COUNTERPART (display only, number findings): the value the aligned sentence of the other side states instead, with the
# same unit class (Nemluvio: DE 'alle acht Wochen', IT 'ogni quattro settimane' -> IT 4).
KINDS_R5 = ("operator", "negation", "number_word")
R5_ON = {"operator": False, "negation": False, "number_word": False}     # R15 outcome (PREREG results log): no kind passed; all off
ALIGN_MAX, ALIGN_MAX_UNEVEN = 0.4, 0.2
_ABBR = (r"(?:[A-Z]|z|d|u|s|v|o|ca|bzw|max|min|resp|vgl|Nr|inkl|exkl|evtl|ggf|sog|usw|etc|Abs|Art|Ziff|lit|al|cf|ex|env|p|"
         r"c|i|e|vs|Std|Kps|Inj|Fr|ev|ecc|es|ad|sig|Dr|Prof|Mio|Mrd|Lsg|Tbl|Amp|Fl|Tabl|ml|mg|kg|mind|év|ann|cap|n|ss|segg|"
         r"Mo|Mt|Wo|J|Jh|Tab|Kap|Pat|Hrsg|bspw|zB|sq|cit|op|pag|pp|Bd|Nos?)\.")
_SENT_END = re.compile(r"(?<=[.;!?])\s+(?=[^\s a-zäöüàâéèêîôûç])|(?<=:)\s+(?=[A-ZÄÖÜÀÂÉÈÊÎÔÛÇ«\"(•–-])")


def sentences(t):
    """-> [(start, end)] of the sentences of t (see ALIGNMENT)."""
    out, s = [], 0
    for m in _SENT_END.finditer(t):
        pre = t[s:m.start()]
        if (re.search(r"(?:^|[\s(/])" + _ABBR + r"$", pre) or re.search(r"(?:[A-Za-z]\.){2,}$", pre)
                or (re.search(r"(?:^|\s)\d{1,3}\.$", pre) and not re.search(r"\d\.\d", pre[-6:]))):
            continue
        if pre.strip(): out.append((s, m.start()))
        s = m.end()
    if t[s:].strip(): out.append((s, len(t)))
    return out


def _anchors(seg, L): return set(x["v"] for x in values(seg, L) if x["src"] != "word")


def align(de, tgt, lang):
    """monotone sentence alignment -> (pairs [(de_span, tgt_span, cost)], n_de, n_tgt). Spans of merged sentences
    (1-2, 2-1) run from the first start to the last end. Skipped sentences are in no pair."""
    import math
    S, T = sentences(de), sentences(tgt); n, m = len(S), len(T)
    ad = [_anchors(de[a:b], "de") for a, b in S]; at = [_anchors(tgt[a:b], lang) for a, b in T]
    ld = [b - a for a, b in S]; lt = [b - a for a, b in T]; rat = sum(lt) / max(1, sum(ld))

    def cost(i0, i1, j0, j1):
        if i0 == i1 or j0 == j1: return 3.0
        A_, B_ = set().union(*ad[i0:i1]), set().union(*at[j0:j1])
        c = abs(math.log((sum(lt[j0:j1]) + 10) / (sum(ld[i0:i1]) * rat + 10)))
        if A_ or B_: c += 2 * (1 - len(A_ & B_) / len(A_ | B_))
        return c + (0.5 if (i1 - i0) + (j1 - j0) > 2 else 0)
    INF = float("inf"); D = [[INF] * (m + 1) for _ in range(n + 1)]; P = {}; D[0][0] = 0.0
    for i in range(n + 1):
        for j in range(m + 1):
            if D[i][j] == INF: continue
            for di, dj in ((1, 1), (1, 2), (2, 1), (1, 0), (0, 1)):
                a, b = i + di, j + dj
                if a > n or b > m: continue
                c = D[i][j] + cost(i, a, j, b)
                if c < D[a][b]: D[a][b] = c; P[(a, b)] = (i, j)
    out, a, b = [], n, m
    while (a, b) != (0, 0):
        i, j = P[(a, b)]
        if i < a and j < b: out.append(((S[i][0], S[a - 1][1]), (T[j][0], T[b - 1][1]), round(cost(i, a, j, b), 3)))
        a, b = i, j
    return out[::-1], n, m


def aligned(de, tgt, lang):
    """the aligned sentence pairs that are judged (ALIGN_MAX, ALIGN_MAX_UNEVEN) -> [(de_span, tgt_span, cost)]."""
    P, n, m = align(de, tgt, lang)
    return [p for p in P if p[2] <= ALIGN_MAX and (n == m or p[2] <= ALIGN_MAX_UNEVEN)]


# ---- operator direction
_GLUE = {"de": r"(?:von|vom|dem|den|der|des|zu|einer?|einem|eines|insgesamt|total|ca\.|circa|je|pro)",
         "fr": r"(?:à|a|de|d['’]|des|du|le|la|les|l['’]|un|une|total|au total|environ|env\.|par)",
         "it": r"(?:a|ad|al|ai|agli|alla|alle|da|di|del|dei|degli|della|delle|i|gli|il|la|le|l['’]|un|uno|una|totale|in totale|circa|per)"}
OP_PRE = {"de": [("min", r"≥|>=|>|mindestens|minimal|minimum|min\.|ab|über|mehr als|grösser als|größer als|frühestens|wenigstens|oberhalb von|nicht weniger als|nicht unter|"
                         r"minimale[nrms]?\s+[A-ZÄÖÜ]\w+|Mindest\w+|grösser oder gleich|größer oder gleich"),
                 ("max", r"≤|<=|<|höchstens|maximal|maximum|max\.|bis maximal|bis zu|bis|unter|weniger als|kleiner als|spätestens|unterhalb von|längstens|nicht mehr als|nicht über|nicht länger als|"
                         r"maximale[nrms]?\s+[A-ZÄÖÜ]\w+|Maximal\w+|Höchst\w+|kleiner oder gleich")],
          "fr": [("min", r"≥|>=|>|au moins|au minimum|minimum|minimale?s? de|plus de|plus d['’]|supérieure?s? ou égale?s? à|égale?s? ou supérieure?s? à|supérieure?s? à|dès|à partir de|au-delà de|au-dessus de|pas moins de|d['’]au moins"),
                 ("max", r"≤|<=|<|au plus|au maximum|maximum|maximale?s? de|moins de|moins d['’]|inférieure?s? ou égale?s? à|égale?s? ou inférieure?s? à|inférieure?s? à|jusqu['’]à|en dessous de|au-dessous de|pas plus de|n['’]excédant pas|ne dépassant pas|d['’]au plus|d['’]au maximum")],
          "it": [("min", r"≥|>=|>|almeno|al minimo|minimo|minima|più di|più del|superiore o uguale a|superiori o uguali a|pari o superiore a|pari o superiori a|superiore a|superiori a|oltre|a partire da|a partire dai|a partire dal|sopra|non meno di"),
                 ("max", r"≤|<=|<|al massimo|al più|massimo|massima|meno di|meno del|inferiore o uguale a|inferiori o uguali a|pari o inferiore a|pari o inferiori a|inferiore a|inferiori a|fino a|fino al|fino ai|sotto|non più di|non oltre")]}
OP_POST = {"de": [("min", r"oder mehr|und mehr|oder älter|oder höher|oder länger|und darüber|oder darüber|mindestens"), ("max", r"oder weniger|und weniger|oder jünger|oder kürzer|und darunter|oder darunter|höchstens|maximal")],
           "fr": [("min", r"ou plus|et plus|au moins|au minimum|minimum|ou davantage"), ("max", r"ou moins|au plus|au maximum|maximum")],
           "it": [("min", r"o più|e più|almeno|al minimo|o oltre"), ("max", r"o meno|al massimo|al più|massimo")]}
_OPRE = {L: re.compile(r"(?:^|(?<=[\s(\[/,;:]))(?:" + "|".join(f"(?P<{d}>{p})" for d, p in v) + r")\s*(?:" + _GLUE[L] + r"\s*){0,2}$", re.I)
         for L, v in OP_PRE.items()}
_OPOST = {L: re.compile(r"^\s*(?:" + "|".join(f"(?P<{d}>{p})" for d, p in v) + r")(?![\w])", re.I) for L, v in OP_POST.items()}
_RANGE_BIS = {"de": r"\d\s*(?:\S+\s+)?(?:bis|-|–)\s*$", "fr": r"\d\s*(?:\S+\s+)?(?:à|-|–)\s*$", "it": r"\d\s*(?:\S+\s+)?(?:a|-|–)\s*$"}


_ADJ_SFX = r"\w*(?:bil[ei]s?|ic[oaie]|iques?|ique|ar[ei]s?|air[es]?|os[oaie]|euse?s?|eux|al[ei]s?|aux|iv[oaie]|ifs?|ives?|ent[ei]s?|ant[ei]s?|at[oaie]|é[es]?|ée?s|it[oaie])"


def _negated(text, at, lang):
    """a clause negation earlier in the same clause, at most 12 words before position at ('n'ont pas reçu plus de
    deux', 'non inferiore a 4', 'kein Ansprechen von mindestens 50%'). The languages place a negation differently, so a
    negated bound is left out of the comparison (on both sides). FR/IT 'non' right before an adjective or participle
    ('non lacunaire', 'non resecabile') negates that word, not the clause."""
    pre = re.split(r"[,.;:()•]|\s[-–]\s", text[max(0, at - 160):at])[-1]
    ws = re.findall(r"\S+", pre)[-12:]
    if not ws: return False
    j = " ".join(ws)
    hits = [h for h in neg_strong(j, lang) if not (lang in ("fr", "it") and h[2].lower() == "non"
                                                    and re.match(r"\s+" + _ADJ_SFX + r"\b", j[h[1]:], re.I))]
    return bool(hits)


def directions(text, lang):
    """-> [dict(v, dir 'min'|'max', s, e, op, os, oe)] for the values of text that carry a comparison word."""
    out = []
    for x in values(text, lang):
        pre = text[max(0, x["s"] - 40):x["s"]]
        m = _OPRE[lang].search(pre); d = None
        if m:
            m0 = _OPRE[lang].search(pre[:m.start()].rstrip() + " ")
            if m0 and m.start() - m0.end() <= 1 and m.group(m.lastgroup).lower() == "über": m = m0   # 'maximal über 12 Monate'
            d = "min" if m.group("min") else "max"; op = m.group(m.lastgroup).strip(); os_ = x["s"] - len(pre) + m.start()
            if d == "max" and re.fullmatch(r"bis|-|à|a", op.lower()) and re.search(_RANGE_BIS[lang], text[max(0, x["s"] - 30):x["s"]]): d = None
            if op.lower() == "über" and _ucls(x.get("unit"), lang) in ("d", "w", "m", "h"): d = None    # 'über 6 Monate': a duration
        if d is None:
            e = x["e"]
            if x.get("unit"):
                um = UNIT_RX[lang].match(text, e)
                if um: e = um.end()
            m2 = _OPOST[lang].match(text[e:e + 30])
            if m2: d = "min" if m2.group("min") else "max"; op = m2.group(m2.lastgroup); os_ = e + m2.start(m2.lastgroup)
        neg = bool(d) and _negated(text, min(os_, x["s"]), lang)
        if d: out.append(dict(v=x["v"], alt=x["alt"], dir=d, neg=neg, s=x["s"], e=x["e"], op=op, os=os_, oe=os_ + len(op), unit=x.get("unit")))
    return out


def operator_diff(de, tgt, lang):
    """R15 (1): values both texts state with a direction (the same number of times), whose directions differ ->
    [dict(value, de_dirs, tgt_dirs, de_op, tgt_op, de_dir, tgt_dir, unit, context_de, context_tgt, tgt_spans)];
    tgt_spans: every target occurrence with the direction the German lacks."""
    de, tgt = nrm(de), nrm(tgt)
    A_, B_ = directions(de, "de"), directions(tgt, lang); out = []
    for v in sorted(set(x["v"] for x in A_) & set(x["v"] for x in B_)):
        xa = [x for x in A_ if x["v"] == v]; xb = [x for x in B_ if x["v"] == v]
        xa = [x for x in xa if not x["neg"]]; xb = [x for x in xb if not x["neg"]]    # negated bounds are left out
        ca, cb = Counter(x["dir"] for x in xa), Counter(x["dir"] for x in xb)
        if not ca or sum(ca.values()) != sum(cb.values()) or ca == cb: continue
        dd = (ca - cb) or ca; dt = (cb - ca) or cb
        ea = next(x for x in xa if x["dir"] in dd); EB = [x for x in xb if x["dir"] in dt]; eb = EB[0]
        sp = lambda x: (min(x["s"], x["os"]), max(x["e"], x["oe"]))
        out.append(dict(value=v, de_dirs=dict(ca), tgt_dirs=dict(cb), de_op=ea["op"], tgt_op=eb["op"],
                        de_dir=ea["dir"], tgt_dir=eb["dir"], unit=ea["unit"] or eb["unit"],
                        context_de=ctx(de, dict(zip(("s", "e"), sp(ea)))), context_tgt=ctx(tgt, dict(zip(("s", "e"), sp(eb)))),
                        tgt_spans=[sp(x) for x in EB]))
    return out


# ---- negation
NEG_STRONG = {"de": r"\bnicht\b(?!-)|\bkein(?:e|er|en|em|es)?\b|\bnie\b|\bniemals\b|\bweder\b|\bnichts\b",
              "fr": r"\bne\b|\bn['’](?=\w)|\bpas\b|\baucune?s?\b|\bnon\b(?!-)|\bjamais\b|\bni\b|\bnulle?s?\b|\brien\b",
              "it": r"\bnon\b(?!-)|\bnessun[oa]?\b|\bnessun['’]|\bmai\b|\bné\b|\bniente\b|\bnulla\b"}
# companions: counted only without their clause negator before them (FR 'n'a pas', 'n'a aucun'; IT 'non ... nessun')
NEG_COMPANION = {"de": r"(?!)", "fr": r"pas|aucune?s?|jamais|rien|nulle?s?|ni", "it": r"nessun[oa']?|mai|né|niente|nulla"}
# negations inside a bound or time idiom, and expletive ones, are not a negated condition (they count as SUPP below)
NEG_IDIOM = {"de": r"\bnicht\s+(?:mehr|weniger|länger|kürzer|früher|später)\s+als\b|\bnicht\s+(?:über|unter)\b|\bnicht\s+\w*(?:überschreit|übersteig)\w*|"
                   r"\bes sei denn\b",
             "fr": r"\b(?:ne|n['’])\s*(?:\S+\s+){0,2}?(?:pas|plus)\s+(?:plus|moins)\s+(?:de|d['’]|que)|\bpas\s+(?:plus|moins)\s+(?:de|d['’]|que)|"
                   r"\b(?:ne\s+|n['’])(?:\S+\s+){0,3}?(?:dépass|excéd)\w*(?:\s+pas)?|\bpas\s+avant\b|"
                   r"\b(?:avant|moins|crainte|peur)\s+qu(?:e\s+|['’])(?:\S+\s+){0,5}?(?:ne\b|n['’])",
             "it": r"\bnon\s+(?:più|meno|oltre|prima|dopo|appena|superiore|inferiore)\b|\bnon\s+(?:\S+\s+){0,2}?(?:superar|eccede)\w*|"
                   r"\bnon\s+(?:\S+\s+){0,6}?se non\b|"
                   r"\b(?:a meno che|finché|finche|fino a quando|fintanto che|prima che)\s+(?:\S+\s+){0,5}?non\b"}
# lexical negation: the negation lives in a word (ohne, sans, unzureichend, insuffisant, nicht-kleinzellig, absence ...)
NEG_LEX = {"de": r"\bohne\b|\bausgenommen\b|\bausgeschlossen\b|\bausnahme\w*|\bfehlen\w*|\babwesenheit\b|\bversagen\b|"
                 r"\w{3,}los(?:e[nmrs]?)?\b|\w{3,}frei(?:e[nmrs]?)?\b|\bun(?!d\b|ter|ten\b|s\b|ser|gefähr|iver|ion|fall)\w{4,}|"
                 r"\bin(?:akzep|operab|effektiv|kompat|tolera|suffizient|adäquat)\w*|\w*intoleranz\w*|\bnicht-\w+|\bnicht\w{3,}|\w+-nicht\w*|"
                 r"\bnegativ\w*|\bnon\b|\bnon-\w+|\ba(?:traumat|symptomat|typisch)\w*|\w*refrakt\w*|\bkontraindiz\w*|"
                 r"\bversäum\w*|\bverpass\w*|\bverzicht\w*|\bunterlass\w*|\bfehlschlag\w*|\bverweiger\w*",
           "fr": r"\bsans\b|\bexclu\w*|\babsence\b|\bhors\b|\bdéfaut\b|\bmanque\b|\béchec\b|"
                 r"\bin(?:suffisant|suffisamment|adéqu|toléra|efficac|contrôl|satisf|appropri|accept|compatib|complet|opérab|éligib|évitab|capac)\w*|\bintoléran\w*|"
                 r"\bimpossib\w*|\bnon-\w+|\bnégati\w*|\bréfractaire\w*|\bcontre-indiqu\w*|\bomi[st]\w*|\bomett\w*|\brenonc\w*|\brefus\w*",
           "it": r"\bsenza\b|\bescl[ua]\w*|\bassenza\b|\bmancat\w*|\bmancanza\b|\bfallimento\b|"
                 r"\bin(?:sufficient[ei]\b|sufficientemente|adegua|tollera|efficac|controlla|soddisfa|appropria|accettab|compatib|complet|operab|eleggib|evitab|capac)\w*|"
                 r"\bintolleran\w*|\bimpossib\w*|\bnon-\w+|\bnegativ\w*|\brefrattari\w*|\bcontroindica\w*|\bomess\w*|\bomett\w*|\brinunc\w*|\brifiut\w*"}
# restriction, exception and 'below' words: a language may say with them what the other says with a negation
NEG_SUPP = {"de": r"\baus?ser\b|\baußer\b|\bansonsten\b|\bandernfalls\b|\bsonst\b|\babweich\w*|\bunter\b|\bweniger als\b|\bkleiner\b",
            "fr": r"\bsauf\b|\bhormis\b|\bexcept\w*|\bexception\b|\bà moins\b|\binférieur\w*|\bmoins de\b|\ben dessous\b",
            "it": r"\bsalvo\b|\btranne\b|\beccezione\b|\ba meno che\b|\binferior\w*|\bmeno di\b|\bsotto\b|\bse non\b"}
_NS = {L: re.compile(v, re.I) for L, v in NEG_STRONG.items()}
_NC = {L: re.compile(r"(?:" + v + r")", re.I) for L, v in NEG_COMPANION.items()}
_NI = {L: re.compile(v, re.I) for L, v in NEG_IDIOM.items()}
_NL = {L: re.compile(v, re.I) for L, v in NEG_LEX.items()}
_NP = {L: re.compile(v, re.I) for L, v in NEG_SUPP.items()}


def _ne_que(s, at):
    """FR 'ne ... que' (= only): a 'que/qu'' later in the sentence before any pas/plus/jamais/aucun/rien/guère/point."""
    q = re.search(r"\bqu(?:e\b|['’])", s[at:]); n = re.search(r"\b(?:pas|plus|jamais|aucune?s?|rien|guère|point|ni)\b", s[at:])
    return q is not None and (n is None or q.start() < n.start())


def neg_strong(s, L):
    """clause negations of one sentence -> [(start, end, surface)], counted per clause (split at , ; : and brackets):
    FR the 'ne/n'' of the clause (each), or, without one, its first pas/aucun/jamais/rien/ni/non word ('Pas de ...');
    IT each 'non', or, without one, the first nessuno/mai/né; DE each nicht/kein/nie/weder. Idioms, expletives and FR
    'ne ... que' (= only) are left out."""
    skip = [m.span() for m in _NI[L].finditer(s)]; out = []
    bounds = [0] + [m.end() for m in re.finditer(r"[,;:()\[\]]", s)] + [len(s)]
    for c0, c1 in zip(bounds, bounds[1:]):
        heads, comps = [], []
        for m in _NS[L].finditer(s, c0, c1):
            if any(a <= m.start() < b for a, b in skip): continue
            w = m.group(0).lower()
            if L == "fr" and (w == "ne" or w[:2] in ("n'", "n’")) and _ne_que(s, m.end()): continue      # ne ... que = only
            (comps if _NC[L].fullmatch(w) else heads).append((m.start(), m.end(), m.group(0)))
        if not heads:                                                                  # 'aucune A ou aucune B'; 'ni A ni B' once
            ni = [h for h in comps if h[2].lower() in ("ni", "né")]; heads = [h for h in comps if h not in ni] + ni[:1]
        out += heads
    return sorted(out)


def neg_lex(s, L): return [m.group(0) for m in _NL[L].finditer(s)]


def neg_supp(s, L):
    return [m.group(0) for m in _NP[L].finditer(s)] + [m.group(0) for m in _NI[L].finditer(s)] + \
           (["ne … que"] if L == "fr" and any(_ne_que(s, m.end()) for m in re.finditer(r"\b(?:ne\b|n['’])", s, re.I)) else [])


def neg_weak(s, L): return neg_lex(s, L) + neg_supp(s, L)


NEG_LEXT = {"de": r"\bohne\b|\bnon-\w+|\bnicht-?\w{4,}|\bun(?:zureichend|genügend|befriedigend|wirksam|kontrolliert|behandelt|verträglich|angemessen|geeignet)\w*|"
                  r"\bin(?:akzep|operab|suffizient|adäquat)\w*|\b(?:erfolg|wirkung|ergebnis)\w*los\w*|\w*refrakt\w*",
            "fr": r"\bsans\b|\bnon-\w+|\bin(?:suffisant|adéquat|efficace|acceptable|opérable|éligible)\w*|\bréfractaire\w*",
            "it": r"\bsenza\b|\bnon-\w+|\bin(?:sufficient|adeguat|efficac|accettabil|operabil|eleggibil|idone)\w*|\brefrattari\w*"}
_NT = {L: re.compile(v, re.I) for L, v in NEG_LEXT.items()}


def _adj_non(s, L, h):
    """FR/IT 'non' right before an adjective or participle ('non lacunaire', 'non resecabile'): a word negation."""
    return L in ("fr", "it") and h[2].lower() == "non" and re.match(r"\s+" + _ADJ_SFX + r"\b", s[h[1]:], re.I) is not None


def _neg_profile(t, k):
    hs = neg_strong(t, k)
    adj = [t[h[0]:h[1] + 1 + len(re.match(r"\s*\S*", t[h[1]:]).group(0).strip())] for h in hs if _adj_non(t, k, h)]
    return dict(S=[h[2] for h in hs if not _adj_non(t, k, h)], X=neg_lex(t, k) + adj, P=neg_supp(t, k),
                T=[m.group(0) for m in _NT[k].finditer(t)] + adj)


def _neg_one_sided(A_, B_):
    """side 'a' or 'b' whose negation the other lacks entirely, or None (presence rule)."""
    for x, y, side in ((A_, B_, "a"), (B_, A_, "b")):
        if (x["S"] or x["T"]) and not (y["S"] or y["X"] or y["P"]): return side
    return None


def negation_diff(de, tgt, lang):
    """R15 (2), per aligned sentence pair: one side has a clause negation, or (narrow list NEG_LEXT) a word negation
    such as 'ohne', 'unzureichend', 'non résécable', and the other side has none at all: no clause negation, no word
    negation (NEG_LEX), no restriction / exception / 'below' word and no negation idiom (NEG_SUPP, NEG_IDIOM).
    -> [dict(side, negations, de_sentence, tgt_sentence, de_span, tgt_span, cost, unit)]."""
    de, tgt = nrm(de), nrm(tgt); out = []
    for d, g, c in aligned(de, tgt, lang):
        sd, sg = de[d[0]:d[1]], tgt[g[0]:g[1]]
        side = _neg_one_sided(_neg_profile(sd, "de"), _neg_profile(sg, lang))
        if side is None: continue
        k = "de" if side == "a" else lang; pr = _neg_profile(sd if side == "a" else sg, k)
        out.append(dict(side=k, negations=pr["S"] or pr["T"], de_sentence=sd, tgt_sentence=sg, de_span=d, tgt_span=g, cost=c,
                        unit="sentence"))
    return out


# ---- number words
_BOTH = {"de": r"\bbeide\w*", "fr": r"\b(?:les|tous|toutes|ces)\s+deux\b|\bl['’]un et l['’]autre\b", "it": r"\bentramb\w*|\bambedue\b|\bambo\b|\btutti e due\b|\btutte e due\b"}


def number_word_diff(de, tgt, lang, reported=None):
    """R15 (3): per aligned sentence pair, values involving a number word that one side lacks -> [dict(side, value,
    unit, src, context, span)]. reported: {(side, value)} already named by a number finding (skipped)."""
    de, tgt = nrm(de), nrm(tgt); out = []; reported = reported or set()
    for d, g, c in aligned(de, tgt, lang):
        sd, sg = de[d[0]:d[1]], tgt[g[0]:g[1]]
        r = compare(sd, sg, lang, bind_words=True)
        def word(x, text): return x["src"] == "word" and not any(re.search(r"fach", text[a:b], re.I) for a, b in x["spans"])
        wa = [x for x in r["de_only"] if word(x, sd)]; wb = [x for x in r["tgt_only"] if word(x, sg)]
        if not (wa or wb): continue
        cand = [("de", x, sd, d[0]) for x in r["de_only"] if x in wa or (wb and x["unit"] != "word")] + \
               [(lang, x, sg, g[0]) for x in r["tgt_only"] if x in wb or (wa and x["unit"] != "word")]
        for side, x, text, off in cand:
            other, ol = (sg, lang) if side == "de" else (sd, "de")
            n = _num(x["value"])
            if n is not None and n == int(n) and 2 <= n <= 12 and re.search(r"\b(?:" + ORD[ol][int(n)] + r")", other, re.I): continue
            if x["value"] == "2" and re.search(_BOTH[ol], other, re.I): continue
            if equivalence(x["value"], side, text, other, ol): continue
            if (side, x["value"]) in reported: continue
            out.append(dict(side=side, value=x["value"], unit=None if x["unit"] == "word" else x["unit"], src=x["src"],
                            context=x["context"][:1], span=(off + x["spans"][0][0], off + x["spans"][0][1]),
                            de_sentence=sd, tgt_sentence=sg))
    return out


def counterpart(f, de, tgt):
    """display field of a number finding: per one-sided value, the values the aligned sentence of the other side states
    in surplus with the same unit class -> {side: [dict(value, unit, src, for_value)]}."""
    L = f["lang"]; de, tgt = nrm(de), nrm(tgt); res = {}
    pairs = align(de, tgt, L)[0]
    for side, lst in (("de", f.get("de_only") or []), (L, f.get("tgt_only") or [])):
        for y in lst:
            for d, g, c in pairs:
                own, oth, ol, ow = (de[d[0]:d[1]], tgt[g[0]:g[1]], L, "de") if side == "de" else (tgt[g[0]:g[1]], de[d[0]:d[1]], "de", L)
                X = values(own, ow)
                if not any(x["v"] == y["value"] for x in X): continue
                uc = _ucls(y["unit"], ow) or (y["unit"] or "").lower()
                same = lambda x, l: bool(x["unit"]) and (_ucls(x["unit"], l) or x["unit"].lower()) == uc
                co = Counter(x["v"] for x in X if same(x, ow)); cx = [x for x in values(oth, ol) if same(x, ol)]
                cy = Counter(x["v"] for x in cx)
                for x in cx:
                    if cy[x["v"]] > co.get(x["v"], 0) and x["v"] != y["value"]:
                        o = ol if side == "de" else "de"
                        e = dict(value=x["v"], unit=x["unit"], src=x["src"], for_value=y["value"])
                        if e not in res.setdefault(o, []): res[o].append(e)
                break
    return res


def r5_findings(i, de, tgt, lang, number_f=None, kinds=KINDS_R5):
    """the round-5 findings of one limitation and language (without fid/rank). number_f: the existing number finding of
    (i, lang), if any (its values are not repeated as number_word findings)."""
    out = []
    if "operator" in kinds:
        for o in operator_diff(de, tgt, lang):
            W = {"min": "a lower bound", "max": "an upper bound"}
            out.append(dict(id=i, lang=lang, kind="operator", languages=["de", lang], value=o["value"], unit=o["unit"],
                            de_op=o["de_op"], tgt_op=o["tgt_op"], de_dir=o["de_dir"], tgt_dir=o["tgt_dir"],
                            context=[o["context_de"], o["context_tgt"]], tgt_spans=[list(x) for x in o["tgt_spans"]],
                            description=f"DE makes {o['value']} {W[o['de_dir']]} ('{o['de_op']}'), {lang.upper()} "
                                        f"{W[o['tgt_dir']]} ('{o['tgt_op']}')."))
    if "negation" in kinds:
        for g in negation_diff(de, tgt, lang):
            S = NAME[g["side"]]; O = NAME[lang] if g["side"] == "de" else "German"
            out.append(dict(id=i, lang=lang, kind="negation", languages=["de", lang], side=g["side"], negations=g["negations"],
                            unit=g["unit"], context=[_clip(g["de_sentence"]), _clip(g["tgt_sentence"])],
                            tgt_span=list(g["tgt_span"]),
                            description=f"The {S} {g['unit']} is negated ({', '.join(g['negations'])}); the aligned {O} {g['unit']} "
                                        f"has no negation."))
    if "number_word" in kinds:
        rep = set()
        if number_f:
            rep = {("de", x["value"]) for x in number_f.get("de_only") or []} | {(lang, x["value"]) for x in number_f.get("tgt_only") or []}
        ws = number_word_diff(de, tgt, lang, rep)
        if ws:
            da = [w for w in ws if w["side"] == "de"]; ta = [w for w in ws if w["side"] != "de"]
            p = [f"DE has {w['value']} ({w['unit'] or 'number word'}), {lang.upper()} does not" for w in da] + \
                [f"{lang.upper()} has {w['value']} ({w['unit'] or 'number word'}), DE does not" for w in ta]
            out.append(dict(id=i, lang=lang, kind="number_word", languages=["de", lang],
                            de_only=[dict(value=w["value"], unit=w["unit"], src=w["src"], context=w["context"]) for w in da],
                            tgt_only=[dict(value=w["value"], unit=w["unit"], src=w["src"], context=w["context"], span=list(w["span"])) for w in ta],
                            context=[c for w in ws for c in w["context"][:1]], description="; ".join(p) + " (in the aligned sentence)."))
    return out


def _clip(s, n=300): return s if len(s) <= n else s[:n] + "…"


def run_r5(J, names, F=None, kinds=KINDS_R5):
    """round-5 findings on a register (J as load()); F: the number findings of run() (for number_word dedup)."""
    by = {(f["id"], f["lang"]): f for f in F or [] if f["kind"] == "number"}
    pname = lambda i: sorted(set(n.split(" ")[0] for n in names.get(i, [])))[:3]
    R = []
    for i in sorted(J["de"]["lim"]):
        de = J["de"]["lim"][i]
        for L in ("fr", "it"):
            t = J[L]["lim"].get(i)
            if not t: continue
            for f in r5_findings(i, de, t, L, by.get((i, L)), kinds):
                f.update(product=pname(i), half=half(i), odd_one_out=None, suggested_action=None, likely_equivalent=False, equivalence=None)
                R.append(f)
    order = {k: n for n, k in enumerate(KINDS_R5)}
    R.sort(key=lambda f: (order[f["kind"]], f["id"], f["lang"], str(f.get("value") or f.get("tgt_span"))))
    pre = {"operator": "O", "negation": "G", "number_word": "W"}; c = Counter()
    for f in R: c[f["kind"]] += 1; f["rank"] = c[f["kind"]]; f["fid"] = f"{pre[f['kind']]}{c[f['kind']]:02d}"
    return R
# ------------------------------------------------------------------ END OF ROUND-5 RULES


LOC = {"lang": {"fr": "l'ancien texte français est en {x}", "it": "il vecchio testo italiano è in {x}",
                "de": "der alte deutsche Text ist auf {x}"},
       "lname": {"fr": {"de": "allemand", "fr": "français", "it": "italien", "en": "anglais"},
                 "it": {"de": "tedesco", "fr": "francese", "it": "italiano", "en": "inglese"},
                 "de": {"de": "Deutsch", "fr": "Französisch", "it": "Italienisch", "en": "Englisch"}},
       "edit": {"fr": "coquille probable dans l'ancien texte{w} : «{s}» (sans doute «{g}»)",
                "it": "probabile refuso nel vecchio testo{w}: «{s}» (forse «{g}»)",
                "de": "wahrscheinlicher Tippfehler im alten Text{w}: «{s}» (wohl «{g}»)"},
       "edit_de": {"fr": " allemand", "it": " tedesco", "de": " (Deutsch)"}}


KINDS_ALL = ("number", "unit", "language", "editorial", "terminology")


def audit_item(x, stats=None, kinds=KINDS_ALL, terms=None):
    """For the review UI: pre-existing problems of an item's old texts. x: dict with de_old, tgt_old, lang.
    kinds may also name the round-5 kinds (operator, negation, number_word; not in the default).
    -> [] or a list of dicts, each with kind ('number'|'unit'|'language'|'editorial'|'terminology'), lang, detail (one
    English sentence), values (optional), odd_one_out (optional), and 'text' (one phrase in the item's language).
    Number findings keep the round-2 shape (side 'de'|lang, value, n, unit, src, context) and add likely_equivalent /
    equivalence (a triage hint, Q1-Q5); unit findings carry the same keys for the target side. Language findings judge
    the old target only; editorial findings both old texts. Terminology findings (old, new, de_term, corrected_in) use
    the precomputed pairs (default: the shipped data/audit/term_pairs_20261006.json; no snapshot dir needed).
    stats: register statistics (default: the shipped data/audit/lang_stats_20261006.json.gz)."""
    L = x["lang"]; st = _prep(stats) if stats is not None else load_stats(); out = []
    T = {"fr": "French", "it": "Italian"}.get(L, L)
    if "number" in kinds:
        r = compare(x["de_old"], x["tgt_old"], L)
        for y in r["de_only"]:
            q = equivalence(y["value"], "de", x["de_old"], x["tgt_old"], L)
            out.append(dict(kind="number", lang=L, side="de", values=[y["value"]],
                            detail=f"The old German has {y['value']} ({y['unit']}); the old {T} does not.",
                            likely_equivalent=bool(q), equivalence=q, **y))
        for y in r["tgt_only"]:
            q = equivalence(y["value"], L, x["tgt_old"], x["de_old"], "de")
            out.append(dict(kind="number", lang=L, side=L, values=[y["value"]],
                            detail=f"The old {T} has {y['value']} ({y['unit']}); the old German does not.",
                            likely_equivalent=bool(q), equivalence=q, **y))
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
    if "terminology" in kinds and L in ("fr", "it"):
        for p, m in term_check(x["de_old"], x["tgt_old"], L, load_terms() if terms is None else terms):
            out.append(dict(kind="terminology", lang=L, odd_one_out=L, old=p["old_surface"], new=p["new_surface"],
                            de_term=p["de_surface"], corrected_in=p["corrected_in"], n_limitations=p["n_limitations"],
                            context=[ctx(nrm(x["tgt_old"]), dict(s=m.start(), e=m.end()), 50)] if m else [],
                            detail=term_detail(p, L),
                            text=LOC_TERM[L].format(o=p["old_surface"], n=p["new_surface"], d=p["de_surface"], k=p["n_limitations"])))
    for f in r5_findings(None, x["de_old"], x["tgt_old"], L, kinds=tuple(k for k in KINDS_R5 if k in kinds)) if set(kinds) & set(KINDS_R5) else []:
        vals = [f["value"]] if f.get("value") else [y["value"] for y in f.get("de_only", []) + f.get("tgt_only", [])]
        out.append(dict({k: v for k, v in f.items() if k not in ("id", "description")}, values=vals, detail=f["description"]))
    return out


# ------------------------------------------------------------------ the whole snapshot
def half(i): return "dev" if int(hashlib.md5(i.encode()).hexdigest(), 16) % 2 == 0 else "held"


_LOADED = {}


def load(hist, date):
    k = (os.path.abspath(hist), date)
    if k not in _LOADED:
        if len(_LOADED) >= 12: _LOADED.pop(next(iter(_LOADED)))
        _LOADED[k] = _load(hist, date)
    return _LOADED[k]


def _load(hist, date):
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


def run_all(hist, date, J=None, names=None, st=None, pairs=None, r5=False):
    """every kind on one snapshot -> (findings, number stats, extra stats). Number findings are exactly run()'s.
    pairs: terminology pairs (default: the shipped data/audit/term_pairs_20261006.json; [] = no terminology check).
    r5: also append the round-5 findings (operator, negation, number_word; PREREG R15), after all the others; the
    findings of the other kinds are the same either way."""
    if J is None: J, names = load(hist, date)
    if pairs is None: pairs = load_terms()
    F, S = run(hist, date, J, names)
    st = _prep(st or build_stats(J))
    pname = lambda i: sorted(set(n.split(" ")[0] for n in names.get(i, [])))[:3]
    for f in F:
        f["fid"] = f"N{f['rank']:02d}"; f["languages"] = ["de", f["lang"]]
        f["odd_one_out"], f["third"] = odd_number(f, J); f["suggested_action"] = None
        f["context"] = [c for x in f["de_only"] + f["tgt_only"] for c in x["context"][:1]]
    U, Lg, E, Tm, one = [], [], [], [], []; judged = Counter(); short = Counter()
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
        for L in ("fr", "it"):
            if not T[L] or det.get(L, {}).get("detected", L) != L: continue
            for p, m in term_check(T["de"], T[L], L, pairs):
                M = _third(L); tm = term_check(T["de"], T[M], M, [q for q in pairs if q["lang"] == M]) if T[M] else []
                Tm.append(dict(id=i, product=pname(i), lang=L, kind="terminology", languages=["de", L], odd_one_out=L, third=M,
                               third_also=bool(tm), old=p["old_surface"], new=p["new_surface"], de_term=p["de_surface"],
                               old_phrase=p["old_phrase"], new_phrase=p["new_phrase"], de_stem=p["de_term"],
                               n_limitations=p["n_limitations"], corrected_in=p["corrected_in"], half=half(i),
                               context=[ctx(T[L], dict(s=m.start(), e=m.end()), 60)] if m else [T[L][:160]],
                               description=term_detail(p, L), suggested_action=None))
    Lg.sort(key=lambda f: (-(f["margin"] or 0), f["id"], f["lang"]))
    U.sort(key=lambda f: (f["id"], f["lang"], f["value"]))
    E.sort(key=lambda f: (f["rule"], f["id"], f["lang"], f["surface"]))
    Tm.sort(key=lambda f: (-f["n_limitations"], f["old_phrase"], f["id"], f["lang"]))
    for pre, G in (("L", Lg), ("U", U), ("E", E), ("T", Tm)):
        for n, f in enumerate(G): f["rank"] = n + 1; f["fid"] = f"{pre}{n + 1:02d}"
    ed = {}
    for e in E: ed.setdefault(e["id"], []).append(e)
    for f in F:                                     # a number finding that an editorial defect explains (LEQVIO '1 .4')
        vs = set(x["value"] for x in f["de_only"] + f["tgt_only"])
        f["explained_by"] = [e["fid"] for e in ed.get(f["id"], []) if e["lang"] in ("de", f["lang"]) and vs & set(e["values"])]
        f["likely_equivalent"], f["equivalence"] = likely_equivalent(f, J["de"]["lim"][f["id"]], J[f["lang"]]["lim"][f["id"]])
        f["counterpart"] = counterpart(f, J["de"]["lim"][f["id"]], J[f["lang"]]["lim"][f["id"]])     # display only (round 5)
    for f in U + Lg + E + Tm: f["likely_equivalent"], f["equivalence"] = False, None     # assessed for number findings only
    X = dict(language_fields_judged=dict(judged), language_fields_too_short=dict(short), unit_one_sided=one)
    if r5: return F + U + Lg + E + Tm + run_r5(J, names, F), S, X
    return F + U + Lg + E + Tm, S, X


def fkeys(f):
    """identity of a finding across snapshots (for dating): by limitation id, and by content (the early 2026 snapshots
    use other limitation ids, 'RA:<uuid>#n'), so a finding counts as present when either matches."""
    k = (f["lang"], f["kind"])
    if f["kind"] == "number":
        sig = (tuple(sorted(x["value"] for x in f["de_only"])), tuple(sorted(x["value"] for x in f["tgt_only"])))
        con = tuple(sorted(c for x in f["de_only"] + f["tgt_only"] for c in x["context"][:1]))
    elif f["kind"] == "unit": sig = (f["value"], f["de_unit"], f["tgt_unit"]); con = tuple(f["context"])
    elif f["kind"] == "language": sig = (f["detected"],); con = (f["context"][0],)
    elif f["kind"] == "terminology": sig = (f["old_phrase"], f["new_phrase"]); con = (f["context"][0],)
    else: sig = (f["rule"], f["surface"]); con = (f["context"][0],)
    return [("id", f["id"]) + k + sig, ("text",) + k + sig + con]


def snapshots(hist, upto):
    """usable snapshots of the same year up to `upto`: all three languages present."""
    ds = sorted(set(f.split("-")[0] for f in os.listdir(hist) if re.fullmatch(r"\d{8}-(de|fr|it)\.json", f)))
    return [d for d in ds if d[:4] == upto[:4] and d <= upto and all(os.path.exists(os.path.join(hist, f"{d}-{L}.json")) for L in LANGS)]


def date_findings(F, hist, date, st=None, pairs=None):
    """first snapshot (of the usable ones of the year) in which each finding appears, and in how many it appears. The
    earlier snapshots are checked with the register statistics of `date` (st), so a defect is dated by its presence,
    not by when the register counts crossed a threshold."""
    seen = defaultdict(list); ds = snapshots(hist, date); per, lang_any = {}, {}
    for d in ds:
        G = F if d == date else run_all(hist, d, st=st, pairs=pairs)[0]
        per[d] = {k: sum(g["kind"] == k for g in G) for k in KINDS_ALL}
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
        f = max(sorted(c), key=lambda f: c[f] * c[f] / (nd[w] * nt[f]))       # sorted: ties independent of hash order
        if c[f] / nd[w] >= p and c[f] / nt[f] >= p: P.append((w, f))
    exc = [(i, w, f) for i, d, t in docs for w, f in P if (w in d) != (f in t)]
    return dict(p=p, support=support, distinct_pairs=len(docs), term_pairs=len(P), exceptions=len(exc),
                ids_with_exception=len(set(e[0] for e in exc)), examples=[list(x) for x in sorted(P, key=lambda x: (-nd[x[0]], x))[:10]])


def term_probe(J, lang="fr"):
    """the motivating case: how often FR says 'récepteurs ... angiotensine' where DE says 'Angiotensin-II-Antagonist'."""
    ids = [i for i, t in J["de"]["lim"].items() if "Angiotensin-II-Antagonist" in t]
    ok = [i for i in ids if re.search(r"récepteurs? de l.angiotensine", J[lang]["lim"].get(i, ""))]
    return dict(de_ids=len(ids), fr_with_receptor_antagonist=len(ok), wrong_class=sorted(set(ids) - set(ok)))


def fresh(items, st=None, pairs=None):
    """audit_item on every item of a set (old texts). An item counts as having a pre-existing divergence when it has a
    number, unit or language finding; editorial and terminology findings are counted separately."""
    X = json.load(open(items, encoding="utf-8")); hits = []
    for x in X:
        r = audit_item(x, stats=st, terms=pairs)
        if r: hits.append(dict(key=x["key"], lang=x["lang"], kinds=sorted(set(f["kind"] for f in r)), findings=r))
    div = [h for h in hits if set(h["kinds"]) & {"number", "unit", "language"}]
    by = {k: sorted(h["key"] for h in hits if k in h["kinds"]) for k in KINDS_ALL}
    return dict(items=len(X), with_preexisting=len(div), with_language_or_number=len(div),
                with_editorial=len(by["editorial"]), with_terminology=len(by["terminology"]), with_any=len(hits),
                pairs=len(set(h["key"].split("-")[0] for h in div)), by_kind=by, hits=hits)


def worklist_terms(F, J, d, seed=SEED + 2):
    """all terminology findings, shuffled (seed), blind: no rank, no dates, no ids of BAG's corrections."""
    pool = [f for f in F if f["kind"] == "terminology"]
    S = random.Random(seed).sample(pool, len(pool))
    os.makedirs(d, exist_ok=True); W, K = [], {}; w = 2 if len(S) <= 100 else 3
    for j, f in enumerate(S):
        c = f"C{j:0{w}d}"
        W.append(dict(id=c, kind="terminology", lang=f["lang"], de=nrm(J["de"]["lim"][f["id"]]), fr=nrm(J["fr"]["lim"].get(f["id"]) or ""),
                      it=nrm(J["it"]["lim"].get(f["id"]) or ""),
                      finding=f"The {NAME[f['lang']]} text says '{f['old']}' for the German '{f['de_term']}'; elsewhere the "
                              f"register now says '{f['new']}'.",
                      question=QUESTION_TERM))
        K[c] = dict(cud=f["id"], fid=f["fid"], lang=f["lang"], old=f["old_phrase"], new=f["new_phrase"], de_term=f["de_stem"],
                    n_limitations=f["n_limitations"], half=f["half"], first_seen=f.get("first_seen"),
                    corrected_in=[x["id"] for x in f["corrected_in"]])
    json.dump(W, open(os.path.join(d, "worklist.json"), "w"), ensure_ascii=False, indent=1)
    json.dump(K, open(os.path.join(d, "key_map_DO_NOT_SHOW.json"), "w"), ensure_ascii=False, indent=1)
    return len(pool)


QUESTION_R5 = ("Is the difference named in 'finding' a real divergence between the German and the 'lang' text (a different "
               "condition for the reader)? Answer real / minor / not (same condition: rephrasing, style, alignment or parser "
               "artefact).")
SEED_R5 = 20261017


def worklist_r5(R, J, d, n=60, seed=SEED_R5):
    """PREREG R15: all round-5 findings of a kind if there are at most n, else a seeded sample of n; shuffled, blind
    (ids R00..., no kind-specific rule names, no rank, no half) -> {kind: (findings, labelled)}."""
    S = []; used = {}
    for k in KINDS_R5:
        pool = [f for f in R if f["kind"] == k]
        pick = pool if len(pool) <= n else random.Random(seed).sample(pool, n)
        S += pick; used[k] = dict(findings=len(pool), labelled=len(pick))
    S = random.Random(seed).sample(S, len(S))
    os.makedirs(d, exist_ok=True); W, K = [], {}; w = 2 if len(S) <= 100 else 3
    for j, f in enumerate(S):
        r = f"R{j:0{w}d}"
        W.append(dict(id=r, kind=f["kind"], lang=f["lang"], de=nrm(J["de"]["lim"][f["id"]]), fr=nrm(J["fr"]["lim"].get(f["id"]) or ""),
                      it=nrm(J["it"]["lim"].get(f["id"]) or ""), finding=f["description"], question=QUESTION_R5))
        K[r] = dict(cud=f["id"], fid=f["fid"], kind=f["kind"], lang=f["lang"], half=f["half"])
    json.dump(W, open(os.path.join(d, "worklist.json"), "w"), ensure_ascii=False, indent=1)
    json.dump(K, open(os.path.join(d, "key_map_DO_NOT_SHOW.json"), "w"), ensure_ascii=False, indent=1)
    return used


def r5_block_sha():
    s = open(os.path.abspath(__file__), encoding="utf-8").read()
    a = s.index("# " + "=" * 66 + " round 5"); b = s.index("# " + "-" * 66 + " END OF ROUND-5 RULES")
    return hashlib.sha256(s[a:b].encode("utf-8")).hexdigest()


QUESTION_TERM = ("Does the 'lang' text render the German term named in 'finding' with a term that is wrong or that BAG no "
                 "longer uses (so the newer wording should be used)? Answer real (wrong term: different meaning) / minor "
                 "(outdated or inconsistent wording, same meaning) / not (correct here, e.g. it translates a different "
                 "German word).")


def texts_file(F, J, date, path):
    """data/audit/audit_texts_<date>.json: the DE/FR/IT texts of every limitation with a finding (for the register
    without the snapshot files)."""
    T = {i: {L: nrm(J[L]["lim"].get(i) or "") for L in LANGS} for i in sorted(set(f["id"] for f in F))}
    json.dump(dict(note=f"DE/FR/IT texts of every limitation with an audit finding, from the {_fmt_date(date)} public SL feed "
                        "(official publication), so the register can show excerpts without the snapshot files.",
                   date=date, texts=T), open(path, "w"), ensure_ascii=False, indent=0)


def mine_from(H, date, J, items=None):
    """terminology pairs from the usable snapshots of the year up to `date` (+ recorded amendments in `items`)."""
    ds = snapshots(H, date)
    U = list(term_units(H, ds))
    if items and os.path.exists(items): U += list(item_units(json.load(open(items, encoding="utf-8"))))
    P = mine_terms(U, J)
    meta = dict(generated_by=f"python3 -m gleichlaut.audit --date {date}", date=date, snapshots=ds,
                items=os.path.relpath(items, core.ROOT) if items and os.path.exists(items) and items.startswith(core.ROOT) else items,
                units=dict(Counter("items" if u["source"].startswith("items") else "snapshots" for u in U)),
                rules=dict(max_tokens=TERM_MAXTOK, rewrite_similarity=TERM_SIM, position_tolerance=TERM_POS, min_support=TERM_MIN,
                           min_stem_letters=TERM_MINLEN, dice=TERM_DICE, context=TERM_CTX))
    return P, meta


def main(argv=None):
    ap = argparse.ArgumentParser(prog="gleichlaut.audit", description=__doc__.split("\n\n")[0])
    ap.add_argument("--hist", help="snapshot dir (default: $GLEICHLAUT_HIST or track_2b/out/hist)")
    ap.add_argument("--date", default=None, help="snapshot date YYYYMMDD (default 20261006; for --list: from the file name)")
    ap.add_argument("--out", default=DEST)
    ap.add_argument("--items", default=os.path.join(core.ROOT, "data", "items", "items_fresh.json"),
                    help="item set: fresh-item hits, and its recorded BAG amendments as a terminology source ('' = none)")
    ap.add_argument("--worklist", help="write the blind round-2 worklist (number findings) + key map to this dir")
    ap.add_argument("--worklist-new", help="write the blind round-3 worklist (all unit/language/editorial findings) + key map")
    ap.add_argument("--worklist-terms", help="write the blind worklist of all terminology findings + key map to this dir")
    ap.add_argument("--worklist-r5", help="write the blind round-5 worklist (PREREG R15: operator/negation/number_word) + key map")
    ap.add_argument("--no-dating", action="store_true", help="skip the run over the earlier snapshots of the year")
    ap.add_argument("--terms", help="use this term_pairs_<date>.json instead of mining the pairs from the snapshots")
    ap.add_argument("--list", choices=("migel", "al"), help="audit another trilingual BAG list (xlsx) instead of the SL")
    ap.add_argument("--file", help="with --list: the list's xlsx file")
    ap.add_argument("--fail-on-findings", action="store_true",
                    help="exit 1 when any finding is not marked likely_equivalent (for CI / scheduled runs)")
    a = ap.parse_args(argv)
    if a.list:
        from . import audit_lists
        return audit_lists.run_list(a)
    a.date = a.date or "20261006"
    H = hist_dir(a.hist)
    if not os.path.exists(os.path.join(H, f"{a.date}-de.json")): sys.exit(f"no snapshot {a.date} in {H}")
    J, names = load(H, a.date); st = build_stats(J)
    os.makedirs(a.out, exist_ok=True)
    if a.terms: P = load_terms(a.terms); PM = dict(source=a.terms)
    else: P, PM = mine_from(H, a.date, J, a.items or None)
    tp = os.path.join(a.out, f"term_pairs_{a.date}.json")
    if not a.terms: json.dump(dict(meta=PM, pairs=P), open(tp, "w"), ensure_ascii=False, indent=1)
    ALL, S, XS = run_all(H, a.date, J, names, st, pairs=P)
    F = [f for f in ALL if f["kind"] == "number"]
    R = recall(F)
    DT = dict(snapshots=[a.date]) if a.no_dating else date_findings(ALL, H, a.date, st, pairs=P); ds = DT["snapshots"]
    import gzip
    sp = os.path.join(a.out, f"lang_stats_{a.date}.json.gz")
    with gzip.GzipFile(sp, "wb", mtime=0) as g: g.write(json.dumps({k: v for k, v in st.items() if k != "_vocab"}, ensure_ascii=False, sort_keys=True).encode("utf-8"))
    fr = None
    if a.items and os.path.exists(a.items):
        fr = fresh(a.items, st, pairs=P)
    terms = dict(status="off: not precise enough (docs/audit.md)", fr=term_pairs(J, "fr"), it=term_pairs(J, "it"),
                 probe=term_probe(J))
    K = Counter(f["kind"] for f in ALL)
    kt = [f for f in ALL if f["id"] == KNOWN_BONUS]
    TF = [f for f in ALL if f["kind"] == "terminology"]
    summ = dict(generated_by="python3 -m gleichlaut.audit --hist <dir> --date " + a.date, date=a.date, model_calls=0,
                findings=len(F), findings_note="'findings' counts the number findings (round 2); all kinds: by_kind",
                by_kind={k: K.get(k, 0) for k in KINDS_ALL},
                by_kind_lang={k: dict(Counter(f["lang"] for f in ALL if f["kind"] == k)) for k in KINDS_ALL},
                editorial_by_rule=dict(sorted(Counter(f["rule"] for f in ALL if f["kind"] == "editorial").items())),
                findings_all=len(ALL), limitations_with_any_finding=len(set(f["id"] for f in ALL)),
                by_lang=dict(Counter(f["lang"] for f in F)), by_half=dict(Counter(f["half"] for f in F)),
                limitations_with_finding=len(set(f["id"] for f in F)), distinct_text_pairs=len(set(f["group"] for f in F)),
                swaps=sum(1 for f in F if f["score"] >= 11), **S, **XS,
                number_explained_by_editorial={f["fid"]: f["explained_by"] for f in F if f["explained_by"]},
                likely_equivalent=dict(note="triage hint on number findings (Q1-Q5, typo); ids, ranks and counts unchanged",
                                       number=sum(1 for f in F if f["likely_equivalent"]), of=len(F),
                                       findings={f["fid"]: f["equivalence"] for f in F if f["likely_equivalent"]}),
                terminology=dict(pairs=len(P), pairs_file=os.path.relpath(tp, core.ROOT) if tp.startswith(core.ROOT) else tp,
                                 pairs_meta=PM, findings=len(TF), limitations=len(set(f["id"] for f in TF)),
                                 by_pair=dict(Counter(f"{f['lang']}: {f['old_phrase']} -> {f['new_phrase']} (DE {f['de_stem']})" for f in TF))),
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
                                    for k in KINDS_ALL},
                stats_file=os.path.relpath(sp, core.ROOT) if sp.startswith(core.ROOT) else sp,
                s1_census_reference=dict(precision="3/50 = 6% (all categories)", num="3/15 = 20% strict",
                                         source="spikes/gleichlaut/results.md (research, not shipped)"),
                term_pairs=terms,
                fresh=dict((k, v) for k, v in fr.items() if k != "hits") if fr else None)
    R5 = run_r5(J, names, F)
    summ["round5"] = dict(note="PREREG R15: operator / negation / number_word, reported apart from the kinds above (findings_r5 in "
                               "audit_<date>.json); 'on' is set by the R15 outcome; number findings carry a display-only 'counterpart'",
                          rules_sha256=r5_block_sha(), on=dict(R5_ON), findings=len(R5),
                          by_kind={k: sum(f["kind"] == k for f in R5) for k in KINDS_R5},
                          by_kind_lang={k: dict(Counter(f["lang"] for f in R5 if f["kind"] == k)) for k in KINDS_R5},
                          by_kind_half={k: dict(Counter(f["half"] for f in R5 if f["kind"] == k)) for k in KINDS_R5},
                          limitations=len(set(f["id"] for f in R5)),
                          number_counterparts={f["fid"]: f["counterpart"] for f in F if f.get("counterpart")})
    json.dump(dict(summary=summ, findings=ALL, fresh_items=fr["hits"] if fr else None, findings_r5=R5),
              open(os.path.join(a.out, f"audit_{a.date}.json"), "w"), ensure_ascii=False, indent=0)
    texts_file(ALL + R5, J, a.date, os.path.join(a.out, f"audit_texts_{a.date}.json"))
    if a.worklist_r5: summ["round5"]["worklist"] = worklist_r5(R5, J, a.worklist_r5)
    if a.worklist: summ["worklist"] = dict(zip(("pool", "n"), worklist(F, H, a.date, a.worklist)))
    if a.worklist_new: summ["worklist_new"] = dict(pool=worklist_new([f for f in ALL if f["kind"] != "terminology"], H, a.date, a.worklist_new))
    if a.worklist_terms: summ["worklist_terms"] = dict(pool=worklist_terms(ALL, J, a.worklist_terms))
    json.dump(summ, open(os.path.join(a.out, f"audit_{a.date}_summary.json"), "w"), ensure_ascii=False, indent=1)
    open_ = sum(1 for f in ALL if not f["likely_equivalent"]) + sum(1 for f in R5 if R5_ON.get(f["kind"]))
    print(f"{len(ALL)} findings {summ['by_kind']} on {summ['limitations_with_any_finding']} of {S['n_limitations']} limitations; "
          f"{summ['likely_equivalent']['number']} number findings likely equivalent; {len(P)} terminology pairs; "
          f"recall {summ['recall']['limitations']}/{len(R)} known limitations; Keytruda {'found' if summ['keytruda_bonus']['found'] else 'not found'}; "
          f"fresh items with a language/number problem: {fr['with_language_or_number'] if fr else '-'} of {fr['items'] if fr else '-'}"
          f"{'; with a terminology notice: ' + str(fr['with_terminology']) if fr else ''}; round 5 (R15, apart): {summ['round5']['by_kind']}")
    print("wrote " + ", ".join(os.path.join(a.out, n) for n in (f"audit_{a.date}.json", f"audit_{a.date}_summary.json",
          f"audit_texts_{a.date}.json", f"lang_stats_{a.date}.json.gz") + ((f"term_pairs_{a.date}.json",) if not a.terms else ())))
    return 1 if a.fail_on_findings and open_ else 0


if __name__ == "__main__":
    sys.exit(main())
