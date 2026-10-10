"""gleichlaut <command>

  run        what `make run` executes: replay (freeze, re-execution, re-scoring), live slice, emit + validate, review UI
  replay     steps 1-3 only (`--write` regenerates eval/results after a deliberate change)
  certify    certify a model on the frozen fresh-166 suite: a local GGUF build (--backend llamacpp --gguf PATH, or
             --import-run RECORDS --gguf-sha256 SHA --labels TSV) or an endpoint (--backend openai); `--canary` an endpoint
  month      one month in operation: --from YYYYMMDD --to YYYYMMDD [--snapshots DIR] [--fetch]  (shadow mode on the public
             feed), or --items FILE (pre-publication: the SL team's own German changes); mines, routes, drafts, summarises
  draft      draft FR/IT for an item file (docs/item-schema.json) through a backend; resumable records + summary
  live       the live slice alone (5 Fedlex items) through LLM_BASE_URL or a local GGUF
  emit, ui   XLIFF 2.1 / FHIR and the review page (over a recorded run; --records/--items where the build supports them)
  audit      the DE<->FR/IT congruence audit of the whole register (gleichlaut.audit; no model; arguments passed through;
             --fail-on-findings exits 8 when a finding is not marked likely equivalent, --fail-on-findings=KIND,...
             when any finding of those kinds exists: for monitoring)
  termbase   mine BAG's house FR/IT renderings of recurring German limitation terms from one snapshot (no model) and
             write the termbase JSON + a TBX-Basic file for terminology tools: [--tbx OUT] [--json OUT] [--hist DIR]
             [--date YYYYMMDD] [--house OUT]; mining also writes the house sentences (BAG's dominant wording of fixed German
             sentences) and the words the German and target registers share; --from JSON exports the TBX from a termbase
             JSON (the shipped one) without snapshots
  feeds      list the BAG ePL FHIR feed dates that are published (resources API + polite HEAD probes), and which are local
  items      build an item file from ePL FHIR exports: --from-fhir OLD NEW [--lang fr,it] --out items.json (gleichlaut.sl.epl)
  resources  rebuild the G5-G7 check resources from your own corpus (`resources build --corpus F --out DIR`), or `show`
             the ones in use (GLEICHLAUT_RESOURCES=DIR; uncertified: every certificate is void, every draft reviewed)
  fetch-gguf download the pinned Apertus 8B GGUF and verify its sha256

Routing (PREREG R1, vision §3):
  corpus sl, default lane -> the local Apertus 8B GGUF on CPU (Q8_0: 4 cores, 16 GiB RAM; GLEICHLAUT_BUILD=q4_k_m
             for an 8 GiB box; offline image), in process, air-gapped, when the GGUF has a build certificate (sha256 of
             the file + llama-cpp-python version + frozen code; `gleichlaut certify`, shipped for both builds:
             eval/certificates/8b-q8_0-fresh166.json, 8b-q4_k_m-fresh166.json): drafts get the guards'
             ready / flagged status. A GGUF without a build certificate drafts with every item marked for review.
  corpus sl, fewer edits  -> Apertus 70B on a certified endpoint (--backend openai: exact endpoint + model) whose latest
             canary passed within 31 days.
  corpus fedlex -> the 8B, every draft reviewed (neither model size passes the rule on statutes).
  --air-gapped, --prompt-domain TEXT (another kind of text than SL conditions) and GLEICHLAUT_RESOURCES (custom check
             resources) are uncertified: any model, every item marked for review whatever the guards say.
Default backend of month / draft: llamacpp when a GGUF with a valid build certificate is in GLEICHLAUT_MODELS (default
models/) or given with --gguf; else openai when LLM_BASE_URL is set; else exit 2. Items whose German changed > 60% of
its tokens go to a human; so do items longer than 2500 characters that need the model (a change the code lane applies
by itself, numbers or months only, is drafted whatever its length).

Monitoring: --metrics-file PATH (or GLEICHLAUT_METRICS_DIR=DIR -> DIR/gleichlaut_<command>.prom) on month, draft, audit
and certify writes a Prometheus textfile (node_exporter textfile collector): exit code, duration, last run time, item
counts by status, model calls, shadow comparison, audit findings by kind.

Exit codes: 0 ok | 1 reproduction or validation failed | 2 usage / bad input / missing configuration (incl. the local
8B lane without llama-cpp-python: use the offline image) | 3 canary outside tolerance, or drafting refused because the
latest canary failed or is stale | 4 refused: endpoint not certified | 5 certificate FAIL | 6 endpoint or feed failed
(records so far are kept; re-run to resume) | 7 certificate PENDING_REVIEW | 8 audit --fail-on-findings found
divergences | 130 interrupted.  GLEICHLAUT_DEBUG=1 shows tracebacks."""
import argparse, datetime, inspect, json, os, re, sys, time, urllib.error, urllib.request
from collections import Counter
from . import core, backends

