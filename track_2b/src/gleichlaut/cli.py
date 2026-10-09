"""gleichlaut <command>

  run        what `make run` executes: replay (freeze, re-execution, re-scoring), live slice, emit + validate, review UI
  replay     steps 1-3 only (`--write` regenerates eval/results after a deliberate change)
  certify    certify an endpoint on the frozen fresh-166 suite, or `--canary` it (see gleichlaut.certify)
  month      one month in operation: --from YYYYMMDD --to YYYYMMDD [--snapshots DIR] [--fetch]  (shadow mode on the public
             feed), or --items FILE (pre-publication: the SL team's own German changes); mines, routes, drafts, summarises
  draft      draft FR/IT for an item file (docs/item-schema.json) through a backend; resumable records + summary
  live       the live slice alone (5 Fedlex items) through LLM_BASE_URL or a local GGUF
  emit, ui   XLIFF 2.1 / FHIR and the review page (over a recorded run; --records/--items where the build supports them)
  fetch-gguf download the pinned Apertus 8B GGUF and verify its sha256

Routing (vision §3): corpus fedlex -> 8B, every draft reviewed; corpus sl -> 70B on a certified endpoint (exact endpoint +
model, `gleichlaut certify`), or any model with --air-gapped, in which case every item is marked for review whatever the
guards say. Items whose German changed > 60% of its tokens, or longer than 2500 characters, go to a human.

Exit codes: 0 ok | 1 reproduction or validation failed | 2 usage / bad input / missing configuration | 3 canary outside
tolerance | 4 refused: endpoint not certified | 5 certificate FAIL | 6 endpoint or feed failed (records so far are kept;
re-run to resume) | 7 certificate PENDING_REVIEW | 130 interrupted.  GLEICHLAUT_DEBUG=1 shows tracebacks."""
import argparse, datetime, inspect, json, os, re, sys, time, urllib.error, urllib.request
from collections import Counter
from . import core, backends

GGUF_URL = os.environ.get("GLEICHLAUT_MODEL_URL",
                          "https://huggingface.co/Colby/apertus-v1.5-8b-text-Q4_K_M-GGUF/resolve/main/apertus-v1.5-8b-text-q4_k_m.gguf")
GGUF_SHA = os.environ.get("GLEICHLAUT_MODEL_SHA256", "a037df8d87ff6caacee794ee85f55342f2152e0d359b7389033300c3bee5f299")
MODELS = os.environ.get("GLEICHLAUT_MODELS", os.path.join(core.ROOT, "models"))
OUT = os.environ.get("GLEICHLAUT_OUT", os.path.join(core.ROOT, "out"))
SCHEMA = os.path.join(core.ROOT, "docs", "item-schema.json")
MAXRATIO, MAXCH = 0.60, 2500                 # = sl.mine.MAXRATIO / MAXCH (the evaluated range)
CHF_PER_MTOK = (0.70, 2.50)                  # Swiss provider's published price, CHF per million input / output tokens (score.economics)
EXIT_OK, EXIT_FAIL, EXIT_USAGE, EXIT_CANARY, EXIT_UNCERTIFIED, EXIT_CERT_FAIL, EXIT_ENDPOINT, EXIT_PENDING = range(8)


class UsageError(Exception):
    """bad arguments or input files: one-line message, exit 2."""


class Uncertified(Exception):
    """the SL lane was asked to draft through an endpoint without a PASS endpoint certificate: exit 4."""


class FeedError(Exception):
    """the BAG feed could not be fetched: exit 6."""


def banner(s): print(f"\n=== {s} " + "=" * max(0, 74 - len(s)), flush=True)
def _now(): return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def fetch_gguf():
    os.makedirs(MODELS, exist_ok=True)
    p = os.path.join(MODELS, os.path.basename(GGUF_URL))
    if not (os.path.exists(p) and core.sha256(p) == GGUF_SHA):
        print(f"downloading {GGUF_URL} (~5 GB) ...", flush=True)
        req = urllib.request.Request(GGUF_URL, headers={"User-Agent": "gleichlaut/0.1"})
        with urllib.request.urlopen(req, timeout=600) as r, open(p + ".part", "wb") as f:
            while True:
                b = r.read(1 << 22)
                if not b: break
                f.write(b)
        os.replace(p + ".part", p)
    got = core.sha256(p)
    if got != GGUF_SHA: raise SystemExit(f"GGUF sha256 mismatch: {got} != {GGUF_SHA}")
    print("GGUF verified", p, got[:16]); return p


