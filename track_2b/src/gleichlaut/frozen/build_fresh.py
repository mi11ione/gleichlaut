"""Fresh Gleichlaut test set from the two 2025 Wayback captures of XMLPublications.zip (BAG SL, releases 01.06.2025 and
01.07.2025; Preparations.xml). Each <Limitation> carries DE/FR/IT side by side, so FR/IT gold is aligned natively.
Mining = gleichlaut/s2/mine.py logic: per product (ProductCommercial id), DE texts gone from A vs new in B, greedy pairing by token
similarity, change ratio <= 0.6, spacing-only dropped. Exclusions = build_items.py: DE > 2500 chars, target text missing,
target unchanged (DE changed but FR/IT not), duplicate-key conflicts. ('<' rule not needed: the XML keeps '<'.)
Family = build_items.sig (digit-masked DE edit signature, md5[:8]); overlap reported against the 362-item 2026 pool.
usage: python3 -I build_fresh.py"""
import json, os, sys, re, hashlib, difflib
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
H = os.path.dirname(os.path.abspath(__file__)); G = "/Users/mi11ion/Desktop/hackapertus/spikes/gleichlaut"
sys.path.insert(0, f"{G}/s2")
from mine import nrm, TOK, change_ratio
MAXCH = 2500
SNAPS = [("20250601", f"{G}/data/wb2025/20250611/Preparations.xml"), ("20250701", f"{G}/data/wb2025/20250731/Preparations.xml"),
         ("20260219", f"{G}/data/hist/20260219")]   # earliest 2026 ePL FHIR snapshot (old format: drops '<...>' spans -> '<' pairs dropped)
NAME = lambda s: re.sub(r"\s+", " ", s or "").strip().lower()


def load_fhir(stem):
    """FHIR hist json -> same shape as load(): {product name: (name, {de: (fr, it, key)})}; FR/IT keys aligned by
    (product, position) as in build_items.tkey."""
    Jd, Jf, Ji = (json.load(open(f"{stem}-{l}.json")) for l in ("de", "fr", "it"))
    out = {}
    for m, p in Jd["prod"].items():
        kf, ki = Jf["prod"].get(m, {}).get("keys", []), Ji["prod"].get(m, {}).get("keys", [])
        if len(kf) != len(p["keys"]) or len(ki) != len(p["keys"]): continue
        T = {}
        for kd, a, b in zip(p["keys"], kf, ki):
            if kd in Jd["conflict"]: continue
            T.setdefault(nrm(Jd["lim"][kd]), (nrm(Jf["lim"].get(a, "")), nrm(Ji["lim"].get(b, "")), kd))
        out[m] = (p["name"] or "", T)
    return out


def sig(a, b):  # = build_items.sig
    ta, tb = TOK.findall(a), TOK.findall(b)
    m = lambda xs: tuple(re.sub(r"\d", "#", x) for x in xs)
    return tuple((o, m(ta[i1:i2]), m(tb[j1:j2])) for o, i1, i2, j1, j2 in difflib.SequenceMatcher(None, ta, tb, autojunk=False).get_opcodes() if o != "equal")


TAGS = re.compile(r"</?(?:br|p|ul|ol|li|div)\b[^<>]*>", re.I)                      # block tags -> space
INLINE = re.compile(r"</?(?:b|i|u|strong|em|sup|sub|span|font)\b[^<>]*>", re.I)       # inline tags -> nothing (m<sup>2</sup> = m2)
def untag(s):
    """XML limitation texts carry HTML formatting (<b>, <br>, lists); the FHIR export renders them as plain text. Strip formatting
    tags only (a literal '<' as in '<18 Jahre' is kept); nrm() then collapses whitespace."""
    s = TAGS.sub(" ", INLINE.sub("", nrm(s)))
    return s.replace("[", "").replace("]", "")   # the 2026 FHIR export drops square brackets (seen on IGA/del[17] texts)


CANON = lambda s: re.sub(r"[\W_]+", "", s).lower()   # format-only test: identical after removing punctuation and spacing


def load(path):
    """-> {product id: (name, {de_text: (fr, it, code)})}, conflicts (same DE text with different FR/IT in one product)"""
    out, conf = {}, 0
    for _, el in ET.iterparse(path, events=("end",)):
        if el.tag != "Preparation": continue
        pid = el.get("ProductCommercial"); name = (el.findtext("NameDe") or "") + " " + (el.findtext("DescriptionDe") or "")
        T = {}
        for lim in el.iter("Limitation"):
            de, fr, it = (nrm(untag(lim.findtext(f"Description{x}") or "")) for x in ("De", "Fr", "It"))
            if not de: continue
            v = (fr, it, lim.findtext("LimitationCode"))
            if de in T and T[de][:2] != v[:2]: T[de] = None; conf += 1; continue
            T.setdefault(de, v)
        out[pid] = (name.strip(), {k: v for k, v in T.items() if v is not None})
        el.clear()
    return out, conf


