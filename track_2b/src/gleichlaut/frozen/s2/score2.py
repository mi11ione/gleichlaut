"""Score Gleichlaut S2 arms against the official new FR/IT text. stdlib only.
usage: python3 -I score2.py  (reads items.json, items_all.json, results/arm2.jsonl, results/arm3.jsonl)
-> results/scores.json, results/review.tsv (every lexicon flip + flagged item + a seeded sample, for hand adjudication)"""
import json, os, sys, re, difflib, random
from collections import Counter, defaultdict
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
import gl2, lock
from lock import tok, norm
R = f"{H}/results"
items = json.load(open(f"{H}/items.json")); ALL = json.load(open(f"{H}/items_all.json"))


def jl(p):
    return {json.loads(l)["key"]: json.loads(l) for l in open(p)} if os.path.exists(p) else {}


def edits(src, dst):
    t, o = tok(src), tok(dst); E = Counter()
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
    h, r = hyp.replace(" ", ""), ref.replace(" ", ""); P, Rr = [], []
    for k in range(1, n + 1):
        hc = Counter(h[i:i + k] for i in range(len(h) - k + 1)); rc = Counter(r[i:i + k] for i in range(len(r) - k + 1))
        if not hc or not rc: continue
        m = sum((hc & rc).values()); P.append(m / sum(hc.values())); Rr.append(m / sum(rc.values()))
    if not P: return 0.0
    p, rr = sum(P) / len(P), sum(Rr) / len(Rr)
    return 0.0 if p + rr == 0 else 100 * (1 + beta ** 2) * p * rr / (beta ** 2 * p + rr)


def score_one(x, out, arm, rec=None):
    gold, told = norm(x["tgt_new"]), norm(x["tgt_old"]); o = norm(out)
    d = dict(key=x["key"], pair=x.get("pair"), lang=x["lang"], arm=arm, out=out,
             exact=o == gold, strict=re.sub(r"\s+", " ", out).strip() == re.sub(r"\s+", " ", x["tgt_new"]).strip(),
             ef1=f1(edits(told, o), edits(told, gold)), chrf=chrf(o, gold))
    d["lock_ok"] = lock.check(x["de_old"], x["de_new"], told, o)["ok"]
    d["flip"] = lock.slot_diff(lock.slots(gold, x["lang"]), lock.slots(o, x["lang"]))
    d["guard"] = lock.guard(x["de_old"], x["de_new"], told, o, x["lang"])
    n, vals = gl2.numbers_not_in_de(o, x["de_new"], x["lang"]); d["nums_not_in_de"] = n; d["nums_not_in_de_vals"] = vals
    tv = gl2.numbers_in(told, x["lang"]); dv = gl2.numbers_in(x["de_new"], "de")
    d["nums_invented"] = sorted(v for v in gl2.numbers_in(o, x["lang"]) if v not in tv and v not in dv)
    if arm == "2":
        d["rule_only"] = rec["rule_only"]; d["secs"] = rec["secs"]
        d["unknown_slots"] = sum(len(w["unknown_slots"]) for w in rec["windows"])
        d["model_chars"] = sum(len(w["out"]) for w in rec["windows"])
        d["flagged"] = bool(d["guard"]) or not d["lock_ok"] or d["unknown_slots"] > 0
    elif arm == "2b":
        d["rule_only"] = rec["rule_only"]; d["secs"] = rec["secs"]; d["retried"] = rec["retried"]
        d["unknown_slots"] = rec.get("unknown_slots", 0)
        d["flagged"] = rec.get("flagged_lock", False) or bool(d["guard"]) or d["unknown_slots"] > 0
    elif arm == "1":
        d["flagged"] = bool(d["guard"]); d["rule_only"] = None
    else:
        d["secs"] = rec["secs"] if rec else 0; d["flagged"] = False
    return d


def boot_diff(rows_a, rows_b, field, n=4000, seed=7):
    """paired cluster bootstrap over DE pairs (FR and IT of one pair resampled together): 95% CI of mean(a)-mean(b), in points."""
    by = defaultdict(list)
    for a, b in zip(rows_a, rows_b): by[a["pair"]].append(float(a[field]) - float(b[field]))
    ks = list(by); rng = random.Random(seed); ds = []
    for _ in range(n):
        s = [rng.choice(ks) for _ in ks]; v = [d for k in s for d in by[k]]; ds.append(100 * sum(v) / len(v))
    ds.sort(); return ds[int(0.025 * n)], ds[int(0.975 * n)]


