"""Real DE limitation changes between consecutive ePL snapshots, and the FR/IT change items built from them.

mine():  ported from spikes/gleichlaut/s2/mine.py. Per product (MPD id, stable across snapshots), DE texts gone from A and texts
         new in B are paired greedily by token similarity. A pair is a change for the drafting lane if <= 60% of tokens changed
         and it is not spacing-only; > 60% is a rewrite routed to a human (kept in 'human'). The 4 May 2026 snapshot is excluded
         (publisher bug: drops every '<...>' span, restored in June); old-format (Feb-Apr) pairs with any '<' are dropped.
build(): ported from spikes/gleichlaut/s2/build_items.py. FR/IT old/new = the official texts under the same key in the same two
         snapshots; filters: DE <= 2500 chars, target present on both sides, no '<' in old-format target texts, target changed.
         Family = digit-masked DE edit signature, md5[:8]. Seeded selection of 60 DE pairs from 60 families (the dev 120).
Only change from the research code: products are iterated in sorted order (the research iterated a set, so the order of pairs,
and with it which member of a multi-pair family was picked, depended on PYTHONHASHSEED). Counts do not depend on it.

month_items(): one month in operation (gleichlaut month): every DE change between two snapshots, as items for the drafting
         lane (key, lang, de_old, de_new, tgt_old, change_ratio, product, cud ids; tgt_new only where BAG already published a
         changed FR/IT text, for shadow-mode evaluation) plus the changes that cannot become an item (no old FR/IT text, ...).

The snapshot dates are parameters (--snaps / --from --to); SNAPS is the research series and the default of the reproduction.

usage: python3 -m gleichlaut.sl.mine [--hist DIR] [--out DIR] [--snaps D1,D2,... | --from D1 --to D2]
       -> changes_de.json, pool_stats.json, items.json, items_all.json"""
import argparse, difflib, hashlib, json, os, random, re, sys
from collections import Counter, defaultdict
from . import hist_dir, OUT
from .ingest import nrm

SNAPS = ["20260219", "20260304", "20260401", "20260601", "20260701", "20260801", "20260901", "20261001", "20261006"]
EXCLUDED = {"20260504": "publisher bug: drops every '<...>' span (restored in June)"}
OLD_FORMAT_LAST = "20260504"      # snapshots <= this drop '<...>' spans: any '<' makes a pair untrustworthy
MAXRATIO = 0.60; N = 60; SEED = 20261009; MAXCH = 2500
TOK = re.compile(r"\d+(?:[.,'’]\d+)*|\w+|[^\w\s]")


def change_ratio(a, b):
    ta, tb = TOK.findall(a), TOK.findall(b)
    sm = difflib.SequenceMatcher(None, ta, tb, autojunk=False)
    return 1 - sum(m.size for m in sm.get_matching_blocks()) / max(1, max(len(ta), len(tb)))


def route(ratio):
    return "draft" if ratio <= MAXRATIO else "human"


class Hist:
    """lazy cache of snapshot files {snap}-{lang}.json in one directory."""
    def __init__(self, d): self.d, self._c = d, {}
    def __call__(self, snap, lang="de"):
        if (snap, lang) not in self._c:
            with open(os.path.join(self.d, f"{snap}-{lang}.json"), encoding="utf-8") as f: self._c[(snap, lang)] = json.load(f)
        return self._c[(snap, lang)]
    def has(self, snap, lang="de"): return os.path.exists(os.path.join(self.d, f"{snap}-{lang}.json"))
    def byprod(self, snap):
        """-> {mpd: (name, {nrm DE text: key})} (first key wins for duplicate texts), as mine.py:load."""
        J = self(snap, "de"); out = {}
        for m, p in J["prod"].items():
            t = {}
            for k in p["keys"]: t.setdefault(nrm(J["lim"][k]), k)
            out[m] = (p["name"], t)
        return out


def match(ta, tb):
    """greedy pairing of texts gone from ta with texts new in tb, most similar first -> [(ratio, gone, new)]."""
    gone = [t for t in ta if t not in tb]; new = [t for t in tb if t not in ta]
    if not gone or not new: return []
    cand = sorted(((change_ratio(g, n), g, n) for g in gone for n in new), key=lambda x: x[0])
    ug, un, out = set(), set(), []
    for r, g, n in cand:
        if g in ug or n in un: continue
        ug.add(g); un.add(n); out.append((r, g, n))
    return out


