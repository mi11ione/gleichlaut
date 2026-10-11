"""PREREG R20: an oracle that is not Claude. The 6 Oct 2026 register audit as a frozen list of predictions, scored against
BAG's own later corrections in the public SL feed. Standard library and gleichlaut (itself standard library); no model.

  build   eval/predictions/audit_20261006_predictions.json from the committed audit (data/audit/audit_20261006.json, its
          texts) and the blind labels (eval/labels/audit_relabel.tsv, audit_r15_20261006.tsv). One record per finding: the
          38 findings of the register's 18 issues and the 31 round-5 (experimental) findings. Confirmed by the blind
          majority (real or minor) = a prediction that BAG corrects it; not confirmed = a negative prediction. Each record
          names the divergent language (the odd one out of the three), what each language states on 6 Oct 2026, and the
          correction it predicts. Deterministic; --check compares with the committed file byte for byte.
  check   one SL snapshot (--hist DIR --date D, the extracted <D>-{de,fr,it}.json of `gleichlaut.sl.ingest`; or --fetch D
          | latest: the same public feed, client and user agent as `gleichlaut month --fetch` in the shadow workflow)
          -> eval/predictions/check_<D>.json: per prediction one status (STATUSES), with the evidence.
  score   every check_<D>.json with D after 20261006 -> eval/predictions/score.json: the R20 measure per horizon
          (6 and 12 months), 'pending' until a horizon has passed.

Status of a prediction in a snapshot (fixed in PREREG R20):
  limitation removed          the limitation id is absent from the German, from the finding's language or from the
                              divergent language
  unchanged                   the German, French and Italian texts of the limitation are identical (gleichlaut.sl.ingest.nrm)
  corrected toward agreement  a text changed, the divergent language's text changed, the same check (gleichlaut.audit,
                              6 Oct 2026 statistics and term pairs) no longer reports the finding on the new texts, and the
                              divergent language now states what the other two state at that place: the predicted value
                              (it states the agreed value more often and the odd value less often than on 6 Oct; the
                              agreeing side still states it), the predicted direction of the bound, the negation status of
                              the aligned German sentence, the typo's correction, the new term, its own language
  changed otherwise           any other change (the finding still reported; resolved by a change of the other side; the
                              passage deleted; the divergent language unchanged)
With the divergent language unclear (the third language does not settle it), 'corrected' needs the finding gone and the
German or the finding's language changed.

usage: PYTHONPATH=src python3 tools/check_predictions.py build [--check]
       PYTHONPATH=src python3 tools/check_predictions.py check --hist DIR --date YYYYMMDD [--out FILE]
       PYTHONPATH=src python3 tools/check_predictions.py check --fetch YYYYMMDD|latest [--snapshots DIR] [--out FILE]
       PYTHONPATH=src python3 tools/check_predictions.py score
       PYTHONPATH=src python3 tools/check_predictions.py backtest --hist DIR --from YYYYMMDD --to YYYYMMDD [...]"""
import argparse, datetime, difflib, glob, hashlib, json, math, os, re, sys, tempfile
from collections import Counter

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))
from gleichlaut import audit as au                      # noqa: E402
from gleichlaut.sl.ingest import nrm                    # noqa: E402

DATE = "20261006"
PRED = os.path.join(ROOT, "eval", "predictions", f"audit_{DATE}_predictions.json")
OUTD = os.path.dirname(PRED)
AUDIT = os.path.join(ROOT, "data", "audit", f"audit_{DATE}.json")
TEXTS = os.path.join(ROOT, "data", "audit", f"audit_texts_{DATE}.json")
LABELS = os.path.join(ROOT, "eval", "labels")
FROZEN_UTC = "2026-10-11T01:04:00Z"                     # when the list was frozen (the commit time is the proof)
LANGS = ("de", "fr", "it")
UNCHANGED, CORRECTED, OTHER, REMOVED = "unchanged", "corrected toward agreement", "changed otherwise", "limitation removed"
STATUSES = (UNCHANGED, CORRECTED, OTHER, REMOVED)
HORIZONS = (("6 months", "20270406"), ("12 months", "20271006"))
U = lambda L: L.upper()


