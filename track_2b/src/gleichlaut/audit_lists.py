"""The divergence audit on the other trilingual BAG lists with limitation columns: MiGeL (Mittel- und Gegenständeliste,
KLV Anhang 2) and the Analysenliste (AL, KLV Anhang 3). BAG publishes both as xlsx with one sheet per language; rows are
aligned by item number. The number, unit, language and editorial checks of gleichlaut.audit run on each text column
(MiGeL: Bezeichnung, Limitation; AL: Bezeichnung, Limitationen, Bemerkungen), with register statistics built from the
list itself. Stdlib only (zipfile + xml.etree); no model calls. Raw files stay outside the repo (docs/audit.md).

usage: python3 -m gleichlaut.audit --list migel|al --file PATH [--date YYYYMMDD] [--out data/audit] [--worklist DIR]"""
import hashlib, json, os, random, re, sys, zipfile
from collections import Counter
import xml.etree.ElementTree as ET

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
      "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
      "rel": "http://schemas.openxmlformats.org/package/2006/relationships"}


def _col(ref):
    n = 0
    for ch in re.match(r"[A-Z]+", ref).group(0): n = n * 26 + ord(ch) - 64
    return n - 1


def read_xlsx(path):
    """-> {sheet name: [[cell text, ...], ...]} (rows in sheet order; shared and inline strings; numbers as written)."""
    z = zipfile.ZipFile(path)
    ss = []
    if "xl/sharedStrings.xml" in z.namelist():
        for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", NS):
            ss.append("".join(t.text or "" for t in si.iter("{%s}t" % NS["m"])))
    wb = ET.fromstring(z.read("xl/workbook.xml"))
    rels = {r.get("Id"): r.get("Target") for r in ET.fromstring(z.read("xl/_rels/workbook.xml.rels")).findall("rel:Relationship", NS)}
    out = {}
    for s in wb.find("m:sheets", NS).findall("m:sheet", NS):
        tgt = rels[s.get("{%s}id" % NS["r"])].lstrip("/")
        tgt = tgt if tgt.startswith("xl/") else "xl/" + tgt
        rows = []
        for row in ET.fromstring(z.read(tgt)).iter("{%s}row" % NS["m"]):
            r = []
            for c in row.findall("m:c", NS):
                i = _col(c.get("r")); t = c.get("t"); v = c.find("m:v", NS)
                if t == "s" and v is not None: val = ss[int(v.text)]
                elif t == "inlineStr": val = "".join(x.text or "" for x in c.iter("{%s}t" % NS["m"]))
                else: val = v.text if v is not None and v.text is not None else ""
                while len(r) < i: r.append("")
                r.append(val)
            rows.append(r)
        out[s.get("name")] = rows
    return out


# ------------------------------------------------------------------ the lists
SOURCES = {
    "migel": dict(name="Mittel- und Gegenständeliste (MiGeL, KLV Anhang 2)", page="https://www.bag.admin.ch/de/mittel-und-gegenstaendeliste-migel",
                  file="https://www.bag.admin.ch/dam/de/sd-web/4GEgEMgJ45A6/Mittel-%20und%20Gegenst%C3%A4ndeliste%20per%201.%20Juli%202026%20(in%20Excel-Format).xlsx",
                  version="per 1. Juli 2026"),
    "al": dict(name="Analysenliste (AL, KLV Anhang 3)", page="https://www.bag.admin.ch/de/analysenliste-al",
               file="https://www.bag.admin.ch/dam/de/sd-web/a-xPwK6T1P0m/Analysenliste%20per%201.%20Juli%202026_Excel-Format.xlsx",
               version="per 1. Juli 2026")}
# per list: sheet name patterns (de, fr, it), the position header, the text columns (DE header -> field name)
LAYOUT = {"migel": dict(sheets=(r"\bD$", r"\bF$", r"\bI$"), pos=r"^Positions-Nr", cat=range(0, 7),
                        fields={"Bezeichnung": "Bezeichnung", "Limitation": "Limitation"}),
          "al": dict(sheets=(r"^Deutsch", r"^Fran", r"^Italian"), pos=r"^Pos\.-Nr", cat=range(0, 1),
                     fields={"Bezeichnung": "Bezeichnung", "Limitationen": "Limitation", "Bemerkungen": "Bemerkungen"})}
LANGS = ("de", "fr", "it")


def parse_list(kind, path):
    """xlsx -> (J, names, info): J[L]['lim'][key] = text with key '<position>|<field>', positions aligned by item number
    (MiGeL: Positions-Nr., or the deepest category code for group rows; AL: Pos.-Nr.); a repeated key gets '#n'."""
    from .sl.ingest import nrm
    lay = LAYOUT[kind]; S = read_xlsx(path); names = list(S)
    sheet = {L: next(n for n in names if re.search(rx, n.strip(), flags=re.I)) for L, rx in zip(LANGS, lay["sheets"])}
    rows = S[sheet["de"]]
    h = next(k for k, r in enumerate(rows) if any(re.search(lay["pos"], c.strip()) for c in r))
    head = [c.strip() for c in rows[h]]; pc = next(k for k, c in enumerate(head) if re.search(lay["pos"], c))
    cols = {f: head.index(c) for c, f in lay["fields"].items() if c in head}
    J = {L: dict(lim={}, prod={}, conflict={}) for L in LANGS}; per = {}; info = dict(sheets=sheet, header_row=h, columns={})
    for L in LANGS:
        R = S[sheet[L]]; hh = [c.strip() for c in R[h]] if len(R) > h else []
        info["columns"][L] = {f: (hh[c] if c < len(hh) else "") for f, c in cols.items()}
        seen = Counter(); keys = []
        for r in R[h + 1:]:
            cell = lambda k: (r[k] if k < len(r) else "").strip()
            pos = cell(pc) or next((cell(k) for k in reversed(lay["cat"]) if cell(k)), "")
            if not pos: continue
            seen[pos] += 1; key = pos if seen[pos] == 1 else f"{pos}#{seen[pos]}"; keys.append(key)
            for f, c in cols.items():
                t = nrm(cell(c))
                if t: J[L]["lim"][f"{key}|{f}"] = t
        per[L] = keys
    common = set(per["de"]) & set(per["fr"]) & set(per["it"])
    info.update(rows={L: len(per[L]) for L in LANGS}, positions_aligned=len(common),
                positions_unaligned={L: sorted(set(per[L]) - common)[:20] for L in LANGS if set(per[L]) - common})
    nm = {k: [k.split("|")[0]] for k in J["de"]["lim"]}
    return J, nm, info


