"""M1/M2 (PREREG R1): the shipped SL pipeline with an Apertus 8B GGUF on CPU over the fresh 166, in shards.

  python -m gleichlaut.m1 run --gguf PATH --build q4_k_m --shard K --of N --out DIR     resumable; one JSON line per item
  python -m gleichlaut.m1 gather --build q4_k_m --in DIR [DIR ...] [--name rerun]     merge, score, write the label worklist
  run records every model call as a hash-addressed cache entry (DIR/cache, backends.write_cache); gather merges those into
  data/cache/responses_8b/<build>/ so that `make run` can re-execute the run (replay.REEXEC). --name: the records file is
  runs/8b_<build>_fresh166_g3_<name>.jsonl (default final = the certified run; PREREG R9's second run is "rerun")
  --suite fed (both commands): PREREG R6, the shipped Fedlex lane (fed.lane.fed_draft) with the GGUF on the 120 Fedlex
  FR/IT items instead (the R5 items; R5 measured the 8B MLX build)

Same frozen code as the 70B lane (run_2b, lock check, retry, guards3, one re-ask); the backend is llama.cpp on CPU with
the 8B digit / number-word logit mask. Runs on a GitHub Actions runner, never on a team machine (corrections §1)."""
import argparse, json, os, random, sys, time
from . import core, score, backends


def fed_items():
    from .fed import lane
    return [x for x in lane.load(lane.ITEMS) if x["src"] == "fed" and x["lang"] in lane.SCOPE]


def run(a):
    if a.suite == "fed": return run_fed(a)
    I = [x for i, x in enumerate(score.load_items("items/items_fresh.json")) if i % a.of == a.shard]
    os.makedirs(a.out, exist_ok=True)
    path = os.path.join(a.out, f"m1_{a.build}_shard{a.shard}of{a.of}.jsonl")
    done = {json.loads(l)["key"] for l in open(path, encoding="utf-8")} if os.path.exists(path) else set()
    ask = backends.LlamaCpp(a.gguf, backends.lang_of_prompt, n_ctx=a.ctx, log=os.path.join(a.out, f"calls_{a.build}_{a.shard}.jsonl"),
                            record_to=os.path.join(a.out, "cache"))
    P = core.Pipeline(ask, "g3")
    for x in I:
        if x["key"] in done: continue
        t0 = time.time(); r = P.run(x); r["wall_secs"] = round(time.time() - t0, 1); r["build"] = a.build
        with open(path, "a", encoding="utf-8") as f: f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(x["key"], "flag" if r["guard_flag"] else "ready", r["wall_secs"], "s", flush=True)
    print("SHARD_DONE", a.shard, flush=True)


def run_fed(a):
    from .fed import lane
    I = [x for i, x in enumerate(fed_items()) if i % a.of == a.shard]
    os.makedirs(a.out, exist_ok=True)
    path = os.path.join(a.out, f"m1fed_{a.build}_shard{a.shard}of{a.of}.jsonl")
    done = {json.loads(l)["key"] for l in open(path, encoding="utf-8")} if os.path.exists(path) else set()
    ask = backends.LlamaCpp(a.gguf, backends.lang_of_prompt, n_ctx=a.ctx, log=os.path.join(a.out, f"calls_fed_{a.build}_{a.shard}.jsonl"))
    for x in I:
        if x["key"] in done: continue
        t0 = time.time(); r = lane.fed_draft(x, ask); r["wall_secs"] = round(time.time() - t0, 1); r["build"] = a.build
        with open(path, "a", encoding="utf-8") as f: f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(x["key"], r["status"], r["wall_secs"], "s", flush=True)
    print("SHARD_DONE", a.shard, flush=True)


def gather_fed(a):
    R = {}
    for d in a.inp:
        for f in sorted(os.listdir(d)):
            if f.startswith(f"m1fed_{a.build}_") and f.endswith(".jsonl"):
                for l in open(os.path.join(d, f), encoding="utf-8"): r = json.loads(l); R[r["key"]] = r
    I = fed_items(); missing = [x["key"] for x in I if x["key"] not in R]
    if missing: raise SystemExit(f"{len(missing)} items missing, e.g. {missing[:5]}")
    rel = f"runs/8b_{a.build}_fedlex_shipped.jsonl"
    with open(os.path.join(score.DATA, rel), "w", encoding="utf-8") as f:
        for x in I: f.write(json.dumps(R[x["key"]], ensure_ascii=False) + "\n")
    todo = sorted(x["key"] for x in I if R[x["key"]]["status"] == "ready" and not R[x["key"]].get("exact"))
    wp = os.path.join(core.ROOT, "eval", "labels", f"worklist_8b_{a.build}_fedlex.json")
    json.dump(dict(build=a.build, unflagged_needing_labels=todo), open(wp, "w"), indent=1)
    secs = [r.get("wall_secs", 0) for r in R.values()]
    print(json.dumps(dict(build=a.build, items=len(I), exact=sum(bool(r.get("exact")) for r in R.values()),
                          flagged=sum(bool(r["flagged"]) for r in R.values()), ready_nonexact=len(todo),
                          wall_secs_per_item=round(sum(secs) / len(secs), 1)), indent=1))
    print("wrote", rel, "and", wp)