def sha(s): return hashlib.sha256(s.encode("utf-8")).hexdigest()
def fsha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()
def third(L): return "it" if L == "fr" else "fr"
def count(t, L, v): return sum(1 for x in au.values(t, L) if x["v"] == v or x.get("alt") == v)
def phr_count(t, phrase): return au._phr(au.ttoks(t)).count(au._phr(phrase.split()))


def _neg(s, L):
    p = au._neg_profile(s, L); return sorted(set(p["S"] + p["T"]))


def _agree_neg(sd, sg, L): return au._neg_one_sided(au._neg_profile(sd, "de"), au._neg_profile(sg, L)) is None


def _vals(xs): return [x["value"] for x in xs or []]


def _u(xs): return next((x.get("unit") for x in xs or [] if x.get("unit")), None)


def _fmt(vs, unit=None): return ", ".join(vs) + (f" ({unit})" if unit and vs else "") if vs else "nothing"


# ------------------------------------------------------------------ build
def _labels():
    """fid -> dict(final, confirmed, source) for the 38 register findings (R14 majority) and the 31 round-5 ones (R15)."""
    A = json.load(open(AUDIT, encoding="utf-8")); F = A["findings"]
    rows = lambda p: (lambda ls: [dict(zip(ls[0].split("\t"), l.split("\t"))) for l in ls[1:] if l.strip()])(
        open(os.path.join(LABELS, p), encoding="utf-8").read().splitlines())
    M = {r["uid"]: r for r in rows("audit_relabel.tsv")}; out = {}
    for r in rows(f"audit_{DATE}.tsv"):
        out[f"N{int(r['rank']):02d}"] = f"audit_{DATE}:{r['id']}"
    for name in (f"audit2_{DATE}.tsv", f"audit3_terminology_{DATE}.tsv"):
        for r in rows(name):
            fs = [f["fid"] for f in F if f["kind"] == r["kind"] and f["id"] == r["cud"] and f["lang"] == r["lang"]]
            assert len(fs) == 1, (name, r["id"], fs)
            out[fs[0]] = f"{name[:-4]}:{r['id']}"
    assert sorted(out) == sorted(f["fid"] for f in F) and len(set(out.values())) == len(F)
    lab = {k: dict(final=M[u]["final"], confirmed=M[u]["final_confirmed"] == "yes", source=f"eval/labels/audit_relabel.tsv:{u}")
           for k, u in out.items()}
    for r in rows(f"audit_r15_{DATE}.tsv"):
        lab[r["fid"]] = dict(final=r["final"], confirmed=r["final"] in ("real", "minor"),
                             source=f"eval/labels/audit_r15_{DATE}.tsv:{r['id']}")
    assert len(lab) == len(F) + len(A["findings_r5"])
    return lab


def _excerpt(snip): return {k: "".join(s for s, _ in v) for k, v in (snip or {}).items()}


