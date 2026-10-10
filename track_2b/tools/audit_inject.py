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

usage: python3 tools/audit_inject.py [--hist DIR] [--n 100] [--seed 20261010] [--jobs J] [--verify K|all] [--out FILE]
writes eval/results/audit_injection.json"""
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
    F, _, _ = A.run_all(None, G["date"], sub, {i: G["names"].get(i, [])}, st, pairs=G["P"])
    out = dict(k=job["k"], findings=F)
    if verify:
        st_full = A.build_stats(J2)
        same_stats = {k: v for k, v in st_full.items() if k != "_vocab"} == {k: v for k, v in st.items() if k != "_vocab"}
        FF, _, _ = A.run_all(None, G["date"], J2, G["names"], A._prep(st_full), pairs=G["P"])
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
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--jobs", type=int, default=min(8, os.cpu_count() or 1))
    ap.add_argument("--verify", default="100", help="copies re-run as a full-register audit (a number, or 'all')")
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args(argv)
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
    for ti, t in enumerate(TYPES):
        for L in LANGS_T:
            rng = random.Random(f"{a.seed}:{t}:{L}"); ids = list(pool); rng.shuffle(ids); n = 0; elig = 0
            for i in ids:
                old = nrm(J[L]["lim"][i])
                if t == "language": inj = INJ[t](old, L, rng, {X: J[X]["lim"][i] for X in A.LANGS if X != L})
                else: inj = INJ[t](old, L, rng)
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
        for t in TYPES:                                            # spread over types and both languages, deterministic
            xs = per[t]; step = max(1, len(xs) // max(1, k // len(TYPES)))
            ver |= set(xs[::step][:max(1, k // len(TYPES))]) if k else set()
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
    for t in TYPES:
        J_t = [j for j in jobs if j["type"] == t]
        rows = []
        for j in J_t:
            F = res[j["k"]]["findings"]; hit = detected(j, F)
            st_j = None
            if not hit:
                st_j = A._prep(stats_for(copy_of(j["id"], j["lang"], j["new"]), j["lang"])) if t in ("language", "typo") else None
                rs = reason(j, F, st_j)
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
        per_type[t] = dict(n=n, detected=k, recall=round(k / n, 3) if n else None, wilson95=wilson(k, n),
                           any_finding=ka, any_recall=round(ka / n, 3) if n else None, any_wilson95=wilson(ka, n),
                           eligible_limitations=dict((L, pools[f"{t}:{L}"]) for L in LANGS_T), by_lang=by_lang,
                           by_subtype={s: dict(n=v[0], detected=v[1]) for s, v in sorted(sub.items())},
                           also_found_as=dict(sorted(Counter(kd for r in rows for kd in r["kinds"]).items())),
                           miss_reasons=dict(Counter(r["reason"] for r in rows if not r["hit"]).most_common()),
                           miss_examples=examples(misses[t]),
                           misses=[dict(id=m["id"], lang=m["lang"], sub=m["sub"], reason=m["reason"]) for m in misses[t]], **extra)
    tot_n = sum(v["n"] for v in per_type.values()); tot_k = sum(v["detected"] for v in per_type.values())
    out = dict(
        generated_by="python3 tools/audit_inject.py" + ("" if a.n == 100 else f" --n {a.n}") + ("" if a.verify == "100" else f" --verify {a.verify}"),
        model_calls=0, network=False, date=a.date, seed=a.seed,
        protocol=dict(
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
                      "full-register run checked on the 'verification' copies"),
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


if __name__ == "__main__":
    main()