# ------------------------------------------------------------------ cost (item 8: both currencies)
def cost_line():
    """per-item cost of the recorded 70B lane in USD (the evaluation provider's price) and CHF (a Swiss provider's price)."""
    try: e = json.load(open(os.path.join(core.ROOT, "eval", "results", "economics.json"), encoding="utf-8"))
    except (OSError, ValueError): return "cost: eval/results/economics.json not found"
    x1 = e.get("x1", {})
    return (f"cost per item: USD {e['usd_per_item_publicai']:.4f} at the evaluation provider's price (Public AI)  |  "
            f"CHF {e['chf_per_item_infomaniak']:.4f} at a Swiss provider's published price (Infomaniak, CHF 0.70 / 2.50 per M "
            f"tokens in / out); at today's volume (~{x1.get('items_per_month', '?')} items/month): USD {x1.get('usd_per_month_publicai', '?')} "
            f"/ CHF {x1.get('chf_per_month_infomaniak', '?')} a month")


# ------------------------------------------------------------------ live slice (make run step 4)
def live_backend():
    """LLM_BASE_URL (judges' / user-controlled endpoint) > local GGUF (GLEICHLAUT_GGUF=1) > none."""
    if os.environ.get("SKIP_MODEL") == "1": return None, "SKIP_MODEL=1"
    if os.environ.get("LLM_BASE_URL"):
        b = backends.OpenAI(log=os.path.join(OUT, "live_calls.jsonl"),                 # fail fast: a demo slice, not a month
                            retries=os.environ.get("GLEICHLAUT_HTTP_RETRIES") or 3, backoff=os.environ.get("GLEICHLAUT_HTTP_BACKOFF") or 5)
        return b, f"endpoint {b.endpoint} model {b.model}"
    if os.environ.get("GLEICHLAUT_GGUF") == "1":
        p = fetch_gguf()
        return backends.LlamaCpp(p, backends.lang_of_prompt, log=os.path.join(OUT, "live_calls.jsonl")), f"local CPU GGUF {os.path.basename(p)}"
    return None, "no LLM_BASE_URL; `make run-offline` runs the local CPU GGUF"


def live_slice():
    """-> (status, detail): status 'skipped' | 'passed' | 'failed'. Never raises."""
    os.makedirs(OUT, exist_ok=True)
    try:
        ask, what = live_backend()
    except (Exception, SystemExit) as e:
        banner("[4] live slice: 5 Fedlex items"); return "failed", f"backend could not start: {type(e).__name__}: {e}"
    banner(f"[4] live slice: 5 Fedlex items, {what if ask is not None else 'skipped (' + what + ')'}")
    if ask is None: return "skipped", what
    try:
        from .fed import lane
        rows = lane.live_slice(ask)
    except (Exception, SystemExit) as e:
        return "failed", f"{type(e).__name__}: {e}"
    if hasattr(lane, "show"): lane.show(rows)
    else:
        for r in rows: print(json.dumps(r, ensure_ascii=False)[:600])
    return "passed", f"{sum(r['status'] == 'ready' for r in rows)}/{len(rows)} ready, {sum(bool(r.get('exact')) for r in rows)}/{len(rows)} exact"


def cmd_live():
    st, why = live_slice()
    if st == "failed": print(f"LIVE SLICE FAILED: {why}"); return EXIT_ENDPOINT
    print(f"live slice {st.upper()}: {why}"); return EXIT_OK


def cmd_emit(n=10):
    banner(f"[5] emit: FHIR ClinicalUseDefinition + XLIFF 2.1 for {n} items, validated")
    try:
        from .emit.__main__ import main as emit_main
    except ImportError as e:
        print("emit not available:", e); return 1
    return emit_main(["--run", "fresh166", "--n", str(n), "--out", os.path.join(OUT, "emit")]) or 0


def cmd_ui():
    banner("[6] review UI")
    try:
        from .ui import build
    except ImportError as e:
        print("ui not available:", e); return 1
    return build.main(["--out", os.path.join(OUT, "ui", "index.html")]) or 0