def _state_and_expect(f, T, D):
    """-> (state on 6 Oct 2026 per language, the predicted correction in words, the machine-readable expectation)."""
    k, L = f["kind"], f["lang"]; M = third(L) if L in ("fr", "it") else None
    agreeing = [x for x in LANGS if x != D] if D in LANGS else []
    if k in ("number", "number_word"):
        de, tg = _vals(f.get("de_only")), _vals(f.get("tgt_only")); vs = sorted(set(de + tg), key=lambda v: (au._num(v) or 0, v))
        state = {X: {v: count(T[X], X, v) for v in vs} for X in LANGS}
        cp = f.get("counterpart") or {}
        ud, ut = _u(f.get("de_only")), _u(f.get("tgt_only"))
        if D == L:
            now = tg or [x["value"] for x in cp.get(L, [])]
            txt = (f"{U(L)} changes {_fmt(now, ut)} to {_fmt(de, ud)}" if de and now else
                   f"{U(L)} comes to state {_fmt(de, ud)}" if de else f"{U(L)} drops {_fmt(tg, ut)}")
            txt += f", as DE and {U(M)} state"
        elif D == "de":
            now = de or [x["value"] for x in cp.get("de", [])]
            txt = (f"DE changes {_fmt(now, ud)} to {_fmt(tg, ut)}" if tg and now else
                   f"DE comes to state {_fmt(tg, ut)}" if tg else f"DE drops {_fmt(de, ud)}")
            txt += f", as FR and IT state"
        else:
            txt = (f"DE ({_fmt(de, ud)}) and {U(L)} ({_fmt(tg, ut)}) come to state the same value at this place; which "
                   f"side changes is not predicted")
        exp = dict(de_only=de, tgt_only=tg)
    elif k == "operator":
        v = f["value"]
        def dirs(X):
            return [[f"{x['op']} {v}", x["dir"]] for x in au.directions(T[X], X) if (x["v"] == v or x.get("alt") == v) and not x["neg"]]
        state = {X: dirs(X) for X in LANGS}
        W = {"min": "a lower bound", "max": "an upper bound"}
        if D == L:
            agreed = f["de_dir"]; txt = f"{U(L)} '{f['tgt_op']} {v}' becomes {W[agreed]} ('{f['de_op']} {v}'), as DE and {U(M)} state"
        elif D == "de":
            agreed = f["tgt_dir"]; txt = f"DE '{f['de_op']} {v}' becomes {W[agreed]} ('{f['tgt_op']} {v}'), as FR and IT state"
        else:
            agreed = None; txt = f"DE and {U(L)} come to state the same direction for {v}; which side changes is not predicted"
        exp = dict(value=v, agreed_dir=agreed, de_dir=f["de_dir"], tgt_dir=f["tgt_dir"])
    elif k == "negation":
        g = next(x for x in au.negation_diff(T["de"], T[L], L) if list(x["tgt_span"]) == list(f["tgt_span"]) and x["side"] == f["side"])
        sm = au.sentence_display(T, L, f["tgt_span"][0], (M,)).get(M, "")
        sent = {"de": g["de_sentence"], L: g["tgt_sentence"], M: sm}
        state = {X: dict(sentence=sent[X], negation=_neg(sent[X], X) if sent[X] else None) for X in LANGS}
        neg = ", ".join(f["negations"]); S = f["side"]
        if D == L:
            txt = (f"{U(L)} sentence gains the negation DE states ({neg}), as {U(M)} has" if S == "de" else
                   f"{U(L)} sentence drops its negation ({neg}), which DE and {U(M)} lack")
        elif D == "de":
            txt = (f"DE sentence drops its negation ({neg}), which FR and IT lack" if S == "de" else
                   f"DE sentence gains the negation {U(L)} states ({neg}), as {U(M)} has")
        else:
            txt = f"DE and {U(L)} come to agree on the negation of this sentence; which side changes is not predicted"
        exp = dict(side=S, negations=f["negations"], de_sentence=g["de_sentence"], tgt_sentence=g["tgt_sentence"])
    elif k == "editorial":
        X = L; st = au.load_stats()
        state = {Y: dict(surface=T[Y].count(f["surface"]), suggestion=T[Y].count(f["suggestion"])) for Y in LANGS}
        txt = f"{U(X)} '{f['surface']}' becomes '{f['suggestion']}'"
        assert any(e["rule"] == f["rule"] and e["surface"] == f["surface"] for e in au.editorial(T[X], X, st))
        exp = dict(rule=f["rule"], surface=f["surface"], suggestion=f["suggestion"])
    elif k == "language":
        st = au.load_stats(); W = {X: set(au.words(T[X])) for X in LANGS}
        det = lambda X: au.lang_check(T[X], X, set.intersection(*[W[Y] for Y in LANGS if Y != X]), st)["detected"]
        state = {X: dict(written_in=det(X)) for X in LANGS}
        txt = f"the {au.NAME[L]} field gets an {au.NAME[L]} text (now {au.NAME[f['detected']]})"
        exp = dict(detected=f["detected"])
    elif k == "terminology":
        state = {"de": dict(de_term=au.dstems(T["de"]).get(f["de_stem"], 0)),
                 L: dict(old=phr_count(T[L], f["old_phrase"]), new=phr_count(T[L], f["new_phrase"])),
                 M: dict(same_notice=bool(f.get("third_also")))}
        txt = f"{U(L)} '{f['old']}' becomes '{f['new']}', BAG's own replacement in {f['n_limitations']} other limitations"
        exp = dict(old_phrase=f["old_phrase"], new_phrase=f["new_phrase"], de_term=f["de_stem"])
    else:
        raise ValueError(k)
    return state, txt, dict(exp, divergent=D, agreeing=agreeing)


