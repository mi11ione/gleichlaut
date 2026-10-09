"""Check resources for guards G5-G7: rebuild them from your own corpus, and switch the checks to them.

  gleichlaut resources build --corpus my_texts.jsonl --out DIR [--fhir fr=FR.ndjson --fhir it=IT.ndjson] [--names fr=FILE]
  gleichlaut resources show                       which resources the checks use now (GLEICHLAUT_RESOURCES or the frozen ones)
  GLEICHLAUT_RESOURCES=DIR gleichlaut draft ...   draft / month / api use the resources in DIR

UNCERTIFIED: the frozen resources (src/gleichlaut/frozen/g3/*.json) are part of what the pre-registered tests measured
and what every certificate is bound to. With GLEICHLAUT_RESOURCES set, every certificate is void (the gate refuses them,
certify.verify / verify_build) and every draft goes to review. `make run` / `replay` ignore the variable: they reproduce the
frozen results.

The logic is that of frozen/g3/build_resources.py (the script that made the frozen files), without its hard-coded paths:
  whitelist_{fr,it}.json  lower-cased word tokens (>= 3 letters) of product names, substance names and ATC display names:
                          from ePL FHIR NDJSON feeds (--fhir L=PATH, as build_resources.py did), and/or plain name lists
                          (--names L=PATH, one name per line; or "names_fr" / "names_it" / "names" arrays in corpus lines)
  vocab_{fr,it}.json      token -> number of distinct target-language texts containing it (G5 / G7)
  terms_{fr,it}.json      DE -> FR/IT abbreviation map mined from aligned DE/FR/IT triples: per triple, abbreviations in the
                          German but not the target (D) and in the target but not the German (T), paired in order when
                          |D| == |T| >= 1; kept when seen >= 2 times, >= 60% of the abbreviation's pairings, A != B, and A
                          itself used in fewer than 5 target-language texts (G6)
Corpus: JSON Lines, one object per text unit: {"de": "...", "fr": "...", "it": "..."} (aligned; any language may be
missing), optionally "names_fr" / "names_it" / "names" (lists of product or substance names for the whitelist). Inline
HTML tags are removed and whitespace normalised as in the original script. Only languages fr and it exist (the guards'
own languages). A resource directory may hold only some of the six files; the others stay the frozen ones."""
import argparse, hashlib, json, os, re, sys
from collections import Counter, defaultdict

LANGS = ("fr", "it")
KINDS = ("whitelist", "vocab", "terms")
WORD = re.compile(r"[^\W\d_]+")
ABBR = re.compile(r"\b[A-Z][A-Z0-9]{1,5}(?:-[A-Z0-9]{1,4})?\b")
LCODE = {"fr": "fr-CH", "it": "it-CH"}
TAGS = re.compile(r"</?(?:br|p|ul|ol|li|div)\b[^<>]*>", re.I)
INLINE = re.compile(r"</?(?:b|i|u|strong|em|sup|sub|span|font)\b[^<>]*>", re.I)
_STATE = {"dir": None, "frozen": None, "swapped": []}


def _nrm(s):
    from .sl.ingest import nrm
    return nrm(s or "")


def untag(s): return TAGS.sub(" ", INLINE.sub("", _nrm(s)))


# ------------------------------------------------------------------ build
def whitelist_from_fhir(path, L):
    """the build_resources.py whitelist rule over one ePL FHIR NDJSON feed of language L."""
    W = set()
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.strip(): continue
            for e in json.loads(line).get("entry", []):
                r = e.get("resource") or {}; rt = r.get("resourceType")
                if rt == "MedicinalProductDefinition":
                    for n in r.get("name", []):
                        langs = [c.get("code") for u in n.get("usage", []) for c in (u.get("language") or {}).get("coding", [])]
                        if LCODE[L] in langs: W.update(w.lower() for w in WORD.findall(n.get("productName") or "") if len(w) >= 3)
                    for c in r.get("classification", []):
                        for cd in c.get("coding", []):
                            if "atc" in cd.get("system", ""): W.update(w.lower() for w in WORD.findall(cd.get("display") or "") if len(w) >= 3)
                elif rt == "Ingredient":
                    t = ((r.get("substance") or {}).get("code") or {}).get("concept", {}).get("text") or ""
                    W.update(w.lower() for w in WORD.findall(t) if len(w) >= 3)
    return W