# The two certified 8B builds (PREREG R1: M1 Q4_K_M, M2 Q8_0; build certificates in eval/certificates/). GLEICHLAUT_BUILD
# picks one, Q8_0 by default (0 errors in its ready drafts, 12.2 points more edits saved than Q4_K_M:
# eval/results/size_compare.json); GLEICHLAUT_MODEL_URL / GLEICHLAUT_MODEL_SHA256 override both (any other file needs its
# own certificate).
BUILDS = {
    "q8_0": ("https://huggingface.co/andreasmartin/apertus-v1.5-8b-text-Q8_0-GGUF/resolve/main/apertus-v1.5-8b-text-q8_0.gguf",
             "dea904ad80cd725ec89962abae464477f5d8114d1f4377514f381f7dc2ed202d"),       # 8.6 GB, a 16 GiB box (default)
    "q4_k_m": ("https://huggingface.co/Colby/apertus-v1.5-8b-text-Q4_K_M-GGUF/resolve/main/apertus-v1.5-8b-text-q4_k_m.gguf",
               "a037df8d87ff6caacee794ee85f55342f2152e0d359b7389033300c3bee5f299"),     # 5.1 GB, an 8 GiB box
}
BUILD = os.environ.get("GLEICHLAUT_BUILD") or "q8_0"
if BUILD not in BUILDS: sys.exit(f"error: GLEICHLAUT_BUILD={BUILD!r}: one of {', '.join(BUILDS)}")
GGUF_URL = os.environ.get("GLEICHLAUT_MODEL_URL") or BUILDS[BUILD][0]
GGUF_SHA = os.environ.get("GLEICHLAUT_MODEL_SHA256") or BUILDS[BUILD][1]
MODELS = os.environ.get("GLEICHLAUT_MODELS", os.path.join(core.ROOT, "models"))


def models_dir(): return os.environ.get("GLEICHLAUT_MODELS") or MODELS
OUT = os.environ.get("GLEICHLAUT_OUT", os.path.join(core.ROOT, "out"))
SCHEMA = os.path.join(core.ROOT, "docs", "item-schema.json")
MAXRATIO, MAXCH = 0.60, 2500                 # = sl.mine.MAXRATIO / MAXCH (the evaluated range)
CHF_PER_MTOK = (0.70, 2.50)                  # Swiss provider's published price, CHF per million input / output tokens (score.economics)
EXIT_OK, EXIT_FAIL, EXIT_USAGE, EXIT_CANARY, EXIT_UNCERTIFIED, EXIT_CERT_FAIL, EXIT_ENDPOINT, EXIT_PENDING, EXIT_FINDINGS = range(9)
_METRICS = {}                                # filled by summarise / cmd_audit; written by main() with --metrics-file


class UsageError(Exception):
    """bad arguments or input files: one-line message, exit 2."""


class Uncertified(Exception):
    """the SL lane was asked to draft through an endpoint without a PASS endpoint certificate: exit 4."""


class FeedError(Exception):
    """the BAG feed could not be fetched: exit 6."""


class CanaryRefused(Exception):
    """the SL lane was asked to draft through a certified endpoint whose latest canary failed or is too old: exit 3."""


def banner(s): print(f"\n=== {s} " + "=" * max(0, 74 - len(s)), flush=True)
def _now(): return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def fetch_gguf():
    M = models_dir(); os.makedirs(M, exist_ok=True)
    p = os.path.join(M, os.path.basename(GGUF_URL))
    if not (os.path.exists(p) and core.sha256(p) == GGUF_SHA):
        part = p + ".part"
        have = os.path.getsize(part) if os.path.exists(part) else 0
        hdr = {"User-Agent": "gleichlaut/0.1"}
        if have: hdr["Range"] = f"bytes={have}-"          # resume an interrupted download (HTTP Range on the .part file)
        print(f"downloading {GGUF_URL} ({BUILD}: 5-9 GB)" + (f", resuming at byte {have}" if have else "") + " ...", flush=True)
        try: r = backends.urlopen(urllib.request.Request(GGUF_URL, headers=hdr), timeout=600)
        except urllib.error.HTTPError as e:
            if not (have and e.code == 416): raise
            r = None                                     # 416: the .part already holds the whole file; the sha256 check decides
        if r is not None:
            with r:
                resumed = have and getattr(r, "status", None) == 206   # a server that ignores Range answers 200: start over
                with open(part, "ab" if resumed else "wb") as f:
                    while True:
                        b = r.read(1 << 22)
                        if not b: break
                        f.write(b)
        os.replace(part, p)
    got = core.sha256(p)
    if got != GGUF_SHA: raise backends.ConfigError(f"GGUF sha256 mismatch: {p} has {got}, expected {GGUF_SHA} (GLEICHLAUT_MODEL_SHA256)")
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
                            retries=backends._env("GLEICHLAUT_RETRIES", "GLEICHLAUT_HTTP_RETRIES", default=3),
                            backoff=backends._env("GLEICHLAUT_BACKOFF", "GLEICHLAUT_HTTP_BACKOFF", default=5))
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


