"""PREREG R24: the shipped divergence audit on binding federal law. The seven federal acts behind the SL (KVG, KVV, KLV,
HMG, VAM, AMZV, VAZV), consolidated DE/FR/IT texts from Fedlex, aligned by structure (article / paragraph / letter /
item eId); every language version is equally binding (PublG, SR 170.512, Art. 14 para. 1).

This is an adapter only: it fetches and aligns. The checks are gleichlaut.audit's defaults, unchanged, run exactly as
gleichlaut.audit_lists runs MiGeL and the Analysenliste (number, unit, language, editorial; register statistics from the
corpus itself; no terminology pairs, they are mined from the SL; the round-5 module R15/R22 off). No model calls.

Units (R24 'Alignment'):
  (a) every AKN leaf with an eId (paragraph, item, list introduction; fed/research/units.py's leaf rule), key = eId;
  (b) every other text block (heading, p, table cell, block) that is not inside an (a) leaf and contains no element with
      an eId, key = the nearest ancestor's eId (or the document root) + its tag[index] path below that ancestor.
  Text: footnotes (authorialNote) and structural labels (num) left out; inline markup joined as rendered (no space is
  inserted inside a word, so '13<sup>a</sup>' stays '13a'), a space at block boundaries; whitespace as sl.ingest.nrm.
  A unit is aligned when its key exists, with text, in DE, FR and IT; the others are counted, not audited. Table guard
  (added after the fetch, on structure alone, before any check ran): the cells of a table are aligned only when the
  table has the same cell keys (rows x cells) in all three languages, so a row added in one language cannot shift the
  positional keys of the rows below it.

usage: python3 -m gleichlaut.audit_fedlex --fetch DIR            (online: SPARQL + filestore XML -> DIR, manifest)
       python3 -m gleichlaut.audit_fedlex --extract DIR          (DIR's XML -> data/fedlex_audit/texts_<date>.json.gz)
       python3 -m gleichlaut.audit_fedlex --run [--worklist DIR] (texts -> data/audit/audit_fedlex_<date>.json)"""
import argparse, gzip, hashlib, json, os, random, re, sys, time
from collections import Counter
import xml.etree.ElementTree as ET
from . import core

LANGS = ("de", "fr", "it")
DATA = os.path.join(core.ROOT, "data", "fedlex_audit")
MANIFEST = os.path.join(DATA, "manifest.json")
RUN_DATE = "2026-10-11"
TEXTS = os.path.join(DATA, "texts_20261011.json.gz")
OUT = os.path.join(core.ROOT, "data", "audit", "audit_fedlex_20261011.json")
SEED, SEED_T = 20261024, 20261025
# R24 corpus, fixed before any fetch (SR number, abbreviation, why it is in)
ACTS = (("832.10", "KVG", "Federal Act on Health Insurance; Art. 52 is the SL's basis"),
        ("832.102", "KVV", "Health Insurance Ordinance; Art. 64-75 SL procedure, Art. 71a-71d single cases"),
        ("832.112.31", "KLV", "FDHA Ordinance on Benefits; Art. 30-38 SL admission and prices; annexes as consolidated"),
        ("812.21", "HMG", "Therapeutic Products Act; Swissmedic authorisation is the first SL condition"),
        ("812.212.21", "VAM", "Medicinal Products Ordinance"),
        ("812.212.22", "AMZV", "Swissmedic Ordinance on authorisation requirements; product information"),
        ("812.212.23", "VAZV", "Swissmedic Ordinance on simplified authorisation"))
ABBR = {sr: a for sr, a, _ in ACTS}
Q_SR = """PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
SELECT ?a ?n ?st WHERE { ?a jolux:classifiedByTaxonomyEntry ?x . ?x skos:notation ?n . FILTER(STR(?n) IN (%s))
 FILTER(STRSTARTS(STR(?a), "https://fedlex.data.admin.ch/eli/cc/")) OPTIONAL { ?a jolux:inForceStatus ?st } }"""
IN_FORCE = "https://fedlex.data.admin.ch/vocabulary/enforcement-status/0"


