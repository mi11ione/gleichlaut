"""PREREG R22. The round-5b rule set (gleichlaut.audit, block 'round 5b', frozen at 951cdd2) on the 6 Oct 2026 register,
the label reuse from R15 and the blind worklist for the findings R15 never labelled. No model, no network.

  register  run the frozen R22 rules on the register (--hist: the snapshot JSONs 20261006-{de,fr,it}.json) and write
            data/audit/audit_r22_20261006.json: the R22 findings, each with its label source (the R15 finding whose final
            label it reuses, or 'new'), and the R15 findings R22 no longer reports. New findings (both halves) go to a
            blind worklist (eval/labels/audit_r22_20261006_worklist.json: R15's fields and question, ids S00...,
            random.Random(20261022) order) with the key map apart (audit_r22_20261006_key.json).
  merge     annotator TSVs A, B (and T for the disagreements) -> eval/labels/audit_r22_20261006.tsv (final = majority).
  --check   (with register) rebuild and compare with the committed file (exit 1 on any difference).

Label reuse (PREREG R22): an R22 finding reuses the R15 final label when an R15 finding has the same limitation, language
and kind and (operator) the same value, (negation) the same negated side and an overlapping target sentence,
(number_word) a shared value on the same side.

usage: PYTHONPATH=src python3 tools/r22_audit.py register [--hist DIR] [--check]
       PYTHONPATH=src python3 tools/r22_audit.py merge"""
import json, os, random, sys
from collections import Counter
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))
from gleichlaut import audit as A                 # noqa: E402
from gleichlaut.sl.ingest import nrm              # noqa: E402

DATE, SEED = "20261006", 20261022
OUT = os.path.join(ROOT, "data", "audit", f"audit_r22_{DATE}.json")
LAB = os.path.join(ROOT, "eval", "labels")
R15_LABELS = os.path.join(LAB, f"audit_r15_{DATE}.tsv")
WL, KEY, TSV = (os.path.join(LAB, f"audit_r22_{DATE}{s}") for s in ("_worklist.json", "_key.json", ".tsv"))
HIST = os.path.expanduser("~/Desktop/hackapertus/spikes/gleichlaut/data/hist")
FREEZE = "951cdd2"


def tsv(p):
    rows = [l.split("\t") for l in open(p, encoding="utf-8").read().splitlines()]
    return [dict(zip(rows[0], r)) for r in rows[1:]]


def _vals(f, side):
    return set(x["value"] for x in (f.get("de_only") if side == "de" else f.get("tgt_only")) or [])


def match(f, R15):
    """the R15 finding whose label f reuses (PREREG R22 rule), or None."""
    for g in R15:
        if (g["id"], g["lang"], g["kind"]) != (f["id"], f["lang"], f["kind"]): continue
        if f["kind"] == "operator" and g["value"] == f["value"]: return g
        if f["kind"] == "negation" and g["side"] == f["side"] and g["tgt_span"][0] < f["tgt_span"][1] and f["tgt_span"][0] < g["tgt_span"][1]:
            return g
        if f["kind"] == "number_word" and any(_vals(f, s) & _vals(g, s) for s in ("de", f["lang"])): return g
    return None


def register(hist, check=False):
    J, names = A.load(hist, DATE)
    F, _ = A.run(hist, DATE, J, names)
    R = A.run_r22(J, names, F)
    R15 = json.load(open(os.path.join(A.DEST, f"audit_{DATE}.json"), encoding="utf-8"))["findings_r5"]
    lab = {r["fid"]: r for r in tsv(R15_LABELS)}
    used = set()
    for f in R:
        g = match(f, R15)
        f["label_source"] = dict(reused=g["fid"], final=lab[g["fid"]]["final"]) if g else dict(reused=None)
        if g: used.add(g["fid"])
    new = [f for f in R if not f["label_source"]["reused"]]
    order = random.Random(SEED).sample(new, len(new))
    W, K = [], {}
    for j, f in enumerate(order):
        r = f"S{j:02d}"; f["label_source"]["worklist_id"] = r
        W.append(dict(id=r, kind=f["kind"], lang=f["lang"], de=nrm(J["de"]["lim"][f["id"]]), fr=nrm(J["fr"]["lim"].get(f["id"]) or ""),
                      it=nrm(J["it"]["lim"].get(f["id"]) or ""), finding=f["description"], question=A.QUESTION_R5))
        K[r] = dict(cud=f["id"], fid=f["fid"], kind=f["kind"], lang=f["lang"], half=f["half"])
    dropped = [dict(fid=g["fid"], id=g["id"], lang=g["lang"], kind=g["kind"], half=g["half"], final=lab[g["fid"]]["final"])
               for g in R15 if g["fid"] not in used]
    out = dict(prereg="R22", date=DATE, freeze=FREEZE, rules_sha256=A.r22_block_sha(), rules_logic_sha256=A.r22_logic_sha(),
               op_align=A.OP_ALIGN, model_calls=0,
               summary=dict(findings=len(R), by_kind={k: sum(f["kind"] == k for f in R) for k in A.KINDS_R22},
                            by_half=dict(Counter(f["half"] for f in R)), reused=len(R) - len(new), new=len(new),
                            r15_findings=len(R15), r15_dropped=len(dropped)),
               findings=R, r15_dropped=dropped)
    if check:
        old = json.load(open(OUT, encoding="utf-8"))
        same = json.dumps(old, sort_keys=True, ensure_ascii=False) == json.dumps(json.loads(json.dumps(out, ensure_ascii=False)), sort_keys=True, ensure_ascii=False)
        print("identical" if same else "DIFFERENT"); sys.exit(0 if same else 1)
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    if W or not os.path.exists(WL):
        json.dump(W, open(WL, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        json.dump(K, open(KEY, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(out["summary"]))
    for f in R:
        print(f["fid"], f["kind"], f["id"], f["lang"], f["half"], f["label_source"])
    print("R15 findings no longer reported:", len(dropped))


def merge(dirpath=LAB):
    K = json.load(open(KEY, encoding="utf-8"))
    rd = lambda p: {r["id"]: r for r in tsv(p)} if os.path.exists(p) else {}
    A_, B_, T_ = (rd(os.path.join(dirpath, f"audit_r22_{DATE}_{x}.tsv")) for x in "ABT")
    yes = lambda v: v in ("real", "minor")
    rows = ["id\tfid\tkind\tcud\tlang\thalf\tA\tB\tT\tfinal\tnote_A"]
    for r in sorted(K):
        a, b = A_[r]["answer"], B_[r]["answer"]
        t = T_.get(r, {}).get("answer", "")
        if yes(a) != yes(b) and not t: sys.exit(f"{r}: annotators disagree and no tie-break label")
        fin = (a if yes(a) == yes(t) else b) if yes(a) != yes(b) else (a if a == b else ("minor" if yes(a) else "not"))
        k = K[r]
        rows.append("\t".join([r, k["fid"], k["kind"], k["cud"], k["lang"], k["half"], a, b, t, fin, A_[r].get("note", "")]))
    open(TSV, "w", encoding="utf-8").write("\n".join(rows) + "\n")
    print(f"{len(rows) - 1} records -> {os.path.relpath(TSV, ROOT)}")


if __name__ == "__main__":
    a = sys.argv[1:]
    h = a[a.index("--hist") + 1] if "--hist" in a else (os.environ.get("GLEICHLAUT_HIST") or HIST)
    if a[:1] == ["register"]: register(h, "--check" in a)
    elif a[:1] == ["merge"]: merge()
    else: sys.exit(__doc__)