def build(hist):
    """hist: the snapshot dir with the 6 Oct 2026 files (for the list of limitation ids, and to verify the shipped texts)."""
    from gleichlaut.ui import audit_view as av
    A = json.load(open(AUDIT, encoding="utf-8")); TX = json.load(open(TEXTS, encoding="utf-8"))["texts"]
    J0, _ = au.load(hist, DATE)
    for i, t in TX.items():
        assert all(nrm(J0[X]["lim"][i]) == nrm(t[X]) for X in LANGS), i
    lab = _labels()
    V = av.data(hist=None); R, I = V["rows"], V["issues"]
    F = A.get("findings") or []
    row_of = {F[r["fi"]]["fid"]: r for r in R}
    iid_of = {F[R[ri]["fi"]]["fid"]: x["iid"] for x in I for ri in x["rows"]}
    assert len(I) == 18 and len(iid_of) == len(F) == 38
    # the round-5 findings as the register shows the confirmed ones (av.experimental), computed here for all 31
    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, "all.tsv")
        open(p, "w", encoding="utf-8").write("fid\tfinal\n" + "".join(f"{f['fid']}\treal\n" for f in A["findings_r5"]))
        X = av.experimental(A, DATE, labels=p)
    xrow = {r["fid"]: r for r in X["rows"]}
    xiid = {r["no"]: i["iid"] for i, r in zip((V["exp"] or {}).get("issues", []), (V["exp"] or {}).get("rows", []))}
    recs = []
    for setname, G in (("issues", F), ("experimental", A["findings_r5"])):
        for f in G:
            fid, i, L = f["fid"], f["id"], f["lang"]
            T = {Y: nrm(TX[i][Y]) for Y in LANGS}
            r = row_of[fid] if setname == "issues" else xrow[fid]
            D = r["odd"] if r["odd"] in LANGS else "unclear"
            if f["kind"] == "terminology": D = L
            lb = lab[fid]
            state, txt, exp = _state_and_expect(f, T, D)
            recs.append(dict(pid=fid, set=setname, issue=iid_of.get(fid) if setname == "issues" else xiid.get(fid),
                             limitation=i, product=f.get("product") or [], kind=f["kind"], lang=L, divergent=D,
                             prediction="BAG corrects it" if lb["confirmed"] else "no correction (not confirmed: negative prediction)",
                             confirmed=lb["confirmed"], blind_label=lb, likely_equivalent=bool(f.get("likely_equivalent")),
                             first_seen=f.get("first_seen"), description=f.get("description"),
                             state_20261006=state, correction=txt, expect=exp,
                             excerpt_20261006=_excerpt(r.get("snip")), texts_sha256={Y: sha(T[Y]) for Y in LANGS}))
    pos = [r for r in recs if r["confirmed"]]; neg = [r for r in recs if not r["confirmed"]]
    cnt = lambda rs: dict(n=len(rs), issues=sum(r["set"] == "issues" for r in rs), experimental=sum(r["set"] == "experimental" for r in rs))
    return dict(
        prereg="eval/prereg/PREREG.md R20", frozen_utc=FROZEN_UTC,
        register=f"BAG SL public FHIR feed of 06.10.2026 ({DATE}); texts: data/audit/audit_texts_{DATE}.json",
        audit="data/audit/audit_20261006.json (gleichlaut.audit; findings: the 18 issues of the review register, findings_r5: "
              "the round-5 checks, off by default)",
        labels="blind Claude annotators, majority of three (PREREG R14 for the issues, R15 for the round-5 findings); "
               "confirmed = real or minor",
        statuses=list(STATUSES), horizons={k: v for k, v in HORIZONS},
        follow="a limitation id absent from a later snapshot is followed to a new id (one not in limitation_ids_20261006) "
               "with the same product prefix whose German text is the most similar (difflib ratio >= 0.9)",
        counts=dict(predictions=len(recs), positive=cnt(pos), negative=cnt(neg),
                    issues=len(I), issue_findings=len(F), experimental_findings=len(A["findings_r5"]),
                    positive_by_kind=dict(sorted(Counter(r["kind"] for r in pos).items())),
                    negative_by_kind=dict(sorted(Counter(r["kind"] for r in neg).items())),
                    divergent=dict(sorted(Counter(r["divergent"] for r in recs).items()))),
        predictions=recs, limitation_ids_20261006=sorted(J0["de"]["lim"]))


