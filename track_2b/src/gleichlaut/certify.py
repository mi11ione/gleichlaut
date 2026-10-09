"""Certify an endpoint for the SL lane by re-running the frozen fresh-166 suite on it, and watch it with a canary.

A certificate records WHAT was certified, never a secret:
  kind               "endpoint" (an OpenAI-compatible endpoint, --backend openai): the only kind that can authorise drafting;
                     "replay" (--backend cache: the recorded responses re-run) and "evaluation" (--backend gateway: the
                     development gateway to Public AI) are evidence only and never authorise anything
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
in eval/certificates/ are evidence of the evaluation (a replay and the Public AI runs) and are never consulted by certified().

certified(base_url, model) -> the newest certificate with kind "endpoint", the exact same endpoint id and model, status PASS,
and the current freeze and suite hashes; else None. The newest certificate for an endpoint+model decides (a later FAIL
revokes an earlier PASS).

Canary (`--canary [N]`, default 40 items): re-runs the first N suite items and compares them with the certified run of the
same endpoint+model on the same items. Byte identity is reported as information only: at temperature 0 the 70B lane is not
deterministic (eval/results/m3.json: a seeded re-run of the fresh 166 gave 69.9% identical outputs, flag agreement 163/166 =
98.2%, kappa 0.963, exact 17.5% -> 18.1%; on the first 40 items agreement 97.5%, exact 12.5% -> 15.0%). The canary fails
(exit 3) only on
  flag agreement < 0.85        (8x the measured disagreement of 1.8%: the guards now see a different model)
  exact drop > 5 points        (8x the measured change of +0.6 points, and the pass rule's minimum gain over rules-only)
  a served model id not seen at certification."""
import argparse, datetime, json, os, re, sys, time
from concurrent.futures import ThreadPoolExecutor
from . import core, score, backends

EVIDENCE = os.path.join(core.ROOT, "eval", "certificates")       # shipped evidence; never authorises
ITEMS = "items/items_fresh.json"
CANARY_N = 40
CANARY_MIN_FLAG_AGREEMENT = 0.85
CANARY_MAX_EXACT_DROP = 5.0
LABEL_CLASSES = ("equivalent", "preexisting", "cosmetic", "minor", "german", "stale", "REAL", "garble")
EXIT = dict(PASS=0, FAIL=5, PENDING_REVIEW=7)


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
    t0 = time.time()
    with ThreadPoolExecutor(workers) as ex: R = list(ex.map(P.run, I))
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
    return sorted(out, key=lambda pc: pc[1].get("date", ""))


def lookup(base_url, model):
    """-> (certificate or None, reason). Only kind 'endpoint', exact endpoint id and model, newest decides."""
    ep = backends.endpoint_id(base_url)
    cands = [c for _, c in certificates() if c.get("kind") == "endpoint" and c.get("endpoint") == ep and c.get("model_requested") == model]
    if not cands: return None, f"no endpoint certificate for {model} at {ep} in {state_dir('certificates')}"
    c = cands[-1]
    if c.get("status") != "PASS":
        return None, f"the newest certificate for {model} at {ep} ({c.get('name')}) has status {c.get('status')}"
    if c.get("freeze_sha256") != core.sha256(core.FREEZE):
        return None, f"certificate {c.get('name')} was made with other frozen code (freeze sha256 changed): re-certify"
    if (c.get("suite") or {}).get("sha256") != core.sha256(os.path.join(core.ROOT, "data", ITEMS)):
        return None, f"certificate {c.get('name')} was made on another suite: re-certify"
    return c, f"certificate {c.get('name')} ({c.get('date')})"


def certified(base_url, model):
    """The certification gate of the SL lane: the PASS endpoint certificate for exactly this endpoint and model, or None."""
    return lookup(base_url, model)[0]


