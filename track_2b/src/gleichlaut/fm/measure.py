"""PREREG R8 scoring: every failure-mode test, the shipped Q8_0 GGUF beside the recorded MLX 4-bit (and 70B) runs, from
recorded outputs only (no model). Each number comes from the research scorer of the original test:

  T1 free / T2 window   frozen/s2/score2.py score_one (arm 3 / arm 2); window obedience by the rule of
                        docs/research/rescue70b-gleichlaut.md A (reproduces 165/226 for the 8B MLX and 183/226 for the 70B)
  T3 judge              research/round7b/analyze7b.py (log-probabilities) and research/rescue70b/fx/fx.py (generation),
                        both executed whole on staged copies
  T4 typing             research/dreiklang/scripts/analyze.py + correlation.py, executed in a subprocess on a staged copy;
                        operator / subject accuracy of the top option over all gold conditions (analyze.load_s1 + gold)
  T5 retry              the recorded retry decisions; flags re-computed with the frozen guards3 (score.rows_for logic)

compute() -> the content of eval/results/failure_modes_q8_0.json. A Q8_0 run that is not recorded yet gives None."""
import contextlib, io, json, os, random, shutil, subprocess, sys, tempfile, types
from collections import Counter
from .. import core, score
from . import RES
from .run import RUNS, TYPING_META, judge_prompts

S = core.SCORE
LABELS = os.path.join(core.ROOT, "eval", "labels")
FREE_LABELS = "fm_q8_0_free_flips.tsv"          # T1: seeded 20 of the counter hits, R1 protocol
S2B_LABELS = "fm_q8_0_s2b_ready.tsv"            # T5: ready non-exact drafts of the dev-120 S2b run, R1 protocol
MLX = dict(free="runs/8b_dwq_dev120_free.jsonl", window="runs/8b_dwq_dev120_window.jsonl", s2b="runs/8b_dwq_dev120_s2b.jsonl",
           window70="runs/70b_dev120_window.jsonl")
SEED = 20261009


def _have(rel): return os.path.exists(os.path.join(score.DATA, rel))
def _pct(k, n): return round(100 * k / n, 1) if n else None


def _final_labels(name):
    p = os.path.join(LABELS, name)
    if not os.path.exists(p): return {}
    L = open(p, encoding="utf-8").read().splitlines(); h = L[0].split("\t")
    return {r["key"]: r for r in (dict(zip(h, l.split("\t"))) for l in L[1:])}



# ---------------------------------------------------------------- T1 free translation, T2 window-only
def _arm_rows(rel, arm):
    I = score.load_items("items/items_dev.json"); F = score.load_jsonl(rel)
    return I, F, [S["score_one"](x, F[x["key"]]["out"], arm, F[x["key"]]) for x in I]


def _mech(B):
    n = len(B)
    return dict(n=n, exact=_pct(sum(r["exact"] for r in B), n), ef1=round(100 * sum(r["ef1"] for r in B) / n, 1),
                chrf=round(sum(r["chrf"] for r in B) / n, 1), flagged=_pct(sum(r["flagged"] for r in B), n),
                lexicon_flips=sum(bool(r["flip"]) for r in B))


def free_sample(rel=RUNS["free"]):
    """the seeded 20 of the counter hits that R8 labels (keys sorted, random.Random(20261009).sample)."""
    _, _, B = _arm_rows(rel, "3")
    hits = sorted(r["key"] for r in B if r["flip"])
    return sorted(random.Random(SEED).sample(hits, min(20, len(hits))))


def free():
    out = {"mlx": _mech(_arm_rows(MLX["free"], "3")[2])}
    out["mlx"].update(sample_n=20, sample_real_flips=2, source_labels="docs/research/gleichlaut-results.md (S2 hand check)")
    if not _have(RUNS["free"]): return dict(out, q8_0=None)
    q = _mech(_arm_rows(RUNS["free"], "3")[2])
    lab = _final_labels(FREE_LABELS); smp = free_sample()
    if lab:
        rows = [lab[k] for k in smp]
        c = Counter(r["final"] for r in rows); real = c.get("REAL", 0)
        q.update(sample_n=len(rows), sample_classes=dict(sorted(c.items())), sample_real_flips=real,
                 real_flips_extrapolated=round(q["lexicon_flips"] * real / len(rows)),
                 annotators=dict(n=len(rows), agree=sum(r["A_class"] == r["B_class"] for r in rows),
                                 tiebreak=sum(bool(r.get("T_class")) for r in rows)))
    q["secs_per_item"] = round(sum(r.get("secs", 0) for r in score.load_jsonl(RUNS["free"]).values()) / q["n"], 1)
    out["q8_0"] = q
    return out