def merge_cache(dirs, dest):
    """copy every recorded call (DIR/cache/<2>/<sha256>.json) into dest; -> number of entries. A key recorded twice must
    carry the same text (the same request answered differently would make the run non-replayable)."""
    n = 0
    for d in dirs:
        root = os.path.join(d, "cache")
        if not os.path.isdir(root): continue
        for sub in sorted(os.listdir(root)):
            for f in sorted(os.listdir(os.path.join(root, sub))):
                e = json.load(open(os.path.join(root, sub, f), encoding="utf-8")); p = os.path.join(dest, sub, f)
                if os.path.exists(p):
                    if json.load(open(p, encoding="utf-8"))["text"] != e["text"]: raise SystemExit(f"{f}: same request, different answers")
                    continue
                os.makedirs(os.path.dirname(p), exist_ok=True)
                with open(p, "w", encoding="utf-8") as o: json.dump(e, o, ensure_ascii=False, sort_keys=True)
                n += 1
    return n


def gather(a):
    if a.suite == "fed": return gather_fed(a)
    R = {}
    for d in a.inp:
        for f in sorted(os.listdir(d)):
            if f.startswith(f"m1_{a.build}_") and f.endswith(".jsonl"):
                for l in open(os.path.join(d, f), encoding="utf-8"): r = json.loads(l); R[r["key"]] = r
    I = score.load_items("items/items_fresh.json")
    missing = [x["key"] for x in I if x["key"] not in R]
    if missing: raise SystemExit(f"{len(missing)} items missing, e.g. {missing[:5]}")
    nc = merge_cache(a.inp, os.path.join(score.DATA, "cache", "responses_8b", a.build))
    rel = f"runs/8b_{a.build}_fresh166_g3_{a.name}.jsonl"
    with open(os.path.join(score.DATA, rel), "w", encoding="utf-8") as f:
        for x in I: f.write(json.dumps(R[x["key"]], ensure_ascii=False) + "\n")
    from .certify import evaluate
    s, status, review, digits = evaluate(I, [R[x["key"]] for x in I])
    fl = sorted(x["key"] for x in I if R[x["key"]]["guard_flag"])
    work = dict(build=a.build, unflagged_needing_labels=review, flagged_sample=random.Random(20261009).sample(fl, min(20, len(fl))))
    wp = os.path.join(core.ROOT, "eval", "labels", f"worklist_8b_{a.build}_fresh166{'' if a.name == 'final' else '_' + a.name}.json")
    json.dump(work, open(wp, "w"), indent=1)
    secs = [R[k].get("wall_secs", 0) for k in R]
    print(json.dumps(dict(build=a.build, status_before_labels=status, exact=s["exact"], flag_rate=s["flag_rate"], ready_rate=s["ready_rate"],
                          needs_labels=len(review), items_with_model_digits=digits, wall_secs_per_item=round(sum(secs) / len(secs), 1),
                          recorded_calls=nc), indent=1))
    print("wrote", rel, "and", wp)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="gleichlaut.m1"); sp = ap.add_subparsers(dest="cmd", required=True)
    r = sp.add_parser("run"); r.add_argument("--gguf", required=True); r.add_argument("--build", required=True)
    r.add_argument("--shard", type=int, default=0); r.add_argument("--of", type=int, default=1); r.add_argument("--out", default="out/m1")
    r.add_argument("--ctx", type=int, default=8192); r.add_argument("--suite", choices=("sl", "fed"), default="sl")
    g = sp.add_parser("gather"); g.add_argument("--build", required=True); g.add_argument("--in", dest="inp", nargs="+", required=True)
    g.add_argument("--suite", choices=("sl", "fed"), default="sl"); g.add_argument("--name", default="final")
    a = ap.parse_args(argv)
    return run(a) if a.cmd == "run" else gather(a)


if __name__ == "__main__":
    sys.exit(main())