def code_only(x):
    """True if the code lane applies this change by itself (numbers / months only: gl2.plan rule_only), so no model is
    called for it, neither to draft nor to re-ask."""
    try: return bool(core.gl2.plan(x["de_old"], x["de_new"], x["tgt_old"], x["lang"])["rule_only"])
    except Exception: return False


def route(x, corpus="sl"):
    """-> ('draft', None) | ('human', reason). Same rule as sl.mine (> 60% of German tokens changed = a rewrite). The length
    limit (the evaluated range of the model lane) applies only to items that need the model: a change the code lane applies
    by itself is drafted whatever the length of the text."""
    r = x["change_ratio"]
    if r > MAXRATIO: return "human", f"German changed {100 * r:.0f}% of its tokens (> 60%): a rewrite, not an amendment"
    if r == 0: return "human", "no change in the German tokens (spacing only)"
    if (len(x["de_old"]) > MAXCH or len(x["de_new"]) > MAXCH) and not (corpus == "sl" and code_only(x)):
        return "human", f"German text longer than {MAXCH} characters and the change needs the model (outside the evaluated range)"
    return "draft", None


# ------------------------------------------------------------------ dry run
class _Captured(Exception):
    def __init__(self, prompt, max_tokens): self.prompt, self.max_tokens = prompt, max_tokens


def _capture(prompt, tag, cap, max_tokens): raise _Captured(prompt, max_tokens)


def _pipeline(ask, variant="frozen", terms_date=None):
    """the SL pipeline: the frozen one (default), or the experimental v3-terms variant (PREREG R12, gleichlaut.v3terms)."""
    if variant in (None, "frozen"): return core.Pipeline(ask, "g3")
    if variant != "v3-terms": raise UsageError(f"unknown variant {variant!r}")
    if not terms_date: raise UsageError("--variant v3-terms needs --terms-date YYYYMMDD (the snapshot the house wording is mined from)")
    from . import v3terms
    try: return v3terms.TermsPipeline(ask, terms_date)
    except FileNotFoundError as e: raise UsageError(str(e))


def dry_run(items, corpus, gate=None, out=None, domain=None, variant="frozen", terms_date=None):
    """print, per item, the routing, the slot map and the exact first prompt; no backend is constructed, nothing is sent."""
    out = out or sys.stdout
    P = _pipeline(backends.DomainAsk(_capture, domain) if domain else _capture, variant, terms_date) if corpus == "sl" else None
    n = Counter()
    if gate: print(gate, file=out)
    for x in items:
        rt, why = route(x, corpus)
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
def local_ggufs():
    d = models_dir()
    return sorted(os.path.join(d, f) for f in os.listdir(d) if f.endswith(".gguf")) if os.path.isdir(d) else []


def certified_gguf(paths=None):
    """-> (path, sha256, certificate, reason) of the first GGUF with a valid build certificate, else (None, None, None, reason).
    Every candidate file is hashed (about 10 s per 5 GB)."""
    from . import certify
    paths = local_ggufs() if paths is None else paths
    if not paths: return None, None, None, f"no GGUF in {models_dir()} (GLEICHLAUT_MODELS)"
    whys = []
    for p in paths:
        sha = backends.file_sha256(p)
        cert, why = certify.build_lookup(sha, backends.llama_version())
        if cert: return p, sha, cert, why
        whys.append(f"{os.path.basename(p)}: {why}")
    return None, None, None, "; ".join(whys)


def resolve_backend(a):
    """month / draft without --backend: the certified local 8B when present, else the endpoint in LLM_BASE_URL."""
    if a.backend: return a.backend
    if a.gguf:
        a.backend = "llamacpp"; return a.backend
    p, sha, cert, why = certified_gguf()
    if p:
        a.gguf, a._gguf_sha, a.backend = p, sha, "llamacpp"
        print(f"backend: llamacpp (default): {os.path.basename(p)} has a valid build certificate", flush=True)
    elif os.environ.get("LLM_BASE_URL"):
        a.backend = "openai"
        print(f"backend: openai (default: no certified GGUF; {why})", flush=True)
    else:
        raise backends.ConfigError(f"no drafting backend: no certified GGUF ({why}) and LLM_BASE_URL is not set. Run the "
                                   "offline image with the 8B (make month; gleichlaut fetch-gguf downloads it), set LLM_BASE_URL "
                                   "to a certified 70B endpoint (make month-70b), or pass --backend")
    return a.backend


def _uncertified_reason(a):
    """the reason every item goes to review whatever the model, or None: --prompt-domain, custom resources, --air-gapped."""
    from . import resources
    if getattr(a, "prompt_domain", None):
        return f"custom prompt domain (--prompt-domain): uncertified, every draft is reviewed"
    if resources.active(): return resources.review_reason()
    if a.air_gapped: return "air-gapped: every item is reviewed"
    return None