def window_obedience(rel):
    """windows whose output is longer than the old window + 1.5 x the German insertion + 30 characters."""
    I, F, _ = _arm_rows(rel, "2"); n = dis = 0
    for x in I:
        r = F[x["key"]]; p = core.gl2.plan(x["de_old"], x["de_new"], x["tgt_old"], x["lang"]); a, b, ops = core.lock.de_ops(x["de_old"], x["de_new"])
        assert len(p["windows"]) == len(r["windows"]), x["key"]
        for w, wops in zip(r["windows"], p["ops_per_window"]):
            ins = " ".join(" ".join(b[o[3]:o[4]]) for o in wops)
            n += 1; dis += len(w["out"]) > len(w["old"]) + 1.5 * len(ins) + 30
    return dict(windows=n, disobeyed=dis, disobeyed_pct=_pct(dis, n))


def window():
    out = {}
    for k, rel in (("mlx", MLX["window"]), ("70b", MLX["window70"]), ("q8_0", RUNS["window"])):
        if not _have(rel): out[k] = None; continue
        out[k] = dict(window_obedience(rel), **_mech(_arm_rows(rel, "2")[2]))
        if k == "q8_0":
            F = score.load_jsonl(rel)
            out[k]["model_digits"] = sum(len(__import__("re").findall(r"\d", w["raw"])) for r in F.values() for w in r["windows"])
    I = score.load_items("items/items_dev.json")
    out["rules"] = _mech([S["score_one"](x, core.gl2.rules(x["de_old"], x["de_new"], x["tgt_old"], x["lang"])[0], "1") for x in I])
    return out


# ---------------------------------------------------------------- T5 retry (and the S2b dev-120 row)
def _s2b(rel, labels):
    I = score.load_items("items/items_dev.json"); F = score.load_jsonl(rel); P = core.check_only("g3")
    A, B = [], []
    for x in I:
        f = F[x["key"]]
        a = S["score_one"](x, core.gl2.rules(x["de_old"], x["de_new"], x["tgt_old"], x["lang"])[0], "1"); b = S["score_one"](x, f["out"], "1")
        b.update(flagged=P.check(x, f["out"])["flag"], reasked=False, replaced=False, rule_only=f["rule_only"], family=x["cluster"],
                 cls="exact" if b["exact"] else labels.get(x["key"], "?"))
        a.update(family=x["cluster"]); A.append(a); B.append(b)
    s = score.summarise(A, B, labelled=False)
    U = [r for r in B if not r["flagged"]]
    d = dict(n=s["n"], exact=s["exact"]["model"], exact_delta=s["exact"]["delta"], flag_rate=s["flag_rate"], ready=s["unflagged"],
             ready_classes=dict(sorted(Counter(r["cls"] for r in U).items())),
             ready_real=sum(r["cls"] == "REAL" for r in U), ready_unlabelled=sum(r["cls"] == "?" for r in U),
             retried=sum(bool(f.get("retried")) for f in F.values()), retry_fixed=sum(bool(f.get("retried")) and f["lock_ok"] for f in F.values()))
    return d, [r["key"] for r in U if not r["exact"]]


def s2b_worklist_keys(rel=RUNS["s2b"]):
    return _s2b(rel, {})[1]


def retry():
    mlx_lab = score.load_labels(score.RUNS["dev120_8b"]["labels"])
    out = {"mlx": _s2b(MLX["s2b"], mlx_lab)[0]}
    out["q8_0"] = _s2b(RUNS["s2b"], {k: r["final"] for k, r in _final_labels(S2B_LABELS).items()})[0] if _have(RUNS["s2b"]) else None
    R = score.load_jsonl("runs/8b_q8_0_fresh166_g3_final.jsonl").values()
    out["q8_0_fresh166_r1"] = dict(n=len(R), retried=sum(r["retried"] for r in R), retry_fixed=sum(r["retried"] and r["lock_ok"] for r in R),
                                   reasked=sum(bool(r.get("reasked")) for r in R), reask_kept=sum(bool(r.get("replaced")) for r in R),
                                   source="data/runs/8b_q8_0_fresh166_g3_final.jsonl (PREREG R1, M2)")
    return out


