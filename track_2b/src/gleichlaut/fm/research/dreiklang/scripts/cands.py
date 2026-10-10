"""Dreiklang shared candidate generator (code, no model).

Candidates = census.py v1 lexicons (digits, number words, "one" next to an operator or quantity unit) plus fixes
for the census noise classes that are *candidate-level* (they decide which spans exist, not how they are typed):
  - digits glued to letters are kept when a unit follows ("de15 kg"), else skipped as marker codes (HER2, v1.1)
  - digits after a comma glued to a letter ("semaine,3 mg") and after "/" ("12/24/36", "mg/40 ml") are kept
  - compound number words 13-19 and tens no longer split ("vierzehn" was 4, "achtzehn" 8, "vierzig" 4)
  - FR/IT 13-19 and tens added; interval adjectives ("bimestrale", "trimestriel", "halbjährlich") give value+unit
  - range partners lend their unit to a bare lower bound ("15 - < 60 kg", "ab 15 bis unter 30 kg")
Typing (is it a condition, which subject/operator) is NOT done here: that is the model's (S1) or regex v2's (S2) job.
Dates are masked as in census and are not candidates.
"""
import re, sys, os
sys.path.insert(0, os.path.expanduser("~/Desktop/hackapertus/spikes/gleichlaut/scripts"))
import census as C  # noqa: E402

LANGS = C.LANGS

# number words v2 (whole-word, value 1 handled by census ONE)
W2 = {
    "de": {"zwei": 2, "zweit\\w*": 2, "drei": 3, "dritt(?!el)\\w*": 3, "vier": 4, "viert(?!el)\\w*": 4, "fünf": 5, "fünft\\w*": 5,
           "sechs": 6, "sechst\\w*": 6, "sieben": 7, "siebt\\w*": 7, "acht": 8, "achte[nrsm]?": 8, "neun": 9, "neunt\\w*": 9,
           "zehn": 10, "zehnt\\w*": 10, "elf": 11, "zwölf": 12, "dreizehn": 13, "vierzehn": 14, "fünfzehn": 15, "sechzehn": 16,
           "siebzehn": 17, "achtzehn": 18, "neunzehn": 19, "zwanzig": 20, "dreissig": 30, "vierzig": 40, "fünfzig": 50,
           "sechzig": 60, "hundert": 100,
           # compounds carrying a unit: zweiwöchig, dreimonatig, vierwöchentlich, zweijährig, zweimal ...
           "(?:zwei|drei|vier|fünf|sechs|acht|zwölf)(?:wöch\\w*|monat\\w*|jähr\\w*|tägi\\w*|mal\\w*|fach\\w*|stündi\\w*)": None},
    "fr": {"deux": 2, "deuxi[eè]mes?": 2, "second(?:e|es|s)?": 2, "trois": 3, "troisi[eè]mes?": 3, "quatre": 4,
           "quatri[eè]mes?": 4, "cinq": 5, "cinqui[eè]mes?": 5, "six": 6, "sixi[eè]mes?": 6, "sept": 7, "huit": 8, "neuf": 9,
           "dix": 10, "onze": 11, "douze": 12, "treize": 13, "quatorze": 14, "quinze": 15, "seize": 16, "dix-sept": 17,
           "dix-huit": 18, "dix-neuf": 19, "vingt": 20, "trente": 30, "quarante": 40, "cinquante": 50, "soixante": 60, "cent": 100},
    "it": {"due": 2, "second[aei]": 2, "tre": 3, "terz[aoei]": 3, "quattro": 4, "quart[aei]": 4, "cinque": 5, "quint[aoei]": 5,
           "sei": 6, "sest[aoei]": 6, "sette": 7, "otto": 8, "nove": 9, "dieci": 10, "undici": 11, "dodici": 12, "tredici": 13,
           "quattordici": 14, "quindici": 15, "sedici": 16, "diciassette": 17, "diciotto": 18, "diciannove": 19, "venti": 20,
           "trenta": 30, "quaranta": 40, "cinquanta": 50, "sessanta": 60, "cento": 100},
}
W2_EXTRA = {"it": [(r"secondo(?=\s+" + C.QTY_UNITS + ")", 2)]}
# interval adjectives -> (value, unit)
ADJ = {
    "de": [(r"zweimonatlich\w*", 2, "month"), (r"dreimonatlich\w*", 3, "month"), (r"vierteljährlich\w*", 3, "month"),
           (r"quartalsweise", 3, "month"), (r"halbjährlich\w*", 6, "month"), (r"zweiwöchentlich\w*", 2, "week")],
    "fr": [(r"bimestriel\w*", 2, "month"), (r"trimestriel\w*", 3, "month"), (r"semestriel\w*", 6, "month"),
           (r"bihebdomadaire\w*", 2, "week")],
    "it": [(r"bimestral\w*", 2, "month"), (r"trimestral\w*", 3, "month"), (r"semestral\w*", 6, "month"),
           (r"bisettimanal\w*", 2, "week")],
}
NUM2 = re.compile(r"(\d{1,3}(?:'\d{3})+(?!\d)|\d{1,3}(?: \d{3})+(?![\d.,])|\d+(?:[.,]\d+)?)")
TIME_U = {"year", "month", "week", "day", "hour"}
WORD_UNIT_RE = [(c, re.compile(p, re.I)) for c, p in C.UNITS[18:23]]  # year..hour


