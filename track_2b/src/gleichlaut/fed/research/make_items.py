"""pools/*.json -> items.json (one item per paragraph x target language) + S3 items. stdlib only."""
import json, os
H = os.path.dirname(os.path.abspath(__file__))
P = lambda f: json.load(open(f"{H}/pools/{f}")) if os.path.exists(f"{H}/pools/{f}") else None
items = []
fi = P("fed_fr_it.json")
for x in fi["pool"][:60]:
    for l in ("fr", "it"):
        items.append(dict(key=f"{x['id']}|{l}", src="fed", lang=l, act=x["act"], eid=x["eid"], d_old=x["d_old"], d_new=x["d_new"],
                          de_old=x["de_old"], de_new=x["de_new"], tgt_old=x[f"{l}_old"], tgt_new=x[f"{l}_new"]))
rm = []
fr = P("fed_rm.json")
if fr:
    for x in fr["pool"][:10]:
        rm.append(dict(key=f"{x['id']}|rm", src="fed", lang="rm", act=x["act"], eid=x["eid"], d_old=x["d_old"], d_new=x["d_new"],
                       de_old=x["de_old"], de_new=x["de_new"], tgt_old=x["rm_old"], tgt_new=x["rm_new"]))
gr = P("gr_rm.json")
for x in gr["pool"]:
    if len(rm) >= 30: break
    rm.append(dict(key=f"{x['id']}|rm", src="gr", lang="rm", act=x["act"], eid=x["eid"], d_old=x["d_old"], d_new=x["d_new"],
                   de_old=x["de_old"], de_new=x["de_new"], tgt_old=x["rm_old"], tgt_new=x["rm_new"]))
items += rm
s3 = P("s3_history.json") or []
for r in s3:
    if r.get("kind") == "new_unit_in_amendment":  # no old target text: arm B only (fresh translation of the new DE unit)
        items.append(dict(key=f"S3|{r['oc']}|{r['eid']}|{r['lang']}", src="s3", lang=r["lang"], act=r["act"], eid=r["eid"], d_old=r["prev"], d_new=r["born"],
                          de_old="", de_new=r["de_new"], tgt_old="", tgt_new=r["bad"], tgt_corrected=r["good"], de_at_fix=r["de_at_fix"]))
    if r.get("kind") == "amendment_delta":
        items.append(dict(key=f"S3|{r['oc']}|{r['eid']}|{r['lang']}", src="s3", lang=r["lang"], act=r["act"], eid=r["eid"], d_old=r["prev"], d_new=r["born"],
                          de_old=r["de_old"], de_new=r["de_new"], tgt_old=r["tgt_old"], tgt_new=r["bad"], tgt_corrected=r["good"]))
import re
def clean(t):
    return re.sub(r"\(\s+", "(", re.sub(r"\s+([.,;:)»])", r"\1", t)) if t else t
for x in items:
    for k in ("de_old", "de_new", "tgt_old", "tgt_new", "tgt_corrected", "de_at_fix"):
        if x.get(k): x[k] = clean(x[k])
json.dump(items, open(f"{H}/items.json", "w"), ensure_ascii=False, indent=1)
from collections import Counter
print(len(items), Counter((x["src"], x["lang"]) for x in items))