# ---------------------------------------------------------------- T3 equivalence judging
def _analyze7b(rows):
    d = tempfile.mkdtemp(prefix="r8-7b-")
    try:
        os.makedirs(os.path.join(d, "results"))
        json.dump(dict(rows=rows), open(os.path.join(d, "results", "fedlex7b_A.json"), "w", encoding="utf-8"), ensure_ascii=False)
        src = os.path.join(RES, "round7b", "analyze7b.py")
        ns = {"__name__": "analyze7b", "__file__": os.path.join(d, "analyze7b.py")}
        with open(src, encoding="utf-8") as f: code = compile(f.read(), src, "exec")
        with contextlib.redirect_stdout(io.StringIO()): exec(code, ns)
        res = json.load(open(os.path.join(d, "results", "analysis7b.json"), encoding="utf-8"))
    finally:
        shutil.rmtree(d, ignore_errors=True)
    A = res["A"]
    return dict(hits_at_half=A["hits_thr"], targets=A["n_t"], false_flags=A["false_flags_n"], controls=A["n_c"],
                auroc_item=A["auroc_item"], argmax_hits=A["hits_argmax"], auroc_item_ab=res["A[ab only]"]["auroc_item"],
                auroc_item_ba=res["A[ba only]"]["auroc_item"], logodds_argmax_hits=A["logodds"]["hits_argmax"],
                logodds_auroc_item=A["logodds"]["auroc_item"], mean_mass=A["mean_mass"],
                max_p_diff_controls=max(p[o]["p_diff"] for r in rows if r["kind"] == "control" for p in r["pairs"].values() for o in ("ab", "ba")),
                max_p_diff_targets=max(p[o]["p_diff"] for r in rows if r["kind"] == "target" for p in r["pairs"].values() for o in ("ab", "ba")),
                cases=[dict(case=c["case"], gold=c["gold"], argmax=c["argmax"]) for c in A["cases"]])


def _fx(answers):
    """fx.py executed whole with a replay `ask` (recorded answer per prompt) and the vendored items."""
    P, PAIRS, _ = judge_prompts(); items = json.load(open(os.path.join(RES, "round7", "fedlex_items.json"), encoding="utf-8"))
    raw = {}
    for x in items:
        for a, b in PAIRS:
            for o, prompt in (("ab", P["q"].format(la=a.upper(), lb=b.upper(), ta=x[a], tb=x[b], o1="Ja", o2="Nein")),
                              ("ba", P["q"].format(la=b.upper(), lb=a.upper(), ta=x[b], tb=x[a], o1="Nein", o2="Ja"))):
                t = answers[(x["id"], f"{a}-{b}", o)]
                assert raw.setdefault(prompt, t) == t, "one prompt, two answers"
    d = tempfile.mkdtemp(prefix="r8-fx-")
    common = types.ModuleType("common")
    common.ask = lambda prompt, tag, cap, mt: (raw[prompt], {"usd": 0.0, "cached": True})
    common.pmap = lambda f, xs, n: [f(x) for x in xs]
    real_open = open
    ITEMS = "/Users/mi11ion/Desktop/hackapertus/spikes/round7/fedlex_items.json"
    def _open(p, *a, **k): return real_open(os.path.join(RES, "round7", "fedlex_items.json") if p == ITEMS else p, *a, **k)
    old_mod, old_argv, old_path = sys.modules.get("common"), sys.argv, list(sys.path)
    try:
        sys.modules["common"] = common; sys.argv = ["fx.py"]
        src = os.path.join(RES, "rescue70b", "fx", "fx.py")
        ns = {"__name__": "fx", "__file__": os.path.join(d, "fx", "fx.py"), "open": _open}
        os.makedirs(os.path.join(d, "fx"))
        with open(src, encoding="utf-8") as f: code = compile(f.read(), src, "exec")
        with contextlib.redirect_stdout(io.StringIO()): exec(code, ns)
        res = json.load(open(os.path.join(d, "fx", "fx_results.json"), encoding="utf-8"))
    finally:
        if old_mod is None: sys.modules.pop("common", None)
        else: sys.modules["common"] = old_mod
        sys.argv = old_argv; sys.path[:] = old_path; shutil.rmtree(d, ignore_errors=True)
    s = res["summary"]
    return dict(hits=s["hits"], targets=s["n_targets"], false_flags=s["false_flags"], controls=s["n_controls"], targets_flagged=s["targets_flagged"],
                nein_answers=s["any_nein_answers"], calls=s["n_calls"], unparsed=s["unparsed"], order_agreement=round(s["order_agreement"], 3))


def judge():
    mlx = json.load(open(os.path.join(RES, "round7b", "results", "fedlex7b_A.json"), encoding="utf-8"))["rows"]
    fx70 = json.load(open(os.path.join(RES, "rescue70b", "fx", "fx_raw.json"), encoding="utf-8"))
    out = {"mlx_logprob": _analyze7b(mlx), "70b_generation": _fx({(r["id"], r["pair"], r["order"]): r["raw"] for r in fx70})}
    if not _have(RUNS["judge"]): return dict(out, q8_0_logprob=None, q8_0_generation=None)
    rows = [json.loads(l) for l in open(os.path.join(score.DATA, RUNS["judge"]), encoding="utf-8")]
    out["q8_0_logprob"] = _analyze7b(rows)
    out["q8_0_generation"] = _fx({(r["id"], p, o): r["pairs"][p][o]["raw"] for r in rows for p in r["pairs"] for o in ("ab", "ba")})
    out["q8_0_answer_token_ids"] = rows[0].get("token_ids")
    return out


