"""Validation of the emitted files against vendored schemas (data/schemas/, sources and licences in its README.md).

XLIFF: the OASIS XLIFF 2.1 core XSD via lxml (the only non-stdlib dependency), plus the core-spec constraints the XSD
  cannot express and that apply here (the official Schematron is XSLT 2 and does not run under lxml): trgLang set when
  targets exist, subState only with an explicit state, unique unit / note / target-marker ids.
XLIFF 1.2: the OASIS XLIFF 1.2 strict XSD (its xml.xsd import resolved to the vendored W3C copy, no network), plus
  unique trans-unit ids per file.
FHIR: (a) parity with the real ePL feed: every path the draft CUD shares with the feed has the feed's JSON type, every
  path present in all feed CUDs is present, extra paths are only the declared additions (fhir.py), fullUrl, id rule and
  narrative rule as in the feed (data/schemas/epl-feed/cud_shape.json, written by --survey).
  (b) structure against StructureDefinition snapshots: CH EPL ch-idmp-clinicalusedefinition-indication 1.0.1 for the
  CUD (from the IG package), FHIR R5 base for Bundle, Provenance, Device and the datatypes used. Checked: unknown
  elements, cardinality, array vs single, primitive formats, choice types, pattern[x] / fixed[x], profile slices by value,
  required bindings on codes (vendored R5 CodeSystems; all-languages only by BCP-47 syntax), ele-1, ext-1, cud-1, the
  narrative is an XHTML div, unique fullUrls, every reference resolves inside the Bundle.
  Not checked: other FHIRPath invariants, non-required bindings, the definition of Gleichlaut's own extension. So this is
  a structural profile check, not the HL7 Java validator."""
import html, json, os, re, sys
import xml.etree.ElementTree as ET
from collections import Counter
from . import SCHEMAS, fhir, sha256_bytes

XSD = os.path.join(SCHEMAS, "xliff-2.1", "xliff_core_2.0.xsd")
XSD12 = os.path.join(SCHEMAS, "xliff-1.2", "xliff-core-1.2-strict.xsd")
XMLXSD = os.path.join(SCHEMAS, "xliff-2.1", "informativeCopiesOf3rdPartySchemas", "w3c", "xml.xsd")
XL12 = "{urn:oasis:names:tc:xliff:document:1.2}"
SHAPE = os.path.join(SCHEMAS, "epl-feed", "cud_shape.json")
XL = "{urn:oasis:names:tc:xliff:document:2.0}"


def _sha(p): return sha256_bytes(open(p, "rb").read())


# ------------------------------------------------------------------------------------------------------------ XLIFF
_xsd = None
def xliff_schema():
    global _xsd
    if _xsd is None:
        try: from lxml import etree
        except ImportError: raise SystemExit("validate: lxml is required for XLIFF XSD validation (pip install lxml)")
        _xsd = etree.XMLSchema(etree.parse(XSD))
    return _xsd


def validate_xliff(path):
    """-> list of errors (empty = valid against the XSD and the extra core constraints)."""
    from lxml import etree
    S = xliff_schema(); doc = etree.parse(path)
    errs = [f"XSD line {e.line}: {e.message}" for e in S.error_log] if not S.validate(doc) else []
    r = ET.parse(path).getroot()
    if r.find(f".//{XL}target") is not None and not r.get("trgLang"): errs.append("trgLang missing although targets exist")
    for f in r.iter(f"{XL}file"):
        ids = Counter(u.get("id") for u in f.iter(f"{XL}unit"))
        errs += [f"duplicate unit id {i}" for i, c in ids.items() if c > 1]
        for ns in f.iter(f"{XL}notes"):
            c = Counter(n.get("id") for n in ns if n.get("id"))
            errs += [f"duplicate note id {i}" for i, k in c.items() if k > 1]
        for u in f.iter(f"{XL}unit"):
            c = Counter(m.get("id") for t in u.iter(f"{XL}target") for m in t.iter() if m is not t)
            errs += [f"unit {u.get('id')}: duplicate target inline id {i}" for i, k in c.items() if k > 1]
            for s in u.iter(f"{XL}segment"):
                if s.get("subState") and not s.get("state"): errs.append(f"unit {u.get('id')}: subState without explicit state")
    return errs


