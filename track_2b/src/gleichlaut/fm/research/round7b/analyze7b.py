"""Score round-7b outputs. Usage: python3 analyze7b.py  (reads results/fedlex7b_{A,B,AEN}.json, writes results/analysis7b.json)"""
import json, os, sys
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
NAME = {"oc/2026/65": "MinöStV 24/2b", "oc/2025/97": "MAV 22/2", "oc/2024/79": "DBA Kanada 10/2a", "oc/2023/7": "VZVM 5/2",
        "oc/2025/135": "MWSTG 18/3", "oc/2024/137": "ETS Anh. IV", "oc/2026/170": "VZAE 82/1", "oc/2023/129": "EnG 71a/1",
        "oc/2026/273": "EnFV 46a/1"}
THR = 0.5
OTHER = {"de": "fr-it", "fr": "de-it", "it": "de-fr"}
CONT = {"de": ("de-fr", "de-it"), "fr": ("de-fr", "fr-it"), "it": ("de-it", "fr-it")}

def auroc(pos, neg):
    s = sum((p > n) + 0.5 * (p == n) for p in pos for n in neg); return s / (len(pos) * len(neg))

def loc(pd):
    sc = {L: (pd[a] + pd[b]) / 2 - pd[OTHER[L]] for L, (a, b) in CONT.items()}
    L = max(sc, key=sc.get); return L, sc[L], sc

def score(rows, getpd):
    T = [r for r in rows if r["kind"] == "target"]; C = [r for r in rows if r["kind"] == "control"]
    out = dict(n_t=len(T), n_c=len(C), cases=[])
    hit_thr = hit_arg = ff = 0; item_t = []; item_c = []; loc_t = []; loc_c = []
    for r in rows:
        pd = getpd(r); L, s, sc = loc(pd); flag = s >= THR; item = max(pd.values()) - min(pd.values())
        if r["kind"] == "target":
            hit_arg += L == r["gold"]; hit_thr += (L == r["gold"] and flag); item_t.append(item); loc_t.append(s)
            out["cases"].append(dict(case=NAME[r["oc"]], gold=r["gold"], argmax=L, loc_score=round(s, 3), flagged=flag,
                                     hit=L == r["gold"] and flag, pd={k: round(v, 3) for k, v in pd.items()}))
        else:
            ff += flag; item_c.append(item); loc_c.append(s)
            if flag: out.setdefault("false_flags", []).append(dict(id=r["id"], eid=r["eid"], argmax=L, loc_score=round(s, 3),
                                                                 pd={k: round(v, 3) for k, v in pd.items()}))
    # operating points calibrated on the controls themselves (TUNED, descriptive only): threshold = (k+1)-th highest control loc score
    srt = sorted(loc_c, reverse=True); ops = {}
    for k in (0, 3):
        th = srt[k]
        ops[f"ff<={k}"] = dict(thr=round(th, 4), ff=sum(1 for v in loc_c if v > th),
                              hits=sum(1 for r in T if (lambda L, s, _: L == r["gold"] and s > th)(*loc(getpd(r)))),
                              flagged_t=sum(1 for v in loc_t if v > th))
    out["ctrl_calibrated"] = ops
    out.update(hits_thr=hit_thr, hits_argmax=hit_arg, false_flags_n=ff, auroc_item=round(auroc(item_t, item_c), 3),
               auroc_loc=round(auroc(loc_t, loc_c), 3),
               mean_pd_controls={k: round(sum(getpd(r)[k] for r in C) / len(C), 3) for k in ("de-fr", "de-it", "fr-it")},
               mean_pd_targets={k: round(sum(getpd(r)[k] for r in T) / len(T), 3) for k in ("de-fr", "de-it", "fr-it")},
               argmax_dist={L: sum(1 for r in rows if loc(getpd(r))[0] == L) for L in "de fr it".split()},
               max_ctrl_loc=round(max(loc_c), 3), item_t=[round(v, 3) for v in item_t])
    return out