# ---------------------------------------------------------------- T4 operator typing
_OPACC = r"""
import json, sys
sys.path.insert(0, sys.argv[1])
import analyze as A, gold as G, compare as K
D, I, gold, _, _ = G.load(); S1 = A.load_s1()
n = op = sj = ge = 0
for it in D["items"]:
    for l in K.LANGS:
        for c, g in zip(it["langs"][l]["cands"], gold[(it["cud"], l)]):
            if g is None: continue
            b = S1[f"{it['cud']}/{l}/{c['idx']}"]["best"]; n += 1; op += b[1] == g["op"]; sj += b[0] == g["subj"]; ge += b[1] == ">="
print(json.dumps(dict(gold_conditions=n, operator_correct=op, subject_correct=sj, top_operator_ge=ge)))
"""


def _dreiklang(scores_rel=None, meta_rel=None):
    d = tempfile.mkdtemp(prefix="r8-dk-")
    try:
        dk = os.path.join(d, "dreiklang"); shutil.copytree(os.path.join(RES, "dreiklang"), dk)
        shutil.copyfile(os.path.join(RES, "gleichlaut", "scripts", "census.py"), os.path.join(dk, "scripts", "census.py"))
        if scores_rel:
            shutil.copyfile(os.path.join(score.DATA, scores_rel), os.path.join(dk, "raw", "s1_scores.jsonl"))
            shutil.copyfile(os.path.join(score.DATA, meta_rel), os.path.join(dk, "raw", "s1_meta.json"))
        os.remove(os.path.join(dk, "raw", "threshold.json"))
        env = dict(os.environ, PYTHONHASHSEED="0")
        for s in ("analyze.py", "correlation.py"):
            subprocess.run([sys.executable, "-I", os.path.join(dk, "scripts", s)], cwd=dk, env=env, check=True, capture_output=True, timeout=600)
        acc = json.loads(subprocess.run([sys.executable, "-I", "-c", _OPACC, os.path.join(dk, "scripts")], cwd=dk, env=env, check=True,
                                        capture_output=True, text=True, timeout=600).stdout)
        an = json.load(open(os.path.join(dk, "raw", "analysis.json"), encoding="utf-8"))
        co = json.load(open(os.path.join(dk, "raw", "correlation.json"), encoding="utf-8"))
        th = json.load(open(os.path.join(dk, "raw", "threshold.json"), encoding="utf-8"))
    finally:
        shutil.rmtree(d, ignore_errors=True)
    held = next(r for r in an["runs"] if r["name"] == "S1 8B tau" and r["split"] == "held")
    h = co["held"]; n = acc["gold_conditions"]
    return dict(gold_conditions=n, operator_correct=acc["operator_correct"], operator_acc_pct=_pct(acc["operator_correct"], n),
                subject_correct=acc["subject_correct"], subject_acc_pct=_pct(acc["subject_correct"], n), top_operator_ge=acc["top_operator_ge"],
                tau=round(th["tau"], 3), held_triples=h["n_triples"], held_wrong_all_three=h["wrong_dist"].get("3", 0),
                held_expected_all_three_if_independent=h["expected_indep"].get("3"), held_identical_wrong=h["all3_wrong_identical"],
                held_phi=h["phi"], held_phi_min=min(h["phi"].values()), held_phi_max=max(h["phi"].values()), held_accepted_correct=held["accepted"]["correct"], held_accepted=held["accepted"]["n"],
                held_accepted_precision_pct=_pct(held["accepted"]["correct"], held["accepted"]["n"]),
                held_flags=held["flags"]["n"], held_flags_real=held["flags"]["lenient"],
                prompts=an.get("speed", {}).get("n_prompts"), secs_per_prompt=round(an.get("speed", {}).get("mean_s", 0), 2))


def typing():
    out = {"mlx": _dreiklang()}
    if not (_have(RUNS["typing"]) and _have(TYPING_META)): return dict(out, q8_0=None)
    q = _dreiklang(RUNS["typing"], TYPING_META)
    m = json.load(open(os.path.join(score.DATA, TYPING_META), encoding="utf-8"))
    q.update(selfcheck_maxdiff=round(m["selfcheck_maxdiff"], 4), static_tokens=m["static_tokens"], chat_format=m.get("chat_format"))
    out["q8_0"] = q
    return out


def compute():
    return dict(prereg="R8", build=dict(gguf="apertus-v1.5-8b-text-q8_0.gguf", sha256="dea904ad80cd725ec89962abae464477f5d8114d1f4377514f381f7dc2ed202d",
                                        runtime="llama-cpp-python 0.3.35, GitHub Actions ubuntu-latest CPU (fm workflow)"),
                free=free(), window=window(), judge=judge(), typing=typing(), retry=retry())


if __name__ == "__main__":
    print(json.dumps(compute(), ensure_ascii=False, indent=1))