def main():
    A2, A3, A2B = jl(f"{R}/arm2.jsonl"), jl(f"{R}/arm3.jsonl"), jl(f"{R}/arm2b.jsonl")
    rows = []
    for x in items:
        r1, _ = gl2.rules(x["de_old"], x["de_new"], x["tgt_old"], x["lang"]); rows.append(score_one(x, r1, "1"))
        if x["key"] in A2: rows.append(score_one(x, A2[x["key"]]["out"], "2", A2[x["key"]]))
        if x["key"] in A3: rows.append(score_one(x, A3[x["key"]]["out"], "3", A3[x["key"]]))
        if x["key"] in A2B:
            o = A2B[x["key"]]["out"]
            o = o.replace("'", "’") if ("’" in x["tgt_old"] and "'" not in x["tgt_old"]) else o  # Gleichschritt restore_apos (strict only)
            rows.append(score_one(x, o, "2b", A2B[x["key"]]))
        rows.append(score_one(x, x["tgt_new"], "gold"))
    T = defaultdict(list)
    model_items = {r["key"] for r in rows if r["arm"] == "2" and not r["rule_only"]}
    for r in rows:
        for g in (r["lang"], "fr+it"):
            T[(g, r["arm"])].append(r)
            if r["key"] in model_items: T[(g + "|model-touched", r["arm"])].append(r)
    S = {}
    hdr = f"{'group':22s} {'arm':4s} {'n':>3s} {'exact':>6s} {'strict':>6s} {'editF1':>6s} {'chrF':>5s} {'lockOK':>6s} {'flag%':>5s} {'flipHit':>7s} {'unflFlipHit':>11s} {'numNotDE':>8s} {'itemsNumNotDE':>13s} {'invented':>8s} {'s/item':>6s}"
    print(hdr)
    for (g, arm), R_ in sorted(T.items()):
        n = len(R_)
        s = dict(n=n, exact=sum(r["exact"] for r in R_) / n, strict=sum(r["strict"] for r in R_) / n, edit_f1=100 * sum(r["ef1"] for r in R_) / n,
                 chrf=sum(r["chrf"] for r in R_) / n, lock_ok=sum(r["lock_ok"] for r in R_) / n,
                 flagged=sum(r.get("flagged", False) for r in R_) / n, flip_hits=sum(bool(r["flip"]) for r in R_),
                 unflagged_flip_hits=sum(bool(r["flip"]) and not r.get("flagged", False) for r in R_),
                 nums_not_in_de=sum(r["nums_not_in_de"] for r in R_), items_nums_not_in_de=sum(r["nums_not_in_de"] > 0 for r in R_),
                 invented=sum(bool(r["nums_invented"]) for r in R_), secs=sum(r.get("secs", 0) for r in R_) / n)
        S[f"{g}|{arm}"] = s
        print(f"{g:22s} {arm:4s} {n:3d} {s['exact']:6.1%} {s['strict']:6.1%} {s['edit_f1']:6.1f} {s['chrf']:5.1f} {s['lock_ok']:6.0%} {s['flagged']:5.0%} {s['flip_hits']:7d} {s['unflagged_flip_hits']:11d} {s['nums_not_in_de']:8d} {s['items_nums_not_in_de']:13d} {s['invented']:8d} {s['secs']:6.1f}")
    # kill-rule deltas with paired cluster bootstrap
    K = {}
    for arm2, g in [(a, g) for a in ("2", "2b") for g in ("fr+it", "fr", "it", "fr+it|model-touched")]:
        a1 = {r["key"]: r for r in T[(g, "1")]}; a2 = {r["key"]: r for r in T[(g, arm2)]}
        ks = [k for k in a2 if k in a1]
        if not ks: continue
        ra, rb = [a2[k] for k in ks], [a1[k] for k in ks]
        for f in ("exact", "ef1", "chrf"):
            sc = 1 if f == "chrf" else 100
            d = sc * (sum(float(r[f]) for r in ra) - sum(float(r[f]) for r in rb)) / len(ks)
            ci = boot_diff(ra, rb, f); ci = (ci[0] / 100, ci[1] / 100) if f == "chrf" else ci
            K[f"{arm2}|{g}|{f}"] = dict(n=len(ks), delta=d, ci95=ci)
            print(f"arm{arm2} - arm1 {g:22s} {f:5s} n={len(ks)} delta {d:+.1f} pts  95% CI [{ci[0]:+.1f}, {ci[1]:+.1f}]")
    # rules arm + gold ceiling on the full eligible pool
    P = Counter()
    for x in ALL:
        r1, _ = gl2.rules(x["de_old"], x["de_new"], x["tgt_old"], x["lang"])
        P["n"] += 1; P["rules_exact"] += norm(r1) == norm(x["tgt_new"]); P["gold_lock_ok"] += lock.check(x["de_old"], x["de_new"], x["tgt_old"], x["tgt_new"])["ok"]
    print("full eligible pool (both langs):", dict(P))
    # review sheet: every lexicon flip hit, every flagged arm-2 item, plus a seeded sample of 20 unflagged arm-2 items
    rv = [r for r in rows if r["arm"] in ("2", "2b", "3") and (r["flip"] or r.get("flagged"))] + [r for r in rows if r["arm"] == "2b" and not r.get("flagged") and not r["exact"]]
    rng = random.Random(20261009); pool = [r for r in rows if r["arm"] == "2" and not r["flip"] and not r.get("flagged") and not r["exact"]]
    rv += rng.sample(pool, min(20, len(pool)))
    IX = {x["key"]: x for x in items}
    with open(f"{R}/review.tsv", "w") as f:
        f.write("key\tarm\tflagged\tguard\tflip\texact\tde_ops\ttgt_gold_ops\tout_ops\n")
        for r in rv:
            x = IX[r["key"]]
            a, b, ops = lock.de_ops(x["de_old"], x["de_new"])
            def opstr(s, t):
                ta, tb = tok(s), tok(t)
                return " | ".join(f"{o[:3]} «{' '.join(ta[i1:i2])}»→«{' '.join(tb[j1:j2])}»" for o, i1, i2, j1, j2 in difflib.SequenceMatcher(None, ta, tb, autojunk=False).get_opcodes() if o != "equal")[:1500]
            f.write("\t".join(map(str, [r["key"], r["arm"], r.get("flagged"), r["guard"], r["flip"], r["exact"], opstr(x["de_old"], x["de_new"]),
                                        opstr(norm(x["tgt_old"]), norm(x["tgt_new"])), opstr(norm(x["tgt_old"]), norm(r["out"]))])) + "\n")
    json.dump(dict(summary=S, kill=K, pool=dict(P), rows=rows), open(f"{R}/scores.json", "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
