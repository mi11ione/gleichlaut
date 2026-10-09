"""Fedlex mining: two consecutive consolidated versions of an act -> change items {key, de_old, de_new, tgt_old, tgt_new, ...}.

The per-paragraph filters are build_fed.py's main loop, ported line for line (it is not a function there): DE leaf text
changed; DE_new is a repeal ("aufgehoben", "…") -> skipped (the code lane copies "N …"); a target text unchanged ->
skipped; DE change ratio > 0.6 -> skipped (route to a human); 15 <= len(DE_old) <= 1200 and len(DE_new) <= 1400.
The item shape and the punctuation clean-up are make_items.py's (clean() executed from the vendored file).

usage: PYTHONPATH=src python3 -m gleichlaut.fed.mine cc/2011/28 [D_OLD D_NEW] [--langs fr,it] [--online]
       PYTHONPATH=src python3 -m gleichlaut.fed.mine --smoke     (re-mine the research items from the local cache)"""
import json, os, re, sys
from collections import Counter, defaultdict
from ..core import _extract
from .ingest import Fedlex, common, RES

MK = _extract(os.path.join(RES, "make_items.py"), ("clean",), {"re": re})
clean = MK["clean"]


def candidates(fx, act, d_old, d_new, tl=("fr", "it"), v=None):
    """-> (pool rows as build_fed.py writes them, stats, skipped) for one version pair, or None if a document is missing."""
    langs = ("de",) + tuple(tl)
    v = v or fx.versions(act)
    if not all(l in v.get(d, {}) for d in (d_old, d_new) for l in langs): return None
    ao, an = fx.leaves(v[d_old], langs), fx.leaves(v[d_new], langs)
    if ao is None or an is None: return None
    found, stats, skipped = [], Counter(), []
    for eid in sorted(set(ao) & set(an)):
        o, n = ao[eid], an[eid]
        if o["de"] == n["de"]: continue
        stats["de_changed"] += 1
        if common.is_repeal(n["de"]): stats["repealed"] += 1; skipped.append(dict(act=act, eid=eid, why="repeal", de_new=n["de"], **{f"{l}_new": n[l] for l in tl})); continue
        if not all(n[l] != o[l] for l in tl): stats["target_unchanged"] += 1; skipped.append(dict(act=act, eid=eid, why="target_unchanged", de_old=o["de"], de_new=n["de"])); continue
        r = common.change_ratio(o["de"], n["de"])
        if r > 0.6: stats["replaced_gt60"] += 1; skipped.append(dict(act=act, eid=eid, why="replaced_gt60", ratio=r)); continue
        if not (15 <= len(o["de"]) <= 1200 and len(n["de"]) <= 1400): stats["length"] += 1; continue
        found.append(dict(id=f"{act}/{d_new}#{eid}", act=act, d_old=d_old, d_new=d_new, eid=eid, de_change_ratio=round(r, 3),
                          de_old=o["de"], de_new=n["de"], **{f"{l}_old": o[l] for l in tl}, **{f"{l}_new": n[l] for l in tl}))
    return found, stats, skipped


def to_items(rows, tl=("fr", "it")):
    """pool rows -> items, one per target language (make_items.py's shape and clean())."""
    out = []
    for x in rows:
        for l in tl:
            it = dict(key=f"{x['id']}|{l}", src="fed", lang=l, act=x["act"], eid=x["eid"], d_old=x["d_old"], d_new=x["d_new"],
                      de_old=x["de_old"], de_new=x["de_new"], tgt_old=x[f"{l}_old"], tgt_new=x[f"{l}_new"])
            for k in ("de_old", "de_new", "tgt_old", "tgt_new"):
                if it.get(k): it[k] = clean(it[k])
            out.append(it)
    return out


def mine(act, d_old=None, d_new=None, tl=("fr", "it"), fx=None):
    """items for one act: the given version pair, or the newest consecutive pair in DE + `tl`."""
    fx = fx or Fedlex()
    v, P = fx.pairs(act, ("de",) + tuple(tl))
    if d_old is None:
        if not P: return [], Counter(no_pair=1), []
        d_old, d_new = P[-1]
    r = candidates(fx, act, d_old, d_new, tl, v)
    if r is None: return [], Counter(missing_document=1), []
    rows, stats, skipped = r
    return to_items(rows, tl), stats, skipped


def smoke(items_path=None, acts=None, fx=None):
    """Re-mine every federal FR/IT item of data/items/fedlex_items.json from the local cache and require identical items.
    -> dict(n_items, reproduced, missing, differing, version_pairs)."""
    from .lane import ITEMS
    from .lane import load
    items = [x for x in load(items_path or ITEMS) if x["src"] == "fed" and x["lang"] in ("fr", "it")]
    fx = fx or Fedlex()
    by = defaultdict(list)
    for x in items: by[(x["act"], x["d_old"], x["d_new"])].append(x)
    ok, missing, diff = 0, [], []
    for (act, a, b), xs in sorted(by.items()):
        if acts and act not in acts: continue
        got = {y["key"]: y for y in mine(act, a, b, fx=fx)[0]}
        for x in xs:
            if x["key"] not in got: missing.append(x["key"])
            elif got[x["key"]] != x: diff.append(x["key"])
            else: ok += 1
    n = sum(len(xs) for (act, _, _), xs in by.items() if not acts or act in acts)
    return dict(n_items=n, reproduced=ok, missing=missing, differing=diff, version_pairs=len([k for k in by if not acts or k[0] in acts]))


def main(argv):
    if "--smoke" in argv:
        r = smoke(); print(json.dumps(r, indent=1)); return 0 if r["reproduced"] == r["n_items"] else 1
    online = "--online" in argv
    tl = ("fr", "it")
    if "--langs" in argv: tl = tuple(argv[argv.index("--langs") + 1].split(","))
    pos = [a for i, a in enumerate(argv) if not a.startswith("--") and (i == 0 or argv[i - 1] != "--langs")]
    items, stats, skipped = mine(pos[0], *(pos[1:3] or [None, None]), tl=tl, fx=Fedlex(online=online))
    print(json.dumps(dict(stats=stats, skipped=len(skipped), items=items), ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
