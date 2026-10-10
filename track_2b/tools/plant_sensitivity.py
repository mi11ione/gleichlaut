"""Annotator sensitivity (PREREG R11): how often do the blind Claude annotators of eval/labels/PROTOCOL.md catch a meaning
error? Known meaning errors are planted into copies of ready fresh-166 drafts that the existing labels call exact or
equivalent, mixed with the same drafts untouched and with real labelled drafts, shuffled under neutral ids, and labelled
by the unchanged protocol twice: (a) as used (official_new shown) and (b) with the published reference hidden.
Deterministic (seed 20261012), stdlib only, no model, no network.

DESIGN (fixed in this file and in PREREG R11 before any annotation)
  Bases      ready drafts (guards3 passed) of the three recorded fresh-166 runs (70B, 8B Q8_0, 8B Q4_K_M), pooled by
             (item, normalised text). Eligible: every label the text carries is 'exact' (equals BAG's text) or
             'equivalent' (70B: the first annotation's class, and not 'needs a fix' after the tie-break; 8B: the final
             column of m1_<build>_fresh166.tsv). One base per item (seeded choice when an item has several).
  Types      one meaning error per planted copy, mirroring the REAL class of PROTOCOL.md:
    drop        a clause or sentence deleted (3..40 words, under half the text; the text keeps the rest)
    and_or      fr ' et ' <-> ' ou ', it ' e '/' ed ' <-> ' o ' (never inside 'et/ou', 'e/o')
    obligation  fr doit/doivent <-> peut/peuvent; it deve/devono <-> può/possono (sites outside the indication-code
                sentence first)
    scope       population or line widened or narrowed: fr adultes -> adultes et adolescents, adulte -> adulte ou
                adolescent, en monothérapie -> en monothérapie ou en association, de/en première ligne -> de/en première
                ou deuxième ligne, adultes et adolescents -> adultes, enfants et adolescents -> adolescents; it the same
                with adulti (e adolescenti), adulto (o adolescente), in monoterapia (o in associazione), prima (o seconda)
                linea
    operator    direction flipped: the comparison operators of tools/audit_inject.py v2 (au moins <-> au plus, plus de <->
                moins de, supérieur <-> inférieur, ≥ <-> ≤, almeno <-> al massimo, più di <-> meno di, oltre <-> sotto,
                ...; symbols only next to a number) and fr à partir de / dès <number> -> jusqu'à, it a partire da / dai
                <number> -> fino a
    negation    a negation dropped (fr ne/n' ... pas, non; it non) or added (fr est/sont remboursé/indiqué/... -> n'est
                pas / ne sont pas ..., doit être -> ne doit pas être; it è/sono rimborsato/indicato/... -> non è/sono ...,
                deve essere -> non deve essere), drop or add 50/50 where both exist
    number      one number of the draft changed (tools/audit_inject.py v2 tokens and rule: indication codes, I.T. codes
                and multi-separator references excluded; a number bound to a unit first)
  Assignment bases in seeded order, fewest applicable types first; each gets the applicable type with the lowest count so
             far in its language (ties seeded): stratified by type and FR/IT. The site and the edit within a draft are
             drawn with random.Random('20261012:<item>:<type>').
  Sets       every base appears twice, planted and untouched, never in the same worklist: two sets per protocol; set 1
             holds the planted copy of half the bases (alternating within each type x language) and the untouched copy of
             the others, set 2 the reverse. Real items (existing labelled fresh-166 drafts of other items whose final
             label is REAL, stale or german) are split between the sets. No item appears twice in one worklist.
  Worklists  per protocol and set, seeded shuffle, neutral ids; fields as PROTOCOL.md: id, lang, de_old, de_new, tgt_old,
             draft, official_new ((b): no official_new). The key (id -> item, kind, type, edit) is written apart.

usage: python3 tools/plant_sensitivity.py [--check]
writes eval/labels/sensitivity_key.json and eval/labels/sensitivity_{a,b}_set{1,2}_worklist.json; --check verifies the
committed files are reproduced byte for byte."""
import json, os, random, re, sys
from collections import Counter

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(ROOT, "src")); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gleichlaut import score, core          # noqa: E402
import audit_inject as AI                   # noqa: E402

SEED = 20261012
TYPES = ("drop", "and_or", "obligation", "scope", "operator", "negation", "number")
RUNS = (("70b", "runs/70b_fresh166_g3_final.jsonl"), ("q8_0", "runs/8b_q8_0_fresh166_g3_final.jsonl"),
        ("q4_k_m", "runs/8b_q4_k_m_fresh166_g3_final.jsonl"))
