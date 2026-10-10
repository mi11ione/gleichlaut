"""Flag triage for the review page: each finding of a flagged draft is sorted into "check" or "probably fine" by four
fixed, transparent rules. Display only: the verdict, the findings and every metric stay exactly as the frozen guards
produced them; a "probably fine" finding is shown collapsed and last, never hidden.

Rules (each one is also stated in the page legend, in the interface language):
  T1 vocabulary   a Vocabulary (out-of-vocabulary, G7) finding whose every word is a well-formed target-language word:
                  letters of the target alphabet only (no ä/ö/ß, no ü in Italian), at least 4 letters, no German letter
                  sequence (sch, ck, tz, -ung, -keit, -heit, -lich, -isch), not a word of the new German text and not
                  sharing its first 8 letters with one (hormonsensible / hormonsensitivem stays "check"), and, when capitalised,
                  not starting with the first 4 letters of a German word of the text of 6 letters or more unless the old
                  target text already has the word (Folguer / Folgore for Folgender: a German word left garbled, stays
                  "check"; the lower-case cognate ophtalmochirurgiens stays probably fine).
  T2 modal        a modal-verb (obligation) finding where the draft's extra 'doit/doivent … / deve/devono …' equals the
                  change in German 'ist/sind … zu <verb>' constructions (German necessity without a modal verb, which the
                  slot check does not count as one), and the text with the extra modal (the draft when the German adds, the
                  old text when it removes) contains 'doit/doivent être' or 'deve/devono essere'.
  T3 numbers      a numbers finding where the draft changes exactly the same number values as the German (counting number
                  words 2-12 as numbers and a decimal comma as a decimal point).
  T4 acronyms     a German-left / copied-from-German (G1, G5) finding whose every word, as written in the draft, is a Roman
                  numeral or an acronym (at least 2 capitals, capitals >= half of its letters, no umlaut).
  T5 numbers outside the change  a lock (outside-edit) finding whose every changed passage consists of numbers only, the
                  old ones being exactly values the German change removes and the new ones exactly values it adds (Ocrevus
                  944.61 -> 731.07: a price the German changes in another sentence).
  T6 orthographic a change-not-applied (G2) finding where the German change is orthographic only: the old and new German
                  are equal after folding case, umlauts / ß, hyphens, spaces and punctuation (Zeitpunkt -> Zeit-punkt), or
                  every word differs only by an inflectional ending (-e, -n, -en, -s, -es, -er, -em, -t, -et, -st) and at
                  most one vowel of the stem (bedürfen -> bedarf, erste -> erst, Monaten -> Monate).
  T7 negation     a negation finding that disappears when negation is recounted the way a reader counts it: 'nicht-' as a
                  word prefix (nicht-kleinzelligem) is not a negation, a French two-part negation (ne … pas, n' … jamais,
                  aucun … ne) counts once, and 'personne' as a noun (la personne assurée) is not a negation; the draft then
                  changes the count exactly as the German does.
  T8 same values  a numbers finding whose added and removed values are the same on both sides and only how often a value
                  occurs differs (Kyprolis: German adds 20481 twice, the draft once), or a finding whose before and after
                  are identical.
Every other finding (content lost, duplication, terminology, pipeline status, the correction notice, and any lock, G2,
negation or numbers finding outside these rules) is always "check".

level(v): the three-level register status, display only: "ready" (the frozen verdict), "fine" (flagged, every finding
probably fine), "check" (flagged, at least one finding to check). Flagged drafts stay flagged in every count."""
import re
from collections import Counter
from .. import core
from . import explain

RULES = ("T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8")
ALPHA = {"fr": "a-zàâçéèêëîïôûùüÿœæ", "it": "a-zàèéìíîòóùú"}
GERMANISH = re.compile(r"sch|ck|tz|ung$|keit$|heit$|lich$|isch$", re.I)
ISTZU = re.compile(r"\b(?:ist|sind)\b[^.;:]{0,120}?\bzu\s+\w+(?:en|ern|eln)\b", re.I)
MUST_BE = {"fr": re.compile(r"\b(?:doit|doivent|devra|devront)\s+(?:\w+\s+)?être\b", re.I),
           "it": re.compile(r"\b(?:deve|devono|dovrà|dovranno)\s+(?:\w+\s+)?essere\b", re.I)}
ROMAN = re.compile(r"^(?=[IVXLC]+$)C{0,3}(?:XC|XL|L?X{0,3})(?:IX|IV|V?I{0,3})$")