_xsd12 = None
def xliff12_schema():
    """The OASIS XLIFF 1.2 strict XSD. It imports http://www.w3.org/2001/xml.xsd; that URL is resolved to the vendored
    copy and the parser may not touch the network."""
    global _xsd12
    if _xsd12 is None:
        try: from lxml import etree
        except ImportError: raise SystemExit("validate: lxml is required for XLIFF XSD validation (pip install lxml)")
        class Local(etree.Resolver):
            def resolve(self, url, pubid, ctx):
                if url and url.rstrip("/").endswith("xml.xsd"): return self.resolve_filename(XMLXSD, ctx)
        parser = etree.XMLParser(no_network=True); parser.resolvers.add(Local())
        _xsd12 = etree.XMLSchema(etree.parse(XSD12, parser))
    return _xsd12


def validate_xliff12(path):
    """-> list of errors (empty = valid against the XLIFF 1.2 strict XSD, plus: a target only with a valid state)."""
    from lxml import etree
    S = xliff12_schema(); doc = etree.parse(path)
    errs = [f"XSD line {e.line}: {e.message}" for e in S.error_log] if not S.validate(doc) else []
    r = ET.parse(path).getroot()
    if r.get("version") != "1.2": errs.append("not an XLIFF 1.2 document")
    for f in r.iter(f"{XL12}file"):
        ids = Counter(u.get("id") for u in f.iter(f"{XL12}trans-unit"))
        errs += [f"duplicate trans-unit id {i}" for i, c in ids.items() if c > 1]
    return errs


# ------------------------------------------------------------------------------------------------------------ FHIR (b)
PRIM = {"id": r"[A-Za-z0-9\-.]{1,64}", "code": r"[^\s]+( [^\s]+)*", "uri": r"\S*", "url": r"\S*", "canonical": r"\S*",
        "string": r"[\s\S]+", "markdown": r"[\s\S]+", "System.String": r"[\s\S]+",
        "instant": r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})",
        "dateTime": r"\d{4}(-\d{2}(-\d{2}(T\d{2}:\d{2}(:\d{2}(\.\d+)?)?(Z|[+-]\d{2}:\d{2}))?)?)?", "date": r"\d{4}(-\d{2}(-\d{2})?)?"}
BCP47 = re.compile(r"[a-z]{2,3}(-[A-Za-z0-9]{2,8})*")
XHTMLNS = "{http://www.w3.org/1999/xhtml}"


def _tcode(t):
    c = t["code"]
    if c.startswith("http://hl7.org/fhirpath/System."):
        return next((x["valueUrl"] for x in t.get("extension", []) if x["url"].endswith("structuredefinition-fhir-type")), "System.String")
    return c


class SD:
    def __init__(self, path):
        d = json.load(open(path, encoding="utf-8")); self.path, self.url, self.type = path, d["url"], d["type"]
        self.version = d.get("version"); self.el = {e["id"]: e for e in d["snapshot"]["element"]}
        self.kids = {}
        for i in self.el:
            if "." in i: self.kids.setdefault(i.rsplit(".", 1)[0], []).append(i)


