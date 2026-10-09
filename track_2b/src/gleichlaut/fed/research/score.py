"""Score arms A/B + code lane against the official new target text. stdlib only.
usage: python3 -I score.py  (reads items.json, results/A.jsonl, results/B.jsonl) -> results/scores.json + stdout tables"""
import json, os, sys, difflib, re
from collections import Counter, defaultdict
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
import lock
from lock import tok, norm

items = json.load(open(f"{H}/items.json"))
EXCL = set(json.load(open(f"{H}/pools/excluded_keys.json"))) if os.path.exists(f"{H}/pools/excluded_keys.json") else set()


def jl(p):
    return {json.loads(l)["key"]: json.loads(l) for l in open(p)} if os.path.exists(p) else {}


CONTAM = {}
if os.path.exists(f"{H}/results/s2_contamination.json"):
    for c in json.load(open(f"{H}/results/s2_contamination.json")):
        if c["n_novel"] > 0: CONTAM[c["key"]] = "contam" if c["c_novel"] >= 0.5 else "clean"
        elif c["n_new"] > 0: CONTAM[c["key"]] = "contam" if c["c_new"] >= 0.5 else "clean"
        else: CONTAM[c["key"]] = "short"
A, B = jl(f"{H}/results/A.jsonl"), jl(f"{H}/results/B.jsonl")


def edits(src, dst):
    t, o = tok(src), tok(dst)
    E = Counter()
    for op, j1, j2, k1, k2 in difflib.SequenceMatcher(None, t, o, autojunk=False).get_opcodes():
        if op in ("delete", "replace"):
            for j in range(j1, j2): E[("D", j, t[j])] += 1
        if op in ("insert", "replace"):
            for k in range(k1, k2): E[("I", j1, o[k])] += 1
    return E


def f1(pred, gold):
    if not pred and not gold: return 1.0
    tp = sum((pred & gold).values()); p = tp / max(1, sum(pred.values())); r = tp / max(1, sum(gold.values()))
    return 0.0 if tp == 0 else 2 * p * r / (p + r)


def chrf(hyp, ref, n=6, beta=2):
    h, r = hyp.replace(" ", ""), ref.replace(" ", "")
    P, R = [], []
    for k in range(1, n + 1):
        hc = Counter(h[i:i + k] for i in range(len(h) - k + 1)); rc = Counter(r[i:i + k] for i in range(len(r) - k + 1))
        if not hc or not rc: continue
        m = sum((hc & rc).values()); P.append(m / sum(hc.values())); R.append(m / sum(rc.values()))
    if not P: return 0.0
    p, rr = sum(P) / len(P), sum(R) / len(R)
    return 0.0 if p + rr == 0 else 100 * (1 + beta ** 2) * p * rr / (beta ** 2 * p + rr)


def is_cluster(x):
    """SEFRI general-education ordinance mass amendment (27 April 2006 -> 9 April 2025) repeated across vocational ordinances."""
    a, b, ops = lock.de_ops(x["de_old"], x["de_new"])
    sig = [(" ".join(a[i1:i2]), " ".join(b[j1:j2])) for o, i1, i2, j1, j2 in ops]
    return ("27", "9") in sig and ("2006", "2025") in sig


def flip(out, gold, lang):
    return lock.slot_diff(lock.slots(gold, lang), lock.slots(out, lang))


def score_one(x, out, arm, rec=None):
    gold = x["tgt_new"]
    strict = re.sub(r"\s+", " ", out).strip() == re.sub(r"\s+", " ", gold).strip()
    out, gold, told = norm(out), norm(gold), norm(x["tgt_old"])
    d = dict(key=x["key"], lang=x["lang"], src=x["src"], arm=arm, out=out, exact_strict=strict,
             cluster=is_cluster(x),
             exact=out == gold,
             ef1=f1(edits(told, out), edits(told, gold)),
             chrf=chrf(norm(out), norm(gold)))
    c = lock.check(x["de_old"], x["de_new"], told, out)
    d["outside_chars"] = c["outside_chars"]
    d["flip"] = flip(out, gold, x["lang"])
    d["guard"] = lock.guard(x["de_old"], x["de_new"], told, out, x["lang"])
    if arm in ("A", "A+code", "A-asrun"):
        d["flag_lock"] = rec["flagged_lock"]; d["retried"] = rec["retried"]; d["secs"] = rec["secs"]
        d["flagged"] = d["flag_lock"] or bool(d["guard"])
    elif arm == "B":
        d["secs"] = rec["secs"]; d["flagged"] = False
    return d


def restore_apos(tgt_old, out):
    """deterministic: the 8B emits ' for the typographic apostrophe; restore ’ when the old target text uses only ’."""
    return out.replace("'", "’") if ("’" in tgt_old and "'" not in tgt_old) else out