def names_words(names):
    return {w.lower() for n in names for w in WORD.findall(n or "") if len(w) >= 3}


def read_corpus(path):
    """-> (set of (de, fr, it) triples, {L: [names]}). Raises ValueError with the line number on bad input."""
    triples, names = set(), {L: [] for L in LANGS}
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            if not line.strip(): continue
            try: o = json.loads(line)
            except ValueError as e: raise ValueError(f"{path}:{i}: not JSON ({e})")
            if not isinstance(o, dict): raise ValueError(f"{path}:{i}: expected an object with de / fr / it")
            for k in ("de", "fr", "it"):
                if k in o and not isinstance(o[k], str): raise ValueError(f"{path}:{i}: {k!r} must be a string")
            t = tuple(untag(o.get(k, "")) for k in ("de", "fr", "it"))
            if any(t): triples.add(t)
            for L in LANGS: names[L] += list(o.get(f"names_{L}") or []) + list(o.get("names") or [])
    return triples, names


def build(triples, whitelists):
    """-> {L: {"whitelist": sorted list, "vocab": {token: n}, "terms": {A: B}}} (the build_resources.py rules)."""
    out = {}
    for li, L in ((1, "fr"), (2, "it")):
        V = Counter(); P = defaultdict(Counter); AT = Counter()
        for t in triples:
            V.update({w.lower() for w in WORD.findall(t[li])}); AT.update(set(ABBR.findall(t[li])))
            de, tg = t[0], t[li]
            if not de or not tg: continue
            ad, at = ABBR.findall(de), ABBR.findall(tg)
            D = [a for a in dict.fromkeys(ad) if a not in set(at)]; T = [a for a in dict.fromkeys(at) if a not in set(ad)]
            if D and len(D) == len(T):
                for a, b in zip(D, T): P[a][b] += 1
        terms = {a: c.most_common(1)[0][0] for a, c in P.items()
                 if c.most_common(1)[0][1] >= 2 and c.most_common(1)[0][1] / sum(c.values()) >= 0.6 and c.most_common(1)[0][0] != a and AT[a] < 5}
        out[L] = dict(whitelist=sorted(whitelists.get(L, set())), vocab=dict(V), terms=dict(sorted(terms.items())))
    return out


def _sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f: h.update(f.read())
    return h.hexdigest()


def write(res, out, sources):
    os.makedirs(out, exist_ok=True); files = {}
    for L, d in res.items():
        for k in KINDS:
            if k == "whitelist" and not d[k]: continue          # no names given: keep the frozen whitelist
            p = os.path.join(out, f"{k}_{L}.json")
            with open(p, "w", encoding="utf-8") as f: json.dump(d[k], f, ensure_ascii=False, indent=0 if k == "terms" else None)
            files[os.path.basename(p)] = dict(sha256=_sha(p), n=len(d[k]))
    man = dict(generated_by="gleichlaut resources build", sources=sources, files=files, certified=False,
               note="uncertified: certificates are void with custom resources and every draft goes to review")
    with open(os.path.join(out, "manifest.json"), "w", encoding="utf-8") as f: json.dump(man, f, ensure_ascii=False, indent=1)
    return man


# ------------------------------------------------------------------ use (the hook)
def active():
    """the custom resource directory the checks use, or None (frozen resources)."""
    return _STATE["dir"]