def check_snaps(snaps):
    """dates must be YYYYMMDD, strictly increasing, and not a known-bad snapshot."""
    for d in snaps:
        if not re.fullmatch(r"\d{8}", d): raise ValueError(f"snapshot date {d!r} is not YYYYMMDD")
        if d in EXCLUDED: raise ValueError(f"snapshot {d} is excluded: {EXCLUDED[d]}")
    if any(a >= b for a, b in zip(snaps, snaps[1:])): raise ValueError(f"snapshot dates must increase: {snaps}")
    return list(snaps)


def steps(hist, snaps=SNAPS):
    """yield (a, b, mpd, name, ta, tb, [(ratio, gone, new)]) for every product present in both snapshots of each step."""
    prev = hist.byprod(snaps[0])
    for a, b in zip(snaps, snaps[1:]):
        cur = hist.byprod(b)
        for m in sorted(set(prev) & set(cur)):
            name, ta = prev[m]; _, tb = cur[m]
            yield a, b, m, name, ta, tb, match(ta, tb)
        prev = cur


def mine(hist, snaps=SNAPS, log=True):
    """-> dict(stats, pairs, human). stats/pairs as the research changes_de.json; human = distinct > 60% rewrites."""
    pairs, human, stats, st = {}, {}, [], None
    for a, b, m, name, ta, tb, M in steps(hist, snaps):
        if st is None or st["a"] != a:
            if st: stats.append(st)
            st = dict(a=a, b=b, matched=0, over60=0, new_distinct_pairs=0)
        for r, g, n in M:
            st["matched"] += 1
            occ = dict(snap_old=a, key_old=ta[g], snap_new=b, key_new=tb[n], mpd=m, name=name)
            if r > MAXRATIO:
                st["over60"] += 1
                human.setdefault((g, n), dict(de_old=g, de_new=n, ratio=round(r, 3), first=(a, b), occ=[]))["occ"].append(occ)
                continue
            if TOK.findall(g) == TOK.findall(n): continue                                  # spacing-only
            if a <= OLD_FORMAT_LAST and ("<" in g or "<" in n): continue                   # publisher '<...>' bug
            if (g, n) not in pairs:
                pairs[(g, n)] = dict(de_old=g, de_new=n, ratio=round(r, 3), first=(a, b), occ=[]); st["new_distinct_pairs"] += 1
            pairs[(g, n)]["occ"].append(occ)
    if st: stats.append(st)
    if log:
        for s in stats: print(s, file=sys.stderr)
        print("distinct DE change pairs:", len(pairs), " distinct >60% rewrites:", len(human), file=sys.stderr)
    return dict(stats=stats, pairs=list(pairs.values()), human=list(human.values()))


# ------------------------------------------------------------------ items (ported from build_items.py)
def tkey(hist, snap, lang, mpd, dekey):
    """target-language key: CUD ids are shared across languages; old-format RA ids are not, so align by (product, position)
    (verified in the research: Apr->Jun DE-unchanged limitations give identical FR 5498/5504, IT 5502/5504)."""
    if not dekey.startswith("RA:"): return dekey
    kd, kt = hist(snap, "de")["prod"][mpd]["keys"], hist(snap, lang)["prod"].get(mpd, {}).get("keys", [])
    return kt[kd.index(dekey)] if len(kd) == len(kt) else None


def sig(a, b):
    ta, tb = TOK.findall(a), TOK.findall(b)
    m = lambda xs: tuple(re.sub(r"\d", "#", x) for x in xs)  # digit-masked: the same boilerplate edit with different codes = one family
    return tuple((o, m(ta[i1:i2]), m(tb[j1:j2])) for o, i1, i2, j1, j2 in difflib.SequenceMatcher(None, ta, tb, autojunk=False).get_opcodes() if o != "equal")


def family(a, b): return hashlib.md5(repr(sig(a, b)).encode()).hexdigest()[:8]


def targets(hist, o):
    """FR/IT (old, new) for one DE change occurrence -> {lang: (old, new) | reason}."""
    ok = {}
    for lang in ("fr", "it"):
        A, B = hist(o["snap_old"], lang), hist(o["snap_new"], lang)
        ko, kn = tkey(hist, o["snap_old"], lang, o["mpd"], o["key_old"]), tkey(hist, o["snap_new"], lang, o["mpd"], o["key_new"])
        if o["key_old"] in hist(o["snap_old"], "de")["conflict"] or o["key_new"] in hist(o["snap_new"], "de")["conflict"]: ok[lang] = "conflict"; continue
        to, tn = A["lim"].get(ko), B["lim"].get(kn)
        if to is None or tn is None: ok[lang] = "missing"; continue
        to, tn = nrm(to), nrm(tn)
        if o["snap_old"] <= OLD_FORMAT_LAST and ("<" in to or "<" in tn): ok[lang] = "lt_bug"; continue
        if to == tn: ok[lang] = "tgt_unchanged"; continue
        ok[lang] = (to, tn)
    return ok