def _words(detail):
    """'G7: a, b, c' -> ['a', 'b', 'c']"""
    return [w.strip() for w in detail.split(":", 1)[-1].split(",") if w.strip()]


GERMAN_STEM = 4       # T1: a capitalised word that starts like a German word of the text (>= 6 letters) is a German word cut
                      # or garbled ('Folguer' / 'Folgore' / 'Folgente' for 'Folgender'), not a well-formed target word; a
                      # lower-case cognate ('ophtalmochirurgiens' next to 'Ophthalmochirurgen') stays well-formed


def well_formed(w, lang, de_new, old=""):
    if len(w) < 4 or lang not in ALPHA: return False
    if not re.fullmatch(f"[{ALPHA[lang]}]+(?:[-'’][{ALPHA[lang]}]+)*", w.lower()): return False
    if GERMANISH.search(w): return False
    lw = w.lower()
    for g in set(re.findall(r"\w+", de_new.lower())):
        if g == lw or (len(lw) >= 8 and len(g) >= 8 and g[:8] == lw[:8]): return False
        if w[:1].isupper() and len(g) >= 6 and g[:GERMAN_STEM] == lw[:GERMAN_STEM] and not re.search(r"(?<!\w)" + re.escape(lw) + r"(?!\w)", old.lower()):
            return False
    return True


def acronym(w):
    if ROMAN.match(w): return True
    letters = [c for c in w if c.isalpha()]
    caps = sum(c.isupper() for c in letters)
    return caps >= 2 and caps * 2 >= len(letters) and not re.search(r"[äöüÄÖÜß]", w)


def _istzu(x):
    return len(ISTZU.findall(x["de_new"])) - len(ISTZU.findall(x["de_old"]))


def _modal_delta(s, lang, k="MUST"):
    return core.lock.slots(s, lang)["modal"][k]


def _num_delta(a, b, lang):
    va, vb = explain.values(a, lang), explain.values(b, lang)
    return Counter({k: vb[k] - va[k] for k in set(va) | set(vb) if vb[k] != va[k]})


def rule(f, v):
    """-> rule id ("T1".."T4") when the finding is probably fine, else None."""
    L, d = v["lang"], f.get("detail") or ""
    if L not in ("fr", "it") or not v.get("draft"): return None
    gid = f["gid"]
    if gid == "g7":
        ws = _words(d)
        if ws and all(well_formed(explain.case_in(v["draft"], w), L, v["de_new"], v.get("tgt_old") or "") for w in ws): return "T1"
    if gid in ("g1", "g5"):
        ws = _words(d)
        if ws and all(acronym(explain.case_in(v["draft"], w)) for w in ws): return "T4"
    if gid == "slot" and d.startswith("Slots: modal:MUST"):
        dt = _modal_delta(v["draft"], L) - _modal_delta(v["tgt_old"], L)
        dd = _modal_delta(v["de_new"], "de") - _modal_delta(v["de_old"], "de")
        iz = _istzu(v)
        if iz and dt - dd == iz and MUST_BE[L].search(v["draft"] if iz > 0 else v["tgt_old"]): return "T2"
    if gid == "slot" and d.startswith("Slots: nums"):
        dd, dt = _num_delta(v["de_old"], v["de_new"], "de"), _num_delta(v["tgt_old"], v["draft"], L)
        if dd == dt: return "T3"
        if _signs(dd) == _signs(dt): return "T8"
    if gid == "lock" and _lock_numbers(d, v): return "T5"
    if gid == "g2" and _orthographic(d): return "T6"
    if gid == "slot" and d.startswith("Slots: neg") and _neg_ok(v): return "T7"
    pairs = PAIR.findall(d) if gid in ("lock", "g2") else []
    if pairs and all(" ".join(a.split()) == " ".join(b.split()) for a, b in pairs): return "T8"
    return None


def _signs(c):
    """{value: +1 | -1}: which values a change adds and which it removes (ignoring how often)."""
    return {k: (1 if n > 0 else -1) for k, n in c.items() if n}


PAIR = re.compile(r"«([^«»]*)» -> «([^«»]*)»")
NUMTOK = re.compile(r"^(?:\d+(?:[.,'’ ]\d+)*|[.,'’%-])$")


