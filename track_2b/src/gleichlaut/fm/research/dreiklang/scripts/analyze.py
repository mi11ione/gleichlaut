"""Dreiklang S1/S2 analysis. Run on the M4 after raw/s1_scores.jsonl has come back from the Air.
  S1: 8B closed-list typing; "not a condition" threshold tau fitted on dev (candidate-level F1 of condition-vs-not), frozen,
      then everything is scored on held-out.
  S2: typed-regex v2 (frozen, built on dev only).
Outputs raw/analysis.json, raw/s1_pred.tsv, raw/s2_pred.tsv, raw/threshold.json; prints the tables used in results.md.
"""
import json, os, sys, math, collections
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, ".."); RAW = os.path.join(ROOT, "raw")
sys.path.insert(0, HERE)
import gold as G, compare as K, regex_v2 as R, gold_flags as GF  # noqa: E402

SUBJ = {"Alter": "age", "Gewicht": "wt", "Dosis": "dose", "Intervall": "int", "Zeit": "time", "Anzahl": "cnt",
        "Messwert": "meas", "Preis": "price"}
OPS = {"≥": ">=", ">": ">", "≤": "<=", "<": "<", "=": "="}
KNOWN = ["NEMLUVIO.01", "DIAPHIN.6-", "NEPEXTO", "BENEPALI4", "ERELZI2", "CRESE.Kps.IM", "DUPIXENT.02", "DUPIXENT.02P",
         "DUPIXENT.05a", "DUPIXENT.05P"]


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n); h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - h) / d, (c + h) / d)


def lse(xs):
    m = max(xs); return m + math.log(sum(math.exp(x - m) for x in xs))


def load_s1():
    p = os.path.join(RAW, "s1_scores.jsonl")
    if not os.path.exists(p):
        return None
    sc = {}
    for ln in open(p):
        r = json.loads(ln); sc[r["pkey"]] = r
    cmap = json.load(open(os.path.join(ROOT, "s1_candmap.json")))
    out = {}
    for ck, pk in cmap.items():
        r = sc[pk]; lp = r["lp"]
        cond = {o: v for o, v in lp.items() if o.strip() != "keine"}
        best = max(cond, key=cond.get)
        s_, o_ = best.strip().split(" ")
        out[ck] = dict(margin=lse(list(cond.values())) - lp[" keine"], best=(SUBJ[s_], OPS[o_]), secs=r["secs"], ntok=r["ntok"],
                       p_none=math.exp(lp[" keine"] - lse(list(lp.values()))))
    return out


