"""Recall of the congruence audit (gleichlaut.audit) on planted divergences: fault injection into the 6 Oct 2026 register.

Why: the audit's recall on the 10 known divergent limitations is circular (those were found by a numeric census whose
noise classes shaped the rules). Here faults of five pre-declared types are planted into otherwise unchanged copies of the
register and the unmodified audit is run on every copy. Deterministic (seed 20261010), stdlib only, no model, no network.

PROTOCOL (fixed in this file before the first run; also written into the output file)
  Register   the public SL feed of 6 Oct 2026, the snapshot the audit reads (--hist DIR, files 20261006-{de,fr,it}.json).
  Eligible   one representative per distinct (DE, FR, IT) text triple (the smallest id), and only limitations on which the
             baseline audit has no finding of any kind, so every finding on a copy is caused by the planted fault.
  Sampling   per type and target language (FR, IT): seeded shuffle of the eligible limitations that offer a site for the
             type, the first N (default 100) are taken; one site and one fault per limitation, drawn with the same rng.
  Sites      found by this file's own patterns, not by the audit's parser: a number (digits, or a number word 2..12) followed
             by a unit or quantity word (dose, time, age, weight, percentage, count) in the target text.
  Types
    number     one number in the target changed to another plausible value (n -> 2n, n+1, n-1, n/2, n+10; a decimal
               x -> 2x or x/2; a number word -> another number word 2..12)
    unit       one unit changed within its dimension, the number kept (mg <-> µg, g -> mg, kg -> g, ml -> dl;
               days -> weeks, weeks -> months, months -> weeks, years -> months, hours -> days)
    deletion   one number-bearing clause deleted from the target: a sentence (when the text has >= 2) or a comma clause
               (when its sentence has >= 2); the text keeps at least one other clause
    language   the whole target field replaced by the text of one of the two other language fields (50/50)
    typo       one typo right next to a number: in the word before it or in the unit word after it (or, for a number word,
               in the number word itself). Edits: glue (delete the separating space; not before a symbol unit, '15mg'
               is house style), delete one letter, double one letter, substitute one letter, transpose two letters
  Detection (strict, pre-declared; a finding on the copy's limitation, in the target language, that points to the fault)
    number     a number finding with the new value on the target side or the old value on the German side
    unit       a unit finding for the value whose unit was changed
    deletion   a number finding with a value of the deleted clause on the German side
    language   a language finding on the target field naming the source language
    typo       an editorial finding whose surface lies within 30 characters of the edit
  Also reported: 'any' = the copy's limitation has any finding at all (any kind), and per-type miss reasons.
  Execution  For each copy the register statistics are rebuilt from the modified register with the audit's own
             build_stats (only the modified language changes), the shipped terminology pairs are used (as with --terms),
             and run_all() runs on the copy's limitation. A limitation's findings depend only on its three texts, the
             statistics and the pairs, so this equals a full run on that limitation. --verify K (default 100, spread
             over the types and languages) re-runs K copies as a full-register run_all with build_stats(full copy) and
             checks (a) the statistics are identical, (b) the injected limitation's findings are identical, (c) every
             other finding equals the baseline by identity (false positives elsewhere); a language finding whose trigram
             margin moved by a few thousandths is counted apart as 'statistic-only'. --verify all does this for every
             copy (slow: ~30 s per copy and core).
  Changed after the first full run (reporting only; sampling, injectors and detection untouched): the identity used for
  (c) ignores the trigram margin (the first run counted 3 such margin shifts on the Keytruda finding as new+lost), the
  wording of the unit miss reasons, the choice of miss examples, and the default --verify (20 -> 100). One scoring fix
  (a bug against the declared rule): 'a value of the deleted clause' was computed from the clause's unit sites only;
  it now takes every number of the clause (deletion 147 -> 150 of 200; the other types are unchanged).

PROTOCOL v2 (--protocol v2; written into this docstring on 10 Oct 2026 before the first v2 run; v1 above, its output
eval/results/audit_injection.json and the audit's rules are unchanged)
  Why        a juror's objection to v1: v1 sites are 'a number followed by a unit word', which is the audit's own unit-binding
             rule R2, so v1 number recall is close to true by construction; and operator flips were not planted at all.
  Register, eligibility, execution, one fault per copy, n per type and language: as v1. Seed 20261011
             (random.Random('20261011:<type>:<lang>')). --verify default 40 (runtime budget).
  Number tokens (this file's own pattern NUM2, not the audit's parser): every digit token not glued to a preceding
             letter or digit (thousands written 1'000 / 1’000 / 150 000 are one token; decimals 0,5 / 7.5), every date
             dd.mm.yyyy, and every number word 2..12 of the language that is not hyphen-joined to another word
             ('dix-huit' is excluded). Excluded, and only these, because the audit deliberately does not treat them as
             quantities (docs/audit.md R2: 'codes, SR numbers ... are counted but not reported'; canon() reads a number
             with several separators as a code) and because they are identifiers copied verbatim, not translated:
               (x1) BAG indication codes: five digits, '.', one or two digits ('19989.01', the code the insurer receives),
                    and the five digits of the placeholder '19989.XX';
               (x2) Index Therapeuticus group codes: a token right after 'I.T.' / 'IT', or a zero-padded 'dd.dd' ('02.06');
               (x3) other multi-separator references that are not dates ('RS 832.112.31').
             Digits glued to a preceding letter ('FEV1', 'HER2', 'NCT00358943') are not tokens: the audit documents them
             as names. List numbers ('1) ', '2. '), counts, years, prices, scores and table cells ARE sites.
  Types
    number_any   one number token drawn uniformly from all tokens of the target text, changed as in v1 (n -> 2n, n+1, n-1,
                 n/2, n+10; a decimal x -> 2x or x/2; a number word -> another number word 2..12), except: a 4-digit
                 integer 1900..2099 without separator (a year) -> n+1 or n-1; a date -> its day +/-1 (kept in 1..28 when
                 it moves) or its year +/-1 (50/50). The site's category is recorded: v1_site (the v1 pattern matches at
                 this number), list (list numbering, R1 shape), date, word, digit.
    number_word  one number word 2..12 (anywhere, unit word or not) changed to another number word (v1 rule).
    operator     one comparison operator within 25 characters of a number token in the same sentence (no [.;:!?] +
                 space between) flipped in the target only:
                   fr  au moins <-> au plus; au minimum <-> au maximum; minimum <-> maximum; plus de/d'/des/du <-> moins
                       de/...; supérieur(e)(s) <-> inférieur(e)(s); ≥ <-> ≤; > <-> < (not part of '->', '>=', '<<')
                   it  almeno <-> al massimo; al minimo -> al massimo; massimo/a/i/e <-> minimo/...; più di/del/... <->
                       meno di/...; superiore/i <-> inferiore/i; oltre <-> sotto (only when a number follows, optionally
                       after an article: 'oltre i 65 anni'); ≥ <-> ≤; > <-> <
                 Longer phrases win over overlapping shorter ones (pattern order). Case of the first letter is kept.
    negation     one negation within 60 characters of a number token in the same sentence dropped from the target:
                   fr  'ne/n' ... pas' with at most 3 words between (both parts removed: 'ne doit pas dépasser' -> 'doit
                       dépasser', 'n'est pas' -> 'est'); 'non' before a word ('non traités' -> 'traités', 'non-' too)
                   it  'non' before a word ('non superiore a 2 volte' -> 'superiore a 2 volte')
  Detection (strict, pre-declared)
    number_any, number_word   as v1 'number': a number finding in the target language with the new value on the target
                 side or the old value on the German side.
    operator, negation        the audit has no operator or negation kind, so any kind counts if it points to the place:
                 a finding in the target language that is (a) a number or unit finding naming the value of a number token
                 within 60 characters of the edit (in the copy), or (b) an editorial or terminology finding whose surface
                 occurs in the copy within 30 characters of the edit.
    'any' as v1. Per-type miss reasons (number types: the v1 diagnostics plus 'list numbering (R1)'; operator/negation:
    'no rule'), per-category recall for number_any, and recall split by whether the audit's own parse binds the planted
    token to a unit (R2) on the target side.

PROTOCOL r15 (--protocol r15 --half dev|held; PREREG R15, committed 28fe22b before the round-5 rules were written)
  Register and execution as v2, with the audit's round-5 kinds on (run_all(..., r5=True)). Eligible: one representative
             per distinct text triple, of the given half (audit.half), with no finding of any kind, round-5 kinds included.
             100 copies per type and target language (all eligible if fewer). Seed: --half dev 20261015 (design only),
             --half held 20261016 (the pre-registered measurement); random.Random('<seed>:<type>:<lang>').
  Types      operator (v2 injector), negation_drop (v2 'negation' injector), number_word (v2 injector), and
    negation_add  one finite verb within 60 characters of a number token, same sentence, not already negated, negated in
                 the target: FR est, sont, doit, doivent, peut, peuvent, a, ont -> 'n'est pas', 'ne doit pas', 'n'a pas'
                 ('il y a' -> 'il n'y a pas'); IT è, sono, deve, devono, può, possono, viene, vengono, ha, hanno -> 'non è' ...
                 Not already negated: no ne/n'/non/pas/mai/né among the 3 words before, no pas/plus/jamais/point among the 2
                 words after (FR).
  Detection  before: the v2 rule with the pre-round-5 kinds only (number types: a number finding with the new value on the
             target side or the old on the German side). after: the v2 rule plus: operator, an operator finding in the target
             language whose target span (operator and value) lies within 30 characters of the edit; negation_*, a negation
             finding in the target language whose target sentence contains the edit position; number_word, a number or
             number_word finding with the new value on the target side or the old value on the German side.

PROTOCOL r22 (--protocol r22 --half dev|held; PREREG R22, committed 2514b9b before the round-5b rules were written)
  Copies      exactly R15's (protocol r15: same eligibility under the frozen R15 audit, seed, types, n, injectors).
  Execution   every copy runs once with run_all(..., r5='r22'); the R15 round-5 findings of the same copy are computed
              beside it (run_r5 on the copy's limitation with the same number findings, as run_all(..., r5=True) does).
  Detection   R15's rule, 'after' with the R15 kinds (must reproduce R15's committed counts: the copies are the same)
              and with the R22 kinds in their place (the measurement).

usage: python3 tools/audit_inject.py [--protocol v1|v2|r15|r22] [--half dev|held] [--hist DIR] [--n 100] [--seed S] [--jobs J]
                                     [--verify K|all] [--out FILE]
writes eval/results/audit_injection.json (v1), eval/results/audit_injection_v2.json (v2) or
       eval/results/audit_injection_r15_<half>.json (r15), eval/results/audit_injection_r22_<half>.json (r22)"""
