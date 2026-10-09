"""Federal pool: consecutive consolidated versions (new version applicable 2025-01-01..2026-10-08), AKN leaves aligned by eId,
DE paragraph changed -> (DE_old, DE_new, FR/IT/RM old, new). stdlib only.
usage: python3 -I build_fed.py fr_it   |   python3 -I build_fed.py rm"""
import json, os, random, re, sys, difflib
from collections import Counter
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
import net, units as U
from common import tok, change_ratio, is_repeal

MODE = sys.argv[1]
LM = {"DEU": "de", "FRA": "fr", "ITA": "it", "ROH": "rm"}
QV = """PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
SELECT ?d ?lang ?f WHERE { ?c jolux:isMemberOf <https://fedlex.data.admin.ch/eli/%s> ; jolux:dateApplicability ?d .
 ?c jolux:isRealizedBy ?e . ?e jolux:language ?lang . ?e jolux:isEmbodiedBy ?m . ?m jolux:userFormat <https://fedlex.data.admin.ch/vocabulary/user-format/xml> . ?m jolux:isExemplifiedBy ?f . }"""


def versions(act):
    v = {}
    for b in net.sparql(QV % act):
        l = LM.get(b["lang"]["value"].rsplit("/", 1)[1])
        if l: v.setdefault(b["d"]["value"], {})[l] = b["f"]["value"]
    return v


def roots_for(urls, langs):
    out = {}
    for l in langs:
        b = net.get(urls[l])
        if b is None or len(b) > 6_000_000: return None
        try: out[l] = U.load_xml_bytes(b)
        except Exception: return None
    return out


def main():
    rng = random.Random(20261008)
    if MODE == "fr_it":
        langs, tl = ("de", "fr", "it"), ("fr", "it")
        rows = json.load(open(f"{H}/raw/fed_cons_2025_26.json")); lo, hi = "2025-01-01", "2026-10-08"
        target, per_act = 60, 4
    else:
        langs, tl = ("de", "rm"), ("rm",)
        rows = json.load(open(f"{H}/raw/fed_rm_cons_2023plus.json")); lo, hi = "2024-01-01", "2026-10-08"
        target, per_act = 30, 4
    acts = sorted({a for a, d in rows}); rng.shuffle(acts)
    pool, stats, skipped = [], Counter(), []
    for act in acts:
        if len(pool) >= target: break
        v = versions(act)
        ds = sorted(d for d in v if all(l in v[d] for l in langs))
        cand = [(ds[i - 1], ds[i]) for i in range(1, len(ds)) if lo <= ds[i] <= hi]
        if not cand: stats["act_no_pair"] += 1; continue
        d_old, d_new = cand[-1] if MODE == "rm" else rng.choice(cand)
        ro, rn = roots_for(v[d_old], langs), roots_for(v[d_new], langs)
        if not ro or not rn: stats["act_fetch_fail"] += 1; continue
        ao, an = U.aligned_leaves(ro), U.aligned_leaves(rn)
        found = []
        for eid in sorted(set(ao) & set(an)):
            o, n = ao[eid], an[eid]
            if o["de"] == n["de"]: continue
            stats["de_changed"] += 1
            if is_repeal(n["de"]): stats["repealed"] += 1; skipped.append(dict(act=act, eid=eid, why="repeal", de_new=n["de"], **{f"{l}_new": n[l] for l in tl})); continue
            if not all(n[l] != o[l] for l in tl): stats["target_unchanged"] += 1; skipped.append(dict(act=act, eid=eid, why="target_unchanged", de_old=o["de"], de_new=n["de"])); continue
            r = change_ratio(o["de"], n["de"])
            if r > 0.6: stats["replaced_gt60"] += 1; skipped.append(dict(act=act, eid=eid, why="replaced_gt60", ratio=r)); continue
            if not (15 <= len(o["de"]) <= 1200 and len(n["de"]) <= 1400): stats["length"] += 1; continue
            found.append(dict(id=f"{act}/{d_new}#{eid}", act=act, d_old=d_old, d_new=d_new, eid=eid, de_change_ratio=round(r, 3),
                              de_old=o["de"], de_new=n["de"], **{f"{l}_old": o[l] for l in tl}, **{f"{l}_new": n[l] for l in tl}))
        rng.shuffle(found)
        pool += found[:per_act]
        stats["acts_used"] += bool(found)
        print(act, d_old, "->", d_new, "leaves", len(ao), "found", len(found), "pool", len(pool), flush=True)
    pool = pool[:target]
    json.dump(dict(mode=MODE, stats=stats, pool=pool, skipped=skipped), open(f"{H}/pools/fed_{MODE}.json", "w"), ensure_ascii=False, indent=1)
    print("POOL", len(pool), dict(stats))


if __name__ == "__main__":
    main()
