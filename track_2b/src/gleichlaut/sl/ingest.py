"""BAG ePL FHIR NDJSON (one file per language and date) -> compact snapshot JSON {lim, prod, conflict}.

  lim:  {key: text}    key = CUD id (new format, May 2026+) or 'RA:<ra id>#<i>' (old format, limitationText in RA.indication)
  prod: {mpd id: {name, keys:[...]}}  limitations attached to each product bundle
  conflict: {key: [texts]}  the same key carrying different texts in one file

Texts are stored as published (byte-compatible with the research snapshots in spikes/gleichlaut/data/hist/, so those are a
drop-in); nrm() (html-unescape x2, nbsp/narrow spaces, whitespace) is applied on load by every consumer.
Publisher bug: the Feb-Apr 2026 (old format) and 4 May 2026 files drop every '<...>' span; May is excluded downstream and
old-format pairs containing '<' are dropped (sl.mine). The feed is streamed: nothing raw is stored unless --keep-raw is given.

The 'latest' feed is stored under its real publication date ({YYYYMMDD}-{lang}.json): the feed's own Bundle timestamp /
meta.lastUpdated if it carries one, else the HTTP Last-Modified of the file (as a Europe/Zurich date). latest-{lang}.json is
kept as an alias (symlink, or a copy where symlinks are unavailable) and latest.json records which date it points to and how
that date was established.

usage: python3 -m gleichlaut.sl.ingest 20261006 [20261001 ...|latest] [--out DIR] [--langs de,fr,it] [--keep-raw DIR]
       python3 -m gleichlaut.sl.ingest --file feed-de.ndjson --date 20261005 --lang de [--out DIR]"""
import argparse, datetime, email.utils, html, io, json, os, re, shutil, sys, time, urllib.request, urllib.error
from . import hist_dir

UA = "hackapertus-research/0.1"
BASE = "https://epl.bag.admin.ch/static"
LANGS = ("de", "fr", "it")
NEW_PATH_FROM = "20260825"     # the publisher moved the dated files on 25 Aug 2026 (results.md S3, HEAD scan)


def url(date, lang):
    """date 'YYYYMMDD' or 'latest'."""
    if date == "latest": return f"{BASE}/sl/publication/fhir/foph-sl-publication-latest-{lang}.ndjson"
    if date < NEW_PATH_FROM: return f"{BASE}/fhir/foph-sl-export-{date}-{lang}.ndjson"
    return f"{BASE}/sl/publication/fhir/foph-sl-publication-{date}-{lang}.ndjson"


def nrm(s):
    """ported from spikes/gleichlaut/s2/mine.py:nrm (NBSP, narrow NBSP, thin space -> space)."""
    s = html.unescape(html.unescape(s))
    s = s.replace(" ", " ").replace(" ", " ").replace(" ", " ")
    return re.sub(r"\s+", " ", s).strip()


TRANSLATION = "http://hl7.org/fhir/StructureDefinition/translation"


def translation(ext_holder, lang):
    """the FHIR translation extension of a primitive (`_text`, `_valueString`) for lang ('fr' matches 'fr-CH'), or None."""
    for e in (ext_holder or {}).get("extension", []) or []:
        if e.get("url") != TRANSLATION: continue
        sub = {x.get("url"): x for x in e.get("extension", []) or []}
        code = (sub.get("lang") or {}).get("valueCode") or ""
        if code.split("-")[0].lower() == lang: return (sub.get("content") or {}).get("valueString")
    return None


def _pick(obj, field, lang, file_lang):
    """the text of obj[field] in `lang`: the element itself if the file is in that language, else its translation extension."""
    if lang is None or lang == (file_lang or "de"): return obj.get(field)
    return translation(obj.get("_" + field), lang)


