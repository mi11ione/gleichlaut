"""ePL bridge: an item file (docs/item-schema.json) from two ePL FHIR exports, the integration point for BAG's ePL team.

  gleichlaut items --from-fhir OLD NEW [--lang fr,it] --out items.json [--old-date YYYYMMDD] [--new-date YYYYMMDD]

OLD and NEW are ePL FHIR exports in the format of the public feed (NDJSON, one product Bundle per line, CH EPL profile:
MedicinalProductDefinition + ClinicalUseDefinition, or the older RegulatedAuthorization limitationText). Each side is
  - one German file whose French / Italian siblings sit next to it (foph-sl-publication-20261001-de.ndjson -> -fr / -it), or
  - a comma-separated list of files, one per language (language from the name '-de.' / '_fr.' / '.it.', else Bundle.language),
  - or one file carrying FR/IT as FHIR translation extensions (concept._text.extension[translation], lang fr-CH / it-CH).
NEW may also be a single draft Bundle (JSON, not NDJSON; a Bundle of product Bundles works too) in which only the German
changed: the pre-publication case. Items then carry tgt_old (the current FR/IT from OLD) and no tgt_new.

Pairing is sl.mine's: per product (MedicinalProductDefinition id, so the draft must keep the product's id), German texts gone
from OLD and new in NEW are paired by token similarity; > 60% changed = a rewrite (kept; `draft` routes it to a human). Item
keys are <CUD id>-<6 hex of the German pair>-<lang>, so re-running on the same change gives the same keys (resume).
Changes without an old FR/IT text under the same id go to <out>.unmatched.json. Nothing is sent anywhere."""
import argparse, json, os, re, shutil, sys, tempfile
from . import ingest, mine

LANG_RX = re.compile(r"[-_.](de|fr|it)\.(?:nd)?json$", re.I)
DATE_RX = re.compile(r"(?<!\d)(20\d{6})(?!\d)")


def bundles(path):
    """-> list of Bundle JSON strings (what ingest.extract reads) from NDJSON, one Bundle, a Bundle of Bundles, or an array."""
    with open(path, encoding="utf-8") as f: raw = f.read()
    try:
        doc = json.loads(raw)
    except ValueError:
        out = []
        for i, l in enumerate(raw.splitlines()):
            if not l.strip(): continue
            try: json.loads(l)
            except ValueError as e: raise ValueError(f"{path}: line {i + 1} is not JSON ({e})")
            out.append(l)
        return out
    docs = doc if isinstance(doc, list) else [doc]
    out = []
    for d in docs:
        if not isinstance(d, dict): raise ValueError(f"{path}: expected FHIR Bundles, found {type(d).__name__}")
        inner = [e.get("resource") for e in d.get("entry", []) or [] if (e.get("resource") or {}).get("resourceType") == "Bundle"]
        out += [json.dumps(b, ensure_ascii=False) for b in inner] if inner else [json.dumps(d, ensure_ascii=False)]
    return out


def file_lang(path, B):
    m = LANG_RX.search(os.path.basename(path))
    if m: return m.group(1).lower()
    for b in B[:1]:
        code = (json.loads(b).get("language") or "").split("-")[0].lower()
        if code in ("de", "fr", "it"): return code
    return None


def side(spec):
    """'a.ndjson[,b.ndjson...]' -> [(path, file language or None, bundles)], adding -fr/-it siblings of a lone -de file."""
    paths = [p for p in spec.split(",") if p]
    for p in paths:
        if not os.path.isfile(p): raise FileNotFoundError(f"FHIR export not found: {p}")
    if len(paths) == 1 and LANG_RX.search(os.path.basename(paths[0])) and LANG_RX.search(os.path.basename(paths[0])).group(1).lower() == "de":
        p = paths[0]; m = LANG_RX.search(os.path.basename(p))
        for L in ("fr", "it"):
            sib = os.path.join(os.path.dirname(p), os.path.basename(p)[: m.start(1)] + L + os.path.basename(p)[m.end(1):])
            if os.path.isfile(sib): paths.append(sib)
    out = []
    for p in paths:
        B = bundles(p); out.append((p, file_lang(p, B), B))
    return out


def snapshot(files, lang):
    """merge the texts in `lang` from every file of one side (its own language first, then translation extensions)."""
    snap = dict(lim={}, prod={}, conflict={}); meta = {}
    order = sorted(files, key=lambda f: (f[1] or "de") != lang)
    for path, fl, B in order:
        s = ingest.extract(B, meta, lang=lang, file_lang=fl or "de")
        for k, t in s["lim"].items(): snap["lim"].setdefault(k, t)
        for k, v in s["conflict"].items(): snap["conflict"].setdefault(k, v)
        for m, p in s["prod"].items():
            q = snap["prod"].setdefault(m, dict(name=p["name"], keys=[]))
            q["name"] = q["name"] or p["name"]
            for k in p["keys"]:
                if k not in q["keys"]: q["keys"].append(k)
    snap["prod"] = {m: p for m, p in snap["prod"].items() if p["keys"]}
    return snap, meta.get("feed_timestamp")


