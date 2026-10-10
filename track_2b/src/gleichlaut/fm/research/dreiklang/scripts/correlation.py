"""Are S1 8B typing errors correlated across languages? Aligned triples = the k-th candidate carrying the same gold tuple
(gold units) in DE, FR and IT of one CUD, for tuples with equal gold counts in all three. Also subject-only accuracy."""
import json, os, sys, collections, math, itertools
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import analyze as A, gold as G, compare as K, regex_v2 as R
D, I, gold, _, _ = G.load(); S1 = A.load_s1(); tau = json.load(open(os.path.join(HERE, "..", "raw", "threshold.json")))["tau"]
L = K.LANGS
def s1(cud, l, c):
    x = S1[f"{cud}/{l}/{c['idx']}"]; return x["best"] if x["margin"] > tau else None
out = {}
for split in ("held", "all"):
    triples = []
    for it in D["items"]:
        if split != "all" and it["split"] != split: continue
        if it["cud"] in ("DUPIXENT.02P", "DUPIXENT.05P", "BENEPALI4", "ERELZI2"): continue  # copies: count each text once
        occ = {l: collections.defaultdict(list) for l in L}
        for l in L:
            for c, g in zip(it["langs"][l]["cands"], gold[(it["cud"], l)]):
                if g is None: continue
                v, u = K.norm_value_unit(c["v"], g["unit"]); occ[l][(g["subj"], g["op"], v, u)].append(c)
        for t in occ["de"]:
            if all(len(occ[l][t]) == len(occ["de"][t]) for l in L):
                for k in range(len(occ["de"][t])):
                    triples.append((it["cud"], t, {l: occ[l][t][k] for l in L}))
    rows = []
    for cud, t, cs in triples:
        g = (t[0], t[1])
        pred = {l: s1(cud, l, cs[l]) for l in L}
        rows.append(dict(cud=cud, wrong={l: pred[l] != g for l in L}, pred=pred))
    n = len(rows); p = {l: sum(r["wrong"][l] for r in rows) / n for l in L}
    dist = collections.Counter(sum(r["wrong"].values()) for r in rows)
    # expected #wrong distribution under independence with the observed per-language rates
    exp = collections.Counter()
    for combo in itertools.product([0, 1], repeat=3):
        pr = 1
        for l, w in zip(L, combo): pr *= p[l] if w else 1 - p[l]
        exp[sum(combo)] += pr * n
    all3_same = sum(1 for r in rows if all(r["wrong"].values()) and len({r["pred"][l] for l in L}) == 1)
    two_same_wrong = sum(1 for r in rows if sum(r["wrong"].values()) >= 2 and
                         any(r["wrong"][a] and r["wrong"][b] and r["pred"][a] == r["pred"][b] for a, b in itertools.combinations(L, 2)))
    phi = {}
    for a, b in itertools.combinations(L, 2):
        n11 = sum(r["wrong"][a] and r["wrong"][b] for r in rows); n10 = sum(r["wrong"][a] and not r["wrong"][b] for r in rows)
        n01 = sum(not r["wrong"][a] and r["wrong"][b] for r in rows); n00 = n - n11 - n10 - n01
        den = math.sqrt((n11 + n10) * (n01 + n00) * (n11 + n01) * (n10 + n00)) or 1
        phi[f"{a}-{b}"] = round((n11 * n00 - n10 * n01) / den, 3)
    out[split] = dict(n_triples=n, err_rate=p, wrong_dist=dict(sorted(dist.items())), expected_indep={k: round(v, 1) for k, v in sorted(exp.items())},
                      all3_wrong_identical=all3_same, ge2_wrong_with_identical_pair=two_same_wrong, phi=phi)
# subject-only accuracy on gold conditions (held-out), 8B best subject vs regex subject
texts = {(it["cud"], l): it["langs"][l]["text"] for it in D["items"] for l in L}
sub = {}
for name in ("8B", "regex"):
    acc = {l: [0, 0] for l in L}; opacc = {l: [0, 0] for l in L}
    for it in D["items"]:
        if it["split"] != "held": continue
        for l in L:
            for c, g in zip(it["langs"][l]["cands"], gold[(it["cud"], l)]):
                if g is None: continue
                pr = S1[f"{it['cud']}/{l}/{c['idx']}"]["best"] if name == "8B" else (R.type_cand(texts[(it["cud"], l)], c, l) or (None, None))
                acc[l][0] += pr[0] == g["subj"]; acc[l][1] += 1; opacc[l][0] += pr[1] == g["op"]; opacc[l][1] += 1
    sub[name] = {l: dict(subject=round(acc[l][0] / acc[l][1], 3), operator=round(opacc[l][0] / opacc[l][1], 3), n=acc[l][1]) for l in L}
out["held_subject_operator_acc_on_gold_conditions"] = sub
json.dump(out, open(os.path.join(HERE, "..", "raw", "correlation.json"), "w"), indent=1, default=str)
print(json.dumps(out, indent=1, default=str))
