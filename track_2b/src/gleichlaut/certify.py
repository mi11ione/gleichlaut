"""Certify a model for the SL lane by re-running the frozen fresh-166 suite on it, and watch endpoints with a canary.

Two kinds authorise drafting:
  "build"     a local GGUF build of Apertus 8B run in process by llama.cpp (the SL default lane, PREREG R1). Bound to the
              GGUF's sha256, the llama-cpp-python version and the freeze hash. Made by running the suite locally
              (`certify --backend llamacpp --gguf PATH`; on 4 CPU cores about 9.2 h for Q8_0 at the measured 200.5 s
              per item, 7.1 h for Q4_K_M at 153.4 s) or by importing a recorded run (`certify --import-run RECORDS
              --gguf-sha256 SHA --labels TSV`, e.g. the M1/M2 runs of the GitHub Actions CPU runners). Two build
              certificates ship, both imports of those runs: eval/certificates/8b-q8_0-fresh166.json (M2, Q8_0, the
              default build) and eval/certificates/8b-q4_k_m-fresh166.json (M1, Q4_K_M, the 8 GiB option). The gate
              accepts each (and any build certificate in the state directory) for exactly its GGUF and llama-cpp-python
              version, after re-scoring its records like any other certificate (build_lookup()).
              A build certificate does not expire and needs no canary: nothing it certifies can change under it (a file
              hash, a library version, frozen code), unlike a remote serving stack.
  "endpoint"  an OpenAI-compatible endpoint (--backend openai), the 70B "fewer edits" lane.

A certificate records WHAT was certified, never a secret:
  kind               "build" or "endpoint" (above); "replay" (--backend cache: the recorded responses re-run) and
                     "evaluation" (--backend gateway: the development gateway to Public AI) are evidence only and never
                     authorise anything
  endpoint           scheme://host[:port]/path of LLM_BASE_URL (backends.endpoint_id; never the key)
  model_requested    LLM_NAME;  models_served / system_fingerprints / seeds: everything the endpoint reported on the suite calls
  freeze_sha256, suite.sha256   the frozen code and items the run used (a certificate stops counting when either changes)
  status             PASS            every pre-registered criterion is met and no unflagged output is unlabelled
                     PENDING_REVIEW  the automatic criteria are met, but some unflagged non-exact outputs are new (not identical
                                     to an output already hand-labelled in the reference run) and need a human label
                                     (`--resolve CERT --labels TSV`) before the certificate holds
                     FAIL            an automatic criterion fails (exact gain < +5, flag rate > 70%), or labels exceed the limits
Labels are inherited only by identical outputs (after whitespace/apostrophe normalisation): nothing is judged by a model.

New certificates, their call logs, the suite records and recorded responses go to the state directory ($GLEICHLAUT_STATE,
default track_2b/state, gitignored): state/certificates/, state/runs/, state/cache/, state/canary/. The certificates shipped
in eval/certificates/ are evidence of the evaluation (a replay and the Public AI runs) and are never consulted by certified();
the one exception is a build certificate there (kind "build"), which build_lookup() verifies and accepts like one in state/.
With GLEICHLAUT_CERT_KEY set, unsigned certificates are refused, the shipped build certificates included: `make certify`
imports a signed copy of the selected build's certificate into state/.
Custom check resources (GLEICHLAUT_RESOURCES, gleichlaut.resources) void every certificate: the gate refuses them all.

Integrity (a certificate is a claim that is re-checked every time it is used, not trusted as written):
  run_records_sha256 / calls_log_sha256 / labels_sha256   sha256 of the suite records (state/runs/), the call log
                     (state/certificates/<name>.calls.jsonl) and, after --resolve, the human labels (state/certificates/
                     <name>.labels.tsv) the certificate was computed from
  expires            certification date + GLEICHLAUT_CERT_DAYS (default 90; --valid-days); the gate also applies the
                     validity configured at check time, whichever ends first
  hmac_sha256        optional: HMAC-SHA256 of the certificate with the key in the file named by GLEICHLAUT_CERT_KEY. When that
                     variable is set, unsigned or wrongly signed certificates and canary reports are refused. Keep the key
                     outside state/ (root-owned file, Kubernetes Secret)
certified(base_url, model) -> the newest certificate with kind "endpoint", the exact same endpoint id and model, status PASS,
the current freeze and suite hashes, not expired, whose stored files match their hashes and whose records, re-scored here with
the frozen checks and the reference labels (verify()), give PASS again with the same metrics; else None. So a hand-edited
"status": "PASS" opens nothing: a forger has to produce suite records that really pass the frozen checks. Without
GLEICHLAUT_CERT_KEY nothing stops a writer of state/ from re-dating a certificate or copying passing records; the HMAC does.
The newest certificate for an endpoint+model decides (a later FAIL revokes an earlier PASS).

Canary gate (canary_gate(), used by draft / month on the SL lane): the newest canary report for the certificate in use must
have passed, and the newest check (that canary, or the certification itself) must be at most GLEICHLAUT_CANARY_MAX_AGE_DAYS
old (default 31). A failed canary refuses (exit 3) until a later canary passes or the endpoint is re-certified; a stale one
refuses unless --allow-stale-canary is given (logged to state/gate-overrides.jsonl and summary.json).

Canary (`--canary [N]`, default 40 items): re-runs the first N suite items and compares them with the certified run of the
same endpoint+model on the same items. Byte identity is reported as information only: at temperature 0 the 70B lane is not
deterministic (eval/results/m3.json: a seeded re-run of the fresh 166 gave 69.9% identical outputs, flag agreement 163/166 =
98.2%, kappa 0.963, exact 17.5% -> 18.1%; on the first 40 items agreement 97.5%, exact 12.5% -> 15.0%). The canary fails
(exit 3) only on
  flag agreement < 0.85        (8x the measured disagreement of 1.8%: the guards now see a different model)
  exact drop > 5 points        (8x the measured change of +0.6 points, and the pass rule's minimum gain over rules-only)
  a served model id not seen at certification.
A system_fingerprint not seen at certification is a warning (recorded in the report), not a failure. Reports are never
overwritten: state/canary/canary-<endpoint>--<model>-<UTC time>[-N].json."""
import argparse, datetime, hashlib, hmac, json, os, re, sys, time
from concurrent.futures import ThreadPoolExecutor
from . import core, score, backends

EVIDENCE = os.path.join(core.ROOT, "eval", "certificates")       # shipped evidence; never authorises
ITEMS = "items/items_fresh.json"
CANARY_N = 40
CANARY_MIN_FLAG_AGREEMENT = 0.85
CANARY_MAX_EXACT_DROP = 5.0
LABEL_CLASSES = ("equivalent", "preexisting", "cosmetic", "minor", "german", "stale", "REAL", "garble")
# the shipped build certificates (PREREG R1): M2 Q8_0 (the default build, cli.BUILD) and M1 Q4_K_M (an 8 GiB box)
BUILD_NAMES = {"q8_0": "8b-q8_0-fresh166", "q4_k_m": "8b-q4_k_m-fresh166"}
BUILD_NAME = BUILD_NAMES["q8_0"]                                     # the default build's certificate
M1_RUN, M1_LABELS = "data/runs/8b_q4_k_m_fresh166_g3_final.jsonl", "eval/labels/m1_q4_k_m_fresh166.tsv"
M2_RUN, M2_LABELS = "data/runs/8b_q8_0_fresh166_g3_final.jsonl", "eval/labels/m1_q8_0_fresh166.tsv"
GGUF_SHA_Q4 = "a037df8d87ff6caacee794ee85f55342f2152e0d359b7389033300c3bee5f299"     # M1, eval/certificates/8b-q4_k_m-fresh166.json
GGUF_SHA_Q8 = "dea904ad80cd725ec89962abae464477f5d8114d1f4377514f381f7dc2ed202d"     # M2, eval/certificates/8b-q8_0-fresh166.json
SECS_PER_ITEM = {GGUF_SHA_Q8: 200.5, GGUF_SHA_Q4: 153.4}            # measured on 4 cores (eval/results/m1_<build>.json)
EXIT = dict(PASS=0, FAIL=5, PENDING_REVIEW=7)
CERT_DAYS = 90
CANARY_MAX_AGE_DAYS = 31