LABELS = os.path.join(ROOT, "eval", "labels")
PROTOS = {"a": ("reference_shown", ("M", "N")), "b": ("reference_hidden", ("P", "R"))}
SEVERE = ("REAL", "stale", "german")
norm = core.lock.norm


# ------------------------------------------------------------------ labels and pool
def _tsv(name):
    lines = open(os.path.join(LABELS, name), encoding="utf-8").read().splitlines(); hdr = lines[0].split("\t")
    return {c[0]: dict(zip(hdr, c)) for c in (l.split("\t") for l in lines[1:])}


def run_labels():
    """run -> {key: (class, final needs_fix)} for the labelled drafts of that run."""
    U = score.load_labels("fresh166_unflagged.tsv"); F = score.load_labels("fresh166_flagged20.tsv")
    B = _tsv("fresh166_second_annotator.tsv"); T = {k: v["needs_fix"] for k, v in _tsv("fresh166_tiebreak.tsv").items()}
    A = {k: ("no" if v in ("equivalent", "preexisting", "exact") else "yes") for k, v in U.items()}
    A.update({k: ("no" if v == "good" else "yes") for k, v in F.items()})
    fin = {k: (A[k] if A[k] == B[k]["needs_fix"] else T[k]) for k in A}
    out = {"70b": {k: (U.get(k) or B[k]["class"], fin[k]) for k in A}}
    for b in ("q8_0", "q4_k_m"):
        out[b] = {k: (v["final"], v["final_fix"]) for k, v in _tsv(f"m1_{b}_fresh166.tsv").items()}
    return out


def pool():
    """-> items, bases {key: dict}, real {key: dict}"""
    I = {x["key"]: x for x in score.load_items("items/items_fresh.json")}
    L = run_labels(); seen = {}
    for run, rel in RUNS:
        for k, r in score.load_jsonl(rel).items():
            o = norm(r["out"])
            cls = "exact" if o == norm(I[k]["tgt_new"]) else (L[run][k][0] if k in L[run] else None)
            fix = "no" if cls == "exact" else (L[run][k][1] if k in L[run] else None)
            d = seen.setdefault((k, o), dict(key=k, text=r["out"], runs=[], ready=[], labels=[]))
            d["runs"].append(run); d["ready"].append(not r["guard_flag"])
            if cls: d["labels"].append((run, cls, fix))
    bases, real = {}, {}
    rng = random.Random(f"{SEED}:pool")
    for (k, o), d in sorted(seen.items()):
        if not d["labels"]: continue
        ok = all(c in ("exact", "equivalent") and f == "no" for _, c, f in d["labels"])
        if ok and any(d["ready"]): bases.setdefault(k, []).append(d)
    for k in sorted(bases):
        c = bases[k]; bases[k] = c[0] if len(c) == 1 else rng.choice(c)
    for (k, o), d in sorted(seen.items()):
        if k in bases or not d["labels"]: continue
        sev = [c for _, c, f in d["labels"] if c in SEVERE and f == "yes"]
        if sev: real.setdefault(k, []).append(dict(d, existing=sev[0]))
    for k in sorted(real):
        c = real[k]; real[k] = c[0] if len(c) == 1 else rng.choice(c)
    return I, bases, real


# ------------------------------------------------------------------ sites: (t, L) -> list of (start, end, replacement or None, sub)
def _code_sentence(t, s):
    a = max(t.rfind(". ", 0, s), t.rfind(": ", 0, s)); b = t.find(". ", s)
    return bool(re.search(r"(?i)\bcod(?:e|ice)\b", t[a + 1:(b if b >= 0 else len(t))]))


def _prefer(t, S):
    """sites outside the indication-code sentence when there are any."""
    P = [x for x in S if not _code_sentence(t, x[0])]
    return P or S


_ABBR = re.compile(r"(?:\b[A-Z]|\bI\.T|\b(?:z\.B|max|min|Fr|env|ca|resp|p\.ex|etc|cf|al|art|Art|no|n|nr|Nr|ev|p\.es|ecc|vol))$")


def sentences(t):
    """sentence spans: a '.' or ';' followed by space and an upper-case letter ends a sentence, unless it closes an
    abbreviation or an initial ('I.T. 02.06', 'Fr. 263.80', 'max. 24' never split: a digit or lower case follows)."""
    out, a = [], 0
    for m in re.finditer(r"[.;](?=\s+[A-ZÀ-Ý])", t):
        if _ABBR.search(t[a:m.start()]): continue
        out.append((a, m.end())); a = m.end()
        while a < len(t) and t[a].isspace(): a += 1
    if a < len(t): out.append((a, len(t)))
    return out


