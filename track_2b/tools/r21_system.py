"""PREREG R21 (variant v4-system: the v3-terms house-wording block plus one fixed system message replacing the chat
template's default "Apertus 1.5 Omni" system turn; gleichlaut.v4system).

  mine --xml DIR      the house wording of the two 2025 snapshots the fresh 166 start from (no model, no network): BAG's
                      XML captures DIR/20250611/Preparations.xml (release 01.06.2025) and DIR/20250731/Preparations.xml
                      (release 01.07.2025), the files the fresh set was built from (frozen/build_fresh.py SNAPS), read
                      with sl.ingest.load_xml (the frozen exporter emulation), one text per limitation code as sl.ingest
                      keeps it (the first; differing later texts listed as conflicts), then the unchanged mining code
                      (termbase.mine, house.mine, termbase.shared_words) -> data/termbase/r21/*_<date>.json + TBX.
  prompts             write eval/prereg/r21_prompts.json: the system message and its sha256; per set (fresh166 and both
                      live months) and item, the terms date, the block, and the sha256 of the first request of the frozen
                      pipeline, of v3-terms and of v4-system (user prompt; system message).
  --check             recompute both and compare with the committed files (exit 1 on any difference; mine needs --xml).
  run --set S --gguf F --gguf-sha256 H --shard K --of N     CI only (workflow r21-8b, GitHub Actions CPU runners): the
                      build certificate of the loaded GGUF is verified first (cli.certified_gguf; the shard stops without
                      one), then every item of the shard through v4-system with llama.cpp; every exchange (request as
                      sent, response) -> out/r21/<S>/shard<K>of<N>/exchanges.jsonl, records.jsonl, calls.jsonl, gate.json.
  gather --set S --in DIR...   merge the shards -> data/r21/runs/<S>_q8_0/ (records, exchanges, calls, summary).
  worklist --map M    pool every ready (guard verdict) v4-system draft that differs from BAG's published text and is not
                      byte-identical to an already-labelled draft of the same item, all three sets, one record per distinct
                      (set, item, draft), seeded shuffle, neutral ids -> eval/labels/r21_system_ready_worklist.json.
  merge A B [T] --map M   annotator TSVs -> eval/labels/r21_system_ready.tsv (tie-break worklist when only A and B).
usage: PYTHONPATH=src python3 tools/r21_system.py mine --xml DIR|prompts|--check [--xml DIR]|run ...|gather ...|worklist|merge"""
import argparse, glob, hashlib, json, os, random, re, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from gleichlaut import core, cli, v3terms, v4system

SETS = ("fresh166", "20260801-20260901", "20260901-20261001")
XML = (("20250601", "20250611"), ("20250701", "20250731"))      # release date, capture dir (backtest.WB, frozen/build_fresh.py)
TB = os.path.join(core.ROOT, "data", "termbase", "r21")
OUT = os.path.join(core.ROOT, "eval", "prereg", "r21_prompts.json")
RUNS = os.path.join(core.ROOT, "data", "r21", "runs")
LAB = os.path.join(core.ROOT, "eval", "labels")
WL = os.path.join(LAB, "r21_system_ready_worklist.json")
TB_WL = os.path.join(LAB, "r21_system_ready_tiebreak_worklist.json")
TSV = os.path.join(LAB, "r21_system_ready.tsv")
SEED = 20261021
BUILD = "q8_0"


def items(s):
    if s == "fresh166": return json.load(open(os.path.join(core.ROOT, "data", "items", "items_fresh.json"), encoding="utf-8"))
    return json.load(open(os.path.join(core.ROOT, "data", "shadow", s, "items.json"), encoding="utf-8"))


def drafted(s):
    """the items each set drafts: the fresh 166 all (as R1 / M2: m1 runs every item), a live month its routed items (as
    the shadow workflow; status human items are not drafted)."""
    I = items(s)
    return I if s == "fresh166" else [x for x in I if cli.route(x)[0] != "human"]