def _date(files, ts, given):
    if given: return given, True
    for p, _, _ in files:
        m = DATE_RX.search(os.path.basename(p))
        if m: return m.group(1), True
    if ts:
        d, _ = ingest.publication_date(ts)
        if d: return d, True
    return None, False


def build(old, new, langs=("fr", "it"), old_date=None, new_date=None):
    """-> dict(items, unmatched, stats) as sl.mine.month_items, from two exports (see the module doc)."""
    O, N = side(old), side(new)
    snaps = {}
    for tag, files in (("old", O), ("new", N)):
        for L in ("de",) + tuple(langs):
            snaps[(tag, L)] = snapshot(files, L)
    if not snaps[("old", "de")][0]["lim"]: raise ValueError(f"no German limitation text found in {old}")
    if not snaps[("new", "de")][0]["lim"]: raise ValueError(f"no German limitation text found in {new}")
    d1, real1 = _date(O, snaps[("old", "de")][1], old_date)
    d2, real2 = _date(N, snaps[("new", "de")][1], new_date)
    if not (real1 and real2 and d1 < d2):                 # undated draft, or same day: synthetic, increasing, post-May-2026 dates
        d1, d2, real1, real2 = "20990101", "20990102", False, False
    tmp = tempfile.mkdtemp(prefix="gl-epl-")
    try:
        for (tag, L), (s, _) in snaps.items():
            if s["lim"]: ingest.save(s, os.path.join(tmp, f"{d1 if tag == 'old' else d2}-{L}.json"))
        M = mine.month_items(mine.Hist(tmp), d1, d2, langs)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    label = {d1: (old_date or d1) if real1 else None, d2: (new_date or d2) if real2 else None}
    for x in M["items"] + M["unmatched"]:
        for f in ("snap_old", "snap_new"):
            if label.get(x.get(f)) is None: x.pop(f, None)
    published = {L: bool(snaps[("new", L)][0]["lim"]) for L in langs}
    M["stats"].update(source="ePL FHIR exports", old=[p for p, _, _ in O], new=[p for p, _, _ in N],
                      new_has_targets=published, mode="shadow" if any(published.values()) else "pre-publication")
    if not real1 or not real2: M["stats"].update(snap_old=None, snap_new=None)
    return M


def main(argv=None):
    ap = argparse.ArgumentParser(prog="gleichlaut items", description="build an item file from two ePL FHIR exports (sl.epl)")
    ap.add_argument("--from-fhir", nargs=2, metavar=("OLD", "NEW"), required=True,
                    help="old and new export (NDJSON, or NEW as one draft Bundle); comma-separate per-language files")
    ap.add_argument("--lang", default="fr,it", help="target languages (default fr,it)")
    ap.add_argument("--out", required=True, help="items file to write (JSON array); unmatched changes go to <out>.unmatched.json")
    ap.add_argument("--old-date"); ap.add_argument("--new-date")
    a = ap.parse_args(argv)
    langs = tuple(L.strip() for L in a.lang.split(",") if L.strip())
    if not langs or any(L not in ("fr", "it") for L in langs): ap.error("--lang takes fr, it or fr,it")
    for d in (a.old_date, a.new_date):
        if d and not re.fullmatch(r"\d{8}", d): ap.error("--old-date / --new-date are YYYYMMDD")
    M = build(a.from_fhir[0], a.from_fhir[1], langs, a.old_date, a.new_date)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f: json.dump(M["items"], f, ensure_ascii=False, indent=1)
    um = os.path.splitext(a.out)[0] + ".unmatched.json"
    with open(um, "w", encoding="utf-8") as f: json.dump(M["unmatched"], f, ensure_ascii=False, indent=1)
    st = M["stats"]
    print(f"{st['mode']}: {st['de_changes']} German changes (+{st['de_rewrites_over60']} > 60% rewrites) -> {len(M['items'])} items "
          f"in {a.out} ({st['items_with_published_target']} with a published target); {len(M['unmatched'])} without an old "
          f"FR/IT text -> {um}")
    if M["items"]: print(f"next: gleichlaut draft --items {a.out} --out out/draft/{os.path.splitext(os.path.basename(a.out))[0]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