class FhirValidator:
    """Snapshot-driven structural validator (see the module docstring for exactly what it covers)."""
    def __init__(self, root=SCHEMAS):
        self.base, self.prof, self.codes, self.files = {}, {}, {}, []
        for d, store in ((os.path.join(root, "fhir-r5"), self.base), (os.path.join(root, "ch-epl"), self.prof)):
            for fn in sorted(os.listdir(d)):
                if fn.endswith(".json") and (fn.endswith(".profile.json") or fn.startswith("StructureDefinition-")):
                    s = SD(os.path.join(d, fn)); self.files.append(s.path)
                    if store is self.base: store[s.type] = s
                    else: store[s.url] = s
        cs, td = {}, os.path.join(root, "fhir-r5", "terminology")
        for fn in sorted(os.listdir(td)):
            j = json.load(open(os.path.join(td, fn), encoding="utf-8")); self.files.append(os.path.join(td, fn))
            if j["resourceType"] == "CodeSystem":
                def flat(cc): return [c["code"] for c in cc] + [x for c in cc for x in flat(c.get("concept", []))]
                cs[j["url"]] = set(flat(j.get("concept", [])))
        for fn in sorted(os.listdir(td)):
            j = json.load(open(os.path.join(td, fn), encoding="utf-8"))
            if j["resourceType"] == "ValueSet":
                inc = j["compose"]["include"]
                if all(set(i) == {"system"} and i["system"] in cs for i in inc):   # whole-system value sets only
                    self.codes[j["url"]] = set().union(*(cs[i["system"]] for i in inc))
        self.codes_cs = cs

    def validate_bundle(self, b):
        errs = self.resource(b, "Bundle")
        full = Counter(e.get("fullUrl") for e in b.get("entry", []))
        errs += [f"Bundle: duplicate fullUrl {u}" for u, c in full.items() if c > 1]
        for k, e in enumerate(b.get("entry", [])):
            r, u = e["resource"], e.get("fullUrl", "")
            want = f"urn:uuid:{r.get('id')}" if u.startswith("urn:uuid:") else f"/{r['resourceType']}/{r.get('id')}"
            if not u.endswith(want): errs.append(f"entry[{k}]: fullUrl {u} does not name {r['resourceType']}/{r.get('id')}")
            for ref in _refs(r):
                if ref not in full: errs.append(f"entry[{k}] {r['resourceType']}/{r.get('id')}: reference {ref} not in the Bundle")
        return errs

    def resource(self, r, where):
        rt = r.get("resourceType"); decl = r.get("meta", {}).get("profile", [])
        errs = [f"{where}: declared profile {p} is not vendored" for p in decl if p not in self.prof]
        sds = [self.prof[p] for p in decl if p in self.prof] or ([self.base[rt]] if rt in self.base else [])
        if not sds: return errs + [f"{where}: no vendored StructureDefinition for {rt}"]
        errs += [f"{where}: profile {s.url} is for {s.type}, not {rt}" for s in sds if s.type != rt]
        for sd in sds:
            errs += self.node(r, sd, rt, f"{where}<{sd.url.rsplit('/', 1)[1]}>", root=True)
        if rt == "ClinicalUseDefinition" and sum(k in r for k in ("indication", "contraindication", "interaction", "undesirableEffect", "warning")) > 1:
            errs.append(f"{where}: cud-1 violated")
        return errs

    def node(self, obj, sd, eid, where, root=False):
        if not isinstance(obj, dict) or not obj: return [f"{where}: must be a non-empty object (ele-1)"]
        errs = []; kids = [k for k in sd.kids.get(eid, []) if ":" not in k[len(eid) + 1:]]
        byname = {k[len(eid) + 1:]: k for k in kids}
        seen = set()
        for key, val in obj.items():
            if root and key == "resourceType": continue
            el, tcode = self._child(sd, byname, key)
            if el is None: errs.append(f"{where}.{key}: unknown element"); continue
            seen.add(el["id"]); errs += self.values(val, el, tcode, sd, f"{where}.{key}")
        for k in kids:
            e = sd.el[k]
            if e["min"] > 0 and k not in seen: errs.append(f"{where}.{k[len(eid) + 1:]}: required (min {e['min']}) but missing")
        if sd.type == "Extension" and eid == "Extension":
            if ("extension" in obj) == any(k.startswith("value") for k in obj): errs.append(f"{where}: ext-1 (value[x] xor extension)")
        return errs

    def _child(self, sd, byname, key):
        if key in byname: e = sd.el[byname[key]]; return e, None
        for n, i in byname.items():
            if n.endswith("[x]") and key.startswith(n[:-3]):
                t = key[len(n) - 3:]; types = [_tcode(x) for x in sd.el[i].get("type", [])]
                m = next((x for x in types if x[:1].upper() + x[1:] == t), None)
                if m: return sd.el[i], m
        return None, None

    def values(self, val, el, tcode, sd, where):
        errs = []; mx = el["max"]; many = mx == "*" or int(mx) > 1
        if many != isinstance(val, list): errs.append(f"{where}: {'must' if many else 'must not'} be an array (max {mx})")
        items = val if isinstance(val, list) else [val]
        if not items: return errs + [f"{where}: empty array (ele-1)"]
        if mx != "*" and len(items) > int(mx): errs.append(f"{where}: {len(items)} > max {mx}")
        if len(items) < el["min"]: errs.append(f"{where}: {len(items)} < min {el['min']}")
        if el.get("slicing"): errs += self.slices(items, el, sd, where)
        for k, it in enumerate(items):
            w = f"{where}[{k}]" if isinstance(val, list) else where
            errs += self.value(it, el, tcode, sd, w)
        return errs

    def slices(self, items, el, sd, where):
        """slices by value discriminator (the CH EPL coding:SMC / coding:FOPH slices): count and validate members."""
        errs = []; disc = [d["path"] for d in el["slicing"]["discriminator"] if d["type"] in ("value", "pattern")]
        for sid, se in sd.el.items():
            if not sid.startswith(el["id"] + ":") or "." in sid[len(el["id"]) + 1:]: continue
            pats = {p: next((v for k, v in sd.el.get(f"{sid}.{p}", {}).items() if k.startswith(("pattern", "fixed"))), None) for p in disc}
            mem = [it for it in items if isinstance(it, dict) and all(pats[p] is not None and it.get(p) == pats[p] for p in disc)]
            if len(mem) < se["min"] or (se["max"] != "*" and len(mem) > int(se["max"])):
                errs.append(f"{where}: slice {sid.rsplit(':', 1)[1]} has {len(mem)} (card {se['min']}..{se['max']})")
            for it in mem: errs += self.node(it, sd, sid, f"{where}:{sid.rsplit(':', 1)[1]}")
        return errs

    def value(self, it, el, tcode, sd, where):
        errs = []
        if "contentReference" in el:
            return self.node(it, sd, el["contentReference"].split("#", 1)[1], where)
        types = [_tcode(t) for t in el.get("type", [])]
        t = tcode or (types[0] if len(types) == 1 else None)
        if t is None: return [f"{where}: ambiguous type {types}"]
        for k, v in el.items():
            if k.startswith("fixed") and it != v: errs.append(f"{where}: must equal fixed {v!r}")
            if k.startswith("pattern") and not _matches(it, v): errs.append(f"{where}: does not match pattern {v!r}")
        b = el.get("binding", {})
        if b.get("strength") == "required" and t == "code":
            vs = b["valueSet"].split("|")[0]
            if vs.endswith("/all-languages"):
                if not BCP47.fullmatch(str(it)): errs.append(f"{where}: {it!r} is not a BCP-47 language tag")
            elif vs not in self.codes: errs.append(f"{where}: required binding {vs} not vendored")
            elif it not in self.codes[vs]: errs.append(f"{where}: {it!r} not in {vs}")
        if t == "xhtml": return errs + _xhtml(it, where)
        if t in PRIM or t[:1].islower():
            if t == "boolean": ok = isinstance(it, bool)
            elif t in ("integer", "positiveInt", "unsignedInt", "integer64"): ok = isinstance(it, int) and not isinstance(it, bool)
            elif t == "decimal": ok = isinstance(it, (int, float)) and not isinstance(it, bool)
            else: ok = isinstance(it, str) and it != "" and re.fullmatch(PRIM.get(t, r"[\s\S]+"), it) is not None
            if not ok: errs.append(f"{where}: {it!r} is not a valid {t}")
            return errs
        if t == "Resource": return errs + self.resource(it, where)
        if any(":" not in k[len(el["id"]) + 1:] for k in sd.kids.get(el["id"], [])):
            return errs + self.node(it, sd, el["id"], where)      # inline children (backbone, or a datatype the profile expanded)
        if t not in self.base: return errs + [f"{where}: datatype {t} has no vendored StructureDefinition"]
        return errs + self.node(it, self.base[t], t, where)


