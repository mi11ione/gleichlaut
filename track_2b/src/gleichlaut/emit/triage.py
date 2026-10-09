"""Flag triage for the review page: each finding of a flagged draft is sorted into "check" or "probably fine" by four
fixed, transparent rules. Display only: the verdict, the findings and every metric stay exactly as the frozen guards
produced them; a "probably fine" finding is shown collapsed and last, never hidden.

Rules (each one is also stated in the page legend, in the interface language):
  T1 vocabulary   a Vocabulary (out-of-vocabulary, G7) finding whose every word is a well-formed target-language word:
                  letters of the target alphabet only (no ä/ö/ß, no ü in Italian), at least 4 letters, no German letter
                  sequence (sch, ck, tz, -ung, -keit, -heit, -lich, -isch), not a word of the new German text and not
                  sharing its first 8 letters with one (hormonsensible / hormonsensitivem stays "check").
  T2 modal        a modal-verb (obligation) finding where the draft's extra 'doit/doivent … / deve/devono …' equals the
                  change in German 'ist/sind … zu <verb>' constructions (German necessity without a modal verb, which the
                  slot check does not count as one), and the text with the extra modal (the draft when the German adds, the
                  old text when it removes) contains 'doit/doivent être' or 'deve/devono essere'.
  T3 numbers      a numbers finding where the draft changes exactly the same number values as the German (counting number
                  words 2-12 as numbers and a decimal comma as a decimal point).
  T4 acronyms     a German-left / copied-from-German (G1, G5) finding whose every word, as written in the draft, is a Roman
                  numeral or an acronym (at least 2 capitals, capitals >= half of its letters, no umlaut).
Every other finding (lock, change not applied, content lost, duplication, terminology, negation, pipeline status, the
correction notice) is always "check"."""
import re
from collections import Counter
from .. import core
from . import explain

RULES = ("T1", "T2", "T3", "T4")
ALPHA = {"fr": "a-zàâçéèêëîïôûùüÿœæ", "it": "a-zàèéìíîòóùú"}
GERMANISH = re.compile(r"sch|ck|tz|ung$|keit$|heit$|lich$|isch$", re.I)
ISTZU = re.compile(r"\b(?:ist|sind)\b[^.;:]{0,120}?\bzu\s+\w+(?:en|ern|eln)\b", re.I)
MUST_BE = {"fr": re.compile(r"\b(?:doit|doivent|devra|devront)\s+(?:\w+\s+)?être\b", re.I),
           "it": re.compile(r"\b(?:deve|devono|dovrà|dovranno)\s+(?:\w+\s+)?essere\b", re.I)}
ROMAN = re.compile(r"^(?=[IVXLC]+$)C{0,3}(?:XC|XL|L?X{0,3})(?:IX|IV|V?I{0,3})$")


def _words(detail):
    """'G7: a, b, c' -> ['a', 'b', 'c']"""
    return [w.strip() for w in detail.split(":", 1)[-1].split(",") if w.strip()]


def well_formed(w, lang, de_new):
    if len(w) < 4 or lang not in ALPHA: return False
    if not re.fullmatch(f"[{ALPHA[lang]}]+(?:[-'’][{ALPHA[lang]}]+)*", w.lower()): return False
    if GERMANISH.search(w): return False
    lw = w.lower()
    for g in set(re.findall(r"\w+", de_new.lower())):
        if g == lw or (len(lw) >= 8 and len(g) >= 8 and g[:8] == lw[:8]): return False
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
        if ws and all(well_formed(explain.case_in(v["draft"], w), L, v["de_new"]) for w in ws): return "T1"
    if gid in ("g1", "g5"):
        ws = _words(d)
        if ws and all(acronym(explain.case_in(v["draft"], w)) for w in ws): return "T4"
    if gid == "slot" and d.startswith("Slots: modal:MUST"):
        dt = _modal_delta(v["draft"], L) - _modal_delta(v["tgt_old"], L)
        dd = _modal_delta(v["de_new"], "de") - _modal_delta(v["de_old"], "de")
        iz = _istzu(v)
        if iz and dt - dd == iz and MUST_BE[L].search(v["draft"] if iz > 0 else v["tgt_old"]): return "T2"
    if gid == "slot" and d.startswith("Slots: nums"):
        if _num_delta(v["de_old"], v["de_new"], "de") == _num_delta(v["tgt_old"], v["draft"], L): return "T3"
    return None


def triage(v):
    """-> [rule id or None] per finding of v["findings"] (the 'corr' notice is always None)."""
    if v.get("status") != "flagged": return [None] * len(v.get("findings", []))
    return [None if f["gid"] in ("corr", "record") else rule(f, v) for f in v["findings"]]