def extract(lines, meta=None, lang=None, file_lang=None):
    """ported from spikes/gleichlaut/s2/extract.py (stdin loop -> function). Reads both formats, so it works on every snapshot.
    meta: optional dict; receives 'feed_timestamp' (the latest Bundle timestamp / meta.lastUpdated, if the feed has any).
    lang / file_lang (ePL bridge, sl.epl): extract the texts in `lang` from a file written in `file_lang` (default de): the
    texts themselves when the languages agree, else their FHIR translation extensions; a text with neither is skipped.
    With lang None (the default) every text is taken as it stands (the public feed: one file per language)."""
    lim, prod, conflict = {}, {}, {}
    def put(k, t):
        if k in lim and lim[k] != t: conflict.setdefault(k, [lim[k]]).append(t)
        lim.setdefault(k, t)
    for line in lines:
        if not line.strip(): continue
        b = json.loads(line); mpd, name, keys = None, None, []
        if meta is not None:
            ts = b.get("timestamp") or (b.get("meta") or {}).get("lastUpdated")
            if ts and ts > meta.get("feed_timestamp", ""): meta["feed_timestamp"] = ts
        for e in b.get("entry", []):
            r = e["resource"]; rt = r["resourceType"]
            if rt == "MedicinalProductDefinition":
                mpd = mpd or r["id"]
                for n in r.get("name", []): name = name or n.get("productName")
            elif rt == "ClinicalUseDefinition":
                k = r["id"]; t = _pick(r["indication"]["diseaseSymptomProcedure"]["concept"], "text", lang, file_lang)
                if t is not None: put(k, t); keys.append(k)
            elif rt == "RegulatedAuthorization":
                i = 0
                for ind in r.get("indication", []) or []:
                    for ex in ind.get("extension", []):
                        if ex.get("url", "").endswith("regulatedAuthorization-limitation"):
                            for sub in ex.get("extension", []):
                                if sub.get("url") == "limitationText":
                                    k = f"RA:{r['id']}#{i}"; t = _pick(sub, "valueString", lang, file_lang); i += 1
                                    if t is not None: put(k, t); keys.append(k)
        if mpd:
            p = prod.setdefault(mpd, dict(name=name, keys=[]))
            for k in keys:
                if k not in p["keys"]: p["keys"].append(k)
    return dict(lim=lim, prod=prod, conflict=conflict)


def save(snap, path):
    with open(path, "w", encoding="utf-8") as f: json.dump(snap, f, ensure_ascii=False)
    print(path, len(snap["lim"]), "lims", len(snap["prod"]), "products", len(snap["conflict"]), "conflicts", file=sys.stderr)


MIN_INTERVAL = 1.0            # seconds between two requests to BAG (<= 1 request per second, every request type)
_last = [0.0]
def _open(u, tries=4, method="GET", headers=None):
    """polite request: >= MIN_INTERVAL s between requests, UA hackapertus-research/0.1, backoff on 429/5xx. Honours
    HTTPS_PROXY / NO_PROXY and an internal CA in SSL_CERT_FILE (backends.urlopen)."""
    from ..backends import urlopen
    for k in range(tries):
        time.sleep(max(0.0, MIN_INTERVAL - (time.time() - _last[0]))); _last[0] = time.time()
        try:
            return urlopen(urllib.request.Request(u, headers=dict({"User-Agent": UA}, **(headers or {})), method=method), timeout=120)
        except urllib.error.HTTPError as e:
            if e.code not in (429, 500, 502, 503, 504) or k == tries - 1: raise
            time.sleep(5 * 2 ** k)


class _Tee:
    def __init__(self, src, dst): self.src, self.dst = src, dst
    def __iter__(self):
        for line in self.src: self.dst.write(line); yield line


def _zurich_date(dt):
    try:
        from zoneinfo import ZoneInfo
        return dt.astimezone(ZoneInfo("Europe/Zurich")).strftime("%Y%m%d")
    except Exception:                                    # no tz database (slim images): UTC date
        return dt.astimezone(datetime.timezone.utc).strftime("%Y%m%d")


def publication_date(feed_timestamp=None, last_modified=None):
    """-> (YYYYMMDD or None, source). The feed's own timestamp wins; else the HTTP Last-Modified header."""
    if feed_timestamp:
        try:
            dt = datetime.datetime.fromisoformat(feed_timestamp.replace("Z", "+00:00"))
            return (_zurich_date(dt) if dt.tzinfo else dt.strftime("%Y%m%d")), "feed timestamp"
        except ValueError: pass
    if last_modified:
        try: return _zurich_date(email.utils.parsedate_to_datetime(last_modified)), "HTTP Last-Modified"
        except (TypeError, ValueError): pass
    return None, "unknown"


def alias_latest(out, date, lang):
    """latest-{lang}.json -> {date}-{lang}.json (relative symlink; a copy where symlinks are not available)."""
    dst, tmp = os.path.join(out, f"latest-{lang}.json"), os.path.join(out, f".latest-{lang}.json.tmp")
    if os.path.lexists(tmp): os.remove(tmp)
    try: os.symlink(f"{date}-{lang}.json", tmp)
    except (OSError, NotImplementedError): shutil.copyfile(os.path.join(out, f"{date}-{lang}.json"), tmp)
    os.replace(tmp, dst)