def apply(directory=None):
    """swap guards3.WL / VOC / TERMS for the files in `directory` (default: $GLEICHLAUT_RESOURCES); with neither, restore the
    frozen resources. -> list of swapped file names. Frozen files are never written."""
    from . import core
    g = core.guards3
    if _STATE["frozen"] is None: _STATE["frozen"] = (g.WL, g.VOC, g.TERMS)
    d = directory if directory is not None else os.environ.get("GLEICHLAUT_RESOURCES") or None
    WL, VOC, TERMS = (dict(x) for x in _STATE["frozen"])
    swapped = []
    if d:
        if not os.path.isdir(d):
            from .backends import ConfigError
            raise ConfigError(f"GLEICHLAUT_RESOURCES={d!r} is not a directory (gleichlaut resources build --out DIR makes one)")
        for L in LANGS:
            for k, tgt, conv in (("whitelist", WL, set), ("vocab", VOC, dict), ("terms", TERMS, dict)):
                p = os.path.join(d, f"{k}_{L}.json")
                if os.path.exists(p):
                    with open(p, encoding="utf-8") as f: tgt[L] = conv(json.load(f))
                    swapped.append(os.path.basename(p))
        if not swapped:
            from .backends import ConfigError
            raise ConfigError(f"GLEICHLAUT_RESOURCES={d!r} holds none of whitelist_/vocab_/terms_{{fr,it}}.json")
    g.WL, g.VOC, g.TERMS = WL, VOC, TERMS
    _STATE["dir"] = os.path.abspath(d) if d else None; _STATE["swapped"] = swapped
    return swapped


def review_reason():
    return (f"custom check resources (GLEICHLAUT_RESOURCES={_STATE['dir']}): uncertified, every draft is reviewed"
            if _STATE["dir"] else None)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="gleichlaut resources", description="build or show the G5-G7 check resources (uncertified when custom)")
    sp = ap.add_subparsers(dest="cmd", required=True)
    b = sp.add_parser("build", help="rebuild whitelist / vocabulary / terms from a corpus")
    b.add_argument("--corpus", required=True, help="JSON Lines: {de, fr, it} per text unit (+ optional names_fr / names_it / names)")
    b.add_argument("--out", required=True)
    b.add_argument("--fhir", action="append", default=[], metavar="L=NDJSON", help="ePL FHIR feed of language L for the whitelist")
    b.add_argument("--names", action="append", default=[], metavar="L=FILE", help="one product / substance name per line, language L")
    sp.add_parser("show", help="which resources the checks use now")
    a = ap.parse_args(argv)
    if a.cmd == "show":
        sw = apply()
        print(f"custom resources from {active()}: {', '.join(sw)} (UNCERTIFIED: certificates void, every draft reviewed)" if sw
              else "frozen resources (src/gleichlaut/frozen/g3, hash-checked in eval/prereg/freeze.json)")
        return 0
    try:
        triples, names = read_corpus(a.corpus)
        W = {L: names_words(names[L]) for L in LANGS}
        src = dict(corpus=os.path.abspath(a.corpus), triples=len(triples), fhir={}, names={})
        for kind, specs in (("fhir", a.fhir), ("names", a.names)):
            for spec in specs:
                L, _, p = spec.partition("=")
                if L not in LANGS or not p: raise ValueError(f"--{kind} expects fr=PATH or it=PATH, got {spec!r}")
                if kind == "fhir": W[L] |= whitelist_from_fhir(p, L)
                else:
                    with open(p, encoding="utf-8") as f: W[L] |= names_words(f.read().splitlines())
                src[kind][L] = os.path.abspath(p)
    except (OSError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr); return 2
    if not triples: print(f"error: {a.corpus} holds no text", file=sys.stderr); return 2
    man = write(build(triples, W), a.out, src)
    for fn, d in sorted(man["files"].items()): print(f"  {fn:20s} {d['n']:7d} entries  sha256 {d['sha256'][:12]}")
    print(f"wrote {a.out} from {len(triples)} text units. Use it with GLEICHLAUT_RESOURCES={a.out} "
          "(UNCERTIFIED: every certificate is void and every draft goes to review).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
