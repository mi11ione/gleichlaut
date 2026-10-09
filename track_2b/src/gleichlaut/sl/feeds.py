"""Which BAG ePL FHIR feed dates are published, and the `latest` / `previous` dates of `gleichlaut month`.

Sources (every request is spaced >= 1 s, User-Agent hackapertus-research/0.1, plain GET/HEAD to epl.bag.admin.ch):
  1. the SL app's resources API, GET https://epl.bag.admin.ch/api/sl/public/resources/current: fhir.fileUrl names the newest
     feed (e.g. sl/publication/fhir/foph-sl-publication-20261006-de.ndjson). The archive endpoint lists only Excel/XML.
  2. HEAD probes of the known file pattern (sl.ingest.url) for: the 1st of each of the last --months months (BAG publishes on
     the 1st), the research dates (sl.mine.SNAPS), the dates already in the snapshot dir, and the dates recorded earlier.
  3. --scan FROM TO: a HEAD for every day in the range (finds mid-month republications such as 6 Oct 2026; ~1 s per day).
Results are kept in <snapshot dir>/feeds.json. A published date is not probed again; a missing date is probed again until it
is 7 days in the past (a feed may appear on its date a little late). Future dates are never probed.

usage: gleichlaut feeds [--months 12] [--scan FROM TO] [--refresh] [--offline] [--snapshots DIR] [--json] [--latest]"""
import argparse, datetime, json, os, re, sys, urllib.error
from . import hist_dir, ingest, mine

API = "https://epl.bag.admin.ch/api/sl/public/resources/current"
SNAP_RX = re.compile(r"^(\d{8})-(de|fr|it)\.json$")


def _today(): return datetime.datetime.now(datetime.timezone.utc).date()
def _d(s): return datetime.date(int(s[:4]), int(s[4:6]), int(s[6:8]))
def _s(d): return d.strftime("%Y%m%d")
def _now(): return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def current():
    """-> dict(date, url, last_updated) of the newest FHIR feed according to BAG's resources API."""
    with ingest._open(API, tries=2, headers={"Accept": "application/json", "Accept-Language": "de"}) as r:
        d = json.load(r)
    f = (d or {}).get("fhir") or {}
    m = re.search(r"(\d{8})", f.get("fileUrl") or "")
    date = m.group(1) if m else (f.get("lastUpdated") or "").replace("-", "")[:8] or None
    if not date or not re.fullmatch(r"\d{8}", date): raise ValueError(f"the resources API gave no FHIR feed date: {f!r}")
    return dict(date=date, url=f.get("fileUrl"), last_updated=f.get("lastUpdated"))


def probe(date, lang="de"):
    """HEAD the feed file of one date -> dict(status, url, bytes, last_modified)."""
    u = ingest.url(date, lang)
    try:
        with ingest._open(u, tries=2, method="HEAD") as r:
            n = r.headers.get("Content-Length")
            return dict(status=getattr(r, "status", 200), url=u, bytes=int(n) if n and n.isdigit() else None,
                        last_modified=r.headers.get("Last-Modified"))
    except urllib.error.HTTPError as e:
        return dict(status=e.code, url=u)


def local_dates(hd):
    """-> {date: [langs]} of the snapshots in the snapshot dir."""
    out = {}
    if os.path.isdir(hd):
        for f in os.listdir(hd):
            m = SNAP_RX.match(f)
            if m: out.setdefault(m.group(1), []).append(m.group(2))
    return {d: sorted(v) for d, v in sorted(out.items())}


def _load(hd):
    try:
        with open(os.path.join(hd, "feeds.json"), encoding="utf-8") as f: c = json.load(f)
        return c if isinstance(c, dict) else {}
    except (OSError, ValueError): return {}