def _days(var, default):
    v = os.environ.get(var)
    try: return float(v) if v not in (None, "") else float(default)
    except ValueError: raise backends.ConfigError(f"{var} must be a number of days, got {v!r}")


def cert_days(): return _days("GLEICHLAUT_CERT_DAYS", CERT_DAYS)
def canary_max_age_days(): return _days("GLEICHLAUT_CANARY_MAX_AGE_DAYS", CANARY_MAX_AGE_DAYS)


def state_dir(*parts):
    base = os.environ.get("GLEICHLAUT_STATE") or os.path.join(core.ROOT, "state")
    return os.path.join(os.path.abspath(base), *parts)


def _now(): return datetime.datetime.now(datetime.timezone.utc)


def reference_labels():
    """norm(output) -> label, for every hand-labelled or exact output of the reference fresh-166 run (per item key)."""
    I = {x["key"]: x for x in score.load_items(ITEMS)}
    F = score.load_jsonl(score.RUNS["fresh166"]["final"])
    lab = score.load_labels(score.RUNS["fresh166"]["labels"])
    ref = {}
    for k, f in F.items():
        o = core.lock.norm(f["out"])
        if o == core.lock.norm(I[k]["tgt_new"]): ref[k] = {o: "exact"}
        elif k in lab: ref[k] = {o: lab[k]}
    return ref


def run_suite(ask, n=None, workers=2):
    I = score.load_items(ITEMS)[:n] if n else score.load_items(ITEMS)
    P = core.Pipeline(ask, "g3")
    t0 = time.time(); ex = ThreadPoolExecutor(max(1, workers)); futs = []
    try:
        futs = [ex.submit(P.run, x) for x in I]
        R = [f.result() for f in futs]
    except BaseException:
        for f in futs: f.cancel()              # a dead endpoint stops the run now, not after every queued item has timed out
        raise
    finally:
        ex.shutdown(wait=True)
    return I, R, time.time() - t0


def evaluate(I, R, extra_labels=None):
    S = core.SCORE; ref = reference_labels(); chk = core.check_only("g3")
    for k, d in (extra_labels or {}).items(): ref.setdefault(k, {}).update(d)
    rows1, rows2, review = [], [], []
    for x, r in zip(I, R):
        r1, _ = core.gl2.rules(x["de_old"], x["de_new"], x["tgt_old"], x["lang"])
        a = S["score_one"](x, r1, "1"); b = S["score_one"](x, r["out"], "1")
        flag = chk.check(x, r["out"])["flag"]
        assert flag == r["guard_flag"], x["key"]
        cls = "exact" if b["exact"] else ref.get(x["key"], {}).get(core.lock.norm(r["out"]), "?")
        if not flag and cls == "?": review.append(x["key"])
        b.update(flagged=flag, cls=cls, family=x["cluster"], reasked=r.get("reasked", False), replaced=bool(r.get("replaced")))
        a.update(family=x["cluster"]); rows1.append(a); rows2.append(b)
    s = score.summarise(rows1, rows2, labelled=True)
    auto_ok = s["pass_rule"]["exact_gain"][1] and s["pass_rule"]["flag_rate"][1]
    inherited_ok = s["pass_rule"]["unflagged_real"][1] and s["pass_rule"]["unflagged_stale_untranslated"][1]
    status = "FAIL" if not (auto_ok and inherited_ok) else ("PENDING_REVIEW" if review else "PASS")
    digits = sum(r.get("digits_raw", 0) > 0 or r.get("reask_digits", 0) > 0 for r in R)
    return s, status, review, digits


def certificate(name, kind, endpoint, model, I, R, secs, served, seeds, fingerprints=(), extra_labels=None):
    s, status, review, digits = evaluate(I, R, extra_labels)
    return dict(name=name, kind=kind, date=_now().isoformat(timespec="seconds"),
                endpoint=endpoint, model_requested=model, models_served=sorted(served),
                system_fingerprints=sorted(f for f in fingerprints if f), seeds=sorted(seeds),
                suite=dict(items=ITEMS, n=len(I), sha256=core.sha256(os.path.join(core.ROOT, "data", ITEMS))),
                freeze_sha256=core.sha256(core.FREEZE), pass_rule=score.PASS_RULE, status=status,
                metrics={k: s[k] for k in ("exact", "ef1", "chrf", "flag_rate", "ready_rate", "unflagged", "unflagged_REAL",
                                           "unflagged_stale", "unflagged_german", "pass_rule")},
                needs_review=review, items_with_model_digits=digits, wall_secs=round(secs, 1),
                run_records=f"runs/certify_{name}.jsonl", calls_log=f"certificates/{name}.calls.jsonl")