def build(pairs, hist, n=N, seed=SEED, maxch=MAXCH):
    """-> dict(stats, items (the seeded n DE pairs x fr/it), items_all (every eligible pair x fr/it), cands)."""
    st = Counter(); cands = []
    for p in pairs:
        st["de_pairs"] += 1
        if len(p["de_new"]) > maxch or len(p["de_old"]) > maxch: st["too_long"] += 1; continue
        best = None
        for o in p["occ"]:
            ok = targets(hist, o)
            if all(isinstance(v, tuple) for v in ok.values()): best = (o, ok); break
            best = best or (o, ok)
        o, ok = best
        reasons = [v for v in ok.values() if not isinstance(v, tuple)]
        if reasons:
            for r in set(reasons): st["excl_" + r] += 1
            continue
        cands.append(dict(p=p, o=o, ok=ok, sig=sig(p["de_old"], p["de_new"])))
    st["eligible"] = len(cands)
    clusters = defaultdict(list)
    for c in cands: clusters[c["sig"]].append(c)
    st["clusters"] = len(clusters)
    rng = random.Random(seed); keys = sorted(clusters, key=lambda s: hashlib.md5(repr(s).encode()).hexdigest()); rng.shuffle(keys)
    chosen = []
    for rnd in range(10):
        for k in keys:
            if len(chosen) >= n: break
            if len(clusters[k]) > rnd: chosen.append(clusters[k][rnd])
    fam = lambda c: hashlib.md5(repr(c["sig"]).encode()).hexdigest()[:8]
    items = []
    for i, c in enumerate(chosen):
        p, o = c["p"], c["o"]
        for lang in ("fr", "it"):
            to, tn = c["ok"][lang]
            items.append(dict(key=f"{i:02d}-{lang}", pair=i, lang=lang, de_old=p["de_old"], de_new=p["de_new"], tgt_old=to, tgt_new=tn,
                              cud_old=o["key_old"], cud_new=o["key_new"], snap_old=o["snap_old"], snap_new=o["snap_new"], product=o["name"],
                              cluster=fam(c), cluster_size=len(clusters[c["sig"]]), de_ratio=p["ratio"]))
    st["chosen_de"] = len(chosen); st["items"] = len(items)
    st["by_transition"] = dict(Counter(f'{c["o"]["snap_old"]}>{c["o"]["snap_new"]}' for c in chosen))
    ids = {id(c) for c in chosen}; allit = []
    for i, c in enumerate(cands):
        o = c["o"]
        for lang in ("fr", "it"):
            to, tn = c["ok"][lang]
            allit.append(dict(key=f"all{i:03d}-{lang}", lang=lang, de_old=c["p"]["de_old"], de_new=c["p"]["de_new"], tgt_old=to, tgt_new=tn,
                              cluster=fam(c), chosen=id(c) in ids, snap_old=o["snap_old"], snap_new=o["snap_new"],
                              cud_old=o["key_old"], cud_new=o["key_new"], product=o["name"], de_ratio=c["p"]["ratio"]))
    return dict(stats=dict(st), items=items, items_all=allit, cands=cands)


# ------------------------------------------------------------------ one month in operation
def _target(hist, o, lang):
    """-> ('ok', tgt_old, tgt_new or None) | (reason,) for one DE change occurrence and one target language. Unlike targets(),
    a target that BAG has not (yet) changed is not an exclusion: it is what the drafting lane is for."""
    if o["key_old"] in hist(o["snap_old"], "de")["conflict"] or o["key_new"] in hist(o["snap_new"], "de")["conflict"]: return ("conflict",)
    if not hist.has(o["snap_old"], lang): return ("no_snapshot",)
    ko = tkey(hist, o["snap_old"], lang, o["mpd"], o["key_old"])
    to = hist(o["snap_old"], lang)["lim"].get(ko) if ko else None
    if to is None: return ("missing_old_target",)
    to = nrm(to); tn = None
    if hist.has(o["snap_new"], lang):
        kn = tkey(hist, o["snap_new"], lang, o["mpd"], o["key_new"])
        tn = hist(o["snap_new"], lang)["lim"].get(kn) if kn else None
        tn = nrm(tn) if tn is not None else None
    if o["snap_old"] <= OLD_FORMAT_LAST and ("<" in to or "<" in (tn or "")): return ("lt_bug",)
    return ("ok", to, tn)