import argparse, hashlib, json, math, os, random, re, sys, time
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
import multiprocessing

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))
from gleichlaut import audit as A          # noqa: E402
from gleichlaut.sl.ingest import nrm       # noqa: E402

DATE, SEED, LANGS_T = "20261006", 20261010, ("fr", "it")
TYPES = ("number", "unit", "deletion", "language", "typo")
OUT = os.path.join(ROOT, "eval", "results", "audit_injection.json")

# ------------------------------------------------------------------ sites (this file's own patterns)
NUMWORD = {"fr": "deux trois quatre cinq six sept huit neuf dix onze douze".split(),
           "it": "due tre quattro cinque sei sette otto nove dieci undici dodici".split()}
SYM = r"mg|µg|μg|mcg|g|kg|ml|mL|UI|mmol|%"
UWORD = {"fr": r"jours?|semaines?|mois|ans|an|années?|heures?|cycles?|doses?|fois|comprimés?|perfusions?|injections?|"
               r"cures?|séances?|semestres?",
         "it": r"giorn[oi]|settiman[ae]|mes[ei]|ann[oi]|or[ae]|cicl[oi]|dos[ei]|volte|compress[ae]|infusion[ei]|"
               r"iniezion[ei]|sedut[ae]"}
SITE = {L: re.compile(r"(?<![\w.,'’])(?P<num>(?!0\d)\d+(?:[.,]\d+)?|(?i:" + "|".join(NUMWORD[L]) + r"))"
                      r"(?P<sp>\s?)(?P<unit>(?:" + SYM + r")(?![\w])|(?i:" + UWORD[L] + r")\b)") for L in LANGS_T}
# unit changes within a dimension (lower-case keys; singular/plural chosen by the number)
UNIT_MAP = {"fr": {"mg": "µg", "µg": "mg", "μg": "mg", "mcg": "mg", "g": "mg", "kg": "g", "ml": "dl", "mL": "dl",
                   "jour": "semaine", "jours": "semaines", "semaine": "mois", "semaines": "mois", "mois": ("semaine", "semaines"),
                   "an": "mois", "ans": "mois", "année": "mois", "années": "mois", "heure": "jour", "heures": "jours"},
            "it": {"mg": "µg", "µg": "mg", "μg": "mg", "mcg": "mg", "g": "mg", "kg": "g", "ml": "dl", "mL": "dl",
                   "giorno": "settimana", "giorni": "settimane", "settimana": "mese", "settimane": "mesi",
                   "mese": "settimana", "mesi": "settimane", "anno": "mese", "anni": "mesi", "ora": "giorno", "ore": "giorni"}}
LETTERS = {"fr": "abcdefghijlmnopqrstuvé", "it": "abcdefghilmnopqrstuvz"}


def sites(t, L):
    """number + unit sites in a (normalised) target text -> list of match objects."""
    return list(SITE[L].finditer(t))


def numval(s, L):
    """surface of a site's number -> float."""
    if s.lower() in NUMWORD[L]: return float(NUMWORD[L].index(s.lower()) + 2)
    return float(s.replace(",", "."))


def fmt(x, like):
    """float -> surface in the style of `like` (decimal comma kept)."""
    s = (str(int(x)) if x == int(x) else ("%.4f" % x).rstrip("0").rstrip("."))
    return s.replace(".", ",") if "," in like else s


