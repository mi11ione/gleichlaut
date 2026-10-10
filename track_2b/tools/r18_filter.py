"""PREREG R18. Apertus 8B log-probability filter for the round-5 audit findings that ship off (R15: operator, negation,
number_word). For each finding, the aligned German sentence and the French / Italian sentence go to the certified 8B
GGUF Q8_0 with one fixed question (same condition? Ja / Nein); score = P(Nein) from the first answer position, computed
exactly as R8 T3 (gleichlaut.fm.run.run_judge: both orders, the mean of the two). The threshold is chosen on planted
copies (fit half) and applied unchanged to the 31 register findings (score.audit_apertus_filter).

  build     write data/r18/items.json: the 31 R15 register findings (6 Oct 2026) and the R15 held planted copies
            (tools/audit_inject.py --protocol r15 --half held, seed 20261016, regenerated here and checked against
            eval/results/audit_injection_r15_held.json), each planted sentence pair with its unmodified control.
            Deterministic; no model, no network. --hist: the snapshot JSONs (files 20261006-{de,fr,it}.json).
  --check   rebuild and compare with the committed file (exit 1 on any difference).
  run8b     CI only (workflow r18-8b, GitHub Actions CPU runners): the build certificate of the loaded GGUF is verified
            first (cli.certified_gguf: records re-scored, hashes match; the shard stops without one), then every pair of
            the shard is scored in both orders. Resumable; every raw answer is kept. Never run on a team machine.
  gather    merge the shard folders into data/r18/runs/8b_q8_0/ (records.jsonl in items order, calls.jsonl, shards.json).

Sentence pair of a finding or a planted edit (pair_at): the pair of audit.aligned() (the pairs the round-5 checks judge)
whose target span contains the target position (for a German-side finding: whose German span contains the German
position); if none, the pair of audit.align() (any cost) that does; if none, the item is left out and counted.
Negation and number_word register findings use the pair their check judged (negation_diff / number_word_diff).

usage: PYTHONPATH=src python3 tools/r18_filter.py build|--check [--hist DIR]
       PYTHONPATH=src python3 tools/r18_filter.py run8b --gguf models/q8_0.gguf --gguf-sha256 SHA --shard K --of N [--budget S]
                                                       [--limit M]  (smoke: at most M planted pairs, never a register pair)
       PYTHONPATH=src python3 tools/r18_filter.py gather --in DIR"""
import hashlib, json, math, os, random, sys, time
from collections import Counter
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from gleichlaut import audit as A, core          # noqa: E402
from gleichlaut.sl.ingest import nrm              # noqa: E402

OUT = os.path.join(ROOT, "data", "r18", "items.json")
RUN = os.path.join(ROOT, "data", "r18", "runs", "8b_q8_0")
HIST = os.path.expanduser("~/Desktop/hackapertus/spikes/gleichlaut/data/hist")
DATE, SEED_SPLIT = "20261006", "r18"
LABELS = os.path.join(ROOT, "eval", "labels", "audit_r15_20261006.tsv")
HELD = os.path.join(ROOT, "eval", "results", "audit_injection_r15_held.json")
LNAME = {"de": "DE", "fr": "FR", "it": "IT"}
# The R18 question: R8 T3's prompt (round7b/spike7b.py PAIR['de']) with the object and the checks named for a limitation
# sentence; both orders, Ja/Nein in the order named, plain user message, no system message, no prefill.
Q = ("Unten stehen zwei Sprachfassungen ({la} und {lb}) derselben Stelle einer Limitation der Spezialitätenliste des BAG. "
     "Beide Fassungen sind gleichermassen verbindlich und sollten dieselbe Bedingung festlegen. Prüfe, ob sie dieselbe "
     "Bedingung ausdrücken, insbesondere dieselbe Richtung einer Grenze (mindestens oder höchstens, über oder unter), "
     "dieselben Zahlen und dieselbe Verneinung.\n\n"
     "[{la}] {ta}\n\n[{lb}] {tb}\n\nDrücken die beiden Fassungen dieselbe Bedingung aus? Antworte nur mit {o1} oder {o2}.")
YES, NO, MAX_TOKENS = "Ja", "Nein", 8