def cmd_run():
    from . import replay
    t0 = time.time(); os.makedirs(OUT, exist_ok=True)
    banner("[1-3] freeze, re-execution, re-scoring (offline)")
    rc = replay.main([])
    if rc: print("REPLAY FAILED"); print("make run: reproduction FAILED"); return rc
    print(cost_line())
    live, why = live_slice()
    if live == "failed": print(f"LIVE SLICE FAILED: {why}")
    for step in (cmd_emit, cmd_ui):
        r = step()
        if r: print(f"step {step.__name__} FAILED"); print("make run: reproduction FAILED"); return r
    banner(f"make run done in {time.time() - t0:.0f}s; outputs in {OUT}")
    if live == "failed": print(f"LIVE SLICE FAILED: {why}")
    print(f"make run: reproduction PASSED; live slice {live.upper()}" + (f" ({why})" if live != "failed" else ""))
    return EXIT_OK


# ------------------------------------------------------------------ items: load, validate, route
def _type_ok(v, t):
    if isinstance(t, list): return any(_type_ok(v, u) for u in t)
    return {"string": isinstance(v, str), "integer": isinstance(v, int) and not isinstance(v, bool),
            "number": isinstance(v, (int, float)) and not isinstance(v, bool), "boolean": isinstance(v, bool),
            "object": isinstance(v, dict), "array": isinstance(v, list), "null": v is None}.get(t, True)


def validate(schema, v, path="$"):
    """the JSON Schema subset docs/item-schema.json uses -> list of error strings (empty = valid)."""
    E = []
    if "type" in schema and not _type_ok(v, schema["type"]): return [f"{path}: expected {schema['type']}, got {type(v).__name__}"]
    if "enum" in schema and v not in schema["enum"]: E.append(f"{path}: {v!r} not one of {schema['enum']}")
    if isinstance(v, str):
        if len(v) < schema.get("minLength", 0): E.append(f"{path}: empty" if not v else f"{path}: shorter than {schema['minLength']}")
        if "maxLength" in schema and len(v) > schema["maxLength"]: E.append(f"{path}: longer than {schema['maxLength']}")
        if "pattern" in schema and not re.search(schema["pattern"], v): E.append(f"{path}: {v[:40]!r} does not match {schema['pattern']}")
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        if "minimum" in schema and v < schema["minimum"]: E.append(f"{path}: {v} < {schema['minimum']}")
        if "maximum" in schema and v > schema["maximum"]: E.append(f"{path}: {v} > {schema['maximum']}")
    if isinstance(v, dict):
        for k in schema.get("required", []):
            if k not in v: E.append(f"{path}: missing required field {k!r}")
        for k, s in schema.get("properties", {}).items():
            if k in v: E += validate(s, v[k], f"{path}.{k}")
    if isinstance(v, list):
        if len(v) < schema.get("minItems", 0): E.append(f"{path}: needs at least {schema['minItems']} item(s)")
        if "items" in schema:
            for i, x in enumerate(v):
                k = x.get("key") if isinstance(x, dict) else None
                E += validate(schema["items"], x, f"{path}[{i}]" + (f"({k})" if isinstance(k, str) else ""))
    return E


def change_ratio(a, b):
    from .sl.mine import change_ratio as cr
    return round(cr(a, b), 3)


def load_items(path):
    """read a JSON array or JSON Lines item file, validate it against docs/item-schema.json, fill change_ratio."""
    if not os.path.exists(path): raise UsageError(f"items file not found: {path}")
    try:
        raw = open(path, encoding="utf-8").read()
    except (OSError, UnicodeDecodeError) as e:
        raise UsageError(f"cannot read items file {path}: {e}")
    try:
        items = json.loads(raw)
    except ValueError as e:
        try: items = [json.loads(l) for l in raw.splitlines() if l.strip()]            # JSON Lines
        except ValueError: raise UsageError(f"items file {path} is neither JSON nor JSON Lines: {e}")
    if isinstance(items, dict) and isinstance(items.get("items"), list): items = items["items"]
    E = validate(json.load(open(SCHEMA, encoding="utf-8")), items)
    if isinstance(items, list):
        seen = Counter(x.get("key") for x in items if isinstance(x, dict))
        E += [f"$: duplicate key {k!r} ({n}x)" for k, n in seen.items() if n > 1 and k is not None]
    if E:
        raise UsageError(f"items file {path} does not match docs/item-schema.json ({len(E)} problem{'s' if len(E) > 1 else ''}):\n  "
                         + "\n  ".join(E[:12]) + ("\n  ..." if len(E) > 12 else ""))
    for x in items:
        if "change_ratio" not in x: x["change_ratio"] = x["de_ratio"] if "de_ratio" in x else change_ratio(x["de_old"], x["de_new"])
    return items