# ------------------------------------------------------------------ injectors: (text, L, rng) -> None or dict(new, ...)
def inj_number(t, L, rng):
    S = sites(t, L)
    if not S: return None
    m = rng.choice(S); old = m.group("num"); v = numval(old, L)
    if old.lower() in NUMWORD[L]:
        n = int(v); opts = sorted({k for k in (n - 1, n + 1, 2 * n, n // 2 if n % 2 == 0 else 0) if 2 <= k <= 12 and k != n})
        new_v = float(rng.choice(opts)); w = NUMWORD[L][int(new_v) - 2]
        new = w.capitalize() if old[0].isupper() else w
    else:
        if v == int(v):
            n = int(v); opts = sorted({k for k in (2 * n, n + 1, n - 1 if n > 1 else 0, n // 2 if n % 2 == 0 and n >= 4 else 0,
                                                 n + 10 if n >= 10 else 0) if k > 0 and k != n})
            new_v = float(rng.choice(opts))
        else:
            new_v = rng.choice(sorted({v * 2, v / 2}))
        new = fmt(new_v, old)
    s, e = m.span("num")
    return dict(new=t[:s] + new + t[e:], pos=s, end=s + len(new), old_value=v, new_value=new_v,
                before=old + m.group("sp") + m.group("unit"), after=new + m.group("sp") + m.group("unit"),
                sub="word" if old.lower() in NUMWORD[L] else "digit")


def inj_unit(t, L, rng):
    S = [m for m in sites(t, L) if m.group("unit") in UNIT_MAP[L] or m.group("unit").lower() in UNIT_MAP[L]]
    if not S: return None
    m = rng.choice(S); u = m.group("unit"); v = numval(m.group("num"), L)
    nu = UNIT_MAP[L].get(u, UNIT_MAP[L].get(u.lower()))
    if isinstance(nu, tuple): nu = nu[0] if v <= 1 else nu[1]
    if u[0].isupper(): nu = nu[0].upper() + nu[1:]
    s, e = m.span("unit")
    return dict(new=t[:s] + nu + t[e:], pos=m.start(), end=s + len(nu), value=v, old_unit=u, new_unit=nu,
                before=m.group(0), after=m.group("num") + m.group("sp") + nu, sub=u.lower() + "->" + nu.lower())


def clauses(t):
    """candidate deletion spans: sentences (when >= 2), and comma clauses inside a sentence (when it has >= 2)."""
    sents = [(m.start(), m.end()) for m in re.finditer(r"\S.*?(?:[.;:](?=\s|$)|$)", t)]
    out = []
    if len(sents) >= 2: out += [(s, e, "sentence") for s, e in sents]
    for s, e in sents:
        parts, p = [], s
        for m in re.finditer(r",\s", t[s:e]):
            parts.append((p, s + m.start() + 1)); p = s + m.end()
        parts.append((p, e))
        if len(parts) >= 2: out += [(a, b, "comma") for a, b in parts if t[a:b].strip(" ,.;:")]
    return out


def allnums(t, L):
    """every number of a text (digits not glued to letters, number words 2..12), unit or not -> set of floats."""
    out = {float(m.group(0).replace(",", ".")) for m in re.finditer(r"(?<![\w.,'’])\d+(?:[.,]\d+)?(?![.,]?\d)", t)}
    out |= {numval(m.group("num"), L) for m in sites(t, L)}                    # a superset of the unit sites' values
    return out | {float(NUMWORD[L].index(m.group(0).lower()) + 2) for m in re.finditer(r"(?i)\b(?:" + "|".join(NUMWORD[L]) + r")\b", t)}


def inj_deletion(t, L, rng):
    C = [c for c in clauses(t) if sites(t[c[0]:c[1]], L)]
    if not C: return None
    s, e, lvl = rng.choice(C)
    # remove the span and the separator next to it
    a, b = s, e
    if lvl == "comma":
        if b < len(t) and t[b:b + 1] == " ": b += 1
        elif a > 0 and t[a - 2:a] == ", ": a -= 2
    else:
        if b < len(t) and t[b:b + 1] == " ": b += 1
        elif a > 0 and t[a - 1:a] == " ": a -= 1
    new = (t[:a] + t[b:]).strip()
    if not new or new == t: return None
    seg = t[s:e]; vals = sorted(allnums(seg, L)); rest = allnums(new, L)
    return dict(new=new, pos=a, end=a, values=vals, values_gone=[v for v in vals if v not in rest],
                before=seg[:200] + ("…" if len(seg) > 200 else ""), after="", sub=lvl)


def inj_language(t, L, rng, others):
    """others: {lang: text} of the same limitation."""
    src = rng.choice(sorted(others))
    new = nrm(others[src] or "")
    if not new or new == t: return None
    return dict(new=new, pos=0, end=len(new), source=src, before=t[:120], after=new[:120], sub=f"{L}<-{src}")


def _edit(w, op, L, rng):
    if op == "delete": i = rng.randrange(len(w)); return w[:i] + w[i + 1:]
    if op == "double": i = rng.randrange(len(w)); return w[:i + 1] + w[i:]
    if op == "substitute":
        i = rng.randrange(len(w)); c = rng.choice([x for x in LETTERS[L] if x != w[i].lower()])
        return w[:i] + (c.upper() if w[i].isupper() else c) + w[i + 1:]
    if op == "transpose":
        ks = [k for k in range(len(w) - 1) if w[k] != w[k + 1]]
        if not ks: return None
        k = rng.choice(ks); return w[:k] + w[k + 1] + w[k] + w[k + 2:]
    raise ValueError(op)


def inj_typo(t, L, rng):
    S = sites(t, L)
    if not S: return None
    m = rng.choice(S); opts = []
    pw = re.search(r"([^\W\d_]{2,}) $", t[:m.start()])           # the word right before the number, one space between
    if pw: opts += [("before", "glue")] + ([("before", op) for op in ("delete", "double", "substitute", "transpose")]
                                          if len(pw.group(1)) >= 3 else [])
    u = m.group("unit")
    if re.fullmatch(r"[^\W\d_]{3,}", u):
        opts += [("unit", op) for op in ("delete", "double", "substitute", "transpose")] + ([("unit", "glue")] if m.group("sp") else [])
    if m.group("num").lower() in NUMWORD[L] and len(m.group("num")) >= 3:
        opts += [("numword", op) for op in ("delete", "double", "substitute", "transpose")]
    rng.shuffle(opts)
    for side, op in opts:
        if op == "glue":
            if side == "before": s, e, rep = pw.end(1), pw.end(1) + 1, ""
            else: s, e, rep = m.end("num"), m.start("unit"), ""
            if t[s:e] != " ": continue
        else:
            s, e = (pw.span(1) if side == "before" else m.span("unit") if side == "unit" else m.span("num"))
            rep = _edit(t[s:e], op, L, rng)
            if rep is None or rep == t[s:e]: continue
        new = t[:s] + rep + t[e:]
        a = (pw.start(1) if pw else m.start()); b = m.end() - (e - s) + len(rep)
        return dict(new=new, pos=s, end=s + len(rep), side=side, op=op, word_before=t[s:e], word_after=rep,
                    before=t[a:m.end()], after=new[a:b], sub=f"{side}:{op}")
    return None


INJ = {"number": inj_number, "unit": inj_unit, "deletion": inj_deletion, "language": inj_language, "typo": inj_typo}


# ================================================================== protocol v2 (docstring 'PROTOCOL v2')
SEED2 = 20261011
TYPES2 = ("number_any", "number_word", "operator", "negation")
OUT2 = os.path.join(ROOT, "eval", "results", "audit_injection_v2.json")
NUM2 = re.compile(r"(?<![^\W_])(?<![.,'’])(?:(?P<date>\d{1,2}\.\d{1,2}\.\d{4})(?![\d])"
                  r"|(?P<th>\d{1,3}(?:(?:['’]|[  ](?=\d{3}(?!\d)))\d{3})+(?:[.,]\d+)?)(?![\d])"
                  r"|(?P<dig>\d+(?:[.,]\d+)*))")
NUMW2 = {L: re.compile(r"(?i)(?<![\w-])(?:" + "|".join(NUMWORD[L]) + r")(?![\w-])") for L in LANGS_T}
LIST2 = re.compile(r"(?:^|[.:;!?•]\s|\s[•\-–]\s)\s*\(?(\d{1,2})[.)](?=\s+\S)")        # list numbering (the R1 shape)
_ART_IT = r"(?:(?:i|gli|le|il|la|l['’]|ai|agli|alle|al|allo|alla|dei|degli|delle)\s*)?"
_D_FR = r"(?=d(?:e|es|u)\b|d['’])"
_D_IT = r"(?=d(?:i|el|ella|ello|ei|egli|elle|ell['’]|al)\b)"
OPS = {"fr": [(r"\bau moins\b", "au plus"), (r"\bau plus\b", "au moins"), (r"\bau minimum\b", "au maximum"),
              (r"\bau maximum\b", "au minimum"), (r"\bmaximum\b", "minimum"), (r"\bminimum\b", "maximum"),
              (r"\bplus " + _D_FR, "moins "), (r"\bmoins " + _D_FR, "plus "),
              (r"\bsupérieur(?=e?s?\b)", "inférieur"), (r"\binférieur(?=e?s?\b)", "supérieur"),
              (r"≥", "≤"), (r"≤", "≥"), (r"(?<![-=<>])>(?![=<>])", "<"), (r"(?<![-=<>])<(?![=<>-])", ">")],
       "it": [(r"\balmeno\b", "al massimo"), (r"\bal massimo\b", "almeno"), (r"\bal minimo\b", "al massimo"),
              (r"\bmassim(?=[oaie]\b)", "minim"), (r"\bminim(?=[oaie]\b)", "massim"),
              (r"\bpiù " + _D_IT, "meno "), (r"\bmeno " + _D_IT, "più "),
              (r"\bsuperior(?=[ei]\b)", "inferior"), (r"\binferior(?=[ei]\b)", "superior"),
              (r"\boltre(?=\s+" + _ART_IT + r"(?:\d|(?i:" + "|".join(NUMWORD["it"]) + r")\b))", "sotto"),
              (r"\bsotto(?=\s+" + _ART_IT + r"(?:\d|(?i:" + "|".join(NUMWORD["it"]) + r")\b))", "oltre"),
              (r"≥", "≤"), (r"≤", "≥"), (r"(?<![-=<>])>(?![=<>])", "<"), (r"(?<![-=<>])<(?![=<>-])", ">")]}
OPS_RX = {L: [(re.compile(p, re.I), r) for p, r in v] for L, v in OPS.items()}
NEG = {"fr": [("ne_pas", re.compile(r"(?i)\b(?:ne\s+|n['’])((?:[^\W\d_][\w'’-]*\s+){0,3}?)pas\b")),
              ("non", re.compile(r"(?i)\bnon(?:\s+|-)(?=[^\W\d_])"))],
       "it": [("non", re.compile(r"(?i)\bnon\s+(?=[^\W\d_])"))]}
_SENT = re.compile(r"[.;:!?](?:\s|$)")


def ntoks(t, L):
    """v2 number tokens of a target text -> list of dict(s, e, surf, kind, value(s), excluded reason or None, cat)."""
    out = []
    lists = set(m.start(1) for m in LIST2.finditer(t))
    v1 = set(m.start("num") for m in sites(t, L))
    for m in NUM2.finditer(t):
        s, e, sf = m.start(), m.end(), m.group(0); ex = None
        if m.group("date"): kind = "date"
        else:
            kind = "digit"
            if re.fullmatch(r"\d{5}\.\d{1,2}", sf) or (re.fullmatch(r"\d{5}", sf) and re.match(r"\.XX\b", t[e:e + 3], re.I)):
                ex = "indication code"
            elif re.search(r"(?:\bI\.\s?T\.|\bIT)\s*$", t[max(0, s - 6):s]) or re.fullmatch(r"0\d\.\d\d(?:\.\d\d)?", sf):
                ex = "IT group code"
            elif m.group("dig") and len(re.findall(r"[.,]", sf)) >= 2:
                ex = "multi-separator reference"
        cat = ("v1_site" if s in v1 else "list" if s in lists else "date" if kind == "date" else "digit")
        out.append(dict(s=s, e=e, surf=sf, kind=kind, excluded=ex, cat=cat))
    for m in NUMW2[L].finditer(t):
        out.append(dict(s=m.start(), e=m.end(), surf=m.group(0), kind="word", excluded=None,
                        cat="v1_site" if m.start() in v1 else "word"))
    return sorted(out, key=lambda x: x["s"])


def _tokval(sf):
    """digit surface -> float (thousands separators removed, decimal comma read)."""
    s = re.sub(r"['’  ]", "", sf)
    return float(s.replace(",", "."))


def fmt2(x, like):
    """float -> surface in the style of `like`: its thousands separator and decimal mark."""
    ts = re.search(r"\d(['’  ])\d{3}", like); ts = ts.group(1) if ts else None
    dec = "," if re.search(r",\d{1,2}$|,\d{4,}$", like) or ("," in like and not ts and "." not in like) else "."
    s = str(int(x)) if x == int(x) else ("%.4f" % x).rstrip("0").rstrip(".")
    ip, _, fp = s.partition(".")
    if ts and len(ip) > 3: ip = "{:,}".format(int(ip)).replace(",", ts)
    return ip + (dec + fp if fp else "")


def _change(tok, L, rng):
    """one plausible new value for a v2 token -> (old_value, new_value, new_surface)."""
    sf = tok["surf"]
    if tok["kind"] == "word":
        n = NUMWORD[L].index(sf.lower()) + 2
        opts = sorted({k for k in (n - 1, n + 1, 2 * n, n // 2 if n % 2 == 0 else 0) if 2 <= k <= 12 and k != n})
        k = rng.choice(opts); w = NUMWORD[L][k - 2]
        return float(n), float(k), (w.capitalize() if sf[0].isupper() else w)
    if tok["kind"] == "date":
        d, mo, y = sf.split(".")
        if rng.random() < 0.5:
            dv = int(d); nd = dv + 1 if dv < 28 else dv - 1
            return float(dv), float(nd), str(nd).zfill(len(d)) + "." + mo + "." + y
        yv = int(y); ny = yv + rng.choice((1, -1))
        return float(yv), float(ny), d + "." + mo + "." + str(ny)
    v = _tokval(sf)
    if v == int(v) and re.fullmatch(r"\d{4}", sf) and 1900 <= v <= 2099:
        nv = v + rng.choice((1, -1))
    elif v == int(v):
        n = int(v); opts = sorted({k for k in (2 * n, n + 1, n - 1 if n > 1 else 0, n // 2 if n % 2 == 0 and n >= 4 else 0,
                                             n + 10 if n >= 10 else 0) if k > 0 and k != n})
        nv = float(rng.choice(opts))
    else:
        nv = rng.choice(sorted({v * 2, v / 2}))
    return v, nv, fmt2(nv, sf)


def _plant_number(t, L, rng, S):
    tok = rng.choice(S); ov, nv, ns = _change(tok, L, rng)
    if ns == tok["surf"]: return None
    s, e = tok["s"], tok["e"]; new = t[:s] + ns + t[e:]
    a, b = max(0, s - 40), min(len(t), e + 40)
    return dict(new=new, pos=s, end=s + len(ns), old_value=ov, new_value=nv, token=tok["surf"], new_token=ns,
                cat=tok["cat"], kind=tok["kind"], before=t[a:b], after=new[a:b - len(tok["surf"]) + len(ns)], sub=tok["cat"])


def inj_number_any(t, L, rng):
    S = [x for x in ntoks(t, L) if not x["excluded"]]
    return _plant_number(t, L, rng, S) if S else None


def inj_number_word(t, L, rng):
    S = [x for x in ntoks(t, L) if x["kind"] == "word"]
    return _plant_number(t, L, rng, S) if S else None


def _near_number(t, L, s, e, w):
    """a v2 number token within w characters of t[s:e], with no sentence end in between."""
    for x in ntoks(t, L):
        if x["excluded"]: continue
        gap = t[e:x["s"]] if x["s"] >= e else t[x["e"]:s] if x["e"] <= s else ""
        if len(gap) <= w and not _SENT.search(gap): return True
    return False


def op_sites(t, L):
    taken, out = [], []
    for rx, rep in OPS_RX[L]:
        for m in rx.finditer(t):
            if any(m.start() < b and a < m.end() for a, b in taken): continue
            taken.append(m.span())
            if _near_number(t, L, m.start(), m.end(), 25): out.append((m.start(), m.end(), rep))
    return sorted(out)


def inj_operator(t, L, rng):
    S = op_sites(t, L)
    if not S: return None
    s, e, rep = rng.choice(S); old = t[s:e]
    if old[:1].isupper(): rep = rep[:1].upper() + rep[1:]
    new = t[:s] + rep + t[e:]
    a, b = max(0, s - 40), min(len(t), e + 40)
    return dict(new=new, pos=s, end=s + len(rep), old_op=old, new_op=rep, sub=f"{old.lower().strip()}->{rep.lower().strip()}",
                before=t[a:b], after=new[a:b - len(old) + len(rep)])


def neg_sites(t, L):
    out = []
    for name, rx in NEG[L]:
        for m in rx.finditer(t):
            if _near_number(t, L, m.start(), m.end(), 60): out.append((m.start(), m.end(), name, m.group(1) if m.groups() else ""))
    return sorted(out)


def inj_negation(t, L, rng):
    S = neg_sites(t, L)
    if not S: return None
    s, e, name, keep = rng.choice(S); old = t[s:e]
    rep = keep.rstrip() if name == "ne_pas" else ""
    head, tail = t[:s], t[e:]
    if not rep and head.endswith(" ") and tail.startswith(" "): tail = tail[1:]
    if rep and not tail[:1].isspace() and tail[:1].isalnum(): rep += " "
    if old[:1].isupper():
        if rep: rep = rep[:1].upper() + rep[1:]
        elif tail: tail = tail[:1].upper() + tail[1:]
    new = head + rep + tail
    if new == t: return None
    a, b = max(0, s - 40), min(len(t), e + 40)
    return dict(new=new, pos=s, end=s + len(rep), removed=old, sub=name, before=t[a:b], after=new[a:max(a, b - (len(t) - len(new)))])


INJ2 = {"number_any": inj_number_any, "number_word": inj_number_word, "operator": inj_operator, "negation": inj_negation}

# ================================================================== protocol r15 (docstring 'PROTOCOL r15')
SEED_R15 = {"dev": 20261015, "held": 20261016}
TYPES_R15 = ("operator", "negation_drop", "negation_add", "number_word")
VERB = {"fr": re.compile(r"(?<![\w'’-])(?P<y>y\s)?(?P<v>est|sont|doit|doivent|peut|peuvent|a|ont)(?![\w'’-])"),
        "it": re.compile(r"(?<![\w'’-])(?P<v>è|È|sono|deve|devono|può|possono|viene|vengono|ha|hanno)(?![\w'’-])")}


def negadd_sites(t, L):
    out = []
    for m in VERB[L].finditer(t):
        s, e = m.span()
        before = re.findall(r"\S+", t[max(0, s - 40):s])[-3:]; after = re.findall(r"\S+", t[e:e + 30])[:2]
        if any(re.fullmatch(r"(?i)(?:ne|n['’]\S*|non|pas|mai|né|\S*n['’]y)", w) for w in before): continue
        if L == "fr" and any(re.fullmatch(r"(?i)(?:pas|plus|jamais|point)\W*", w) for w in after): continue
        if _near_number(t, L, s, e, 60): out.append((s, e, m.group("v"), bool(m.groupdict().get("y"))))
    return out


def inj_negation_add(t, L, rng):
    S = negadd_sites(t, L)
    if not S: return None
    s, e, v, y = rng.choice(S)
    if L == "fr":
        rep = ("n'y " + v if y else ("n'" + v if v[0] in "aeo" else "ne " + v)) + " pas"
    else:
        rep = ("Non è" if v == "È" else "non " + v)
    new = t[:s] + rep + t[e:]
    a, b = max(0, s - 40), min(len(t), e + 40)
    return dict(new=new, pos=s, end=s + len(rep), added=rep, sub=f"{L}:{v.lower()}", before=t[a:b], after=new[a:b + len(rep) - (e - s)])


INJ_R15 = {"operator": inj_operator, "negation_drop": inj_negation, "negation_add": inj_negation_add, "number_word": inj_number_word}


# ------------------------------------------------------------------ the audit on a copy
G = {}


def _init(hist, date):
    J, names = A.load(hist, date)
    G.update(J=J, names=names, P=A.load_terms(), hist=hist, date=date)
    G["base"] = {k: v for k, v in A.build_stats(J).items() if k != "_vocab"}


def stats_for(J2, L):
    """register statistics of the copy: build_stats on the modified language field, the others from the baseline."""
    part = A.build_stats({X: {"lim": (J2[X]["lim"] if X == L else {})} for X in A.LANGS})
    st = {k: (dict(v) if isinstance(v, dict) else v) for k, v in G["base"].items()}
    for k in ("tri", "ntri", "vocab", "after", "utri"): st[k][L] = part[k][L]
    st["V"] = len(set(k for X in A.LANGS for k in st["tri"][X]))
    return st


def copy_of(i, L, new):
    J = G["J"]; J2 = dict(J); J2[L] = dict(J[L], lim=dict(J[L]["lim"])); J2[L]["lim"][i] = new
    return J2


def proj(f):
    """a finding without its rank-dependent fields (fid, rank, explained_by ids)."""
    d = {k: v for k, v in f.items() if k not in ("rank", "fid", "explained_by", "equivalence")}
    d["explained"] = bool(f.get("explained_by")); return json.dumps(d, sort_keys=True, ensure_ascii=False)


def ident(f):
    """a finding's identity: proj() without the language check's trigram margin, a register statistic that moves by
    a few thousandths whenever any text of that language changes (it is also printed in 'description')."""
    d = json.loads(proj(f)); d.pop("margin", None)
    if d.get("kind") == "language": d.pop("description", None)
    return json.dumps(d, sort_keys=True, ensure_ascii=False)


def run_copy(job):
    i, L, new, verify = job["id"], job["lang"], job["new"], job["verify"]
    J2 = copy_of(i, L, new); st = A._prep(stats_for(J2, L))
    sub = {X: {"lim": {i: J2[X]["lim"][i]}} for X in A.LANGS}
    F, _, _ = A.run_all(None, G["date"], sub, {i: G["names"].get(i, [])}, st, pairs=G["P"], r5=G.get("r5", False))
    out = dict(k=job["k"], findings=F)
    if verify:
        st_full = A.build_stats(J2)
        same_stats = {k: v for k, v in st_full.items() if k != "_vocab"} == {k: v for k, v in st.items() if k != "_vocab"}
        FF, _, _ = A.run_all(None, G["date"], J2, G["names"], A._prep(st_full), pairs=G["P"], r5=G.get("r5", False))
        mine = sorted(proj(f) for f in FF if f["id"] == i); here = sorted(proj(f) for f in F)
        other = Counter(proj(f) for f in FF if f["id"] != i); oid = Counter(ident(f) for f in FF if f["id"] != i)
        bid = G["baseline_id"]
        out["verify"] = dict(stats_identical=same_stats, limitation_identical=mine == here,
                             elsewhere_new=sum((oid - bid).values()), elsewhere_lost=sum((bid - oid).values()),
                             elsewhere_statistic_only=sum((other - G["baseline"]).values()))
    return out


# ------------------------------------------------------------------ scoring
def _f(v):
    try: return float(v)
    except (TypeError, ValueError): return None


def detected(job, F):
    t, L, inj = job["type"], job["lang"], job["inj"]
    if t == "number":
        return any(f["kind"] == "number" and f["lang"] == L and (any(_f(x["value"]) == inj["new_value"] for x in f["tgt_only"]) or
                                                               any(_f(x["value"]) == inj["old_value"] for x in f["de_only"])) for f in F)
    if t == "unit":
        return any(f["kind"] == "unit" and f["lang"] == L and _f(f["value"]) == inj["value"] for f in F)
    if t == "deletion":
        return any(f["kind"] == "number" and f["lang"] == L and any(_f(x["value"]) in inj["values"] for x in f["de_only"]) for f in F)
    if t == "language":
        return any(f["kind"] == "language" and f["lang"] == L and f["detected"] == inj["source"] for f in F)
    if t == "typo":
        t2 = job["new"]
        for f in F:
            if f["kind"] != "editorial" or f["lang"] != L: continue
            for m in re.finditer(re.escape(f["surface"]), t2):
                if m.start() <= inj["end"] + 30 and m.end() >= inj["pos"] - 30: return True
        return False
    raise ValueError(t)


def _vals(t, L): return set(x["v"] for x in A.values(nrm(t), L))


def reason(job, F, st):
    """why a planted fault was missed (diagnostic, computed with the audit's own parser)."""
    t, L, inj, de, old, new = job["type"], job["lang"], job["inj"], job["de"], job["old"], job["new"]
    if t in ("number", "deletion"):
        r0, r1 = A.compare(de, old, L), A.compare(de, new, L)
        vd, vo, vn = _vals(de, "de"), _vals(old, L), _vals(new, L)
        if t == "number":
            o, n = A.canon(fmt(inj["old_value"], "."))[0], A.canon(fmt(inj["new_value"], "."))[0]
            if o in vn and n in vd: return "masked: the old value stays elsewhere in the target and the new value is in the German (set comparison, R5)"
            if o not in vd and n not in vd: return "the German does not state the old value either (written differently, e.g. a word or a conversion)"
            if o in vn and n in vo: return "masked: both values were already in the target"
        else:
            if not inj["values_gone"]: return "the deleted values occur elsewhere in the target (set comparison, R5)"
            if not any(A.canon(fmt(v, "."))[0] in vd for v in inj["values_gone"]): return "the deleted values are not in the German either"
        su = Counter(r1["suppressed"]) - Counter(r0["suppressed"])
        if su: return "reconciled by " + ", ".join(sorted(su))
        if r1["unbound"] > r0["unbound"]: return "value not bound to a unit in the audit's parse (R2)"
        if r1["count"] != r0["count"]: return "count-only difference (R5)"
        return "other"
    if t == "unit":
        v = A.canon(fmt(inj["value"], "."))[0]
        if v not in _vals(de, "de"): return "the German does not state this value (written differently)"
        if any(u["value"] == v for u in A.unit_one_sided(de, new, L)):
            oc = {A._ucls(x["unit"], L) for x in A.values(nrm(new), L) if x["v"] == v}
            dc = {A._ucls(x["unit"], "de") for x in A.values(nrm(de), "de") if x["v"] == v}
            if A._ucls(inj["old_unit"], L) in oc: return "one-directional: the target still has this value with the old unit elsewhere (unit_one_sided, not a finding)"
            if A._ucls(inj["new_unit"], L) in dc: return "one-directional: the German also has this value with the new unit (unit_one_sided, not a finding)"
            return "one-directional unit difference (unit_one_sided, not a finding)"
        dcls = {A._ucls(x["unit"], "de") for x in A.values(nrm(de), "de") if x["v"] == v}
        if dcls <= {None}: return "the German unit of this value is outside the time/mass/volume classes"
        tc = {A._ucls(x["unit"], L) for x in A.values(nrm(new), L) if x["v"] == v}
        if tc - {None} == dcls - {None}: return "both texts still have this value with both units (unit classes are compared as sets)"
        if tc <= {None}: return "the new target unit is not read by the audit's parser"
        if any(f["kind"] == "number" for f in F): return "reported as a number finding instead"
        return "other"
    if t == "language":
        o = [M for M in A.LANGS if M != L]; W = {X: set(A.words(nrm(job["texts"][X]))) for X in o}
        r = A.lang_check(new, L, W[o[0]] & W[o[1]], st)
        if not r["judged"]: return "not judged: fewer than 3 function words (short field)"
        h = r["fw"]; X = inj["source"]
        if h.get(X, 0) < max(A.LID_MIN, A.LID_RATIO * h.get(L, 0)): return "rule A: too few function words of the source language"
        if r["ntri"] < A.LID_NTRI: return "rule B: fewer than 12 trigrams after removing shared words"
        if r["margin"] is not None and r["margin"] < A.LID_MARGIN: return "rule B: trigram margin under 0.5 nat"
        return "other"
    if t == "typo":
        side, op, w2 = inj["side"], inj["op"], inj["word_after"].lower()
        if op == "glue":
            if side == "before":
                return ("E2 fires only before a unit symbol/word it reads" if w2 in A.PREP[L].split() + A._FW_RAW[L].split()
                        else "the glued word is not a preposition/article (E2 closed list)")
            return "glued to a non-time unit word (E3 covers time words only)"
        if side == "before": return "no rule looks at a misspelt word before a number"
        if op == "transpose": return "a transposition is two edits (E4/E5 allow one)"
        if side == "numword":
            return "E4: the corrected phrase is in < 5 register texts, or the edit is not one edit from a number word before a unit word"
        if w2 in st["_vocab"][L] or st["after"][L].get(w2, 0) >= 2: return "real-word or common register word (E5 needs a rare word)"
        if len(w2) < 4: return "E5 looks at words of >= 4 letters only"
        if not any(k >= A.E5_MIN and A.lev1(w2, u) and A._is_unit_word(u, L) for u, k in st["after"][L].items()):
            return "no frequent unit word one edit away (E5 threshold 20 texts)"
        return "other"
    return "other"


def _tokvals(x):
    if x["kind"] == "word": return {float(NUMWORD_ALL.index(x["surf"].lower()) % 11 + 2)}
    if x["kind"] == "date": d, _, y = x["surf"].split("."); return {float(int(d)), float(int(y))}
    return {_tokval(x["surf"])}


NUMWORD_ALL = NUMWORD["fr"] + NUMWORD["it"]


def near_values(t, L, s, e, w=60):
    """values of the v2 number tokens within w characters of t[s:e] (any side)."""
    out = set()
    for x in ntoks(t, L):
        if x["excluded"]: continue
        if x["s"] <= e + w and x["e"] >= s - w: out |= _tokvals(x)
    return out


def detected2(job, F):
    t, L, inj = job["type"], job["lang"], job["inj"]
    if t in ("number_any", "number_word"): return detected(dict(job, type="number"), F)
    near = near_values(job["new"], L, inj["pos"], inj["end"])
    for f in F:
        if f["lang"] != L: continue
        if f["kind"] == "number" and any(_f(x["value"]) in near for x in f["tgt_only"] + f["de_only"]): return True
        if f["kind"] == "unit" and _f(f["value"]) in near: return True
        if f["kind"] in ("editorial", "terminology"):
            for m in re.finditer(re.escape(f.get("surface") or f.get("old") or "\0"), job["new"], re.I):
                if m.start() <= inj["end"] + 30 and m.end() >= inj["pos"] - 30: return True
    return False


OLD_KINDS = ("number", "unit", "language", "editorial", "terminology")


def _num_hit(job, F, kinds):
    L, inj = job["lang"], job["inj"]
    return any(f["kind"] in kinds and f["lang"] == L and (any(_f(x["value"]) == inj["new_value"] for x in f.get("tgt_only") or []) or
                                                           any(_f(x["value"]) == inj["old_value"] for x in f.get("de_only") or [])) for f in F)


def detected_r15(job, F, after=True):
    """PROTOCOL r15: before (after=False) = the v2 rule on the pre-round-5 kinds; after = that plus the round-5 kinds."""
    t, L, inj = job["type"], job["lang"], job["inj"]
    old = [f for f in F if f["kind"] in OLD_KINDS]
    if t == "number_word": return _num_hit(job, F, ("number", "number_word") if after else ("number",))
    if detected2(dict(job, type="operator"), old): return True
    if not after: return False
    for f in F:
        if f["lang"] != L: continue
        if t == "operator" and f["kind"] == "operator":
            if any(a <= inj["end"] + 30 and b >= inj["pos"] - 30 for a, b in f["tgt_spans"]): return True
        if t.startswith("negation") and f["kind"] == "negation":
            a, b = f["tgt_span"]
            if a <= inj["pos"] <= b: return True
    return False


def reason_r15(job, F, st):
    if job["type"] == "number_word":
        r = reason2(job, F, st)
        return r
    what = {"operator": "comparison operator", "negation_drop": "negation", "negation_add": "negation"}[job["type"]]
    if F: return f"a finding appeared, but not at the planted {what}"
    return f"no finding at the planted {what}"


def reason2(job, F, st):
    t, L, inj = job["type"], job["lang"], job["inj"]
    if t in ("number_any", "number_word"):
        if inj["cat"] == "list" and any(m.start(1) == inj["pos"] for m in A.ENUM.finditer(job["new"])):
            return "list numbering: dropped on both sides (R1)"
        r = reason(dict(job, type="number"), F, st)
        if r == "other" and F: return "a finding on another value (does not point to the planted one)"
        return r
    what = "comparison operator" if t == "operator" else "negation"
    if F: return f"a finding appeared, but not at the planted {what}"
    return f"no rule looks at a {what}: numbers, units, language, typos and terms are unchanged"


def bound_at(t, L, pos):
    """does the audit's own parse (R2) bind the value that starts at pos to a unit? None if it reads no value there."""
    for x in A.values(t, L):
        if x["s"] <= pos < max(x["e"], x["s"] + 1): return bool(x["unit"])
    return None


def wilson(k, n, z=1.959964):
    if not n: return [None, None]
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n); h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return [round((c - h) / d, 3), round((c + h) / d, 3)]


def examples(ms, k=8):
    """up to k missed copies: the first of each reason (most frequent reason first), then the next ones in order."""
    c = Counter(m["reason"] for m in ms); out = []
    for r, _ in c.most_common():
        out.append(next(m for m in ms if m["reason"] == r))
    out = out[:k]
    for m in ms:
        if len(out) >= k: break
        if m not in out: out.append(m)
    return out


def snip(s, n=160): return s if len(s) <= n else s[:n] + "…"


def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--hist", default=os.environ.get("GLEICHLAUT_HIST") or os.path.expanduser("~/Desktop/hackapertus/spikes/gleichlaut/data/hist"))
    ap.add_argument("--date", default=DATE)
    ap.add_argument("--n", type=int, default=100, help="injections per type and target language (default 100)")
    ap.add_argument("--protocol", choices=("v1", "v2", "r15", "r22"), default="v1", help="v1 (default, the published run), v2, r15 or r22 (docstring)")
    ap.add_argument("--half", choices=("dev", "held"), default=None, help="r15: the half of the register to plant into")
    ap.add_argument("--seed", type=int, default=None, help="default 20261010 (v1) / 20261011 (v2)")
    ap.add_argument("--jobs", type=int, default=min(8, os.cpu_count() or 1))
    ap.add_argument("--verify", default=None, help="copies re-run as a full-register audit (a number, or 'all'; default 100 v1 / 40 v2)")
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    if a.protocol == "r15": return main_r15(a)
    if a.protocol == "r22": return main_r22(a)
    v2 = a.protocol == "v2"
    if a.seed is None: a.seed = SEED2 if v2 else SEED
    if a.verify is None: a.verify = "40" if v2 else "100"
    if a.out is None: a.out = OUT2 if v2 else OUT
    TYPES_, INJ_, det_, reason_ = (TYPES2, INJ2, detected2, reason2) if v2 else (TYPES, INJ, detected, reason)
    if not os.path.exists(os.path.join(a.hist, f"{a.date}-de.json")): sys.exit(f"no snapshot {a.date} in {a.hist} (--hist DIR)")
    t0 = time.time()
    _init(a.hist, a.date); J, P = G["J"], G["P"]
    stb = A._prep(dict(G["base"]))
    B, _, _ = A.run_all(None, a.date, J, G["names"], stb, pairs=P)
    flagged = set(f["id"] for f in B)
    baseline = [proj(f) for f in B]
    t_base = time.time() - t0
    # one representative per distinct text triple, unflagged
    rep = {}
    for i in sorted(J["de"]["lim"]):
        k = tuple(nrm(J[X]["lim"].get(i) or "") for X in A.LANGS)
        if all(k) and k not in rep: rep[k] = i
    flagged_triples = sum(1 for k, i in rep.items() if i in flagged)
    pool = sorted(i for i in rep.values() if i not in flagged)
    jobs, pools = [], {}
    for ti, t in enumerate(TYPES_):
        for L in LANGS_T:
            rng = random.Random(f"{a.seed}:{t}:{L}"); ids = list(pool); rng.shuffle(ids); n = 0; elig = 0
            for i in ids:
                old = nrm(J[L]["lim"][i])
                if t == "language": inj = INJ[t](old, L, rng, {X: J[X]["lim"][i] for X in A.LANGS if X != L})
                else: inj = INJ_[t](old, L, rng)
                if inj is None: continue
                elig += 1
                if n >= a.n: continue
                assert inj["new"] != old
                jobs.append(dict(k=len(jobs), type=t, lang=L, id=i, old=old, new=inj["new"], inj={k: v for k, v in inj.items() if k != "new"},
                                 de=nrm(J["de"]["lim"][i]), texts={X: J[X]["lim"][i] for X in A.LANGS}, verify=False))
                n += 1
            pools[f"{t}:{L}"] = elig
    if a.verify == "all": ver = set(range(len(jobs)))
    else:
        k = int(a.verify); per = defaultdict(list)
        for j in jobs: per[j["type"]].append(j["k"])
        ver = set()
        for t in TYPES_:                                           # spread over types and both languages, deterministic
            xs = per[t]; step = max(1, len(xs) // max(1, k // len(TYPES_)))
            ver |= set(xs[::step][:max(1, k // len(TYPES_))]) if k else set()
    for j in jobs: j["verify"] = j["k"] in ver
    t1 = time.time()
    res = {}
    G["baseline"] = Counter(baseline); G["baseline_id"] = Counter(ident(f) for f in B)
    # fork: the workers inherit the loaded register, the baseline statistics and the pairs (spawn would re-import the
    # frozen modules with the parent's sys.path, which core.py's frozen-import check rejects)
    with ProcessPoolExecutor(max_workers=a.jobs, mp_context=multiprocessing.get_context("fork")) as ex:
        light = [dict(k=j["k"], id=j["id"], lang=j["lang"], new=j["new"], verify=j["verify"]) for j in jobs]
        for r in ex.map(run_copy, light, chunksize=4): res[r["k"]] = r
    t_runs = time.time() - t1
    # ---------------------------------------------------------------- score
    per_type = {}; misses = defaultdict(list); V = []
    for t in TYPES_:
        J_t = [j for j in jobs if j["type"] == t]
        rows = []
        for j in J_t:
            F = res[j["k"]]["findings"]; hit = det_(j, F)
            st_j = None
            if not hit:
                st_j = A._prep(stats_for(copy_of(j["id"], j["lang"], j["new"]), j["lang"])) if t in ("language", "typo") else None
                rs = reason_(j, F, st_j)
                misses[t].append(dict(id=j["id"], lang=j["lang"], sub=j["inj"]["sub"], before=snip(j["inj"]["before"]),
                                      after=snip(j["inj"]["after"]), reason=rs,
                                      findings=[f"{f['kind']}: " + snip(f.get("description") or "", 120) for f in F]))
            rows.append(dict(j=j, hit=hit, any=bool(F), kinds=sorted(set(f["kind"] for f in F)),
                             reason=None if hit else misses[t][-1]["reason"]))
            if "verify" in res[j["k"]]: V.append(dict(type=t, id=j["id"], lang=j["lang"], **res[j["k"]]["verify"]))
        n = len(rows); k = sum(r["hit"] for r in rows); ka = sum(r["any"] for r in rows)
        by_lang = {L: dict(n=sum(r["j"]["lang"] == L for r in rows), detected=sum(r["hit"] for r in rows if r["j"]["lang"] == L))
                   for L in LANGS_T}
        for L in LANGS_T: by_lang[L]["recall"] = round(by_lang[L]["detected"] / by_lang[L]["n"], 3) if by_lang[L]["n"] else None
        sub = defaultdict(lambda: [0, 0])
        for r in rows:
            s = r["j"]["inj"]["sub"] if t != "unit" else r["j"]["inj"]["sub"]
            if t == "typo": s = r["j"]["inj"]["side"] + ":" + r["j"]["inj"]["op"]
            sub[s][0] += 1; sub[s][1] += r["hit"]
        extra = {}
        if t == "deletion":
            vis = [r for r in rows if r["j"]["inj"]["values_gone"]]
            extra["values_gone_subset"] = dict(n=len(vis), detected=sum(r["hit"] for r in vis),
                                               recall=round(sum(r["hit"] for r in vis) / len(vis), 3) if vis else None,
                                               wilson95=wilson(sum(r["hit"] for r in vis), len(vis)),
                                               note="copies where at least one deleted value no longer occurs anywhere in the target")
        if t == "language":
            jd = [r for r in rows if A.lang_check(r["j"]["new"], r["j"]["lang"], set(), None)["judged"]]
            extra["judged_subset"] = dict(n=len(jd), detected=sum(r["hit"] for r in jd),
                                          recall=round(sum(r["hit"] for r in jd) / len(jd), 3) if jd else None,
                                          wilson95=wilson(sum(r["hit"] for r in jd), len(jd)),
                                          note="copies whose planted text has >= 3 function words (the check's own judging floor)")
        if t in ("number_any", "number_word"):
            def split(key):
                d = defaultdict(lambda: [0, 0])
                for r in rows: d[key(r)][0] += 1; d[key(r)][1] += r["hit"]
                return {c: dict(n=v[0], detected=v[1], recall=round(v[1] / v[0], 3), wilson95=wilson(v[1], v[0])) for c, v in sorted(d.items())}
            extra["by_category"] = split(lambda r: r["j"]["inj"]["cat"])
            extra["by_audit_parse"] = split(lambda r: {True: "bound to a unit (R2)", False: "unbound (R2: counted, not reported)",
                                                       None: "not read as a value"}[bound_at(r["j"]["old"], r["j"]["lang"], r["j"]["inj"]["pos"])])
            extra["note_by_audit_parse"] = "whether the audit's own parse of the original target binds the planted token to a unit (diagnostic, after the run)"
        per_type[t] = dict(n=n, detected=k, recall=round(k / n, 3) if n else None, wilson95=wilson(k, n),
                           any_finding=ka, any_recall=round(ka / n, 3) if n else None, any_wilson95=wilson(ka, n),
                           eligible_limitations=dict((L, pools[f"{t}:{L}"]) for L in LANGS_T), by_lang=by_lang,
                           by_subtype={s: dict(n=v[0], detected=v[1]) for s, v in sorted(sub.items())},
                           also_found_as=dict(sorted(Counter(kd for r in rows for kd in r["kinds"]).items())),
                           miss_reasons=dict(Counter(r["reason"] for r in rows if not r["hit"]).most_common()),
                           miss_examples=examples(misses[t]),
                           misses=[dict(id=m["id"], lang=m["lang"], sub=m["sub"], reason=m["reason"]) for m in misses[t]], **extra)
    tot_n = sum(v["n"] for v in per_type.values()); tot_k = sum(v["detected"] for v in per_type.values())
    common = dict(register=f"public SL feed {a.date}: {len(J['de']['lim'])} limitations, {len(rep)} distinct DE/FR/IT text triples",
                  eligible=f"one representative per distinct triple, no baseline finding of any kind: {len(pool)} limitations "
                           f"({flagged_triples} triples with a baseline finding excluded)",
                  sampling=f"per type and target language (fr, it): random.Random('{a.seed}:<type>:<lang>') shuffle, first {a.n} with a site; one fault per copy")
    if v2:
        tokstat = {}
        for L in LANGS_T:
            c = Counter()
            for i in pool:
                for x in ntoks(nrm(J[L]["lim"][i]), L): c[("excluded: " + x["excluded"]) if x["excluded"] else ("site: " + x["cat"])] += 1
            tokstat[L] = dict(sorted(c.items()))
        protocol = dict(
            written="PROTOCOL v2 in the tools/audit_inject.py docstring, before the first v2 run; v1 and the audit's rules unchanged",
            why="v1 sites are 'a number followed by a unit word' (the audit's own R2 binding) and v1 planted no operator flips",
            **common,
            number_tokens="this file's NUM2/NUMW2 patterns: digit tokens not glued to a preceding letter, dates, number words 2..12 "
                          "(not hyphen-joined); excluded only: BAG indication codes (ddddd.dd, ddddd.XX), Index Therapeuticus "
                          "group codes (after 'I.T.', or zero-padded dd.dd), other multi-separator references (RS 832.112.31)",
            number_tokens_in_eligible_pool=tokstat,
            types=dict(number_any="one number token drawn uniformly from all included tokens of the target, changed as v1 (years +/-1; dates: day or year +/-1)",
                       number_word="one number word 2..12 anywhere in the target changed to another (v1 rule)",
                       operator="one comparison operator within 25 characters of a number (same sentence) flipped: " +
                                "; ".join(f"{L}: " + ", ".join(sorted(set(r.strip() for _, r in OPS[L]))) for L in LANGS_T),
                       negation="one negation within 60 characters of a number (same sentence) dropped: fr 'ne/n' ... pas', 'non'; it 'non'"),
            detection=dict(number_any="as v1 number: number finding with the new value on the target side or the old value on the German side",
                           number_word="as number_any",
                           operator="a target-language finding pointing to the place: a number/unit finding naming a value of a number "
                                    "token within 60 characters of the edit, or an editorial/terminology surface within 30 characters",
                           negation="as operator",
                           any="the limitation has any finding (all were finding-free before the injection)"),
            execution="as v1: register statistics rebuilt from each modified register, shipped terminology pairs, audit.run_all "
                      "on the copy's limitation; equivalence to a full-register run checked on the 'verification' copies")
    else:
        protocol = dict(
            written="before the first run (tools/audit_inject.py docstring); the audit's rules were not changed",
            register=f"public SL feed {a.date}: {len(J['de']['lim'])} limitations, {len(rep)} distinct DE/FR/IT text triples",
            eligible=f"one representative per distinct triple, no baseline finding of any kind: {len(pool)} limitations "
                     f"({flagged_triples} triples with a baseline finding excluded)",
            sampling=f"per type and target language (fr, it): random.Random('{a.seed}:<type>:<lang>') shuffle, first {a.n} with a site; one fault per copy",
            types=dict(number="one number (digits or number word 2..12, followed by a unit word) changed to another plausible value",
                       unit="one unit changed within its dimension, number kept (mg<->µg, g->mg, kg->g, ml->dl; days->weeks->months, months->weeks, years->months, hours->days)",
                       deletion="one number-bearing sentence (text has >= 2) or comma clause (sentence has >= 2) deleted",
                       language="the target field replaced by one of the two other language fields (50/50)",
                       typo="one edit in the word before a number, the unit word after it, or a number word: glue (delete the space; not before a unit symbol), delete, double, substitute or transpose a letter"),
            detection=dict(number="number finding: new value on the target side or old value on the German side",
                           unit="unit finding for the changed value",
                           deletion="number finding with a deleted value on the German side",
                           language="language finding on the target field naming the source language",
                           typo="editorial finding whose surface is within 30 characters of the edit",
                           any="the limitation has any finding (all were finding-free before the injection)"),
            execution="register statistics rebuilt from each modified register (audit.build_stats on the modified language), "
                      "shipped terminology pairs (as --terms), audit.run_all on the copy's limitation; equivalence to a "
                      "full-register run checked on the 'verification' copies")
    out = dict(
        generated_by=("python3 tools/audit_inject.py --protocol v2" + ("" if a.n == 100 else f" --n {a.n}") + ("" if a.verify == "40" else f" --verify {a.verify}"))
                     if v2 else
                     ("python3 tools/audit_inject.py" + ("" if a.n == 100 else f" --n {a.n}") + ("" if a.verify == "100" else f" --verify {a.verify}")),
        model_calls=0, network=False, date=a.date, seed=a.seed, protocol=protocol,
        summary=dict(injections=tot_n, detected=tot_k, recall=round(tot_k / tot_n, 3) if tot_n else None, wilson95=wilson(tot_k, tot_n),
                     note="pooled over types with equal n per type: a summary of this protocol's mix, not of real error frequencies"),
        types=per_type,
        verification=dict(copies=len(V), stats_identical=sum(v["stats_identical"] for v in V),
                          limitation_identical=sum(v["limitation_identical"] for v in V),
                          findings_new_elsewhere=sum(v["elsewhere_new"] for v in V),
                          findings_lost_elsewhere=sum(v["elsewhere_lost"] for v in V),
                          statistic_only_changes_elsewhere=sum(v["elsewhere_statistic_only"] for v in V), copies_list=V,
                          note="full-register run_all on these copies: false positives elsewhere = findings on other limitations (by identity) that "
                               "the baseline does not have; statistic-only = the same finding with a different trigram margin "
                               "(the language profile moved by the copy's one changed text)"),
        baseline=dict(findings=len(B), by_kind=dict(Counter(f["kind"] for f in B)), limitations=len(flagged)),
        inputs=dict(audit_py_sha256=sha(os.path.join(ROOT, "src", "gleichlaut", "audit.py")),
                    snapshot_sha256={X: sha(os.path.join(a.hist, f"{a.date}-{X}.json")) for X in A.LANGS},
                    term_pairs=os.path.relpath(A.TERMS, ROOT)),
        runtime=dict(seconds_total=round(time.time() - t0, 1), seconds_baseline=round(t_base, 1), seconds_copies=round(t_runs, 1),
                     jobs=a.jobs, seconds_per_copy_core=round(t_runs * a.jobs / max(1, len(jobs)), 2)))
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    json.dump(out, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{'type':9} {'n':>4} {'det':>4} {'recall':>7}  wilson95       any")
    for t, v in per_type.items():
        print(f"{t:9} {v['n']:4d} {v['detected']:4d} {v['recall']:7.3f}  {v['wilson95'][0]:.3f}-{v['wilson95'][1]:.3f}  {v['any_recall']:.3f}")
    vv = out["verification"]
    print(f"verified {vv['copies']} copies as full runs: stats identical {vv['stats_identical']}, limitation identical "
          f"{vv['limitation_identical']}, new findings elsewhere {vv['findings_new_elsewhere']}, lost {vv['findings_lost_elsewhere']}, "
          f"statistic-only changes {vv['statistic_only_changes_elsewhere']}")
    print(f"{out['runtime']['seconds_total']} s; wrote {os.path.relpath(a.out, ROOT)}")


def main_r15(a):
    """PROTOCOL r15 (docstring): planted operator flips, negations dropped and added, number words changed, on one half."""
    if not a.half: sys.exit("--protocol r15 needs --half dev|held")
    seed = a.seed if a.seed is not None else SEED_R15[a.half]
    verify = int(a.verify) if a.verify not in (None, "all") else (0 if a.verify is None else 10 ** 9)
    out_p = a.out or os.path.join(ROOT, "eval", "results", f"audit_injection_r15_{a.half}.json")
    if not os.path.exists(os.path.join(a.hist, f"{a.date}-de.json")): sys.exit(f"no snapshot {a.date} in {a.hist} (--hist DIR)")
    t0 = time.time()
    _init(a.hist, a.date); J, P = G["J"], G["P"]; G["r5"] = True
    B, _, _ = A.run_all(None, a.date, J, G["names"], A._prep(dict(G["base"])), pairs=P, r5=True)
    flagged = set(f["id"] for f in B); G["baseline"] = Counter(proj(f) for f in B); G["baseline_id"] = Counter(ident(f) for f in B)
    rep = {}
    for i in sorted(J["de"]["lim"]):
        k = tuple(nrm(J[X]["lim"].get(i) or "") for X in A.LANGS)
        if all(k) and k not in rep: rep[k] = i
    inhalf = [i for i in rep.values() if A.half(i) == a.half]
    pool = sorted(i for i in inhalf if i not in flagged)
    jobs, pools = [], {}
    for t in TYPES_R15:
        for L in LANGS_T:
            rng = random.Random(f"{seed}:{t}:{L}"); ids = list(pool); rng.shuffle(ids); n = elig = 0
            for i in ids:
                old = nrm(J[L]["lim"][i]); inj = INJ_R15[t](old, L, rng)
                if inj is None: continue
                elig += 1
                if n >= a.n: continue
                assert inj["new"] != old
                jobs.append(dict(k=len(jobs), type=t, lang=L, id=i, old=old, new=inj["new"], inj={k: v for k, v in inj.items() if k != "new"},
                                 de=nrm(J["de"]["lim"][i]), texts={X: J[X]["lim"][i] for X in A.LANGS}, verify=False))
                n += 1
            pools[f"{t}:{L}"] = elig
    if verify:
        per = defaultdict(list)
        for j in jobs: per[j["type"]].append(j["k"])
        q = max(1, verify // len(TYPES_R15))
        for t in TYPES_R15:
            for k in per[t][::max(1, len(per[t]) // q)][:q]: jobs[k]["verify"] = True
    t1 = time.time(); res = {}
    with ProcessPoolExecutor(max_workers=a.jobs, mp_context=multiprocessing.get_context("fork")) as ex:
        light = [dict(k=j["k"], id=j["id"], lang=j["lang"], new=j["new"], verify=j["verify"]) for j in jobs]
        for r in ex.map(run_copy, light, chunksize=4): res[r["k"]] = r
    t_runs = time.time() - t1
    per_type, V = {}, []
    for t in TYPES_R15:
        rows = []
        for j in (j for j in jobs if j["type"] == t):
            F = res[j["k"]]["findings"]; hb, ha = detected_r15(j, F, after=False), detected_r15(j, F, after=True)
            rows.append(dict(j=j, before=hb, after=ha, kinds=sorted(set(f["kind"] for f in F)),
                             reason=None if ha else reason_r15(j, F, None),
                             findings=[f"{f['kind']}: " + snip(f.get("description") or "", 140) for f in F]))
            if "verify" in res[j["k"]]: V.append(dict(type=t, id=j["id"], lang=j["lang"], **res[j["k"]]["verify"]))
        n = len(rows); kb = sum(r["before"] for r in rows); ka = sum(r["after"] for r in rows)
        bl = {L: dict(n=sum(r["j"]["lang"] == L for r in rows), before=sum(r["before"] for r in rows if r["j"]["lang"] == L),
                      after=sum(r["after"] for r in rows if r["j"]["lang"] == L)) for L in LANGS_T}
        for L in LANGS_T:
            m = bl[L]["n"]; bl[L].update(recall_before=round(bl[L]["before"] / m, 3) if m else None, recall_after=round(bl[L]["after"] / m, 3) if m else None,
                                         wilson95_after=wilson(bl[L]["after"], m))
        sub = defaultdict(lambda: [0, 0])
        for r in rows: sub[r["j"]["inj"]["sub"]][0] += 1; sub[r["j"]["inj"]["sub"]][1] += r["after"]
        ms = [dict(id=r["j"]["id"], lang=r["j"]["lang"], sub=r["j"]["inj"]["sub"], before=snip(r["j"]["inj"]["before"]),
                   after=snip(r["j"]["inj"]["after"]), reason=r["reason"], findings=r["findings"]) for r in rows if not r["after"]]
        per_type[t] = dict(n=n, detected_before=kb, recall_before=round(kb / n, 3) if n else None, wilson95_before=wilson(kb, n),
                           detected_after=ka, recall_after=round(ka / n, 3) if n else None, wilson95_after=wilson(ka, n),
                           eligible_limitations={L: pools[f"{t}:{L}"] for L in LANGS_T}, by_lang=bl,
                           by_subtype={k: dict(n=v[0], detected_after=v[1]) for k, v in sorted(sub.items())},
                           also_found_as=dict(sorted(Counter(kd for r in rows for kd in r["kinds"]).items())),
                           miss_reasons=dict(Counter(m["reason"] for m in ms).most_common()), miss_examples=examples(ms),
                           misses=[dict(id=m["id"], lang=m["lang"], sub=m["sub"], reason=m["reason"]) for m in ms])
    out = dict(generated_by=f"python3 tools/audit_inject.py --protocol r15 --half {a.half}" + ("" if a.n == 100 else f" --n {a.n}")
                            + (f" --verify {a.verify}" if a.verify else ""),
               model_calls=0, network=False, date=a.date, half=a.half, seed=seed,
               status="design (dev half): not a measurement" if a.half == "dev" else "pre-registered measurement (PREREG R15)",
               protocol=dict(written="PROTOCOL r15 in the tools/audit_inject.py docstring; PREREG R15 (commit 28fe22b)",
                             register=f"public SL feed {a.date}: {len(J['de']['lim'])} limitations, {len(rep)} distinct DE/FR/IT text triples",
                             eligible=f"half {a.half}: {len(inhalf)} triples, {len(pool)} with no finding of any kind (round-5 kinds included)",
                             sampling=f"per type and target language: random.Random('{seed}:<type>:<lang>') shuffle, first {a.n} with a site; one fault per copy",
                             types=dict(operator="v2 operator flip", negation_drop="v2 negation drop", negation_add="docstring 'negation_add'",
                                        number_word="v2 number word change"),
                             detection="docstring 'PROTOCOL r15': before = v2 rule on the pre-round-5 kinds; after = plus the round-5 kinds"),
               summary={t: dict(n=v["n"], recall_before=v["recall_before"], recall_after=v["recall_after"], wilson95_after=v["wilson95_after"])
                        for t, v in per_type.items()},
               types=per_type,
               verification=dict(copies=len(V), stats_identical=sum(v["stats_identical"] for v in V),
                                 limitation_identical=sum(v["limitation_identical"] for v in V),
                                 findings_new_elsewhere=sum(v["elsewhere_new"] for v in V), findings_lost_elsewhere=sum(v["elsewhere_lost"] for v in V),
                                 copies_list=V),
               baseline=dict(findings=len(B), by_kind=dict(Counter(f["kind"] for f in B)), limitations=len(flagged)),
               inputs=dict(audit_py_sha256=sha(os.path.join(ROOT, "src", "gleichlaut", "audit.py")),
                           snapshot_sha256={X: sha(os.path.join(a.hist, f"{a.date}-{X}.json")) for X in A.LANGS}),
               runtime=dict(seconds_total=round(time.time() - t0, 1), seconds_copies=round(t_runs, 1), jobs=a.jobs))
    os.makedirs(os.path.dirname(out_p), exist_ok=True)
    json.dump(out, open(out_p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{'type':14} {'n':>4} {'before':>7} {'after':>7}  wilson95(after)")
    for t, v in per_type.items():
        print(f"{t:14} {v['n']:4d} {v['recall_before']:7.3f} {v['recall_after']:7.3f}  {v['wilson95_after'][0]:.3f}-{v['wilson95_after'][1]:.3f}")
    print(f"{out['runtime']['seconds_total']} s; wrote {os.path.relpath(out_p, ROOT)}")


# ================================================================== protocol r22 (docstring 'PROTOCOL r22')
def run_copy_r22(job):
    i, L, new = job["id"], job["lang"], job["new"]
    J2 = copy_of(i, L, new); st = A._prep(stats_for(J2, L))
    sub = {X: {"lim": {i: J2[X]["lim"][i]}} for X in A.LANGS}; nm = {i: G["names"].get(i, [])}
    F22, _, _ = A.run_all(None, G["date"], sub, nm, st, pairs=G["P"], r5="r22")
    old = [f for f in F22 if f["kind"] in OLD_KINDS]
    F15 = old + A.run_r5(sub, nm, [f for f in old if f["kind"] == "number"])
    return dict(k=job["k"], r15=F15, r22=F22)


def main_r22(a):
    """PROTOCOL r22 (docstring): R15's planted copies, scored with the R15 and the R22 round-5 rules."""
    if not a.half: sys.exit("--protocol r22 needs --half dev|held")
    seed = a.seed if a.seed is not None else SEED_R15[a.half]
    out_p = a.out or os.path.join(ROOT, "eval", "results", f"audit_injection_r22_{a.half}.json")
    t0 = time.time()
    _init(a.hist, a.date); J, P = G["J"], G["P"]
    B, _, _ = A.run_all(None, a.date, J, G["names"], A._prep(dict(G["base"])), pairs=P, r5=True)
    flagged = set(f["id"] for f in B)
    rep = {}
    for i in sorted(J["de"]["lim"]):
        k = tuple(nrm(J[X]["lim"].get(i) or "") for X in A.LANGS)
        if all(k) and k not in rep: rep[k] = i
    inhalf = [i for i in rep.values() if A.half(i) == a.half]
    pool = sorted(i for i in inhalf if i not in flagged)
    jobs, pools = [], {}
    for t in TYPES_R15:                                   # exactly main_r15's sampling
        for L in LANGS_T:
            rng = random.Random(f"{seed}:{t}:{L}"); ids = list(pool); rng.shuffle(ids); n = elig = 0
            for i in ids:
                old = nrm(J[L]["lim"][i]); inj = INJ_R15[t](old, L, rng)
                if inj is None: continue
                elig += 1
                if n >= a.n: continue
                jobs.append(dict(k=len(jobs), type=t, lang=L, id=i, old=old, new=inj["new"], inj={k: v for k, v in inj.items() if k != "new"},
                                 de=nrm(J["de"]["lim"][i])))
                n += 1
            pools[f"{t}:{L}"] = elig
    t1 = time.time(); res = {}
    with ProcessPoolExecutor(max_workers=a.jobs, mp_context=multiprocessing.get_context("fork")) as ex:
        light = [dict(k=j["k"], id=j["id"], lang=j["lang"], new=j["new"]) for j in jobs]
        for r in ex.map(run_copy_r22, light, chunksize=4): res[r["k"]] = r
    t_runs = time.time() - t1
    per_type = {}
    for t in TYPES_R15:
        rows = []
        for j in (j for j in jobs if j["type"] == t):
            r = res[j["k"]]
            rows.append(dict(j=j, r15=detected_r15(j, r["r15"], after=True), r22=detected_r15(j, r["r22"], after=True),
                             before=detected_r15(j, r["r22"], after=False)))
        n = len(rows); k15 = sum(x["r15"] for x in rows); k22 = sum(x["r22"] for x in rows)
        bl = {L: dict(n=sum(x["j"]["lang"] == L for x in rows), r15=sum(x["r15"] for x in rows if x["j"]["lang"] == L),
                      r22=sum(x["r22"] for x in rows if x["j"]["lang"] == L)) for L in LANGS_T}
        for L in LANGS_T: bl[L]["wilson95_r22"] = wilson(bl[L]["r22"], bl[L]["n"])
        per_type[t] = dict(n=n, detected_before=sum(x["before"] for x in rows), detected_r15=k15, detected_r22=k22,
                           recall_r15=round(k15 / n, 3) if n else None, recall_r22=round(k22 / n, 3) if n else None,
                           wilson95_r22=wilson(k22, n), eligible_limitations={L: pools[f"{t}:{L}"] for L in LANGS_T}, by_lang=bl,
                           gained=sum(1 for x in rows if x["r22"] and not x["r15"]), lost=sum(1 for x in rows if x["r15"] and not x["r22"]),
                           lost_list=[dict(id=x["j"]["id"], lang=x["j"]["lang"], sub=x["j"]["inj"]["sub"]) for x in rows if x["r15"] and not x["r22"]])
    out = dict(generated_by=f"python3 tools/audit_inject.py --protocol r22 --half {a.half}" + ("" if a.n == 100 else f" --n {a.n}"),
               model_calls=0, network=False, date=a.date, half=a.half, seed=seed,
               status="design (dev half): not a measurement" if a.half == "dev" else "pre-registered measurement (PREREG R22)",
               protocol=dict(written="PROTOCOL r22 in the tools/audit_inject.py docstring; PREREG R22 (commit 2514b9b)",
                             copies="R15's (protocol r15, same seed and eligibility)",
                             eligible=f"half {a.half}: {len(inhalf)} triples, {len(pool)} with no finding of any kind under the frozen R15 audit",
                             detection="R15's 'after' rule, with the R15 kinds (reproduction) and with the R22 kinds (measurement)"),
               rules=dict(r22_block_sha256=A.r22_block_sha(), r22_logic_sha256=A.r22_logic_sha(), r15_logic_sha256=A.r5_logic_sha(), op_align=A.OP_ALIGN),
               summary={t: dict(n=v["n"], recall_r15=v["recall_r15"], recall_r22=v["recall_r22"], wilson95_r22=v["wilson95_r22"]) for t, v in per_type.items()},
               types=per_type,
               inputs=dict(audit_py_sha256=sha(os.path.join(ROOT, "src", "gleichlaut", "audit.py")),
                           snapshot_sha256={X: sha(os.path.join(a.hist, f"{a.date}-{X}.json")) for X in A.LANGS}),
               runtime=dict(seconds_total=round(time.time() - t0, 1), seconds_copies=round(t_runs, 1), jobs=a.jobs))
    os.makedirs(os.path.dirname(out_p), exist_ok=True)
    json.dump(out, open(out_p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{'type':14} {'n':>4} {'r15':>7} {'r22':>7}  wilson95(r22)")
    for t, v in per_type.items():
        print(f"{t:14} {v['n']:4d} {v['recall_r15']:7.3f} {v['recall_r22']:7.3f}  {v['wilson95_r22'][0]:.3f}-{v['wilson95_r22'][1]:.3f}")
    print(f"{out['runtime']['seconds_total']} s; wrote {os.path.relpath(out_p, ROOT)}")


if __name__ == "__main__":
    main()