# ------------------------------------------------------------------ fetch (online, once)
def fetch(dest, run_date=RUN_DATE):
    """SR -> in-force eli/cc work (SPARQL), its latest DE/FR/IT version applicable on or before run_date, the three AKN
    XML files from www.fedlex.admin.ch/filestore (robots.txt: fedlex.data.admin.ch disallows /filestore/*). UA
    hackapertus-research/0.1, >= 1.1 s between requests (the vendored net.py). -> manifest dict, XML files in dest."""
    from .fed.ingest import Fedlex, www
    os.makedirs(dest, exist_ok=True)
    F = Fedlex(online=True, caches=[], write_cache=os.path.join(dest, "cache"))
    works = {}
    for b in F.N["sparql"](Q_SR % ", ".join('"%s"' % sr for sr, _, _ in ACTS)):
        if b.get("st", {}).get("value") == IN_FORCE: works.setdefault(b["n"]["value"], []).append(b["a"]["value"].split("/eli/", 1)[1])
    man = dict(prereg="R24", run_date=run_date, user_agent="hackapertus-research/0.1", min_interval_s=1.1,
               robots=dict(checked="2026-10-11", **{"fedlex.data.admin.ch": "Disallow: /filestore/* (SPARQL endpoint allowed)",
                                                     "www.fedlex.admin.ch": "Allow: / (print views disallowed)"}),
               acts={})
    for sr, ab, why in ACTS:
        w = works.get(sr, [])
        if len(w) != 1: man["acts"][sr] = dict(abbr=ab, missing=f"{len(w)} in-force works"); continue
        v = F.versions(w[0]); ds = sorted(d for d in v if d <= run_date and all(L in v[d] for L in LANGS))
        if not ds: man["acts"][sr] = dict(abbr=ab, eli=w[0], missing="no DE/FR/IT version"); continue
        d = ds[-1]; files = {}
        for L in LANGS:
            body = F.get(v[d][L])
            if body is None: break
            open(os.path.join(dest, f"{sr}_{L}.xml"), "wb").write(body)
            files[L] = dict(url=www(v[d][L]), bytes=len(body), sha256=hashlib.sha256(body).hexdigest())
        man["acts"][sr] = dict(abbr=ab, why=why, eli=w[0], version=d, later_versions=sorted(x for x in v if x > run_date),
                               files=files, **({} if len(files) == 3 else dict(missing="fetch failed")))
    cd = os.path.join(dest, "cache"); mt = sorted(os.path.getmtime(os.path.join(cd, x)) for x in os.listdir(cd) if x != "net.log")
    iso = lambda s: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(s))
    man["fetch_window_utc"] = [iso(mt[0]), iso(mt[-1])]; man["requests"] = len(mt)
    json.dump(man, open(os.path.join(dest, "manifest.json"), "w"), ensure_ascii=False, indent=1)
    return man


# ------------------------------------------------------------------ extraction and alignment (R24 'Alignment')
LEAF = {"paragraph", "item", "listIntroduction"}
CONTAINER = {"paragraph", "item", "blockList", "list"}
BLOCKS_B = {"heading", "subheading", "p", "td", "th", "block"}
SPACED = {"p", "item", "listIntroduction", "blockList", "list", "td", "th", "tr", "table", "heading", "subheading", "br",
          "paragraph", "content", "intro", "wrapUp", "level", "article", "block", "container", "num"}
SKIP = {"authorialNote", "num", "meta"}


def _strip(root):
    for e in root.iter():
        if isinstance(e.tag, str) and "}" in e.tag: e.tag = e.tag.split("}", 1)[1]
    return root


def _text(e):
    out = [e.text or ""]
    for c in e:
        if not isinstance(c.tag, str): out.append(c.tail or ""); continue
        if c.tag not in SKIP:
            s = _text(c); out.append(" " + s + " " if c.tag in SPACED else s)
        out.append(c.tail or "")
    return "".join(out)


def clean(s):
    from .sl.ingest import nrm
    return nrm(re.sub(r"\s+", " ", s.replace("­", "")).strip())


def _is_leaf(e):
    if e.tag not in LEAF or not e.get("eId"): return False
    return not any(c.tag in CONTAINER and (c.get("eId") or c.tag in ("blockList", "list")) for c in list(e.iter())[1:])


def units(xml_bytes):
    """AKN XML -> {key: text}: (a) eId leaves, (b) other text blocks keyed by nearest eId ancestor + tag[index] path."""
    root = _strip(ET.fromstring(xml_bytes)); out = {}
    has_id = {}

    def mark(e):
        h = bool(e.get("eId"))
        for c in e:
            if isinstance(c.tag, str): h = mark(c) or h
        has_id[e] = h; return h
    mark(root)

    def walk(e, anchor, path):
        if e.tag in SKIP: return
        if _is_leaf(e):
            t = clean(_text(e))
            if t: out[e.get("eId")] = t
            return
        if e.tag in BLOCKS_B and not any(has_id[c] for c in e if isinstance(c.tag, str)) and not (e.get("eId")):
            t = clean(_text(e))
            if t: out[anchor + "/" + "/".join(path)] = t
            return
        seen = Counter()
        for c in e:
            if not isinstance(c.tag, str): continue
            k = f"{c.tag}[{seen[c.tag]}]"; seen[c.tag] += 1
            if c.get("eId"): walk(c, c.get("eId"), [])
            else: walk(c, anchor, path + [k])
    walk(root, "", [])
    return out