def route(x):
    """-> ('draft', None) | ('human', reason). Same rule as sl.mine (> 60% of German tokens changed = a rewrite)."""
    r = x["change_ratio"]
    if r > MAXRATIO: return "human", f"German changed {100 * r:.0f}% of its tokens (> 60%): a rewrite, not an amendment"
    if len(x["de_old"]) > MAXCH or len(x["de_new"]) > MAXCH: return "human", f"German text longer than {MAXCH} characters (outside the evaluated range)"
    if r == 0: return "human", "no change in the German tokens (spacing only)"
    return "draft", None


# ------------------------------------------------------------------ dry run
class _Captured(Exception):
    def __init__(self, prompt, max_tokens): self.prompt, self.max_tokens = prompt, max_tokens


def _capture(prompt, tag, cap, max_tokens): raise _Captured(prompt, max_tokens)


def dry_run(items, corpus, gate=None, out=None):
    """print, per item, the routing, the slot map and the exact first prompt; no backend is constructed, nothing is sent."""
    out = out or sys.stdout
    P = core.Pipeline(_capture, "g3") if corpus == "sl" else None
    n = Counter()
    if gate: print(gate, file=out)
    for x in items:
        rt, why = route(x)
        print(f"\n--- {x['key']} [{x['lang']}] change_ratio {x['change_ratio']:.3f} route {rt}" + (f": {why}" if why else ""), file=out)
        if rt == "human": n["human"] += 1; continue
        try:
            if corpus == "sl": r = P.draft(x)
            else:
                from .fed import lane
                r = lane.fed_draft(x, _capture)
        except _Captured as c:
            n["model"] += 1
            if corpus == "sl":
                S = core.gl2.Slots(x["tgt_old"]); S.mask(x["de_old"], "de"); S.mask(x["de_new"], "de"); S.mask(x["tgt_old"], x["lang"])
                sm = {k: (v if isinstance(v, str) else f"number word {v['w']}") for k, v in S.surf.items()}
                print("slot map (code writes these back; the model sees only the codes): "
                      + (", ".join(f"{k} = {v}" for k, v in sm.items()) or "none"), file=out)
            else:
                print("slot map: none (the Fedlex lane passes numbers verbatim)", file=out)
            print(f"max_tokens {c.max_tokens}; prompt ({len(c.prompt)} chars):\n{c.prompt}", file=out)
            print("(a lock retry or one guard re-ask is sent only if the first answer fails a check; its prompt is this one plus "
                  "the previous answer and the complaints)", file=out)
            continue
        n["code"] += 1
        print("no model call: code applies the change (rule-only / code lane):\n" + r["out"], file=out)
    print(f"\ndry run: {len(items)} items: {n['model']} would call the model, {n['code']} code-only, {n['human']} to a human. "
          "No request was sent.", file=out)
    return EXIT_OK


# ------------------------------------------------------------------ backends for draft / month
def make_backend(a, out):
    """-> (ask, label, review_reason). Raises ConfigError, Uncertified."""
    log = os.path.join(out, "calls.jsonl")
    review = None
    if a.backend == "openai":
        ask = backends.OpenAI(log=log, record_to=os.path.join(out, "cache"))
        label = f"openai {ask.endpoint} {ask.model}"
        if a.corpus == "sl" and not a.air_gapped:
            from . import certify
            cert, why = certify.lookup(ask.base, ask.model)
            if cert is None:
                raise Uncertified(f"{why}. Run `gleichlaut certify` (make certify) against this endpoint first, or use "
                                  f"--air-gapped (every item then goes to review).")
            ask.expect_served = set(cert.get("models_served") or []) or None
            print(f"certification gate: {why}", flush=True)
    elif a.backend == "llamacpp":
        ask = backends.LlamaCpp(a.gguf or fetch_gguf(), backends.lang_of_prompt, log=log); label = f"llamacpp {ask.model}"
        if a.corpus == "sl": review = "SL lane on a local, uncertified model: every item is reviewed"
    elif a.backend == "cache":
        ask = backends.Cache(os.path.join(core.ROOT, "data", "cache", "responses")); label = "cache (recorded responses)"
    else:
        ask = backends.Stub(log=log); label = "stub"; review = "stub backend (wiring test): the draft is the old text, not a translation"
    if a.air_gapped and not review: review = "air-gapped: every item is reviewed"
    if a.corpus == "fedlex" and not review: review = "statute lane: every draft is reviewed (neither model size passes the rule on statutes)"
    return ask, label, review