def s_drop(t, L):
    """deletable condition spans: a sentence (text has >= 2), a comma clause (its sentence has >= 2), a parenthesis, or the
    middle element of a coordination 'X et/ou Y et/ou Z' / 'X e/o Y e/o Z' (Y deleted with its connector)."""
    cand, S = [], sentences(t)
    if len(S) >= 2: cand += [(s, e, "sentence") for s, e in S]
    for s, e in S:
        parts, p = [], s
        for m in re.finditer(r",\s", t[s:e]):
            parts.append((p, s + m.start())); p = s + m.end()
        parts.append((p, e))
        if len(parts) >= 2: cand += [(a, b, "comma") for a, b in parts[1:]]       # clauses after the first comma
    cand += [(m.start(), m.end(), "parenthesis") for m in re.finditer(r" \([^()]*\)", t)]
    co = r" (?:et/ou|e/o) "
    cand += [(m.start(), m.end(1), "coordination") for m in re.finditer(co + r"(.*?)(?=" + co + ")", t)]
    out = []
    for s, e, lvl in cand:
        seg = t[s:e]; nw = len(seg.split())
        if not 3 <= nw <= 40 or len(seg) >= 0.5 * len(t): continue
        a, b = s, e
        if lvl == "comma": a -= 2                                                   # the ', ' before the clause
        elif lvl == "sentence":
            if b < len(t) and t[b:b + 1] == " ": b += 1
            elif a > 0 and t[a - 1:a] == " ": a -= 1
        if (t[:a] + t[b:]).strip(" .;,"): out.append((a, b, "", lvl))
    return _prefer(t, sorted(set(out)))


AO = {"fr": [(r"(?<=\S) et (?=\S)", " ou "), (r"(?<=\S) ou (?=\S)", " et ")],
      "it": [(r"(?<=\S) e (?=\S)", " o "), (r"(?<=\S) ed (?=\S)", " o "), (r"(?<=\S) o (?=\S)", " e ")]}


def s_and_or(t, L):
    out = []
    for p, rep in AO[L]:
        for m in re.finditer(p, t):
            if "/" in t[max(0, m.start() - 1):m.end() + 1]: continue
            out.append((m.start(), m.end(), rep, m.group(0).strip() + "->" + rep.strip()))
    return _prefer(t, sorted(out))


OB = {"fr": {"doit": "peut", "doivent": "peuvent", "peut": "doit", "peuvent": "doivent"},
      "it": {"deve": "può", "devono": "possono", "può": "deve", "possono": "devono"}}


def s_obligation(t, L):
    out = []
    for m in re.finditer(r"(?i)\b(" + "|".join(OB[L]) + r")\b", t):
        w = m.group(1); rep = OB[L][w.lower()]
        if w[0].isupper(): rep = rep[0].upper() + rep[1:]
        out.append((m.start(), m.end(), rep, w.lower() + "->" + rep.lower()))
    return _prefer(t, out)


SC = {"fr": [(r"\badultes(?!\s+(?:et|ou)\s+(?:les\s+)?(?:adolescents|enfants))\b", "adultes et adolescents"),
             (r"\badulte(?!s)(?!\s+(?:et|ou)\s)\b", "adulte ou adolescent"),
             (r"\ben monothérapie(?!\s+ou\b)", "en monothérapie ou en association"),
             (r"\b(de|en) première ligne\b", r"\1 première ou deuxième ligne"),
             (r"\badultes et (?:les )?adolescents\b", "adultes"), (r"\benfants et (?:les )?adolescents\b", "adolescents")],
      "it": [(r"\badulti(?!\s+(?:e|o)\s+(?:gli\s+)?(?:adolescenti|bambini))\b", "adulti e adolescenti"),
             (r"\badulto(?!\s+(?:e|o)\s)\b", "adulto o adolescente"),
             (r"\bin monoterapia(?!\s+o\b)", "in monoterapia o in associazione"),
             (r"\b(di|in) prima linea\b", r"\1 prima o seconda linea"),
             (r"\badulti e (?:gli )?adolescenti\b", "adulti"), (r"\bbambini e (?:gli )?adolescenti\b", "adolescenti")]}


_YOUNG = re.compile(r"(?i)adolescen|enfant|pédiatri|ragazz|bambin|pediatri")


def s_scope(t, L):
    """widening to adolescents only where the text names no younger group already."""
    taken, out = [], []
    for p, rep in SC[L][::-1]:                         # narrowing patterns (longer) first
        for m in re.finditer(p, t):
            if any(m.start() < b and a < m.end() for a, b in taken): continue
            taken.append(m.span())
            if "adolescen" in rep and _YOUNG.search(t): continue
            out.append((m.start(), m.end(), m.expand(rep), m.group(0) + "->" + m.expand(rep)))
    return sorted(out)