def corrected(x, rec):
    """Replays the recorded run with the lock computed on apostrophe-normalised text (the as-run lock counted ’->' as an
    out-of-span edit). out1 passes -> keep out1, no retry. out1 fails -> the recorded retry (out2) is what the pipeline would have produced."""
    r = dict(rec)
    c1 = lock.check(x["de_old"], x["de_new"], norm(x["tgt_old"]), norm(rec["out1"]))
    if c1["ok"]:
        r.update(out=rec["out1"], retried=False, flagged_lock=False, secs=rec["secs1"])
    else:
        assert rec["retried"]
        c2 = lock.check(x["de_old"], x["de_new"], norm(x["tgt_old"]), norm(rec["out2"]))
        r.update(out=rec["out2"], retried=True, flagged_lock=not c2["ok"], secs=rec["secs1"] + rec["secs2"], retry_fixed=c2["ok"])
    r["out"] = restore_apos(x["tgt_old"], r["out"])
    return r


def main():
    rows = []
    code = []
    for x in items:
        if x["key"] in EXCL or x["src"] == "s3": continue
        if x["key"] in A:
            rows.append(score_one(x, A[x["key"]]["out"], "A-asrun", A[x["key"]]))
            A[x["key"]] = corrected(x, A[x["key"]])
            rows.append(score_one(x, A[x["key"]]["out"], "A", A[x["key"]]))
        if x["key"] in B: rows.append(score_one(x, B[x["key"]]["out"], "B", B[x["key"]]))
        app, out = lock.code_lane(x["de_old"], x["de_new"], x["tgt_old"], x["lang"])
        code.append(dict(key=x["key"], lang=x["lang"], applicable=app, produced=out is not None,
                         exact=out is not None and norm(out) == norm(x["tgt_new"]), out=out))
        if x["key"] in A:  # combined: code lane where it produced output, else arm A
            r = score_one(x, out if out is not None else A[x["key"]]["out"], "A+code", A[x["key"]])
            if out is not None: r.update(flagged=bool(r["guard"]), flag_lock=False, secs=0.0, retried=False)
            rows.append(r)
    # gold sanity: does the official edit fit inside the lock windows?
    gold_fit = defaultdict(list)
    for x in items:
        if x["key"] in EXCL or x["src"] == "s3": continue
        gold_fit[x["lang"]].append(lock.check(x["de_old"], x["de_new"], x["tgt_old"], x["tgt_new"])["ok"])
    T = defaultdict(lambda: defaultdict(list))
    for r in rows:
        gs = [r["lang"], "fr+it" if r["lang"] in ("fr", "it") else None]
        if r["lang"] in ("fr", "it") and not r["cluster"]: gs.append("fr+it-noSEFRI")
        if r["lang"] == "rm": gs.append("rm-" + CONTAM.get(r["key"], "unk"))
        for g in gs:
            if g: T[(g, r["arm"])]["rows"].append(r)
    out = {}
    print(f"{'group':14s} {'arm':7s} {'n':>3s} {'exact':>6s} {'strict':>6s} {'editF1':>6s} {'chrF':>5s} {'out0%':>5s} {'outCh':>6s} {'flag%':>5s} {'flip%':>5s} {'unflFlip%':>9s} {'exact|unfl':>10s} {'s/par':>6s}")
    for (g, arm), v in sorted(T.items()):
        R = v["rows"]; n = len(R)
        unfl = [r for r in R if not r["flagged"]]
        s = dict(n=n, exact=sum(r["exact"] for r in R) / n, exact_strict=sum(r["exact_strict"] for r in R) / n, edit_f1=100 * sum(r["ef1"] for r in R) / n, chrf=sum(r["chrf"] for r in R) / n,
                 zero_outside=sum(r["outside_chars"] == 0 for r in R) / n, outside_chars_mean=sum(r["outside_chars"] for r in R) / n,
                 flagged=sum(r["flagged"] for r in R) / n, flips=sum(bool(r["flip"]) for r in R) / n,
                 unflagged_flips=sum(bool(r["flip"]) and not r["flagged"] for r in R) / n,
                 exact_unflagged=(sum(r["exact"] for r in unfl) / len(unfl)) if unfl else None, n_unflagged=len(unfl),
                 secs=sum(r.get("secs", 0) for r in R) / n)
        out[f"{g}|{arm}"] = s
        eu = f"{s['exact_unflagged']:.0%}" if s["exact_unflagged"] is not None else "-"
        print(f"{g:14s} {arm:7s} {n:3d} {s['exact']:6.0%} {s['exact_strict']:6.0%} {s['edit_f1']:6.1f} {s['chrf']:5.1f} {s['zero_outside']:5.0%} {s['outside_chars_mean']:6.1f} {s['flagged']:5.0%} {s['flips']:5.0%} {s['unflagged_flips']:9.0%} {eu:>10s} {s['secs']:6.1f}")
    cl = defaultdict(Counter)
    for c in code:
        cl[c["lang"]]["n"] += 1; cl[c["lang"]]["applicable"] += c["applicable"]; cl[c["lang"]]["produced"] += c["produced"]; cl[c["lang"]]["exact"] += c["exact"]
    print("code lane:", {k: dict(v) for k, v in cl.items()})
    print("gold edit inside lock windows:", {k: f"{sum(v)}/{len(v)}" for k, v in gold_fit.items()})
    json.dump(dict(summary=out, code_lane={k: dict(v) for k, v in cl.items()}, gold_fit={k: [sum(v), len(v)] for k, v in gold_fit.items()},
                   rows=rows, code=code), open(f"{H}/results/scores.json", "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
