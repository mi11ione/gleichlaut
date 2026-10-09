"""claims.tsv: every number in the README, the report, the video script and the form notes -> a results file + a path
in it + the command that produced it. This checker fails if a value drifts from its source, or (--scan) if a document
contains a number that is not a registered claim value (years, article numbers etc. are listed in ALLOW).

columns: id  value  source  path  fmt  command  where
  path  dotted path into the JSON (list indices as numbers; keys with spaces allowed), or 'len:<path>' for a length
  fmt   python format applied to the value at path, e.g. {:.1f} ; '{}' when the value is used verbatim
usage: python3 tools/claims.py [--scan FILE ...]"""
import json, os, re, sys
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
TSV = os.path.join(ROOT, "claims.tsv")


def get(d, path):
    if path.startswith("len:"): return len(get(d, path[4:]))
    for part in path.split("."):
        d = d[int(part)] if isinstance(d, list) else d[part]
    return d


def load():
    rows = []
    for i, l in enumerate(open(TSV, encoding="utf-8").read().splitlines()):
        if i == 0 or not l.strip() or l.startswith("#"): continue
        c = l.split("\t")
        rows.append(dict(zip(("id", "value", "source", "path", "fmt", "command", "where"), c)))
    return rows


def check(rows):
    bad = []
    for r in rows:
        try:
            d = json.load(open(os.path.join(ROOT, r["source"]), encoding="utf-8"))
            v = r["fmt"].format(get(d, r["path"]))
        except Exception as e:
            bad.append(f"{r['id']}: cannot resolve {r['source']}:{r['path']} ({type(e).__name__}: {e})"); continue
        if v != r["value"]: bad.append(f"{r['id']}: claims.tsv says {r['value']!r}, {r['source']}:{r['path']} gives {v!r}")
    return bad


NUM = re.compile(r"(?<![\w.])[+−-]?\d+(?:[.,]\d+)?(?![\w])")
ALLOW = re.compile(r"^(?:19|20)\d\d$|^[0-9]$|^1[0-2]$")   # years, small counts like "5 errors", "2 minutes" are claims too
                                                         # only when listed; bare digits 0-12 are allowed as prose


def scan(files, rows):
    vals = set()
    for r in rows:
        v = r["value"]; vals.add(v); vals.add(v.lstrip("+")); vals.add(v.replace("-", "−"))
    missing = []
    for f in files:
        txt = open(f, encoding="utf-8").read()
        txt = re.sub(r"```.*?```", "", txt, flags=re.S)             # code blocks are commands, not claims
        txt = re.sub(r"`[^`]*`", "", txt)                            # inline code (paths, hashes, ids)
        txt = re.sub(r"\]\([^)]*\)|https?://\S+", "", txt)            # link targets
        txt = re.sub(r"<!--\s*noclaim\s*-->.*?<!--\s*/noclaim\s*-->", "", txt, flags=re.S)
        txt = re.sub(r"(?m)^#+\s*[\d.]+", "", txt)                                        # section numbers
        txt = re.sub(r"XLIFF \d\.\d((?: and |/|, )\d\.\d)?", "", txt)                         # format versions
        txt = re.sub(r"(Apache-|CC-BY-|XLIFF |FHIR R|IG |PublG Art\. |Art\. |T |su-d-)[\d.]+", "", txt)   # versions, articles, table ids
        txt = re.sub(r"95% (CI|upper|confidence|Wilson)", "", txt)                           # the confidence level itself
        txt = re.sub(r"\*\*Team:\*\*[^\n]*|[Tt]eam 444", "", txt)                                 # team name
        txt = re.sub(r"95% (bound|interval)", "", txt)
        txt = re.sub(r"≤ ?5000 characters|≤ ?100 MB|< ?100 MB", "", txt)                       # form / template limits
        for m in NUM.finditer(txt):
            s = m.group(0).replace("−", "-")
            if ALLOW.match(s.lstrip("+-")) or s in vals or s.lstrip("+") in vals: continue
            line = txt.count("\n", 0, m.start()) + 1
            missing.append(f"{os.path.relpath(f, ROOT)}:{line}: {m.group(0)}")
    return missing


if __name__ == "__main__":
    rows = load(); bad = check(rows)
    for b in bad: print("DRIFT", b)
    miss = []
    if "--scan" in sys.argv:
        miss = scan(sys.argv[sys.argv.index("--scan") + 1:], rows)
        for m in miss: print("UNREGISTERED", m)
    print(f"claims: {len(rows)} registered, {len(bad)} drifted, {len(miss)} unregistered numbers")
    sys.exit(1 if bad or miss else 0)