def worklist_list(F, J, kind, d, n=40, seed=None):
    """seeded sample of up to n findings of every kind, blind (no rank, rule, fid or equivalence hint)."""
    from . import audit as A
    seed = A.SEED + (3 if kind == "migel" else 4) if seed is None else seed
    S = random.Random(seed).sample(F, min(n, len(F)))
    os.makedirs(d, exist_ok=True); W, K = [], {}; pre = "MG" if kind == "migel" else "AL"
    numq = ("Do the German and the 'lang' text state a different condition for at least one of the values named in "
            "'finding'? Answer real / minor / not (same condition: formatting, rephrasing, unit conversion, parser artefact).")
    for j, f in enumerate(S):
        w = f"{pre}{j:02d}"; pos, field = f["id"].split("|")
        W.append(dict(id=w, list=kind, position=pos, field=field, kind=f["kind"], lang=f["lang"],
                      de=J["de"]["lim"].get(f["id"], ""), fr=J["fr"]["lim"].get(f["id"], ""), it=J["it"]["lim"].get(f["id"], ""),
                      finding=re.sub(r",? ?rule E\d\)", ")", f["description"]),
                      question=numq if f["kind"] == "number" else A.QUESTION[f["kind"]]))
        K[w] = dict(list=kind, key=f["id"], fid=f["fid"], kind=f["kind"], lang=f["lang"], rule=f.get("rule"),
                    detected=f.get("detected"), likely_equivalent=f.get("likely_equivalent"), equivalence=f.get("equivalence"))
    json.dump(W, open(os.path.join(d, "worklist.json"), "w"), ensure_ascii=False, indent=1)
    json.dump(K, open(os.path.join(d, "key_map_DO_NOT_SHOW.json"), "w"), ensure_ascii=False, indent=1)
    return len(S)


def run_list(a):
    """`python -m gleichlaut.audit --list migel|al --file PATH [--date D] [--out DIR] [--worklist DIR]`: number, unit,
    language and editorial checks on the DE/FR/IT columns (no terminology: the pairs are mined from the SL)."""
    from . import audit as A
    if not a.file or not os.path.exists(a.file): sys.exit(f"--list {a.list}: give the list's xlsx with --file (not found: {a.file})")
    m = re.search(r"(20\d{6})", os.path.basename(a.file)); date = a.date or (m.group(1) if m else "unknown")
    J, names, info = parse_list(a.list, a.file)
    st = A.build_stats(J)
    ALL, S, XS = A.run_all(None, date, J, names, st, pairs=[])
    for f in ALL: f["position"], f["field"] = f["id"].split("|"); f.pop("known", None)
    K = Counter(f["kind"] for f in ALL); N = [f for f in ALL if f["kind"] == "number"]
    sha = hashlib.sha256(open(a.file, "rb").read()).hexdigest()
    kinds = ("number", "unit", "language", "editorial")
    summ = dict(generated_by=f"python3 -m gleichlaut.audit --list {a.list} --file <xlsx>", list=a.list, date=date, model_calls=0,
                source=dict(SOURCES[a.list], sha256=sha, bytes=os.path.getsize(a.file)), parse=info,
                n_fields=S["n_limitations"], n_fields_by_lang={L: len(J[L]["lim"]) for L in LANGS},
                fields_by_column=dict(Counter(k.split("|")[1] for k in J["de"]["lim"])),
                findings_all=len(ALL), by_kind={k: K.get(k, 0) for k in kinds},
                by_kind_lang={k: dict(Counter(f["lang"] for f in ALL if f["kind"] == k)) for k in kinds},
                by_kind_field={k: dict(Counter(f["field"] for f in ALL if f["kind"] == k)) for k in kinds},
                editorial_by_rule=dict(sorted(Counter(f["rule"] for f in ALL if f["kind"] == "editorial").items())),
                positions_with_finding=len(set(f["position"] for f in ALL)),
                likely_equivalent=dict(number=sum(1 for f in N if f["likely_equivalent"]), of=len(N)),
                count_only_differences=S["count_only_differences"], unbound_differences=S["unbound_differences"],
                suppressed=S["suppressed"], **XS)
    os.makedirs(a.out, exist_ok=True)
    out = os.path.join(a.out, f"audit_{a.list}_{date}.json")
    if a.worklist: summ["worklist"] = dict(n=worklist_list(ALL, J, a.list, a.worklist), pool=len(ALL))
    json.dump(dict(summary=summ, findings=ALL), open(out, "w"), ensure_ascii=False, indent=0)
    print(f"{a.list} {date}: {len(ALL)} findings {summ['by_kind']} on {summ['positions_with_finding']} positions "
          f"({S['n_limitations']} DE fields, {info['positions_aligned']} positions aligned); "
          f"{summ['likely_equivalent']['number']}/{len(N)} number findings likely equivalent -> {out}")
    return 1 if a.fail_on_findings and any(not f["likely_equivalent"] for f in ALL) else 0