def prompts(lang, de, tgt):
    """-> {'ab': German first, 'Ja oder Nein'; 'ba': target first, 'Nein oder Ja'} (R8 T3's two orders)."""
    L = LNAME[lang]
    return {"ab": Q.format(la="DE", lb=L, ta=de, tb=tgt, o1=YES, o2=NO),
            "ba": Q.format(la=L, lb="DE", ta=tgt, tb=de, o1=NO, o2=YES)}


def pkey(lang, de, tgt): return hashlib.sha256(f"{lang}\n{de}\n{tgt}".encode()).hexdigest()[:20]


def split(i):
    """planted copies: threshold half 'fit' or evaluation half 'test', by limitation (md5 of 'r18:<id>')."""
    return "fit" if int(hashlib.md5(f"{SEED_SPLIT}:{i}".encode()).hexdigest(), 16) % 2 == 0 else "test"


def pair_at(de, tgt, lang, tpos=None, dpos=None):
    """-> (de_span, tgt_span, how) of the sentence pair holding the position, or None (module docstring)."""
    inside = lambda p: (tpos is not None and p[1][0] <= tpos[0] and tpos[1] <= p[1][1]) or \
                       (tpos is None and dpos is not None and p[0][0] <= dpos[0] and dpos[1] <= p[0][1])
    for how, P in (("aligned", A.aligned(de, tgt, lang)), ("align", A.align(de, tgt, lang)[0])):
        for p in P:
            if inside(p): return p[0], p[1], how
    return None


def register():
    T = json.load(open(os.path.join(ROOT, "data", "audit", "audit_texts_20261006.json"), encoding="utf-8"))["texts"]
    F = json.load(open(os.path.join(ROOT, "data", "audit", "audit_20261006.json"), encoding="utf-8"))["findings_r5"]
    rows = [l.split("\t") for l in open(LABELS, encoding="utf-8").read().splitlines()]
    lab = {r["fid"]: r for r in (dict(zip(rows[0], x)) for x in rows[1:])}
    out, miss = [], []
    for f in F:
        L = f["lang"]; de, tgt = nrm(T[f["id"]]["de"]), nrm(T[f["id"]][L]); sd = sg = how = None
        if f["kind"] == "negation":
            g = [g for g in A.negation_diff(de, tgt, L) if list(g["tgt_span"]) == f["tgt_span"]]
            if g: sd, sg, how = g[0]["de_sentence"], g[0]["tgt_sentence"], "negation_diff"
        elif f["kind"] == "number_word":
            w = f["tgt_only"] or f["de_only"]
            g = [g for g in A.number_word_diff(de, tgt, L) if g["value"] == w[0]["value"]
                 and (not f["tgt_only"] or list(g["span"]) == f["tgt_only"][0]["span"])]
            if g: sd, sg, how = g[0]["de_sentence"], g[0]["tgt_sentence"], "number_word_diff"
        else:
            p = pair_at(de, tgt, L, tpos=tuple(f["tgt_spans"][0]))
            if p: sd, sg, how = de[p[0][0]:p[0][1]], tgt[p[1][0]:p[1][1]], p[2]
        if sd is None: miss.append(f["fid"]); continue
        lb = lab[f["fid"]]
        out.append(dict(uid=f"reg:{f['fid']}", set="register", fid=f["fid"], wid=lb["id"], cud=f["id"], lang=L, kind=f["kind"],
                        half=f["half"], product=f.get("product"), final=lb["final"], confirmed=lb["final"] in ("real", "minor"),
                        how=how, de=sd, tgt=sg, pk=pkey(L, sd, sg)))
    return out, miss