def dump(obj): return json.dumps(obj, ensure_ascii=False, indent=1, sort_keys=False) + "\n"


# ------------------------------------------------------------------ check
def _still(p, T, st, pairs):
    """does the same check still report the finding on texts T? -> bool"""
    k, L, e = p["kind"], p["lang"], p["expect"]
    if k == "number":
        r = au.compare(T["de"], T[L], L)
        return bool(set(e["de_only"]) & set(_vals(r["de_only"])) or set(e["tgt_only"]) & set(_vals(r["tgt_only"])))
    if k == "number_word":
        r = au.compare(T["de"], T[L], L); nf = dict(de_only=r["de_only"], tgt_only=r["tgt_only"]) if (r["de_only"] or r["tgt_only"]) else None
        G = au.r5_findings(p["limitation"], T["de"], T[L], L, nf, kinds=("number_word",))
        return any(set(e["de_only"]) & set(_vals(g["de_only"])) or set(e["tgt_only"]) & set(_vals(g["tgt_only"])) for g in G)
    if k == "operator":
        return any(o["value"] == e["value"] for o in au.operator_diff(T["de"], T[L], L))
    if k == "negation":
        return any(g["side"] == e["side"] and (g["de_sentence"] == e["de_sentence"] or g["tgt_sentence"] == e["tgt_sentence"])
                   for g in au.negation_diff(T["de"], T[L], L))
    if k == "editorial":
        return any(x["rule"] == e["rule"] and x["surface"] == e["surface"] for x in au.editorial(T[L], L, st))
    if k == "language":
        W = {X: set(au.words(T[X])) for X in LANGS}
        return au.lang_check(T[L], L, set.intersection(*[W[Y] for Y in LANGS if Y != L]), st)["detected"] != L
    if k == "terminology":
        P = [q for q in pairs if q["lang"] == L and q["old_phrase"] == e["old_phrase"] and q["new_phrase"] == e["new_phrase"]]
        return bool(au.term_check(T["de"], T[L], L, P))
    raise ValueError(k)


def _agreement(p, T, old):
    """does the divergent language now state what the other two state at that place? -> (bool, reason)"""
    k, L, e, D = p["kind"], p["lang"], p["expect"], p["divergent"]
    if k in ("number", "number_word"):
        S = p["state_20261006"]; why = ""
        for X in ([D] if D in LANGS else ["de", L]):                 # unclear: either side may be the one that changes
            O = L if X == "de" else "de"                              # the side whose values the divergent one adopts
            gain, lose = (e["tgt_only"], e["de_only"]) if X == "de" else (e["de_only"], e["tgt_only"])
            bad = ([f"{U(X)} does not state {v} more often than on 6 Oct" for v in gain if count(T[X], X, v) <= S[X][v]] +
                   [f"{U(X)} does not state {v} less often than on 6 Oct" for v in lose if count(T[X], X, v) >= S[X][v]] +
                   [f"{U(O)} no longer states {v}" for v in gain if count(T[O], O, v) == 0])
            if not bad: return True, f"{U(X)} now states the value {U(O)} states"
            why = why or bad[0]
        return False, why
    if k == "operator":
        dirs = lambda X: {x["dir"] for x in au.directions(T[X], X) if (x["v"] == e["value"] or x.get("alt") == e["value"]) and not x["neg"]}
        if e["agreed_dir"] is None:
            ok = bool(dirs("de") & dirs(L))
            return ok, "DE and the target state the value with the same direction" if ok else "no common direction"
        ok = any((x["v"] == e["value"] or x.get("alt") == e["value"]) and not x["neg"] and x["dir"] == e["agreed_dir"]
                 for x in au.directions(T[D], D))
        return ok, "the divergent language states the agreed direction" if ok else "no bound of the agreed direction"
    if k == "negation":
        P = [(T["de"][d[0]:d[1]], T[L][g[0]:g[1]]) for d, g, c in au.align(T["de"], T[L], L)[0]]
        a = [_agree_neg(sd, sg, L) for sd, sg in P if sd == e["de_sentence"]]           # German kept, target edited
        b = [_agree_neg(sd, sg, L) for sd, sg in P if sg == e["tgt_sentence"]]          # target kept, German edited
        ok = any(a) if D == L else any(b) if D == "de" else any(a) or any(b)
        return ok, "the aligned sentences now agree on the negation" if ok else "no aligned pair that agrees on the negation"
    if k == "editorial":
        ok = T[L].count(e["surface"]) < old[L].count(e["surface"]) and T[L].count(e["suggestion"]) > old[L].count(e["suggestion"])
        return ok, "the typo is replaced by its correction" if ok else "the correction is not written"
    if k == "language": return True, f"the {au.NAME[L]} field is in {au.NAME[L]}"
    if k == "terminology":
        o = p["state_20261006"][L]
        ok = phr_count(T[L], e["new_phrase"]) > o["new"] and phr_count(T[L], e["old_phrase"]) < o["old"]
        return ok, "the new term replaces the old one" if ok else "the new term does not replace the old one"
    raise ValueError(k)