def _records(path):
    """read records.jsonl; a torn last line (crash mid-write) is cut off so the file can be appended to again."""
    if not os.path.exists(path): return []
    out, good = [], 0
    with open(path, "rb") as f: data = f.read()
    for line in data.splitlines(keepends=True):
        try: out.append(json.loads(line)); good += len(line)
        except ValueError:
            if line.strip(): break
            good += len(line)
    if good < len(data):
        with open(path, "r+b") as f: f.truncate(good)
        print(f"note: cut a torn last line from {path}", flush=True)
    return out


def draft_items(items, ask, out, corpus="sl", review=None, label=""):
    """draft every item not yet in out/records.jsonl; one JSON line per item, flushed as it is written (resumable)."""
    os.makedirs(out, exist_ok=True)
    path = os.path.join(out, "records.jsonl")
    done = {r.get("key") for r in _records(path)}
    todo = [x for x in items if x["key"] not in done]
    if done: print(f"resuming: {len(items) - len(todo)} of {len(items)} items already in {path}", flush=True)
    P = core.Pipeline(ask, "g3") if corpus == "sl" else None
    with open(path, "a", encoding="utf-8") as f:
        for i, x in enumerate(todo):
            rt, why = route(x); t0 = time.time()
            base = dict(key=x["key"], lang=x["lang"], change_ratio=x["change_ratio"], route=rt)
            if rt == "human":
                rec = dict(base, status="human", reason=why)
            else:
                try:
                    if corpus == "sl": r = P.run(x)
                    else:
                        from .fed import lane
                        r = lane.fed_draft(x, ask); r["guard_flag"] = r["flagged"]
                except backends.EndpointError as e:
                    raise backends.EndpointError(f"{e} [{len(done) + i} of {len(items)} records kept in {path}; re-run the same command to resume]")
                except KeyError as e:
                    if not isinstance(ask, backends.Cache): raise
                    r = None; rec = dict(base, status="human", reason=f"no recorded response (cache backend): {e}")
                if r is not None:
                    rec = dict(r, **base)
                    rec["guard_status"] = "flagged" if r["guard_flag"] else "ready"
                    rec["status"] = "flagged" if (r["guard_flag"] or review) else "ready"
                    if review: rec["review_reason"] = review
                    if x.get("tgt_new"): rec["shadow_exact"] = core.lock.norm(r["out"]) == core.lock.norm(x["tgt_new"])
            rec.update(backend=label, drafted_at=_now(), wall_secs=round(time.time() - t0, 2))
            f.write(json.dumps(rec, ensure_ascii=False) + "\n"); f.flush(); os.fsync(f.fileno())
            print(f"[{len(done) + i + 1}/{len(items)}] {x['key']} {rec['status']}" + (f" ({rec.get('reason')})" if rec["status"] == "human" else ""), flush=True)
    return path


