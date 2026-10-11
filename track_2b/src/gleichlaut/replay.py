"""`make run` steps 1-3: verify the freeze, re-execute the recorded 70B and 8B runs from their recorded responses, re-score
every recorded run, and assert that everything equals the committed results (eval/results/*.json).

Re-execution means the frozen pipeline (draft, lock check, retry, guards, re-ask) runs end-to-end with the `cache`
backend. Every model request is rebuilt from the items and looked up by the sha256 of its payload, so a cache hit
proves the prompt was rebuilt byte-for-byte; the final records must then equal the recorded ones. The 8B entry is the
PREREG R9 Q8_0 run (data/cache/responses_8b/q8_0, keyed on the request the local llama.cpp backend was sent; the digit
mask acts on generation and is not part of the request). The certified 8B runs of R1 did not record their calls and are
re-scored only."""
import json, os, sys, time
from . import core, score, backends

RESULTS = os.path.join(core.ROOT, "eval", "results")
CACHE = os.path.join(core.ROOT, "data", "cache", "responses")
FIELDS = ("out", "guard_flag", "rule_only", "reasked", "replaced", "retried", "lock_ok")
# Runs that re-execute exactly. oos242 is re-scored and re-guarded but not re-executed: 4 of its 242 items were sent
# the same masked prompt as another item concurrently and the API answered differently; the response cache kept one
# answer per prompt (docs/provenance.md).
REEXEC = ("fresh166", "dev120", "m3_seed1", "q8_0_rerun")
SCORED = ("fresh166", "oos242", "dev120", "dev120_8b")


def reexecute(run_id, workers=4):
    from concurrent.futures import ThreadPoolExecutor
    R = score.RUNS[run_id]; I = score.load_items(R["items"]); F = score.load_jsonl(R["final"])
    ask = backends.Cache(os.path.join(score.DATA, R["cache"]) if "cache" in R else CACHE, model=R.get("model", core.M70),
                         extra={"seed": R["seed"]} if "seed" in R else None)
    P = core.Pipeline(ask, R["stack"])
    with ThreadPoolExecutor(workers) as ex: out = list(ex.map(P.run, I))
    diff = [(x["key"], f) for x, r in zip(I, out) for f in FIELDS if r.get(f) != F[x["key"]].get(f)]
    return dict(items=len(I), cache_hits=ask.hits, cache_misses=len(ask.misses), differing_fields=len(diff), diff=diff[:10])


def compute():
    res = {rid: score.score_run(rid) for rid in SCORED}
    res["naive"] = score.score_naive()
    res["cost_fresh166"] = score.cost("fresh166")
    res["agreement_fresh166"] = score.agreement()
    res["fedlex_shipped"] = score.fedlex_shipped()
    res["economics"] = score.economics()
    res["fedlex_compare"] = score.fedlex_compare()
    res["m3"] = score.m3()
    res["post_edit"] = score.post_edit()
    res["ready_quality"] = score.ready_quality()
    res["audit"] = score.audit_eval()
    res["audit_more"] = score.audit_more()
    res["baseline_plus"] = score.baseline_plus()          # the 70B and the default Q8_0 against rules+
    res["fresh166_by_backend"] = score.fresh166_by_backend()   # post hoc: the 70B fresh-166 arms by serving backend
    res["m1_q4_k_m"] = score.m1("q4_k_m")
    res["post_edit_8b_q4_k_m"] = score.post_edit("runs/8b_q4_k_m_fresh166_g3_final.jsonl")
    res["m1_q8_0"] = score.m1("q8_0")
    res["post_edit_8b_q8_0"] = score.post_edit("runs/8b_q8_0_fresh166_g3_final.jsonl")
    res["m2_rerun"] = score.m2_rerun("q8_0")          # PREREG R9
    res["size_compare"] = score.size_compare()
    res["shadow_20260901_20261001"] = score.shadow_month()
    res["shadow_20260801_20260901"] = score.shadow_month("20260801-20260901", r0=True)   # PREREG R10: second, prospective month, R0 criteria
    res["r12_terms"] = score.r12_terms()          # PREREG R12: house wording in the prompt (v3-terms) beside the frozen pipeline, both live months
    res["audit_recall"] = score.audit_recall()
    res["audit_grouping"] = score.audit_grouping()
    res["audit_r15"] = score.audit_r15()             # PREREG R15: audit round 5 (operator, negation, number words)
    res["value"] = score.value()
    res["failure_modes_q8_0"] = score.failure_modes_q8_0()   # PREREG R8: failure-mode tests on the shipped Q8_0
    res["annotator_sensitivity"] = score.annotator_sensitivity(res)   # PREREG R11: planted meaning errors, reference shown / hidden
    res["fresh166_blind"] = score.blind_relabel_70b(res)   # PREREG R13: the headline 70B run relabelled fully blind (PROTOCOL.md)
    res["audit_relabel"] = score.audit_relabel()   # PREREG R14 (A): every labelled audit finding, two blind annotators + a third
    res["audit_grouping"]["reconciliation"] = score.audit_reconciliation(res)   # findings -> issues -> confirmed, in one table
    res["annotator_sensitivity_inspan"] = score.annotator_sensitivity_inspan(res)   # PREREG R14 (B): errors inside the amended wording
    res["memorisation"] = score.memorisation()     # PREREG R16: memorisation probe of the held-out answers (T) against P and N controls
    res["annotator_real_errors"] = score.annotator_real_errors()   # PREREG R17 (A): errors BAG fixed without a German change
    res["annotator_crossfamily"] = score.annotator_crossfamily()   # PREREG R17 (B): Apertus 70B as a non-Claude annotator
    res["audit_apertus_filter"] = score.audit_apertus_filter()   # PREREG R18: Apertus 8B log-probability filter on the round-5 audit findings
    res["identity_r19"] = score.identity_r19()   # PREREG R19: the certified 8B Q8_0 on the identity probes (MMLU 250, battery 792)
    from .emit import explain
    res["explain_v2"] = explain.measure_v2()       # translator-facing reasons, before/after the round-6 wording (display only)
    res["explain_v3"] = explain.measure_v3()       # house sentences, termbase in rewritten text, noise, hedging, codes (display only)
    from . import termbase
    res["termbase"] = termbase.measure()          # display-only advisory: how often it fires on ready drafts, what it explains
    return res