def _matches(it, pat):
    if isinstance(pat, dict): return isinstance(it, dict) and all(k in it and _matches(it[k], v) for k, v in pat.items())
    if isinstance(pat, list): return isinstance(it, list) and all(any(_matches(i, p) for i in it) for p in pat)
    return it == pat


def _xhtml(s, where):
    try: d = ET.fromstring(s)
    except ET.ParseError as e: return [f"{where}: narrative is not well-formed XML ({e})"]
    if d.tag != XHTMLNS + "div": return [f"{where}: narrative root must be an XHTML div"]
    if any(x.tag.split("}")[-1] in ("script", "form", "base", "link", "xlink", "style", "head", "title") for x in d.iter()): return [f"{where}: forbidden XHTML element"]
    return []


def _refs(o):
    if isinstance(o, dict):
        for k, v in o.items():
            if k == "reference" and isinstance(v, str): yield v
            else: yield from _refs(v)
    elif isinstance(o, list):
        for v in o: yield from _refs(v)


# ------------------------------------------------------------------------------------------------------------ FHIR (a)
def paths(o, p=""):
    if isinstance(o, dict):
        for k, v in o.items(): yield from paths(v, f"{p}.{k}" if p else k)
    elif isinstance(o, list):
        for v in o: yield from paths(v, p + "[]")
    else: yield p, type(o).__name__