def byname(D):
    c = Counter(NAME(n) for n, _ in D.values())
    return {NAME(n): (n, T) for n, T in D.values() if c[NAME(n)] == 1}


S0, ca = load(SNAPS[0][1]); S1, cb = load(SNAPS[1][1]); S2_ = load_fhir(SNAPS[2][1])
st = Counter(conflicts_a=ca, conflicts_b=cb)
TRANS = [(SNAPS[0][0], SNAPS[1][0], byname(S0), byname(S1), False), (SNAPS[1][0], SNAPS[2][0], byname(S1), byname(S2_), True)]
pairs = {}
for sa, sb, A, B, ltrule in TRANS:
  common = set(A) & set(B); st[f"{sa}>{sb}_products_matched"] = len(common)
  st[f"{sa}>{sb}_texts_identical"] = sum(t in B[n][1] for n in common for t in A[n][1]); st[f"{sa}>{sb}_texts"] = sum(len(A[n][1]) for n in common)
  for pid in common:
    name, ta = A[pid]; _, tb = B[pid]
    gone = [t for t in ta if t not in tb]; new = [t for t in tb if t not in ta]
    if not gone or not new: continue
    cand = sorted(((change_ratio(g, n), g, n) for g in gone for n in new), key=lambda x: x[0])
    ug, un = set(), set()
    for r, g, n in cand:
        if g in ug or n in un: continue
        ug.add(g); un.add(n); st[f"{sa}>{sb}_matched"] += 1
        if r > 0.6: st[f"{sa}>{sb}_over60"] += 1; continue
        if TOK.findall(g) == TOK.findall(n): st[f"{sa}>{sb}_spacing_only"] += 1; continue
        if CANON(g) == CANON(n): st[f"{sa}>{sb}_excl_format_only"] += 1; continue
        if ltrule and "<" in g + n + "".join(ta[g][:2]) + "".join(tb[n][:2]): st[f"{sa}>{sb}_lt_bug"] += 1; continue
        if (g, n) in pairs: continue
        pairs[(g, n)] = dict(de_old=g, de_new=n, ratio=round(r, 3), occ=[dict(pid=pid, name=name, old=ta[g], new=tb[n], sa=sa, sb=sb)])
st["de_pairs"] = len(pairs)
pool = json.load(open(f"{G}/s2/items_all.json")); seen_fam = {x["cluster"] for x in pool}
used_fam_120 = {x["cluster"] for x in json.load(open(f"{G}/s2/items.json"))}
items = []
for i, p in enumerate(sorted(pairs.values(), key=lambda p: (p["de_old"], p["de_new"]))):
    if len(p["de_old"]) > MAXCH or len(p["de_new"]) > MAXCH: st["excl_too_long"] += 1; continue
    o = p["occ"][0]; fam = hashlib.md5(repr(sig(p["de_old"], p["de_new"])).encode()).hexdigest()[:8]
    for li, lang in ((0, "fr"), (1, "it")):
        to, tn = o["old"][li], o["new"][li]
        if not to or not tn: st[f"excl_missing"] += 1; continue
        if to == tn: st[f"excl_tgt_unchanged"] += 1; continue
        if CANON(to) == CANON(tn): st[f"excl_tgt_format_only"] += 1; continue
        items.append(dict(key=f"wb{i:03d}-{lang}", pair=f"wb{i:03d}", lang=lang, de_old=p["de_old"], de_new=p["de_new"], tgt_old=to, tgt_new=tn,
                          product=o["name"], code_old=o["old"][2], code_new=o["new"][2], snap_old=o["sa"], snap_new=o["sb"], de_ratio=p["ratio"],
                          cluster=fam, seen_family=fam in seen_fam, seen_in_120=fam in used_fam_120))
st["items"] = len(items); st["de_changes_with_items"] = len({x["pair"] for x in items})
st["families"] = len({x["cluster"] for x in items}); st["families_seen_in_2026_pool"] = len({x["cluster"] for x in items if x["seen_family"]})
st["items_in_seen_families"] = sum(x["seen_family"] for x in items); st["items_in_families_of_the_120"] = sum(x["seen_in_120"] for x in items)
st["lt_in_texts"] = sum("<" in x["tgt_old"] + x["tgt_new"] + x["de_old"] + x["de_new"] for x in items)
st["by_lang"] = dict(Counter(x["lang"] for x in items)); st["by_transition"] = dict(Counter(f'{x["snap_old"]}>{x["snap_new"]}' for x in items))
json.dump(items, open(f"{H}/items_fresh.json", "w"), ensure_ascii=False, indent=1)
json.dump(dict(st), open(f"{H}/fresh_stats.json", "w"), indent=1)
print(json.dumps(dict(st), indent=1))
