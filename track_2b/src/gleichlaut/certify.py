"""Certify an endpoint (or a local build) for the SL lane by re-running the frozen fresh-166 suite on it.

The certificate carries the endpoint identity, the models that actually served the calls, the sha256 of the frozen code
and items, the automatic pass-rule metrics, and a status:
  PASS            every pre-registered criterion is met and no unflagged output is unlabelled
  PENDING_REVIEW  the automatic criteria are met, but some unflagged non-exact outputs are new (not identical to an
                  output already hand-labelled in the reference run) and need a human label before the certificate holds
  FAIL            an automatic criterion fails (exact gain < +5, flag rate > 70%), or inherited labels exceed the limits
Labels are inherited only by identical outputs (after whitespace/apostrophe normalisation): nothing is judged by a model.

Canary: `--canary N` re-runs the first N items of the suite and reports drift against a certified run."""
import argparse, datetime, json, os, sys, time
from concurrent.futures import ThreadPoolExecutor
from . import core, score, backends

CERTS = os.path.join(core.ROOT, "eval", "certificates")
ITEMS = "items/items_fresh.json"


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


def evaluate(I, R):
    S = core.SCORE; ref = reference_labels(); chk = core.check_only("g3")
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


def certificate(name, endpoint, model, I, R, secs, served, seeds):
    s, status, review, digits = evaluate(I, R)
    return dict(name=name, date=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
                endpoint=endpoint, model_requested=model, models_served=sorted(served), seeds=sorted(seeds),
                suite=dict(items=ITEMS, n=len(I), sha256=core.sha256(os.path.join(core.ROOT, "data", ITEMS))),
                freeze_sha256=core.sha256(core.FREEZE), pass_rule=score.PASS_RULE, status=status,
                metrics={k: s[k] for k in ("exact", "ef1", "chrf", "flag_rate", "ready_rate", "unflagged", "unflagged_REAL",
                                           "unflagged_stale", "unflagged_german", "pass_rule")},
                needs_review=review, items_with_model_digits=digits, wall_secs=round(secs, 1))


def main(argv=None):
    ap = argparse.ArgumentParser(prog="gleichlaut certify")
    ap.add_argument("--backend", choices=["cache", "openai", "gateway"], default="cache")
    ap.add_argument("--name", default=None)
    ap.add_argument("--n", type=int, default=None, help="first N items only (smoke test; never a certificate)")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--canary", type=int, default=None, help="re-run the first N items and compare with --against")
    ap.add_argument("--against", default=os.path.join(core.ROOT, "data", score.RUNS["fresh166"]["final"]))
    ap.add_argument("--gw-dir", default=os.path.expanduser("~/Desktop/hackapertus/gateway"))
    ap.add_argument("--tag", default="gleichlaut-certify"); ap.add_argument("--cap", type=float, default=1.0)
    ap.add_argument("--workers", type=int, default=2)
    a = ap.parse_args(argv)
    os.makedirs(CERTS, exist_ok=True)
    name = a.name or f"{a.backend}{'' if a.seed is None else '-seed' + str(a.seed)}"
    log = os.path.join(CERTS, f"{name}.calls.jsonl")
    rec_dir = os.path.join(core.ROOT, "data", "cache", "responses")
    if a.backend == "cache":
        ask = backends.Cache(rec_dir); endpoint, model = "recorded responses (data/cache)", core.M70
    elif a.backend == "openai":
        ask = backends.OpenAI(seed=a.seed, log=log, record_to=os.path.join(core.ROOT, "out", "cache", name))
        endpoint, model = ask.base.split("//")[-1].split("/")[0], ask.model
    else:
        ask = backends.Gateway(a.gw_dir, a.tag, a.cap, seed=a.seed, log=log, record_to=rec_dir)
        endpoint, model = "Public AI via development gateway (evaluation only; may route outside Switzerland)", core.M70
    n = a.canary or a.n
    I, R, secs = run_suite(ask, n, a.workers)
    served, seeds = set(), set()
    if os.path.exists(log):
        for l in open(log, encoding="utf-8"):
            c = json.loads(l); served.add(c.get("model_served") or ""); seeds.add(str(c.get("seed")))
    if a.backend == "cache": served, seeds = {core.M70 + " (as recorded)"}, {"None"}
    if a.canary:
        ref = {json.loads(l)["key"]: json.loads(l) for l in open(a.against, encoding="utf-8")}
        drift = [dict(key=r["key"], same_output=r["out"] == ref[r["key"]]["out"], same_flag=r["guard_flag"] == ref[r["key"]]["guard_flag"])
                 for r in R]
        ok = all(d["same_output"] for d in drift)
        print(json.dumps(dict(canary=len(drift), identical=sum(d["same_output"] for d in drift),
                              same_flag=sum(d["same_flag"] for d in drift), drift=[d for d in drift if not d["same_output"]]), indent=1))
        return 0 if ok else 3
    if a.n:
        print(json.dumps(evaluate(I, R)[0], indent=1)); return 0
    with open(os.path.join(core.ROOT, "data", "runs", f"certify_{name}.jsonl"), "w", encoding="utf-8") as f:
        for r in R: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    cert = certificate(name, endpoint, model, I, R, secs, served, seeds)
    p = os.path.join(CERTS, f"{name}.json")
    json.dump(cert, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    m = cert["metrics"]
    print(f"certificate {p}\n  status {cert['status']}  exact +{m['exact']['delta']} {m['exact']['ci95']}  flagged {m['flag_rate']}%  "
          f"ready {m['ready_rate']}%  needs review {len(cert['needs_review'])}  served by {cert['models_served']}")
    return 0 if cert["status"] != "FAIL" else 2


def certified(endpoint_model):
    """True if a PASS certificate exists for this model id (any endpoint name ending in the same model)."""
    if not os.path.isdir(CERTS): return False
    for f in os.listdir(CERTS):
        if not f.endswith(".json") or f.endswith(".calls.jsonl"): continue
        c = json.load(open(os.path.join(CERTS, f), encoding="utf-8"))
        if c.get("status") == "PASS" and c.get("model_requested", "").split("/")[-1] == endpoint_model.split("/")[-1]: return True
    return False


if __name__ == "__main__":
    sys.exit(main())
