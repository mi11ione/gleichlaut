"""Gleichlaut S1 census (no model, stdlib only).

Reads the BAG ePL FHIR NDJSON publication (DE/FR/IT), aligns every ClinicalUseDefinition (CUD = one SL
limitation) by id, extracts hard facts per language and flags cross-language disagreements:
  NUM    a numeric value (digits, cardinal/ordinal number words; "one" only next to an operator or a
         quantity/time unit) or a date that is missing in at least one language
  UNIT   a value present in all three languages whose unit classes disagree (both sides carry a unit)
  OP     a value present in all three whose operator classes (GE/GT/LE/LT) disagree. Operators are anchored
         just before the number (<=2 filler words) or right after it ("und älter", "ou plus", "al massimo");
         numbers in a range ("18 bis 75", "de 18 à 75", "tra 18 e 75", "18-75") default to GE/LE.
         OP = both sides explicit and different; OPMISS = explicit in some languages, none in another.
  NEG    negation counts (doubled negation collapsed, lexical negation "unzureichend/insuffisant" counted)
         differ by >=2, or one language has 0 and another has >=1
  ITEMS  list-item counts (bullets, a)/b) items, dash items after punctuation) differ, max >= 2
Run:  python3 -I census.py <data_dir> <out_dir>
"""
import json, re, sys, collections, os, unicodedata

LANGS = ["de", "fr", "it"]