def _prefix(i): return re.match(r"[A-Za-z0-9]*", i).group(0).upper()


def follow(i, J, ids0, old_de):
    """the id of the limitation in snapshot J: i itself, else a new id (not in ids0) with the same product prefix and the
    most similar German text (ratio >= 0.9; a tie: None), else None."""
    if i in J["de"]["lim"]: return i
    if not old_de: return None
    C = sorted(((difflib.SequenceMatcher(None, old_de, nrm(J["de"]["lim"][k] or ""), autojunk=False).ratio(), k)
                for k in J["de"]["lim"] if k not in ids0 and _prefix(k) == _prefix(i)), reverse=True)
    if not C or C[0][0] < 0.9 or (len(C) > 1 and C[1][0] == C[0][0]): return None
    return C[0][1]


def check_one(p, J, st, pairs, old=None, ids0=()):
    i0, L, D = p["limitation"], p["lang"], p["divergent"]
    i = follow(i0, J, set(ids0), (old or {}).get("de")) or i0
    need = {"de", L} | ({D} if D in LANGS else set())
    if any(i not in (J[X].get("lim") or {}) or not J[X]["lim"][i] for X in need):
        return dict(pid=p["pid"], status=REMOVED, missing=sorted(X for X in need if i not in J[X]["lim"] or not J[X]["lim"][i]))
    T = {X: nrm(J[X]["lim"].get(i) or "") for X in LANGS}
    changed = [X for X in LANGS if sha(T[X]) != p["texts_sha256"][X]]
    still = _still(p, T, st, pairs)
    out = dict(pid=p["pid"], changed=changed, still_reported=still)
    if i != i0: out["followed_to"] = i
    if not changed: return dict(out, status=UNCHANGED)
    dchg = (D in changed) if D in LANGS else bool({"de", L} & set(changed))
    out["divergent_changed"] = dchg
    if still or not dchg:
        return dict(out, status=OTHER, reason="the finding is still reported" if still else "the divergent language is unchanged")
    ok, why = _agreement(p, T, old or {})
    return dict(out, status=CORRECTED if ok else OTHER, reason=why)


def check(hist, date, P=None):
    P = P or json.load(open(PRED, encoding="utf-8"))
    J, _ = au.load(hist, date)
    st = au.load_stats(); pairs = au.load_terms()
    TX = json.load(open(TEXTS, encoding="utf-8"))["texts"]
    res = []
    for p in P["predictions"]:
        old = {X: nrm(TX[p["limitation"]][X]) for X in LANGS} if p["limitation"] in TX else {}
        res.append(check_one(p, J, st, pairs, old, P.get("limitation_ids_20261006") or ()))
    by = {r["pid"]: r for r in res}
    def tab(rs): return {s: sum(1 for r in rs if by[r["pid"]]["status"] == s) for s in STATUSES}
    pos = [p for p in P["predictions"] if p["confirmed"]]; neg = [p for p in P["predictions"] if not p["confirmed"]]
    role = "self-test (the register's own snapshot)" if date == DATE else \
        "sanity check (a snapshot before the register; changes run backwards in time)" if date < DATE else "scoring"
    return dict(date=date, role=role, generated_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
                predictions_sha256=fsha(PRED), checker_sha256=fsha(os.path.abspath(__file__)),
                audit_sha256=fsha(os.path.join(ROOT, "src", "gleichlaut", "audit.py")),
                snapshot=dict(files=[f"{date}-{X}.json" for X in LANGS], n_limitations=len(J["de"]["lim"])),
                summary=dict(positive=dict(n=len(pos), **tab(pos)), negative=dict(n=len(neg), **tab(neg)),
                             still_reported=sum(1 for r in res if r.get("still_reported")),
                             by_set={s: dict(n=len([p for p in G if p["set"] == s]), **tab([p for p in G if p["set"] == s]))
                                     for G, s in ((P["predictions"], "issues"), (P["predictions"], "experimental"))}),
                results=res)


