"""PREREG R19. The certified 8B GGUF Q8_0 on the identity probes of the research record: the 250 MMLU questions behind the
"shared model is the 70B" verdict and the 792-cell battery whose recorded outputs identify the Public AI backends
(fp1-nes: free generation on the 70B name; tp2: exact forced choice on the apertus-70b-instruct alias; the 8B name).

Prompts, candidates, parser and decoding come from the vendored research files themselves (data/r19/, sha256 in
data/r19/SHA256SUMS, checked before anything runs): mmlu/run.py `prompt`, at most 3 tokens, first [ABCD]; battery/live.py
`Q`, `CANDS`, `parse`, generation at most 24 tokens, forced choice as `fc_cell` (the rendered prompt + the candidate, its
last tokens scored by teacher forcing). Greedy, no logit mask, one plain user message, the GGUF's own chat template.

  run8b   CI only (workflow r19-8b, GitHub Actions CPU runners): the build certificate of the loaded GGUF is verified first
          (cli.certified_gguf; the shard stops without one), then every MMLU question and battery cell of the shard.
          Resumable; every raw answer is kept. Never run on a team machine.
  gather  merge the shard folders into data/r19/runs/8b_q8_0/ (mmlu.jsonl, battery.jsonl in index order, shards.json).

usage: PYTHONPATH=src python3 tools/r19_identity.py run8b --gguf models/q8_0.gguf --gguf-sha256 SHA --shard K --of N
                                                         [--budget S] [--limit M]   (smoke: M questions and M cells, not used)
       PYTHONPATH=src python3 tools/r19_identity.py gather --in DIR"""
import hashlib, json, os, re, sys, time
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))
from gleichlaut import core                       # noqa: E402

D = os.path.join(ROOT, "data", "r19")
RUN = os.path.join(D, "runs", "8b_q8_0")
MMLU_MAX, GEN_MAX = 3, 24                         # run.py: max_tokens=3; live.py gen_cell: max_tokens=24
LETTER = r"[ABCD]"                                # run.py: re.search(r"[ABCD]", txt or "")


def verify():
    for l in open(os.path.join(D, "SHA256SUMS"), encoding="utf-8"):
        h, rel = l.split()
        got = hashlib.sha256(open(os.path.join(D, rel), "rb").read()).hexdigest()
        if got != h: raise SystemExit(f"R19: {rel} differs from its recorded sha256")


def defs():
    """the research definitions, executed from the vendored files (only the named top-level assignments/functions)."""
    ns = {"re": re}
    core._extract(os.path.join(D, "battery", "live.py"), ("QHEAD", "R3", "R4", "T_CONV", "T_VER", "Q", "CANDS", "parse"), ns)
    mm = {}
    core._extract(os.path.join(D, "mmlu", "run.py"), ("prompt",), mm)
    assert f're.search(r"{LETTER}", txt or "")' in open(os.path.join(D, "mmlu", "run.py"), encoding="utf-8").read()
    ns["mmlu_prompt"] = mm["prompt"]
    return ns


def load(rel): return json.load(open(os.path.join(D, rel), encoding="utf-8"))


def mmlu_items(): return load("mmlu/items.json")


def cell_key(r): return (r["set"], r["item"], r["variant"], r["cell"])


def cells():
    """the 792 battery cells in live.py jobs() order: (set, item, framing, rung) over ladder/never x conv/ver x R0/R3,
    then the ladder x conv/ver x R4; each with the recorded rows of fp1-nes (gen), the 8B name (gen, fc) and tp2 (fc)."""
    sets = {"ladder": load("battery/linie_items.json"), "never": load("battery/never_items.json")}
    order = [(s, fr, r) for s in ("ladder", "never") for fr in ("conv", "ver") for r in ("R0", "R3")] + \
            [("ladder", fr, "R4") for fr in ("conv", "ver")]
    out = [dict(set=s, x=x, fr=fr, rung=r) for s, fr, r in order for x in sets[s]]
    rec = {n: load(f"battery/{n}.json") for n in ("gen_apertus-v1.5-70b", "gen_apertus-v1.5-8b", "fc_apertus-v1.5-8b", "fc_apertus-70b-instruct")}
    Q = defs()["Q"]
    for n, d in rec.items():
        for fr in ("conv", "ver"):
            for r in ("R0", "R3", "R4"): assert d["questions"][fr][r] == Q[fr][r], (n, fr, r)
        assert [cell_key(z) for z in d["rows"]] == [(c["set"], c["x"]["item"], c["x"]["variant"], f"{c['fr']}_{c['rung']}") for c in out], n
    for j, c in enumerate(out):
        c.update(j=j, fp1=rec["gen_apertus-v1.5-70b"]["rows"][j], gen8=rec["gen_apertus-v1.5-8b"]["rows"][j],
                 fc8=rec["fc_apertus-v1.5-8b"]["rows"][j], tp2=rec["fc_apertus-70b-instruct"]["rows"][j])
    return out


