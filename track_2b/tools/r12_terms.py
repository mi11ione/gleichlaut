"""PREREG R12 (v3-terms: BAG's house wording in the drafting prompt), the parts that are not model runs. No model, no network.

  blocks      write eval/prereg/r12_blocks.json: per live month and drafted item, the block the variant adds to the prompt
              (as the model sees it, slot codes for numbers), the entries behind it, and the sha256 of the exact first
              prompt of both the frozen pipeline and the variant (committed with the rule, before any run).
  --check     recompute the blocks and compare with the committed file (exit 1 on any difference).
  worklist    pool every ready (guard_status) v3-terms draft that differs from BAG's published text, both months and both
              models, one record per distinct (item, draft), seeded shuffle (SEED), neutral ids (R1 protocol fields only)
              -> eval/labels/r12_terms_ready_worklist.json; the id -> (month, model, key) map goes to the path given with
              --map (kept apart, never shown to an annotator).
  merge A B [T] --map M   annotator TSVs -> eval/labels/r12_terms_ready.tsv (one row per (month, model, key)); with only
              A and B, also writes the tie-break worklist (disagreement on needs_fix or class, or any REAL) and its map.
usage: PYTHONPATH=src python3 tools/r12_terms.py blocks|--check|worklist --map PATH|merge A.tsv B.tsv [T.tsv] --map PATH"""
import hashlib, json, os, random, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from gleichlaut import core, cli, v3terms

MONTHS = ("20260801-20260901", "20260901-20261001")
MODELS = ("q8_0", "70b")
OUT = os.path.join(core.ROOT, "eval", "prereg", "r12_blocks.json")
LAB = os.path.join(core.ROOT, "eval", "labels")
WL = os.path.join(LAB, "r12_terms_ready_worklist.json")
TB_WL = os.path.join(LAB, "r12_terms_ready_tiebreak_worklist.json")
TSV = os.path.join(LAB, "r12_terms_ready.tsv")
SEED = 20261015
FIELDS = ("lang", "de_old", "de_new", "tgt_old", "draft", "official_new")


def items(month): return json.load(open(os.path.join(core.ROOT, "data", "shadow", month, "items.json"), encoding="utf-8"))


def first_prompt(P, x):
    try: P.draft(x)
    except cli._Captured as c: return c.prompt
    return None                                     # rule-only: no model call


def build():
    res = dict(rule="PREREG R12", variant=v3terms.VARIANT, header=v3terms.HEAD, months={})
    for m in MONTHS:
        d = m[:8]; R = v3terms.resources(d)
        F, V = core.Pipeline(cli._capture, "g3"), v3terms.TermsPipeline(cli._capture, d)
        rows = {}
        for x in items(m):
            if cli.route(x)[0] == "human": continue
            pf, pv = first_prompt(F, x), first_prompt(V, x)
            E = v3terms.entries(x, d, R)
            rows[x["key"]] = dict(lang=x["lang"], entries=E, block=v3terms.block(x, d, R),
                                  model_call=pf is not None,
                                  prompt_sha256_frozen=hashlib.sha256(pf.encode()).hexdigest() if pf else None,
                                  prompt_sha256_v3=hashlib.sha256(pv.encode()).hexdigest() if pv else None)
        tp, hp = v3terms.paths(d)
        res["months"][m] = dict(terms_date=d, termbase=os.path.relpath(tp, core.ROOT), house_sentences=os.path.relpath(hp, core.ROOT),
                                termbase_sha256=core.sha256(tp), house_sentences_sha256=core.sha256(hp),
                                drafted=len(rows), with_block=sum(bool(r["block"]) for r in rows.values()),
                                model_calls=sum(r["model_call"] for r in rows.values()),
                                prompt_changed=sum(r["prompt_sha256_frozen"] != r["prompt_sha256_v3"] for r in rows.values()),
                                items=rows)
    return res


def dump(o): return json.dumps(o, ensure_ascii=False, indent=1, sort_keys=True) + "\n"


