"""gleichlaut <command>

  run        what `make run` executes: replay (freeze, re-execution, re-scoring), live slice, emit + validate, review UI
  replay     steps 1-3 only (`--write` regenerates eval/results after a deliberate change)
  certify    certify an endpoint on the frozen fresh-166 suite (see gleichlaut.certify)
  draft      draft FR/IT for an item file through a backend; writes records, XLIFF, FHIR and a review page
  live       the live slice alone (5 Fedlex items) through LLM_BASE_URL or a local GGUF
  fetch-gguf download the pinned Apertus 8B GGUF and verify its sha256

Routing (vision §3): corpus fedlex -> 8B; corpus sl -> 70B on a certified endpoint, or any model with --air-gapped, in
which case every item is marked for review whatever the guards say. Items whose DE changed > 60% go to a human."""
import argparse, hashlib, json, os, sys, time, urllib.request
from . import core

GGUF_URL = os.environ.get("GLEICHLAUT_MODEL_URL",
                          "https://huggingface.co/Colby/apertus-v1.5-8b-text-Q4_K_M-GGUF/resolve/main/apertus-v1.5-8b-text-q4_k_m.gguf")
GGUF_SHA = os.environ.get("GLEICHLAUT_MODEL_SHA256", "a037df8d87ff6caacee794ee85f55342f2152e0d359b7389033300c3bee5f299")
MODELS = os.environ.get("GLEICHLAUT_MODELS", os.path.join(core.ROOT, "models"))
OUT = os.environ.get("GLEICHLAUT_OUT", os.path.join(core.ROOT, "out"))


def banner(s): print(f"\n=== {s} " + "=" * max(0, 74 - len(s)), flush=True)


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


def live_backend():
    """LLM_BASE_URL (judges' / user-controlled endpoint) > local GGUF (GLEICHLAUT_GGUF=1) > none."""
    from . import backends
    if os.environ.get("SKIP_MODEL") == "1": return None, "skipped (SKIP_MODEL=1)"
    if os.environ.get("LLM_BASE_URL"):
        b = backends.OpenAI(log=os.path.join(OUT, "live_calls.jsonl"))
        return b, f"endpoint {b.base.split('//')[-1].split('/')[0]} model {b.model}"
    if os.environ.get("GLEICHLAUT_GGUF") == "1":
        p = fetch_gguf()
        return backends.LlamaCpp(p, backends.lang_of_prompt, log=os.path.join(OUT, "live_calls.jsonl")), f"local CPU GGUF {os.path.basename(p)}"
    return None, "skipped (no LLM_BASE_URL; `make run-offline` runs the local CPU GGUF)"


def cmd_live():
    ask, what = live_backend()
    banner(f"[4] live slice: 5 Fedlex items, {what}")
    if ask is None: return 0
    try:
        from .fed import lane
    except ImportError as e:
        print("Fedlex lane not available:", e); return 1
    try:
        rows = lane.live_slice(ask)
    except Exception as e:                   # a live endpoint failing is reported, not a reproducibility failure
        print(f"live slice could not complete: {type(e).__name__}: {e}"); return 0
    for r in rows: print(lane.format_row(r) if hasattr(lane, "format_row") else json.dumps(r, ensure_ascii=False)[:600])
    return 0


def cmd_emit(n=10):
    banner(f"[5] emit: FHIR ClinicalUseDefinition + XLIFF 2.1 for {n} items, validated")
    try:
        from . import emit
    except ImportError as e:
        print("emit not available:", e); return 1
    return emit.main(["--run", "fresh166", "--n", str(n), "--out", os.path.join(OUT, "emit")])


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
    if rc: print("REPLAY FAILED"); return rc
    for step in (cmd_live, cmd_emit, cmd_ui):
        r = step()
        if r: print(f"step {step.__name__} FAILED"); return r
    banner(f"make run PASSED in {time.time() - t0:.0f}s; outputs in {OUT}")
    return 0


def cmd_draft(a):
    """Draft new items. SL items need a certified endpoint unless --air-gapped."""
    from . import backends, certify
    items = json.load(open(a.items, encoding="utf-8"))
    if a.backend == "openai": ask = backends.OpenAI(log=os.path.join(a.out, "calls.jsonl"), record_to=os.path.join(a.out, "cache"))
    elif a.backend == "llamacpp": ask = backends.LlamaCpp(a.gguf or fetch_gguf(), backends.lang_of_prompt, log=os.path.join(a.out, "calls.jsonl"))
    else: ask = backends.Cache(os.path.join(core.ROOT, "data", "cache", "responses"))
    if a.corpus == "sl" and a.backend == "openai" and not a.air_gapped and not certified_or_explain(certify, ask.model): return 4
    os.makedirs(a.out, exist_ok=True)
    P = core.Pipeline(ask, "g3"); out = []
    for x in items:
        if x.get("change_ratio", x.get("de_ratio", 0)) > 0.6:
            out.append(dict(key=x["key"], status="human", reason="DE changed more than 60% of its tokens")); continue
        r = P.run(x)
        r["status"] = "flagged" if (r["guard_flag"] or a.air_gapped) else "ready"
        if a.air_gapped: r["air_gapped_review"] = True
        out.append(r); print(x["key"], r["status"], flush=True)
    with open(os.path.join(a.out, "records.jsonl"), "w", encoding="utf-8") as f:
        for r in out: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("wrote", os.path.join(a.out, "records.jsonl")); return 0


def certified_or_explain(certify, model):
    if certify.certified(model): return True
    print(f"refusing: no PASS certificate for {model} in eval/certificates/. Run `gleichlaut certify --backend openai` "
          f"against this endpoint first, or use --air-gapped (every item then goes to review)."); return False


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    if not argv or argv[0] in ("-h", "--help"): print(__doc__); return 0
    c, rest = argv[0], argv[1:]
    if c == "run": return cmd_run()
    if c == "replay":
        from . import replay; return replay.main(rest)
    if c == "certify":
        from . import certify; return certify.main(rest)
    if c == "live": return cmd_live()
    if c == "fetch-gguf": fetch_gguf(); return 0
    if c == "emit":
        from . import emit; return emit.main(rest)
    if c == "ui":
        from .ui import build; return build.main(rest) or 0
    if c == "backtest":
        from . import backtest; return backtest.main(rest) or 0
    if c == "draft":
        ap = argparse.ArgumentParser(prog="gleichlaut draft")
        ap.add_argument("--items", required=True); ap.add_argument("--out", required=True)
        ap.add_argument("--corpus", choices=["sl", "fedlex"], default="sl")
        ap.add_argument("--backend", choices=["openai", "llamacpp", "cache"], default="openai")
        ap.add_argument("--gguf"); ap.add_argument("--air-gapped", action="store_true")
        return cmd_draft(ap.parse_args(rest))
    print(__doc__); return 2


if __name__ == "__main__":
    sys.exit(main())