def planted(hist):
    """the R15 held planted copies (main_r15's job list, without running the audit on them) -> rows, stats."""
    import audit_inject as I
    held = json.load(open(HELD, encoding="utf-8"))
    I._init(hist, DATE); J = I.G["J"]
    B, _, _ = A.run_all(None, DATE, J, I.G["names"], A._prep(dict(I.G["base"])), pairs=I.G["P"], r5=True)
    flagged = set(f["id"] for f in B); rep = {}
    for i in sorted(J["de"]["lim"]):
        k = tuple(nrm(J[X]["lim"].get(i) or "") for X in A.LANGS)
        if all(k) and k not in rep: rep[k] = i
    pool = sorted(i for i in rep.values() if A.half(i) == "held" and i not in flagged)
    seed = held["seed"]; out, st = [], Counter()
    for t in I.TYPES_R15:
        miss = {(m["id"], m["lang"]) for m in held["types"][t]["misses"]}
        for L in I.LANGS_T:
            rng = random.Random(f"{seed}:{t}:{L}"); ids = list(pool); rng.shuffle(ids); n = elig = 0
            for i in ids:
                old = nrm(J[L]["lim"][i]); inj = I.INJ_R15[t](old, L, rng)
                if inj is None: continue
                elig += 1
                if n >= 100: continue
                n += 1; new = inj["new"]; d = len(new) - len(old); de = nrm(J["de"]["lim"][i])
                p = pair_at(de, old, L, tpos=(inj["pos"], inj["end"] - d))
                st[f"{t}:{L}:copies"] += 1
                if p is None: st[f"{t}:{L}:no_pair"] += 1; continue
                (d0, d1), (g0, g1), how = p
                sd, ctl, pl = de[d0:d1], old[g0:g1], new[g0:g1 + d]
                assert pl != ctl, (t, L, i)
                base = dict(type=t, lang=L, cud=i, split=split(i), how=how, de=sd, sub=inj.get("sub"), detected=(i, L) not in miss)
                out.append(dict(base, uid=f"pl:{t}:{L}:{i}", set="planted", tgt=pl, pk=pkey(L, sd, pl), label=1))
                out.append(dict(base, uid=f"ct:{t}:{L}:{i}", set="control", tgt=ctl, pk=pkey(L, sd, ctl), label=0))
            assert elig == held["types"][t]["eligible_limitations"][L], (t, L, elig)
            assert n == held["types"][t]["by_lang"][L]["n"], (t, L, n)
    return out, dict(st), len(pool)


def build(hist):
    R, rmiss = register()
    P, st, pool = planted(hist)
    assert not rmiss, rmiss
    pairs, order = {}, []
    for x in R + P:                    # register first, then the planted pairs (one call pair per distinct sentence pair)
        if x["pk"] not in pairs:
            pairs[x["pk"]] = dict(pk=x["pk"], register=x["set"] == "register", lang=x["lang"], de=x["de"], tgt=x["tgt"]); order.append(x["pk"])
    reg = order[:len({x["pk"] for x in R})]; rest = order[len(reg):]
    rest = [rest[j] for j in sorted(range(len(rest)), key=lambda j: hashlib.md5(rest[j].encode()).hexdigest())]
    U = [pairs[k] for k in reg + rest]
    return dict(prereg="R18", question=Q, yes=YES, no=NO, max_tokens=MAX_TOKENS, date=DATE,
                sources=dict(register="data/audit/audit_20261006.json findings_r5 + eval/labels/audit_r15_20261006.tsv",
                             planted=f"tools/audit_inject.py --protocol r15 --half held (seed 20261016), regenerated; "
                                     f"{pool} eligible held triples; checked against eval/results/audit_injection_r15_held.json"),
                split_rule="planted copies: md5('r18:<limitation id>') even = fit (threshold), odd = test",
                counts=dict(register=len(R), planted=sum(x["set"] == "planted" for x in P), control=sum(x["set"] == "control" for x in P),
                            pairs=len(U), by_type={t: dict(Counter(x["split"] for x in P if x["type"] == t and x["set"] == "planted"))
                                                    for t in sorted({x["type"] for x in P})}),
                planted_stats=st, items=[{k: v for k, v in x.items() if k not in ("de", "tgt")} for x in R + P], pairs=U)


