"""Score the out-of-sample run. usage: python3 -I oos_score.py [labels.tsv]
Reads fresh/items_fresh.json, fresh/final/arm2b.jsonl (fresh 2025 set, guards3). Flag = the frozen full guard stack (reask.py full_check), final output.
Metrics per group (all / seen families / unseen families): exact, edit-F1, chrF vs rules-only (paired cluster bootstrap over
DE pairs, score2.boot_diff), flag rate, and - when labels are given - unflagged real / stale / untranslated per 100.
Without labels it writes the hand-check worklist: every unflagged non-exact item + 20 flagged (seed 20261009)."""
import json, sys, os, random
from collections import Counter
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, "/Users/mi11ion/Desktop/hackapertus/spikes/gleichlaut/s2")
import score2, gl2
from lock import norm
I = {x["key"]: x for x in json.load(open(f"{H}/items_fresh.json"))}
F = {json.loads(l)["key"]: json.loads(l) for l in open(f"{H}/final/arm2b.jsonl")}
lab = {}
if len(sys.argv) > 1:
    for l in open(sys.argv[1]).read().splitlines()[1:]:
        k, c, *_ = l.split("\t"); lab[k] = c
rows1, rows2 = [], []
for k, x in I.items():
    r1, _ = gl2.rules(x["de_old"], x["de_new"], x["tgt_old"], x["lang"])
    a = score2.score_one(x, r1, "1"); f = F[k]
    b = score2.score_one(x, f["out"], "1")      # arm "1" path = metrics only; flag taken from the frozen stack below
    b.update(flagged=f["guard_flag"], reasked=f.get("reasked", False), replaced=f.get("replaced", False), rule_only=f["rule_only"],
             seen=x["seen_family"], cls=("exact" if b["exact"] else lab.get(k, "?")))
    a["seen"] = x["seen_family"]; rows1.append(a); rows2.append(b)
out = {}
for g, sel in (("all", lambda r: True), ("unseen families", lambda r: not r["seen"]), ("seen families", lambda r: r["seen"]),
               ("fr", lambda r: r["lang"] == "fr"), ("it", lambda r: r["lang"] == "it")):
    A = [r for r in rows1 if sel(r)]; B = [r for r in rows2 if sel(r)]; n = len(B)
    d = {"n": n, "pairs": len({r["pair"] for r in B}), "families": len({I[r["key"]]["cluster"] for r in B})}
    for fld, sc in (("exact", 100), ("ef1", 100), ("chrf", 1)):
        ma, mb = sc * sum(float(r[fld]) for r in A) / n, sc * sum(float(r[fld]) for r in B) / n
        ci = score2.boot_diff(B, A, fld); ci = (ci[0] / 100, ci[1] / 100) if fld == "chrf" else ci
        d[fld] = dict(rules=round(ma, 1), model=round(mb, 1), delta=round(mb - ma, 1), ci95=[round(ci[0], 1), round(ci[1], 1)])
    d["flagged"] = sum(r["flagged"] for r in B); d["flag_rate"] = round(100 * d["flagged"] / n, 1)
    d["exact_n"] = sum(r["exact"] for r in B); d["rules_exact_n"] = sum(r["exact"] for r in A)
    d["exact_flagged"] = sum(r["exact"] and r["flagged"] for r in B)
    d["reasked"] = sum(r["reasked"] for r in B); d["replaced"] = sum(r["replaced"] for r in B)
    U = [r for r in B if not r["flagged"]]; d["unflagged"] = len(U); d["unflagged_classes"] = dict(Counter(r["cls"] for r in U))
    if lab:
        for c in ("REAL", "stale", "german"):
            m = sum(r["cls"] == c for r in U); d[f"unflagged_{c}"] = m; d[f"unflagged_{c}_per100"] = round(100 * m / n, 2)
    out[g] = d
    print(g, json.dumps(d, ensure_ascii=False))
json.dump(dict(summary=out, rows=rows2), open(f"{H}/oos_scores.json", "w"), ensure_ascii=False, indent=1)
if not lab:
    work = [r["key"] for r in rows2 if not r["flagged"] and not r["exact"]]
    fl = sorted(r["key"] for r in rows2 if r["flagged"]); samp = random.Random(20261009).sample(fl, min(20, len(fl)))
    json.dump(dict(unflagged=work, flagged_sample=samp), open(f"{H}/worklist.json", "w"), indent=1)
    print("worklist: unflagged non-exact", len(work), "flagged sample", len(samp))