def summarise(items, out, mode, extra=None):
    """summary.json over every record in out/ (including resumed ones) + a printed digest."""
    R = {r["key"]: r for r in _records(os.path.join(out, "records.jsonl"))}
    I = {x["key"]: x for x in items}
    recs = [R[k] for k in I if k in R]
    st = Counter(r["status"] for r in recs)
    s = dict(mode=mode, date=_now(), items=len(items), records=len(recs), missing=len(I) - len(recs),
             status=dict(st), by_lang={L: dict(Counter(r["status"] for r in recs if r["lang"] == L)) for L in ("fr", "it")},
             rule_only=sum(bool(r.get("rule_only")) for r in recs), reasked=sum(bool(r.get("reasked")) for r in recs),
             human_reasons=dict(Counter(r.get("reason", "") for r in recs if r["status"] == "human")),
             review_reasons=dict(Counter(r["review_reason"] for r in recs if r.get("review_reason"))))
    sh = [r for r in recs if "shadow_exact" in r]
    if sh:
        rd = [r for r in sh if r["status"] == "ready"]
        s["shadow"] = dict(compared=len(sh), exact=sum(r["shadow_exact"] for r in sh), ready=len(rd), ready_exact=sum(r["shadow_exact"] for r in rd),
                           ready_not_exact=[r["key"] for r in rd if not r["shadow_exact"]],
                           note="tgt_new = the FR/IT text BAG already published; it was never shown to the model")
    calls = []
    if os.path.exists(os.path.join(out, "calls.jsonl")):
        for l in open(os.path.join(out, "calls.jsonl"), encoding="utf-8"):
            try: calls.append(json.loads(l))
            except ValueError: pass
    pt = sum(c.get("prompt_tokens") or 0 for c in calls); ct = sum(c.get("completion_tokens") or 0 for c in calls)
    s["calls"] = dict(n=len(calls), prompt_tokens=pt, completion_tokens=ct, models_served=sorted({c.get("model_served") or "" for c in calls}),
                      system_fingerprints=sorted({c.get("system_fingerprint") for c in calls if c.get("system_fingerprint")}),
                      endpoints=sorted({c.get("endpoint") for c in calls if c.get("endpoint")}),
                      chf_estimate=round((pt * CHF_PER_MTOK[0] + ct * CHF_PER_MTOK[1]) / 1e6, 4),
                      chf_basis="Swiss provider's published price, CHF 0.70 / 2.50 per M input / output tokens")
    s.update(extra or {})
    s["next"] = [f"gleichlaut emit --records {os.path.join(out, 'records.jsonl')} --items {os.path.join(out, 'items.json')} --n 0 --out {os.path.join(out, 'emit')}",
                 f"gleichlaut ui --records {os.path.join(out, 'records.jsonl')} --items {os.path.join(out, 'items.json')} --out {os.path.join(out, 'ui', 'index.html')}"]
    with open(os.path.join(out, "summary.json"), "w", encoding="utf-8") as f: json.dump(s, f, ensure_ascii=False, indent=1)
    print(f"\nSUMMARY ({mode}): {len(recs)}/{len(items)} items: " + ", ".join(f"{k} {v}" for k, v in sorted(st.items()))
          + f"; rule-only {s['rule_only']}, re-asked {s['reasked']}")
    for k, v in s["human_reasons"].items(): print(f"  human: {v} x {k}")
    for k, v in s["review_reasons"].items(): print(f"  review: {v} x {k}")
    if sh: print(f"  shadow: {s['shadow']['exact']}/{len(sh)} drafts identical to the published text; ready {s['shadow']['ready']}, "
                 f"of which {s['shadow']['ready_exact']} identical ({len(s['shadow']['ready_not_exact'])} ready drafts differ: check them)")
    print(f"  calls {len(calls)}, tokens {pt} in / {ct} out, ~CHF {s['calls']['chf_estimate']} at the Swiss provider's price; "
          f"served by {s['calls']['models_served']}")
    print(f"  summary {os.path.join(out, 'summary.json')}\n  next: " + "\n        ".join(s["next"]))
    return s


def _write_items(items, out):
    os.makedirs(out, exist_ok=True)
    p = os.path.join(out, "items.json")
    with open(p, "w", encoding="utf-8") as f: json.dump(items, f, ensure_ascii=False, indent=1)
    return p


def _gate_text(a):
    if a.backend != "openai": return f"backend {a.backend}"
    if not os.environ.get("LLM_BASE_URL"): return "backend openai: LLM_BASE_URL is not set (a real run would stop here)"
    if a.corpus != "sl" or a.air_gapped: return f"backend openai {backends.endpoint_id(os.environ['LLM_BASE_URL'])} (no certification needed: {'air-gapped' if a.air_gapped else 'fedlex'})"
    from . import certify
    cert, why = certify.lookup(os.environ["LLM_BASE_URL"], os.environ.get("LLM_NAME") or core.M70)
    return f"certification gate: {'would PASS' if cert else 'would REFUSE'}: {why}"