DIR = {"fr": [(r"\b[àÀ] partir de(?=\s+\d)", "jusqu'à"), (r"\b[dD]ès(?=\s+(?:l['’]âge de\s+)?\d)", "jusqu'à")],
       "it": [(r"\b[aA] partire da(?:i|l|gli)?(?=\s+\d)", "fino a"), (r"\b[dD]ai(?=\s+\d+\s+anni)", "fino ai")]}


def s_operator(t, L):
    taken, out = [], []
    for rx, rep in AI.OPS_RX[L] + [(re.compile(p), r) for p, r in DIR[L]]:
        for m in rx.finditer(t):
            if any(m.start() < b and a < m.end() for a, b in taken): continue
            taken.append(m.span())
            if not re.search(r"\w", m.group(0)) and not AI._near_number(t, L, m.start(), m.end(), 25): continue
            if re.search(r"(?i)\b(?:en|in|de|di)\s+$", t[max(0, m.start() - 4):m.start()]): continue   # 'en plus de' = 'in addition to'

            r = rep[0].upper() + rep[1:] if m.group(0)[:1].isupper() else rep
            out.append((m.start(), m.end(), r, m.group(0).lower().strip() + "->" + r.lower().strip()))
    return sorted(out)


NADD = {"fr": [(r"\b(est|sont) (?=(?:rembours|indiqu|autoris|admis|pris en charge)\w*)", None),
               (r"\bdoit (?=être\b)", "ne doit pas ")],
        "it": [(r"\b(è|sono) (?=(?:rimborsat|indicat|ammess|autorizzat)\w*)", None), (r"\bdeve (?=essere\b)", "non deve ")]}


def s_negation(t, L):
    drop, add = [], []
    for name, rx in AI.NEG[L]:
        for m in rx.finditer(t):
            drop.append((m.start(), m.end(), (m.group(1) or "").rstrip() if name == "ne_pas" else "", "drop:" + name))
    for p, rep in NADD[L]:
        for m in re.finditer(p, t):
            if re.search(r"(?i)\b(?:ne|n['’]|non)\s*$", t[max(0, m.start() - 6):m.start()]): continue   # already negated
            if rep is None:
                v = m.group(1)
                r = (("n'est pas " if v == "est" else "ne sont pas ") if L == "fr" else ("non " + v + " "))
            else:
                r = rep
            add.append((m.start(), m.end(), r, "add:" + m.group(0).strip()))
    return drop, add


def s_number(t, L):
    S = [x for x in AI.ntoks(t, L) if not x["excluded"] and x["cat"] != "list"]
    P = [x for x in S if x["cat"] == "v1_site"]
    return P or S


SITES = {"drop": s_drop, "and_or": s_and_or, "obligation": s_obligation, "scope": s_scope, "operator": s_operator,
         "number": s_number, "negation": lambda t, L: [x for p in s_negation(t, L) for x in p]}


def plant(t, L, ty, rng):
    """-> dict(new, sub, before, after)"""
    if ty == "number":
        tok = rng.choice(s_number(t, L)); ov, nv, ns = AI._change(tok, L, rng)
        s, e, rep, sub = tok["s"], tok["e"], ns, f"{tok['surf']}->{ns}"
    elif ty == "negation":
        drop, add = s_negation(t, L)
        S = drop if (drop and (not add or rng.random() < 0.5)) else add
        s, e, rep, sub = rng.choice(S)
    else:
        s, e, rep, sub = rng.choice(SITES[ty](t, L))
    head, tail = t[:s], t[e:]
    if ty == "negation" and sub.startswith("drop"):
        old = t[s:e]
        if not rep and head.endswith(" ") and tail.startswith(" "): tail = tail[1:]
        if rep and tail[:1].isalnum(): rep += " "
        if old[:1].isupper():
            if rep: rep = rep[:1].upper() + rep[1:]
            elif tail: tail = tail[:1].upper() + tail[1:]
    new = head + rep + tail
    assert new != t, (ty, sub)
    a, b = max(0, s - 60), min(len(t), e + 60)
    return dict(new=new, sub=sub, before=t[a:b], after=new[a:b - (len(t) - len(new))])