def write():
    os.makedirs(RESULTS, exist_ok=True)
    for k, v in compute().items():
        json.dump(v, open(os.path.join(RESULTS, f"{k}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, sort_keys=True)
    print("wrote", RESULTS)


def _cmp(a, b, path=""):
    """exact structural equality, floats within 1e-9; -> list of differing paths."""
    if isinstance(a, dict) and isinstance(b, dict):
        out = [f"{path}/{k} (missing)" for k in set(a) ^ set(b)]
        for k in set(a) & set(b): out += _cmp(a[k], b[k], f"{path}/{k}")
        return out
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b): return [f"{path} (length {len(a)} vs {len(b)})"]
        return [d for i, (x, y) in enumerate(zip(a, b)) for d in _cmp(x, y, f"{path}[{i}]")]
    if isinstance(a, float) or isinstance(b, float):
        try: return [] if abs(float(a) - float(b)) <= 1e-9 else [f"{path}: {a} vs {b}"]
        except (TypeError, ValueError): return [f"{path}: {a!r} vs {b!r}"]
    return [] if a == b else [f"{path}: {a!r} vs {b!r}"]


def headline(res):
    f = res["fresh166"]["summary"]["all"]; d = res["dev120_8b"]["summary"]["all"]; o = res["oos242"]["summary"]["all"]
    c = res["cost_fresh166"]; a = res["audit"]; ar = res["audit_recall"]["types"]; g = res["audit_grouping"]
    yn = lambda ok: "PASS" if ok else "FAIL"
    L = ["", "HEADLINE",
         f"  Audit (no model, 6 Oct 2026 register): {a['v2']['findings_all_kinds']} findings in {g['issues']} issues, "
         f"{res['audit_relabel']['sets']['register']['confirmed_majority']} confirmed by blind Claude annotators "
         f"({res['audit_relabel']['sets']['register']['confirmed_strict_real']} change a condition); planted-divergence recall: changed number "
         f"{ar['number']['recall_pct']:.1f}%, changed unit {ar['unit']['recall_pct']:.1f}%, deleted clause {ar['deletion']['recall_pct']:.1f}%, "
         f"typo {ar['typo']['recall_pct']:.1f}%",
         "  Drafting, fresh 2025 held-out set (166 FR/IT items, guards frozen before any output existed), pre-registered rule R0:",
         *[f"  Apertus 8B GGUF {name} on CPU ({role}): exact {res[k]['exact']['model']:.1f}% vs rules-only {res[k]['exact']['rules']:.1f}% "
           f"(+{res[k]['exact']['delta']:.1f}, 95% CI [{res[k]['exact']['ci95'][0]:+.1f}, {res[k]['exact']['ci95'][1]:+.1f}]), "
           f"ready {res[k]['ready_rate']:.1f}%, {yn(res[k]['pass'])}"
           for k, name, role in (("m1_q8_0", "Q8_0", "the air-gapped default"), ("m1_q4_k_m", "Q4_K_M", "the 8 GiB option"))
           if res.get(k)],
         f"  Apertus 70B, recorded Public AI endpoint: exact {f['exact']['model']:.1f}% (+{f['exact']['delta']:.1f}, 95% CI "
         f"[{f['exact']['ci95'][0]:+.1f}, {f['exact']['ci95'][1]:+.1f}]), ready {f['unflagged']}/{f['n']} = {f['ready_rate']:.1f}%, "
         f"meaning errors among ready {f['unflagged_REAL']} (95% upper bound {f['wilson95_severe_among_ready'][1]:.1f}%), {yn(f['pass'])}, "
         f"CHF {res['economics']['chf_per_item_infomaniak']:.4f}/item (Swiss provider price; USD {c['usd_per_item']:.4f} at the evaluation provider)",
         "", "WHERE IT FELL SHORT (same pass rule)",
         *[f"  live month {lbl}: " + "; ".join(
               f"{m} {yn(r['month']['meets_r0'])} (exact {r['month']['exact']}/{r['month']['n']}, flagged "
               f"{r['month']['criteria']['flag_rate'][0]:.1f}% > 70%, meaning errors among ready {r['month']['unflagged_real_n']})"
               for m, r in res[k]["r0"].items())
           for k, lbl in (("shadow_20260801_20260901", "Aug 2026 (R10; its drafted items were already in our dev and out-of-sample sets)"),) if res.get(k, {}).get("r0")],
         *[f"  house wording in the prompt (R12, v3-terms, not shipped): " + "; ".join(
               f"{run[4:6]}/{m} {'PASS' if v['v3_terms']['meets_r0'] else 'FAIL'} (identical {v['frozen']['exact']} -> {v['v3_terms']['exact']}"
               f"/{v['v3_terms']['n']}, flagged {v['v3_terms']['criteria']['flag_rate'][0]:.1f}%)"
               for run, mo in res[k]["months"].items() for m, v in mo.items() if isinstance(v, dict) and "v3_terms" in v)
           for k in ("r12_terms",) if res.get(k)],
         *[f"  live month Sep 2026 (R7): flagged " + ", ".join(f"{m} {res[k][m]['flag_rate']:.1f}%" for m in ("q8_0", "q4_k_m", "70b") if m in res[k])
           + f"; {res[k]['ready_errors_total']} errors among {res[k]['ready_total']} ready"
           for k in ("shadow_20260901_20261001",) if res.get(k)],
         f"  out-of-sample 2026 run, guards v2: {yn(o['pass'])} (unflagged untranslated {o['unflagged_german_per100']:.2f}% > 2%)",
         f"  Apertus 8B (MLX DWQ, dev 120, guards3, no re-ask): {yn(d['pass'])} (flagged {d['flag_rate']:.1f}% > 70%; "
         f"{d['unflagged_REAL']} unflagged real error)",
         f"  over-flagging: {res['fresh166']['summary']['flagged_sample']['good']} of a seeded {res['fresh166']['summary']['flagged_sample']['n']} flagged 70B drafts needed no change; "
         f"{f['exact_flagged']} of the {f['exact_n']} drafts identical to BAG's text were flagged", ""]
    return "\n".join(L)


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    if "--write" in argv: return write()
    t0 = time.time(); ok = True
    print("[1/3] freeze: verifying sha256 of frozen code, guard resources and items ...", end=" ", flush=True)
    core.verify_freeze(strict=True); print("OK", len(json.load(open(core.FREEZE))["files"]), "files")
    print("[2/3] re-executing recorded 70B and 8B runs from recorded responses (no network) ...")
    rep = {}
    for rid in REEXEC:
        r = reexecute(rid); rep[rid] = r
        good = r["cache_misses"] == 0 and r["differing_fields"] == 0
        ok &= good
        print(f"      {rid:10s} items {r['items']:3d}  prompts rebuilt and found {r['cache_hits']:3d}  misses {r['cache_misses']}  "
              f"records differing {r['differing_fields']}  {'OK' if good else 'MISMATCH ' + str(r['diff'])}")
    print("[3/3] re-guarding every recorded output and re-scoring every run against eval/results ...")
    res = compute()
    for k, v in res.items():
        p = os.path.join(RESULTS, f"{k}.json")
        if not os.path.exists(p): print(f"      {k}: no committed result"); ok = False; continue
        d = _cmp(json.loads(json.dumps(v)), json.load(open(p, encoding="utf-8")))
        ok &= not d
        print(f"      {k:14s} {'OK' if not d else 'DIFFERS: ' + '; '.join(d[:3])}")
    print(headline(res))
    print(f"replay {'PASSED' if ok else 'FAILED'} in {time.time() - t0:.0f}s")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
