"""Cached, rate-limited HTTP (UA hackapertus-research/0.1, >=1.1 s between uncached requests). stdlib only."""
import hashlib, json, os, sys, time, urllib.parse, urllib.request
UA = "hackapertus-research/0.1"
EP = "https://fedlex.data.admin.ch/sparqlendpoint"
H = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(H, "cache")
OLD = ["/Users/mi11ion/Desktop/hackapertus/spikes/fedlex/cache", "/Users/mi11ion/Desktop/hackapertus/spikes/leggasi/cache"]
LOG = os.path.join(H, "raw", "net.log")
_last = [0.0]
def get(url, data=None, accept=None):
    key = hashlib.sha1((url + (data or "")).encode()).hexdigest()
    for d in [CACHE] + OLD:
        p = os.path.join(d, key)
        if os.path.exists(p): return open(p, "rb").read()
    wait = 1.1 - (time.time() - _last[0])
    if wait > 0: time.sleep(wait)
    h = {"User-Agent": UA}
    if accept: h["Accept"] = accept
    req = urllib.request.Request(url, data=data.encode() if data else None, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=180) as r: body = r.read()
    except Exception as e:
        _last[0] = time.time(); open(LOG, "a").write(f"ERR {url} {e}\n"); return None
    _last[0] = time.time()
    open(os.path.join(CACHE, key), "wb").write(body)
    open(LOG, "a").write(f"GET {url} {len(body)}\n")
    return body
def sparql(q):
    b = get(EP, urllib.parse.urlencode({"query": q}), "application/sparql-results+json")
    return [] if b is None else json.loads(b)["results"]["bindings"]