def _save(hd, c):
    os.makedirs(hd, exist_ok=True)
    tmp = os.path.join(hd, ".feeds.json.tmp")
    with open(tmp, "w", encoding="utf-8") as f: json.dump(c, f, ensure_ascii=False, indent=1, sort_keys=True)
    os.replace(tmp, os.path.join(hd, "feeds.json"))


def listing(hist=None, months=12, scan=None, refresh=False, net=True, today=None, log=None):
    """-> dict(published=[dates], local={date: langs}, latest, latest_source, excluded, probed, errors)."""
    hd = hist_dir(hist); c = _load(hd); D = c.setdefault("dates", {}); today = today or _today()
    errors, probed, latest, how = [], 0, None, None
    if net:
        try:
            cur = current(); latest, how = cur["date"], "BAG resources API"
            D[cur["date"]] = dict(D.get(cur["date"], {}), status=200, url=ingest.BASE.rstrip("/") + "/" + (cur["url"] or "").lstrip("/"),
                                  source="resources API", checked=_now())
            c["current"] = dict(cur, checked=_now())
        except (urllib.error.URLError, OSError, ValueError) as e:
            errors.append(f"resources API: {getattr(e, 'reason', None) or e}")
    cands = set(D) | set(local_dates(hd)) | set(mine.SNAPS)
    y, m = today.year, today.month
    for _ in range(max(0, months) + 1):
        cands.add(f"{y:04d}{m:02d}01"); y, m = (y, m - 1) if m > 1 else (y - 1, 12)
    if scan:
        a, b = _d(scan[0]), _d(scan[1])
        while a <= b: cands.add(_s(a)); a += datetime.timedelta(days=1)
    for d in sorted(cands):
        if not re.fullmatch(r"\d{8}", d) or _d(d) > today or d in mine.EXCLUDED: continue
        e = D.get(d)
        if e and not refresh:
            if e.get("status") == 200: continue
            chk = (e.get("checked") or "")[:10].replace("-", "")
            if chk and _d(chk) >= _d(d) + datetime.timedelta(days=7): continue
        if not net: continue
        try:
            r = probe(d)
        except (urllib.error.URLError, OSError) as e:
            errors.append(f"{d}: {getattr(e, 'reason', None) or e}"); continue
        D[d] = dict(r, source="HEAD probe", checked=_now()); probed += 1
        if log: print(f"  {d}: HTTP {r['status']}", file=log, flush=True)
    _save(hd, c)
    loc = local_dates(hd)
    pub = sorted(d for d, e in D.items() if e.get("status") == 200 and d not in mine.EXCLUDED)
    if latest is None:
        rec = c.get("current") or {}
        latest, how = (rec.get("date"), "resources API, as recorded " + str(rec.get("checked", "?"))[:10]) if rec.get("date") else \
                      ((pub[-1], "newest probed date") if pub else (None, None))
    return dict(published=pub, local=loc, latest=latest, latest_source=how, excluded=dict(mine.EXCLUDED), probed=probed,
                errors=errors, cache=os.path.join(hd, "feeds.json"))


def resolve_latest(hist=None, net=True):
    """-> (date, how). The resources API, else the date recorded by the last `ingest latest` / `feeds` run."""
    err = "offline"
    if net:
        try:
            cur = current(); return cur["date"], "BAG resources API (newest FHIR feed)"
        except (urllib.error.URLError, OSError, ValueError) as e:
            err = getattr(e, "reason", None) or e
    hd = hist_dir(hist)
    try:
        with open(os.path.join(hd, "latest.json"), encoding="utf-8") as f: rec = json.load(f)["de"]
        return rec["date"], f"{os.path.join(hd, 'latest.json')} (resources API unreachable: {err})"
    except (OSError, ValueError, KeyError, TypeError): pass
    c = (_load(hd).get("current") or {}).get("date")
    if c: return c, f"{os.path.join(hd, 'feeds.json')} (resources API unreachable: {err})"
    raise ValueError(f"cannot resolve 'latest': the BAG resources API is unreachable ({err}) and no earlier record exists in {hd}")


