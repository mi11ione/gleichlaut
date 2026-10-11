"""PREREG R19 (the certified 8B Q8_0 on the identity probes) and the post hoc 70B-by-backend re-score: the vendored research
inputs match their sha256, the prompts and candidates are the recorded ones, the recorded cross-backend references
reproduce the research log, the decision rule on small cases, and the committed results recomputed."""
import importlib.util, json, os, unittest
from gleichlaut import score

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
spec = importlib.util.spec_from_file_location("r19_identity", os.path.join(ROOT, "tools", "r19_identity.py"))
T = importlib.util.module_from_spec(spec); spec.loader.exec_module(T)
RES = os.path.join(ROOT, "eval", "results")


def test_inputs_sha256_and_prompts():
    T.verify()
    d = T.defs(); C = T.cells()
    assert len(C) == 792 and len(T.mmlu_items()) == 250
    assert d["mmlu_prompt"](dict(q="Q?", ch=["a", "b", "c", "d"])) == "Q?\n\nA. a\nB. b\nC. c\nD. d\n\nAnswer with only the letter (A, B, C or D)."
    assert d["CANDS"] == {"conv": [("Ja", 1), ("Nein", 1)], "ver": [("Urteil: schuldig", 2), ("Urteil: nicht schuldig", 3)]}
    for c in C:                                   # the token tails the API recorded for tp2 are the ones R19 scores
        for cand, k in d["CANDS"][c["fr"]]:
            assert len(c["tp2"]["calls"][cand]["toks"]) == k and "".join(c["tp2"]["calls"][cand]["toks"]) == cand.split("Urteil:")[-1]
    assert {c["fp1"]["fp"] for c in C} == {"fp1-nes"} and all("-tp2-" in c["tp2"]["calls"]["Ja" if c["fr"] == "conv" else "Urteil: schuldig"]["fp"] for c in C)
    assert d["parse"]("conv", "Nein.") == 0 and d["parse"]("ver", "nicht schuldig\n\nBegründung") == 0 and d["parse"]("ver", "schuldig") == 1


def test_recorded_references_match_the_research_log():
    C = T.cells()
    assert sum(c["fp1"]["text"] == c["gen8"]["text"] for c in C) == 760                  # "byte-identical ... in 760 of 792"
    assert sum(c["fp1"]["dec"] is not None and c["fp1"]["dec"] == c["gen8"]["dec"] for c in C) == 787
    assert sum((c["fc8"]["lo_conv"] > 0) == (c["tp2"]["lo_conv"] > 0) for c in C) == 760
    sh = json.load(open(os.path.join(T.D, "mmlu", "res_swiss-ai_apertus-v1.5-8b.json"), encoding="utf-8"))
    v1 = json.load(open(os.path.join(T.D, "mmlu", "res_swiss-ai_apertus-8b-instruct.json"), encoding="utf-8"))
    assert sum(r["pred"] == r["gold"] for r in sh) == 211 and sum(r["pred"] == r["gold"] for r in v1) == 177   # 84.4%, 70.8%


def test_decision_rule():
    assert score.r19_decide(72.0, [5, 15], 92.0, 4.0)[0] == "O1"
    assert score.r19_decide(72.0, [5, 15], 92.0, 2.0)[0] == "O4"          # not "far more" than tp2
    assert score.r19_decide(60.0, [15, 30], 92.0, 4.0)[0] == "O4"         # below 65%: not near 70-75%
    assert score.r19_decide(70.0, [8, 20], 60.0, 0.0)[0] == "O2"
    assert score.r19_decide(83.0, [-3, 5], 70.0, 0.0)[0] == "O3" and score.r19_decide(79.0, [-1, 9], 95.0, 5.0)[0] == "O3"
    assert score.r19_decide(76.0, [2, 12], 80.0, 1.0)[0] == "O4"


def test_r19_result_recomputed():
    r = score.identity_r19()
    if r is None: raise unittest.SkipTest("R19 run not recorded yet")
    assert json.loads(json.dumps(r)) == json.load(open(os.path.join(RES, "identity_r19.json"), encoding="utf-8"))
    assert r["shards"]["certificate_verified"] == r["shards"]["n"] > 0 and r["mmlu"]["n"] == 250 and r["battery"]["n"] == 792
    assert r["mmlu"]["shared"]["correct"] == 211 and r["mmlu"]["v1_8b"]["correct"] == 177


def test_fresh166_by_backend():
    r = score.fresh166_by_backend()
    assert json.loads(json.dumps(r)) == json.load(open(os.path.join(RES, "fresh166_by_backend.json"), encoding="utf-8"))
    h, m = r["fresh166"], r["m3_seed1"]
    assert h["calls"] == 285 and h["calls_by_backend"] == {"unknown": 285}                 # the headline run logged no backend
    assert m["calls"] == 283 and m["calls_by_backend"] == {"fp1-nes": 81, "tp2": 202}      # the R2 rerun: 202 / 81
    for arm in (h, m):
        assert sum(v["n"] for v in arm["by_backend"].values()) == 166
    assert m["by_backend"]["mixed"]["reasked"] == m["by_backend"]["mixed"]["n"]          # two calls on two backends = a re-ask


def test_baseline_plus_q8_0():
    r = score.baseline_plus()
    assert json.loads(json.dumps(r)) == json.load(open(os.path.join(RES, "baseline_plus.json"), encoding="utf-8"))
    assert (r["delta"], r["ci95"], r["edits_saved_pct"]) == (6.6, [1.8, 12.0], 41.3)      # the 70B row unchanged
    q = r["q8_0"]
    assert q["n"] == 166 and q["rules_plus_exact"] == r["rules_plus_exact"] and q["model_exact"] == 17.5
    assert q["ci95"][0] <= q["delta"] <= q["ci95"][1] and q["edits_saved_ci95"][0] <= q["edits_saved_pct"] <= q["edits_saved_ci95"][1]