# ------------------------------------------------------------------ build
def build():
    I, bases, real = pool()
    app = {k: [ty for ty in TYPES if SITES[ty](bases[k]["text"], I[k]["lang"])] for k in bases}
    rng = random.Random(SEED)
    order = sorted(bases); rng.shuffle(order); order.sort(key=lambda k: len(app[k]))
    cnt, typ = Counter(), {}
    for k in order:
        L = I[k]["lang"]; m = min(cnt[(ty, L)] for ty in app[k])
        typ[k] = rng.choice([ty for ty in app[k] if cnt[(ty, L)] == m]); cnt[(typ[k], L)] += 1
    items = {}
    for k in sorted(bases):
        d = bases[k]; x = I[k]
        p = plant(d["text"], x["lang"], typ[k], random.Random(f"{SEED}:{k}:{typ[k]}"))
        base_cls = "exact" if any(c == "exact" for _, c, _ in d["labels"]) else "equivalent"
        common = dict(key=k, lang=x["lang"], base_class=base_cls, base_runs=d["runs"])
        items[f"{k}|planted"] = dict(common, kind="planted", type=typ[k], sub=p["sub"], before=p["before"], after=p["after"],
                                     draft=p["new"])
        items[f"{k}|untouched"] = dict(common, kind="untouched", type=None, draft=d["text"])
    for k in sorted(real):
        d = real[k]
        items[f"{k}|real"] = dict(key=k, lang=I[k]["lang"], kind="real", existing=d["existing"], base_runs=d["runs"],
                                  ready=any(d["ready"]), draft=d["text"])
    # sets: alternate within type x language (offset flips per group so the sets stay balanced)
    plant_set, off = {}, 0
    for g in sorted({(typ[k], I[k]["lang"]) for k in bases}):
        ks = sorted(k for k in bases if (typ[k], I[k]["lang"]) == g); rng.shuffle(ks)
        for i, k in enumerate(ks): plant_set[k] = 1 + (i + off) % 2
        off = (off + len(ks)) % 2
    rk = sorted(real); rng.shuffle(rk); real_set = {k: 1 + i % 2 for i, k in enumerate(rk)}
    for uid, it in items.items():
        k = it["key"]
        it["set"] = (plant_set[k] if it["kind"] == "planted" else 3 - plant_set[k] if it["kind"] == "untouched" else real_set[k])
    W, ids = {}, {}
    for pr, (name, prefixes) in PROTOS.items():
        for st in (1, 2):
            uids = sorted(u for u, it in items.items() if it["set"] == st)
            random.Random(f"{SEED}:{pr}:{st}").shuffle(uids)
            recs = []
            for i, u in enumerate(uids):
                it = items[u]; x = I[it["key"]]; rid = f"{prefixes[st - 1]}{i:03d}"
                r = dict(id=rid, lang=x["lang"], de_old=x["de_old"], de_new=x["de_new"], tgt_old=x["tgt_old"], draft=it["draft"])
                if pr == "a": r["official_new"] = x["tgt_new"]
                recs.append(r); ids.setdefault(pr, {})[rid] = u
            assert len({items[u]["key"] for u in uids}) == len(uids)       # no item twice in one worklist
            W[f"sensitivity_{pr}_set{st}_worklist.json"] = recs
    key = dict(prereg="eval/prereg/PREREG.md R11", seed=SEED, types=list(TYPES), protocols={k: v[0] for k, v in PROTOS.items()},
               counts=dict(bases=len(bases), planted=len(bases), untouched=len(bases), real=len(real),
                           by_type_lang={f"{t}/{L}": cnt[(t, L)] for t in TYPES for L in ("fr", "it")}),
               items={u: {k: v for k, v in it.items() if k != "draft"} for u, it in sorted(items.items())}, ids=ids)
    return W, key


def dumps(o): return json.dumps(o, ensure_ascii=False, indent=1) + "\n"


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    W, key = build(); files = dict(W, **{"sensitivity_key.json": key})
    bad = []
    for name, o in files.items():
        p = os.path.join(LABELS, name)
        if "--check" in argv:
            if not os.path.exists(p) or open(p, encoding="utf-8").read() != dumps(o): bad.append(name)
        else:
            open(p, "w", encoding="utf-8").write(dumps(o))
    if "--check" in argv:
        print("plant_sensitivity:", "OK" if not bad else "DIFFERS " + ", ".join(bad)); return 1 if bad else 0
    c = key["counts"]; print(f"bases {c['bases']}  planted {c['planted']}  untouched {c['untouched']}  real {c['real']}")
    print("by type/lang", c["by_type_lang"])
    for n, r in W.items(): print(n, len(r), "records", sum(len(json.dumps(x, ensure_ascii=False)) for x in r), "chars")
    return 0


if __name__ == "__main__":
    sys.exit(main())