def unit2(s, en, hops=3):
    u = C.unit_after(s, en)
    if u:
        return u
    mc = COMPOUND.match(s[en:en + 40])  # DE compounds: "Behandlungszyklen", "Therapiewochen", "Lebensmonate"
    if mc:
        return mc.lastgroup
    mo = re.match(r"(?:\.|°|º|\.?\s*-)(?=\s*\w)", s[en:en + 3])  # ordinals: "12. Lebensjahr", "16° anno"
    if mo:
        u = C.unit_after(s, en + mo.end())
        if u in TIME_U:
            return u
    m = re.match(r"\s*(?:-|–|/|bis(?: unter| und mit| zu)?|à(?: moins de)?|a(?: meno di)?|e|und|et|al|fino a)\s*(?:<\s*|≤\s*)?"
                 r"(\d+(?:[.,]\d+)?)", s[en:en + 30], re.I)
    if m and hops > 0:
        u = unit2(s, en + m.end(), hops - 1)
        if u:
            return u
    # time unit word right before the number: "in Woche 0", "an Tag 15", "semaine 0", "il giorno 15", "Zyklus 1"
    st = st_hint(s, en)
    mb = UNIT_BEFORE.search(s[max(0, st - 25):st])
    if mb:
        return mb.lastgroup
    return None


COMPOUND = re.compile(r"\s*-?\s*[A-Za-zäöü]{3,}(?:(?P<cycle>zykl\w*)|(?P<week>woche\w*)|(?P<month>monat\w*)|(?P<year>jahr\w*)"
                      r"|(?P<day>tage?n?)\b)", re.I)
UNIT_BEFORE = re.compile(r"\b(?:(?P<week>Woche|semaine|settimana)|(?P<day>Tag|jour|giorno)|(?P<month>Monat|mois|mese)"
                         r"|(?P<cycle>Zyklus|cycle|ciclo))\s+$", re.I)


def st_hint(s, en):
    """start of the number token ending at en"""
    i = en
    while i > 0 and (s[i - 1].isalnum() or s[i - 1] in ".,'"):
        i -= 1
    return i