ADDED = ("meta.profile", "meta.tag", "language", "status.")     # the declared additions (fhir.py docstring)


def parity(b, shape):
    """CUD entries of an emitted Bundle vs the surveyed feed shape."""
    errs = []; P = {p: set(t) for p, t in shape["paths"].items()}; rx = re.compile(shape["id_regex"])
    for k, e in enumerate(b["entry"]):
        r = e["resource"]
        if r["resourceType"] != "ClinicalUseDefinition": continue
        w = f"entry[{k}] CUD {r.get('id')}"; got = dict(paths(r))
        for p, t in got.items():
            if p in P:
                if t not in P[p]: errs.append(f"{w}: {p} is {t}, the feed has {sorted(P[p])}")
            elif not p.startswith(ADDED): errs.append(f"{w}: {p} does not occur in the ePL feed and is not a declared addition")
        errs += [f"{w}: {p} is in every feed CUD but missing" for p in shape["always"] if p not in got]
        rid = str(r.get("id", "")); t = r.get("indication", {}).get("diseaseSymptomProcedure", {}).get("concept", {}).get("text")
        if e.get("fullUrl") != shape["fullUrl_base"] + rid: errs.append(f"{w}: fullUrl {e.get('fullUrl')} differs from the feed pattern")
        if not rx.fullmatch(rid): errs.append(f"{w}: id does not follow the feed's id rule")
        if not isinstance(t, str) or r.get("text", {}).get("div") != fhir.XHTML.format(html.escape(t, quote=False)):
            errs.append(f"{w}: narrative is not the escaped limitation text (the feed's rule)")
        if r.get("type") != "indication": errs.append(f"{w}: type {r.get('type')} (the feed has only indication)")
    return errs