# ---------------------------------------------------------------- mine: house wording of the 2025 snapshots
def snapshot_from_xml(path):
    """-> J as audit.load returns it ({de, fr, it} each {lim, prod, conflict}) from one Preparations.xml."""
    from gleichlaut.sl.ingest import load_xml
    X = load_xml(path); J = {L: dict(lim={}, prod={}, conflict={}) for L in ("de", "fr", "it")}
    for k in sorted(X):
        for e in X[k]:
            for L in ("de", "fr", "it"):
                lim, t = J[L]["lim"], e[L]
                if k in lim and lim[k] != t: J[L]["conflict"].setdefault(k, [lim[k]]).append(t)
                elif k not in lim: lim[k] = t
            for L in ("de", "fr", "it"):
                p = J[L]["prod"].setdefault(e["pid"] or "", dict(name=e["product"], keys=[]))
                if k not in p["keys"]: p["keys"].append(k)
    return J


def mine(xml_dir, dest=TB):
    from gleichlaut import termbase, house
    os.makedirs(dest, exist_ok=True); out = {}
    for date, sub in XML:
        src = os.path.join(xml_dir, sub, "Preparations.xml"); sha = core.sha256(src)
        J = snapshot_from_xml(src)
        src_txt = f"BAG Spezialitätenliste release {termbase._d(date)}, XML capture {sub}/Preparations.xml (sha256 {sha})"
        tb = termbase.mine(J, date); tb["meta"]["source"] = src_txt; review(tb)
        hs = house.mine(J, date); hs["meta"]["source"] = src_txt
        sw = termbase.shared_words(J, date)
        jp = os.path.join(dest, f"termbase_{date}.json"); termbase.write_json(tb, jp)
        house.write_json(hs, os.path.join(dest, f"house_sentences_{date}.json"))
        termbase.write_json(sw, os.path.join(dest, f"shared_words_{date}.json"))
        termbase.write_tbx(tb, os.path.join(dest, f"gleichlaut_sl_termbase_{date}.tbx"))
        out[date] = dict(xml=f"{sub}/Preparations.xml", xml_sha256=sha, limitations=len(J["de"]["lim"]),
                         conflicts=len(J["de"]["conflict"]),
                         house_terms=sum(1 for e in tb["entries"] if e.get("house")),
                         house_sentences=sum(1 for e in hs["entries"] if e.get("house")))
        print(date, out[date], flush=True)
    return out


SHIPPED = os.path.join(core.ROOT, "data", "termbase", "termbase_20261006.json")


def review(tb):
    """PREREG R21 review of the 2025 house renderings (the R12 review rule, "a fragment, not a rendering", made mechanical;
    fixed before any run). A house rendering of a 2025 snapshot is set to house = false when (a) termbase.DROP_VARIANTS
    lists it for the term (a reviewed non-rendering), (b) its words are a strict contiguous part of the term's house
    rendering in the shipped, reviewed 6 Oct 2026 termbase (a fragment), or (c) it shares no word of four or more letters
    with the shipped entry's rendering or its variants (not a rendering of the term). It only removes entries: every
    wording in a block still comes from the item's old snapshot."""
    from gleichlaut import termbase
    W = lambda t: re.findall(r"\w+", (t or "").lower())
    S = {(e["lang"], e["term"]): e for e in json.load(open(SHIPPED, encoding="utf-8"))["entries"]}
    tb["meta"]["r21_review"] = review.__doc__.split("\n\n")[0].strip(); tb["meta"]["r21_rejected"] = []
    for e in tb["entries"]:
        if not e.get("house"): continue
        k = (e["lang"], e["term"]); s = S.get(k); p = e["preferred"]; w = W(p); why = None
        if p in termbase.DROP_VARIANTS.get(k, ()): why = "(a) a reviewed non-rendering (termbase.DROP_VARIANTS)"
        elif s and s.get("house") and s.get("preferred") != p:
            sw = W(s["preferred"])
            if len(w) < len(sw) and any(sw[i:i + len(w)] == w for i in range(len(sw))): why = f"(b) fragment of « {s['preferred']} »"
        if not why and s:
            ref = set(W(s.get("preferred"))) | {t for v in s.get("variants", []) for t in W(v["text"])}
            if ref and not {t for t in w if len(t) >= 4} & ref: why = f"(c) not a rendering (shipped: « {s.get('preferred')} »)"
        if why:
            e["house"] = False; e["note"] = f"rejected on review (PREREG R21): {why}"
            tb["meta"]["r21_rejected"].append(dict(lang=e["lang"], term=e["term"], rendering=p, reason=why))
    return tb