def worklist(map_path):
    norm = core.lock.norm; recs = []
    for m in MONTHS:
        I = {x["key"]: x for x in items(m)}
        for mo in MODELS:
            p = os.path.join(core.ROOT, "data", "shadow", m, f"v3_terms_{mo}", "records.jsonl")
            for l in open(p, encoding="utf-8"):
                r = json.loads(l); x = I[r["key"]]
                if r["status"] == "human" or r.get("guard_status") != "ready" or not x.get("tgt_new"): continue
                if norm(r["out"]) == norm(x["tgt_new"]): continue
                recs.append((m, mo, r["key"], r["out"]))
    uniq = {}
    for m, mo, k, out in recs: uniq.setdefault((m, k, out), []).append(mo)
    keys = sorted(uniq); random.Random(SEED).shuffle(keys)
    W, M = [], {}
    for i, (m, k, out) in enumerate(keys):
        x = {y["key"]: y for y in items(m)}[k]; rid = f"V{i:02d}"
        W.append(dict(id=rid, lang=x["lang"], de_old=x["de_old"], de_new=x["de_new"], tgt_old=x["tgt_old"], draft=out,
                      official_new=x["tgt_new"]))
        M[rid] = dict(month=m, key=k, models=uniq[(m, k, out)])
    open(WL, "w", encoding="utf-8").write(json.dumps(W, ensure_ascii=False, indent=1) + "\n")
    open(map_path, "w", encoding="utf-8").write(json.dumps(M, indent=1) + "\n")
    print(f"{len(recs)} ready non-identical drafts, {len(W)} distinct -> {WL}; map -> {map_path}")


def _tsv(p):
    L = open(p, encoding="utf-8").read().splitlines(); h = L[0].split("\t")
    return {r["id"]: r for r in (dict(zip(h, l.split("\t"))) for l in L[1:] if l.strip())}


def merge(a, b, t, map_path):
    M = json.load(open(map_path)); A, B = _tsv(a), _tsv(b)
    assert set(A) == set(B) == set(M), "annotator files do not cover the worklist"
    need = sorted(i for i in M if A[i]["needs_fix"] != B[i]["needs_fix"] or A[i]["class"] != B[i]["class"]
                  or "REAL" in (A[i]["class"], B[i]["class"]))
    T = _tsv(t) if t else {}
    if need and not t:
        W = {w["id"]: w for w in json.load(open(WL, encoding="utf-8"))}
        ids = list(need); random.Random(SEED + 1).shuffle(ids)
        TW, TM = [], {}
        for j, i in enumerate(ids):
            w = dict(W[i]); w["id"] = f"W{j:02d}"; TW.append(w); TM[w["id"]] = i
        open(TB_WL, "w", encoding="utf-8").write(json.dumps(TW, ensure_ascii=False, indent=1) + "\n")
        open(map_path + ".tiebreak.json", "w").write(json.dumps(TM, indent=1) + "\n")
        print(f"{len(need)} need a tie-break -> {TB_WL}; map -> {map_path}.tiebreak.json"); return
    if t:
        TM = json.load(open(map_path + ".tiebreak.json")); T = {TM[k]: v for k, v in T.items()}
        assert set(T) == set(need), "tie-break file does not cover the disagreements"
    rows = ["\t".join(("month", "model", "key", "A_fix", "A_class", "B_fix", "B_class", "T_fix", "T_class", "final_fix", "final", "note_A"))]
    for i in sorted(M, key=lambda i: (M[i]["month"], M[i]["key"])):
        a_, b_, t_ = A[i], B[i], T.get(i)
        if t_: votes = [a_["class"], b_["class"], t_["class"]]; fin = t_["class"] if len(set(votes)) == 3 else max(set(votes), key=votes.count)
        else: fin = a_["class"]
        if t_: fx = [a_["needs_fix"], b_["needs_fix"], t_["needs_fix"]]; ffix = max(set(fx), key=fx.count)
        else: ffix = a_["needs_fix"]
        for mo in M[i]["models"]:
            rows.append("\t".join((M[i]["month"], mo, M[i]["key"], a_["needs_fix"], a_["class"], b_["needs_fix"], b_["class"],
                                   t_["needs_fix"] if t_ else "", t_["class"] if t_ else "", ffix, fin, a_.get("note", "").replace("\t", " "))))
    open(TSV, "w", encoding="utf-8").write("\n".join(rows) + "\n")
    print(f"merged {len(M)} records ({len(rows) - 1} rows) -> {TSV}; tie-breaks {len(T)}")


def main(argv):
    if not argv or argv[0] in ("-h", "--help"): print(__doc__); return 0
    mp = argv[argv.index("--map") + 1] if "--map" in argv else None
    if argv[0] == "blocks":
        open(OUT, "w", encoding="utf-8").write(dump(build()))
        d = json.load(open(OUT, encoding="utf-8"))
        for m, v in d["months"].items():
            print(f"{m}: drafted {v['drafted']}, model calls {v['model_calls']}, with a block {v['with_block']}, prompt changed {v['prompt_changed']}")
        return 0
    if argv[0] == "--check":
        same = open(OUT, encoding="utf-8").read() == dump(build())
        print("r12 blocks: " + ("identical to the committed file" if same else "DIFFER from the committed file")); return 0 if same else 1
    if argv[0] == "worklist": worklist(mp); return 0
    if argv[0] == "merge":
        files = [a for a in argv[1:] if a != "--map" and a != mp]
        merge(files[0], files[1], files[2] if len(files) > 2 else None, mp); return 0
    print(__doc__); return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