FLIP = False
def lo_of(r):
    """mean over the two orders of log-odds(differs), from raw logprobs (avoids saturation)."""
    f = lambda o: (o["lp_yes"] - o["lp_no"]) if FLIP else (o["lp_no"] - o["lp_yes"])
    return {k: (f(v["ab"]) + f(v["ba"])) / 2 for k, v in r["pairs"].items()}

def pd_of(r, order=None):
    return {k: (v["p_diff"] if order is None else v[order]["p_diff"]) for k, v in r["pairs"].items()}

res = {}; data = {}
for v in ("A", "B", "AEN", "AFLIP"):
    f = f"{D}/fedlex7b_{v}.json"
    if os.path.exists(f): data[v] = json.load(open(f))["rows"]
for v, rows in data.items():
    FLIP = v == "AFLIP"
    res[v] = score(rows, pd_of)
    lo = score(rows, lo_of)
    res[v]["logodds"] = dict(hits_argmax=lo["hits_argmax"], ctrl_calibrated=lo["ctrl_calibrated"], auroc_item=lo["auroc_item"], auroc_loc=lo["auroc_loc"],
                             mean_lo_controls=lo["mean_pd_controls"], mean_lo_targets=lo["mean_pd_targets"], argmax_dist=lo["argmax_dist"],
                             cases=[dict(case=c["case"], gold=c["gold"], argmax=c["argmax"], loc_score=c["loc_score"], lo=c["pd"]) for c in lo["cases"]])
    for o in ("ab", "ba"): res[f"{v}[{o} only]"] = {k: x for k, x in score(rows, lambda r: pd_of(r, o)).items() if k != "cases"}
    res[v]["order_agreement_mean_abs_diff"] = round(sum(abs(p["ab"]["p_diff"] - p["ba"]["p_diff"]) for r in rows for p in r["pairs"].values()) / (3 * len(rows)), 3)
    FLIP = False
    res[v]["mean_mass"] = round(sum(p[o]["mass"] for r in rows for p in r["pairs"].values() for o in ("ab", "ba")) / (6 * len(rows)), 3)
if "A" in data and "AEN" in data:
    FLIP = False
    ids = {r["id"] + r["eid"] for r in data["AEN"]}
    res["A[EN subset]"] = {k: x for k, x in score([r for r in data["A"] if r["id"] + r["eid"] in ids], pd_of).items() if k != "cases"}
if "A" in data and "B" in data:
    bmap = {r["id"] + r["eid"]: r for r in data["B"]}
    res["A+B mean (post hoc)"] = score(data["A"], lambda r: {k: (pd_of(r)[k] + pd_of(bmap[r["id"] + r["eid"]])[k]) / 2 for k in r["pairs"]})
from math import comb
res["_chance"] = {f">={k}/9 argmax by chance (p=1/3)": round(sum(comb(9, j) * (1/3)**j * (2/3)**(9-j) for j in range(k, 10)), 4) for k in (4, 5, 6)}
json.dump(res, open(f"{D}/analysis7b.json", "w"), ensure_ascii=False, indent=1)
print(res["_chance"])
for v, s in res.items():
    if v.startswith("_"): continue
    print(f"{v:22s} hits(thr)={s['hits_thr']}/{s['n_t']} hits(argmax)={s['hits_argmax']}/{s['n_t']} FF={s['false_flags_n']}/{s['n_c']} "
          f"calib={s.get('ctrl_calibrated')} AUROC item={s['auroc_item']} loc={s['auroc_loc']} ctrl pd={s['mean_pd_controls']} tgt pd={s['mean_pd_targets']} argmax={s['argmax_dist']}")
    for c in s.get("cases", []): print("   ", c)
    if "logodds" in s:
        L = s["logodds"]; print("   LOGODDS ctrl-calibrated", L["ctrl_calibrated"], "argmax hits", L["hits_argmax"], "AUROC item", L["auroc_item"], "loc", L["auroc_loc"], "ctrl", L["mean_lo_controls"], "tgt", L["mean_lo_targets"], L["argmax_dist"])
        for c in L["cases"]: print("     ", c)
    for c in s.get("false_flags", []): print("    FF", c)