# ---------------------------------------------------------------- CI: the certified 8B
def run8b(gguf, sha, k, n, budget, limit=0):
    from gleichlaut import cli
    from gleichlaut.fm.run import Model, Budget
    verify()
    p, got, cert, why = cli.certified_gguf([gguf])
    print("certificate:", why, flush=True)
    if not p or (sha and got != sha): sys.exit(f"R19: no valid build certificate for {gguf}: {why}")
    ns = defs(); Q, CANDS, parse, prompt = ns["Q"], ns["CANDS"], ns["parse"], ns["mmlu_prompt"]
    out = os.path.join(ROOT, "out", "r19", f"shard{k}of{n}"); os.makedirs(out, exist_ok=True)
    json.dump(dict(certificate=cert.get("name"), verified=why, gguf_sha256=got,
                   inputs_sha256=hashlib.sha256(open(os.path.join(D, "SHA256SUMS"), "rb").read()).hexdigest()),
              open(os.path.join(out, "gate.json"), "w"), indent=1)
    path = os.path.join(out, "records.jsonl")
    done = {json.loads(l)["uid"] for l in open(path, encoding="utf-8")} if os.path.exists(path) else set()
    model = Model(gguf, n_ctx=8192, deadline=time.time() + budget if budget else None)
    L = model.llm

    def gen(user, mt):
        model._check_time(); L.reset(); t0 = time.time()       # a fresh prefill for every request
        r = L.create_chat_completion(messages=[{"role": "user", "content": user}], max_tokens=mt, temperature=0.0)
        return r["choices"][0]["message"]["content"], dict(ptok=r["usage"]["prompt_tokens"], ctok=r["usage"]["completion_tokens"],
                                                           finish=r["choices"][0].get("finish_reason"), secs=round(time.time() - t0, 2))

    def fc(user, cands):
        """live.py fc_cell / stage9.py: the rendered prompt + the candidate; its last tokens (the ones the API recorded)
        scored by teacher forcing on a fresh prefill of the shared prefix."""
        model._check_time(); pre = model.chat_text(user); res, lp0, prefix = {}, None, None
        for cand, toks in cands:
            ids = model.toks(pre + cand); m = len(toks); tail, head = ids[-m:], ids[:-m]
            dec = L.detokenize(tail).decode("utf-8", "replace")
            assert dec == "".join(toks), (cand, dec, toks)
            if head != prefix: prefix, lp0 = head, model.eval_from(0, head)
            lp, s = lp0, 0.0
            for i, t in enumerate(tail):
                s += float(lp[t])
                if i + 1 < m: lp = model.eval_from(len(head) + i, [t])
            res[cand] = dict(lp=s, ntok=len(ids), tail_ids=list(tail))
        return res

    items = mmlu_items(); C = cells()
    mine_m = [j for j in range(len(items)) if j % n == k and f"mmlu:{j}" not in done]
    mine_b = [c for c in C if c["j"] % n == k and f"bat:{c['j']}" not in done]
    if limit: mine_m, mine_b = mine_m[:limit], mine_b[:limit]
    print(f"R19 shard {k}/{n}: {len(mine_m)} questions, {len(mine_b)} cells to run", flush=True)
    try:
        for j in mine_m:
            it = items[j]; text, meta = gen(prompt(it), MMLU_MAX)
            m_ = re.search(LETTER, text or "")
            r = dict(uid=f"mmlu:{j}", j=j, subject=it["subject"], raw=text, pred=m_.group(0) if m_ else None, gold="ABCD"[it["a"]], **meta)
            with open(path, "a", encoding="utf-8") as f: f.write(json.dumps(r, ensure_ascii=False) + "\n")
            print("mmlu", j, repr(text), r["gold"], meta["secs"], flush=True)
        for c in mine_b:
            user = c["x"]["text"] + Q[c["fr"]][c["rung"]]
            text, meta = gen(user, GEN_MAX)
            cands = [(cand, c["tp2"]["calls"][cand]["toks"]) for cand, _ in CANDS[c["fr"]]]
            f_ = fc(user, cands); a, b = (f_[cand]["lp"] for cand, _ in CANDS[c["fr"]])
            r = dict(uid=f"bat:{c['j']}", j=c["j"], set=c["set"], item=c["x"]["item"], variant=c["x"]["variant"],
                     cell=f"{c['fr']}_{c['rung']}", text=text, dec=parse(c["fr"], text), lo=a - b, fc=f_, **meta)
            with open(path, "a", encoding="utf-8") as f: f.write(json.dumps(r, ensure_ascii=False) + "\n")
            print("cell", c["j"], r["cell"], repr(text[:30]), round(r["lo"], 2), meta["secs"], flush=True)
    except Budget:
        print("BUDGET_SPENT: stopping cleanly; re-run with resume_run to continue", flush=True)
        return
    print("SHARD_DONE", k, flush=True)


def gather(dirs):
    recs, gates = {}, []
    for d in dirs:
        for root, _, files in os.walk(d):
            if "records.jsonl" in files:
                for l in open(os.path.join(root, "records.jsonl"), encoding="utf-8"):
                    r = json.loads(l); recs[r["uid"]] = r
            if "gate.json" in files: gates.append(dict(json.load(open(os.path.join(root, "gate.json"))), shard=os.path.basename(root)))
    os.makedirs(RUN, exist_ok=True)
    for kind, n in (("mmlu", len(mmlu_items())), ("bat", 792)):
        rows = [recs[f"{kind}:{j}"] for j in range(n) if f"{kind}:{j}" in recs]
        with open(os.path.join(RUN, "mmlu.jsonl" if kind == "mmlu" else "battery.jsonl"), "w", encoding="utf-8") as f:
            for r in rows: f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(kind, len(rows), "of", n)
    json.dump(sorted(gates, key=lambda g: g["shard"]), open(os.path.join(RUN, "shards.json"), "w"), indent=1)
    print(f"{len(gates)} shard gates -> {os.path.relpath(RUN, ROOT)}")


if __name__ == "__main__":
    a = sys.argv[1:]
    opt = lambda f, d=None: a[a.index(f) + 1] if f in a else d
    if not a: sys.exit(__doc__)
    if a[0] == "run8b": run8b(opt("--gguf"), opt("--gguf-sha256"), int(opt("--shard", 0)), int(opt("--of", 1)), float(opt("--budget", 0)),
                              int(opt("--limit", 0)))
    elif a[0] == "gather": gather(a[a.index("--in") + 1:])
    else: sys.exit(__doc__)