def fetch(date, lang, out, keep_raw=None):
    """stream one feed straight into extract(); the raw NDJSON is kept only if keep_raw (a directory outside data/) is given.
    date 'latest': stored under its publication date (publication_date) with a latest-{lang}.json alias -> (snap, date)."""
    u = url(date, lang); print("GET", u, file=sys.stderr); meta = {}
    with _open(u) as r:
        last_modified = r.headers.get("Last-Modified")
        lines = io.TextIOWrapper(r, encoding="utf-8")
        if keep_raw:
            os.makedirs(keep_raw, exist_ok=True)
            with open(os.path.join(keep_raw, os.path.basename(u)), "w", encoding="utf-8") as raw: snap = extract(_Tee(lines, raw), meta)
        else:
            snap = extract(lines, meta)
    os.makedirs(out, exist_ok=True)
    if date != "latest":
        save(snap, os.path.join(out, f"{date}-{lang}.json")); return snap, date
    pub, how = publication_date(meta.get("feed_timestamp"), last_modified)
    if pub is None:
        print(f"warning: no publication date for the latest {lang} feed (no feed timestamp, no Last-Modified); stored as "
              f"latest-{lang}.json only", file=sys.stderr)
        save(snap, os.path.join(out, f"latest-{lang}.json")); return snap, None
    save(snap, os.path.join(out, f"{pub}-{lang}.json")); alias_latest(out, pub, lang)
    p = os.path.join(out, "latest.json")
    try: rec = json.load(open(p, encoding="utf-8"))
    except (OSError, ValueError): rec = {}
    rec[lang] = dict(date=pub, source=how, last_modified=last_modified, feed_timestamp=meta.get("feed_timestamp"), url=u,
                     fetched=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"))
    with open(p, "w", encoding="utf-8") as f: json.dump(rec, f, ensure_ascii=False, indent=1)
    print(f"latest {lang} feed published {pub} ({how}) -> {pub}-{lang}.json, alias latest-{lang}.json", file=sys.stderr)
    return snap, pub


# ------------------------------------------------------------------ 2025 XML captures (Preparations.xml, DE/FR/IT side by side)
def fhir_id(code):
    """XML LimitationCode -> the CUD id the FHIR export uses for it (observed: 'DIAPHIN.6%' -> 'DIAPHIN.6-')."""
    return re.sub(r"[^A-Za-z0-9.\-]", "-", code or "")


def load_xml(path):
    """-> {fhir id: [dict(code, de, fr, it, product, pid)]} for every <Limitation> (product- and ItCode-level) in a
    Preparations.xml. Texts go through the frozen exporter emulation (frozen/build_fresh.py:untag, then nrm), so they compare
    with FHIR texts."""
    import xml.etree.ElementTree as ET
    from .. import core
    ns = core._extract(os.path.join(core.FROZEN, "build_fresh.py"), ("TAGS", "INLINE", "untag"), {"re": re, "nrm": nrm})
    untag = ns["untag"]; out = {}
    for _, el in ET.iterparse(path, events=("end",)):
        if el.tag != "Preparation": continue
        name = ((el.findtext("NameDe") or "") + " " + (el.findtext("DescriptionDe") or "")).strip()
        for lim in el.iter("Limitation"):
            code = lim.findtext("LimitationCode") or ""
            de, fr, it = (nrm(untag(lim.findtext(f"Description{x}") or "")) for x in ("De", "Fr", "It"))
            out.setdefault(fhir_id(code), []).append(dict(code=code, de=de, fr=fr, it=it, product=name, pid=el.get("ProductCommercial")))
        el.clear()
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("dates", nargs="*", help="YYYYMMDD or 'latest'")
    ap.add_argument("--out", help="snapshot dir (default: $GLEICHLAUT_HIST or track_2b/out/hist)")
    ap.add_argument("--langs", default=",".join(LANGS))
    ap.add_argument("--keep-raw", help="also keep the raw NDJSON here (never inside data/)")
    ap.add_argument("--file", help="extract a local NDJSON instead of downloading (needs --date, --lang)")
    ap.add_argument("--date"); ap.add_argument("--lang")
    a = ap.parse_args(argv); out = hist_dir(a.out)
    if a.file:
        if not (a.date and a.lang): ap.error("--file needs --date and --lang")
        with open(a.file, encoding="utf-8") as f: snap = extract(f)
        os.makedirs(out, exist_ok=True); save(snap, os.path.join(out, f"{a.date}-{a.lang}.json")); return
    if not a.dates: ap.error("give at least one date")
    for d in a.dates:
        for lang in a.langs.split(","): fetch(d, lang, out, a.keep_raw)


if __name__ == "__main__":
    main()