# ------------------------------------------------------------------ canary
def canary_report(I, R, ref, served=(), cert=None):
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
    return dict(ok=not reasons, reasons=reasons, n=n,
                tolerances=dict(min_flag_agreement=CANARY_MIN_FLAG_AGREEMENT, max_exact_drop_pts=CANARY_MAX_EXACT_DROP,
                                derived_from="eval/results/m3.json (seeded re-run of the fresh 166)"),
                flag_agreement=round(agree, 3), exact_now_pct=round(ex_now, 1), exact_ref_pct=round(ex_ref, 1),
                flag_rate_now_pct=round(100 * sum(d["flag_now"] for d in rows) / n, 1),
                flag_rate_ref_pct=round(100 * sum(d["flag_ref"] for d in rows) / n, 1),
                info=dict(byte_identical=sum(d["same_output"] for d in rows), byte_identical_pct=round(100 * sum(d["same_output"] for d in rows) / n, 1),
                          note="byte identity is information only: measured 69.9% at temperature 0 (eval/results/m3.json)"),
                flag_changes=[d["key"] for d in rows if not d["same_flag"]])


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
    runs = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(cert_path))), c["run_records"])
    if not os.path.exists(runs): print(f"error: the suite records of this certificate are missing: {runs}"); return 2
    R = {json.loads(l)["key"]: json.loads(l) for l in open(runs, encoding="utf-8")}
    lines = [l for l in open(labels_path, encoding="utf-8").read().splitlines() if l.strip()]
    if not lines or lines[0].split("\t")[:2] != ["key", "class"]:
        print("error: the labels file must be a TSV with the header 'key<TAB>class'"); return 2
    extra, bad = {}, []
    for l in lines[1:]:
        k, cls = (l.split("\t") + [""])[:2]
        if cls not in LABEL_CLASSES or k not in R: bad.append(l); continue
        extra[k] = {core.lock.norm(R[k]["out"]): cls}
    if bad: print(f"error: {len(bad)} label line(s) with an unknown key or class (classes: {', '.join(LABEL_CLASSES)}): {bad[:3]}"); return 2
    I = [x for x in score.load_items(ITEMS) if x["key"] in R]
    new = certificate(c["name"], c["kind"], c["endpoint"], c["model_requested"], I, [R[x["key"]] for x in I], c.get("wall_secs", 0),
                      c.get("models_served", []), c.get("seeds", []), c.get("system_fingerprints", []), extra)
    new.update(date=c["date"], resolved=_now().isoformat(timespec="seconds"),
               review_labels=dict(path=os.path.basename(labels_path), sha256=core.sha256(labels_path), n=len(extra)))
    json.dump(new, open(cert_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"certificate {cert_path}: {c['status']} -> {new['status']}  (still needs review: {len(new['needs_review'])})")
    return EXIT[new["status"]]


def main(argv=None):
    ap = argparse.ArgumentParser(prog="gleichlaut certify", description="certify an endpoint on the frozen fresh-166 suite, or run the canary")
    ap.add_argument("--backend", choices=["openai", "cache", "gateway"], default="openai",
                    help="openai: LLM_BASE_URL (the only kind that authorises); cache: replay of the recorded responses; gateway: development only")
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
    ap.add_argument("--labels", metavar="TSV")
    ap.add_argument("--list", action="store_true", help="list the certificates in the state directory")
    a = ap.parse_args(argv)
    if a.list:
        for p, c in certificates():
            print(f"{c.get('status', '?'):14s} {c.get('kind', '?'):10s} {c.get('date', '?')}  {c.get('endpoint')}  {c.get('model_requested')}  {p}")
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
        else:
            kind, endpoint, model = "evaluation", "Public AI via development gateway (evaluation only; may route outside Switzerland)", core.M70
            name = a.name or f"gateway-{stamp}"
            if not a.gw_dir: raise backends.ConfigError("the gateway backend is development-only: set GLEICHLAUT_GATEWAY_DIR (or --gw-dir)")
    except backends.ConfigError as e:
        print(f"error: {e}"); return 2
    if a.canary: name = f"canary-{name}" if a.name else f"canary-{stamp}"
    for d in ("certificates", "runs", "cache", "canary"): os.makedirs(state_dir(d), exist_ok=True)
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
        rep = canary_report(I, R, ref, served, cert)
        rep.update(date=_now().isoformat(timespec="seconds"), endpoint=endpoint, model=model, against=what,
                   models_served=sorted(served), system_fingerprints=sorted(f for f in fps if f),
                   fingerprints_at_certification=(cert or {}).get("system_fingerprints"))
        p = state_dir("canary", f"{name}.json")
        json.dump(rep, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(json.dumps({k: rep[k] for k in rep if k not in ("flag_changes",)}, indent=1, ensure_ascii=False))
        print(f"CANARY {'PASSED' if rep['ok'] else 'FAILED: ' + '; '.join(rep['reasons'])}  (report {p})")
        return 0 if rep["ok"] else 3
    if a.n:
        print(json.dumps(evaluate(I, R)[0], indent=1)); return 0
    with open(state_dir("runs", f"certify_{name}.jsonl"), "w", encoding="utf-8") as f:
        for r in R: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    cert = certificate(name, kind, endpoint, model, I, R, secs, served, seeds, fps)
    p = state_dir("certificates", f"{name}.json")
    json.dump(cert, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    m = cert["metrics"]
    print(f"certificate {p}\n  kind {kind}  status {cert['status']}  exact +{m['exact']['delta']} {m['exact']['ci95']}  flagged {m['flag_rate']}%  "
          f"ready {m['ready_rate']}%  needs review {len(cert['needs_review'])}  served by {cert['models_served']}")
    if kind != "endpoint": print("  (a", kind, "certificate is evidence only: it never authorises the SL lane)")
    if cert["status"] == "PENDING_REVIEW":
        print(f"  label the {len(cert['needs_review'])} outputs listed in needs_review, then: "
              f"gleichlaut certify --resolve {p} --labels LABELS.tsv")
    return EXIT[cert["status"]]


if __name__ == "__main__":
    sys.exit(main())