def fetch(date, hd):
    from gleichlaut.sl import feeds, ingest
    if date == "latest":
        date, how = feeds.resolve_latest(hd); print(f"latest = {date} ({how})", file=sys.stderr)
    for X in LANGS:
        if not os.path.exists(os.path.join(hd, f"{date}-{X}.json")): ingest.fetch(date, X, hd)
    return date


# ------------------------------------------------------------------ backtest (a sanity check of the checker on history)
def backtest(hist, d0, later):
    """The same audit (all kinds, round 5 included) on an earlier snapshot d0, each finding made a prediction exactly as
    in build (divergent language from the third language as the register computes it; no labels: confirmed is None),
    and checked on each later snapshot: how often did BAG change or correct a text the audit flags?"""
    J0, names = au.load(hist, d0); ids0 = sorted(J0["de"]["lim"])
    F, _, _ = au.run_all(hist, d0, J0, names, r5=True)
    st = au.load_stats(); pairs = au.load_terms(); P = []
    for f in F:
        i, L = f["id"], f["lang"]
        T = {X: nrm(J0[X]["lim"].get(i) or "") for X in LANGS}
        if not all(T.values()): continue
        D = L if f["kind"] in ("terminology", "language") else f.get("odd_one_out")
        if f["kind"] == "operator": D = (au.operator_display(f, T) or {}).get("odd")
        if f["kind"] == "negation":
            D = au.negation_odd(T, f, au.sentence_display(T, L, f["tgt_span"][0], ("de", L, third(L))))
        D = D if D in LANGS else "unclear"
        state, txt, exp = _state_and_expect(f, T, D)
        P.append((dict(pid=f["fid"], kind=f["kind"], lang=L, limitation=i, divergent=D, state_20261006=state, expect=exp,
                       correction=txt, texts_sha256={X: sha(T[X]) for X in LANGS}), T))
    out = dict(date=d0, findings=len(P), by_kind=dict(sorted(Counter(p["kind"] for p, _ in P).items())), later={})
    for d in later:
        J, _ = au.load(hist, d)
        R = [dict(check_one(p, J, st, pairs, T, ids0), kind=p["kind"], limitation=p["limitation"], correction=p["correction"])
             for p, T in P]
        out["later"][d] = dict(counts={s: sum(r["status"] == s for r in R) for s in STATUSES},
                               followed=sum(1 for r in R if r.get("followed_to")),
                               not_unchanged=[r for r in R if r["status"] != UNCHANGED])
    return out


# ------------------------------------------------------------------ score (after a scoring date)
def wilson(k, n, z=1.96):
    if not n: return [None, None]
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(100 * (c - h), 1), round(100 * (c + h), 1)]


def fisher_greater(a, n1, b, n2):
    """one-sided Fisher exact p for 'share a/n1 > share b/n2' (hypergeometric upper tail)."""
    K, N = a + b, n1 + n2
    tot = math.comb(N, K)
    return sum(math.comb(n1, x) * math.comb(n2, K - x) for x in range(a, min(n1, K) + 1)) / tot