def _lock_numbers(d, v):
    """T5: every outside-edit passage changes numbers only, exactly the values the German change replaces."""
    pairs = PAIR.findall(d)
    if not pairs: return False
    dd = _num_delta(v["de_old"], v["de_new"], "de")
    gone, came = {k for k, n in dd.items() if n < 0}, {k for k, n in dd.items() if n > 0}
    for u, w in pairs:
        if not any(re.search(r"\d", t) for t in (u, w)): return False
        if not all(NUMTOK.match(t) for t in (u + " " + w).split()): return False
        vu, vw = set(explain.values(u, "de")), set(explain.values(w, "de"))
        if not (vu <= gone and vw <= came and (vu or vw)): return False
    return True


FOLD = str.maketrans({"ä": "a", "ö": "o", "ü": "u", "à": "a", "é": "e", "è": "e"})
ENDINGS = ("", "e", "n", "en", "s", "es", "er", "em", "t", "et", "st")
VOWELS = set("aeiouy")


def _fold(s, keep_space=False):
    s = s.lower().replace("ß", "ss").translate(FOLD)
    s = re.sub(r"[^\w\s]|_", "", s)
    return re.sub(r"\s+", " ", s).strip() if keep_space else re.sub(r"\s+", "", s)


def _stems(w):
    return {w[:len(w) - len(e)] for e in ENDINGS if w.endswith(e) and len(w) - len(e) >= 3}


def _inflected(a, b):
    """a, b (folded words) differ only by an inflectional ending and at most one stem vowel."""
    if a == b: return True
    for x in _stems(a):
        for y in _stems(b):
            if x == y: return True
            if len(x) == len(y) and sum(p != q for p, q in zip(x, y)) == 1 and \
               all(p in VOWELS and q in VOWELS for p, q in zip(x, y) if p != q): return True
    return False


def _orthographic(d):
    """T6: the German change of a G2 finding is orthographic or inflectional only."""
    m = PAIR.search(d)
    if not m: return False
    u, w = m.groups()
    if _fold(u) == _fold(w): return True
    A, B = _fold(u, True).split(), _fold(w, True).split()
    return bool(A) and len(A) == len(B) and all(_inflected(a, b) for a, b in zip(A, B))


NICHT_PREFIX = re.compile(r"\bnicht\s*-\s*(?=\w)", re.I)
FR_PART = r"(?:pas|plus|jamais|rien|aucun\w*|personne|nul\w*|guère)"
FR_PAIR = re.compile(r"\b(?:ne|n')\s+(?:\S+\s+){0,5}?" + FR_PART + r"\b|\b(?:aucun\w*|personne|rien|nul\w*)\s+(?:\S+\s+){0,5}?(?:ne|n')(?=\s|\b)")
FR_NOUN = re.compile(r"\b(?:la|une|chaque|toute|cette|de|d'|l')\s*personne\b|\bpersonnes?\s+(?:assurée|concernée|traitée)s?\b")


def _neg(s, lang):
    """The negation count of the slot check, recounted: nicht- prefixes dropped, French two-part negations once,
    'personne' as a noun dropped."""
    n = core.lock.slots(s, lang)["neg"]
    if lang == "de": return n - len(NICHT_PREFIX.findall(s))
    if lang == "fr":
        t = re.sub(r"(\w)'", r"\1' ", s.lower().replace("’", "'"))
        nouns = len(FR_NOUN.findall(t)); t = FR_NOUN.sub(" nom ", t)
        return n - nouns - len(FR_PAIR.findall(t))
    return n


def _neg_ok(v):
    L = v["lang"]
    raw = core.lock.slots(v["de_new"], "de")["neg"] - core.lock.slots(v["de_old"], "de")["neg"], \
        core.lock.slots(v["draft"], L)["neg"] - core.lock.slots(v["tgt_old"], L)["neg"]
    fix = _neg(v["de_new"], "de") - _neg(v["de_old"], "de"), _neg(v["draft"], L) - _neg(v["tgt_old"], L)
    return fix[0] == fix[1] and fix != raw


def level(v):
    """-> "ready" | "fine" | "check" | "human" (display only; see the module docstring)."""
    if v.get("status") != "flagged": return v.get("status") or "ready"
    T = [t for f, t in zip(v.get("findings", []), triage(v)) if f["gid"] != "corr"]
    return "fine" if T and all(T) else "check"


def triage(v):
    """-> [rule id or None] per finding of v["findings"] (the 'corr' notice is always None)."""
    if v.get("status") != "flagged": return [None] * len(v.get("findings", []))
    return [None if f["gid"] in ("corr", "record") else rule(f, v) for f in v["findings"]]