# ---------------------------------------------------------------- prompts: the pre-registered request record
def build():
    res = dict(rule="PREREG R21", variant=v4system.VARIANT, system=v4system.SYSTEM, system_sha256=v4system.SYSTEM_SHA256,
               house_wording={}, sets={})
    for d in ("20250601", "20250701", "20260801", "20260901"):
        tp, hp = v4system.paths(d)
        res["house_wording"][d] = dict(termbase=os.path.relpath(tp, core.ROOT), termbase_sha256=core.sha256(tp),
                                       house_sentences=os.path.relpath(hp, core.ROOT), house_sentences_sha256=core.sha256(hp))
    for s in SETS:
        F = core.Pipeline(cli._capture, "g3"); Vs = v4system.SystemPipeline(v4system.capture); rows = {}
        for x in drafted(s):
            d = v4system.terms_date(x)
            pf = cli_first(F, x); pv = v4system.first_request(Vs, x)
            F.ns["PA"] = v3terms.template(F.PA, v3terms.block(x, d, v4system.resources(d)))      # v3-terms' prompt for this item
            try: pt = cli_first(F, x)
            finally: F.ns["PA"] = F.PA
            sh = lambda p: hashlib.sha256(p.encode()).hexdigest() if p else None
            rows[x["key"]] = dict(lang=x["lang"], terms_date=d, block=Vs.block(x), model_call=pf is not None,
                                  prompt_sha256_frozen=sh(pf), prompt_sha256_v3=sh(pt), prompt_sha256_v4=sh(pv[0] if pv else None),
                                  system_v4=bool(pv and pv[2] == v4system.SYSTEM))
        res["sets"][s] = dict(drafted=len(rows), model_calls=sum(r["model_call"] for r in rows.values()),
                              with_block=sum(bool(r["block"]) for r in rows.values()),
                              user_prompt_changed=sum(r["prompt_sha256_frozen"] != r["prompt_sha256_v4"] for r in rows.values()),
                              user_prompt_equal_v3=sum(r["prompt_sha256_v3"] == r["prompt_sha256_v4"] for r in rows.values()),
                              terms_dates=dict(sorted(__import__("collections").Counter(r["terms_date"] for r in rows.values()).items())),
                              items=rows)
    return res


def cli_first(P, x):
    try: P.draft(x)
    except cli._Captured as c: return c.prompt
    return None


def dump(o): return json.dumps(o, ensure_ascii=False, indent=1, sort_keys=True) + "\n"


# ---------------------------------------------------------------- CI: the certified 8B with v4-system
def run(s, gguf, sha, k, n):
    from gleichlaut import backends
    p, got, cert, why = cli.certified_gguf([gguf])
    print("certificate:", why, flush=True)
    if not p or (sha and got != sha): sys.exit(f"R21: no valid build certificate for {gguf}: {why}")
    out = os.path.join(core.ROOT, "out", "r21", s, f"shard{k}of{n}"); os.makedirs(out, exist_ok=True)
    json.dump(dict(certificate=cert.get("name"), verified=why, gguf_sha256=got, llama_cpp_python=backends.llama_version(),
                   system_sha256=v4system.SYSTEM_SHA256), open(os.path.join(out, "gate.json"), "w"), indent=1)
    I = [x for i, x in enumerate(items(s)) if i % n == k]
    ask = v4system.Recorder(backends.LlamaCpp(gguf, backends.lang_of_prompt, log=os.path.join(out, "calls.jsonl"), gguf_sha256=got),
                            os.path.join(out, "exchanges.jsonl"))
    if s != "fresh166":                  # a live month: the shadow workflow's drafting (routing, record fields) with v4-system
        review = ("experimental prompt variant v4-system (PREREG R21), not the certified pipeline: every item is reviewed; "
                  "guard_status keeps the frozen guards' verdict")
        cli.draft_items(I, ask, out, "sl", review, f"llamacpp {ask.model} (variant v4-system, PREREG R21)", "v4-system", None)
    else:                                # the fresh 166: as m1.run (R1 / M2), every item through the pipeline
        P = v4system.SystemPipeline(ask); path = os.path.join(out, "records.jsonl")
        done = {json.loads(l)["key"] for l in open(path, encoding="utf-8")} if os.path.exists(path) else set()
        for x in I:
            if x["key"] in done: continue
            t0 = time.time(); r = P.run(x); r["wall_secs"] = round(time.time() - t0, 1); r["build"] = BUILD
            with open(path, "a", encoding="utf-8") as f: f.write(json.dumps(r, ensure_ascii=False) + "\n")
            print(x["key"], "flag" if r["guard_flag"] else "ready", r["wall_secs"], "s", flush=True)
    print("SHARD_DONE", s, k, flush=True)