def fit_tau(S1, D, gold, split="dev"):
    xs = []
    for it in D["items"]:
        if it["split"] != split:
            continue
        for l in K.LANGS:
            for c, g in zip(it["langs"][l]["cands"], gold[(it["cud"], l)]):
                xs.append((S1[f"{it['cud']}/{l}/{c['idx']}"]["margin"], g is not None))
    ms = sorted(set(m for m, _ in xs))
    grid = [ms[0] - 1] + [(a + b) / 2 for a, b in zip(ms, ms[1:])] + [ms[-1] + 1]
    best, res = None, []
    for t in grid:
        tp = sum(1 for m, y in xs if m > t and y); fp = sum(1 for m, y in xs if m > t and not y); fn = sum(1 for m, y in xs if m <= t and y)
        f1 = 2 * tp / (2 * tp + fp + fn) if tp else 0.0
        res.append((t, f1, tp, fp, fn))
    top = max(r[1] for r in res)
    tied = [r for r in res if r[1] == top]
    pick = tied[len(tied) // 2]
    auc_pos = [m for m, y in xs if y]; auc_neg = [m for m, y in xs if not y]
    auroc = sum((p > n) + 0.5 * (p == n) for p in auc_pos for n in auc_neg) / (len(auc_pos) * len(auc_neg))
    return dict(tau=pick[0], dev_f1=pick[1], dev_tp=pick[2], dev_fp=pick[3], dev_fn=pick[4], n_dev=len(xs), dev_auroc=auroc,
                tied_range=[tied[0][0], tied[-1][0]])


def evaluate(name, label, D, I, gold, gflags, split):
    """label(it, lang, cand) -> None | (subj, op)"""
    typ = {l: [0, 0] for l in K.LANGS}; typ_cond = {l: [0, 0] for l in K.LANGS}; typ_none = {l: [0, 0] for l in K.LANGS}
    acc_ok = acc_all = gold_acc_all = acc_ok_l = cov_l = 0
    wrong_acc, flags_out = [], []
    lim = dict(flagged=0, flagged_tp=0)
    known_hit = {}
    preds = []
    for it in D["items"]:
        if split != "all" and it["split"] != split:
            continue
        cud = it["cud"]
        per_p, per_g = {}, {}
        for l in K.LANGS:
            cs = it["langs"][l]["cands"]; labs = []
            for c, g in zip(cs, gold[(cud, l)]):
                p = label(it, l, c)
                gl = None if g is None else (g["subj"], g["op"])
                typ[l][0] += (p == gl); typ[l][1] += 1
                if gl is None:
                    typ_none[l][0] += (p is None); typ_none[l][1] += 1
                else:
                    typ_cond[l][0] += (p == gl); typ_cond[l][1] += 1
                labs.append(None if p is None else dict(subj=p[0], op=p[1]))
                preds.append((cud, it["split"], l, c["idx"], c["surface"], "N" if p is None else p[0] + p[1], "N" if gl is None else gl[0] + gl[1]))
            per_p[l] = K.tuples(cs, labs)[0]
            per_g[l] = K.tuples(cs, gold[(cud, l)], use_label_unit=True)[0]
        A_p, F_p = K.compare(per_p)
        A_g, _ = K.compare(per_g)
        acc_all += len(A_p); acc_ok += len(A_p & A_g); gold_acc_all += len(A_g)
        ok_l = {t for t in A_p if t in A_g or (t[3] == "" and any(g[:3] == t[:3] for g in A_g))}
        acc_ok_l += len(ok_l)
        cov_l += sum(1 for g in A_g if g in A_p or any(t[3] == "" and t[:3] == g[:3] for t in A_p))
        for t in sorted(A_p - ok_l, key=str):
            wrong_acc.append((cud, K.fmt_t(t)))
        gf = [g for g in gflags if g["cud"] == cud]
        real = [g for g in gf if g["verdict"] == "real"]; realm = [g for g in gf if g["verdict"] in ("real", "minor")]
        prim = [f for f in F_p if f["kind"] != "count"]
        cud_tp = False
        for f in prim:
            strict = any(g["kind"] == f["kind"] and g["odd"] == f["odd"] and tuple(g["t"]) == f["t"] for g in real)
            len_ = any(g["odd"] == f["odd"] and g["t"][2] == f["t"][2] for g in real)
            len_m = any(g["odd"] == f["odd"] and g["t"][2] == f["t"][2] for g in realm)
            flags_out.append(dict(cud=cud, kind=f["kind"], odd=f["odd"], t=K.fmt_t(f["t"]), strict=strict, lenient=len_, lenient_minor=len_m))
            cud_tp |= len_
        if prim:
            lim["flagged"] += 1; lim["flagged_tp"] += cud_tp
        if cud in KNOWN:
            known_hit[cud] = cud_tp
    nf = len(flags_out)
    r = dict(name=name, split=split,
             typing={l: dict(acc=typ[l][0] / typ[l][1], n=typ[l][1], cond_acc=typ_cond[l][0] / max(1, typ_cond[l][1]),
                             n_cond=typ_cond[l][1], none_acc=typ_none[l][0] / max(1, typ_none[l][1]), n_none=typ_none[l][1])
                     for l in K.LANGS},
             accepted=dict(n=acc_all, correct=acc_ok, precision=acc_ok / acc_all if acc_all else float("nan"),
                           ci=wilson(acc_ok, acc_all), gold_accepted=gold_acc_all,
                           coverage=acc_ok / gold_acc_all if gold_acc_all else float("nan"),
                           correct_ul=acc_ok_l, precision_ul=acc_ok_l / acc_all if acc_all else float("nan"),
                           ci_ul=wilson(acc_ok_l, acc_all), covered_ul=cov_l,
                           coverage_ul=cov_l / gold_acc_all if gold_acc_all else float("nan")),
             wrong_accepted=wrong_acc,
             flags=dict(n=nf, strict=sum(f["strict"] for f in flags_out), lenient=sum(f["lenient"] for f in flags_out),
                        lenient_minor=sum(f["lenient_minor"] for f in flags_out),
                        prec_lenient=sum(f["lenient"] for f in flags_out) / nf if nf else float("nan"),
                        prec_lenient_ci=wilson(sum(f["lenient"] for f in flags_out), nf),
                        prec_strict=sum(f["strict"] for f in flags_out) / nf if nf else float("nan"),
                        prec_lenient_minor=sum(f["lenient_minor"] for f in flags_out) / nf if nf else float("nan")),
             limitation_level=lim, known=known_hit, flag_list=flags_out)
    return r, preds


def show(r):
    a, f = r["accepted"], r["flags"]
    print(f"--- {r['name']} [{r['split']}]")
    print(f"  accepted precision {a['correct']}/{a['n']} = {a['precision']:.3f} CI [{a['ci'][0]:.3f}, {a['ci'][1]:.3f}]; "
          f"coverage {a['correct']}/{a['gold_accepted']} = {a['coverage']:.3f}")
    print(f"  unit-lenient: precision {a['correct_ul']}/{a['n']} = {a['precision_ul']:.3f} CI [{a['ci_ul'][0]:.3f}, {a['ci_ul'][1]:.3f}]; "
          f"coverage {a['covered_ul']}/{a['gold_accepted']} = {a['coverage_ul']:.3f}")
    print(f"  flags {f['n']}: lenient-real {f['lenient']} ({f['prec_lenient']:.3f}, CI {f['prec_lenient_ci'][0]:.3f}-{f['prec_lenient_ci'][1]:.3f}), "
          f"strict-real {f['strict']} ({f['prec_strict']:.3f}), real+minor {f['lenient_minor']} ({f['prec_lenient_minor']:.3f}); "
          f"limitations flagged {r['limitation_level']['flagged']}, with a real hit {r['limitation_level']['flagged_tp']}")
    print("  known:", sum(r["known"].values()), "/", len(r["known"]), {k: v for k, v in r["known"].items()})
    print("  typing:", {l: f"{t['acc']:.3f} (cond {t['cond_acc']:.3f} n={t['n_cond']}, N {t['none_acc']:.3f} n={t['n_none']})" for l, t in r["typing"].items()})
    if r["wrong_accepted"]:
        print("  wrong accepted (unit-lenient):", r["wrong_accepted"][:40])


def main():
    D, I, gold, _, _ = G.load()
    gflags = GF.build()
    texts = {(it["cud"], l): it["langs"][l]["text"] for it in D["items"] for l in K.LANGS}
    out = dict(runs=[])
    s2 = lambda it, l, c: R.type_cand(texts[(it["cud"], l)], c, l)
    S1 = load_s1()
    if S1:
        th = fit_tau(S1, D, gold)
        meta = json.load(open(os.path.join(RAW, "s1_meta.json")))
        th.update(premises=dict(model=meta["model"], weights_sha256=meta.get("weights_sha256"), template_sha256=meta["template_sha256"],
                                instr_sha256=meta["instr_sha256"]))
        json.dump(th, open(os.path.join(RAW, "threshold.json"), "w"), indent=1)
        print("threshold", {k: v for k, v in th.items() if k != "premises"})
        tau = th["tau"]
        s1 = lambda it, l, c: (S1[f"{it['cud']}/{l}/{c['idx']}"]["best"] if S1[f"{it['cud']}/{l}/{c['idx']}"]["margin"] > tau else None)
        s1_raw = lambda it, l, c: (S1[f"{it['cud']}/{l}/{c['idx']}"]["best"] if S1[f"{it['cud']}/{l}/{c['idx']}"]["margin"] > 0 else None)
        arms = [("S1 8B tau", s1), ("S1 8B argmax (tau=0)", s1_raw), ("S2 regex v2", s2)]
        out["threshold"] = th
    else:
        arms = [("S2 regex v2", s2)]
    for name, fn in arms:
        for split in ("held", "dev", "all"):
            r, preds = evaluate(name, fn, D, I, gold, gflags, split)
            out["runs"].append(r); show(r)
            if split == "all":
                tag = "s1" if name == "S1 8B tau" else "s2" if name.startswith("S2") else None
                if tag:
                    with open(os.path.join(RAW, f"{tag}_pred.tsv"), "w") as f:
                        f.write("cud\tsplit\tlang\tidx\tsurface\tpred\tgold\n")
                        for p in preds:
                            f.write("\t".join(map(str, p)) + "\n")
    if S1:
        sc = [json.loads(ln) for ln in open(os.path.join(RAW, "s1_scores.jsonl"))]
        out["speed"] = dict(n_prompts=len(sc), mean_s=sum(x["secs"] for x in sc) / len(sc),
                            median_s=sorted(x["secs"] for x in sc)[len(sc) // 2], mean_tokens=sum(x["ntok"] for x in sc) / len(sc))
        print("speed", out["speed"])
    json.dump(out, open(os.path.join(RAW, "analysis.json"), "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