# ---------------------------------------------------------------- CI: the certified 8B
def run8b(gguf, sha, k, n, budget, limit=0):
    from gleichlaut import cli
    from gleichlaut.fm.run import Model, Budget
    p, got, cert, why = cli.certified_gguf([gguf])
    print("certificate:", why, flush=True)
    if not p or (sha and got != sha): sys.exit(f"R18: no valid build certificate for {gguf}: {why}")
    D = json.load(open(OUT, encoding="utf-8"))
    out = os.path.join(ROOT, "out", "r18", f"shard{k}of{n}"); os.makedirs(out, exist_ok=True)
    json.dump(dict(certificate=cert.get("name"), verified=why, gguf_sha256=got, items_sha256=core.sha256(OUT)),
              open(os.path.join(out, "gate.json"), "w"), indent=1)
    path = os.path.join(out, "records.jsonl")
    done = {json.loads(l)["pk"] for l in open(path, encoding="utf-8")} if os.path.exists(path) else set()
    model = Model(gguf, n_ctx=8192, log=os.path.join(out, "calls.jsonl"), deadline=time.time() + budget if budget else None)
    ids = {w: model.llm.tokenize(w.encode(), add_bos=False, special=False) for w in (YES, NO)}
    assert all(len(v) == 1 for v in ids.values()), ids
    mine = [x for j, x in enumerate(D["pairs"]) if j % n == k and x["pk"] not in done]
    if limit: mine = [x for x in mine if not x["register"]][:limit]          # smoke run: planted pairs only, not used
    print(f"R18 shard {k}/{n}: {len(mine)} pairs to score", flush=True)
    try:
        for x in mine:
            r = dict(pk=x["pk"], token_ids=ids)
            for o, prompt in prompts(x["lang"], x["de"], x["tgt"]).items():       # as fm.run.run_judge
                text, meta = model.chat(prompt, MAX_TOKENS, lang=None, first=True, tag="r18")
                lp = meta["first"]; ly, ln = float(lp[ids[YES][0]]), float(lp[ids[NO][0]])
                m = max(ly, ln); py, pn = math.exp(ly - m), math.exp(ln - m)
                r[o] = dict(lp_yes=ly, lp_no=ln, p_diff=pn / (py + pn), mass=math.exp(ly) + math.exp(ln),
                            ntok=meta["prompt_tokens"], raw=text, secs=meta["secs"])
            r["p_diff"] = (r["ab"]["p_diff"] + r["ba"]["p_diff"]) / 2
            with open(path, "a", encoding="utf-8") as f: f.write(json.dumps(r, ensure_ascii=False) + "\n")
            print(x["pk"][:8], x["lang"], round(r["p_diff"], 3), repr(r["ab"]["raw"][:12]), repr(r["ba"]["raw"][:12]), flush=True)
    except Budget:
        print("BUDGET_SPENT: stopping cleanly; re-run with resume_run to continue", flush=True)
        return
    print("SHARD_DONE", k, flush=True)


def gather(dirs):
    D = json.load(open(OUT, encoding="utf-8")); recs, calls, gates = {}, [], []
    for d in dirs:
        for root, _, files in os.walk(d):
            if "records.jsonl" in files:
                for l in open(os.path.join(root, "records.jsonl"), encoding="utf-8"):
                    r = json.loads(l); recs[r["pk"]] = r
            if "calls.jsonl" in files: calls += [l for l in open(os.path.join(root, "calls.jsonl"), encoding="utf-8") if l.strip()]
            if "gate.json" in files: gates.append(dict(json.load(open(os.path.join(root, "gate.json"))), shard=os.path.basename(root)))
    os.makedirs(RUN, exist_ok=True)
    with open(os.path.join(RUN, "records.jsonl"), "w", encoding="utf-8") as f:
        for x in D["pairs"]:
            if x["pk"] in recs: f.write(json.dumps(recs[x["pk"]], ensure_ascii=False) + "\n")
    open(os.path.join(RUN, "calls.jsonl"), "w", encoding="utf-8").write("".join(calls))
    json.dump(sorted(gates, key=lambda g: g["shard"]), open(os.path.join(RUN, "shards.json"), "w"), indent=1)
    print(f"{len(recs)} of {len(D['pairs'])} pairs; {len(calls)} calls; {len(gates)} shard gates -> {os.path.relpath(RUN, ROOT)}")


if __name__ == "__main__":
    a = sys.argv[1:]
    opt = lambda f, d=None: a[a.index(f) + 1] if f in a else d
    if not a: sys.exit(__doc__)
    if a[0] == "run8b": run8b(opt("--gguf"), opt("--gguf-sha256"), int(opt("--shard", 0)), int(opt("--of", 1)), float(opt("--budget", 0)),
                              int(opt("--limit", 0)))
    elif a[0] == "gather": gather(a[a.index("--in") + 1:])
    else:
        d = build(opt("--hist") or HIST)
        s = json.dumps(d, ensure_ascii=False, indent=1) + "\n"
        if a[0] == "--check":
            same = open(OUT, encoding="utf-8").read() == s
            print("r18 items", "identical" if same else "DIFFER"); sys.exit(0 if same else 1)
        os.makedirs(os.path.dirname(OUT), exist_ok=True); open(OUT, "w", encoding="utf-8").write(s)
        print("wrote", os.path.relpath(OUT, ROOT), d["counts"], d["planted_stats"])