def gather(s, dirs):
    R, E, C, G = {}, {}, [], []
    for d in dirs:
        for p in sorted(glob.glob(os.path.join(d, "**", "records.jsonl"), recursive=True)):
            for l in open(p, encoding="utf-8"): r = json.loads(l); R[r["key"]] = r
        for p in sorted(glob.glob(os.path.join(d, "**", "exchanges.jsonl"), recursive=True)):
            for l in open(p, encoding="utf-8"):
                e = json.loads(l)
                if e["key"] in E and E[e["key"]]["response"] != e["response"]: sys.exit(f"{e['key']}: same request, different answers")
                E.setdefault(e["key"], e)
        for p in sorted(glob.glob(os.path.join(d, "**", "calls.jsonl"), recursive=True)): C += [l for l in open(p, encoding="utf-8") if l.strip()]
        for p in sorted(glob.glob(os.path.join(d, "**", "gate.json"), recursive=True)): G.append(json.load(open(p)))
    I = items(s); missing = [x["key"] for x in I if x["key"] not in R]
    if missing: sys.exit(f"{len(missing)} items missing, e.g. {missing[:5]}")
    dest = os.path.join(RUNS, f"{s}_{BUILD}"); os.makedirs(dest, exist_ok=True)
    with open(os.path.join(dest, "records.jsonl"), "w", encoding="utf-8") as f:
        for x in I: f.write(json.dumps(R[x["key"]], ensure_ascii=False) + "\n")
    with open(os.path.join(dest, "exchanges.jsonl"), "w", encoding="utf-8") as f:
        for k in sorted(E): f.write(json.dumps(E[k], ensure_ascii=False, sort_keys=True) + "\n")
    open(os.path.join(dest, "calls.jsonl"), "w", encoding="utf-8").write("".join(C))
    calls = [json.loads(l) for l in C]
    S = dict(set=s, build=BUILD, variant=v4system.VARIANT, system_sha256=v4system.SYSTEM_SHA256, items=len(I), shards=len(G),
             gates=sorted({g["certificate"] for g in G}), gates_verified=sum(bool(g.get("certificate")) for g in G),
             gguf_sha256=sorted({g["gguf_sha256"] for g in G}), llama_cpp_python=sorted({g.get("llama_cpp_python") or "" for g in G}),
             calls=len(calls), exchanges=len(E), models_served=sorted({c.get("model_served") or "" for c in calls}),
             prompt_tokens=sum(c.get("prompt_tokens") or 0 for c in calls), completion_tokens=sum(c.get("completion_tokens") or 0 for c in calls),
             cpu_secs=round(sum(c.get("secs") or 0 for c in calls), 1))
    json.dump(S, open(os.path.join(dest, "summary.json"), "w", encoding="utf-8"), indent=1, sort_keys=True)
    print(json.dumps(S, indent=1))