# ------------------------------------------------------------------ integrity: hashes, expiry, optional HMAC
def _canon(c): return json.dumps({k: v for k, v in c.items() if k != "hmac_sha256"}, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def cert_key():
    """the HMAC key (bytes) from the file named by GLEICHLAUT_CERT_KEY, or None when the variable is unset."""
    p = os.environ.get("GLEICHLAUT_CERT_KEY")
    if not p: return None
    try:
        with open(p, "rb") as f: k = f.read().strip()
    except OSError as e:
        raise backends.ConfigError(f"GLEICHLAUT_CERT_KEY names {p!r}, which cannot be read: {e.strerror or e}")
    if len(k) < 16: raise backends.ConfigError(f"the certificate key in {p!r} is shorter than 16 bytes")
    return k


def sign(c):
    k = cert_key()
    c.pop("hmac_sha256", None)
    if k: c["hmac_sha256"] = hmac.new(k, _canon(c).encode("utf-8"), hashlib.sha256).hexdigest()
    return c


def check_signature(c):
    """-> None if acceptable, else the reason. With no key configured, signatures are not checked."""
    k = cert_key()
    if not k: return None
    if "hmac_sha256" not in c: return "unsigned, but GLEICHLAUT_CERT_KEY is set (every certificate and canary report must be signed)"
    if not hmac.compare_digest(c["hmac_sha256"], hmac.new(k, _canon(c).encode("utf-8"), hashlib.sha256).hexdigest()):
        return "HMAC does not match (edited, or signed with another key)"
    return None


def _write_json(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f: json.dump(obj, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def _unique(path):
    """path, or path with -2, -3, ... before the extension: nothing is ever overwritten."""
    base, ext = os.path.splitext(path); n = 1
    while os.path.exists(path): n += 1; path = f"{base}-{n}{ext}"
    return path


def _parse_date(s):
    try:
        d = datetime.datetime.fromisoformat(str(s).replace("Z", "+00:00"))
        return d if d.tzinfo else d.replace(tzinfo=datetime.timezone.utc)
    except ValueError: return None


def write_certificate(name, kind, endpoint, model, I, R, secs, served, seeds, fps, calls_log, extra_labels=None, labels_file=None,
                      valid_days=None, date=None):
    """write the suite records and the certificate (hashes of records, call log and labels; expiry; HMAC if a key is set)."""
    for d in ("certificates", "runs"): os.makedirs(state_dir(d), exist_ok=True)
    runs = state_dir("runs", f"certify_{name}.jsonl")
    with open(runs, "w", encoding="utf-8") as f:
        for r in R: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    if not os.path.exists(calls_log): open(calls_log, "a").close()
    c = certificate(name, kind, endpoint, model, I, R, secs, served, seeds, fps, extra_labels)
    if date: c["date"] = date
    days = float(valid_days) if valid_days is not None else cert_days()
    c.update(valid_days=days, expires=(_parse_date(c["date"]) + datetime.timedelta(days=days)).isoformat(timespec="seconds"),
             run_records_sha256=core.sha256(runs), calls_log=os.path.relpath(calls_log, state_dir()),
             calls_log_sha256=core.sha256(calls_log))
    if labels_file:
        c.update(review_labels_file=os.path.relpath(labels_file, state_dir()), labels_sha256=core.sha256(labels_file))
    sign(c)
    p = state_dir("certificates", f"{name}.json")
    _write_json(p, c)
    return p, c


def read_labels(path, R):
    """TSV key<TAB>class -> ({key: {norm(output): class}}, bad lines)."""
    lines = [l for l in open(path, encoding="utf-8").read().splitlines() if l.strip()]
    if not lines or lines[0].split("\t")[:2] != ["key", "class"]: return None, ["the labels file must be a TSV with the header 'key<TAB>class'"]
    extra, bad = {}, []
    for l in lines[1:]:
        k, cls = (l.split("\t") + [""])[:2]
        if cls not in LABEL_CLASSES or k not in R: bad.append(l); continue
        extra[k] = {core.lock.norm(R[k]["out"]): cls}
    return extra, bad


_VERIFIED = {}


def verify(c, now=None):
    """-> None if the certificate holds, else the reason. Re-checks everything the certificate claims (see the module doc)."""
    now = now or _now(); name = c.get("name")
    if c.get("kind") == "build": return verify_build(c)
    if c.get("kind") != "endpoint": return f"certificate {name} is of kind {c.get('kind')!r}: evidence only, never authorises"
    void = _resources_void()
    if void: return void
    if c.get("status") != "PASS": return f"certificate {name} has status {c.get('status')}"
    bad = check_signature(c)
    if bad: return f"certificate {name}: {bad}"
    if c.get("freeze_sha256") != core.sha256(core.FREEZE):
        return f"certificate {name} was made with other frozen code (freeze sha256 changed): re-certify"
    if (c.get("suite") or {}).get("sha256") != core.sha256(os.path.join(core.ROOT, "data", ITEMS)):
        return f"certificate {name} was made on another suite: re-certify"
    made = _parse_date(c.get("date"))
    if made is None: return f"certificate {name} has no valid date"
    if made > now + datetime.timedelta(hours=1): return f"certificate {name} is dated in the future ({c.get('date')})"
    stored = _parse_date(c.get("expires"))
    if stored is None or not all(c.get(k) for k in ("run_records_sha256", "calls_log_sha256")):
        return f"certificate {name} has no integrity fields (made by an older Gleichlaut): re-certify"
    exp = min(stored, made + datetime.timedelta(days=cert_days()))
    if now > exp: return f"certificate {name} expired on {exp.date().isoformat()} (made {made.date().isoformat()}; validity {cert_days():g} days): re-certify"
    files = [("run_records", c.get("run_records"), c["run_records_sha256"]), ("call log", c.get("calls_log"), c["calls_log_sha256"])]
    if c.get("review_labels_file") or c.get("labels_sha256"):
        files.append(("review labels", c.get("review_labels_file"), c.get("labels_sha256")))
    paths = {}
    for what, rel, want in files:
        p = state_dir(rel or "-")
        if not rel or not os.path.isfile(p): return f"certificate {name}: its {what} file is missing ({rel})"
        if core.sha256(p) != want: return f"certificate {name}: its {what} file ({rel}) does not match the sha256 in the certificate"
        paths[what] = p
    ck = (name, c["run_records_sha256"], c["calls_log_sha256"], c.get("labels_sha256"), json.dumps(c.get("metrics"), sort_keys=True),
          json.dumps(c.get("models_served")), core.sha256(core.FREEZE))
    if ck in _VERIFIED: return _VERIFIED[ck]
    _VERIFIED[ck] = why = _recheck(c, paths)
    return why


def _recheck(c, paths):
    """re-score the stored records with the frozen checks; the result must be the certificate's own PASS."""
    name = c.get("name")
    try:
        R = [json.loads(l) for l in open(paths["run_records"], encoding="utf-8") if l.strip()]
        I = score.load_items(ITEMS)
        if [r.get("key") for r in R] != [x["key"] for x in I]:
            return f"certificate {name}: its records do not cover the {len(I)} suite items in order"
        extra = None
        if "review labels" in paths:
            extra, bad = read_labels(paths["review labels"], {r["key"]: r for r in R})
            if extra is None or bad: return f"certificate {name}: its review labels file is not valid"
        s, status, review, _ = evaluate(I, R, extra)
    except AssertionError as e:
        return f"certificate {name}: a stored guard verdict differs from the frozen checks ({e})"
    except (ValueError, KeyError, TypeError, OSError) as e:
        return f"certificate {name}: its records cannot be re-scored ({type(e).__name__}: {e})"
    if status != "PASS": return f"certificate {name}: its records re-score to {status}, not PASS"
    want = {k: s[k] for k in (c.get("metrics") or {})}
    if json.loads(json.dumps(want)) != c.get("metrics") or review != c.get("needs_review"):
        return f"certificate {name}: the metrics in the certificate differ from its re-scored records"
    calls = []
    for l in open(paths["call log"], encoding="utf-8"):
        try: calls.append(json.loads(l))
        except ValueError: return f"certificate {name}: its call log has a line that is not JSON"
    need = sum(not r.get("rule_only") for r in R)
    if len(calls) < need: return f"certificate {name}: its call log has {len(calls)} calls for {need} model-drafted items"
    eps = {x.get("endpoint") for x in calls}
    if eps != {c.get("endpoint")}: return f"certificate {name}: its call log names other endpoints {sorted(e for e in eps if e)}"
    if sorted({x.get("model_served") or "" for x in calls}) != sorted(c.get("models_served") or []):
        return f"certificate {name}: the models served in its call log differ from the certificate"
    return None


def _resources_void():
    from . import resources
    if resources.active():
        return (f"custom check resources are in use (GLEICHLAUT_RESOURCES={resources.active()}): every certificate is void "
                f"with resources other than the frozen ones; every draft goes to review")
    return None


# ------------------------------------------------------------------ build certificates (local GGUF, the SL default lane)
def read_label_table(path, R, extra_classes=()):
    """labels file -> ({key: {norm(output): class}}, bad lines). Accepts 'key<TAB>class' or a table with a 'final' column
    (the M1 annotation file: two blind annotators + tie-break). Rows for keys outside R are bad."""
    lines = [l for l in open(path, encoding="utf-8").read().splitlines() if l.strip()]
    if not lines: return None, ["the labels file is empty"]
    hdr = lines[0].split("\t")
    col = 1 if hdr[:2] == ["key", "class"] else (hdr.index("final") if hdr[0] == "key" and "final" in hdr else None)
    if col is None: return None, ["the labels file must be a TSV with the header 'key<TAB>class' (or a 'final' column)"]
    ok = set(LABEL_CLASSES) | set(extra_classes); extra, bad = {}, []
    for l in lines[1:]:
        c = l.split("\t") + [""] * len(hdr)
        k, cls = c[0], c[col]
        if cls not in ok or k not in R: bad.append(l); continue
        extra[k] = {core.lock.norm(R[k]["out"]): cls}
    return extra, bad


def _base(c):
    return core.ROOT if c.get("files_base") == "root" else state_dir()


def build_dirs():
    """where build certificates are looked up: the state directory, then the shipped evidence."""
    return [state_dir("certificates"), EVIDENCE]


def build_certificates():
    out = []
    for d in build_dirs():
        if not os.path.isdir(d): continue
        for f in sorted(os.listdir(d)):
            if not f.endswith(".json"): continue
            try:
                with open(os.path.join(d, f), encoding="utf-8") as fh: c = json.load(fh)
            except (OSError, ValueError): continue
            if isinstance(c, dict) and c.get("kind") == "build": out.append((os.path.join(d, f), c))
    return sorted(out, key=lambda pc: (pc[1].get("date", ""), os.path.getmtime(pc[0])))


def verify_build(c):
    """-> None if the build certificate holds, else the reason: signature, freeze and suite hashes, stored files against
    their sha256, and the stored records re-scored with the frozen checks and the stored labels to the same PASS."""
    name = c.get("name")
    void = _resources_void()
    if void: return void
    if c.get("status") != "PASS": return f"build certificate {name} has status {c.get('status')}"
    bad = check_signature(c)
    if bad: return f"build certificate {name}: {bad}"
    if c.get("freeze_sha256") != core.sha256(core.FREEZE):
        return f"build certificate {name} was made with other frozen code (freeze sha256 changed): re-certify"
    if (c.get("suite") or {}).get("sha256") != core.sha256(os.path.join(core.ROOT, "data", ITEMS)):
        return f"build certificate {name} was made on another suite: re-certify"
    if not ((c.get("gguf") or {}).get("sha256") and c.get("run_records_sha256") and c.get("labels_sha256")):
        return f"build certificate {name} has no integrity fields"
    files = [("run_records", c.get("run_records"), c["run_records_sha256"]), ("labels", c.get("labels_file"), c["labels_sha256"])]
    if c.get("calls_log"): files.append(("call log", c["calls_log"], c.get("calls_log_sha256")))
    paths = {}
    for what, rel, want in files:
        p = os.path.join(_base(c), rel or "-")
        if not rel or not os.path.isfile(p): return f"build certificate {name}: its {what} file is missing ({rel})"
        if core.sha256(p) != want: return f"build certificate {name}: its {what} file ({rel}) does not match the sha256 in the certificate"
        paths[what] = p
    ck = ("build", name, c["run_records_sha256"], c["labels_sha256"], json.dumps(c.get("metrics"), sort_keys=True), core.sha256(core.FREEZE))
    if ck in _VERIFIED: return _VERIFIED[ck]
    try:
        R = [json.loads(l) for l in open(paths["run_records"], encoding="utf-8") if l.strip()]
        I = score.load_items(ITEMS)
        if [r.get("key") for r in R] != [x["key"] for x in I]:
            why = f"build certificate {name}: its records do not cover the {len(I)} suite items in order"
        else:
            extra, bad = read_label_table(paths["labels"], {r["key"]: r for r in R}, ("exact",))
            if extra is None: why = f"build certificate {name}: its labels file is not valid"
            else:
                s_, status, review, _ = evaluate(I, R, extra)
                want = {k: s_[k] for k in (c.get("metrics") or {})}
                if status != "PASS": why = f"build certificate {name}: its records re-score to {status}, not PASS"
                elif json.loads(json.dumps(want)) != c.get("metrics") or review != c.get("needs_review"):
                    why = f"build certificate {name}: the metrics in the certificate differ from its re-scored records"
                else: why = None
    except AssertionError as e:
        why = f"build certificate {name}: a stored guard verdict differs from the frozen checks ({e})"
    except (ValueError, KeyError, TypeError, OSError) as e:
        why = f"build certificate {name}: its records cannot be re-scored ({type(e).__name__}: {e})"
    _VERIFIED[ck] = why
    return why


def build_lookup(gguf_sha256, runtime=None):
    """-> (certificate or None, reason) for a local GGUF: kind 'build', the same GGUF sha256 and (when given) the same
    llama-cpp-python version; the newest such certificate decides (a later FAIL revokes an earlier PASS)."""
    allc = [c for _, c in build_certificates() if (c.get("gguf") or {}).get("sha256") == gguf_sha256]
    if not allc:
        return None, (f"no build certificate for the GGUF with sha256 {gguf_sha256[:12]}... in "
                      f"{' or '.join(build_dirs())} (certify it: gleichlaut certify --backend llamacpp --gguf PATH)")
    cands = [c for c in allc if runtime is None or (c.get("runtime") or {}).get("llama_cpp_python") == runtime]
    if not cands:
        vs = sorted({str((c.get("runtime") or {}).get("llama_cpp_python")) for c in allc})
        return None, (f"the build certificates for GGUF {gguf_sha256[:12]}... were made with llama-cpp-python {', '.join(vs)}, "
                      f"this is {runtime}: use the offline image, or re-certify (gleichlaut certify --backend llamacpp --gguf PATH)")
    c = cands[-1]
    if c.get("status") != "PASS":
        return None, f"the newest build certificate for GGUF {gguf_sha256[:12]}... ({c.get('name')}) has status {c.get('status')}"
    why = verify_build(c)
    if why: return None, why
    return c, (f"build certificate {c.get('name')} ({c.get('date')}, GGUF sha256 {gguf_sha256[:12]}..., llama-cpp-python "
               f"{(c.get('runtime') or {}).get('llama_cpp_python')}; verified: records re-scored, hashes match"
               f"{', HMAC ok' if cert_key() else ''})")


def m1_inherited_labels(R):
    """labels of the M1 and M2 runs (two blind annotators + tie-break each) for outputs identical to the M1 or M2 output
    of the same item."""
    known = {}
    for run, labels in ((M1_RUN, M1_LABELS), (M2_RUN, M2_LABELS)):
        p = os.path.join(core.ROOT, labels)
        if not os.path.exists(p): continue
        lab, _ = read_label_table(p, score.load_jsonl(run.split("data/", 1)[1]), ("exact",))
        for k, d in (lab or {}).items(): known.setdefault(k, {}).update(d)
    out = {}
    for k, d in known.items():
        if k in R and core.lock.norm(R[k]["out"]) in d: out[k] = d[core.lock.norm(R[k]["out"])]
    return out


def write_build_certificate(name, I, R, secs, gguf_sha256, gguf_file, runtime, runtime_source, source, labels_rows=None,
                            labels_path=None, records_path=None, calls_log=None, dest=None, date=None):
    """write a build certificate. Records and labels inside track_2b/ are referenced in place (files_base 'root', used for
    the shipped evidence); otherwise they are copied into the state directory (files_base 'state')."""
    dest = os.path.abspath(dest or state_dir("certificates")); os.makedirs(dest, exist_ok=True)
    root = os.path.abspath(core.ROOT) + os.sep
    in_root = lambda p: p is not None and os.path.abspath(p).startswith(root)
    base = "root" if dest.startswith(root) and not dest.startswith(state_dir() + os.sep) and in_root(records_path) and in_root(labels_path) else "state"
    if base == "root":
        rec_rel, lab_rel = os.path.relpath(records_path, core.ROOT), os.path.relpath(labels_path, core.ROOT)
    else:
        os.makedirs(state_dir("runs"), exist_ok=True); os.makedirs(state_dir("certificates"), exist_ok=True)
        rec_rel = os.path.join("runs", f"certify_{name}.jsonl")
        with open(state_dir(rec_rel), "w", encoding="utf-8") as f:
            for r in R: f.write(json.dumps(r, ensure_ascii=False) + "\n")
        lab_rel = os.path.join("certificates", f"{name}.labels.tsv")
        if labels_path:
            with open(labels_path, encoding="utf-8") as src, open(state_dir(lab_rel), "w", encoding="utf-8") as dst: dst.write(src.read())
        else:
            with open(state_dir(lab_rel), "w", encoding="utf-8") as f:
                f.write("key\tclass\n" + "".join(f"{k}\t{v}\n" for k, v in sorted((labels_rows or {}).items())))
    bp = lambda rel: os.path.join(core.ROOT if base == "root" else state_dir(), rel)
    extra, bad = read_label_table(bp(lab_rel), {r["key"]: r for r in R}, ("exact",))
    if extra is None: raise backends.ConfigError(f"labels file {labels_path}: {bad[0]}")
    s_, status, review, digits = evaluate(I, R, extra)
    c = dict(name=name, kind="build", kind_note="a local GGUF build run in process by llama.cpp: authorises the SL lane for "
             "exactly this GGUF sha256 and llama-cpp-python version (certify.build_lookup)",
             date=date or _now().isoformat(timespec="seconds"), endpoint="local llama.cpp (in process)",
             model_requested="Apertus v1.5 8B GGUF", models_served=["gguf:" + (gguf_file or "?")],
             gguf=dict(sha256=gguf_sha256, file=gguf_file), runtime=dict(llama_cpp_python=runtime, source=runtime_source),
             source=source, suite=dict(items=ITEMS, n=len(I), sha256=core.sha256(os.path.join(core.ROOT, "data", ITEMS))),
             freeze_sha256=core.sha256(core.FREEZE), pass_rule=score.PASS_RULE, status=status,
             metrics={k: s_[k] for k in ("exact", "ef1", "chrf", "flag_rate", "ready_rate", "unflagged", "unflagged_REAL",
                                         "unflagged_stale", "unflagged_german", "pass_rule")},
             needs_review=review, items_with_model_digits=digits, wall_secs=round(secs, 1),
             files_base=base, run_records=rec_rel, run_records_sha256=core.sha256(bp(rec_rel)),
             labels_file=lab_rel, labels_sha256=core.sha256(bp(lab_rel)), labels_n=len(extra), expires=None,
             expires_note="a build certificate does not expire: the GGUF, the library version and the frozen code are hashed")
    if calls_log and os.path.exists(calls_log):
        c.update(calls_log=os.path.relpath(calls_log, state_dir()), calls_log_sha256=core.sha256(calls_log))
    sign(c)
    p = os.path.join(dest, f"{name}.json")
    _write_json(p, c)
    return p, c


def import_run(records, gguf_sha256, labels, name=None, runtime=None, dest=None, gguf_file=None):
    """certify a GGUF build from a recorded suite run (e.g. the M1 shards of the GitHub Actions CPU runners)."""
    if not re.fullmatch(r"[0-9a-f]{64}", gguf_sha256 or ""): raise backends.ConfigError("--gguf-sha256 must be 64 hex digits")
    for what, p in (("records", records), ("labels", labels)):
        if not p or not os.path.isfile(p): raise backends.ConfigError(f"{what} file not found: {p!r}")
    I = score.load_items(ITEMS)
    try: R = {json.loads(l)["key"]: json.loads(l) for l in open(records, encoding="utf-8") if l.strip()}
    except (ValueError, KeyError) as e: raise backends.ConfigError(f"records file {records} is not JSON Lines with a 'key' per line: {e}")
    missing = [x["key"] for x in I if x["key"] not in R]
    if missing: raise backends.ConfigError(f"records file {records} misses {len(missing)} of the {len(I)} suite items, e.g. {missing[:3]}")
    RR = [R[x["key"]] for x in I]
    if runtime is None:
        runtime, src = pinned_llama(), "requirements-offline.txt pin (the version the M1 workflow installed)"
    else: src = "--llama-cpp-version"
    secs = sum(float(r.get("wall_secs") or 0) for r in RR)
    gf = gguf_file or {GGUF_SHA_Q4: "apertus-v1.5-8b-text-q4_k_m.gguf", GGUF_SHA_Q8: "apertus-v1.5-8b-text-q8_0.gguf"}.get(gguf_sha256)
    return write_build_certificate(name or f"build-{gguf_sha256[:12]}-{_now().strftime('%Y%m%dT%H%M%SZ')}", I, RR, secs, gguf_sha256, gf,
                                   runtime, src, f"imported run {os.path.relpath(os.path.abspath(records), core.ROOT)}",
                                   labels_path=labels, records_path=records, dest=dest)


def pinned_llama():
    try:
        for l in open(os.path.join(core.ROOT, "requirements-offline.txt"), encoding="utf-8"):
            m = re.match(r"\s*llama-cpp-python==([^\s\\;]+)", l)
            if m: return m.group(1)
    except OSError: pass
    return None


# ------------------------------------------------------------------ lookup
def certificates():
    """-> [(path, certificate)] in the state directory, oldest first."""
    d = state_dir("certificates"); out = []
    if not os.path.isdir(d): return out
    for f in sorted(os.listdir(d)):
        if not f.endswith(".json"): continue
        try:
            with open(os.path.join(d, f), encoding="utf-8") as fh: c = json.load(fh)
        except (OSError, ValueError): continue
        if isinstance(c, dict): out.append((os.path.join(d, f), c))
    return sorted(out, key=lambda pc: (pc[1].get("date", ""), os.path.getmtime(pc[0])))


def lookup(base_url, model):
    """-> (certificate or None, reason). Only kind 'endpoint', exact endpoint id and model, newest decides."""
    ep = backends.endpoint_id(base_url)
    cands = [c for _, c in certificates() if c.get("kind") == "endpoint" and c.get("endpoint") == ep and c.get("model_requested") == model]
    if not cands: return None, f"no endpoint certificate for {model} at {ep} in {state_dir('certificates')}"
    c = cands[-1]
    if c.get("status") != "PASS":
        return None, f"the newest certificate for {model} at {ep} ({c.get('name')}) has status {c.get('status')}"
    why = verify(c)
    if why: return None, why
    return c, (f"certificate {c.get('name')} ({c.get('date')}, verified: records re-scored, hashes match"
               f"{', HMAC ok' if cert_key() else ''}; expires {str(c.get('expires'))[:10]})")


def certified(base_url, model):
    """The certification gate of the SL lane: the PASS endpoint certificate for exactly this endpoint and model, or None."""
    return lookup(base_url, model)[0]


# ------------------------------------------------------------------ canary
def canary_report(I, R, ref, served=(), cert=None, fingerprints=()):
    S = core.SCORE; rows = []
    for x, r in zip(I, R):
        f = ref.get(x["key"])
        if f is None: continue
        rows.append(dict(key=x["key"], same_output=r["out"] == f["out"], same_flag=r["guard_flag"] == f["guard_flag"],
                         flag_now=r["guard_flag"], flag_ref=f["guard_flag"],
                         exact_now=bool(S["score_one"](x, r["out"], "1")["exact"]), exact_ref=bool(S["score_one"](x, f["out"], "1")["exact"])))
    n = len(rows)
    if not n: return dict(ok=False, n=0, reasons=["no canary item found in the reference run"])
    agree = sum(d["same_flag"] for d in rows) / n
    ex_now, ex_ref = 100 * sum(d["exact_now"] for d in rows) / n, 100 * sum(d["exact_ref"] for d in rows) / n
    reasons = []
    if agree < CANARY_MIN_FLAG_AGREEMENT: reasons.append(f"flag agreement {agree:.3f} < {CANARY_MIN_FLAG_AGREEMENT}")
    if ex_ref - ex_now > CANARY_MAX_EXACT_DROP: reasons.append(f"exact dropped {ex_ref - ex_now:.1f} points > {CANARY_MAX_EXACT_DROP}")
    new_served = sorted(set(s for s in served if s) - set((cert or {}).get("models_served", []))) if cert else []
    if new_served: reasons.append(f"served model(s) not seen at certification: {new_served}")
    warnings = []
    then = set((cert or {}).get("system_fingerprints") or [])
    new_fp = sorted(set(f for f in fingerprints if f) - then) if then else []
    if new_fp:
        warnings.append(f"system_fingerprint changed: now {new_fp}, at certification {sorted(then)} (the serving build changed; "
                         f"within tolerance, but consider re-certifying)")
    return dict(ok=not reasons, reasons=reasons, warnings=warnings, fingerprint_changed=bool(new_fp), n=n,
                tolerances=dict(min_flag_agreement=CANARY_MIN_FLAG_AGREEMENT, max_exact_drop_pts=CANARY_MAX_EXACT_DROP,
                                derived_from="eval/results/m3.json (seeded re-run of the fresh 166)"),
                flag_agreement=round(agree, 3), exact_now_pct=round(ex_now, 1), exact_ref_pct=round(ex_ref, 1),
                flag_rate_now_pct=round(100 * sum(d["flag_now"] for d in rows) / n, 1),
                flag_rate_ref_pct=round(100 * sum(d["flag_ref"] for d in rows) / n, 1),
                info=dict(byte_identical=sum(d["same_output"] for d in rows), byte_identical_pct=round(100 * sum(d["same_output"] for d in rows) / n, 1),
                          note="byte identity is information only: measured 69.9% at temperature 0 (eval/results/m3.json)"),
                flag_changes=[d["key"] for d in rows if not d["same_flag"]])


def canary_reports(endpoint=None, model=None, cert_name=None):
    """-> [(path, report)] in state/canary/, oldest first, optionally for one endpoint / model / certificate."""
    d = state_dir("canary"); out = []
    if not os.path.isdir(d): return out
    for f in sorted(os.listdir(d)):
        if not f.endswith(".json"): continue
        try:
            with open(os.path.join(d, f), encoding="utf-8") as fh: r = json.load(fh)
        except (OSError, ValueError): continue
        if not isinstance(r, dict): continue
        if endpoint and r.get("endpoint") != endpoint: continue
        if model and r.get("model") != model: continue
        if cert_name and r.get("certificate") != cert_name: continue
        out.append((os.path.join(d, f), r))
    return sorted(out, key=lambda pr: (pr[1].get("date", ""), os.path.getmtime(pr[0])))


def canary_gate(cert, max_age_days=None, now=None):
    """-> (state, reason): state 'ok' | 'failed' | 'stale'. The newest canary for this certificate decides; with none since
    certification, the certification itself is the latest check."""
    now = now or _now(); max_age = canary_max_age_days() if max_age_days is None else float(max_age_days)
    reps = [(p, r) for p, r in canary_reports(cert.get("endpoint"), cert.get("model_requested"), cert.get("name"))]
    unsigned = [p for p, r in reps if check_signature(r)]
    reps = [(p, r) for p, r in reps if not check_signature(r)]
    note = f" ({len(unsigned)} report(s) ignored: not signed with GLEICHLAUT_CERT_KEY)" if unsigned else ""
    if reps:
        p, r = reps[-1]; when, what = _parse_date(r.get("date")), f"canary {os.path.basename(p)}"
        if not r.get("ok"):
            return "failed", (f"the latest canary for certificate {cert.get('name')} ({os.path.basename(p)}, {r.get('date')}) FAILED: "
                              f"{'; '.join(r.get('reasons') or [])}. Re-certify (make certify-endpoint), or draft with the local 8B (make month){note}")
    else:
        when, what = _parse_date(cert.get("date")), f"certification {cert.get('name')}"
    if when is None: return "stale", f"the date of the latest check ({what}) cannot be read{note}"
    age = (now - when).total_seconds() / 86400
    if age > max_age:
        return "stale", (f"the latest check of this endpoint ({what}, {when.date().isoformat()}) is {age:.0f} days old "
                         f"(> {max_age:g}; GLEICHLAUT_CANARY_MAX_AGE_DAYS). Run `make canary` first, or pass --allow-stale-canary{note}")
    return "ok", f"latest check: {what}, {when.date().isoformat()}, {age:.0f} day(s) ago, passed{note}"


def _read_log(log):
    served, seeds, fps = set(), set(), set()
    if os.path.exists(log):
        for l in open(log, encoding="utf-8"):
            try: c = json.loads(l)
            except ValueError: continue
            served.add(c.get("model_served") or ""); seeds.add(str(c.get("seed"))); fps.add(c.get("system_fingerprint") or c.get("backend"))
    return served, seeds, fps


def _slug(s): return re.sub(r"[^A-Za-z0-9.]+", "-", s).strip("-")[:80]


def resolve(cert_path, labels_path):
    """apply human labels (TSV: key<TAB>class) to the needs_review outputs of a PENDING_REVIEW certificate."""
    c = json.load(open(cert_path, encoding="utf-8"))
    bad = check_signature(c)
    if bad: print(f"error: certificate {cert_path}: {bad}"); return 2
    if c.get("kind") == "build": return resolve_build(cert_path, c, labels_path)
    runs = state_dir(c["run_records"])
    if not os.path.exists(runs): print(f"error: the suite records of this certificate are missing: {runs}"); return 2
    if c.get("run_records_sha256") and core.sha256(runs) != c["run_records_sha256"]:
        print(f"error: the suite records {runs} do not match the sha256 in the certificate"); return 2
    R = {json.loads(l)["key"]: json.loads(l) for l in open(runs, encoding="utf-8")}
    extra, bad = read_labels(labels_path, R)
    if extra is None: print("error: " + bad[0]); return 2
    if bad: print(f"error: {len(bad)} label line(s) with an unknown key or class (classes: {', '.join(LABEL_CLASSES)}): {bad[:3]}"); return 2
    I = [x for x in score.load_items(ITEMS) if x["key"] in R]
    keep = state_dir("certificates", f"{c['name']}.labels.tsv")
    with open(labels_path, encoding="utf-8") as src, open(keep, "w", encoding="utf-8") as dst: dst.write(src.read())
    log = state_dir(c.get("calls_log") or f"certificates/{c['name']}.calls.jsonl")
    _, new = write_certificate(c["name"], c["kind"], c["endpoint"], c["model_requested"], I, [R[x["key"]] for x in I],
                               c.get("wall_secs", 0), c.get("models_served", []), c.get("seeds", []), c.get("system_fingerprints", []),
                               log, extra, labels_file=keep, valid_days=c.get("valid_days"), date=c["date"])
    new.update(resolved=_now().isoformat(timespec="seconds"),
               review_labels=dict(path=os.path.basename(labels_path), sha256=core.sha256(keep), n=len(extra)))
    _write_json(state_dir("certificates", f"{c['name']}.json"), sign(new))
    print(f"certificate {cert_path}: {c['status']} -> {new['status']}  (still needs review: {len(new['needs_review'])})")
    return EXIT[new["status"]]


def resolve_build(cert_path, c, labels_path):
    """add human labels to a PENDING_REVIEW build certificate (its stored labels are kept; new rows win)."""
    base = _base(c); runs = os.path.join(base, c["run_records"])
    if not os.path.exists(runs) or core.sha256(runs) != c.get("run_records_sha256"):
        print(f"error: the suite records of this certificate are missing or do not match: {runs}"); return 2
    R = {json.loads(l)["key"]: json.loads(l) for l in open(runs, encoding="utf-8") if l.strip()}
    new, bad = read_label_table(labels_path, R)
    if new is None: print("error: " + bad[0]); return 2
    if bad: print(f"error: {len(bad)} label line(s) with an unknown key or class (classes: {', '.join(LABEL_CLASSES)}): {bad[:3]}"); return 2
    old, _ = read_label_table(os.path.join(base, c["labels_file"]), R, ("exact",))
    rows = {k: next(iter(d.values())) for k, d in (old or {}).items()}
    rows.update({k: next(iter(d.values())) for k, d in new.items()})
    I = score.load_items(ITEMS)
    p, n = write_build_certificate(c["name"], I, [R[x["key"]] for x in I], c.get("wall_secs", 0), c["gguf"]["sha256"], c["gguf"].get("file"),
                                   (c.get("runtime") or {}).get("llama_cpp_python"), (c.get("runtime") or {}).get("source"),
                                   c.get("source", "?"), labels_rows=rows, date=c["date"],
                                   calls_log=state_dir(c["calls_log"]) if c.get("calls_log") else None)
    print(f"build certificate {p}: {c['status']} -> {n['status']}  (still needs review: {len(n['needs_review'])})")
    return EXIT[n["status"]]


def run_build(a):
    """certify --backend llamacpp --gguf PATH: the frozen suite on this machine's CPU (slow: about 7-9 h on 4 cores)."""
    if not a.gguf: raise backends.ConfigError("--backend llamacpp needs --gguf PATH (the GGUF file to certify)")
    backends.require_llama()
    sha = backends.file_sha256(a.gguf)
    name = a.name or f"build-{sha[:12]}-{_now().strftime('%Y%m%dT%H%M%SZ')}"
    for d in ("certificates", "runs"): os.makedirs(state_dir(d), exist_ok=True)
    log = state_dir("certificates", f"{name}.calls.jsonl")
    ask = backends.LlamaCpp(a.gguf, backends.lang_of_prompt, log=log, gguf_sha256=sha)
    n = a.n or len(score.load_items(ITEMS))
    print(f"certify: build {os.path.basename(a.gguf)} sha256 {sha[:12]}... llama-cpp-python {ask.runtime}, {ask.n_threads} threads; "
          f"{n} items one at a time (measured {SECS_PER_ITEM.get(sha, 200.5)} s per item on 4 cores: about "
          f"{n * SECS_PER_ITEM.get(sha, 200.5) / 3600:.1f} h) -> {state_dir()}", flush=True)
    I, R, secs = run_suite(ask, a.n, 1)
    if a.n:
        print(json.dumps(evaluate(I, R)[0], indent=1)); return 0
    Rk = {r["key"]: r for r in R}
    p, c = write_build_certificate(name, I, R, secs, sha, os.path.basename(a.gguf), ask.runtime, "installed (llama_cpp)",
                                   "local run", labels_rows=m1_inherited_labels(Rk), calls_log=log)
    _print_cert(p, c)
    return EXIT[c["status"]]


def _print_cert(p, c):
    m = c["metrics"]; ci = m["exact"]["ci95"]
    print(f"certificate {p}\n  kind {c['kind']}  status {c['status']}  exact {m['exact']['delta']:+.1f} pts vs rules-only "
          f"(95% CI {ci[0]:+.1f} to {ci[1]:+.1f})  flagged {m['flag_rate']}%  ready {m['ready_rate']}%  "
          f"needs review {len(c['needs_review'])}  served by {c['models_served']}")
    if c["kind"] == "build":
        print(f"  GGUF sha256 {c['gguf']['sha256']}  llama-cpp-python {c['runtime']['llama_cpp_python']}  records sha256 "
              f"{c['run_records_sha256'][:12]}  labels sha256 {c['labels_sha256'][:12]}  "
              f"{'HMAC-signed' if 'hmac_sha256' in c else 'unsigned (set GLEICHLAUT_CERT_KEY to sign)'}")
    if c["status"] == "PENDING_REVIEW":
        print(f"  label the {len(c['needs_review'])} outputs listed in needs_review, then: "
              f"gleichlaut certify --resolve {p} --labels LABELS.tsv")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="gleichlaut certify", description="certify an endpoint on the frozen fresh-166 suite, or run the canary")
    ap.add_argument("--backend", choices=["openai", "llamacpp", "cache", "gateway"], default="openai",
                    help="openai: LLM_BASE_URL (endpoint certificate); llamacpp: a local GGUF (--gguf; build certificate, slow on CPU); "
                         "cache: replay of the recorded responses; gateway: development only")
    ap.add_argument("--gguf", help="--backend llamacpp: the GGUF file to certify")
    ap.add_argument("--import-run", metavar="RECORDS", help="certify a GGUF build from a recorded suite run (JSON Lines, one record per "
                    "suite item) instead of running it; needs --gguf-sha256 and --labels")
    ap.add_argument("--gguf-sha256", help="--import-run: sha256 of the GGUF the records were drafted with")
    ap.add_argument("--llama-cpp-version", help="--import-run: llama-cpp-python version of the run (default: the requirements-offline.txt pin)")
    ap.add_argument("--out", help="--import-run: certificate directory (default state/certificates; eval/certificates for shipped evidence)")
    ap.add_argument("--name", default=None)
    ap.add_argument("--n", type=int, default=None, help="first N items only (smoke test; never a certificate)")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--canary", type=int, nargs="?", const=CANARY_N, default=None,
                    help=f"re-run the first N items (default {CANARY_N}) and compare with the certified run")
    ap.add_argument("--against", default=None, help="canary reference records (default: the certified run of this endpoint+model)")
    ap.add_argument("--gw-dir", default=os.environ.get("GLEICHLAUT_GATEWAY_DIR"), help="development gateway checkout (env GLEICHLAUT_GATEWAY_DIR)")
    ap.add_argument("--tag", default="gleichlaut-certify"); ap.add_argument("--cap", type=float, default=1.0)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--resolve", metavar="CERT", help="apply human labels to a PENDING_REVIEW certificate (needs --labels)")
    ap.add_argument("--labels", metavar="TSV", help="--resolve: human labels (key<TAB>class); --import-run: the run's labels "
                    "(key<TAB>class, or a table with a 'final' column)")
    ap.add_argument("--list", action="store_true", help="list the certificates in the state directory, each re-verified")
    ap.add_argument("--valid-days", type=float, default=None, help=f"certificate validity in days (default GLEICHLAUT_CERT_DAYS or {CERT_DAYS})")
    a = ap.parse_args(argv)
    try:
        cert_key(); cert_days(); canary_max_age_days()
    except backends.ConfigError as e:
        print(f"error: {e}"); return 2
    if a.import_run:
        if not (a.gguf_sha256 and a.labels): ap.error("--import-run needs --gguf-sha256 and --labels")
        try: p, c = import_run(a.import_run, a.gguf_sha256, a.labels, a.name, a.llama_cpp_version, a.out)
        except backends.ConfigError as e: print(f"error: {e}"); return 2
        _print_cert(p, c); return EXIT[c["status"]]
    if a.backend == "llamacpp" and not a.list and not a.resolve:
        if a.canary: print("error: a build certificate needs no canary (nothing it certifies can change); re-certify instead"); return 2
        try: return run_build(a)
        except backends.ConfigError as e: print(f"error: {e}"); return 2
    if a.list:
        for p, c in build_certificates():
            v = verify_build(c) if c.get("status") == "PASS" else None
            print(f"{c.get('status', '?'):14s} {'build':10s} {c.get('date', '?')}  no expiry  GGUF {(c.get('gguf') or {}).get('sha256', '?')[:12]}  "
                  f"llama-cpp-python {(c.get('runtime') or {}).get('llama_cpp_python')}  {p}\n{'':16s}gate: "
                  f"{('holds' if not v else 'DOES NOT HOLD: ' + v) if c.get('status') == 'PASS' else '-'}")
        for p, c in certificates():
            if c.get("kind") == "build": continue
            v = verify(c) if c.get("kind") == "endpoint" and c.get("status") == "PASS" else None
            gate = ("holds" if not v else "DOES NOT HOLD: " + v) if c.get("kind") == "endpoint" and c.get("status") == "PASS" else "-"
            print(f"{c.get('status', '?'):14s} {c.get('kind', '?'):10s} {c.get('date', '?')}  expires {str(c.get('expires', '?'))[:10]}  "
                  f"{c.get('endpoint')}  {c.get('model_requested')}  {p}\n{'':16s}gate: {gate}")
            if v is None and c.get("kind") == "endpoint" and c.get("status") == "PASS":
                st, why = canary_gate(c); print(f"{'':16s}canary: {st}: {why}")
        return 0
    if a.resolve:
        if not a.labels: ap.error("--resolve needs --labels")
        return resolve(a.resolve, a.labels)
    stamp = _now().strftime("%Y%m%dT%H%M%SZ")
    rec_dir = os.path.join(core.ROOT, "data", "cache", "responses")
    try:
        if a.backend == "cache":
            kind = "replay"; ask = backends.Cache(rec_dir); endpoint, model = ask.endpoint, core.M70
            name = a.name or f"replay-{stamp}"
        elif a.backend == "openai":
            probe = backends.OpenAI(); endpoint, model = probe.endpoint, probe.model; kind = "endpoint"
            name = a.name or f"{_slug(endpoint.split('//', 1)[-1])}--{_slug(model.split('/')[-1])}{'' if a.seed is None else '-seed' + str(a.seed)}-{stamp}"
            if a.canary and not a.name: name = f"{_slug(endpoint.split('//', 1)[-1])}--{_slug(model.split('/')[-1])}-{stamp}"
        else:
            kind, endpoint, model = "evaluation", "Public AI via development gateway (evaluation only; may route outside Switzerland)", core.M70
            name = a.name or f"gateway-{stamp}"
            if not a.gw_dir: raise backends.ConfigError("the gateway backend is development-only: set GLEICHLAUT_GATEWAY_DIR (or --gw-dir)")
    except backends.ConfigError as e:
        print(f"error: {e}"); return 2
    if a.canary: name = f"canary-{name}" if a.backend == "openai" or a.name else f"canary-{a.backend}-{stamp}"
    for d in ("certificates", "runs", "cache", "canary"): os.makedirs(state_dir(d), exist_ok=True)
    sub = "canary" if a.canary else "certificates"; base, n = name, 1
    while any(os.path.exists(state_dir(sub, name + e)) for e in (".json", ".calls.jsonl")) or os.path.exists(state_dir("runs", f"certify_{name}.jsonl")):
        n += 1; name = f"{base}-{n}"                       # never overwrite a report, a certificate or its log
    log = state_dir("certificates" if not a.canary else "canary", f"{name}.calls.jsonl")
    try:
        if a.backend == "openai":
            ask = backends.OpenAI(seed=a.seed, log=log, record_to=state_dir("cache", name))
        elif a.backend == "gateway":
            ask = backends.Gateway(a.gw_dir, a.tag, a.cap, seed=a.seed, log=log, record_to=rec_dir)
    except backends.ConfigError as e:
        print(f"error: {e}"); return 2
    cert = None
    if a.canary:
        if a.against:
            ref_path, cert, what = a.against, None, a.against
        elif kind == "endpoint":
            cert, why = lookup(endpoint, model)
            if cert is None:
                print(f"canary refused: {why}. Certify this endpoint first (`gleichlaut certify`), or pass --against RECORDS."); return 4
            ref_path, what = state_dir(cert["run_records"]), f"certified run {cert['name']}"
        else:
            ref_path, what = os.path.join(core.ROOT, "data", score.RUNS["fresh166"]["final"]), "the pre-registered reference run"
        if not os.path.exists(ref_path): print(f"error: canary reference records not found: {ref_path}"); return 2
        ref = {json.loads(l)["key"]: json.loads(l) for l in open(ref_path, encoding="utf-8")}
    print(f"{'canary' if a.canary else 'certify'}: {kind} {endpoint}  model {model}  -> {state_dir()}", flush=True)
    try:
        I, R, secs = run_suite(ask, a.canary or a.n, a.workers)
    except backends.EndpointError as e:
        print(f"ENDPOINT FAILED: {e}"); return 6
    served, seeds, fps = _read_log(log)
    if a.backend == "cache": served, seeds, fps = {core.M70 + " (as recorded)"}, {"None"}, set()
    if a.canary:
        rep = canary_report(I, R, ref, served, cert, fps)
        rep.update(name=name, date=_now().isoformat(timespec="seconds"), endpoint=endpoint, model=model, against=what,
                   certificate=(cert or {}).get("name"), models_served=sorted(served), system_fingerprints=sorted(f for f in fps if f),
                   fingerprints_at_certification=(cert or {}).get("system_fingerprints"),
                   calls_log=os.path.relpath(log, state_dir()), calls_log_sha256=core.sha256(log) if os.path.exists(log) else None)
        p = _unique(state_dir("canary", f"{name}.json"))
        _write_json(p, sign(rep))
        print(json.dumps({k: rep[k] for k in rep if k not in ("flag_changes",)}, indent=1, ensure_ascii=False))
        for w in rep["warnings"]: print(f"WARNING: {w}")
        print(f"CANARY {'PASSED' if rep['ok'] else 'FAILED: ' + '; '.join(rep['reasons'])}  (report {p})")
        return 0 if rep["ok"] else 3
    if a.n:
        print(json.dumps(evaluate(I, R)[0], indent=1)); return 0
    p, cert = write_certificate(name, kind, endpoint, model, I, R, secs, served, seeds, fps, log, valid_days=a.valid_days)
    m = cert["metrics"]; ci = m["exact"]["ci95"]
    print(f"certificate {p}\n  kind {kind}  status {cert['status']}  exact {m['exact']['delta']:+.1f} pts vs rules-only "
          f"(95% CI {ci[0]:+.1f} to {ci[1]:+.1f})  flagged {m['flag_rate']}%  ready {m['ready_rate']}%  "
          f"needs review {len(cert['needs_review'])}  served by {cert['models_served']}\n"
          f"  expires {cert['expires'][:10]}  records sha256 {cert['run_records_sha256'][:12]}  call log sha256 {cert['calls_log_sha256'][:12]}"
          f"  {'HMAC-signed' if 'hmac_sha256' in cert else 'unsigned (set GLEICHLAUT_CERT_KEY to sign)'}")
    if kind != "endpoint": print("  (a", kind, "certificate is evidence only: it never authorises the SL lane)")
    if cert["status"] == "PENDING_REVIEW":
        print(f"  label the {len(cert['needs_review'])} outputs listed in needs_review, then: "
              f"gleichlaut certify --resolve {p} --labels LABELS.tsv")
    return EXIT[cert["status"]]


if __name__ == "__main__":
    sys.exit(main())