def month_runs(root):
    """-> [(snap_new, run dir)] of completed month runs (summary.json with mining.snap_new) under root."""
    out = []
    if os.path.isdir(root):
        for d in os.listdir(root):
            try:
                with open(os.path.join(root, d, "summary.json"), encoding="utf-8") as f: s = json.load(f)
                out.append((s["mining"]["snap_new"], os.path.join(root, d)))
            except (OSError, ValueError, KeyError, TypeError): continue
    return sorted(out)


def resolve_previous(to, hist=None, runs_root=None, net=True):
    """-> (date, how): where the last completed month run ended (so consecutive runs leave no gap, also across mid-month
    republications), else the newest published feed before `to`."""
    done = [(d, p) for d, p in month_runs(runs_root or "") if re.fullmatch(r"\d{8}", str(d)) and d < to]
    if done:
        d, p = done[-1]; return d, f"end of the last completed month run ({p})"
    L = listing(hist, months=3, net=net)
    pub = [d for d in sorted(set(L["published"]) | set(d for d, v in L["local"].items() if "de" in v)) if d < to and d not in mine.EXCLUDED]
    if pub: return pub[-1], "the newest published feed before " + to
    raise ValueError(f"cannot resolve 'previous' for --to {to}: no earlier month run and no earlier published feed found")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="gleichlaut feeds", description="list the published BAG ePL FHIR feed dates")
    ap.add_argument("--snapshots", help="snapshot dir (default $GLEICHLAUT_HIST or out/hist); feeds.json is kept there")
    ap.add_argument("--months", type=int, default=12, help="probe the 1st of each of the last N months (default 12)")
    ap.add_argument("--scan", nargs=2, metavar=("FROM", "TO"), help="also probe every day FROM..TO (YYYYMMDD; ~1 s per day)")
    ap.add_argument("--refresh", action="store_true", help="probe again what feeds.json already knows")
    ap.add_argument("--offline", action="store_true", help="no request: show what feeds.json and the snapshot dir know")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--latest", action="store_true", help="print only the newest published date (one request; for scripts)")
    a = ap.parse_args(argv)
    if a.latest:
        try: d, how = resolve_latest(a.snapshots, net=not a.offline)
        except ValueError as e: print(f"error: {e}", file=sys.stderr); return 6
        print(d); print(f"({how})", file=sys.stderr); return 0
    if a.scan and not all(re.fullmatch(r"\d{8}", x) for x in a.scan): ap.error("--scan takes two YYYYMMDD dates")
    if not a.offline: print("asking BAG (resources API + HEAD probes, <= 1 request/s) ...", file=sys.stderr, flush=True)
    L = listing(a.snapshots, a.months, a.scan, a.refresh, net=not a.offline, log=sys.stderr)
    if a.json: print(json.dumps(L, ensure_ascii=False, indent=1)); return 0
    allds = sorted(set(L["published"]) | set(L["local"]))
    print(f"{'date':10s} {'published':10s} {'local snapshots':16s} note")
    for d in allds:
        note = "latest (" + str(L["latest_source"]) + ")" if d == L["latest"] else ""
        if d in mine.EXCLUDED: note = "excluded: " + mine.EXCLUDED[d]
        print(f"{d:10s} {'yes' if d in L['published'] else '?':10s} {','.join(L['local'].get(d, [])) or '-':16s} {note}")
    for e in L["errors"]: print("warning:", e, file=sys.stderr)
    print(f"\n{len(L['published'])} published dates known ({L['probed']} probed now); cache {L['cache']}")
    if len(L["published"]) >= 2:
        print(f"e.g.  gleichlaut month --from {L['published'][-2]} --to {L['published'][-1]} --fetch      "
              f"or   gleichlaut month --from previous --to latest --fetch")
    return 0


if __name__ == "__main__":
    sys.exit(main())