def item_key(cud, de_old, de_new, lang):
    """stable, unique item key: CUD id (filesystem/XML-safe, <= 40 chars) + 6 hex of the DE pair + language."""
    h = hashlib.md5((de_old + "\x00" + de_new).encode("utf-8")).hexdigest()[:6]
    c = re.sub(r"-{2,}", "-", re.sub(r"[^A-Za-z0-9.-]", "-", cud))[:40].strip("-")
    return f"{c}-{h}-{lang}"


REASONS = {"conflict": "the CUD id carries different texts in one snapshot", "no_snapshot": "no FR/IT snapshot for the old date",
           "missing_old_target": "no old FR/IT text under the same id", "lt_bug": "old-format snapshot with a '<' (publisher bug)"}


def month_items(hist, d_from, d_to, langs=("fr", "it")):
    """-> dict(items, unmatched, stats). items: one per distinct DE change x target language, each with tgt_old; > 60% and
    over-long changes are kept (the drafting step routes them to a human). unmatched: changes that cannot become an item."""
    check_snaps([d_from, d_to])
    C = mine(hist, [d_from, d_to], log=False)
    items, unmatched = [], []
    for p, rewrite in [(p, False) for p in C["pairs"]] + [(h, True) for h in C["human"]]:
        for lang in langs:
            best = None
            for o in p["occ"]:
                t = _target(hist, o, lang)
                if t[0] == "ok": best = (o, t); break
                best = best or (o, t)
            o, t = best
            base = dict(key=item_key(o["key_new"], p["de_old"], p["de_new"], lang), lang=lang, de_old=p["de_old"], de_new=p["de_new"],
                        change_ratio=p["ratio"], product=o["name"], mpd=o["mpd"], cud_old=o["key_old"], cud_new=o["key_new"],
                        snap_old=o["snap_old"], snap_new=o["snap_new"], family=family(p["de_old"], p["de_new"]), occurrences=len(p["occ"]))
            if t[0] != "ok":
                unmatched.append(dict(base, reason=REASONS.get(t[0], t[0]))); continue
            base["tgt_old"] = t[1]
            if t[2] is not None and t[2] != t[1]: base["tgt_new"] = t[2]                      # published: shadow-mode gold
            else: base["tgt_published"] = "unchanged" if t[2] is not None else "absent"
            items.append(base)
    items.sort(key=lambda x: x["key"])
    st = dict(snap_old=d_from, snap_new=d_to, de_changes=len(C["pairs"]), de_rewrites_over60=len(C["human"]), items=len(items),
              items_with_published_target=sum("tgt_new" in x for x in items), unmatched=len(unmatched),
              unmatched_reasons=dict(Counter(u["reason"] for u in unmatched)), step=C["stats"])
    return dict(items=items, unmatched=unmatched, stats=st)


def _dump(obj, path, indent=1):
    with open(path, "w", encoding="utf-8") as f: json.dump(obj, f, ensure_ascii=False, indent=indent)


def main(argv=None):
    ap = argparse.ArgumentParser(description="mine DE limitation changes and build FR/IT items from ePL snapshots")
    ap.add_argument("--hist", help="snapshot dir (default: $GLEICHLAUT_HIST or track_2b/out/hist)")
    ap.add_argument("--out", default=os.path.join(OUT, "sl"))
    ap.add_argument("--snaps", help="comma-separated YYYYMMDD snapshot dates (default: the research series " + ",".join(SNAPS) + ")")
    ap.add_argument("--from", dest="d_from", help="with --to: mine one step and write month items (month_items.json) instead")
    ap.add_argument("--to", dest="d_to")
    a = ap.parse_args(argv); H = Hist(hist_dir(a.hist)); os.makedirs(a.out, exist_ok=True)
    if bool(a.d_from) != bool(a.d_to): ap.error("--from and --to go together")
    try:
        if a.d_from:
            M = month_items(H, a.d_from, a.d_to)
            _dump(M["items"], os.path.join(a.out, "month_items.json")); _dump(M["unmatched"], os.path.join(a.out, "month_unmatched.json"))
            print(json.dumps(M["stats"], indent=1)); return
        snaps = check_snaps(a.snaps.split(",")) if a.snaps else SNAPS
    except (ValueError, FileNotFoundError) as e:
        ap.exit(2, f"error: {e}\n")
    C = mine(H, snaps)
    _dump(C, os.path.join(a.out, "changes_de.json"))
    B = build(C["pairs"], H)            # the seeded research selection (n=60 DE pairs); meaningful on the research series
    _dump(B["items"], os.path.join(a.out, "items.json")); _dump(B["items_all"], os.path.join(a.out, "items_all.json"), None)
    _dump(B["stats"], os.path.join(a.out, "pool_stats.json"))
    print(json.dumps(B["stats"], indent=1))


if __name__ == "__main__":
    main()