def ref(key):
    """'art_52_a/para_2_bis/lbl_b' -> 'Art. 52a para. 2bis let. b' (structural keys of (b) blocks keep their path)."""
    out = []
    for s in key.split("/"):
        m = re.fullmatch(r"art_(\d+)((?:_[a-z]+)*)", s)
        if m: out.append("Art. " + m.group(1) + m.group(2).replace("_", "")); continue
        m = re.fullmatch(r"para_(\d+)((?:_[a-z]+)*)", s)
        if m: out.append("para. " + m.group(1) + m.group(2).replace("_", "")); continue
        m = re.fullmatch(r"lbl_([a-z]+|\d+)((?:_[a-z]+)*)", s)
        if m: out.append(("no. " if m.group(1).isdigit() else "let. ") + m.group(1) + m.group(2).replace("_", "")); continue
        if s == "listintro": out.append("(intro)"); continue
        out.append(s)
    return " ".join(x for x in out if x)


TABLE = re.compile(r"^.*?/table\[\d+\]")


def extract(src, man=None):
    """the fetched XML (dir with manifest.json) -> texts dict: per act, the aligned units and the unaligned counts."""
    man = man or json.load(open(os.path.join(src, "manifest.json"), encoding="utf-8"))
    acts = {}
    for sr, a in man["acts"].items():
        if a.get("missing"): continue
        U = {}
        for L in LANGS:
            b = open(os.path.join(src, f"{sr}_{L}.xml"), "rb").read()
            assert hashlib.sha256(b).hexdigest() == a["files"][L]["sha256"], (sr, L)
            U[L] = units(b)
        common = [k for k in U["de"] if k in U["fr"] and k in U["it"]]
        tab = {L: {} for L in LANGS}                # table guard: a table's cells only when its cell keys agree in all three
        for L in LANGS:
            for k in U[L]:
                m = TABLE.match(k)
                if m: tab[L].setdefault(m.group(0), set()).add(k)
        bad = set(p for p in tab["de"] if not (tab["de"][p] == tab["fr"].get(p) == tab["it"].get(p)))
        guarded = [k for k in common if TABLE.match(k) and TABLE.match(k).group(0) in bad]
        common = [k for k in common if k not in set(guarded)]
        acts[sr] = dict(abbr=a["abbr"], version=a["version"],
                        units={L: len(U[L]) for L in LANGS}, aligned=len(common), table_guard=dict(tables=len(bad), cells=len(guarded)),
                        unaligned={L: len(set(U[L]) - set(common)) for L in LANGS},
                        unaligned_keys={L: sorted(set(U[L]) - set(common))[:30] for L in LANGS if set(U[L]) - set(common)},
                        texts={k: {L: U[L][k] for L in LANGS} for k in common})
    return dict(prereg="R24", run_date=man["run_date"], source="Fedlex consolidated AKN XML (official publication; public law)",
                manifest_sha256={sr: {L: f["sha256"] for L, f in a["files"].items()} for sr, a in man["acts"].items() if a.get("files")},
                acts=acts)


def load_texts(path=TEXTS):
    return json.load(gzip.open(path, "rt", encoding="utf-8"))


def write_texts(T, path=TEXTS):
    """deterministic gzip (mtime 0) so the committed bytes reproduce."""
    raw = json.dumps(T, ensure_ascii=False, indent=0, sort_keys=True).encode("utf-8")
    with open(path, "wb") as f:
        with gzip.GzipFile(filename="", mode="wb", fileobj=f, mtime=0) as g: g.write(raw)


# ------------------------------------------------------------------ the audit, unchanged (as audit_lists.run_list)
def to_J(T):
    """texts -> (J, names) in the shape audit.run_all reads: J[L]['lim'][key], key = '<SR>|<eId or path>'."""
    J = {L: dict(lim={}, prod={}, conflict={}) for L in LANGS}; names = {}
    for sr in sorted(T["acts"]):
        for k, t in sorted(T["acts"][sr]["texts"].items()):
            key = f"{sr}|{k}"
            for L in LANGS: J[L]["lim"][key] = t[L]
            names[key] = [T["acts"][sr]["abbr"]]
    return J, names