# ---------------------------------------------------------------- loading
def load(path):
    out, names = {}, {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            b = json.loads(line)
            prod, cuds = None, []
            for e in b.get("entry", []):
                r = e["resource"]
                if r["resourceType"] == "MedicinalProductDefinition":
                    for n in r.get("name", []):
                        prod = prod or n.get("productName")
                elif r["resourceType"] == "ClinicalUseDefinition":
                    cuds.append(r)
            for r in cuds:
                out[r["id"]] = r["indication"]["diseaseSymptomProcedure"]["concept"]["text"]
                names.setdefault(r["id"], prod)
    return out, names


def norm(s):
    s = unicodedata.normalize("NFC", s)
    for ch in "   ":
        s = s.replace(ch, " ")
    s = s.replace("’", "'").replace("`", "'").replace("ß", "ss")
    s = re.sub(r"https?://\S+|www\.\S+", lambda m: " " * len(m.group(0)), s)
    return s


# ---------------------------------------------------------------- lexicons
UNITS = [  # (class, regex) matched right after a number
    ("mg/kg", r"mg\s*/\s*kg"), ("mg/m2", r"mg\s*/\s*m(?:2|²)"), ("kg/m2", r"kg\s*/\s*m(?:2|²)"),
    ("mmol/l", r"mmol\s*/\s*[lL]"), ("mg/dl", r"mg\s*/\s*d[lL]"), ("g/dl", r"g\s*/\s*d[lL]"), ("g/l", r"g\s*/\s*[lL]\b"),
    ("ug", r"(?:µg|μg|mcg|ug)\b"), ("mg", r"mg\b"), ("g", r"g\b"), ("kg", r"kg\b"), ("ml", r"m[lL]\b"),
    ("mmol", r"mmol\b"), ("umol", r"(?:µmol|μmol)\b"), ("pct", r"(?:%|Prozent|pour\s*cent|per\s*cento)"),
    ("IU", r"(?:I\.?E\.?|U\.?I\.?|IU)\b"), ("mmHg", r"mmHg"), ("cells", r"(?:/\s*(?:µl|μl|mm3|mm³)|x\s*10)"),
    # word units (index 18+), also used for "one + unit"
    ("year", r"(?:Lebensjahr\w*|Jahr\w*|-?jährig\w*|ans?\b|ann[ée]es?\b|anni\b|anno\b|-?enn[ei]\w*)"),
    ("month", r"(?:Monat\w*|-?monatig\w*|mois\b|mes[ei]\b)"),
    ("week", r"(?:Woche\w*|-?wöchig\w*|semaines?\b|settiman[ae]\b)"),
    ("day", r"(?:Tag\b|Tage\w*|-?tägig\w*|jours?\b|giorn[oi]\b)"),
    ("hour", r"(?:Stunde\w*|-?stündig\w*|heures?\b|or[ae]\b)"),
    ("cycle", r"(?:Zykl\w*|cycles?\b|cicl[oi]\b)"),
    ("dose", r"(?:Dos[ie]\w*|doses?\b|dos[ei]\b|Gabe\w*|administrations?\b|somministrazion[ei]\b)"),
    ("inj", r"(?:Injektion\w*|injections?\b|iniezion[ei]\b|Infusion\w*|perfusions?\b|infusion[ei]\b)"),
    ("tab", r"(?:Tablette\w*|comprimés?\b|compress[ae]\b|Kapsel\w*|capsules?\b|capsul[ae]\b)"),
    ("pack", r"(?:Packung\w*|emballages?\b|confezion[ei]\b|boîtes?\b)"),
    ("point", r"(?:Punkt\w*|points?\b|punt[oi]\b)"),
    ("times", r"(?:x\b|×|mal\b|fois\b|volt[ae]\b)"),
    ("line", r"(?:Linie\w*|lignes?\b|line[ae]\b)"),
]
CASED = {"IU", "g"}
UNIT_RE = [(c, re.compile(r"\s*-?\s*" + p, 0 if c in CASED else re.I)) for c, p in UNITS]
QTY_UNITS = "(?:" + "|".join(p for c, p in UNITS if c in
                             ("year", "month", "week", "day", "hour", "cycle", "dose", "inj", "tab", "pack", "times")) + ")"

WORDS = {  # value 1 excluded here (articles), handled by ONE
    "de": {r"zwei(?!fel)(?!\w*fach)\w*": 2, r"drei(?!ssig)(?!\w*fach)\w*": 3, r"dreissig\w*": 30,
           r"vier(?!tel)(?!\w*fach)\w*": 4, r"fünf(?!\w*fach)\w*": 5, r"sechs\w*": 6, r"sieben\w*": 7,
           r"acht(?!ung|e[nt]?\b|sam|tel)\w*": 8, r"neun\w*": 9, r"zehn(?!tel)\w*": 10, r"elf": 11, r"zwölf\w*": 12,
           r"zwanzig\w*": 20, r"zweit\w*": 2, r"dritt(?!el)\w*": 3},
    "fr": {r"deux": 2, r"deuxi[eè]mes?": 2, r"second(?:e|es|s)?": 2, r"trois": 3, r"troisi[eè]mes?": 3,
           r"quatre": 4, r"quatri[eè]mes?": 4, r"cinq": 5, r"cinqui[eè]mes?": 5, r"six": 6, r"sixi[eè]mes?": 6,
           r"sept": 7, r"huit": 8, r"dix": 10, r"onze": 11, r"douze": 12, r"vingt": 20, r"trente": 30},
    "it": {r"due": 2, r"second[aei]": 2, r"tre": 3, r"terz[aoei]": 3, r"quattro": 4, r"quart[aei]": 4,
           r"cinque": 5, r"quint[aoei]": 5, r"sei": 6, r"sest[aoei]": 6, r"sette": 7, r"otto": 8, r"nove": 9,
           r"dieci": 10, r"undici": 11, r"dodici": 12, r"venti": 20, r"trenta": 30},
}
WORD_EXTRA = {"it": [(r"secondo(?=\s+" + QTY_UNITS + ")", 2)]}
BOTH = {"de": r"\bbeide\w*", "fr": r"\b(?:les|des|aux|ces) deux\b(?!\s+(?:ans|mois|semaines|jours|cycles|doses|fois))",
        "it": r"\b(?:entrambi|entrambe|ambedue|tutti e due|tutte e due)\b"}
ONE = {"de": r"\b(?:ein|eine|einen|einem|einer|eines|einmal)\b", "fr": r"\b(?:un|une)\b", "it": r"\b(?:un|uno|una)\b|\bun'"}

NUM = re.compile(r"(?<![\w^/.,])(\d{1,3}(?:'\d{3})+(?!\d)|\d{1,3}(?: \d{3})+(?![\d.,])|\d+(?:[.,]\d+)?)")

MONTHS = {"de": "januar februar märz april mai juni juli august september oktober november dezember",
          "fr": "janvier février mars avril mai juin juillet août septembre octobre novembre décembre",
          "it": "gennaio febbraio marzo aprile maggio giugno luglio agosto settembre ottobre novembre dicembre"}
MONTH_RE = {l: re.compile(r"\b(\d{1,2})(?:\.|er|°|º)?\s+(" + "|".join(m.split()) + r")\s+(\d{4})", re.I)
            for l, m in MONTHS.items()}
DATE_NUM = re.compile(r"\b(\d{1,2})\.(\d{1,2})\.(\d{4})\b")

OPS = {  # order inside one class: longer first
    "de": [("LE", r"nicht mehr als|bis zu(?:m)?(?: maximal| höchstens)?|bis maximal|bis höchstens|bis und mit|kleiner\s*/\s*gleich|kleiner oder gleich|gleich oder kleiner als|höchst\w*|maxima\w*|max\.?|spätestens|innerhalb der letzten|innerhalb von|innerhalb|in den letzten|innert|≤|<=|⩽"),
           ("GE", r"grösser\s*/\s*gleich|grösser oder gleich|gleich oder grösser als|mindest\w*|wenigstens|minima\w*|min\.|ab dem|ab|≥|>=|⩾"),
           ("LT", r"weniger als|kleiner als|kleiner|niedriger als|tiefer als|kürzer als|unterhalb von|unterhalb|bis unter|unter|<"),
           ("GT", r"mehr als|grösser als|grösser|höher als|länger als|oberhalb von|oberhalb|über(?!\s*\S*\s*(?:Jahr|Monat|Woche|Tag))|>")],
    "fr": [("LE", r"pas plus de|inférieure?s? ou égale?s? à|égale?s? ou inférieure?s? à|au maximum|au plus tard|au plus|un maximum de|maxima\w*|maximum|max\.?|jusqu'à|jusqu'au|dans un délai de|dans les|au cours des|≤|<=|⩽"),
           ("GE", r"supérieure?s? ou égale?s? à|égale?s? ou supérieure?s? à|au moins|au minimum|un minimum de|minimum|minimale?s?|min\.|à partir de|à partir du|dès|≥|>=|⩾"),
           ("LT", r"moins de|inférieure?s? à|inférieure?s? au|en dessous de|au-dessous de|<"),
           ("GT", r"plus de|plus que|supérieure?s? à|supérieure?s? au|au-delà de|au-dessus de|>")],
    "it": [("LE", r"non più di|inferiore o uguale a(?:l|i|lla)?|minore o uguale a(?:l|i|lla)?|pari o inferiore a(?:l|i|lla)?|uguale o inferiore a(?:l|i|lla)?|al massimo|al più tardi|un massimo di|massim\w*|max\.?|fino a(?:l|d|i|lla)?|entro|nei|negli ultimi|negli|≤|<=|⩽"),
           ("GE", r"superiore o uguale a(?:l|i|lla)?|maggiore o uguale a(?:l|i|lla)?|pari o superiore a(?:l|i|lla)?|uguale o superiore a(?:l|i|lla)?|non meno di|almeno|al minimo|un minimo di|minim\w*|min\.|a partire da(?:l|i|lla)?|dai|dal|≥|>=|⩾"),
           ("LT", r"meno di|inferiore a(?:l|i|lla)?|inferiori a(?:l|i|lla)?|minore di|al di sotto d(?:i|el|ei)|sotto|<"),
           ("GT", r"più di|superiore a(?:l|i|lla)?|superiori a(?:l|i|lla)?|oltre|maggiore di|al di sopra d(?:i|el|ei)|sopra|>")],
}
OP_ALT = {l: "|".join(p for _, p in ops) for l, ops in OPS.items()}
OP_CLASS = {l: [(c, re.compile(r"^(?:" + p + r")$", re.I)) for c, p in ops] for l, ops in OPS.items()}
GAP = r"[^\s.;:\d]+\s+"
NEG_NEAR = {"de": r"\b(?:nicht|kein\w*)\b(?!-)[^,;.:]{0,40}$", "fr": r"\b(?:pas|jamais)\b[^,;.:]{0,40}$",
            "it": r"\bnon\b(?!-)\s+[^,;.:]{0,40}$"}
FLIP = {"GT": "LE", "GE": "LT", "LT": "GE", "LE": "GT"}
STRONG = {"de": r"mindest\w*|höchst\w*|maxima\w*|minima\w*|max\.|min\.|wenigstens|spätestens|nicht mehr als|mehr als|weniger als|länger als|kürzer als",
          "fr": r"au moins|au maximum|au minimum|au plus tard|au plus|un maximum de|un minimum de|maxima\w*|minima\w*|maximum|minimum|max\.|min\.|pas plus de|plus de|moins de",
          "it": r"almeno|al massimo|al minimo|al più tardi|un massimo di|un minimo di|massim\w*|minim\w*|max\.|min\.|non più di|non meno di|più di|meno di"}
OP_BEFORE = {l: [re.compile(r"(?:(?<![\w])(" + (OP_ALT[l] if g == "" else STRONG[l]) + r"))(?![\w])\s*" + g + r"$", re.I)
                 for g in ("", GAP, GAP + GAP, GAP + GAP + GAP)] for l in LANGS}
POST = {
    "de": [("GE", r"und älter|oder älter|und mehr|oder mehr|und darüber|oder darüber|oder höher|und höher|oder grösser|und grösser"),
           ("LE", r"oder weniger|und weniger|oder jünger|oder kleiner|und kleiner|maximal|höchstens")],
    "fr": [("GE", r"ou plus|et plus|ou davantage|et au-delà|ou au-delà|au moins|minimum|ou supérieure?s?"),
           ("LE", r"ou moins|au maximum|maximum|au plus|ou inférieure?s?")],
    "it": [("GE", r"o più|e più|e oltre|o oltre|o superiore|o maggiore|almeno|minimo"),
           ("LE", r"o meno|al massimo|massimo|o inferiore|o minore")],
}
POST_RE = {l: [(c, re.compile(r"^\s*(?:-?\s*[^\s.;:\d]+\s+)?(?:" + p + r")(?![\w])", re.I)) for c, p in ops]
           for l, ops in POST.items()}
RANGE_SEP = {"de": r"(?:-|–|bis und mit|bis)", "fr": r"(?:-|–|à)", "it": r"(?:-|–|a|al)"}
BETWEEN = {"de": r"zwischen", "fr": r"entre", "it": r"(?:tra|fra)"}
BETWEEN_AND = {"de": r"und", "fr": r"et", "it": r"e"}

NEG = {"de": r"\bnicht\w*|\bkein\w*|\bohne\b|\bnie\b|\bniemals\b|\bweder\b|\bnichts\b|\bun(?:zureichend|genügend|zulänglich|behandelt|vorbehandelt|verträglich|wirksam|kontrolliert)\w*|\bnaiv\w*|\bversagt\w*",
       "fr": r"\bpas\b|\bjamais\b|\baucun\w*|\bsans\b|\bnon\b|\bni\b|\brien\b|\bn[e'][^.;]{0,25}?\bplus\b(?! de\b)|\binsuffisa\w*|\binefficac\w*|\bintoléra\w*|\bna[iï]v\w*|\béchec\w*",
       "it": r"\bnon\b|\bnessun\w*|\bsenza\b|\bmai\b|\bné\b|\bniente\b|\bnulla\b|\binsufficien\w*|\binefficac\w*|\bintolleran\w*|\bnaïv\w*|\bnaiv\w*|\bfalliment\w*"}
# second marker of a doubled negation within the same clause is not counted
NEG_DOUBLE = {"de": r"\bnoch\b", "fr": r"\bni\b|\baucun\w*|\bjamais\b|\brien\b", "it": r"\bnessun\w*|\bné\b|\bmai\b|\bniente\b|\bnulla\b|\balcun\w*"}

ITEM = re.compile(r"[•▪●◦·]|(?:(?<=[:;,.]\s)|^)[-–—](?=\s)|(?:(?<=[\s:;(])|^)[a-h]\)(?=\s)")


# ---------------------------------------------------------------- extraction
def num_value(tok):
    t = tok.replace("'", "").replace(" ", "").replace(",", ".")
    try:
        v = float(t)
    except ValueError:
        return None
    return int(v) if v == int(v) else v


def unit_after(s, end):
    tail = s[end:end + 40]
    for c, rx in UNIT_RE:
        if rx.match(tail):
            return c
    return None


def op_class(lang, txt):
    for c, crx in OP_CLASS[lang]:
        if crx.match(txt.strip()):
            return c
    return None


STRONG_RE = {l: re.compile(r"^(?:" + STRONG[l] + r")$", re.I) for l in LANGS}
TIME_U = {"year", "month", "week", "day", "hour"}


def op_before(s, start, lang, strong_only=False, unit=None):
    head = s[max(0, start - 60):start]
    for rx in OP_BEFORE[lang]:
        m = rx.search(head)
        if not m:
            continue
        op = m.group(1)
        if lang == "de" and op.lower() == "über" and unit in TIME_U:
            continue  # "über 2 Jahre" = for 2 years, not "more than"
        strong = bool(STRONG_RE[lang].match(op))
        if strong_only and not strong:
            continue
        c = op_class(lang, op)
        if c and strong and re.search(NEG_NEAR[lang], head[max(0, m.start() - 60):m.start()], re.I):
            return FLIP[c], "neg+" + op
        return c, op
    return None, None


def op_after(s, end, lang):
    tail = s[end:end + 40]
    um = None
    for c, rx in UNIT_RE:
        um = rx.match(tail)
        if um:
            break
    rest = tail[um.end():] if um else tail
    for c, rx in POST_RE[lang]:
        m = rx.match(rest)
        if m:
            return c, m.group(0).strip()
    return None, None


def range_role(s, st, en, lang):
    """'lo' if the number opens a range, 'hi' if it closes one, else None."""
    tail = s[en:en + 40]
    head = s[max(0, st - 60):st]
    sep = RANGE_SEP[lang]
    unit_opt = r"(?:\s*[^\s\d.;:]{1,12})?"
    if re.match(unit_opt + r"\s*" + sep + r"\s*\d", tail, re.I):
        return "lo"
    if re.search(r"\d" + unit_opt + r"\s*" + sep + r"\s*$", head, re.I):
        return "hi"
    if re.search(r"\b" + BETWEEN[lang] + r"\s+(?:\S+\s+){0,2}$", head, re.I) and \
            re.match(unit_opt + r"\s*" + BETWEEN_AND[lang] + r"\s+(?:\S+\s+){0,2}\d", tail, re.I):
        return "lo"
    if re.search(r"\b" + BETWEEN[lang] + r"\s+(?:\S+\s+){0,3}\d+" + unit_opt + r"\s+" + BETWEEN_AND[lang] + r"\s+(?:\S+\s+){0,2}$", head, re.I):
        return "hi"
    return None


def classify_op(s, st, en, lang):
    op, txt = op_before(s, st, lang, unit=unit_after(s, en))
    if not op:
        op, txt = op_after(s, en, lang)
    explicit = bool(op)
    if not op:
        role = range_role(s, st, en, lang)
        if role == "lo":
            op, txt = "GE", "(range-lo)"
        elif role == "hi":
            op, txt = "LE", "(range-hi)"
    return op, txt, explicit


def facts(text, lang):
    s = norm(text)
    vals, dates = [], []
    for m in DATE_NUM.finditer(s):
        dates.append((int(m.group(3)), int(m.group(2)), int(m.group(1)), m.start(), m.end()))
    for m in MONTH_RE[lang].finditer(s):
        mi = MONTHS[lang].split().index(m.group(2).lower()) + 1
        dates.append((int(m.group(3)), mi, int(m.group(1)), m.start(), m.end()))
    ms = list(s)
    for d in dates:
        for i in range(d[3], d[4]):
            ms[i] = "#"
    ms = "".join(ms)
    for m in NUM.finditer(ms):
        st, en = m.start(), m.end()
        if st > 0 and re.match(r"[A-Za-zÀ-ÿ]", ms[st - 1]):
            continue  # marker codes glued to letters: HER2, CD30, T790M, FEV1
        v = num_value(m.group(1))
        if v is None:
            continue
        op, txt, ex = classify_op(ms, st, en, lang)
        vals.append(dict(v=v, u=unit_after(ms, en), op=op, opt=txt, ex=ex, a=st, b=en, kind="digit"))
    low = ms.lower()
    low = re.sub(BOTH[lang], lambda m: "~" * len(m.group(0)), low)
    pats = list(WORDS[lang].items()) + WORD_EXTRA.get(lang, [])
    for pat, v in pats:
        for m in re.finditer(r"\b(?:" + pat + r")\b" if not pat.startswith("secondo") else r"\b" + pat, low):
            op, txt, ex = classify_op(low, m.start(), m.end(), lang)
            wu = None
            for c, rx in UNIT_RE[18:]:  # unit inside a compound number word: "vierwöchig", "zweijährig"
                if re.search(rx.pattern.replace(r"\s*-?\s*", "", 1) + "$", m.group(0)[3:], rx.flags) and c in TIME_U:
                    wu = c
            vals.append(dict(v=v, u=wu or unit_after(low, m.end()), op=op, opt=txt, ex=ex, a=m.start(), b=m.end(), kind="word"))
    for m in re.finditer(ONE[lang], low):
        u = unit_after(low, m.end())
        op, txt = op_before(low, m.start(), lang, strong_only=True, unit=u)
        qty = re.match(r"\s*(?:[^\s\d.;:]+\s+)?" + QTY_UNITS, low[m.end():m.end() + 40], re.I)
        if op or qty or m.group(0) == "einmal":
            vals.append(dict(v=1, u=u, op=op, opt=txt, ex=bool(op), a=m.start(), b=m.end(), kind="one"))
    # negation, doubled negation collapsed
    neg = []
    low = re.sub(r"\b(?:non|nicht)[- ]?hodgkin", lambda m: "~" * len(m.group(0)), low)
    for m in re.finditer(NEG[lang], low):
        if re.match(NEG_DOUBLE[lang], m.group(0)) and neg and \
                m.start() - neg[-1][1] < 60 and not re.search(r"[.;:]", low[neg[-1][1]:m.start()]):
            continue
        neg.append((m.start(), m.end()))
    items = []
    for m in ITEM.finditer(s):
        prev = s[max(0, m.start() - 3):m.start()]
        if re.search(r"\d\s*$", prev):
            continue  # numeric range dash
        items.append((m.start(), m.end()))
    return dict(s=s, vals=vals, dates=dates, neg=neg, items=items)


# ---------------------------------------------------------------- comparison
def summarise(f):
    units = collections.defaultdict(set)
    for x in f["vals"]:
        if x["u"]:
            units[x["v"]].add(x["u"])
    return dict(vset=set(x["v"] for x in f["vals"]), units=units,
                ops=collections.Counter((x["op"], x["v"]) for x in f["vals"] if x["op"]),
                exops=collections.Counter((x["op"], x["v"]) for x in f["vals"] if x["op"] and x["ex"]),
                neg=len(f["neg"]), items=len(f["items"]), dates=collections.Counter(d[:3] for d in f["dates"]))


def snippet(s, a, b, w=80):
    return ("…" if a - w > 0 else "") + s[max(0, a - w):a] + "⟦" + s[a:b] + "⟧" + s[b:b + w] + ("…" if b + w < len(s) else "")


STOP = {"de": set("der die das und mit von den dem ist wird nicht bei für eine einer oder nach zur".split()),
        "fr": set("le la les des et du avec est pour une dans par au aux sur ou après".split()),
        "it": set("il di e con per che della del una gli dei nel alla sono dopo".split())}


def lang_guess(s):
    toks = re.findall(r"[a-zà-ÿ]+", s.lower())
    sc = {l: sum(t in STOP[l] for t in toks) for l in LANGS}
    return max(sc, key=sc.get), sc


def compare(cid, F):
    S = {l: summarise(F[l]) for l in LANGS}
    flags = []
    for l in LANGS:
        g, sc = lang_guess(F[l]["s"])
        if g != l and sc[g] >= 3:
            flags.append(dict(cat="LANG", key=l, detail=f"{l} slot reads as {g} (stopwords {sc})"))
    allv = set().union(*[S[l]["vset"] for l in LANGS])
    for v in sorted(allv, key=lambda x: float(x)):
        have = [l for l in LANGS if v in S[l]["vset"]]
        if len(have) < 3:
            flags.append(dict(cat="NUM", key=str(v), detail=f"value {v} only in {'/'.join(have)}"))
    for d in set().union(*[set(S[l]["dates"]) for l in LANGS]):
        have = [l for l in LANGS if d in S[l]["dates"]]
        if len(have) < 3:
            flags.append(dict(cat="NUM", key="date:%04d-%02d-%02d" % d, detail=f"date {d} only in {'/'.join(have)}"))
    for v in sorted(allv, key=lambda x: float(x)):
        if not all(v in S[l]["vset"] for l in LANGS):
            continue
        us = {l: S[l]["units"].get(v, set()) for l in LANGS}
        if all(us.values()) and (not (us["de"] & us["fr"]) or not (us["de"] & us["it"])):
            flags.append(dict(cat="UNIT", key=str(v), detail=f"value {v} units " + " ".join(f"{l}={sorted(us[l])}" for l in LANGS)))
        o = {l: sorted(set(k[0] for k in S[l]["ops"] if k[1] == v)) for l in LANGS}
        if not (o["de"] == o["fr"] == o["it"]):
            ex = {l: sorted(set(k[0] for k in S[l]["exops"] if k[1] == v)) for l in LANGS}
            # explicit-vs-explicit conflict: two languages both have explicit ops and the sets differ
            conflict = any(ex[a] and ex[b] and ex[a] != ex[b] for a, b in (("de", "fr"), ("de", "it"), ("fr", "it")))
            cat = "OP" if conflict else "OPMISS"
            flags.append(dict(cat=cat, key=str(v), detail=f"value {v} ops " + " ".join(f"{l}={o[l]}" for l in LANGS)))
    n = {l: S[l]["neg"] for l in LANGS}
    if max(n.values()) - min(n.values()) >= 2 or (min(n.values()) == 0 and max(n.values()) >= 1):
        flags.append(dict(cat="NEG", key="", detail="neg counts " + " ".join(f"{l}={n[l]}" for l in LANGS)))
    it = {l: S[l]["items"] for l in LANGS}
    if len(set(it.values())) > 1 and max(it.values()) >= 2:
        flags.append(dict(cat="ITEMS", key="", detail="item counts " + " ".join(f"{l}={it[l]}" for l in LANGS)))
    for fl in flags:
        fl["cid"] = cid
    return flags


def evidence(fl, F):
    out = {}
    for l in LANGS:
        f, s = F[l], F[l]["s"]
        if fl["key"].startswith("date:"):
            y, mo, d = map(int, fl["key"][5:].split("-"))
            out[l] = [snippet(s, x[3], x[4]) for x in f["dates"] if x[:3] == (y, mo, d)][:4] or ["(absent)"]
        elif fl["cat"] in ("NUM", "UNIT", "OP", "OPMISS"):
            hits = [x for x in f["vals"] if str(x["v"]) == fl["key"]]
            out[l] = [snippet(s, x["a"], x["b"]) + (f"  [op={x['op']}:{x['opt']}]" if x["op"] else "") +
                      (f" [unit={x['u']}]" if fl["cat"] == "UNIT" else "") for x in hits[:5]] or ["(absent)"]
        elif fl["cat"] == "LANG":
            out[l] = [s[:300]]
        elif fl["cat"] == "NEG":
            out[l] = [snippet(s, a, b, 50) for a, b in f["neg"]][:14]
        elif fl["cat"] == "ITEMS":
            out[l] = [snippet(s, a, b, 40) for a, b in f["items"]][:15]
    return out


def main():
    data, outd = sys.argv[1], sys.argv[2]
    T, names = {}, {}
    for l in LANGS:
        T[l], nm = load(os.path.join(data, f"sl-{l}.ndjson"))
        if l == "de":
            names = nm
    ids = sorted(set(T["de"]) & set(T["fr"]) & set(T["it"]))
    unaligned = {l: len(set(T[l]) - set(ids)) for l in LANGS}
    allflags, counts, cud_flagged = [], collections.Counter(), collections.Counter()
    for cid in ids:
        F = {l: facts(T[l][cid], l) for l in LANGS}
        fl = compare(cid, F)
        for x in fl:
            x["drug"] = names.get(cid)
            x["evidence"] = evidence(x, F)
        allflags += fl
        cats = set(x["cat"] for x in fl)
        for c in cats:
            cud_flagged[c] += 1
        if fl:
            cud_flagged["ANY"] += 1
        counts.update(x["cat"] for x in fl)
    os.makedirs(outd, exist_ok=True)
    with open(os.path.join(outd, "flags.jsonl"), "w", encoding="utf-8") as f:
        for i, x in enumerate(allflags):
            x["fid"] = i
            f.write(json.dumps(x, ensure_ascii=False) + "\n")
    with open(os.path.join(outd, "texts.json"), "w", encoding="utf-8") as f:
        json.dump({cid: dict({l: T[l][cid] for l in LANGS}, drug=names.get(cid)) for cid in ids}, f, ensure_ascii=False)
    summ = dict(n_cud=len(ids), unaligned=unaligned, n_flags=len(allflags), flags_by_cat=dict(counts),
                cuds_flagged=dict(cud_flagged))
    with open(os.path.join(outd, "census_summary.json"), "w") as f:
        json.dump(summ, f, indent=1)
    print(json.dumps(summ, indent=1))


if __name__ == "__main__":
    main()