def survey(ndjson_paths):
    """Stream ePL NDJSON files (one Bundle per line; never loaded whole) -> the CUD shape the parity check uses."""
    P, n, ids, files, fu, div, samples = {}, 0, set(), {}, Counter(), Counter(), {}
    always = None
    for path in ndjson_paths:
        h = __import__("hashlib").sha256(); nb = nc = 0
        with open(path, "rb") as fh:
            for line in fh:
                h.update(line); nb += 1
                if b'"ClinicalUseDefinition"' not in line: continue
                for e in json.loads(line)["entry"]:
                    r = e["resource"]
                    if r["resourceType"] != "ClinicalUseDefinition": continue
                    nc += 1; ids.add(r["id"]); got = dict(paths(r))
                    for p, t in got.items(): P.setdefault(p, Counter())[t] += 1
                    always = set(got) if always is None else always & set(got)
                    fu["base_ok" if e["fullUrl"] == fhir.EPL + "ClinicalUseDefinition/" + r["id"] else "other"] += 1
                    t = r["indication"]["diseaseSymptomProcedure"]["concept"]["text"]
                    div["escaped_text"] += r["text"]["div"] == fhir.XHTML.format(html.escape(t, quote=False))
                    lang = os.path.basename(path).rsplit("-", 1)[-1].split(".")[0]
                    if 120 < len(t) < 400 and lang not in samples: samples[lang] = e
        files[os.path.basename(path)] = dict(sha256=h.hexdigest(), bundles=nb, cud_entries=nc); n += nc
    return dict(source="BAG ePL FHIR feed (foph-sl-publication-latest-{de,fr,it}.ndjson, fetched 5 Oct 2026)", files=files,
                cud_entries=n, unique_ids=len(ids), paths={p: dict(c) for p, c in sorted(P.items())}, always=sorted(always or []),
                fullUrl_base=fhir.EPL + "ClinicalUseDefinition/", fullUrl=dict(fu), id_regex=r"[A-Za-z0-9\-.]{1,64}",
                ids_matching_regex=sum(bool(re.fullmatch(r"[A-Za-z0-9\-.]{1,64}", i)) for i in ids),
                narrative=dict(div, rule="div == <div xmlns=xhtml> + html.escape(text, quote=False) + </div>"), samples=samples)


# ------------------------------------------------------------------------------------------------------------ driver
def validate_files(fhir_paths, xliff_paths, xliff12_paths=()):
    """-> report dict; report["ok"] is False on any error. Lists the schema files (with sha256) each check used."""
    V = FhirValidator(); shape = json.load(open(SHAPE, encoding="utf-8")); rep = {"fhir": {}, "xliff": {}}
    if xliff12_paths: rep["xliff12"] = {os.path.basename(p): dict(errors=validate_xliff12(p)) for p in xliff12_paths}
    for p in fhir_paths:
        b = json.load(open(p, encoding="utf-8"))
        rep["fhir"][os.path.basename(p)] = dict(entries=len(b.get("entry", [])), profile_errors=V.validate_bundle(b), parity_errors=parity(b, shape))
    for p in xliff_paths: rep["xliff"][os.path.basename(p)] = dict(errors=validate_xliff(p))
    rel = lambda f: os.path.relpath(f, SCHEMAS)
    rep["schemas"] = dict(xliff=[{"file": rel(XSD), "sha256": _sha(XSD)}],
                          xliff12=[{"file": rel(f), "sha256": _sha(f)} for f in (XSD12, XMLXSD)],
                          fhir_profiles=[{"file": rel(f), "sha256": _sha(f)} for f in V.files], fhir_parity={"file": rel(SHAPE), "sha256": _sha(SHAPE)})
    rep["ok"] = not any(v.get("profile_errors") or v.get("parity_errors") or v.get("errors") for d in (rep["fhir"], rep["xliff"], rep.get("xliff12", {})) for v in d.values())
    return rep


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="validate emitted files, or survey the ePL feed for the parity shape")
    ap.add_argument("--survey", nargs="+", help="ePL NDJSON files to survey (writes --shape-out)")
    ap.add_argument("--shape-out", default=SHAPE)
    ap.add_argument("files", nargs="*", help=".fhir.json / .xlf files to validate")
    a = ap.parse_args()
    if a.survey:
        from . import dump_json
        s = survey(a.survey); dump_json(s, a.shape_out)
        print(f"surveyed {s['cud_entries']} CUD entries ({s['unique_ids']} ids) -> {a.shape_out}"); sys.exit(0)
    rep = validate_files([f for f in a.files if f.endswith(".json")], [f for f in a.files if f.endswith(".xlf") and not f.endswith(".xliff12.xlf")],
                         [f for f in a.files if f.endswith(".xliff12.xlf")])
    print(json.dumps(rep, indent=1, ensure_ascii=False)); sys.exit(0 if rep["ok"] else 1)