# ---------------------------------------------------------------- labels
def labelled_drafts():
    """-> {(set, key): {draft text: final label}} of every already-labelled draft (byte-identical reuse)."""
    from gleichlaut import score
    from gleichlaut.certify import reference_labels
    L = {}
    I = {x["key"]: x for x in items("fresh166")}
    F70 = score.load_jsonl(score.RUNS["fresh166"]["final"]); lab70 = score.load_labels(score.RUNS["fresh166"]["labels"])
    for k, r in F70.items():
        if k in lab70: L.setdefault(("fresh166", k), {})[r["out"]] = lab70[k]
    def tsv(p):
        if not os.path.exists(p): return []
        X = open(p, encoding="utf-8").read().splitlines(); h = X[0].split("\t")
        return [dict(zip(h, l.split("\t"))) for l in X[1:] if l.strip()]
    for rel, lab in (("runs/8b_q4_k_m_fresh166_g3_final.jsonl", "m1_q4_k_m_fresh166.tsv"), ("runs/8b_q8_0_fresh166_g3_final.jsonl", "m1_q8_0_fresh166.tsv"),
                     ("runs/8b_q8_0_fresh166_g3_rerun.jsonl", "m2_rerun_q8_0_fresh166.tsv")):
        if not os.path.exists(os.path.join(score.DATA, rel)): continue
        F = score.load_jsonl(rel)
        for r in tsv(os.path.join(LAB, lab)): L.setdefault(("fresh166", r["key"]), {})[F[r["key"]]["out"]] = r["final"]
    for m in SETS[1:]:
        D = os.path.join(core.ROOT, "data", "shadow", m)
        recs = {}
        for f in os.listdir(D):
            p = os.path.join(D, f, "records.jsonl")
            if os.path.exists(p): recs[f] = {json.loads(l)["key"]: json.loads(l) for l in open(p, encoding="utf-8")}
        for r in tsv(os.path.join(LAB, f"shadow_{m.replace('-', '_')}_ready.tsv")):
            L.setdefault((m, r["key"]), {})[recs[r["model"]][r["key"]]["out"]] = r["final"]
        for r in tsv(os.path.join(LAB, "r12_terms_ready.tsv")):
            if r["month"] == m: L.setdefault((m, r["key"]), {})[recs[f"v3_terms_{r['model']}"][r["key"]]["out"]] = r["final"]
    return L


def v4_records(s):
    p = os.path.join(RUNS, f"{s}_{BUILD}", "records.jsonl")
    return {json.loads(l)["key"]: json.loads(l) for l in open(p, encoding="utf-8")} if os.path.exists(p) else None


def ready(r):
    """the frozen guards' verdict: a fresh-166 record carries guard_flag; a live-month record guard_status (status is
    'flagged' for every variant record, since the variant is not certified)."""
    if r.get("status") == "human": return False
    return r.get("guard_status") == "ready" if "guard_status" in r else not r["guard_flag"]


def worklist(map_path):
    norm = core.lock.norm; L = labelled_drafts(); todo = []
    for s in SETS:
        R = v4_records(s); I = {x["key"]: x for x in items(s)}
        for k, r in R.items():
            if not ready(r) or not I[k].get("tgt_new") or norm(r["out"]) == norm(I[k]["tgt_new"]): continue
            if r["out"] in L.get((s, k), {}): continue
            todo.append((s, k, r["out"]))
    keys = sorted(set(todo)); random.Random(SEED).shuffle(keys)
    W, M = [], {}
    for i, (s, k, out) in enumerate(keys):
        x = {y["key"]: y for y in items(s)}[k]; rid = f"S{i:02d}"
        W.append(dict(id=rid, lang=x["lang"], de_old=x["de_old"], de_new=x["de_new"], tgt_old=x["tgt_old"], draft=out, official_new=x["tgt_new"]))
        M[rid] = dict(set=s, key=k)
    open(WL, "w", encoding="utf-8").write(json.dumps(W, ensure_ascii=False, indent=1) + "\n")
    open(map_path, "w", encoding="utf-8").write(json.dumps(M, indent=1) + "\n")
    print(f"{len(W)} ready non-exact drafts need a label -> {WL}; map -> {map_path}")


def _tsv(p):
    X = open(p, encoding="utf-8").read().splitlines(); h = X[0].split("\t")
    return {r["id"]: r for r in (dict(zip(h, l.split("\t"))) for l in X[1:] if l.strip())}


