"""DEV ONLY (build machine). Re-run the frozen pipeline over a recorded item set with a backend that reads the development
gateway's local response cache (read-only; no network, no key) and copy every hit into data/cache/responses/.
A hit means the frozen code rebuilt the request payload byte-for-byte. Then compare the re-executed final records with
the recorded ones.  usage: python3 tools/harvest_cache.py ITEMS.json RECORDED_FINAL.jsonl [--write]"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from gleichlaut import core, backends
GW_CACHE = os.path.expanduser("~/.config/hackapertus/cache")
OUT = os.path.join(core.ROOT, "data", "cache", "responses")
items = json.load(open(sys.argv[1])); rec = {json.loads(l)["key"]: json.loads(l) for l in open(sys.argv[2])}
write = "--write" in sys.argv
hits, misses = [], []
def ask(prompt, tag, cap, max_tokens):
    h = backends.payload_key(core.M70, prompt, max_tokens, 0.0)
    p = os.path.join(GW_CACHE, h + ".json")
    if not os.path.exists(p): misses.append(h); raise KeyError(h)
    d = json.load(open(p)); hits.append(h)
    if write: backends.write_cache(OUT, h, d["text"], d.get("meta", {}))
    return backends.strip_think(d["text"]), dict(d.get("meta", {}), cached=True)
P = core.Pipeline(ask, "v2" if "--v2" in sys.argv else "g3")
diff = []
for x in items:
    try: r = P.run(x)
    except KeyError: diff.append((x["key"], "MISS")); continue
    o = rec[x["key"]]
    for f in ("out", "guard_flag", "rule_only", "reasked", "replaced", "retried", "lock_ok"):
        if r.get(f) != o.get(f): diff.append((x["key"], f, str(r.get(f))[:80], str(o.get(f))[:80]))
print("items", len(items), "calls hit", len(hits), "miss", len(misses), "unique keys", len(set(hits)))
print("records differing:", len(diff))
for d in diff[:20]: print(" ", d)