def make_backend(a, out):
    """-> (ask, label, review_reason). Raises ConfigError, Uncertified, CanaryRefused."""
    log = os.path.join(out, "calls.jsonl")
    review = None
    if getattr(a, "prompt_domain", None) and a.corpus != "sl":
        raise UsageError("--prompt-domain rewrites the SL drafting prompt; the statute lane (--corpus fedlex) has its own prompt")
    unc = _uncertified_reason(a)
    if a.backend == "openai":
        ask = backends.OpenAI(log=log, record_to=os.path.join(out, "cache"))
        label = f"openai {ask.endpoint} {ask.model}"
        if a.corpus == "sl" and not unc:
            from . import certify
            cert, why = certify.lookup(ask.base, ask.model)
            if cert is None:
                raise Uncertified(f"{why}. Run `gleichlaut certify --backend openai` (make certify-endpoint) against this endpoint first, draft with the certified local 8B (make month), or use "
                                  f"--air-gapped (every item then goes to review).")
            ask.expect_served = set(cert.get("models_served") or []) or None
            print(f"certification gate: {why}", flush=True)
            st, cwhy = certify.canary_gate(cert)
            gate = dict(certificate=cert.get("name"), certification=why, canary=st, canary_reason=cwhy)
            if st == "failed": raise CanaryRefused(cwhy)
            if st == "stale":
                if not getattr(a, "allow_stale_canary", False): raise CanaryRefused(cwhy)
                gate["override"] = "--allow-stale-canary"
                _log_override(dict(ts=_now(), override="--allow-stale-canary", endpoint=ask.endpoint, model=ask.model,
                                   certificate=cert.get("name"), reason=cwhy, out=os.path.abspath(out)))
                print(f"WARNING: canary gate overridden with --allow-stale-canary: {cwhy}", flush=True)
            else:
                print(f"canary gate: {cwhy}", flush=True)
            a._gate = gate
    elif a.backend == "llamacpp":
        backends.require_llama()                 # one line + exit 2 with the fix (the offline image), never a traceback
        path = a.gguf or next(iter(local_ggufs()), None)
        if not path:
            raise backends.ConfigError(f"no GGUF in {models_dir()} (GLEICHLAUT_MODELS): `gleichlaut fetch-gguf` downloads the pinned "
                                       "Apertus 8B build (sha256-checked), or pass --gguf PATH")
        ask = backends.LlamaCpp(path, backends.lang_of_prompt, log=log,
                                gguf_sha256=getattr(a, "_gguf_sha", None) if path == a.gguf else None)
        label = f"llamacpp {ask.model}"
        if a.corpus == "sl" and not unc:
            from . import certify
            cert, why = certify.build_lookup(ask.gguf_sha256, ask.runtime)
            if cert:
                print(f"certification gate: {why}", flush=True)
                a._gate = dict(certificate=cert.get("name"), kind="build", certification=why, gguf_sha256=ask.gguf_sha256,
                               llama_cpp_python=ask.runtime)
            else:
                review = f"SL lane on a local, uncertified model build: every item is reviewed ({why})"
                print(f"WARNING: {review}", flush=True)
    elif a.backend == "cache":
        ask = backends.Cache(os.path.join(core.ROOT, "data", "cache", "responses")); label = "cache (recorded responses)"
    else:
        ask = backends.Stub(log=log); label = "stub"; review = "stub backend (wiring test): the draft is the old text, not a translation"
    if unc and not review: review = unc
    if a.corpus == "fedlex" and not review: review = "statute lane: every draft is reviewed (neither model size passes the rule on statutes)"
    if getattr(a, "prompt_domain", None):
        ask = backends.DomainAsk(ask, a.prompt_domain); label += f" (prompt domain: {ask.sentence})"
    return ask, label, review


def _log_override(rec):
    """every gate override is appended to state/gate-overrides.jsonl (and recorded in the run's summary.json)."""
    from . import certify
    os.makedirs(certify.state_dir(), exist_ok=True)
    with open(certify.state_dir("gate-overrides.jsonl"), "a", encoding="utf-8") as f: f.write(json.dumps(rec, ensure_ascii=False) + "\n")


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