def run(T):
    """-> (findings, summary): audit.run_all(J, names, build_stats(J), pairs=[]) with r5 off: the shipped defaults."""
    from . import audit as A
    J, names = to_J(T)
    st = A.build_stats(J)
    ALL, S, XS = A.run_all(None, T["run_date"].replace("-", ""), J, names, st, pairs=[], r5=False)
    for f in ALL:
        f["act"], f["eid"] = f["id"].split("|", 1); f["abbr"] = ABBR[f["act"]]; f["ref"] = ref(f["eid"]); f.pop("known", None)
    K = Counter(f["kind"] for f in ALL); N = [f for f in ALL if f["kind"] == "number"]
    kinds = ("number", "unit", "language", "editorial")
    summ = dict(generated_by="python3 -m gleichlaut.audit_fedlex --run", prereg="R24", run_date=T["run_date"], model_calls=0,
                checks="audit.run_all defaults: number, unit, language, editorial; pairs=[] (no terminology); r5=False",
                n_units=S["n_limitations"], findings_all=len(ALL), by_kind={k: K.get(k, 0) for k in kinds},
                by_kind_lang={k: dict(Counter(f["lang"] for f in ALL if f["kind"] == k)) for k in kinds},
                by_act={ABBR[sr]: sum(f["act"] == sr for f in ALL) for sr in sorted(T["acts"])},
                units_by_act={ABBR[sr]: T["acts"][sr]["aligned"] for sr in sorted(T["acts"])},
                likely_equivalent=dict(number=sum(1 for f in N if f["likely_equivalent"]), of=len(N)),
                count_only_differences=S["count_only_differences"], unbound_differences=S["unbound_differences"],
                suppressed=S["suppressed"], **XS)
    return ALL, summ


# ------------------------------------------------------------------ blind worklist (R24 'Labels', R14 set-up)
def question(kind):
    from . import audit as A
    if kind == "number":
        return ("Do the German and the 'lang' text state a different condition for at least one of the values named in "
                "'finding'? Answer real / minor / not (same condition: formatting, rephrasing, unit conversion, parser artefact).")
    return A.QUESTION[kind]


def worklist(F, T, d):
    """every finding, shuffled (seed 20261024), neutral ids F00..., no rank / rule / fid / likely_equivalent."""
    order = list(range(len(F))); random.Random(SEED).shuffle(order)
    W, K = [], {}
    for j, i in enumerate(order):
        f = F[i]; w = f"F{j:02d}"; t = T["acts"][f["act"]]["texts"][f["eid"]]
        W.append(dict(id=w, act=f"SR {f['act']} {f['abbr']}", ref=f["ref"], kind=f["kind"], lang=f["lang"],
                      de=t["de"], fr=t["fr"], it=t["it"], finding=re.sub(r",? ?rule E\d\)", ")", f["description"]),
                      question=question(f["kind"])))
        K[w] = dict(key=f["id"], fid=f["fid"], kind=f["kind"], lang=f["lang"])
    os.makedirs(d, exist_ok=True)
    json.dump(W, open(os.path.join(d, "audit_fedlex_worklist.json"), "w"), ensure_ascii=False, indent=1)
    json.dump(dict(seed=SEED, ids=K), open(os.path.join(d, "audit_fedlex_key.json"), "w"), ensure_ascii=False, indent=1)
    return W, K


LAB = os.path.join(core.ROOT, "eval", "labels")
COLS = ("uid", "key", "act", "ref", "lang", "kind", "A", "B", "T", "final", "final_confirmed", "note_A", "note_B", "note_T")


def read_tsv(path):
    lines = open(path, encoding="utf-8").read().splitlines()
    return {c[0]: dict(ans=c[1].strip().lower(), note=c[2] if len(c) > 2 else "") for c in (l.split("\t") for l in lines[1:] if l.strip())}


def tiebreak(A, B, d=LAB):
    """R24: every finding where A and B answer differently -> a new shuffled worklist (seed 20261025, ids T00...)."""
    W = {w["id"]: w for w in json.load(open(os.path.join(d, "audit_fedlex_worklist.json"), encoding="utf-8"))}
    ids = sorted(i for i in W if A[i]["ans"] != B[i]["ans"]); random.Random(SEED_T).shuffle(ids)
    TW, TK = [], {}
    for j, i in enumerate(ids): TW.append(dict(W[i], id=f"T{j:02d}")); TK[f"T{j:02d}"] = i
    json.dump(TW, open(os.path.join(d, "audit_fedlex_tiebreak_worklist.json"), "w"), ensure_ascii=False, indent=1)
    json.dump(dict(seed=SEED_T, ids=TK), open(os.path.join(d, "audit_fedlex_tiebreak_key.json"), "w"), ensure_ascii=False, indent=1)
    return TW