def _drafting(a, items, out, mode, extra=None):
    if getattr(a, "restart", False) and os.path.exists(os.path.join(out, "records.jsonl")):
        bak = os.path.join(out, f"records.{datetime.datetime.now().strftime('%Y%m%dT%H%M%S')}.jsonl")
        os.replace(os.path.join(out, "records.jsonl"), bak); print("previous records moved to", bak)
    if a.dry_run: return dry_run(items, a.corpus, _gate_text(a))
    ask, label, review = make_backend(a, out)
    print(f"drafting {len(items)} items through {label} -> {out}", flush=True)
    draft_items(items, ask, out, a.corpus, review, label)
    summarise(items, out, mode, extra)
    if getattr(a, "emit", False):
        rc = passthrough("emit", ["--records", os.path.join(out, "records.jsonl"), "--items", os.path.join(out, "items.json"), "--n", "0", "--out", os.path.join(out, "emit")])
        rc2 = passthrough("ui", ["--records", os.path.join(out, "records.jsonl"), "--items", os.path.join(out, "items.json"), "--out", os.path.join(out, "ui", "index.html")])
        return rc or rc2
    return EXIT_OK


def _common(ap, default_backend="openai"):
    ap.add_argument("--backend", choices=["openai", "llamacpp", "cache", "stub"], default=default_backend,
                    help="openai = LLM_BASE_URL (SL: must be certified); llamacpp = local GGUF; cache = recorded responses; stub = wiring test")
    ap.add_argument("--corpus", choices=["sl", "fedlex"], default="sl")
    ap.add_argument("--gguf"); ap.add_argument("--air-gapped", action="store_true", help="any model; every item goes to review")
    ap.add_argument("--dry-run", action="store_true", help="print routing, slot maps and the exact prompts; send nothing")
    ap.add_argument("--restart", action="store_true", help="set existing records aside and start over (default: resume)")
    ap.add_argument("--emit", action="store_true", help="afterwards run `emit` and `ui` on the records (where the build supports it)")


def cmd_draft(rest):
    ap = argparse.ArgumentParser(prog="gleichlaut draft", description="draft FR/IT for an item file (docs/item-schema.json)")
    ap.add_argument("--items", required=True); ap.add_argument("--out", required=True)
    _common(ap)
    a = ap.parse_args(rest)
    items = load_items(a.items)
    if not a.dry_run: _write_items(items, a.out)
    return _drafting(a, items, a.out, "draft", dict(items_file=os.path.abspath(a.items)))


def cmd_month(rest):
    ap = argparse.ArgumentParser(prog="gleichlaut month", description="one month in operation: mine (or read) the German changes, "
                                 "route, draft, summarise")
    ap.add_argument("--from", dest="d_from", help="old feed date YYYYMMDD"); ap.add_argument("--to", dest="d_to", help="new feed date YYYYMMDD")
    ap.add_argument("--snapshots", help="snapshot dir (default $GLEICHLAUT_HIST or out/hist)")
    ap.add_argument("--fetch", action="store_true", help="download missing de/fr/it feeds of both dates from BAG (public)")
    ap.add_argument("--items", help="pre-publication mode: the SL team's own item file instead of the feed")
    ap.add_argument("--out", help="output dir (default out/month/<from>-<to> or out/month/<items file name>)")
    _common(ap)
    a = ap.parse_args(rest)
    if a.items and (a.d_from or a.d_to): ap.error("give either --items or --from/--to")
    if a.items:
        items = load_items(a.items)
        out = a.out or os.path.join(OUT, "month", os.path.splitext(os.path.basename(a.items))[0])
        if not a.dry_run: _write_items(items, out)
        published = sum("tgt_new" in x for x in items)
        return _drafting(a, items, out, "pre-publication" if not published else "items (with published targets: shadow)",
                         dict(items_file=os.path.abspath(a.items)))
    if not (a.d_from and a.d_to): ap.error("give --from YYYYMMDD --to YYYYMMDD, or --items FILE")
    from .sl import hist_dir, ingest, mine
    try: mine.check_snaps([a.d_from, a.d_to])
    except ValueError as e: raise UsageError(str(e))
    hd = hist_dir(a.snapshots); H = mine.Hist(hd)
    need = [(d, L) for d in (a.d_from, a.d_to) for L in ("de", "fr", "it") if not H.has(d, L)]
    if need and a.fetch:
        for d, L in need:
            try: ingest.fetch(d, L, hd)
            except (urllib.error.URLError, OSError, ValueError) as e:
                raise FeedError(f"cannot fetch the {d} {L} feed ({ingest.url(d, L)}): {getattr(e, 'reason', None) or e}")
        need = [(d, L) for d, L in need if not H.has(d, L)]
    if need:
        raise UsageError(f"snapshots missing in {hd}: " + ", ".join(f"{d}-{L}.json" for d, L in need)
                         + ". Add --fetch to download them from BAG, or point --snapshots at a directory that has them.")
    M = mine.month_items(H, a.d_from, a.d_to)
    out = a.out or os.path.join(OUT, "month", f"{a.d_from}-{a.d_to}")
    items = M["items"]
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "unmatched.json"), "w", encoding="utf-8") as f: json.dump(M["unmatched"], f, ensure_ascii=False, indent=1)
    E = validate(json.load(open(SCHEMA, encoding="utf-8")), items) if items else []
    if E: raise UsageError("mined items do not match docs/item-schema.json: " + "; ".join(E[:5]))
    _write_items(items, out)
    print(f"mined {a.d_from} -> {a.d_to}: {M['stats']['de_changes']} German changes (+{M['stats']['de_rewrites_over60']} > 60% rewrites) "
          f"-> {len(items)} FR/IT items ({M['stats']['items_with_published_target']} with a published target: shadow mode), "
          f"{len(M['unmatched'])} without an old FR/IT text (unmatched.json)", flush=True)
    if not items: print("nothing to draft this month"); summarise(items, out, "shadow (public feed)", dict(mining=M["stats"])); return EXIT_OK
    return _drafting(a, items, out, "shadow (public feed)", dict(mining=M["stats"]))


