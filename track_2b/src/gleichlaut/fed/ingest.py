"""Fedlex ingest: consolidated versions of an act (SPARQL) and their AKN XML (filestore) -> leaf units aligned by eId.

Thin port of the research code, executed from the vendored files: net.py (get, sparql: sha1-keyed cache, UA
hackapertus-research/0.1, >= 1.1 s between uncached requests), build_fed.py (QV, LM, versions, roots_for) via ast, and
units.py (AKN leaves, aligned_leaves) imported as is. Two deliberate differences, both outside the research code:
  * offline by default: a cache miss returns None and nothing is fetched. online=True (or GLEICHLAUT_FEDLEX_ONLINE=1)
    allows fetching; new responses go to GLEICHLAUT_FEDLEX_CACHE (default ~/.cache/gleichlaut/fedlex).
  * filestore URLs are fetched from www.fedlex.admin.ch/filestore: robots.txt disallows fedlex.data.admin.ch/filestore,
    the host SPARQL names (and the one the research run fetched from). Cache lookups try the URL as SPARQL returned it
    first, so the research cache (spikes/gleichschritt/cache, plus the older fedlex/leggasi caches) is used as is."""
import hashlib, importlib.util, json, os, sys, time, types, urllib.parse, urllib.request
from ..core import _extract, ROOT

RES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "research")
SPIKES = os.environ.get("GLEICHLAUT_SPIKES", os.path.join(os.path.dirname(os.path.dirname(ROOT)), "spikes"))
READ_CACHES = [os.path.join(SPIKES, d, "cache") for d in ("gleichschritt", "fedlex", "leggasi")]
WRITE_CACHE = os.environ.get("GLEICHLAUT_FEDLEX_CACHE", os.path.expanduser("~/.cache/gleichlaut/fedlex"))
DATA_FS, WWW_FS = "https://fedlex.data.admin.ch/filestore/", "https://www.fedlex.admin.ch/filestore/"


def _module(name):
    spec = importlib.util.spec_from_file_location("gleichschritt_" + name, os.path.join(RES, name + ".py"))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


U = _module("units")                  # pure stdlib, no side effects at import
common = _module("common")


class _Offline:
    class request:
        Request = urllib.request.Request
        @staticmethod
        def urlopen(*a, **k): raise ConnectionRefusedError("gleichlaut.fed.ingest is offline (online=True to fetch)")
    parse = urllib.parse


def www(url):
    return WWW_FS + url[len(DATA_FS):] if url.startswith(DATA_FS) else url


class Fedlex:
    def __init__(self, online=None, caches=None, write_cache=WRITE_CACHE):
        self.online = os.environ.get("GLEICHLAUT_FEDLEX_ONLINE") == "1" if online is None else online
        self.caches = [d for d in (caches if caches is not None else READ_CACHES) if os.path.isdir(d)]
        if self.online: os.makedirs(write_cache, exist_ok=True)
        log = os.path.join(write_cache, "net.log") if self.online else os.devnull
        N = {"hashlib": hashlib, "json": json, "os": os, "sys": sys, "urllib": urllib if self.online else _Offline,
             "time": time if self.online else types.SimpleNamespace(time=time.time, sleep=lambda s: None),
             "CACHE": write_cache, "OLD": self.caches, "LOG": log}
        self.N = _extract(os.path.join(RES, "net.py"), ("UA", "EP", "_last", "get", "sparql"), N)
        B = {"net": types.SimpleNamespace(get=self.get, sparql=self.N["sparql"]), "U": U, "json": json, "os": os}
        self.B = _extract(os.path.join(RES, "build_fed.py"), ("LM", "QV", "versions", "roots_for"), B)

    def cached(self, url, data=None):
        k = hashlib.sha1((url + (data or "")).encode()).hexdigest()       # net.py's cache key
        return any(os.path.exists(os.path.join(d, k)) for d in [self.N["CACHE"]] + self.caches)

    def get(self, url, data=None, accept=None):
        u = url if url == www(url) or self.cached(url, data) else www(url)
        return self.N["get"](u, data, accept)

    def versions(self, act):
        """act like 'cc/2011/28' -> {applicability date: {lang: AKN XML url}} (DE/FR/IT/RM)."""
        return self.B["versions"](act)

    def pairs(self, act, langs=("de", "fr", "it")):
        """consecutive consolidated versions that exist in all `langs` (build_fed.py's rule)."""
        v = self.versions(act)
        ds = sorted(d for d in v if all(l in v[d] for l in langs))
        return v, [(ds[i - 1], ds[i]) for i in range(1, len(ds))]

    def leaves(self, urls, langs):
        """{lang: url} -> {eId: {lang: text}} for leaves present in every language (footnotes stripped), or None."""
        roots = self.B["roots_for"](urls, langs)
        return None if roots is None else U.aligned_leaves(roots)