def merge(d=LAB):
    """raw A/B/T labels + keys -> rows (COLS) by neutral id. final = the answer >= 2 of three share, else T's (A's when A
    and B agree); confirmed = real or minor; final_confirmed = majority of three on confirmed (R14)."""
    K = json.load(open(os.path.join(d, "audit_fedlex_key.json"), encoding="utf-8"))["ids"]
    W = {w["id"]: w for w in json.load(open(os.path.join(d, "audit_fedlex_worklist.json"), encoding="utf-8"))}
    A, B = read_tsv(os.path.join(d, "audit_fedlex_A.tsv")), read_tsv(os.path.join(d, "audit_fedlex_B.tsv"))
    tp = os.path.join(d, "audit_fedlex_T.tsv")
    T = read_tsv(tp) if os.path.exists(tp) else {}
    tk = json.load(open(os.path.join(d, "audit_fedlex_tiebreak_key.json"), encoding="utf-8"))["ids"] if T else {}
    Ti = {i: T[t] for t, i in tk.items()}
    conf = lambda a: "yes" if a in ("real", "minor") else "no"
    out = []
    for i in sorted(K):
        a, b, t = A[i], B[i], Ti.get(i)
        assert a["ans"] in ("real", "minor", "not") and b["ans"] in ("real", "minor", "not"), i
        if a["ans"] != b["ans"]:
            assert t, f"{i}: A and B differ and no tie-break label"
            cs = [a["ans"], b["ans"], t["ans"]]; fin = next((c for c in cs if cs.count(c) >= 2), t["ans"])
            fc = max(("yes", "no"), key=[conf(c) for c in cs].count)
        else:
            fin, fc = a["ans"], conf(a["ans"])
        out.append(dict(uid=i, key=K[i]["key"], act=W[i]["act"], ref=W[i]["ref"], lang=W[i]["lang"], kind=W[i]["kind"],
                        A=a["ans"], B=b["ans"], T=t["ans"] if t else "", final=fin, final_confirmed=fc,
                        note_A=a["note"], note_B=b["note"], note_T=t["note"] if t else ""))
    return out


def merged_lines(rows):
    return ["\t".join(COLS)] + ["\t".join(r[h].replace("\t", " ") for h in COLS) for r in rows]


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python3 -m gleichlaut.audit_fedlex")
    ap.add_argument("--fetch", metavar="DIR"); ap.add_argument("--extract", metavar="DIR")
    ap.add_argument("--run", action="store_true"); ap.add_argument("--worklist", metavar="DIR")
    ap.add_argument("--tiebreak", action="store_true", help="eval/labels A/B -> the tie-break worklist")
    ap.add_argument("--merge", action="store_true", help="eval/labels A/B/T -> eval/labels/audit_fedlex.tsv")
    a = ap.parse_args(argv)
    if a.tiebreak:
        print("tie-break:", len(tiebreak(read_tsv(os.path.join(LAB, "audit_fedlex_A.tsv")), read_tsv(os.path.join(LAB, "audit_fedlex_B.tsv")))), "records")
    if a.merge:
        open(os.path.join(LAB, "audit_fedlex.tsv"), "w", encoding="utf-8").write("\n".join(merged_lines(merge())) + "\n")
    if a.fetch:
        m = fetch(a.fetch)
        for sr, x in m["acts"].items(): print(sr, x["abbr"], x.get("version"), x.get("missing", "ok"))
    if a.extract:
        T = extract(a.extract); os.makedirs(DATA, exist_ok=True); write_texts(T)
        json.dump(json.load(open(os.path.join(a.extract, "manifest.json"), encoding="utf-8")), open(MANIFEST, "w"), ensure_ascii=False, indent=1)
        for sr, x in T["acts"].items(): print(sr, x["abbr"], x["version"], "aligned", x["aligned"], "unaligned", x["unaligned"])
    if a.run:
        T = load_texts(); F, S = run(T)
        json.dump(dict(summary=S, findings=F), open(OUT, "w"), ensure_ascii=False, indent=0)
        print(f"R24: {len(F)} findings {S['by_kind']} on {S['n_units']} aligned units -> {OUT}")
        if a.worklist: print("worklist:", len(worklist(F, T, a.worklist)[0]), "records ->", a.worklist)
    return 0


if __name__ == "__main__":
    sys.exit(main())