def score(files=None, today=None):
    P = json.load(open(PRED, encoding="utf-8")); ps = P["predictions"]
    C = sorted((json.load(open(f, encoding="utf-8")) for f in (files or glob.glob(os.path.join(OUTD, "check_*.json")))),
               key=lambda c: c["date"])
    C = [c for c in C if c["date"] > DATE and c.get("predictions_sha256") == fsha(PRED)]
    today = today or datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d")
    out = dict(prereg="PREREG R20", predictions_sha256=fsha(PRED), scoring_snapshots=[c["date"] for c in C], horizons={})
    for name, end in HORIZONS:
        S = [c for c in C if c["date"] <= end]
        st = {p["pid"]: [next(r for r in c["results"] if r["pid"] == p["pid"])["status"] for c in S] for p in ps}
        ever = lambda pid, s: s in st[pid]
        pos = [p["pid"] for p in ps if p["confirmed"]]; neg = [p["pid"] for p in ps if not p["confirmed"]]
        k_pos = sum(ever(x, CORRECTED) for x in pos)
        k_neg_change = sum(any(s in (CORRECTED, OTHER) for s in st[x]) for x in neg)
        k_neg_corr = sum(ever(x, CORRECTED) for x in neg)
        h = dict(end=end, passed=today > end, snapshots=[c["date"] for c in S],
                 positive=dict(n=len(pos), corrected=k_pos, pct=round(100 * k_pos / len(pos), 1), wilson95=wilson(k_pos, len(pos)),
                               changed=sum(any(s in (CORRECTED, OTHER) for s in st[x]) for x in pos),
                               removed=sum(ever(x, REMOVED) for x in pos)),
                 negative=dict(n=len(neg), changed=k_neg_change, pct_changed=round(100 * k_neg_change / len(neg), 1),
                               wilson95=wilson(k_neg_change, len(neg)), corrected=k_neg_corr, removed=sum(ever(x, REMOVED) for x in neg)),
                 fisher_one_sided_p=round(fisher_greater(k_pos, len(pos), k_neg_change, len(neg)), 4) if S else None)
        h["outcome"] = ("pending (no scoring snapshot yet)" if not S else "pending (horizon not passed)" if not h["passed"] else
                        "supported" if k_pos / len(pos) > k_neg_change / len(neg) and h["fisher_one_sided_p"] < 0.05 else "not supported")
        out["horizons"][name] = h
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(prog="check_predictions", description=__doc__.split("\n\n")[0])
    sp = ap.add_subparsers(dest="cmd", required=True)
    b = sp.add_parser("build"); b.add_argument("--check", action="store_true"); b.add_argument("--out", default=PRED)
    b.add_argument("--hist", help="snapshot dir with the 20261006 files (default $GLEICHLAUT_HIST or out/hist)")
    t = sp.add_parser("backtest"); t.add_argument("--hist", required=True); t.add_argument("--from", dest="d0", required=True)
    t.add_argument("--to", nargs="+", required=True); t.add_argument("--out")
    c = sp.add_parser("check"); c.add_argument("--hist"); c.add_argument("--date"); c.add_argument("--fetch")
    c.add_argument("--snapshots", help="snapshot dir for --fetch (default $GLEICHLAUT_HIST or out/hist)"); c.add_argument("--out")
    s = sp.add_parser("score"); s.add_argument("--out", default=os.path.join(OUTD, "score.json"))
    a = ap.parse_args(argv)
    if a.cmd == "build":
        from gleichlaut.sl import hist_dir
        txt = dump(build(hist_dir(a.hist)))
        if a.check:
            same = os.path.exists(a.out) and open(a.out, encoding="utf-8").read() == txt
            print("predictions:", "identical" if same else "DIFFER", a.out); return 0 if same else 1
        os.makedirs(os.path.dirname(a.out), exist_ok=True); open(a.out, "w", encoding="utf-8").write(txt)
        print("wrote", os.path.relpath(a.out, ROOT), "sha256", fsha(a.out)); return 0
    if a.cmd == "check":
        if a.fetch:
            from gleichlaut.sl import hist_dir
            hd = hist_dir(a.snapshots); date = fetch(a.fetch, hd)
        elif a.hist and a.date: hd, date = a.hist, a.date
        else: ap.error("check needs --hist DIR --date D, or --fetch D|latest")
        R = check(hd, date); out = a.out or os.path.join(OUTD, f"check_{date}.json")
        open(out, "w", encoding="utf-8").write(dump(R))
        print(f"{date} ({R['role']}): positive {R['summary']['positive']}, negative {R['summary']['negative']} -> {os.path.relpath(out, ROOT)}")
        return 0
    if a.cmd == "backtest":
        R = backtest(a.hist, a.d0, a.to); out = a.out or os.path.join(OUTD, f"backtest_{a.d0}.json")
        open(out, "w", encoding="utf-8").write(dump(R))
        for d, x in R["later"].items(): print(f"{a.d0} ({R['findings']} findings) -> {d}: {x['counts']}, followed {x['followed']}")
        return 0
    R = score(); open(a.out, "w", encoding="utf-8").write(dump(R))
    for k, h in R["horizons"].items(): print(k, h["outcome"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