def merge(a, b, t, map_path):
    M = json.load(open(map_path)); A, B = _tsv(a), _tsv(b)
    assert set(A) == set(B) == set(M), "annotator files do not cover the worklist"
    need = sorted(i for i in M if A[i]["needs_fix"] != B[i]["needs_fix"] or A[i]["class"] != B[i]["class"] or "REAL" in (A[i]["class"], B[i]["class"]))
    T = {}
    if need and not t:
        W = {w["id"]: w for w in json.load(open(WL, encoding="utf-8"))}
        ids = list(need); random.Random(SEED + 1).shuffle(ids); TW, TM = [], {}
        for j, i in enumerate(ids):
            w = dict(W[i]); w["id"] = f"X{j:02d}"; TW.append(w); TM[w["id"]] = i
        open(TB_WL, "w", encoding="utf-8").write(json.dumps(TW, ensure_ascii=False, indent=1) + "\n")
        open(map_path + ".tiebreak.json", "w").write(json.dumps(TM, indent=1) + "\n")
        print(f"{len(need)} need a tie-break -> {TB_WL}; map -> {map_path}.tiebreak.json"); return
    if t:
        TM = json.load(open(map_path + ".tiebreak.json")); T = {TM[k]: v for k, v in _tsv(t).items()}
        assert set(T) == set(need), "tie-break file does not cover the disagreements"
    rows = ["\t".join(("set", "key", "A_fix", "A_class", "B_fix", "B_class", "T_fix", "T_class", "final_fix", "final", "note_A"))]
    for i in sorted(M, key=lambda i: (M[i]["set"], M[i]["key"])):
        a_, b_, t_ = A[i], B[i], T.get(i)
        if t_:
            v = [a_["class"], b_["class"], t_["class"]]; fin = t_["class"] if len(set(v)) == 3 else max(set(v), key=v.count)
            fx = [a_["needs_fix"], b_["needs_fix"], t_["needs_fix"]]; ffix = max(set(fx), key=fx.count)
        else: fin, ffix = a_["class"], a_["needs_fix"]
        rows.append("\t".join((M[i]["set"], M[i]["key"], a_["needs_fix"], a_["class"], b_["needs_fix"], b_["class"],
                               t_["needs_fix"] if t_ else "", t_["class"] if t_ else "", ffix, fin, a_.get("note", "").replace("\t", " "))))
    open(TSV, "w", encoding="utf-8").write("\n".join(rows) + "\n")
    print(f"merged {len(M)} records -> {TSV}; tie-breaks {len(T)}")


def main(argv):
    if not argv or argv[0] in ("-h", "--help"): print(__doc__); return 0
    if argv[0] == "--check": argv = ["check"] + argv[1:]
    ap = argparse.ArgumentParser(prog="r21_system"); ap.add_argument("cmd")
    ap.add_argument("--xml"); ap.add_argument("--set", choices=SETS); ap.add_argument("--gguf"); ap.add_argument("--gguf-sha256")
    ap.add_argument("--shard", type=int, default=0); ap.add_argument("--of", type=int, default=1)
    ap.add_argument("--in", dest="inp", nargs="+"); ap.add_argument("--map"); ap.add_argument("files", nargs="*")
    a = ap.parse_args(argv)
    if a.cmd == "mine":
        mine(a.xml); return 0
    if a.cmd == "prompts":
        open(OUT, "w", encoding="utf-8").write(dump(build()))
        for s, v in json.load(open(OUT, encoding="utf-8"))["sets"].items():
            print(f"{s}: drafted {v['drafted']}, model calls {v['model_calls']}, with a block {v['with_block']}, "
                  f"user prompt changed {v['user_prompt_changed']}, equal to v3-terms {v['user_prompt_equal_v3']}, dates {v['terms_dates']}")
        print("system sha256", v4system.SYSTEM_SHA256); return 0
    if a.cmd == "check":
        ok = True
        if a.xml:
            import tempfile, filecmp
            with tempfile.TemporaryDirectory() as d:
                mine(a.xml, d)
                for f in sorted(os.listdir(d)):
                    same = filecmp.cmp(os.path.join(d, f), os.path.join(TB, f), shallow=False); ok &= same
                    print(f"{f}: {'identical' if same else 'DIFFERS'}")
        same = open(OUT, encoding="utf-8").read() == dump(build()); ok &= same
        print("r21 prompts: " + ("identical to the committed file" if same else "DIFFER from the committed file")); return 0 if ok else 1
    if a.cmd == "run": run(a.set, a.gguf, a.gguf_sha256, a.shard, a.of); return 0
    if a.cmd == "gather": gather(a.set, a.inp); return 0
    if a.cmd == "worklist": worklist(a.map); return 0
    if a.cmd == "merge": merge(a.files[0], a.files[1], a.files[2] if len(a.files) > 2 else None, a.map); return 0
    print(__doc__); return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