def candidates(text, lang):
    """list of dicts: a, b (offsets into s), surface, v (value), u (unit class or None), kind; and s (normalised text)."""
    s = C.norm(text)
    dates = []
    for m in C.DATE_NUM.finditer(s):
        dates.append((m.start(), m.end()))
    for m in C.MONTH_RE[lang].finditer(s):
        dates.append((m.start(), m.end()))
    ms = list(s)
    for a, b in dates:
        for i in range(a, b):
            ms[i] = "#"
    ms = "".join(ms)
    out = []
    for m in NUM2.finditer(ms):
        st, en = m.start(), m.end()
        prev = ms[st - 1] if st > 0 else " "
        prev2 = ms[st - 2] if st > 1 else " "
        if prev.isdigit() or prev in "'^":
            continue
        if prev in ".," and (prev2.isdigit() or prev == "."):
            continue  # decimal tail / dotted ids (832.112.31)
        if re.match(r"[A-Za-zÀ-ÿ]", prev):
            # glued to a letter: keep only typo-glued function words before a unit ("de15 kg"); skip HER2, v1.1, FEV1, m2
            if not (C.unit_after(ms, en) and re.search(r"(?:^|[\s(])(?:de|à|da|di|a|ab|von|bis)$", ms[max(0, st - 5):st], re.I)):
                continue
        v = C.num_value(m.group(1))
        if v is None:
            continue
        out.append(dict(a=st, b=en, surface=m.group(1), v=v, u=unit2(ms, en), kind="digit"))
    low = ms.lower()
    low = re.sub(C.BOTH[lang], lambda m: "~" * len(m.group(0)), low)
    taken = []
    for pat, v, unit in ADJ[lang]:
        for m in re.finditer(r"\b(?:" + pat + r")\b", low):
            out.append(dict(a=m.start(), b=m.end(), surface=s[m.start():m.end()], v=v, u=unit, kind="adj"))
            taken.append((m.start(), m.end()))
    pats = list(W2[lang].items()) + W2_EXTRA.get(lang, [])
    for pat, v in pats:
        rx = (r"\b(?:" + pat + r")\b") if not pat.startswith("secondo") else (r"\b" + pat)
        for m in re.finditer(rx, low):
            if any(a <= m.start() < b for a, b in taken):
                continue
            w = m.group(0)
            wu = None
            if v is None:  # compound with unit
                base = re.match(r"zwei|drei|vier|fünf|sechs|acht|zwölf", w).group(0)
                v = {"zwei": 2, "drei": 3, "vier": 4, "fünf": 5, "sechs": 6, "acht": 8, "zwölf": 12}[base]
                rest = w[len(base):]
                for c, rx2 in (("week", r"wöch"), ("month", r"monat"), ("year", r"jähr"), ("day", r"tägi"), ("hour", r"stündi"), ("times", r"mal|fach")):
                    if re.match(rx2, rest):
                        wu = c
                out.append(dict(a=m.start(), b=m.end(), surface=s[m.start():m.end()], v=v, u=wu, kind="word"))
                v = None
                continue
            out.append(dict(a=m.start(), b=m.end(), surface=s[m.start():m.end()], v=v, u=unit2(low, m.end()), kind="word"))
    for m in re.finditer(C.ONE[lang], low):
        u = C.unit_after(low, m.end())
        op, txt = C.op_before(low, m.start(), lang, strong_only=True, unit=u)
        qty = re.match(r"\s*(?:[^\s\d.;:]+\s+)?" + C.QTY_UNITS, low[m.end():m.end() + 40], re.I)
        if op or qty or m.group(0) == "einmal":
            out.append(dict(a=m.start(), b=m.end(), surface=s[m.start():m.end()], v=1, u=u, kind="one"))
    out.sort(key=lambda x: (x["a"], -x["b"]))
    # drop spans nested in an earlier span
    res, last = [], -1
    for x in out:
        if x["a"] < last:
            continue
        res.append(x)
        last = x["b"]
    return s, res


# ---------------------------------------------------------------- unit normalisation for comparison
TO_DAYS = {"year": 365, "month": 30, "week": 7, "day": 1, "hour": 1 / 24}


def norm_value_unit(v, u):
    if u in TO_DAYS:
        x = v * TO_DAYS[u]
        return round(x, 3), "day"
    if u == "ug":
        return round(v / 1000, 6), "mg"
    if u == "g":
        return round(v * 1000, 3), "mg"
    return v, (u or "")


def context(s, a, b, w=220):
    """±w chars snapped to word boundaries, span marked ⟦ ⟧."""
    lo = max(0, a - w)
    hi = min(len(s), b + w)
    if lo > 0:
        sp = s.find(" ", lo)
        lo = sp + 1 if 0 <= sp < a else lo
    if hi < len(s):
        sp = s.rfind(" ", b, hi)
        hi = sp if sp > b else hi
    return ("… " if lo > 0 else "") + s[lo:a] + "⟦" + s[a:b] + "⟧" + s[b:hi] + (" …" if hi < len(s) else "")