# ------------------------------------------------------------------ emit / ui pass-through
def _accepts(modname, flag):
    import importlib
    try: return flag in inspect.getsource(importlib.import_module(modname))
    except (ImportError, OSError, TypeError): return False


def passthrough(kind, rest):
    mod = {"emit": "gleichlaut.emit.__main__", "ui": "gleichlaut.ui.build"}[kind]
    wants = [f for f in ("--records", "--items") if f in rest]
    missing = [f for f in wants if not _accepts(mod, f)]
    if missing:
        print(f"`gleichlaut {kind}` in this build does not accept {' / '.join(missing)} yet (it renders recorded runs only). "
              f"The records and items are complete; render them once the {kind} module supports these flags:\n"
              f"  gleichlaut {kind} " + " ".join(rest))
        return EXIT_USAGE
    if kind == "emit":
        from .emit.__main__ import main as m
    else:
        from .ui.build import main as m
    return m(rest) or 0


def _dispatch(argv):
    if not argv or argv[0] in ("-h", "--help"): print(__doc__); return 0
    c, rest = argv[0], argv[1:]
    if c == "run": return cmd_run()
    if c == "replay":
        from . import replay; return replay.main(rest)
    if c == "certify":
        from . import certify; return certify.main(rest)
    if c == "live": return cmd_live()
    if c == "fetch-gguf": fetch_gguf(); return 0
    if c in ("emit", "ui"): return passthrough(c, rest)
    if c == "backtest":
        from . import backtest; return backtest.main(rest) or 0
    if c == "draft": return cmd_draft(rest)
    if c == "month": return cmd_month(rest)
    print(__doc__); return EXIT_USAGE


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    if os.environ.get("GLEICHLAUT_DEBUG") == "1": return _dispatch(argv)
    try:
        return _dispatch(argv)
    except (UsageError, backends.ConfigError) as e:
        print(f"error: {e}", file=sys.stderr); return EXIT_USAGE
    except Uncertified as e:
        print(f"refusing: {e}", file=sys.stderr); return EXIT_UNCERTIFIED
    except backends.EndpointError as e:
        print(f"ENDPOINT FAILED: {e}", file=sys.stderr); return EXIT_ENDPOINT
    except FeedError as e:
        print(f"FEED FAILED: {e}", file=sys.stderr); return EXIT_ENDPOINT
    except KeyboardInterrupt:
        print("\ninterrupted: records written so far are kept; re-run the same command to resume", file=sys.stderr); return 130


if __name__ == "__main__":
    sys.exit(main())