def draft_items(items, ask, out, corpus="sl", review=None, label="", variant="frozen", terms_date=None):
    """draft every item not yet in out/records.jsonl; one JSON line per item, flushed as it is written (resumable)."""
    os.makedirs(out, exist_ok=True)
    path = os.path.join(out, "records.jsonl")
    done = {r.get("key") for r in _records(path)}
    todo = [x for x in items if x["key"] not in done]
    if done: print(f"resuming: {len(items) - len(todo)} of {len(items)} items already in {path}", flush=True)
    P = _pipeline(ask, variant, terms_date) if corpus == "sl" else None
    with open(path, "a", encoding="utf-8") as f:
        for i, x in enumerate(todo):
            rt, why = route(x, corpus); t0 = time.time()
            base = dict(key=x["key"], lang=x["lang"], change_ratio=x["change_ratio"], route=rt)
            if rt == "draft" and (len(x["de_old"]) > MAXCH or len(x["de_new"]) > MAXCH):
                base["route_note"] = f"longer than {MAXCH} characters; drafted because the code lane applies the change (no model call)"
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
        ex = sum(r["shadow_exact"] for r in sh)
        s["shadow"] = dict(compared=len(sh), exact=ex, ready=len(rd), ready_exact=sum(r["shadow_exact"] for r in rd),
                           exact_rate=round(100 * ex / len(sh), 1), ready_rate=round(100 * len(rd) / len(sh), 1),
                           flag_rate=round(100 * sum(r["status"] == "flagged" for r in sh) / len(sh), 1),
                           ready_exact_rate=round(100 * sum(r["shadow_exact"] for r in rd) / len(rd), 1) if rd else None,
                           rates_note="percent of the drafted items with a published target (status human excluded)",
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
    _METRICS.update(items=len(items), status=dict(st), calls=len(calls), prompt_tokens=pt, completion_tokens=ct,
                    shadow=s.get("shadow"), rule_only=s["rule_only"], reasked=s["reasked"])
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
    unc = _uncertified_reason(a)
    if a.backend == "llamacpp":
        if a.corpus != "sl" or unc: return f"backend llamacpp (no certification needed: {unc or 'fedlex'})"
        path = a.gguf or next(iter(local_ggufs()), None)
        if not path: return f"backend llamacpp: no GGUF in {models_dir()} (a real run would stop here)"
        from . import certify
        cert, why = certify.build_lookup(getattr(a, "_gguf_sha", None) or backends.file_sha256(path), backends.llama_version())
        return (f"build certificate gate: would PASS: {why}" if cert else
                f"build certificate gate: no valid certificate, every item would go to review: {why}") + \
               ("" if backends.llama_version() else "; llama-cpp-python is not installed here (a real run needs the offline image)")
    if a.backend != "openai": return f"backend {a.backend}"
    if not os.environ.get("LLM_BASE_URL"): return "backend openai: LLM_BASE_URL is not set (a real run would stop here)"
    if a.corpus != "sl" or unc: return f"backend openai {backends.endpoint_id(os.environ['LLM_BASE_URL'])} (no certification needed: {unc or 'fedlex'})"
    from . import certify
    cert, why = certify.lookup(os.environ["LLM_BASE_URL"], os.environ.get("LLM_NAME") or core.M70)
    if not cert: return f"certification gate: would REFUSE: {why}"
    st, cwhy = certify.canary_gate(cert)
    verdict = "would PASS" if st == "ok" else ("would PASS (stale canary overridden)" if st == "stale" and getattr(a, "allow_stale_canary", False) else "would REFUSE")
    return f"certification gate: {verdict}: {why}; canary: {st}: {cwhy}"


def _drafting(a, items, out, mode, extra=None):
    if getattr(a, "restart", False) and os.path.exists(os.path.join(out, "records.jsonl")):
        bak = os.path.join(out, f"records.{datetime.datetime.now().strftime('%Y%m%dT%H%M%S')}.jsonl")
        os.replace(os.path.join(out, "records.jsonl"), bak); print("previous records moved to", bak)
    resolve_backend(a)
    variant, td = getattr(a, "variant", "frozen") or "frozen", getattr(a, "terms_date", None)
    if variant != "frozen" and a.corpus != "sl": raise UsageError("--variant applies to the SL lane only")
    if a.dry_run: return dry_run(items, a.corpus, _gate_text(a), domain=getattr(a, "prompt_domain", None), variant=variant, terms_date=td)
    if variant != "frozen": _pipeline(None, variant, td)          # fail fast on a missing termbase, before any model loads
    ask, label, review = make_backend(a, out)
    if variant != "frozen":
        label += f" (variant {variant}, house wording mined from the {td} snapshot)"
        review = review or (f"experimental prompt variant {variant} (PREREG R12), not the certified pipeline: every item is "
                            "reviewed; guard_status keeps the frozen guards' verdict")
    print(f"drafting {len(items)} items through {label} -> {out}", flush=True)
    draft_items(items, ask, out, a.corpus, review, label, variant, td)
    if getattr(a, "_gate", None): extra = dict(extra or {}, gate=a._gate)
    extra = dict(extra or {}, backend=dict(name=a.backend, label=label, review_policy=review))
    if variant != "frozen": extra["variant"] = dict(name=variant, terms_date=td)
    summarise(items, out, mode, extra)
    if getattr(a, "emit", False):
        rc = passthrough("emit", ["--records", os.path.join(out, "records.jsonl"), "--items", os.path.join(out, "items.json"), "--n", "0", "--out", os.path.join(out, "emit")])
        rc2 = passthrough("ui", ["--records", os.path.join(out, "records.jsonl"), "--items", os.path.join(out, "items.json"), "--out", os.path.join(out, "ui", "index.html")])
        return rc or rc2
    return EXIT_OK


def _common(ap, default_backend=None):
    ap.add_argument("--backend", choices=["openai", "llamacpp", "cache", "stub"], default=default_backend,
                    help="default: llamacpp when a GGUF with a valid build certificate is in GLEICHLAUT_MODELS (models/) or given "
                         "with --gguf (the SL default lane: local 8B, air-gapped), else openai when LLM_BASE_URL is set. "
                         "openai = LLM_BASE_URL (SL: endpoint certificate + canary; the 70B fewer-edits lane); llamacpp = local GGUF "
                         "(SL: build certificate, else every item reviewed; needs the offline image); cache = recorded responses; "
                         "stub = wiring test")
    ap.add_argument("--corpus", choices=["sl", "fedlex"], default="sl")
    ap.add_argument("--gguf", help="the GGUF for --backend llamacpp (default: the first *.gguf in GLEICHLAUT_MODELS)")
    ap.add_argument("--air-gapped", action="store_true", help="any model; every item goes to review")
    ap.add_argument("--prompt-domain", metavar="TEXT", help="replace the first sentence of the SL prompt ('A Swiss reimbursement "
                    "limitation (Spezialitätenliste, BAG) was amended in German.') for another kind of text: a noun phrase "
                    "('paragraph of a cantonal ordinance') or a whole sentence. UNCERTIFIED: every draft goes to review")
    ap.add_argument("--variant", choices=["frozen", "v3-terms"], default="frozen",
                    help="SL pipeline: frozen (default, certified) or v3-terms (experimental, PREREG R12: the drafting prompt also "
                         "lists BAG's house FR/IT wording of the terms and fixed sentences in the new German; every item reviewed)")
    ap.add_argument("--terms-date", metavar="YYYYMMDD", help="v3-terms: the snapshot whose mined house wording is used "
                    "(data/termbase/r12/termbase_<date>.json and house_sentences_<date>.json)")
    ap.add_argument("--dry-run", action="store_true", help="print routing, slot maps and the exact prompts; send nothing")
    ap.add_argument("--restart", action="store_true", help="set existing records aside and start over (default: resume)")
    ap.add_argument("--emit", action="store_true", help="afterwards run `emit` and `ui` on the records (where the build supports it)")
    ap.add_argument("--allow-stale-canary", action="store_true",
                    help="draft although the latest canary is older than GLEICHLAUT_CANARY_MAX_AGE_DAYS (logged; a FAILED canary still refuses)")


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
    ap.add_argument("--from", dest="d_from", help="old feed date YYYYMMDD, or 'previous' (where the last month run ended, else the "
                    "feed published before --to)")
    ap.add_argument("--to", dest="d_to", help="new feed date YYYYMMDD, or 'latest' (BAG's resources API)")
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
    from .sl import hist_dir, ingest, mine, feeds
    if a.d_to == "latest":
        try: a.d_to, how = feeds.resolve_latest(a.snapshots)
        except ValueError as e: raise FeedError(str(e))
        print(f"--to latest = {a.d_to} ({how})", flush=True)
    if a.d_from == "previous":
        try: a.d_from, how = feeds.resolve_previous(a.d_to, a.snapshots, os.path.join(OUT, "month"))
        except ValueError as e: raise UsageError(str(e))
        print(f"--from previous = {a.d_from} ({how})", flush=True)
        if a.d_from >= a.d_to: raise UsageError(f"nothing to do: --from previous resolved to {a.d_from}, not before --to {a.d_to}")
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


# ------------------------------------------------------------------ audit with --fail-on-findings, metrics textfile
AUDIT_KINDS = ("number", "unit", "language", "editorial", "terminology")


def _audit_kinds():
    try:
        from . import audit
        return tuple(getattr(audit, "KINDS_ALL", AUDIT_KINDS))
    except ImportError: return AUDIT_KINDS


def cmd_audit(rest):
    """gleichlaut audit [--fail-on-findings | --fail-on-findings=KIND,...] <audit arguments>.
    --fail-on-findings      passed through to gleichlaut.audit, which fails when a finding is not marked likely equivalent
                            (its own triage); reported here as exit 8, the monitoring code (not 1, a broken build)
    --fail-on-findings=K,.. exit 8 when the summary counts any finding of these kinds (number, unit, language, editorial,
                            terminology), read from audit_<date>_summary.json
    The summary's counts also feed the metrics textfile (--metrics-file / GLEICHLAUT_METRICS_DIR)."""
    from . import audit
    kinds_all = _audit_kinds()
    bare, kinds, args = False, None, []
    for x in rest:
        if x == "--fail-on-findings": bare = True
        elif x.startswith("--fail-on-findings="):
            kinds = tuple(k for k in x.split("=", 1)[1].split(",") if k)
            bad = [k for k in kinds if k not in kinds_all]
            if bad or not kinds: raise UsageError(f"--fail-on-findings=KINDS takes a comma-separated subset of {','.join(kinds_all)}")
        else: args.append(x)
    native = bare and _accepts("gleichlaut.audit", "--fail-on-findings")
    rc = audit.main(args + (["--fail-on-findings"] if native else [])) or 0
    ap = argparse.ArgumentParser(add_help=False); ap.add_argument("--date", default=None)
    ap.add_argument("--out", default=getattr(audit, "DEST", os.path.join(OUT, "audit")))
    k, _ = ap.parse_known_args(args); date = k.date or "20261006"
    p = os.path.join(k.out, f"audit_{date}_summary.json")
    summ = None
    if os.path.exists(p):
        try: summ = json.load(open(p, encoding="utf-8"))
        except (OSError, ValueError): summ = None
    if isinstance(summ, dict):
        _METRICS.update(audit_date=date, audit_findings=dict(summ.get("by_kind") or {}), audit_kinds=kinds_all,
                        audit_limitations_with_finding=summ.get("limitations_with_any_finding"))
    if native and rc == 1:
        print(f"audit {date}: findings not marked likely equivalent (--fail-on-findings): exit {EXIT_FINDINGS}; details in {p}",
              file=sys.stderr)
        return EXIT_FINDINGS
    if (kinds is None and not bare) or rc: return rc
    if not isinstance(summ, dict): raise UsageError(f"--fail-on-findings: the audit wrote no summary at {p}")
    kinds = kinds or kinds_all
    n = sum(int((summ.get("by_kind") or {}).get(x, 0)) for x in kinds)
    if n:
        print(f"audit {date}: {n} finding(s) of kind {','.join(kinds)} (--fail-on-findings): exit {EXIT_FINDINGS}; details in {p}",
              file=sys.stderr)
        return EXIT_FINDINGS
    return rc


def _pop_metrics(argv):
    """-> (argv without --metrics-file PATH, path or None). GLEICHLAUT_METRICS_DIR gives DIR/gleichlaut_<command>.prom."""
    out, path, i = [], None, 0
    while i < len(argv):
        x = argv[i]
        if x == "--metrics-file" and i + 1 < len(argv): path = argv[i + 1]; i += 2; continue
        if x.startswith("--metrics-file="): path = x.split("=", 1)[1]; i += 1; continue
        out.append(x); i += 1
    cmd = out[0] if out else ""
    if path is None and os.environ.get("GLEICHLAUT_METRICS_DIR") and cmd in ("month", "draft", "audit", "certify"):
        path = os.path.join(os.environ["GLEICHLAUT_METRICS_DIR"], f"gleichlaut_{cmd}.prom")
    return out, path


def _esc(v): return str(v).replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")


def write_metrics(path, cmd, rc, secs, m=None):
    """Prometheus text exposition format, written atomically (tmp file + rename) for node_exporter's textfile collector."""
    m = _METRICS if m is None else m; job = _esc(cmd)
    L = []
    def g(name, help_, rows):
        L.append(f"# HELP {name} {help_}"); L.append(f"# TYPE {name} gauge")
        for labels, v in rows:
            lab = ",".join([f'job="{job}"'] + [f'{a}="{_esc(b)}"' for a, b in labels])
            L.append(f"{name}{{{lab}}} {v}")
    g("gleichlaut_last_run_timestamp_seconds", "end of the last run (unix time)", [((), int(time.time()))])
    g("gleichlaut_last_run_exit_code", "exit code of the last run (docs/operations.md section 6)", [((), rc)])
    g("gleichlaut_last_run_success", "1 if the last run exited 0", [((), int(rc == 0))])
    g("gleichlaut_last_run_duration_seconds", "wall time of the last run", [((), round(secs, 1))])
    if "status" in m:
        g("gleichlaut_items", "items of the last run by record status", [((("status", k),), v) for k, v in sorted(m["status"].items())] or [((("status", "none"),), 0)])
        g("gleichlaut_items_total", "items of the last run", [((), m.get("items", 0))])
        g("gleichlaut_model_calls", "model calls of the last run", [((), m.get("calls", 0))])
        g("gleichlaut_tokens", "tokens of the last run", [((("direction", "in"),), m.get("prompt_tokens", 0)), ((("direction", "out"),), m.get("completion_tokens", 0))])
        sh = m.get("shadow")
        if sh:
            g("gleichlaut_shadow_items", "shadow mode: drafts compared with BAG's published text", [((("what", k),), sh[k]) for k in ("compared", "exact", "ready", "ready_exact")])
            g("gleichlaut_shadow_rate_percent", "shadow mode: rates over the compared drafts",
              [((("what", k),), sh[k]) for k in ("exact_rate", "ready_rate", "flag_rate", "ready_exact_rate") if sh.get(k) is not None])
    if "audit_findings" in m:
        g("gleichlaut_audit_findings", "audit findings by kind",
          [((("kind", k),), m["audit_findings"].get(k, 0)) for k in m.get("audit_kinds") or AUDIT_KINDS])
        if m.get("audit_limitations_with_finding") is not None:
            g("gleichlaut_audit_limitations_with_finding", "limitations with at least one finding", [((), m["audit_limitations_with_finding"])])
    d = os.path.dirname(os.path.abspath(path)); os.makedirs(d, exist_ok=True)
    tmp = os.path.join(d, f".{os.path.basename(path)}.{os.getpid()}.tmp")
    with open(tmp, "w", encoding="utf-8") as f: f.write("\n".join(L) + "\n")
    os.replace(tmp, path)


NOARG_HELP = {
    "run": "gleichlaut run: replay + re-score + emit + review page (no arguments; LLM_BASE_URL etc. from the environment)",
    "live": "gleichlaut live: draft the 5 live statute paragraphs through LLM_BASE_URL (no arguments)",
    "fetch-gguf": "gleichlaut fetch-gguf: download the certified 8B GGUF (GLEICHLAUT_BUILD=q8_0 8.6 GB, the default | q4_k_m 5.1 GB) into "
                  "GLEICHLAUT_MODELS and check its sha256; downloads nothing if a verified file is there (no arguments)",
}


def _dispatch(argv):
    if not argv or argv[0] in ("-h", "--help"): print(__doc__); return 0
    c, rest = argv[0], argv[1:]
    if c in NOARG_HELP and rest:                    # these take no arguments: never start a run or a 5-9 GB download on --help
        if rest[0] in ("-h", "--help"): print(NOARG_HELP[c]); return 0
        raise UsageError(f"{c} takes no arguments (got {' '.join(rest)}); {NOARG_HELP[c]}")
    if c == "run": return cmd_run()
    if c == "replay":
        from . import replay; return replay.main(rest)
    if c == "certify":
        from . import certify; return certify.main(rest)
    if c == "live": return cmd_live()
    if c == "fetch-gguf":
        try: fetch_gguf(); return 0
        except (urllib.error.URLError, OSError) as e:
            raise FeedError(f"cannot download the GGUF from {GGUF_URL}: {getattr(e, 'reason', None) or e} (a re-run resumes the "
                            f"partial download; air-gapped: copy the file into {models_dir()} and check its sha256 {GGUF_SHA})")
    if c in ("emit", "ui"): return passthrough(c, rest)
    if c == "backtest":
        from . import backtest; return backtest.main(rest) or 0
    if c in ("draft", "month"):
        from . import resources
        if resources.apply():                       # GLEICHLAUT_RESOURCES: custom G5-G7 resources, uncertified
            print(f"WARNING: {resources.review_reason()}", flush=True)
        return cmd_draft(rest) if c == "draft" else cmd_month(rest)
    if c == "audit": return cmd_audit(rest)
    if c == "termbase":
        from . import termbase
        try: return termbase.main(rest) or 0
        except (OSError, ValueError) as e: raise UsageError(str(e))
    if c == "resources":
        from . import resources; return resources.main(rest)
    if c == "feeds":
        from .sl import feeds; return feeds.main(rest) or 0
    if c == "items":
        from .sl import epl
        try: return epl.main(rest) or 0
        except (OSError, ValueError) as e: raise UsageError(str(e))
    print(__doc__); return EXIT_USAGE


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    argv, mpath = _pop_metrics(list(argv))
    if not mpath: return _main(argv)
    _METRICS.clear(); t0 = time.time(); rc = EXIT_FAIL
    try:
        rc = _main(argv); return rc
    except SystemExit as e:
        rc = e.code if isinstance(e.code, int) else EXIT_FAIL; raise
    finally:
        try: write_metrics(mpath, argv[0] if argv else "", rc if rc is not None else 0, time.time() - t0)
        except OSError as e: print(f"warning: cannot write the metrics file {mpath}: {e}", file=sys.stderr)


def _main(argv):
    if os.environ.get("GLEICHLAUT_DEBUG") == "1": return _dispatch(argv)
    try:
        return _dispatch(argv)
    except (UsageError, backends.ConfigError) as e:
        print(f"error: {e}", file=sys.stderr); return EXIT_USAGE
    except Uncertified as e:
        print(f"refusing: {e}", file=sys.stderr); return EXIT_UNCERTIFIED
    except CanaryRefused as e:
        print(f"refusing (canary): {e}", file=sys.stderr); return EXIT_CANARY
    except backends.EndpointError as e:
        print(f"ENDPOINT FAILED: {e}", file=sys.stderr); return EXIT_ENDPOINT
    except FeedError as e:
        print(f"FEED FAILED: {e}", file=sys.stderr); return EXIT_ENDPOINT
    except KeyboardInterrupt:
        print("\ninterrupted: records written so far are kept; re-run the same command to resume", file=sys.stderr); return 130


if __name__ == "__main__":
    sys.exit(main())
