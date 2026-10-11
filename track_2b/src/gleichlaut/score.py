"""Scoring of recorded runs. Per-item metrics and the bootstrap are the frozen research scorer's own functions
(frozen/s2/score2.py: score_one, boot_diff, executed via core.SCORE); the grouping follows frozen/score_fresh.py.

Flags are never read from the records: every output is re-guarded with the frozen stack, and the result must equal the
flag the record carries (otherwise the run is reported as inconsistent)."""
import json, math, os
from collections import Counter
from . import core

S = core.SCORE
DATA = os.path.join(core.ROOT, "data")
LABELS = os.path.join(core.ROOT, "eval", "labels")

# The recorded runs. stack = the frozen guard stack that run used; labels = hand-check files (unflagged + flagged sample).
RUNS = {
    "fresh166": dict(items="items/items_fresh.json", final="runs/70b_fresh166_g3_final.jsonl", stack="g3",
                     labels="fresh166_unflagged.tsv", flagged20="fresh166_flagged20.tsv",
                     what="70B whole-paragraph + guards3 + one re-ask, FRESH 2025 set (guards frozen before outputs existed)"),
    "oos242": dict(items="items/items_oos.json", final="runs/70b_oos242_v2_final.jsonl", stack="v2",
                   labels="oos242_unflagged.tsv", flagged20="oos242_flagged20.tsv",
                   what="70B whole-paragraph + guards v2 + one re-ask, out-of-sample 2026 set (FAILED the pass rule; now the guards3 dev set)"),
    "dev120": dict(items="items/items_dev.json", final="runs/70b_dev120_v2_final.jsonl", stack="v2",
                   labels=["dev120_70b_unflagged.tsv", "dev120_70b_reask.tsv"], flagged20=None,
                   what="70B whole-paragraph + guards v2 + one re-ask, 120 dev items (guards designed on these: in-sample)"),
    "m3_seed1": dict(items="items/items_fresh.json", final="runs/certify_m3-seed1.jsonl", stack="g3", labels=None, flagged20=None,
                     seed=1, what="M3 (PREREG R2): the same frozen 70B pipeline on the fresh 166 again, seed=1"),
    "q8_0_rerun": dict(items="items/items_fresh.json", final="runs/8b_q8_0_fresh166_g3_rerun.jsonl", stack="g3", labels=None,
                       flagged20=None, cache="cache/responses_8b/q8_0", model="gguf:q8_0.gguf",
                       what="R9: the certified 8B GGUF Q8_0 again on the fresh 166 (CPU, GitHub Actions), every call recorded"),
    "q8_0": dict(items="items/items_fresh.json", final="runs/8b_q8_0_fresh166_g3_final.jsonl", stack="g3", labels=None, flagged20=None,
                 what="R1 (M2): the certified 8B GGUF Q8_0 on the fresh 166 (CPU, GitHub Actions; build certificate "
                      "eval/certificates/8b-q8_0-fresh166.json, blind labels scored by m1('q8_0')): the default SL lane"),
    "dev120_8b": dict(items="items/items_dev.json", final="runs/8b_dwq_dev120_s2b.jsonl", stack="g3", recorded_flag=False,
                      labels="dev120_8b_s2b_unflagged.tsv", flagged20=None,
                      what="8B (MLX 4-bit DWQ, local) whole-paragraph + guards3, NO re-ask, 120 dev items"),
}
# The naive approaches on the same 120 dev items (mechanical metrics only; their hand checks are in docs/research/).
NAIVE = {"8B window-only (locked span edit)": ("runs/8b_dwq_dev120_window.jsonl", "2"),
         "70B window-only (locked span edit)": ("runs/70b_dev120_window.jsonl", "2"),
         "8B free translation of the new DE": ("runs/8b_dwq_dev120_free.jsonl", "3")}
PASS_RULE = dict(unflagged_real_max_pct=1.0, unflagged_stale_untranslated_max_pct=2.0, exact_gain_min_pts=5.0, flag_rate_max_pct=70.0)
DOMINANT_FAMILY = "981f07a8"     # the 'Grundversicherung' boilerplate family of the fresh set (results: report it separately)


def load_items(rel): return json.load(open(os.path.join(DATA, rel), encoding="utf-8"))
def load_jsonl(rel): return {json.loads(l)["key"]: json.loads(l) for l in open(os.path.join(DATA, rel), encoding="utf-8")}


def load_labels(name):
    """-> {key: class}. Files differ slightly in layout; class names: equivalent, preexisting, cosmetic, minor, german,
    stale, REAL, garble (unflagged files) and good / bad (flagged samples)."""
    if not name: return {}
    if isinstance(name, list):                       # later files override earlier ones (re-ask relabels)
        out = {}
        for n in name: out.update(load_labels(n))
        return out
    lines = open(os.path.join(LABELS, name), encoding="utf-8").read().splitlines()
    hdr = lines[0].split("\t"); out = {}
    for l in lines[1:]:
        c = l.split("\t")
        if hdr[0] == "arm":
            if c[0] != "2b": continue
            out[c[1]] = c[2]
        else:
            out[c[0]] = c[1]
    return out


def wilson(k, n, z=1.96):
    if n == 0: return (0.0, 0.0)
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n); r = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (max(0.0, 100 * (c - r) / d), min(100.0, 100 * (c + r) / d))


def rows_for(run_id, recheck=True):
    """-> (items by key, rules rows, model rows). Model rows carry the re-computed flag."""
    R = RUNS[run_id]; I = {x["key"]: x for x in load_items(R["items"])}; F = load_jsonl(R["final"])
    lab = load_labels(R["labels"]); P = core.check_only(R["stack"]) if recheck else None
    rows1, rows2, incons = [], [], []
    for k, x in I.items():
        r1, _ = core.gl2.rules(x["de_old"], x["de_new"], x["tgt_old"], x["lang"])
        a = S["score_one"](x, r1, "1"); f = F[k]
        b = S["score_one"](x, f["out"], "1")
        flag = P.check(x, f["out"])["flag"] if recheck else f["guard_flag"]
        if R.get("recorded_flag", True) and flag != f["guard_flag"]: incons.append(k)
        b.update(flagged=flag, reasked=f.get("reasked", False), replaced=bool(f.get("replaced", False)), rule_only=f["rule_only"],
                 seen=x.get("seen_family", True), family=x["cluster"], cls=("exact" if b["exact"] else lab.get(k, "?")),
                 secs=f.get("secs", 0.0))
        a.update(seen=x.get("seen_family", True), family=x["cluster"])
        rows1.append(a); rows2.append(b)
    if incons: raise AssertionError(f"{run_id}: re-guarded flag differs from the recorded flag for {incons[:5]}")
    return I, rows1, rows2


def summarise(A, B, labelled=True):
    n = len(B)
    d = {"n": n, "pairs": len({r["pair"] for r in B}), "families": len({r["family"] for r in B})}
    for fld, sc in (("exact", 100), ("ef1", 100), ("chrf", 1)):
        ma, mb = sc * sum(float(r[fld]) for r in A) / n, sc * sum(float(r[fld]) for r in B) / n
        ci = S["boot_diff"](B, A, fld); ci = (ci[0] / 100, ci[1] / 100) if fld == "chrf" else ci
        d[fld] = dict(rules=round(ma, 1), model=round(mb, 1), delta=round(mb - ma, 1), ci95=[round(ci[0], 1), round(ci[1], 1)])
    d["flagged"] = sum(r["flagged"] for r in B); d["flag_rate"] = round(100 * d["flagged"] / n, 1)
    d["exact_n"] = sum(r["exact"] for r in B); d["rules_exact_n"] = sum(r["exact"] for r in A)
    d["exact_flagged"] = sum(r["exact"] and r["flagged"] for r in B)
    d["reasked"] = sum(r["reasked"] for r in B); d["replaced"] = sum(r["replaced"] for r in B)
    U = [r for r in B if not r["flagged"]]; d["unflagged"] = len(U); d["ready_rate"] = round(100 * len(U) / n, 1)
    d["unflagged_classes"] = dict(sorted(Counter(r["cls"] for r in U).items()))
    if labelled:
        unl = sum(r["cls"] == "?" for r in U)
        d["unflagged_unlabelled"] = unl
        for c in ("REAL", "stale", "german"):
            m = sum(r["cls"] == c for r in U); d[f"unflagged_{c}"] = m; d[f"unflagged_{c}_per100"] = round(100 * m / n, 2)
        bad = d["unflagged_REAL"]; su = d["unflagged_stale"] + d["unflagged_german"]
        d["wilson95_unflagged_real"] = [round(v, 1) for v in wilson(bad, n)]
        sev = bad + su
        d["wilson95_severe_among_ready"] = [round(v, 1) for v in wilson(sev, len(U))]   # per ready draft, what a translator receives
        d["wilson95_unflagged_stale_untranslated"] = [round(v, 1) for v in wilson(su, n)]
        d["pass_rule"] = {
            "unflagged_real": [round(100 * bad / n, 2), 100 * bad / n <= PASS_RULE["unflagged_real_max_pct"]],
            "unflagged_stale_untranslated": [round(100 * su / n, 2), 100 * su / n <= PASS_RULE["unflagged_stale_untranslated_max_pct"]],
            "exact_gain": [d["exact"]["delta"], d["exact"]["delta"] >= PASS_RULE["exact_gain_min_pts"]],
            "flag_rate": [d["flag_rate"], d["flag_rate"] <= PASS_RULE["flag_rate_max_pct"]]}
        d["pass"] = all(v[1] for v in d["pass_rule"].values()) and unl == 0
    return d


def score_run(run_id, recheck=True):
    R = RUNS[run_id]; I, rows1, rows2 = rows_for(run_id, recheck)
    labelled = bool(R["labels"])
    groups = [("all", lambda r: True), ("fr", lambda r: r["lang"] == "fr"), ("it", lambda r: r["lang"] == "it")]
    if any("seen_family" in x for x in I.values()):
        groups[1:1] = [("unseen families", lambda r: not r["seen"]), ("seen families", lambda r: r["seen"])]
    if run_id == "fresh166":
        groups.append(("excluding family " + DOMINANT_FAMILY, lambda r: r["family"] != DOMINANT_FAMILY))
    out = {}
    for g, sel in groups:
        A = [r for r in rows1 if sel(r)]; B = [r for r in rows2 if sel(r)]
        if B: out[g] = summarise(A, B, labelled)
    fl = load_labels(R["flagged20"])
    if fl:
        good = sum(v == "good" for v in fl.values()); n = len(fl)
        out["flagged_sample"] = dict(n=n, good=good, bad=n - good, waste_pct=round(100 * good / n, 1),
                                     wilson95=[round(v, 1) for v in wilson(good, n)])
    return dict(run=run_id, what=R["what"], stack=R["stack"], summary=out,
                rows=[{k: r[k] for k in ("key", "lang", "pair", "family", "exact", "ef1", "chrf", "flagged", "cls", "reasked", "replaced", "rule_only")}
                      for r in rows2])


def score_naive():
    """rules-only vs each naive arm on the dev 120: exact, edit-F1, chrF and the arm's own flag (score2 semantics)."""
    I = load_items(RUNS["dev120"]["items"]); out = {}
    rules = [S["score_one"](x, core.gl2.rules(x["de_old"], x["de_new"], x["tgt_old"], x["lang"])[0], "1") for x in I]
    out["rules only (copy old FR/IT + number substitutions)"] = dict(
        n=len(rules), exact=round(100 * sum(r["exact"] for r in rules) / len(rules), 1),
        ef1=round(100 * sum(r["ef1"] for r in rules) / len(rules), 1), chrf=round(sum(r["chrf"] for r in rules) / len(rules), 1))
    for name, (rel, arm) in NAIVE.items():
        F = load_jsonl(rel)
        B = [S["score_one"](x, F[x["key"]]["out"], arm, F[x["key"]]) for x in I]
        n = len(B)
        out[name] = dict(n=n, exact=round(100 * sum(r["exact"] for r in B) / n, 1), ef1=round(100 * sum(r["ef1"] for r in B) / n, 1),
                         chrf=round(sum(r["chrf"] for r in B) / n, 1), flagged=round(100 * sum(r["flagged"] for r in B) / n, 1),
                         lexicon_flips=sum(bool(r["flip"]) for r in B), unflagged_lexicon_flips=sum(bool(r["flip"]) and not r["flagged"] for r in B))
    return out


def cost(run_id, cache_root=None):
    """Spend and latency of a recorded 70B run, from the recorded response metadata (tokens, USD at the then-price, seconds)."""
    from . import backends
    cache_root = cache_root or os.path.join(DATA, "cache", "responses")
    R = RUNS[run_id]; I = {x["key"]: x for x in load_items(R["items"])}
    seen, calls = set(), []
    def ask(prompt, tag, cap, mt):
        h = backends.payload_key(core.M70, prompt, mt)
        d = json.load(open(os.path.join(cache_root, h[:2], h + ".json"), encoding="utf-8"))
        if h not in seen: seen.add(h); calls.append(d["meta"])
        return backends.strip_think(d["text"]), dict(d["meta"], cached=True)
    P = core.Pipeline(ask, R["stack"])
    for x in I.values(): P.run(x)
    usd = sum(m.get("usd", 0) or 0 for m in calls); secs = sum(m.get("secs", 0) or 0 for m in calls)
    pt = sum(m.get("prompt_tokens", 0) or 0 for m in calls); ct = sum(m.get("completion_tokens", 0) or 0 for m in calls)
    n = len(I)
    return dict(items=n, unique_calls=len(calls), usd=round(usd, 4), usd_per_item=round(usd / n, 5), prompt_tokens=pt,
                completion_tokens=ct, model_secs=round(secs, 1), model_secs_per_item=round(secs / n, 2))


def agreement():
    """Blind second annotation of the fresh-166 hand-check sample (49 unflagged non-exact + 20 flagged): binary
    'needs a fix' agreement and Cohen's kappa against the research labels, and what the second annotator says about the
    drafts the guards passed."""
    U = load_labels("fresh166_unflagged.tsv"); F = load_labels("fresh166_flagged20.tsv")
    lines = open(os.path.join(LABELS, "fresh166_second_annotator.tsv"), encoding="utf-8").read().splitlines()[1:]
    B = {c[0]: dict(fix=c[1], cls=c[2], note=c[3] if len(c) > 3 else "") for c in (l.split("\t") for l in lines)}
    A = {k: ("no" if v in ("equivalent", "preexisting", "exact") else "yes") for k, v in U.items()}
    A.update({k: ("no" if v == "good" else "yes") for k, v in F.items()})
    keys = sorted(A); n = len(keys); agree = sum(A[k] == B[k]["fix"] for k in keys)
    pa, pA, pB = agree / n, sum(A[k] == "yes" for k in keys) / n, sum(B[k]["fix"] == "yes" for k in keys) / n
    pe = pA * pB + (1 - pA) * (1 - pB)
    severe = ("REAL", "stale", "german")
    T = {c[0]: c[1] for c in (l.split("\t") for l in open(os.path.join(LABELS, "fresh166_tiebreak.tsv"), encoding="utf-8").read().splitlines()[1:])}
    final = {k: (A[k] if A[k] == B[k]["fix"] else T[k]) for k in keys}          # majority of three on "needs a fix"
    tie = dict(disagreements=len(T), third_sided_with_second=sum(T[k] == B[k]["fix"] for k in T),
               final_unflagged_needs_fix=sum(final[k] == "yes" for k in U), final_flagged_sample_no_fix=sum(final[k] == "no" for k in F))
    return dict(n=n, agree=agree, tiebreak=tie, kappa=round((pa - pe) / (1 - pe), 3),
                unflagged_n=len(U), unflagged_second_severe=sum(B[k]["cls"] in severe for k in U),
                unflagged_second_classes=dict(sorted(Counter(B[k]["cls"] for k in U).items())),
                unflagged_second_needs_fix=sum(B[k]["fix"] == "yes" for k in U),
                disagreements=[dict(key=k, set="unflagged" if k in U else "flagged20", first=U.get(k) or F.get(k),
                                    second=B[k]["fix"] + " " + B[k]["cls"], note=B[k]["note"]) for k in keys if A[k] != B[k]["fix"]])


def fedlex_shipped():
    """Fedlex lane as shipped (A + code lane + lock + slot guard + G1-G4; DEV: the guard choice was made after seeing these
    outputs) against the pass rule, using the blind annotation of every unflagged non-exact draft."""
    F = json.load(open(os.path.join(core.ROOT, "eval", "results", "fedlex.json"), encoding="utf-8"))
    row = next(v for k, v in F.items() if k.startswith("shipped") or (isinstance(v, dict) and "unflagged_nonexact_keys" in v)) \
        if not any(k.startswith("shipped") for k in F) else F[next(k for k in F if k.startswith("shipped"))]
    lines = open(os.path.join(LABELS, "fedlex_shipped_unflagged.tsv"), encoding="utf-8").read().splitlines()[1:]
    lab = {c[0]: c[2] for c in (l.split("\t") for l in lines)}
    n = 120; c = Counter(lab.values())
    real, su = c.get("REAL", 0), c.get("stale", 0) + c.get("german", 0)
    return dict(n=n, labelled=len(lab), classes=dict(sorted(c.items())), unflagged_real=real, unflagged_stale_untranslated=su,
                unflagged_stale_untranslated_pct=round(100 * su / n, 2), wilson95=[round(v, 1) for v in wilson(su, n)],
                needs_fix=sum(1 for l in lines if l.split("\t")[1] == "yes"),
                passes_stale_untranslated_limit=100 * su / n <= PASS_RULE["unflagged_stale_untranslated_max_pct"])


def economics():
    """Monthly volume (from the backtest), cost per item (recorded tokens of the fresh run) at the then Public AI price and
    at a Swiss-resident provider's published price (docs/sources.md §5.1), at 1x and 10x volume. No translator-time
    figure: that needs the timed review study (M5), which has not been run."""
    lag = json.load(open(os.path.join(DATA, "backtest", "lag.json"), encoding="utf-8"))["vision_figures_check"]
    c = json.load(open(os.path.join(core.ROOT, "eval", "results", "cost_fresh166.json"), encoding="utf-8"))
    per_month_de = lag["distinct_draft_pairs"] / lag["span_months"]; items = 2 * per_month_de
    chf_item = (c["prompt_tokens"] * 0.70 + c["completion_tokens"] * 2.50) / 1e6 / c["items"]      # Infomaniak, CHF / M tokens
    out = dict(de_changes=lag["distinct_draft_pairs"], span_months=lag["span_months"], de_changes_per_month=round(per_month_de, 1),
               fr_it_items_per_month=round(items, 1), usd_per_item_publicai=c["usd_per_item"], chf_per_item_infomaniak=round(chf_item, 4),
               model_secs_per_item=c["model_secs_per_item"])
    for k in (1, 10):
        out[f"x{k}"] = dict(items_per_month=round(k * items), usd_per_month_publicai=round(k * items * c["usd_per_item"], 2),
                            chf_per_month_infomaniak=round(k * items * chf_item, 2),
                            model_hours_per_month_sequential=round(k * items * c["model_secs_per_item"] / 3600, 1))
    return out


def fedlex_compare():
    """PREREG R5: the shipped Fedlex lane with the 8B (recorded MLX DWQ run) and with the 70B (gateway run), same 120 FR/IT
    items, against the pass rule, using a blind annotation of every unflagged non-exact draft of each run."""
    from .fed import lane
    items = {x["key"]: x for x in lane.load(lane.ITEMS) if x["src"] == "fed" and x["lang"] in lane.SCOPE}
    rules = sum(core.lock.code_lane(x["de_old"], x["de_new"], x["tgt_old"], x["lang"])[1] is not None and
                core.lock.norm(core.lock.code_lane(x["de_old"], x["de_new"], x["tgt_old"], x["lang"])[1]) == core.lock.norm(x["tgt_new"])
                for x in items.values())
    F = json.load(open(os.path.join(core.ROOT, "eval", "results", "fedlex.json"), encoding="utf-8"))
    s8 = F[next(k for k in F if k.startswith("shipped"))]
    R70 = [json.loads(l) for l in open(os.path.join(DATA, "runs", "70b_fedlex_shipped.jsonl"), encoding="utf-8")]
    def side(labels_file, n, exact, flagged, build=None):
        lines = open(os.path.join(LABELS, labels_file), encoding="utf-8").read().splitlines()[1:]
        if build:                                    # fedlex_gguf_unflagged.tsv: build, key, A/B/T labels, final_fix, final
            lines = [l for l in lines if l.split("\t")[0] == build]; c = Counter(l.split("\t")[9] for l in lines)
        else: c = Counter(l.split("\t")[2] for l in lines)
        real, su = c.get("REAL", 0), c.get("stale", 0) + c.get("german", 0)
        return dict(n=n, exact=exact, exact_pct=round(100 * exact / n, 1), flagged=flagged, flag_rate=round(100 * flagged / n, 1),
                    ready=n - flagged, ready_pct=round(100 * (n - flagged) / n, 1), ready_nonexact_labelled=len(lines), classes=dict(sorted(c.items())),
                    unflagged_real=real, unflagged_real_pct=round(100 * real / n, 2),
                    unflagged_stale_untranslated=su, unflagged_stale_untranslated_pct=round(100 * su / n, 2),
                    passes=(100 * real / n <= PASS_RULE["unflagged_real_max_pct"] and 100 * su / n <= PASS_RULE["unflagged_stale_untranslated_max_pct"]
                            and 100 * flagged / n <= PASS_RULE["flag_rate_max_pct"] and 100 * (exact - rules) / n >= PASS_RULE["exact_gain_min_pts"]))
    n = len(items)
    # every arm under one protocol (two blind annotators + a third on disagreements): the R5 arms were relabelled after a
    # juror noted that their first labels came from one annotator; the first labels stay reported as first_annotation
    a1 = side("fedlex_shipped_unflagged.tsv", n, s8["all"]["exact"], s8["all"]["flagged"])
    b1 = side("fedlex70b_shipped_unflagged.tsv", n, sum(bool(r.get("exact")) for r in R70), sum(r["flagged"] for r in R70))
    a = side("fedlex_r5_relabel_unflagged.tsv", n, s8["all"]["exact"], s8["all"]["flagged"], "8b_mlx_dwq")
    b = side("fedlex_r5_relabel_unflagged.tsv", n, sum(bool(r.get("exact")) for r in R70), sum(r["flagged"] for r in R70), "70b")
    a["first_annotation"] = {k: a1[k] for k in ("classes", "unflagged_real", "unflagged_stale_untranslated")}
    b["first_annotation"] = {k: b1[k] for k in ("classes", "unflagged_real", "unflagged_stale_untranslated")}
    assert len(R70) == n
    out = {"n": n, "rules_exact": rules, "rules_exact_pct": round(100 * rules / n, 1), "8b_mlx_dwq": a, "70b": b,
           "decision": "Fedlex stays 8B; every draft goes to review" if not b["passes"] else "70B passes R0"}
    for build in ("q4_k_m", "q8_0"):                 # PREREG R6: the shipped GGUF builds on the same items (CPU runners)
        rel = os.path.join(DATA, "runs", f"8b_{build}_fedlex_shipped.jsonl")
        if not os.path.exists(rel): continue
        R = [json.loads(l) for l in open(rel, encoding="utf-8")]; assert len(R) == n
        g = side("fedlex_gguf_unflagged.tsv", n, sum(bool(r.get("exact")) for r in R), sum(bool(r["flagged"]) for r in R), build)
        g["exact_vs_mlx_pts"] = round(g["exact_pct"] - a["exact_pct"], 1)
        g["cpu_secs_per_item"] = round(sum(r.get("wall_secs", 0) for r in R) / n, 1)
        out[f"8b_gguf_{build}"] = g
    if any(k.startswith("8b_gguf_") for k in out):
        out["decision_r6"] = ("statutes run the shipped 8B GGUF; every draft goes to review" if all(
            out[k]["exact_vs_mlx_pts"] >= -10 for k in out if k.startswith("8b_gguf_")) else
            "a GGUF build is > 10 points below the MLX build: statute claims name the MLX build")
    return out


def m3():
    """PREREG R2: run-to-run stability of the 70B lane. The same frozen pipeline on the fresh 166 with seed=1 (a distinct
    request, so the provider's response cache cannot answer) vs the original run."""
    p = os.path.join(DATA, "runs", "certify_m3-seed1.jsonl")
    if not os.path.exists(p): return None
    I = {x["key"]: x for x in load_items("items/items_fresh.json")}
    A = load_jsonl(RUNS["fresh166"]["final"]); B = load_jsonl("runs/certify_m3-seed1.jsonl")
    keys = [k for k in I if k in B]; n = len(keys)
    same = sum(A[k]["out"] == B[k]["out"] for k in keys)
    fa = [A[k]["guard_flag"] for k in keys]; fb = [B[k]["guard_flag"] for k in keys]
    agree = sum(x == y for x, y in zip(fa, fb)); pA, pB = sum(fa) / n, sum(fb) / n
    pe = pA * pB + (1 - pA) * (1 - pB); kappa = ((agree / n) - pe) / (1 - pe) if pe < 1 else 1.0
    cert = json.load(open(os.path.join(core.ROOT, "eval", "certificates", "m3-seed1.json"), encoding="utf-8"))
    calls = [json.loads(l) for l in open(os.path.join(core.ROOT, "eval", "certificates", "m3-seed1.calls.jsonl"), encoding="utf-8")]
    new = {c[0]: c[2] for c in (l.split("\t") for l in open(os.path.join(LABELS, "m3_new_ready.tsv"), encoding="utf-8").read().splitlines()[1:])}
    m = cert["metrics"]; nc = Counter(new.values())
    real = m["unflagged_REAL"] + nc.get("REAL", 0); su = m["unflagged_stale"] + m["unflagged_german"] + nc.get("stale", 0) + nc.get("german", 0)
    after = dict(new_ready_labelled=len(new), new_classes=dict(sorted(nc.items())), unflagged_real=real, unflagged_stale_untranslated=su,
                 unflagged_stale_untranslated_pct=round(100 * su / n, 1),
                 passes=(100 * real / n <= PASS_RULE["unflagged_real_max_pct"] and 100 * su / n <= PASS_RULE["unflagged_stale_untranslated_max_pct"]
                         and m["pass_rule"]["exact_gain"][1] and m["pass_rule"]["flag_rate"][1]))
    return dict(n=n, identical_outputs=same, identical_pct=round(100 * same / n, 1), changed_pct=round(100 * (n - same) / n, 1), flag_agreement=agree, flag_kappa=round(kappa, 3),
                after_labels=after,
                flag_rate_original=round(100 * pA, 1), flag_rate_rerun=round(100 * pB, 1),
                rerun=cert["metrics"], status=cert["status"], needs_review=len(cert["needs_review"]),
                calls=len(calls), served=sorted({c["model_served"] for c in calls}),
                serving_backends=dict(Counter((c.get("backend") or "?").split("-")[0] for c in calls)))


def post_edit(final=None):
    """Post-editing effort proxy (no human time needed): token edits (insertions + deletions, score2.edits) a translator
    must make to reach the text BAG published, starting from (a) the Gleichlaut draft or (b) the rules-only start (old
    French/Italian with code-substituted numbers, i.e. what translation memory plus find/replace gives today), on the
    fresh 166. Reported for all items, ready and flagged drafts."""
    I = {x["key"]: x for x in load_items("items/items_fresh.json")}; F = load_jsonl(final or RUNS["fresh166"]["final"])
    norm = core.lock.norm; out = {}
    rows = []
    for k, x in I.items():
        gold = norm(x["tgt_new"]); r1 = norm(core.gl2.rules(x["de_old"], x["de_new"], x["tgt_old"], x["lang"])[0])
        d = norm(F[k]["out"])
        e_rules = sum(S["edits"](r1, gold).values()); e_draft = sum(S["edits"](d, gold).values())
        e_need = sum(S["edits"](norm(x["tgt_old"]), gold).values())
        rows.append(dict(key=k, pair=x["pair"], flagged=F[k]["guard_flag"], rules=e_rules, draft=e_draft, needed=e_need))
    for g, sel in (("all", lambda r: True), ("ready", lambda r: not r["flagged"]), ("flagged", lambda r: r["flagged"])):
        R = [r for r in rows if sel(r)]; n = len(R)
        sr, sd = sum(r["rules"] for r in R), sum(r["draft"] for r in R)
        out[g] = dict(n=n, token_edits_from_rules=sr, token_edits_from_draft=sd,
                      edits_saved_pct=round(100 * (sr - sd) / sr, 1) if sr else 0.0,
                      items_draft_fewer=sum(r["draft"] < r["rules"] for r in R), items_draft_more=sum(r["draft"] > r["rules"] for r in R),
                      items_draft_zero=sum(r["draft"] == 0 for r in R))
        import random
        by = {}
        for r in R: by.setdefault(r["pair"], []).append(r)
        ks = sorted(by); rng = random.Random(7); bs = []
        for _ in range(4000):
            smp = [r for k in (rng.choice(ks) for _ in ks) for r in by[k]]
            a, b = sum(r["rules"] for r in smp), sum(r["draft"] for r in smp)
            if a: bs.append(100 * (a - b) / a)
        bs.sort(); out[g]["edits_saved_ci95"] = [round(bs[int(0.025 * len(bs))], 1), round(bs[int(0.975 * len(bs))], 1)]
    return out


def shadow_month(run="20260901-20261001", r0=False):
    """A shadow month on the public feed (items mined by the shadow workflow from BAG's feeds of the two dates), drafted by
    every model whose run folder exists (q4_k_m, q8_0: shadow workflow, CPU, --network none; 70b: development gateway),
    same items and routing. Labels: every ready draft that differs from BAG's published text, pooled, blind (R1 protocol).
    PREREG R7: the first month (20260901-20261001), descriptive. PREREG R10 (r0=True): the second month, prospective,
    with the four R0 criteria per model and beside them the same on the items not in any earlier item set ("unseen")."""
    import re
    D = os.path.join(DATA, "shadow", run); I = {x["key"]: x for x in json.load(open(os.path.join(D, "items.json"), encoding="utf-8"))}
    lines = open(os.path.join(LABELS, f"shadow_{run.replace('-', '_')}_ready.tsv"), encoding="utf-8").read().splitlines()
    hdr = lines[0].split("\t"); lab = [dict(zip(hdr, l.split("\t"))) for l in lines[1:]]
    norm = core.lock.norm; out = {}; recs = {}
    models = [m for m in ("q4_k_m", "q8_0", "70b") if os.path.exists(os.path.join(D, m, "records.jsonl"))]
    cmp_ = [k for k, x in I.items() if x.get("tgt_new")]
    for m in models:
        R = recs[m] = {json.loads(l)["key"]: json.loads(l) for l in open(os.path.join(D, m, "records.jsonl"), encoding="utf-8")}
        assert set(R) == set(I), m
        dr = [k for k in cmp_ if R[k]["status"] != "human"]
        rd = [k for k in dr if R[k]["status"] == "ready"]
        L = Counter(r["final"] for r in lab if r["model"] == m)
        S = json.load(open(os.path.join(D, m, "summary.json"), encoding="utf-8"))
        out[m] = dict(items=len(I), human=sum(R[k]["status"] == "human" for k in I), compared=len(dr),
                      exact=sum(norm(R[k]["out"]) == norm(I[k]["tgt_new"]) for k in dr), ready=len(rd),
                      flagged=sum(R[k]["status"] == "flagged" for k in dr),
                      ready_exact=sum(norm(R[k]["out"]) == norm(I[k]["tgt_new"]) for k in rd), ready_classes=dict(sorted(L.items())),
                      ready_errors=sum(L.get(c, 0) for c in ("REAL", "stale", "german")),
                      calls=S["calls"]["n"], served_by=S["calls"]["models_served"],
                      gate=(S.get("gate") or {}).get("certificate"))
        out[m]["flag_rate"] = round(100 * out[m]["flagged"] / len(dr), 1); out[m]["exact_rate"] = round(100 * out[m]["exact"] / len(dr), 1)
    base = recs[models[0]]
    dr = [k for k in cmp_ if base[k]["status"] != "human"]
    rule_ok = {k: norm(core.gl2.rules(I[k]["de_old"], I[k]["de_new"], I[k]["tgt_old"], I[k]["lang"])[0]) == norm(I[k]["tgt_new"]) for k in dr}
    rules = sum(rule_ok.values())
    new = "Indikationscode dieser Limitierung"
    boiler = [k for k in dr if new in I[k]["de_new"] and new not in I[k]["de_old"]]
    fr = Counter()
    for k in cmp_:
        x = I[k]
        if x["lang"] == "fr" and new in x["de_new"]:
            m_ = re.search(r"code d.indication de cette limitation[^.]*?transmis à l.(assureur-maladie|assurance maladie)", x["tgt_new"])
            if m_: fr[m_.group(1)] += 1
    mining = next(json.load(open(os.path.join(D, m, "summary.json"), encoding="utf-8")).get("mining") for m in models
                  if json.load(open(os.path.join(D, m, "summary.json"), encoding="utf-8")).get("mining"))
    res = dict(run=run, mining=mining, rules_exact=rules, compared=len(dr), boilerplate_items=len(boiler),
               bag_fr_rendering_of_new_sentence=dict(fr),
               labelled=len(lab), annotators_agree=sum((r["A_fix"], r["A_class"]) == (r["B_fix"], r["B_class"]) for r in lab),
               ready_total=sum(v["ready"] for v in out.values()), ready_errors_total=sum(v["ready_errors"] for v in out.values()),
               **out)
    if not r0: return res
    # PREREG R10: the four R0 criteria per model, n = drafts compared with BAG's text (status != human)
    sig = lambda x: (x["lang"], x["de_old"].strip(), x["de_new"].strip())
    seen_sigs = set()
    for f in ("items_dev", "items_oos", "items_fresh"): seen_sigs |= {sig(x) for x in load_items(f"items/{f}.json")}
    seen = {k for k in I if sig(I[k]) in seen_sigs}
    labk = {(r["model"], r["key"]): r["final"] for r in lab}
    def crit(m, keys):
        R = recs[m]; d = [k for k in keys if k in I and I[k].get("tgt_new") and R[k]["status"] != "human"]; n = len(d)
        if not n: return dict(n=0)
        ex = sum(norm(R[k]["out"]) == norm(I[k]["tgt_new"]) for k in d); ru = sum(rule_ok[k] for k in d)
        rd = [k for k in d if R[k]["status"] == "ready"]
        ne = [k for k in rd if norm(R[k]["out"]) != norm(I[k]["tgt_new"])]
        cls = Counter(labk.get((m, k), "?") for k in ne)
        real = cls.get("REAL", 0); su = cls.get("stale", 0) + cls.get("german", 0); fl = sum(R[k]["status"] == "flagged" for k in d)
        allk = [k for k in keys if k in I and I[k].get("tgt_new")]
        hum = sum(R[k]["status"] == "human" for k in allk)
        c = dict(unflagged_real=[round(100 * real / n, 2), 100 * real / n <= PASS_RULE["unflagged_real_max_pct"]],
                 unflagged_stale_untranslated=[round(100 * su / n, 2), 100 * su / n <= PASS_RULE["unflagged_stale_untranslated_max_pct"]],
                 exact_gain=[round(100 * (ex - ru) / n, 1), 100 * (ex - ru) / n >= PASS_RULE["exact_gain_min_pts"]],
                 flag_rate=[round(100 * fl / n, 1), 100 * fl / n <= PASS_RULE["flag_rate_max_pct"]])
        return dict(n=n, exact=ex, rules_exact=ru, ready=len(rd), ready_not_exact=len(ne), unlabelled=cls.get("?", 0),
                    flagged=fl, unflagged_real_n=real, unflagged_stale_german_n=su,
                    wilson95_unflagged_real=[round(v, 1) for v in wilson(real, n)],
                    wilson95_unflagged_stale_german=[round(v, 1) for v in wilson(su, n)],
                    criteria=c, meets_r0=all(v[1] for v in c.values()) and not cls.get("?", 0),
                    review_share_incl_routed=[fl + hum, len(allk), round(100 * (fl + hum) / len(allk), 1)])
    res["seen_items"] = len(seen); res["seen_compared"] = sum(k in seen for k in dr)
    res["r0"] = {m: dict(month=crit(m, list(I)), unseen=crit(m, [k for k in I if k not in seen])) for m in models}
    res["rules_exact_rate"] = round(100 * rules / len(dr), 1)
    L = lab; n = len(L)
    if n:
        ag = sum(r["A_fix"] == r["B_fix"] for r in L); pA = sum(r["A_fix"] == "yes" for r in L) / n; pB = sum(r["B_fix"] == "yes" for r in L) / n
        pe = pA * pB + (1 - pA) * (1 - pB)
        res["annotators"] = dict(n=n, needs_fix_agree=ag, needs_fix_kappa=round((ag / n - pe) / (1 - pe), 3) if pe < 1 else None,
                                 class_agree=sum(r["A_class"] == r["B_class"] for r in L), tiebreak=sum(bool(r.get("T_class")) for r in L))
    return res


def r12_terms():
    """PREREG R12: the v3-terms variant (BAG's house wording, mined from each month's OLD snapshot, as one block in the
    drafting prompt; gleichlaut.v3terms) beside the frozen pipeline on both live months, per model (Q8_0, 70B). The four R0
    criteria on the drafts compared with BAG's text (status != human), scored on the frozen guards' verdict (guard_status;
    the variant's records are all marked for review because it is not certified, and for the frozen runs status and
    guard_status agree). Frozen: the R7 / R10 records and labels. v3-terms: data/shadow/<month>/v3_terms_<model>/ and
    eval/labels/r12_terms_ready.tsv (blind, R1 protocol)."""
    norm = core.lock.norm
    def tsv(p):
        if not os.path.exists(p): return []
        L = open(p, encoding="utf-8").read().splitlines(); h = L[0].split("\t")
        return [dict(zip(h, l.split("\t"))) for l in L[1:] if l.strip()]
    lab12 = tsv(os.path.join(LABELS, "r12_terms_ready.tsv"))
    B = json.load(open(os.path.join(core.ROOT, "eval", "prereg", "r12_blocks.json"), encoding="utf-8"))["months"]
    st = lambda r: r["status"] if r["status"] == "human" else r.get("guard_status", r["status"])
    new = "Indikationscode dieser Limitierung"
    raw = {a: {r["id"]: r for r in tsv(os.path.join(LABELS, f"r12_terms_ready_{a}.tsv"))} for a in "ABT"}
    res = dict(rule="PREREG R12", pass_rule=PASS_RULE, months={}, labelled=len(raw["A"]),
               annotators_agree=sum((r["needs_fix"], r["class"]) == (raw["B"][i]["needs_fix"], raw["B"][i]["class"]) for i, r in raw["A"].items()),
               tiebreak=len(raw["T"]), final_classes=dict(sorted(Counter(r["final"] for r in lab12).items())))
    for run in ("20260801-20260901", "20260901-20261001"):
        D = os.path.join(DATA, "shadow", run)
        I = {x["key"]: x for x in json.load(open(os.path.join(D, "items.json"), encoding="utf-8"))}
        labf = {(r["model"], r["key"]): r["final"] for r in tsv(os.path.join(LABELS, f"shadow_{run.replace('-', '_')}_ready.tsv"))}
        labv = {(r["model"], r["key"]): r["final"] for r in lab12 if r["month"] == run}
        cmp_ = [k for k, x in I.items() if x.get("tgt_new")]
        rule_ok = {k: norm(core.gl2.rules(I[k]["de_old"], I[k]["de_new"], I[k]["tgt_old"], I[k]["lang"])[0]) == norm(I[k]["tgt_new"]) for k in cmp_}
        blk = B[run]["items"]
        mo = dict(terms_date=B[run]["terms_date"], drafted=B[run]["drafted"], model_calls=B[run]["model_calls"],
                  prompts_changed=B[run]["prompt_changed"])
        for m in ("q8_0", "70b"):
            arms = {}
            for arm, folder, lab in (("frozen", m, labf), ("v3_terms", f"v3_terms_{m}", labv)):
                p = os.path.join(D, folder, "records.jsonl")
                if not os.path.exists(p): continue
                R = {json.loads(l)["key"]: json.loads(l) for l in open(p, encoding="utf-8")}
                assert set(R) == set(I), (run, folder)
                if arm == "frozen": assert all(r["status"] == r.get("guard_status", r["status"]) for r in R.values() if r["status"] != "human")
                d = [k for k in cmp_ if st(R[k]) != "human"]; n = len(d)
                ex = [k for k in d if norm(R[k]["out"]) == norm(I[k]["tgt_new"])]; ru = sum(rule_ok[k] for k in d)
                rd = [k for k in d if st(R[k]) == "ready"]; ne = [k for k in rd if k not in ex]
                cls = Counter(lab.get((m, k), "?") for k in ne)
                real = cls.get("REAL", 0); su = cls.get("stale", 0) + cls.get("german", 0); fl = sum(st(R[k]) == "flagged" for k in d)
                boil = [k for k in d if new in I[k]["de_new"] and new not in I[k]["de_old"]]
                S = json.load(open(os.path.join(D, folder, "summary.json"), encoding="utf-8"))
                sent = rex = None
                if arm == "v3_terms":                    # the variant's first prompt of every model-call item is in the call log
                    from . import cli, backends, v3terms
                    calls = [json.loads(l) for l in open(os.path.join(D, folder, "calls.jsonl"), encoding="utf-8")]
                    keys, model = {c_["key"] for c_ in calls}, calls[0]["model"]
                    P = v3terms.TermsPipeline(cli._capture, B[run]["terms_date"]); hit = tot = 0
                    for k in I:
                        if st(R[k]) == "human": continue
                        try: P.draft(I[k]); continue
                        except cli._Captured as e: tot += 1; hit += backends.payload_key(model, e.prompt, e.max_tokens, 0.0) in keys
                    sent = [hit, tot]
                    rp = os.path.join(D, folder, "responses")
                    if os.path.isdir(rp):                # 70B: re-execute the variant end-to-end from its own recorded responses
                        Pc = v3terms.TermsPipeline(backends.Cache(rp, model=model), B[run]["terms_date"])
                        dk = [k for k in I if st(R[k]) != "human"]
                        reexec = sum(all(Pc.run(I[k]).get(f) == R[k].get(f) for f in ("out", "guard_flag", "reasked", "replaced", "retried"))
                                     for k in dk)
                        rex = [reexec, len(dk)]
                c = dict(unflagged_real=[round(100 * real / n, 2), 100 * real / n <= PASS_RULE["unflagged_real_max_pct"]],
                         unflagged_stale_untranslated=[round(100 * su / n, 2), 100 * su / n <= PASS_RULE["unflagged_stale_untranslated_max_pct"]],
                         exact_gain=[round(100 * (len(ex) - ru) / n, 1), 100 * (len(ex) - ru) / n >= PASS_RULE["exact_gain_min_pts"]],
                         flag_rate=[round(100 * fl / n, 1), 100 * fl / n <= PASS_RULE["flag_rate_max_pct"]])
                arms[arm] = dict(n=n, exact=len(ex), rules_exact=ru, ready=len(rd), ready_exact=len(rd) - len(ne), ready_not_exact=len(ne),
                                 ready_classes=dict(sorted(cls.items())), unlabelled=cls.get("?", 0), flagged=fl,
                                 unflagged_real_n=real, unflagged_stale_german_n=su,
                                 wilson95_unflagged_stale_german=[round(v, 1) for v in wilson(su, n)],
                                 new_sentence_items=len(boil), new_sentence_exact=sum(k in ex for k in boil),
                                 criteria=c, meets_r0=all(v[1] for v in c.values()) and not cls.get("?", 0),
                                 calls=S["calls"]["n"], served_by=S["calls"]["models_served"], first_prompts_in_call_log=sent, reexecuted_from_responses=rex,
                                 gate=(S.get("gate") or {}).get("certificate"), _R=R, _ex=set(ex))
            if "frozen" in arms and "v3_terms" in arms:
                F, V = arms["frozen"]["_R"], arms["v3_terms"]["_R"]
                d = [k for k in cmp_ if st(F[k]) != "human"]
                same = [k for k in d if blk.get(k, {}).get("model_call") and blk[k]["prompt_sha256_frozen"] == blk[k]["prompt_sha256_v3"]]
                arms["paired"] = dict(prompt_unchanged=len(same), prompt_unchanged_same_output=sum(F[k]["out"] == V[k]["out"] for k in same),
                                      prompt_changed=sum(blk.get(k, {}).get("prompt_sha256_frozen") != blk.get(k, {}).get("prompt_sha256_v3") for k in d),
                                      exact_gained=sorted(arms["v3_terms"]["_ex"] - arms["frozen"]["_ex"]),
                                      exact_lost=sorted(arms["frozen"]["_ex"] - arms["v3_terms"]["_ex"]),
                                      flag_to_ready=sum(st(F[k]) == "flagged" and st(V[k]) == "ready" for k in d),
                                      ready_to_flag=sum(st(F[k]) == "ready" and st(V[k]) == "flagged" for k in d))
            for a in ("frozen", "v3_terms"):
                if a in arms: arms[a].pop("_R"); arms[a].pop("_ex")
            mo[m] = arms
        res["months"][run] = mo
    res["candidate"] = sorted(f"{run} {m}" for run, mo in res["months"].items() for m in ("q8_0", "70b")
                              if mo[m].get("v3_terms", {}).get("meets_r0") and not mo[m].get("frozen", {}).get("meets_r0", True))
    return res


def audit_recall():
    """Audit recall on planted divergences (tools/audit_inject.py -> eval/results/audit_injection.json; it needs the 6 Oct
    snapshot, so replay reads its committed output): per fault type, detected / n, recall and Wilson 95% in percent."""
    d = json.load(open(os.path.join(core.ROOT, "eval", "results", "audit_injection.json"), encoding="utf-8"))
    pct = lambda v: round(100 * v, 1)
    out = dict(injections=d["summary"]["injections"], detected=d["summary"]["detected"], recall_pct=pct(d["summary"]["recall"]),
               wilson95_pct=[pct(v) for v in d["summary"]["wilson95"]], seed=d["seed"])
    out["types"] = {k: dict(n=v["n"], detected=v["detected"], recall_pct=pct(v["recall"]), wilson95_pct=[pct(x) for x in v["wilson95"]])
                    for k, v in d["types"].items()}
    p2 = os.path.join(core.ROOT, "eval", "results", "audit_injection_v2.json")     # v2: sites not chosen by the detector's rule
    if os.path.exists(p2):
        d2 = json.load(open(p2, encoding="utf-8"))
        out["v2"] = {k: dict(n=v["n"], detected=v["detected"], recall_pct=pct(v["recall"]), wilson95_pct=[pct(x) for x in v["wilson95"]])
                     for k, v in d2["types"].items()}
    return out


def audit_r15():
    """PREREG R15: audit round 5 (operator / negation / number_word). Held planted recall before and after
    (eval/results/audit_injection_r15_held.json, tools/audit_inject.py --protocol r15 --half held), the dev design run
    beside it (labelled dev), the new findings on the 6 Oct 2026 register (data/audit summary 'round5'), their precision
    by two blind annotators + a third (eval/labels/audit_r15_20261006.tsv: final real/minor/not), and the pass rule per
    kind as pre-registered."""
    from . import audit as A
    R = os.path.join(core.ROOT, "eval", "results")
    pct = lambda v: None if v is None else round(100 * v, 1)
    def rec(p):
        d = json.load(open(p, encoding="utf-8"))
        return {t: dict(n=v["n"], before=v["detected_before"], after=v["detected_after"], before_pct=pct(v["recall_before"]),
                        after_pct=pct(v["recall_after"]), wilson95_after_pct=[pct(x) for x in v["wilson95_after"]],
                        by_lang={L: dict(n=b["n"], before=b["before"], after=b["after"]) for L, b in v["by_lang"].items()})
                for t, v in d["types"].items()}, d
    held, H = rec(os.path.join(R, "audit_injection_r15_held.json"))
    dp = os.path.join(R, "audit_injection_r15_dev.json")
    dev = rec(dp)[0] if os.path.exists(dp) else None
    S = json.load(open(os.path.join(DATA, "audit", "audit_20261006_summary.json"), encoding="utf-8"))["round5"]
    lab = []
    lp = os.path.join(LABELS, "audit_r15_20261006.tsv")
    if os.path.exists(lp):
        rows = [l.split("\t") for l in open(lp, encoding="utf-8").read().splitlines()]
        hd = rows[0]; lab = [dict(zip(hd, r)) for r in rows[1:]]
    prec = {}
    for k in A.KINDS_R5:
        L = [r for r in lab if r["kind"] == k]; y = [r for r in L if r["final"] in ("real", "minor")]; st = [r for r in L if r["final"] == "real"]
        Lh = [r for r in L if r["half"] == "held"]; yh = [r for r in Lh if r["final"] in ("real", "minor")]
        prec[k] = dict(findings=S["by_kind"][k], labelled=len(L), real_or_minor=len(y), real=len(st),
                       precision_pct=round(100 * len(y) / len(L), 1) if L else None,
                       wilson95_pct=[round(v, 1) for v in wilson(len(y), len(L))] if L else None,
                       strict_pct=round(100 * len(st) / len(L), 1) if L else None,
                       held_labelled=len(Lh), held_real_or_minor=len(yh))
    agree = [r for r in lab if (r["A"] in ("real", "minor")) == (r["B"] in ("real", "minor"))]
    po = len(agree) / len(lab) if lab else None
    pa = sum(r["A"] in ("real", "minor") for r in lab) / len(lab) if lab else 0; pb = sum(r["B"] in ("real", "minor") for r in lab) / len(lab) if lab else 0
    pe = pa * pb + (1 - pa) * (1 - pb); kappa = round((po - pe) / (1 - pe), 3) if lab and pe < 1 else None
    rp = lambda t: held[t]["after"] / held[t]["n"] if held[t]["n"] else 0
    pp = lambda k: prec[k]["precision_pct"] is None or prec[k]["precision_pct"] >= 50
    crit = dict(operator=dict(recall=dict(operator=rp("operator") >= 0.6), precision=pp("operator")),
                negation=dict(recall=dict(negation_drop=rp("negation_drop") >= 0.5, negation_add=rp("negation_add") >= 0.5), precision=pp("negation")),
                number_word=dict(recall=dict(number_word=rp("number_word") >= 0.6), precision=pp("number_word")))
    dec = {k: dict(pass_=all(v["recall"].values()) and v["precision"], **v) for k, v in crit.items()}
    dec = {k: dict(**{x: y for x, y in v.items() if x != "pass_"}, **{"pass": v["pass_"], "on": A.R5_ON[k]}) for k, v in dec.items()}
    return dict(prereg="R15", rules_sha256=S["rules_sha256"], rules_logic_sha256=S["rules_logic_sha256"], seed=H["seed"], recall=held, recall_dev=dev,
                register=dict(findings=S["findings"], by_kind=S["by_kind"], by_kind_half=S["by_kind_half"], limitations=S["limitations"],
                              real_or_minor=sum(v["real_or_minor"] for v in prec.values()), real=sum(v["real"] for v in prec.values())),
                precision=prec, labels=dict(records=len(lab), agreement=len(agree), kappa=kappa,
                                            tie_break=sum(1 for r in lab if r.get("T"))),
                decision=dec, verification=dict((k, v) for k, v in H["verification"].items() if k != "copies_list"))


def audit_grouping():
    """How the register groups the audit for decision (ui.audit_view.issues): findings naming the same difference on the
    same text are one issue. Counts the number/unit/language/editorial findings, the terminology notices and the issues."""
    from .ui import audit_view
    A = audit_view.data(hist=None); R = A["rows"]
    return dict(findings=sum(r["kind"] != "terminology" for r in R), terminology=sum(r["kind"] == "terminology" for r in R),
                rows=len(R), issues=len(A["issues"]), issues_terminology=sum(all(R[i]["kind"] == "terminology" for i in I["rows"]) for I in A["issues"]),
                issues_equivalent=sum(1 for I in A["issues"] if I["eq"]))


def audit_reconciliation(res):
    """One table from the counts that are spread over three results: findings + terminology notices -> issues (this
    grouping), how many the blind annotators confirmed (audit_relabel, PREREG R14: register and terminology sets) and,
    apart, the experimental round-5 checks (audit_r15). Written into audit_grouping.json under 'reconciliation'."""
    g, S, X = res["audit_grouping"], res["audit_relabel"]["sets"], res["audit_r15"]["register"]
    def part(a, n):
        a = {k: a.get(k, 0) for k in ("real", "minor", "not")}
        assert sum(a.values()) == n, (a, n)
        return dict(n=n, confirmed=a["real"] + a["minor"], **a)
    reg, term = part(S["register"]["answers"], g["findings"]), part(S["terminology"]["answers"], g["terminology"])
    tot = {k: reg[k] + term[k] for k in reg}
    assert tot["n"] == g["rows"]
    return dict(rows=g["rows"], issues=g["issues"], issues_equivalent=g["issues_equivalent"], register=reg, terminology=term, all=tot,
                experimental=dict(n=X["findings"], confirmed=X["real_or_minor"], real=X["real"], minor=X["real_or_minor"] - X["real"],
                                  **{"not": X["findings"] - X["real_or_minor"]}))


def value():
    """What the drafting saves at today's volume, in the unit we measured: word-level (token) edits a translator would
    still make to reach BAG's published text, per FR/IT text and per month (economics: FR/IT items per month from the
    backtest), for the rules-only start, the default 8B Q8_0 and the 70B. Time per edit is not measured (a timed pilot
    turns this into hours)."""
    E = json.load(open(os.path.join(core.ROOT, "eval", "results", "economics.json"), encoding="utf-8"))
    S2 = json.load(open(os.path.join(core.ROOT, "eval", "results", "size_compare.json"), encoding="utf-8"))["q8_0"]
    n, per_month = S2["n"], E["fr_it_items_per_month"]
    per_item = lambda e: e / n
    out = dict(items_per_month=per_month, n=n,
               edits_per_text_rules=round(per_item(S2["edits_rules"]), 1), edits_per_text_8b=round(per_item(S2["edits_8b"]), 1),
               edits_per_text_70b=round(per_item(S2["edits_70b"]), 1))
    out["saved_per_month_8b"] = int(round((S2["edits_rules"] - S2["edits_8b"]) / n * per_month, -1))
    out["saved_per_month_70b"] = int(round((S2["edits_rules"] - S2["edits_70b"]) / n * per_month, -1))
    out["edits_per_month_rules"] = int(round(S2["edits_rules"] / n * per_month, -1))
    return out


def size_compare(builds=("q4_k_m", "q8_0")):
    """Model size, paired: the 70B (fresh 166) against each 8B GGUF build on the same items. Paired cluster bootstrap over
    German changes (4000 resamples, seed 7) of the difference in token edits saved against the rules-only start, and the
    frozen scorer's paired bootstrap of the exact-match difference. Same pipeline, guards and items in every arm; the
    arms differ in model size and in serving (70B: Public AI API in bf16/fp8 across two backends, see
    docs/research/model-identity-and-quantisation.md; 8B: GGUF on CPU with the digit mask)."""
    import random
    I = {x["key"]: x for x in load_items("items/items_fresh.json")}; norm = core.lock.norm
    F70 = load_jsonl(RUNS["fresh166"]["final"]); out = {}
    for b in builds:
        rel = f"runs/8b_{b}_fresh166_g3_final.jsonl"
        if not os.path.exists(os.path.join(DATA, rel)): continue
        F8 = load_jsonl(rel); rows, A, B = [], [], []
        for k, x in I.items():
            gold = norm(x["tgt_new"]); r1 = norm(core.gl2.rules(x["de_old"], x["de_new"], x["tgt_old"], x["lang"])[0])
            e = lambda t: sum(S["edits"](norm(t), gold).values())
            rows.append(dict(pair=x["pair"], rules=sum(S["edits"](r1, gold).values()), m70=e(F70[k]["out"]), m8=e(F8[k]["out"])))
            A.append(S["score_one"](x, F8[k]["out"], "1")); B.append(S["score_one"](x, F70[k]["out"], "1"))
        by = {}
        for r in rows: by.setdefault(r["pair"], []).append(r)
        ks = sorted(by); rng = random.Random(7); bs = []
        for _ in range(4000):
            smp = [r for kk in (rng.choice(ks) for _ in ks) for r in by[kk]]
            t = sum(r["rules"] for r in smp)
            if t: bs.append(100 * (sum(r["m8"] for r in smp) - sum(r["m70"] for r in smp)) / t)
        bs.sort(); t = sum(r["rules"] for r in rows); ci = S["boot_diff"](B, A, "exact")
        out[b] = dict(n=len(rows), pairs=len(ks), edits_rules=t, edits_70b=sum(r["m70"] for r in rows), edits_8b=sum(r["m8"] for r in rows),
                      saved_70b_pct=round(100 * (t - sum(r["m70"] for r in rows)) / t, 1),
                      saved_8b_pct=round(100 * (t - sum(r["m8"] for r in rows)) / t, 1),
                      saved_diff_pts=round(100 * (sum(r["m8"] for r in rows) - sum(r["m70"] for r in rows)) / t, 1),
                      saved_diff_ci95=[round(bs[int(.025 * len(bs))], 1), round(bs[int(.975 * len(bs))], 1)],
                      exact_70b=round(100 * sum(r["exact"] for r in B) / len(B), 1), exact_8b=round(100 * sum(r["exact"] for r in A) / len(A), 1),
                      exact_diff_pts=round(100 * (sum(r["exact"] for r in B) - sum(r["exact"] for r in A)) / len(A), 1),
                      exact_diff_ci95=[round(ci[0], 1), round(ci[1], 1)],
                      items_70b_fewer_edits=sum(r["m70"] < r["m8"] for r in rows), items_8b_fewer_edits=sum(r["m8"] < r["m70"] for r in rows))
    p4, p8 = (os.path.join(DATA, f"runs/8b_{b}_fresh166_g3_final.jsonl") for b in ("q4_k_m", "q8_0"))
    if os.path.exists(p4) and os.path.exists(p8):            # quantisation, paired: Q8_0 against Q4_K_M, same items
        F4, F8 = load_jsonl(os.path.relpath(p4, DATA)), load_jsonl(os.path.relpath(p8, DATA)); rows, A, B = [], [], []
        for k, x in I.items():
            gold = norm(x["tgt_new"]); r1 = norm(core.gl2.rules(x["de_old"], x["de_new"], x["tgt_old"], x["lang"])[0])
            e = lambda t: sum(S["edits"](norm(t), gold).values())
            rows.append(dict(pair=x["pair"], rules=sum(S["edits"](r1, gold).values()), q4=e(F4[k]["out"]), q8=e(F8[k]["out"])))
            A.append(S["score_one"](x, F4[k]["out"], "1")); B.append(S["score_one"](x, F8[k]["out"], "1"))
        by = {}
        for r in rows: by.setdefault(r["pair"], []).append(r)
        ks = sorted(by); rng = random.Random(7); bs = []
        for _ in range(4000):
            smp = [r for kk in (rng.choice(ks) for _ in ks) for r in by[kk]]
            t = sum(r["rules"] for r in smp)
            if t: bs.append(100 * (sum(r["q4"] for r in smp) - sum(r["q8"] for r in smp)) / t)
        bs.sort(); t = sum(r["rules"] for r in rows); ci = S["boot_diff"](B, A, "exact")
        out["q8_0_vs_q4_k_m"] = dict(saved_diff_pts=round(100 * (sum(r["q4"] for r in rows) - sum(r["q8"] for r in rows)) / t, 1),
                                     saved_diff_ci95=[round(bs[int(.025 * len(bs))], 1), round(bs[int(.975 * len(bs))], 1)],
                                     exact_diff_pts=round(100 * (sum(r["exact"] for r in B) - sum(r["exact"] for r in A)) / len(A), 1),
                                     exact_diff_ci95=[round(ci[0], 1), round(ci[1], 1)])
    return out


def ready_quality():
    """What 'ready' means on the fresh set, with honest bounds: errors the draft introduced vs errors it carried forward
    from the old text (old French naming angiotensin-II receptor antagonists 'inhibiteur de l'enzyme de conversion de
    l'angiotensine II', which BAG fixed in the same update), and 95% bounds per item, per German change and per family."""
    import re
    I = {x["key"]: x for x in load_items("items/items_fresh.json")}; F = load_jsonl(RUNS["fresh166"]["final"])
    U = [k for k in I if not F[k]["guard_flag"]]
    ace = re.compile(r"enzyme de conversion de l.angiotensine II|enzima di conversione dell.angiotensina II")
    carried = [k for k in U if ace.search(F[k]["out"]) and not ace.search(I[k]["tgt_new"])]
    pairs = {I[k]["pair"] for k in U}; fams = {I[k]["cluster"] for k in U}
    D = load_items("items/items_dev.json") + load_items("items/items_oos.json"); n = core.lock.norm
    olds = {n(x["tgt_old"]) for x in D}
    lab = load_labels(RUNS["fresh166"]["labels"])
    severe = sum(lab.get(k) in ("REAL", "stale", "german") for k in U)
    return dict(ready=len(U), introduced_severe=severe, carried_forward_mistranslation=len(carried),
                ready_de_changes=len(pairs), ready_families=len(fams),
                bound95_per_item=round(wilson(0, len(U))[1], 1), bound95_per_change=round(wilson(0, len(pairs))[1], 1),
                bound95_per_family=round(wilson(0, len(fams))[1], 1),
                fresh_gold_seen_as_dev_input=sum(n(x["tgt_new"]) in olds for x in I.values()))


def audit_eval(majority=True):
    """The divergence audit on the 6 Oct 2026 feed (data/audit), against a blind annotation of every finding: the R14
    majority of three blind annotators when committed (eval/labels/audit_relabel.tsv), the first single-annotator labels
    (`real` column of the audit TSVs) kept as first_annotation."""
    M = audit_majority_labels() if majority else None
    S = json.load(open(os.path.join(DATA, "audit", "audit_20261006_summary.json"), encoding="utf-8"))
    rows = [l.split("\t") for l in open(os.path.join(LABELS, "audit_20261006.tsv"), encoding="utf-8").read().splitlines()[1:]]
    if M: rows = [r[:6] + [M[f"audit_20261006:{r[0]}"]] + r[7:] for r in rows]
    real = [r for r in rows if r[6] == "yes"]; held = [r for r in rows if r[5] == "held"]
    rows2 = [l.split("\t") for l in open(os.path.join(LABELS, "audit2_20261006.tsv"), encoding="utf-8").read().splitlines()[1:]]
    if M: rows2 = [r[:4] + [M[f"audit2_20261006:{r[0]}"]] + r[5:] for r in rows2]
    real2 = [r for r in rows2 if r[4] == "yes"]
    allf = len(rows) + len(rows2); allreal = len(real) + len(real2)
    v2 = dict(findings_all_kinds=allf, real_all_kinds=allreal, precision_all_pct=round(100 * allreal / allf, 1),
              new_kinds_findings=len(rows2), new_kinds_real=len(real2),
              by_kind={k: [sum(r[1] == k for r in rows2), sum(r[1] == k and r[4] == "yes" for r in real2)] for k in sorted({r[1] for r in rows2})},
              real_new_beyond_known=len(real2), language_swaps=sum(r[1] == "language" and r[4] == "yes" for r in rows2),
              editorial_real=sum(r[1] == "editorial" and r[4] == "yes" for r in rows2))
    out = dict(findings=len(rows), real=len(real), precision_pct=round(100 * len(real) / len(rows), 1), v2=v2,
               precision_wilson95=[round(v, 1) for v in wilson(len(real), len(rows))],
               real_new=sum(r[4] != "True" for r in real), known_found=sum(r[4] == "True" for r in rows),
               held_findings=len(held), held_real=sum(r[6] == "yes" for r in held),
               limitations_found=len({r[1] for r in rows}), summary=S)
    if M:
        f = audit_eval(majority=False)
        out["labels"] = "majority of three blind annotators (PREREG R14, eval/labels/audit_relabel.tsv)"
        out["first_annotation"] = {k: f[k] for k in ("real", "precision_pct", "held_real")}
        out["first_annotation"]["v2"] = {k: f["v2"][k] for k in ("real_all_kinds", "precision_all_pct", "new_kinds_real", "by_kind")}
    return out


def baseline_plus():
    """Apertus 70B (fresh 166) against rules+ (gleichlaut.baseline): exact match, paired cluster bootstrap over German
    changes, and token edits still needed to reach BAG's text. `q8_0`: the same comparison for the default 8B lane (the
    certified GGUF Q8_0 run of R1/M2), by the same method and resampling seeds."""
    out = _vs_rules_plus(RUNS["fresh166"]["final"])
    out["q8_0"] = _vs_rules_plus(RUNS["q8_0"]["final"])
    return out


def _vs_rules_plus(final):
    from .baseline import rules_plus
    I = load_items("items/items_fresh.json"); F = load_jsonl(final); norm = core.lock.norm
    A, B, rows = [], [], []
    for x in I:
        rp = rules_plus(x); gold = norm(x["tgt_new"])
        a = S["score_one"](x, rp, "1"); b = S["score_one"](x, F[x["key"]]["out"], "1")
        A.append(a); B.append(b)
        rows.append(dict(rules_plus=sum(S["edits"](norm(rp), gold).values()), draft=sum(S["edits"](norm(F[x["key"]]["out"]), gold).values()),
                         pair=x["pair"], family=x["cluster"]))
    n = len(I); ex_a = sum(r["exact"] for r in A); ex_b = sum(r["exact"] for r in B)
    ci = S["boot_diff"](B, A, "exact")
    import random
    by = {}
    for r in rows: by.setdefault(r["pair"], []).append(r)
    ks = sorted(by); rng = random.Random(7); bs = []
    for _ in range(4000):
        smp = [r for k in (rng.choice(ks) for _ in ks) for r in by[k]]
        s1, s2 = sum(r["rules_plus"] for r in smp), sum(r["draft"] for r in smp)
        if s1: bs.append(100 * (s1 - s2) / s1)
    bs.sort(); e1, e2 = sum(r["rules_plus"] for r in rows), sum(r["draft"] for r in rows)
    fam = "981f07a8"; Af = [a for a, x in zip(A, I) if x["cluster"] != fam]; Bf = [b for b, x in zip(B, I) if x["cluster"] != fam]
    cif = S["boot_diff"](Bf, Af, "exact")
    return dict(n=n, rules_plus_exact_n=ex_a, rules_plus_exact=round(100 * ex_a / n, 1), model_exact=round(100 * ex_b / n, 1),
                delta=round(100 * (ex_b - ex_a) / n, 1), ci95=[round(ci[0], 1), round(ci[1], 1)],
                edits_rules_plus=e1, edits_draft=e2, edits_saved_pct=round(100 * (e1 - e2) / e1, 1),
                edits_saved_ci95=[round(bs[int(.025 * len(bs))], 1), round(bs[int(.975 * len(bs))], 1)],
                without_family=dict(n=len(Bf), rules_plus_exact=round(100 * sum(r["exact"] for r in Af) / len(Af), 1),
                                    model_exact=round(100 * sum(r["exact"] for r in Bf) / len(Bf), 1),
                                    delta=round(100 * (sum(r["exact"] for r in Bf) - sum(r["exact"] for r in Af)) / len(Bf), 1),
                                    ci95=[round(cif[0], 1), round(cif[1], 1)]))


def fresh166_by_backend():
    """Post hoc, descriptive (no rule): the 70B fresh-166 drafts split by the Public AI backend that served their calls,
    from the per-call `backend` field of the recorded responses (logged where the API reported it). Two arms: the
    headline run (`fresh166`) and its seeded rerun (R2, `m3_seed1`). Item class: every call of the item on `tp2`, every
    call on `fp1-nes`, both (`mixed`), no backend logged (`unknown`), no model call (rule-only). Per class: items, exact
    (BAG's text), ready (not flagged), and token edits saved against the rules-only start (as `post_edit`)."""
    from . import backends
    norm = core.lock.norm; out = {}
    for arm in ("fresh166", "m3_seed1"):
        R = RUNS[arm]; I = load_items(R["items"]); F = load_jsonl(R["final"])
        ask = backends.Cache(os.path.join(DATA, "cache", "responses"), model=core.M70,
                             extra={"seed": R["seed"]} if "seed" in R else None)
        seen = {}

        def rec(prompt, tag, cap, mt):
            text, meta = ask(prompt, tag, cap, mt); seen.setdefault(rec.key, []).append(meta.get("backend")); return text, meta
        P = core.Pipeline(rec, R["stack"]); rows = []
        for x in I:
            rec.key = x["key"]; r = P.run(x); f = F[x["key"]]
            assert r["out"] == f["out"] and r["guard_flag"] == f["guard_flag"], (arm, x["key"])
            b = seen.get(x["key"], [])
            kinds = {("tp2" if "-tp2-" in v else v) if v else "unknown" for v in b}
            cls = "rule-only" if not b else ("unknown" if kinds == {"unknown"} else kinds.pop() if len(kinds) == 1 else "mixed")
            gold = norm(x["tgt_new"]); r1 = norm(core.gl2.rules(x["de_old"], x["de_new"], x["tgt_old"], x["lang"])[0])
            rows.append(dict(cls=cls, exact=bool(S["score_one"](x, f["out"], "1")["exact"]), ready=not f["guard_flag"], reasked=bool(f.get("reasked")),
                             rules=sum(S["edits"](r1, gold).values()), draft=sum(S["edits"](norm(f["out"]), gold).values()), calls=b))
        calls = [v for r in rows for v in r["calls"]]
        by = {}
        for c in ("tp2", "fp1-nes", "mixed", "unknown", "rule-only"):
            Rc = [r for r in rows if r["cls"] == c]
            if not Rc: continue
            sr, sd = sum(r["rules"] for r in Rc), sum(r["draft"] for r in Rc)
            by[c] = dict(n=len(Rc), exact=sum(r["exact"] for r in Rc), exact_pct=round(100 * sum(r["exact"] for r in Rc) / len(Rc), 1),
                         ready=sum(r["ready"] for r in Rc), ready_pct=round(100 * sum(r["ready"] for r in Rc) / len(Rc), 1),
                         reasked=sum(r["reasked"] for r in Rc),
                         edits_saved_pct=round(100 * (sr - sd) / sr, 1) if sr else None)
        out[arm] = dict(n=len(rows), calls=len(calls),
                        calls_by_backend=dict(sorted(Counter(("tp2" if v and "-tp2-" in v else v) or "unknown" for v in calls).items())),
                        by_backend=by)
    out["note"] = ("post hoc and descriptive; the backend is whatever Public AI routed the call to (not chosen, not randomised), "
                   "so the classes differ in items as well as in backend")
    return out

def m1(build="q4_k_m"):
    """PREREG R1: the shipped SL pipeline with the Apertus 8B GGUF (CPU, GitHub Actions) on the fresh 166, against the same
    pass rule. Labels: drafts identical to an already-labelled output inherit its label (certify.reference_labels); every
    other ready non-exact draft and a seeded 20 flagged drafts were labelled by two blind Claude annotators, a third broke
    disagreements (eval/labels/m1_<build>_fresh166.tsv, column final)."""
    from .certify import reference_labels
    rel = f"runs/8b_{build}_fresh166_g3_final.jsonl"
    if not os.path.exists(os.path.join(DATA, rel)): return None
    I = load_items("items/items_fresh.json"); R = load_jsonl(rel); ref = reference_labels(); chk = core.check_only("g3")
    lines = open(os.path.join(LABELS, f"m1_{build}_fresh166.tsv"), encoding="utf-8").read().splitlines()
    hdr = lines[0].split("\t"); new = {c[0]: dict(zip(hdr, c)) for c in (l.split("\t") for l in lines[1:])}
    W = json.load(open(os.path.join(LABELS, f"worklist_8b_{build}_fresh166.json"), encoding="utf-8"))
    rows1, rows2 = [], []
    for x in I:
        k = x["key"]; r = R[k]
        a = S["score_one"](x, core.gl2.rules(x["de_old"], x["de_new"], x["tgt_old"], x["lang"])[0], "1"); b = S["score_one"](x, r["out"], "1")
        flag = chk.check(x, r["out"])["flag"]; assert flag == r["guard_flag"], k
        cls = "exact" if b["exact"] else (new[k]["final"] if k in new else ref.get(k, {}).get(core.lock.norm(r["out"]), "?"))
        b.update(flagged=flag, cls=cls, family=x["cluster"], reasked=r.get("reasked", False), replaced=bool(r.get("replaced")))
        a.update(family=x["cluster"]); rows1.append(a); rows2.append(b)
    s = summarise(rows1, rows2, labelled=True)
    fl = [new[k] for k in W["flagged_sample"]]
    s["flagged_sample"] = dict(n=len(fl), no_fix=sum(f["final_fix"] == "no" for f in fl))
    U = [r for r in rows2 if not r["flagged"]]
    s["ready_needs_fix"] = sum(new[r["key"]]["final_fix"] == "yes" for r in U if r["key"] in new)
    s["ready_minor_terminology"] = sum(r["cls"] == "minor" for r in U)
    secs = [R[k].get("wall_secs", 0) for k in R]
    s["cpu_secs_per_item"] = round(sum(secs) / len(secs), 1); s["model_digit_items"] = sum((R[k].get("digits_raw") or 0) > 0 or (R[k].get("reask_digits") or 0) > 0 for k in R)
    s["build"] = build
    L = list(new.values()); n = len(L); ag = sum(r["A_fix"] == r["B_fix"] for r in L)
    pA = sum(r["A_fix"] == "yes" for r in L) / n; pB = sum(r["B_fix"] == "yes" for r in L) / n; pe = pA * pB + (1 - pA) * (1 - pB)
    s["annotators"] = dict(n=n, needs_fix_agree=ag, needs_fix_kappa=round((ag / n - pe) / (1 - pe), 3) if pe < 1 else None,
                           class_agree=sum(r["A_class"] == r["B_class"] for r in L), tiebreak=sum(bool(r["T_class"]) for r in L))
    return s


def m2_rerun(build="q8_0"):
    """PREREG R9: a second CPU run of the certified build with every call recorded (data/cache/responses_8b/<build>), against
    the certified run (runs/8b_<build>_fresh166_g3_final.jsonl). Labels: exact, else the label of an identical output
    already labelled for this item (the certified run's labels, the other build's, the 70B reference run's), else the blind
    labels of eval/labels/m2_rerun_<build>_fresh166.tsv (R1 protocol)."""
    from .certify import reference_labels
    rel = f"runs/8b_{build}_fresh166_g3_rerun.jsonl"
    if not os.path.exists(os.path.join(DATA, rel)): return None
    norm = core.lock.norm; I = load_items("items/items_fresh.json"); A = load_jsonl(f"runs/8b_{build}_fresh166_g3_final.jsonl")
    B = load_jsonl(rel); chk = core.check_only("g3"); ref = reference_labels()
    for b in ("q4_k_m", "q8_0"):                        # labelled outputs of both certified 8B runs
        F = load_jsonl(f"runs/8b_{b}_fresh166_g3_final.jsonl")
        for l in open(os.path.join(LABELS, f"m1_{b}_fresh166.tsv"), encoding="utf-8").read().splitlines()[1:]:
            c = l.split("\t"); ref.setdefault(c[0], {})[norm(F[c[0]]["out"])] = c[8]
    lp = os.path.join(LABELS, f"m2_rerun_{build}_fresh166.tsv"); new = {}
    if os.path.exists(lp):
        lines = open(lp, encoding="utf-8").read().splitlines(); hdr = lines[0].split("\t")
        new = {c[0]: dict(zip(hdr, c)) for c in (l.split("\t") for l in lines[1:])}
    rows1, rows2 = [], []
    for x in I:
        k = x["key"]; r = B[k]
        a = S["score_one"](x, core.gl2.rules(x["de_old"], x["de_new"], x["tgt_old"], x["lang"])[0], "1"); b = S["score_one"](x, r["out"], "1")
        flag = chk.check(x, r["out"])["flag"]; assert flag == r["guard_flag"], k
        cls = "exact" if b["exact"] else ref.get(k, {}).get(norm(r["out"])) or (new[k]["final"] if k in new else "?")
        b.update(flagged=flag, cls=cls, family=x["cluster"], reasked=r.get("reasked", False), replaced=bool(r.get("replaced")))
        a.update(family=x["cluster"]); rows1.append(a); rows2.append(b)
    s = summarise(rows1, rows2, labelled=True)
    keys = [x["key"] for x in I]; n = len(keys)
    fa = [A[k]["guard_flag"] for k in keys]; fb = [B[k]["guard_flag"] for k in keys]
    agree = sum(p == q for p, q in zip(fa, fb)); pA, pB = sum(fa) / n, sum(fb) / n
    pe = pA * pB + (1 - pA) * (1 - pB)
    same = sum(A[k]["out"] == B[k]["out"] for k in keys)
    U = [r for r in rows2 if not r["flagged"]]
    s.update(build=build, identical_outputs=same, identical_pct=round(100 * same / n, 1), flag_agreement=agree,
             flag_kappa=round((agree / n - pe) / (1 - pe), 3) if pe < 1 else 1.0,
             flag_rate_certified=round(100 * pA, 1), flag_rate_rerun=round(100 * pB, 1),
             identical_raw_calls=sum(A[k].get(f) == B[k].get(f) for k in keys for f in ("raw1", "raw2", "reask_raw") if B[k].get(f) is not None),
             rerun_calls=sum(B[k].get(f) is not None for k in keys for f in ("raw1", "raw2", "reask_raw")),
             ready_new_labels=sum(r["key"] in new and r["cls"] == new[r["key"]]["final"] for r in U),
             ready_inherited_labels=sum(r["cls"] != "exact" and r["key"] not in new for r in U))
    if new:
        L = list(new.values()); m = len(L); ag = sum(r["A_fix"] == r["B_fix"] for r in L)
        qA = sum(r["A_fix"] == "yes" for r in L) / m; qB = sum(r["B_fix"] == "yes" for r in L) / m; qe = qA * qB + (1 - qA) * (1 - qB)
        s["annotators"] = dict(n=m, needs_fix_agree=ag, needs_fix_kappa=round((ag / m - qe) / (1 - qe), 3) if qe < 1 else None,
                               class_agree=sum(r["A_class"] == r["B_class"] for r in L), tiebreak=sum(bool(r["T_class"]) for r in L))
    return s


def audit_more():
    """Audit round 3: terminology findings learned from BAG's own corrections (6 Oct 2026 SL), and the same audit on two
    other trilingual BAG lists it was never designed on (MiGeL, Analysenliste, 1 Jul 2026), each against a blind annotation."""
    M = audit_majority_labels()

    def lab(name, M=M):
        rows = [l.split("\t") for l in open(os.path.join(LABELS, name), encoding="utf-8").read().splitlines()[1:]]
        if M: rows = [r[:4] + [M[f"{name[:-4]}:{r[0]}"]] + r[5:] for r in rows]
        return dict(findings=len(rows), real=sum(r[4] == "yes" for r in rows),
                    by_kind={k: [sum(r[1] == k for r in rows), sum(r[1] == k and r[4] == "yes" for r in rows)] for k in sorted({r[1] for r in rows})})
    names = ("audit3_terminology_20261006.tsv", "audit_migel_20260701.tsv", "audit_al_20260701.tsv")
    t, m, a = (lab(n) for n in names)
    lists_f, lists_r = m["findings"] + a["findings"], m["real"] + a["real"]
    out = dict(terminology=t, migel=m, al=a, lists_findings=lists_f, lists_real=lists_r,
               lists_precision_pct=round(100 * lists_r / lists_f, 1))
    if M:                                      # PREREG R14: the first single-annotator labels stay as first_annotation
        t1, m1_, a1 = (lab(n, None) for n in names)
        out["labels"] = "majority of three blind annotators (PREREG R14, eval/labels/audit_relabel.tsv)"
        out["first_annotation"] = dict(terminology_real=t1["real"], migel_real=m1_["real"], al_real=a1["real"],
                                       lists_real=m1_["real"] + a1["real"],
                                       lists_precision_pct=round(100 * (m1_["real"] + a1["real"]) / lists_f, 1))
    return out


def failure_modes_q8_0():
    """PREREG R8: the failure-mode tests (free translation, window-only edit, yes/no equivalence, operator typing, greedy
    retry) on the shipped Q8_0 GGUF beside the recorded MLX 4-bit runs, each scored by its research scorer (fm/measure.py)."""
    from .fm import measure
    return measure.compute()


def annotator_sensitivity(res=None):
    """PREREG R11: how often the blind annotators of eval/labels/PROTOCOL.md catch a planted meaning error. One meaning
    error of a pre-declared type was planted into copies of 66 ready fresh-166 drafts labelled exact or equivalent
    (tools/plant_sensitivity.py, seed 20261012); the same drafts untouched and 30 real labelled drafts were mixed in, and
    two blind annotators per set labelled them under (a) the protocol as used (official_new shown) and (b) with the
    published reference hidden (eval/labels/sensitivity_{a,b}.tsv). Severe = REAL or stale. Wilson 95% over items.
    res: the replay results (for the 95% bounds on severe errors among ready drafts); read from eval/results otherwise."""
    K = json.load(open(os.path.join(LABELS, "sensitivity_key.json"), encoding="utf-8"))
    I = {x["key"]: x for x in load_items("items/items_fresh.json")}
    sev = ("REAL", "stale")

    def rate(k, n):
        return dict(k=k, n=n, pct=round(100 * k / n, 1) if n else None, wilson95=[round(v, 1) for v in wilson(k, n)])

    def block(rows, hit):
        a = [hit(r, "A") for r in rows]; b = [hit(r, "B") for r in rows]; n = len(rows)
        return dict(A=rate(sum(a), n), B=rate(sum(b), n), both=rate(sum(x and y for x, y in zip(a, b)), n),
                    either=rate(sum(x or y for x, y in zip(a, b)), n))
    fix = lambda r, x: r[f"{x}_fix"] == "yes"
    severe = lambda r, x: r[f"{x}_class"] in sev

    def summary(rows):
        return dict(n=len(rows), needs_fix=block(rows, fix), severe=block(rows, severe),
                    classes=dict(sorted(Counter(r[f"{x}_class"] for r in rows for x in "AB").items())))
    out = dict(prereg="R11", seed=K["seed"], types=K["types"], counts=K["counts"], protocols={})
    for pr, name in sorted(K["protocols"].items()):
        lines = open(os.path.join(LABELS, f"sensitivity_{pr}.tsv"), encoding="utf-8").read().splitlines()
        hdr = lines[0].split("\t"); rows = [dict(zip(hdr, l.split("\t"))) for l in lines[1:]]
        assert {r["uid"] for r in rows} == set(K["items"]), pr
        for r in rows:
            it = K["items"][r["uid"]]
            r.update(base_class=it.get("base_class"), family="981f07a8" if I[it["key"]]["cluster"] == DOMINANT_FAMILY else "other")
        P = [r for r in rows if r["kind"] == "planted"]; U = [r for r in rows if r["kind"] == "untouched"]
        R = [r for r in rows if r["kind"] == "real"]
        d = dict(planted=summary(P), untouched=summary(U),
                 planted_by_type={t: summary([r for r in P if r["type"] == t]) for t in K["types"]},
                 planted_by_lang={L: summary([r for r in P if r["lang"] == L]) for L in ("fr", "it")},
                 planted_by_base_class={c: summary([r for r in P if r["base_class"] == c]) for c in ("exact", "equivalent")},
                 planted_by_family={f: summary([r for r in P if r["family"] == f]) for f in ("981f07a8", "other")})
        ex = {r["uid"]: K["items"][r["uid"]]["existing"] for r in R}
        d["real"] = dict(summary(R), existing=dict(sorted(Counter(ex.values()).items())),
                         severe_incl_german=block(R, lambda r, x: r[f"{x}_class"] in ("REAL", "stale", "german")),
                         same_class=block(R, lambda r, x: r[f"{x}_class"] == ex[r["uid"]]),
                         severe_incl_german_by_existing={c: block([r for r in R if ex[r["uid"]] == c],
                                                                  lambda r, x: r[f"{x}_class"] in ("REAL", "stale", "german"))
                                                         for c in ("REAL", "stale", "german")})
        d["missed_planted"] = [dict(uid=r["uid"], type=r["type"], A=r["A_class"], B=r["B_class"]) for r in P
                               if not (severe(r, "A") or severe(r, "B"))]
        out["protocols"][name] = d
    # what it means for the headline: an error the labelling misses is not counted, so the 95% bound on severe errors
    # among ready drafts is divided by the recall of the protocol as used (descriptive, PREREG R11)
    if res is None:
        res = {k: json.load(open(os.path.join(core.ROOT, "eval", "results", f"{k}.json"), encoding="utf-8")) for k in ("fresh166", "m1_q8_0")}
    a = out["protocols"]["reference_shown"]["planted"]["severe"]
    out["ready_bound"] = {}
    for name, s in (("70b", res["fresh166"]["summary"]["all"]), ("q8_0", res["m1_q8_0"])):
        sv = s["unflagged_REAL"] + s["unflagged_stale"] + s["unflagged_german"]; hi = s["wilson95_severe_among_ready"][1]
        out["ready_bound"][name] = dict(ready=s["unflagged"], severe=sv, bound95=hi,
                                        adjusted_both=round(min(100.0, hi / (a["both"]["pct"] / 100)), 1) if a["both"]["k"] else None,
                                        adjusted_either=round(min(100.0, hi / (a["either"]["pct"] / 100)), 1) if a["either"]["k"] else None)
    return out


BLIND_CLASSES = ("exact", "equivalent", "preexisting", "cosmetic", "minor", "german", "stale", "REAL")   # least -> most severe


def blind_needs_tiebreak(a, b, ready):
    """PROTOCOL.md step 3: a third annotator when the two disagree on needs_fix, on the class of a ready draft, or either
    says REAL. a, b = (needs_fix, class)."""
    return a[0] != b[0] or (ready and a[1] != b[1]) or "REAL" in (a[1], b[1])


def blind_relabel_70b_merge():
    """PREREG R13 merge -> rows in the R1 layout (key, A/B/T, final_fix, final, note_A), sorted by key: final_fix is the
    majority of three on needs_fix; final is the class at least two of three share, else the third's; without a third
    label the agreed class, or the more severe of two differing classes (a flagged draft without a REAL)."""
    def ann(name):
        lines = open(os.path.join(LABELS, name), encoding="utf-8").read().splitlines()[1:]
        return {c[0]: dict(fix=c[1], cls=c[2], note=c[3] if len(c) > 3 else "") for c in (l.split("\t") for l in lines if l)}
    ids = json.load(open(os.path.join(LABELS, "fresh166_blind_key.json"), encoding="utf-8"))["ids"]
    tids = {k: i for i, k in json.load(open(os.path.join(LABELS, "fresh166_blind_tiebreak_key.json"), encoding="utf-8"))["ids"].items()}
    A, B, T = ann("fresh166_blind_A.tsv"), ann("fresh166_blind_B.tsv"), ann("fresh166_blind_T.tsv")
    rank = {c: i for i, c in enumerate(BLIND_CLASSES)}; out = []
    for i, k in sorted(ids.items(), key=lambda t: t[1]):
        a, b = A[i], B[i]; t = T[tids[k]] if k in tids else None
        if t:
            fix = max(("yes", "no"), key=[a["fix"], b["fix"], t["fix"]].count)
            cs = [a["cls"], b["cls"], t["cls"]]; cls = next((c for c in cs if cs.count(c) >= 2), t["cls"])
        else:
            fix = a["fix"]; cls = max(a["cls"], b["cls"], key=rank.get)
        out.append(dict(key=k, A_fix=a["fix"], A_class=a["cls"], B_fix=b["fix"], B_class=b["cls"], T_fix=t["fix"] if t else "",
                        T_class=t["cls"] if t else "", final_fix=fix, final=cls, note_A=a["note"],
                        note_B=b["note"], note_T=t["note"] if t else ""))
    return out


def blind_relabel_70b(res=None):
    """PREREG R13: the headline 70B fresh-166 run relabelled fully blind under eval/labels/PROTOCOL.md (49 ready non-exact
    drafts + the seeded 20 flagged; two blind annotators, the second in reverse order, a third on every disagreement or
    REAL). Re-derived from the raw annotator files and keys; the committed merged file eval/labels/fresh166_blind.tsv must
    equal the merge. Reports annotator agreement and kappa, severe errors among ready drafts by the blind majority, R0's
    two label-dependent criteria with those labels, and agreement with the research labels (fresh166_*.tsv)."""
    if not os.path.exists(os.path.join(LABELS, "fresh166_blind_T.tsv")): return None
    K = json.load(open(os.path.join(LABELS, "fresh166_blind_key.json"), encoding="utf-8"))
    rows = blind_relabel_70b_merge(); M = {r["key"]: r for r in rows}
    hdr = ("key", "A_fix", "A_class", "B_fix", "B_class", "T_fix", "T_class", "final_fix", "final", "note_A")
    lines = open(os.path.join(LABELS, "fresh166_blind.tsv"), encoding="utf-8").read().splitlines()
    assert lines == ["\t".join(hdr)] + ["\t".join(r[h] for h in hdr) for r in rows], "fresh166_blind.tsv is not the merge of the raw labels"
    ready, fl = K["ready"], K["flagged_sample"]

    def kappa(x, y):
        n = len(x); ag = sum(p == q for p, q in zip(x, y)); pA = x.count("yes") / n; pB = y.count("yes") / n
        pe = pA * pB + (1 - pA) * (1 - pB)
        return dict(n=n, agree=ag, agree_pct=round(100 * ag / n, 1), kappa=round((ag / n - pe) / (1 - pe), 3) if pe < 1 else None)
    ks = sorted(M)
    ann = dict(kappa([M[k]["A_fix"] for k in ks], [M[k]["B_fix"] for k in ks]),
               ready=kappa([M[k]["A_fix"] for k in ready], [M[k]["B_fix"] for k in ready]),
               flagged_sample=kappa([M[k]["A_fix"] for k in fl], [M[k]["B_fix"] for k in fl]),
               class_agree=sum(M[k]["A_class"] == M[k]["B_class"] for k in ks), class_agree_ready=sum(M[k]["A_class"] == M[k]["B_class"] for k in ready),
               tiebreak=sum(bool(M[k]["T_class"]) for k in ks))
    sev = ("REAL", "stale", "german")
    severe = [dict(key=k, final=M[k]["final"], A=M[k]["A_class"], B=M[k]["B_class"], T=M[k]["T_class"] or None,
                   notes=[M[k][f"note_{x}"] for x in "ABT" if M[k][f"note_{x}"]]) for k in ready if M[k]["final"] in sev]
    if res is None: res = {"fresh166": json.load(open(os.path.join(core.ROOT, "eval", "results", "fresh166.json"), encoding="utf-8"))}
    s = res["fresh166"]["summary"]["all"]; n = s["n"]
    real = sum(M[k]["final"] == "REAL" for k in ready); su = sum(M[k]["final"] in ("stale", "german") for k in ready)
    r0 = dict(n=n, ready=s["unflagged"], ready_exact=s["unflagged"] - len(ready), ready_labelled=len(ready),
              unflagged_real=[round(100 * real / n, 2), 100 * real / n <= PASS_RULE["unflagged_real_max_pct"]],
              unflagged_stale_untranslated=[round(100 * su / n, 2), 100 * su / n <= PASS_RULE["unflagged_stale_untranslated_max_pct"]],
              exact_gain=s["pass_rule"]["exact_gain"], flag_rate=s["pass_rule"]["flag_rate"],
              wilson95_severe_among_ready=[round(v, 1) for v in wilson(real + su, s["unflagged"])])
    r0["pass"] = all(r0[c][1] for c in ("unflagged_real", "unflagged_stale_untranslated", "exact_gain", "flag_rate"))
    U = load_labels(RUNS["fresh166"]["labels"]); F = load_labels(RUNS["fresh166"]["flagged20"])
    rfix = {k: ("no" if U[k] in ("equivalent", "preexisting", "exact") else "yes") for k in U}
    rfix.update({k: ("no" if v == "good" else "yes") for k, v in F.items()})
    assert set(rfix) == set(M) and set(U) == set(ready), "R13 items differ from the research-labelled items"
    vs = dict(kappa([rfix[k] for k in ks], [M[k]["final_fix"] for k in ks]),
              ready=kappa([rfix[k] for k in ready], [M[k]["final_fix"] for k in ready]),
              flagged_sample=kappa([rfix[k] for k in fl], [M[k]["final_fix"] for k in fl]),
              class_agree_ready=sum(U[k] == M[k]["final"] for k in ready),
              research_severe_ready=sorted(k for k in ready if U[k] in sev), blind_severe_ready=[d["key"] for d in severe],
              disagreements=[dict(key=k, set="ready" if k in U else "flagged20", research=U.get(k) or F[k],
                                  blind=f"{M[k]['final_fix']} {M[k]['final']}") for k in ks if rfix[k] != M[k]["final_fix"]])
    return dict(prereg="R13", items=len(ks), ready_non_exact=len(ready), flagged_sample=len(fl), annotators=ann,
                ready_classes=dict(sorted(Counter(M[k]["final"] for k in ready).items())),
                ready_needs_fix=sum(M[k]["final_fix"] == "yes" for k in ready),
                flagged_sample_no_fix=sum(M[k]["final_fix"] == "no" for k in fl), flagged_sample_research_good=sum(v == "good" for v in F.values()),
                flagged_sample_classes=dict(sorted(Counter(M[k]["final"] for k in fl).items())),
                severe_among_ready=len(severe), severe_among_ready_items=severe, r0_with_blind_labels=r0, vs_research=vs)


# ------------------------------------------------------------------ PREREG R14 part A: audit findings relabelled blind
AUDIT_RELABEL_SETS = {"register": ("audit_20261006", "audit2_20261006"), "terminology": ("audit3_terminology_20261006",),
                      "lists": ("audit_migel_20260701", "audit_al_20260701")}
AUDIT_RELABEL_COLS = ("uid", "set", "first", "A", "B", "T", "final", "final_confirmed", "note_A", "note_B", "note_T")


def audit_first_labels():
    """The first (single-annotator) audit labels: {'<file>:<id>': 'yes' | 'no'} from the `real` column of each file."""
    out = {}
    for files in AUDIT_RELABEL_SETS.values():
        for f in files:
            lines = open(os.path.join(LABELS, f"{f}.tsv"), encoding="utf-8").read().splitlines(); hdr = lines[0].split("\t")
            for l in lines[1:]:
                c = dict(zip(hdr, l.split("\t"))); out[f"{f}:{c['id']}"] = c["real"]
    return out


def audit_relabel_merge():
    """R14 part A merge -> rows (AUDIT_RELABEL_COLS) sorted by uid: `final` is the answer at least two of A, B, T share,
    else T's; confirmed = real or minor; `final_confirmed` is the majority of three on confirmed (A's when A and B agree)."""
    def ann(name):
        lines = open(os.path.join(LABELS, name), encoding="utf-8").read().splitlines()[1:]
        return {c[0]: dict(ans=c[1], note=c[2] if len(c) > 2 else "") for c in (l.split("\t") for l in lines if l)}
    K = json.load(open(os.path.join(LABELS, "audit_relabel_key.json"), encoding="utf-8"))
    tids = {u: i for i, u in json.load(open(os.path.join(LABELS, "audit_relabel_tiebreak_key.json"), encoding="utf-8"))["ids"].items()}
    A, B, T = ann("audit_relabel_A.tsv"), ann("audit_relabel_B.tsv"), ann("audit_relabel_T.tsv")
    first = audit_first_labels(); st = {f: s for s, fs in AUDIT_RELABEL_SETS.items() for f in fs}
    conf = lambda a: "yes" if a in ("real", "minor") else "no"
    out = []
    for i, u in sorted(K["ids"].items(), key=lambda t: t[1]):
        a, b = A[i], B[i]; t = T[tids[u]] if u in tids else None
        if t:
            cs = [a["ans"], b["ans"], t["ans"]]; fin = next((c for c in cs if cs.count(c) >= 2), t["ans"])
            fc = max(("yes", "no"), key=[conf(c) for c in cs].count)
        else:
            fin = a["ans"]; fc = conf(a["ans"])
        out.append(dict(uid=u, set=st[u.split(":")[0]], first=first[u], A=a["ans"], B=b["ans"], T=t["ans"] if t else "", final=fin,
                        final_confirmed=fc, note_A=a["note"], note_B=b["note"], note_T=t["note"] if t else ""))
    return out


def _kappa_yes(x, y):
    n = len(x); ag = sum(p == q for p, q in zip(x, y)); pA = x.count("yes") / n; pB = y.count("yes") / n
    pe = pA * pB + (1 - pA) * (1 - pB)
    return dict(n=n, agree=ag, agree_pct=round(100 * ag / n, 1), kappa=round((ag / n - pe) / (1 - pe), 3) if pe < 1 else None)


def audit_majority_labels():
    """{'<file>:<id>': 'yes' | 'no'}: the R14 majority-of-three labels when committed, else None."""
    if not os.path.exists(os.path.join(LABELS, "audit_relabel.tsv")): return None
    lines = open(os.path.join(LABELS, "audit_relabel.tsv"), encoding="utf-8").read().splitlines(); hdr = lines[0].split("\t")
    return {r["uid"]: r["final_confirmed"] for r in (dict(zip(hdr, l.split("\t"))) for l in lines[1:])}


def audit_relabel():
    """PREREG R14 part A: every labelled audit finding (register 27, terminology 11, MiGeL + Analysenliste 11) relabelled
    by two fresh blind annotators (the second in reverse order) and a third on every differing answer, with each record's
    audit question unchanged. Re-derived from the raw annotator files and keys; the committed eval/labels/audit_relabel.tsv
    must equal the merge. Confirmed = real or minor (the first annotation's yes)."""
    if not os.path.exists(os.path.join(LABELS, "audit_relabel.tsv")): return None
    rows = audit_relabel_merge()
    lines = open(os.path.join(LABELS, "audit_relabel.tsv"), encoding="utf-8").read().splitlines()
    assert lines == ["\t".join(AUDIT_RELABEL_COLS)] + ["\t".join(r[h] for h in AUDIT_RELABEL_COLS) for r in rows], \
        "audit_relabel.tsv is not the merge of the raw labels"
    conf = lambda a: "yes" if a in ("real", "minor") else "no"

    def block(R):
        n = len(R); maj = sum(r["final_confirmed"] == "yes" for r in R); fst = sum(r["first"] == "yes" for r in R)
        strict = sum(r["final"] == "real" for r in R)
        return dict(n=n, annotators=dict(_kappa_yes([conf(r["A"]) for r in R], [conf(r["B"]) for r in R]),
                                         answer_agree=sum(r["A"] == r["B"] for r in R), tiebreak=sum(bool(r["T"]) for r in R)),
                    confirmed_majority=maj, precision_majority_pct=round(100 * maj / n, 1),
                    precision_majority_wilson95=[round(v, 1) for v in wilson(maj, n)],
                    confirmed_strict_real=strict, precision_strict_pct=round(100 * strict / n, 1),
                    confirmed_first=fst, precision_first_pct=round(100 * fst / n, 1),
                    vs_first=_kappa_yes([r["first"] for r in R], [r["final_confirmed"] for r in R]),
                    answers=dict(sorted(Counter(r["final"] for r in R).items())),
                    changed=[dict(uid=r["uid"], first=r["first"], majority=r["final_confirmed"], A=r["A"], B=r["B"], T=r["T"] or None,
                                  notes=[r[f"note_{x}"] for x in "ABT" if r[f"note_{x}"]]) for r in R if r["first"] != r["final_confirmed"]])
    out = dict(prereg="R14 (part A)", findings=len(rows), all=block(rows),
               sets={s: block([r for r in rows if r["set"] == s]) for s in AUDIT_RELABEL_SETS},
               files={f: block([r for r in rows if r["uid"].startswith(f + ":")]) for fs in AUDIT_RELABEL_SETS.values() for f in fs})
    out["numbers_switch"] = any(b["confirmed_majority"] != b["confirmed_first"] for b in out["sets"].values())
    return out


# ------------------------------------------------------------------ PREREG R14 part B: meaning errors inside the amended wording
def annotator_sensitivity_inspan(res=None):
    """PREREG R14 part B: how often the blind annotators of eval/labels/PROTOCOL.md (reference shown) catch a meaning error
    written inside the sentence the German change touched, as fluent text that reads like part of the amendment
    (tools/plant_inspan.py, seed 20261017; plants by hand in eval/labels/inspan_plants.json). 38 bases (70B and Q8_0 ready
    drafts labelled exact or equivalent) planted and untouched, 30 real drafts mixed in; two annotators per worklist
    (eval/labels/inspan_sensitivity.tsv). Severe = REAL or stale (as R11). Wilson 95% over items."""
    if not os.path.exists(os.path.join(LABELS, "inspan_sensitivity.tsv")): return None
    K = json.load(open(os.path.join(LABELS, "inspan_key.json"), encoding="utf-8"))
    lines = open(os.path.join(LABELS, "inspan_sensitivity.tsv"), encoding="utf-8").read().splitlines()
    hdr = lines[0].split("\t"); rows = [dict(zip(hdr, l.split("\t"))) for l in lines[1:]]
    assert {r["uid"] for r in rows} == set(K["items"])
    sev = ("REAL", "stale")

    def rate(k, n): return dict(k=k, n=n, pct=round(100 * k / n, 1) if n else None, wilson95=[round(v, 1) for v in wilson(k, n)])

    def block(R, hit):
        a = [hit(r, "A") for r in R]; b = [hit(r, "B") for r in R]; n = len(R)
        return dict(A=rate(sum(a), n), B=rate(sum(b), n), both=rate(sum(x and y for x, y in zip(a, b)), n),
                    either=rate(sum(x or y for x, y in zip(a, b)), n))
    fix = lambda r, x: r[f"{x}_fix"] == "yes"
    severe = lambda r, x: r[f"{x}_class"] in sev

    def summary(R):
        return dict(n=len(R), needs_fix=block(R, fix), severe=block(R, severe),
                    classes=dict(sorted(Counter(r[f"{x}_class"] for r in R for x in "AB").items())))
    for r in rows: r.update(family=K["items"][r["uid"]].get("family"), base_class=K["items"][r["uid"]].get("base_class"))
    P = [r for r in rows if r["kind"] == "planted"]; U = [r for r in rows if r["kind"] == "untouched"]; R = [r for r in rows if r["kind"] == "real"]
    ex = {r["uid"]: K["items"][r["uid"]]["existing"] for r in R}
    out = dict(prereg="R14 (part B)", seed=K["seed"], types=K["types"], counts=K["counts"],
               planted=summary(P), untouched=summary(U),
               planted_by_type={t: summary([r for r in P if r["type"] == t]) for t in K["types"]},
               planted_by_lang={L: summary([r for r in P if r["lang"] == L]) for L in ("fr", "it")},
               planted_by_family={f: summary([r for r in P if r["family"] == f]) for f in (DOMINANT_FAMILY, "other")},
               planted_by_base_class={c: summary([r for r in P if r["base_class"] == c]) for c in ("exact", "equivalent")},
               real=dict(summary(R), existing=dict(sorted(Counter(ex.values()).items())),
                         severe_incl_german_by_existing={c: block([r for r in R if ex[r["uid"]] == c],
                                                                  lambda r, x: r[f"{x}_class"] in ("REAL", "stale", "german"))
                                                         for c in ("REAL", "stale", "german")}))
    it = K["items"]
    out["missed_planted"] = [dict(uid=r["uid"], type=r["type"], error=it[r["uid"]]["error"], old=it[r["uid"]]["old"], new=it[r["uid"]]["new"],
                                  A=r["A_class"], B=r["B_class"], note_A=r["note_A"], note_B=r["note_B"])
                             for r in P if not (severe(r, "A") and severe(r, "B"))]
    if res is None:
        res = {k: json.load(open(os.path.join(core.ROOT, "eval", "results", f"{k}.json"), encoding="utf-8")) for k in ("fresh166", "m1_q8_0")}
    a = out["planted"]["severe"]; out["ready_bound"] = {}
    for name, s in (("70b", res["fresh166"]["summary"]["all"]), ("q8_0", res["m1_q8_0"])):
        hi = s["wilson95_severe_among_ready"][1]
        out["ready_bound"][name] = dict(ready=s["unflagged"], bound95=hi,
                                        adjusted_both=round(min(100.0, hi / (a["both"]["pct"] / 100)), 1) if a["both"]["k"] else None,
                                        adjusted_either=round(min(100.0, hi / (a["either"]["pct"] / 100)), 1) if a["either"]["k"] else None)
    return out


def _memo_norm(s):
    import re, unicodedata
    from .sl.ingest import nrm
    s = unicodedata.normalize("NFC", nrm(s)).replace("\u2019", "'").replace("\u2018", "'")
    return re.sub(r"^(\.\.\.|\u2026)\s*", "", s)


def memo_score_text(r, resp):
    """PREREG R16 per text: r = an item of data/memo/r16_items.json, resp = the model's continuation of r["prefix"]."""
    pre, truth, o = _memo_norm(r["prefix"]), _memo_norm(r["truth"]).split(" "), _memo_norm(resp)
    echo = o.startswith(pre)
    if echo: o = o[len(pre):].strip()
    w = o.split(" ") if o else []
    lcp = next((i for i, (a, b) in enumerate(zip(w, truth)) if a != b), min(len(w), len(truth)))
    k = min(100, len(truth)); hyp = " ".join(w[:k])
    d = dict(set=r["set"], key=r["key"], lang=r["lang"], next10=w[:10] == truth[:10], lcp=lcp,
             chrf=round(S["chrf"](hyp, " ".join(truth[:k])), 4), echo=echo)
    if r.get("old_cont"):
        old = _memo_norm(r["old_cont"]).split(" "); a, b = S["chrf"](hyp, " ".join(truth[:k])), S["chrf"](hyp, " ".join(old[:k]))
        d["closer"] = "new" if a > b else "old" if b > a else "tie"
    return d


def memorisation():
    """PREREG R16: memorisation probe. Each text of data/memo/r16_items.json (T: the fresh-166 answers, P: texts unchanged
    since before 2023, N: new texts of the Aug/Sep 2026 live months) was cut after half its words and the model asked to
    continue it word for word. Re-derived from the recorded responses (looked up by the sha256 of the rebuilt request, as
    replay does): next-10 exact (primary), leading words equal, chrF of the first k <= 100 words; T - N and P - N with a
    percentile bootstrap (10,000, seed 20261016) and Mann-Whitney; the pre-registered decision per model."""
    import random
    from . import backends
    D = json.load(open(os.path.join(DATA, "memo", "r16_items.json"), encoding="utf-8"))
    instr, mt = D["instruction"], D["max_tokens"]
    per_text = memo_score_text
    def boot(x, y, B=10000):
        rng = random.Random(20261016); n, m = len(x), len(y); out = []
        for _ in range(B): out.append(sum(rng.choices(x, k=n)) / n - sum(rng.choices(y, k=m)) / m)
        out.sort(); return [out[int(0.025 * B)], out[int(0.975 * B) - 1]]
    def mwu(x, y):
        allv = sorted((v, g) for g, L in ((0, x), (1, y)) for v in L); ranks = {}; i = 0; ties = 0
        while i < len(allv):
            j = i
            while j < len(allv) and allv[j][0] == allv[i][0]: j += 1
            ranks[allv[i][0]] = (i + j + 1) / 2; t = j - i; ties += t ** 3 - t; i = j
        n1, n2 = len(x), len(y); N = n1 + n2
        u = sum(ranks[v] for v in x) - n1 * (n1 + 1) / 2
        sd = math.sqrt(n1 * n2 / 12 * ((N + 1) - ties / (N * (N - 1))))
        z = 0.0 if sd == 0 else (u - n1 * n2 / 2) / sd
        return dict(u=u, p=round(math.erfc(abs(z) / math.sqrt(2)), 6))
    res = dict(prereg="R16", sizes=D["sizes"], langs=D["langs"], instruction=instr, max_tokens=mt, models={})
    for name, folder, model in (("70b", "r16_70b", D["model"]), ("8b_q8_0", "r16_8b_q8_0", "gguf:q8_0.gguf")):
        root = os.path.join(DATA, "memo", folder, "responses")
        if not os.path.isdir(root): continue
        ask = backends.Cache(root, model=model); rows, served = [], Counter()
        for r in D["items"]:
            text, meta = ask(instr + r["prefix"], "r16", 0, mt)
            served[meta.get("model_served")] += 1; rows.append(per_text(r, text))
        G = {s: [d for d in rows if d["set"] == s] for s in "TPN"}
        sets = {s: dict(n=len(L), next10=round(100 * sum(d["next10"] for d in L) / len(L), 2), next10_count=sum(d["next10"] for d in L),
                        lcp_mean=round(sum(d["lcp"] for d in L) / len(L), 3), lcp_max=max(d["lcp"] for d in L),
                        chrf_mean=round(sum(d["chrf"] for d in L) / len(L), 3), echo=sum(d["echo"] for d in L),
                        closer=dict(sorted(Counter(d["closer"] for d in L if "closer" in d).items())))
                for s, L in G.items()}
        cmp_ = {}
        for a in ("T", "P"):
            c = {}
            for f, sc in (("next10", 100), ("lcp", 1), ("chrf", 1)):
                x = [sc * float(d[f]) for d in G[a]]; y = [sc * float(d[f]) for d in G["N"]]
                c[f] = dict(diff=round(sum(x) / len(x) - sum(y) / len(y), 3), ci95=[round(v, 3) for v in boot(x, y)])
                if f != "next10": c[f]["mannwhitney"] = mwu(x, y)
            c["meets_criterion"] = c["next10"]["diff"] > 10 and c["next10"]["ci95"][0] > 0
            cmp_[f"{a}-N"] = c
        flagged = cmp_["T-N"]["meets_criterion"]
        res["models"][name] = dict(model=model, texts=len(rows), requests=len({r["payload_key"] for r in D["items"]}), served=dict(served), sets=sets, compare=cmp_,
                                   memorisation_flagged=flagged, probe_detects_long_standing=cmp_["P-N"]["meets_criterion"],
                                   verdict=("memorisation of the test answers flagged" if flagged else
                                            "no evidence of memorisation beyond the negative control"),
                                   top_lcp=[{k: d[k] for k in ("set", "key", "lang", "lcp", "chrf")} for d in
                                            sorted(rows, key=lambda d: (-d["lcp"], d["key"]))[:8]])
    return res


# ------------------------------------------------------------------ PREREG R17: real errors; a non-Claude annotator
R17_SEVERE = ("REAL", "stale", "german")
R17_SWEEP = "36d94228"           # the one house-wording sweep (Opdivo FR code sentence), 10 of the 17 changes
R17_MODEL = "swiss-ai/apertus-v1.5-70b"


def _r17_clean(text):
    return (text or "").replace("*", "").replace("`", "")


def r17_parse_record(text):
    """PREREG R17 fixed answer format for a part-A record -> (needs_fix, class) or None (unparsed)."""
    import re
    t = _r17_clean(text)
    f = re.search(r"(?im)^\s*needs_fix\s*:\s*(yes|no)\b", t); c = re.search(r"(?im)^\s*class\s*:\s*([A-Za-z]+)", t)
    cls = {x.lower(): x for x in BLIND_CLASSES}.get(c.group(1).lower()) if c else None
    return (f.group(1).lower(), cls) if f and cls else None


def r17_parse_audit(text):
    """PREREG R17 fixed answer format for an audit record -> 'real' | 'minor' | 'not' | None (unparsed)."""
    import re
    m = re.search(r"(?im)^\s*answer\s*:\s*(real|minor|not)\b", _r17_clean(text))
    return m.group(1).lower() if m else None


def _r17_rate(k, n): return dict(k=k, n=n, pct=round(100 * k / n, 1) if n else None, wilson95=[round(v, 1) for v in wilson(k, n)])


def _r17_rows(p):
    lines = open(os.path.join(LABELS, f"r17_real_errors_{p}.tsv"), encoding="utf-8").read().splitlines()
    hdr = lines[0].split("\t")
    return [dict(zip(hdr, l.split("\t"))) for l in lines[1:] if l]


def annotator_real_errors():
    """PREREG R17 part A: do the blind Claude annotators of eval/labels/PROTOCOL.md catch errors that people made and BAG
    later fixed? Every FR/IT limitation change in the SL snapshot series with the German byte-identical, classified
    mechanically; the 17 content changes as an error record (the text that disagrees with the German) and a control
    record (the correct text), never in the same worklist, labelled by two blind annotators per worklist under (a)
    reference shown and (b) hidden (tools/r17_real_errors.py; eval/labels/r17_real_errors_{a,b}.tsv). Severe = REAL,
    stale or german. Wilson 95% over records."""
    if not os.path.exists(os.path.join(LABELS, "r17_real_errors_a.tsv")): return None
    K = json.load(open(os.path.join(LABELS, "r17_key.json"), encoding="utf-8"))
    ch = {c["uid"]: c for c in K["changes"]}

    def block(R, hit):
        a = [hit(r, "A") for r in R]; b = [hit(r, "B") for r in R]
        return dict(A=_r17_rate(sum(a), len(R)), B=_r17_rate(sum(b), len(R)), both=_r17_rate(sum(x and y for x, y in zip(a, b)), len(R)),
                    either=_r17_rate(sum(x or y for x, y in zip(a, b)), len(R)))
    fix = lambda r, x: r[f"{x}_fix"] == "yes"
    sev = lambda r, x: r[f"{x}_class"] in R17_SEVERE

    def summary(R):
        return dict(n=len(R), needs_fix=block(R, fix), severe=block(R, sev),
                    classes=dict(sorted(Counter(r[f"{x}_class"] for r in R for x in "AB").items())))
    out = dict(prereg="R17 (part A)", severe=list(R17_SEVERE), mining=K["mining"], counts=K["counts"], reversed=sorted(K["reversed"]),
               protocols={})
    for p, name in (("a", "reference_shown"), ("b", "reference_hidden")):
        rows = _r17_rows(p)
        assert {r["key"] for r in rows} == set(K["items"]), p
        for r in rows:
            it = K["items"][r["key"]]; r.update(uid=it["uid"], family=it["family"], reversed=it["reversed"])
        E = [r for r in rows if r["kind"] == "error"]; C = [r for r in rows if r["kind"] == "control"]
        d = dict(errors=summary(E), controls=summary(C),
                 errors_by_type={t: summary([r for r in E if r["type"] == t]) for t in sorted({r["type"] for r in E})},
                 errors_by_family={"sweep_" + R17_SWEEP: summary([r for r in E if r["family"] == R17_SWEEP]),
                                   "other": summary([r for r in E if r["family"] != R17_SWEEP])},
                 errors_by_lang={L: summary([r for r in E if r["lang"] == L]) for L in ("fr", "it")},
                 errors_bag_fixes=summary([r for r in E if not r["reversed"]]),
                 errors_reversed=summary([r for r in E if r["reversed"]]),
                 annotators=_kappa_yes([r["A_fix"] for r in rows], [r["B_fix"] for r in rows]))
        d["per_error"] = [dict(uid=r["uid"], type=r["type"], family=r["family"], reversed=r["reversed"], edit=ch[r["uid"]]["word_diff"],
                               A=f"{r['A_fix']} {r['A_class']}", B=f"{r['B_fix']} {r['B_class']}", note_A=r["note_A"], note_B=r["note_B"])
                          for r in sorted(E, key=lambda r: r["uid"])]
        d["missed_by_both"] = [x["uid"] for x in d["per_error"] if not any(fix(r, a) for r in E if r["uid"] == x["uid"] for a in "AB")]
        d["false_alarms"] = [dict(uid=r["uid"], A=f"{r['A_fix']} {r['A_class']}", B=f"{r['B_fix']} {r['B_class']}", note_A=r["note_A"],
                                  note_B=r["note_B"]) for r in sorted(C, key=lambda r: r["uid"]) if fix(r, "A") or fix(r, "B")]
        out["protocols"][name] = d
    return out


def annotator_crossfamily():
    """PREREG R17 part B: Apertus 70B (a different model family) as a second annotator: (i) the 49 audit findings of R14
    (the audit uses no model) against the Claude majority of three; (ii) the part-A records under both protocols against
    the error / control truth and the two Claude annotators. Re-derived from the recorded responses in
    data/r17/apertus70b/responses (looked up by the sha256 of the frozen request) with the fixed parsers."""
    from . import backends
    root = os.path.join(DATA, "r17", "apertus70b", "responses")
    if not os.path.isdir(root): return None
    D = json.load(open(os.path.join(DATA, "r17", "r17_70b_prompts.json"), encoding="utf-8"))
    ask = backends.Cache(root, model=D["model"]); served = Counter(); got = {}
    for r in D["requests"]:
        assert r["payload_key"] == backends.payload_key(D["model"], r["prompt"], D["max_tokens"])
        text, meta = ask(r["prompt"], "r17", 0, D["max_tokens"]); served[meta.get("model_served")] += 1
        got[(r["task"], r["id"])] = text
    assert set(served) == {R17_MODEL}, served
    conf = lambda a: "yes" if a in ("real", "minor") else "no"
    # (i) audit
    ids = json.load(open(os.path.join(LABELS, "audit_relabel_key.json"), encoding="utf-8"))["ids"]
    maj = {r["uid"]: r for r in audit_relabel_merge()}
    rows = []
    for i, u in sorted(ids.items()):
        a = r17_parse_audit(got[("audit", i)])
        rows.append(dict(id=i, uid=u, set=maj[u]["set"], apertus=a, claude=maj[u]["final"], claude_confirmed=maj[u]["final_confirmed"]))
    P = [r for r in rows if r["apertus"]]

    def ablock(R):
        R = [r for r in R if r["apertus"]]
        return dict(_kappa_yes([conf(r["apertus"]) for r in R], [r["claude_confirmed"] for r in R]),
                    answer_agree=sum(r["apertus"] == r["claude"] for r in R),
                    apertus_confirmed=sum(conf(r["apertus"]) == "yes" for r in R), claude_confirmed=sum(r["claude_confirmed"] == "yes" for r in R))
    audit = dict(n=len(rows), unparsed=len(rows) - len(P), all=ablock(rows),
                 sets={s: ablock([r for r in rows if r["set"] == s]) for s in AUDIT_RELABEL_SETS},
                 answers=dict(sorted(Counter(r["apertus"] or "unparsed" for r in rows).items())),
                 differ=[dict(uid=r["uid"], apertus=r["apertus"], claude=r["claude"]) for r in rows
                         if not r["apertus"] or conf(r["apertus"]) != r["claude_confirmed"]])
    # (ii) part A
    K = json.load(open(os.path.join(LABELS, "r17_key.json"), encoding="utf-8")); out_a = {}
    for p, name in (("a", "reference_shown"), ("b", "reference_hidden")):
        L = {r["key"]: r for r in _r17_rows(p)} if os.path.exists(os.path.join(LABELS, f"r17_real_errors_{p}.tsv")) else {}
        recs = []
        for i, k in sorted(K["ids"].items()):
            if not i.startswith(("X", "Y") if p == "a" else ("J", "K")): continue
            it = K["items"][k]; a = r17_parse_record(got[(p, i)])
            recs.append(dict(key=k, kind=it["kind"], type=it["type"], reversed=it["reversed"], ans=a, claude=L.get(k)))
        E = [r for r in recs if r["kind"] == "error"]; C = [r for r in recs if r["kind"] == "control"]
        fx = lambda r: bool(r["ans"]) and r["ans"][0] == "yes"; sv = lambda r: bool(r["ans"]) and r["ans"][1] in R17_SEVERE
        d = dict(unparsed=sum(not r["ans"] for r in recs),
                 errors=dict(n=len(E), needs_fix=_r17_rate(sum(map(fx, E)), len(E)), severe=_r17_rate(sum(map(sv, E)), len(E)),
                             classes=dict(sorted(Counter(r["ans"][1] if r["ans"] else "unparsed" for r in E).items()))),
                 errors_bag_fixes=dict(needs_fix=_r17_rate(sum(fx(r) for r in E if not r["reversed"]), sum(not r["reversed"] for r in E))),
                 errors_by_type={t: _r17_rate(sum(fx(r) for r in E if r["type"] == t), sum(r["type"] == t for r in E)) for t in sorted({r["type"] for r in E})},
                 controls=dict(n=len(C), needs_fix=_r17_rate(sum(map(fx, C)), len(C)), severe=_r17_rate(sum(map(sv, C)), len(C)),
                               classes=dict(sorted(Counter(r["ans"][1] if r["ans"] else "unparsed" for r in C).items()))))
        if L:
            Q = [r for r in recs if r["ans"]]
            d["vs_claude"] = {x: _kappa_yes([r["ans"][0] for r in Q], [r["claude"][f"{x}_fix"] for r in Q]) for x in "AB"}
            S = [r for r in Q if r["claude"]["A_fix"] == r["claude"]["B_fix"]]
            d["vs_claude"]["where_A_B_agree"] = _kappa_yes([r["ans"][0] for r in S], [r["claude"]["A_fix"] for r in S]) if S else None
        out_a[name] = d
    return dict(prereg="R17 (part B)", model=D["model"], requests=len(D["requests"]), served=dict(served), max_tokens=D["max_tokens"],
                audit=audit, real_errors=out_a)


R18_NAMED = ("AMVUTTRA.01a", "BEYONTTRA", "VYNDAQEL.01b")


def _auroc(pos, neg):
    """P(score of a positive > score of a negative), ties count one half."""
    if not pos or not neg: return None
    v = sorted([(s, 1) for s in pos] + [(s, 0) for s in neg]); rk, i = 0.0, 0
    while i < len(v):                                        # rank sum of the positives, tied ranks averaged
        j = i
        while j < len(v) and v[j][0] == v[i][0]: j += 1
        rk += (i + j + 1) / 2 * sum(w for _, w in v[i:j]); i = j
    return (rk - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg))


def audit_apertus_filter():
    """PREREG R18: the certified Apertus 8B Q8_0 as a log-probability filter on the round-5 audit findings that ship off.
    Re-derived from the recorded run (data/r18/runs/8b_q8_0/records.jsonl, keyed by sentence pair) and data/r18/items.json:
    threshold t* by Youden's J on the planted fit half, AUROC on the planted test half (bootstrap over copies), t* applied
    unchanged to the 31 register findings, precision before / after against the R15 blind labels, the decision rule."""
    import random, re
    D = json.load(open(os.path.join(DATA, "r18", "items.json"), encoding="utf-8"))
    run = os.path.join(DATA, "r18", "runs", "8b_q8_0")
    if not os.path.exists(os.path.join(run, "records.jsonl")): return None
    R = {r["pk"]: r for r in (json.loads(l) for l in open(os.path.join(run, "records.jsonl"), encoding="utf-8") if l.strip())}
    I = D["items"]; missing = sorted({x["pk"] for x in I if x["pk"] not in R})
    sc = lambda x: R[x["pk"]]["p_diff"]
    r4 = lambda v: None if v is None else round(v, 4)
    g4 = lambda v: None if v is None else float(f"{v:.4g}")          # scores and threshold: 4 significant digits (many sit near 0)
    # planted copies: (planted, control) per copy
    pl = {x["uid"][3:]: x for x in I if x["set"] == "planted" and x["pk"] in R}
    ct = {x["uid"][3:]: x for x in I if x["set"] == "control" and x["pk"] in R}
    C = [(pl[k], ct[k]) for k in sorted(pl) if k in ct]
    fit = [c for c in C if c[0]["split"] == "fit"]; test = [c for c in C if c[0]["split"] == "test"]
    pos = lambda S: [sc(a) for a, _ in S]; neg = lambda S: [sc(b) for _, b in S]
    rate = lambda v, t: sum(s >= t for s in v) / len(v) if v else None
    best = None
    for t in sorted(set(pos(fit) + neg(fit)), reverse=True):
        j = rate(pos(fit), t) - rate(neg(fit), t)
        if best is None or j > best[0] + 1e-15: best = (j, t)
    J, T = best
    rng = random.Random(20261018); B = []
    for _ in range(2000):
        S = [test[rng.randrange(len(test))] for _ in test]; B.append(_auroc(pos(S), neg(S)))
    B.sort()
    def block(S):
        return dict(copies=len(S), auroc=r4(_auroc(pos(S), neg(S))), tpr_at_t=r4(rate(pos(S), T)), fpr_at_t=r4(rate(neg(S), T)),
                    mean_planted=g4(sum(pos(S)) / len(S)) if S else None, mean_control=g4(sum(neg(S)) / len(S)) if S else None)
    types = sorted({a["type"] for a, _ in C})
    planted = dict(fit=block(fit), test=dict(block(test), auroc_ci95=[r4(B[49]), r4(B[1949])]), all=block(C),
                   by_type={t: dict(test=block([c for c in test if c[0]["type"] == t]), all=block([c for c in C if c[0]["type"] == t]),
                                    by_lang={L: block([c for c in C if c[0]["type"] == t and c[0]["lang"] == L]) for L in ("fr", "it")})
                            for t in types},
                   detected_by_r15=dict(copies=sum(a["detected"] for a, _ in C), kept=sum(a["detected"] and sc(a) >= T for a, _ in C)),
                   not_detected_by_r15=dict(copies=sum(not a["detected"] for a, _ in C), kept=sum((not a["detected"]) and sc(a) >= T for a, _ in C)))
    # register
    parse = lambda t: (lambda m: m.group(1) if m else None)(re.search(r"\b(ja|nein)\b", (t or "").lower()))
    reg = []
    for x in (x for x in I if x["set"] == "register"):
        r = R.get(x["pk"])
        reg.append(dict(fid=x["fid"], id=x["wid"], limitation=x["cud"], lang=x["lang"], kind=x["kind"], label=x["final"],
                        confirmed=x["confirmed"], score=g4(r["p_diff"]) if r else None, kept=bool(r) and r["p_diff"] >= T,
                        answers=[parse(r["ab"]["raw"]), parse(r["ba"]["raw"])] if r else None))
    def prec(S):
        k = [r for r in S if r["kept"]]; y = sum(r["confirmed"] for r in k)
        return dict(findings=len(S), confirmed=sum(r["confirmed"] for r in S), kept=len(k), kept_confirmed=y,
                    precision_before_pct=round(100 * sum(r["confirmed"] for r in S) / len(S), 1) if S else None,
                    precision_after_pct=round(100 * y / len(k), 1) if k else None,
                    wilson95_after_pct=[round(v, 1) for v in wilson(y, len(k))] if k else None)
    allp = prec(reg); kinds = {k: prec([r for r in reg if r["kind"] == k]) for k in ("operator", "negation", "number_word")}
    ok = allp["kept"] > 0 and allp["precision_after_pct"] >= 50 and allp["kept_confirmed"] >= 4
    dec = dict(rule="kept precision >= 50% and >= 4 of the 6 confirmed kept; then per kind kept precision >= 50%",
               precision_ok=bool(allp["kept"]) and allp["precision_after_pct"] >= 50, confirmed_kept_ok=allp["kept_confirmed"] >= 4,
               pass_=ok, proposed_on={k: ok and bool(v["kept"]) and v["precision_after_pct"] >= 50 for k, v in kinds.items()})
    dec["pass"] = dec.pop("pass_")
    pc = [r["score"] for r in reg if r["confirmed"]]; pn = [r["score"] for r in reg if not r["confirmed"]]
    real = [r["score"] for r in reg if r["label"] == "real"]; rest = [r["score"] for r in reg if r["label"] != "real"]
    ans = Counter(parse(R[k]["ab"]["raw"]) or "other" for k in R) + Counter(parse(R[k]["ba"]["raw"]) or "other" for k in R)
    gates = json.load(open(os.path.join(run, "shards.json"), encoding="utf-8")) if os.path.exists(os.path.join(run, "shards.json")) else []
    return dict(prereg="R18", model="Apertus 8B GGUF Q8_0 (certified build), llama-cpp-python, CPU runners",
                pairs=dict(n=len(D["pairs"]), scored=len(R), missing=len(missing)),
                shards=dict(n=len(gates), certificate_verified=sum(bool(g.get("certificate")) for g in gates),
                            certificates=sorted({g.get("certificate") for g in gates if g.get("certificate")})),
                threshold=dict(t=g4(T), youden_j_fit=r4(J), chosen_on="planted fit half"),
                planted=planted,
                register=dict(all=allp, by_kind=kinds, auroc_confirmed_vs_not=r4(_auroc(pc, pn)), auroc_real_vs_rest=r4(_auroc(real, rest)),
                              named={r["limitation"]: dict(fid=r["fid"], score=r["score"], kept=r["kept"]) for r in reg if r["limitation"] in R18_NAMED},
                              confirmed=[dict(fid=r["fid"], limitation=r["limitation"], lang=r["lang"], kind=r["kind"], label=r["label"],
                                              score=r["score"], kept=r["kept"]) for r in reg if r["confirmed"]],
                              rows=reg),
                generation=dict(answers=dict(sorted(ans.items())), calls=2 * len(R),
                                mean_mass=r4(sum(R[k][o]["mass"] for k in R for o in ("ab", "ba")) / (2 * len(R))) if R else None),
                decision=dec)


def r19_decide(acc, ci_shared_minus_q8, byte_fp1_pct, dec_gap_pts):
    """PREREG R19 decision rule (stated before the run): -> (outcome, flags)."""
    low = acc <= 78.0 and ci_shared_minus_q8[0] > 0
    far = byte_fp1_pct >= 90.0 and dec_gap_pts >= 3.0
    if low and acc >= 65.0 and far: o = "O1"
    elif low and byte_fp1_pct < 75.0: o = "O2"
    elif acc >= 80.0 or ci_shared_minus_q8[0] <= 0: o = "O3"
    else: o = "O4"
    return o, dict(mmlu_low=low, fp1_far_more_than_tp2=far, fp1_agreement_low=byte_fp1_pct < 75.0)


R19_OUTCOME = {"O1": "fp1-nes is likely an 8B: the headline '70B' arm may be partly 8B-served",
               "O2": "the 70B inference is strengthened",
               "O3": "MMLU does not separate the shared model from the v1.5 8B; the 84.4% is no longer evidence of size",
               "O4": "inconclusive"}


def identity_r19():
    """PREREG R19: the certified 8B Q8_0 on the identity probes, against the recorded Public AI outputs. MMLU (250
    questions, run.py prompt and first-[ABCD] scorer): accuracy, paired bootstrap differences against the shared model
    (the apertus-v1.5-8b name) and the v1 8B route. Battery (792 cells): byte-identical generated text against fp1-nes and
    the 8B name, generation decisions against both, forced-choice decisions and log-odds against tp2 and the 8B name;
    the prompt token counts against the API's. Then the pre-registered decision rule."""
    import random
    R19 = os.path.join(DATA, "r19"); run = os.path.join(R19, "runs", "8b_q8_0")
    if not os.path.exists(os.path.join(run, "battery.jsonl")): return None
    jl = lambda p: [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]
    ld = lambda rel: json.load(open(os.path.join(R19, rel), encoding="utf-8"))
    items = ld("mmlu/items.json"); M = {r["j"]: r for r in jl(os.path.join(run, "mmlu.jsonl"))}
    sh, v1 = ld("mmlu/res_swiss-ai_apertus-v1.5-8b.json"), ld("mmlu/res_swiss-ai_apertus-8b-instruct.json")
    n = len(items); assert len(M) == n == len(sh) == len(v1)
    gold = ["ABCD"[it["a"]] for it in items]
    for j in range(n): assert M[j]["gold"] == sh[j]["gold"] == v1[j]["gold"] == gold[j]
    q = [M[j]["pred"] == gold[j] for j in range(n)]; s_ = [r["pred"] == r["gold"] for r in sh]; v_ = [r["pred"] == r["gold"] for r in v1]
    pct = lambda k, m: round(100 * k / m, 1)

    def boot(a, b, seed=20261019, B=2000):
        rng = random.Random(seed); ds = []
        for _ in range(B):
            idx = [rng.randrange(n) for _ in range(n)]; ds.append(100 * sum(a[i] - b[i] for i in idx) / n)
        ds.sort(); return [round(ds[int(0.025 * B)], 1), round(ds[int(0.975 * B)], 1)]
    acc = 100 * sum(q) / n
    mmlu = dict(n=n, q8_0=dict(correct=sum(q), pct=pct(sum(q), n), wilson95=[round(v, 1) for v in wilson(sum(q), n)],
                               unparsed=sum(M[j]["pred"] is None for j in range(n))),
                shared=dict(correct=sum(s_), pct=pct(sum(s_), n)), v1_8b=dict(correct=sum(v_), pct=pct(sum(v_), n)),
                shared_minus_q8=dict(pts=round(100 * (sum(s_) - sum(q)) / n, 1), ci95=boot(s_, q)),
                q8_minus_v1=dict(pts=round(100 * (sum(q) - sum(v_)) / n, 1), ci95=boot(q, v_)),
                letters_agree_shared=sum(M[j]["pred"] == sh[j]["pred"] for j in range(n)),
                letters_agree_v1=sum(M[j]["pred"] == v1[j]["pred"] for j in range(n)),
                raw_answers=dict(sorted(Counter(M[j]["raw"] for j in range(n)).most_common(8))))
    rec = {k: ld(f"battery/{k}.json")["rows"] for k in ("gen_apertus-v1.5-70b", "gen_apertus-v1.5-8b", "fc_apertus-v1.5-8b", "fc_apertus-70b-instruct")}
    Bq = {r["j"]: r for r in jl(os.path.join(run, "battery.jsonl"))}; N = len(rec["gen_apertus-v1.5-70b"]); assert len(Bq) == N == 792
    fp1, g8, f8, tp2 = (rec[k] for k in ("gen_apertus-v1.5-70b", "gen_apertus-v1.5-8b", "fc_apertus-v1.5-8b", "fc_apertus-70b-instruct"))
    for j in range(N):
        b = Bq[j]
        for z in (fp1[j], g8[j], f8[j], tp2[j]): assert (z["set"], z["item"], z["variant"], z["cell"]) == (b["set"], b["item"], b["variant"], b["cell"])
    same = lambda a, b: a is not None and a == b
    byte = lambda rows, strip=False: sum((Bq[j]["text"].strip() == rows[j]["text"].strip()) if strip else (Bq[j]["text"] == rows[j]["text"]) for j in range(N))
    dec_g = lambda rows: sum(same(Bq[j]["dec"], rows[j]["dec"]) for j in range(N))
    dec_f = lambda rows: sum((Bq[j]["lo"] > 0) == (rows[j]["lo_conv"] > 0) for j in range(N))

    def corr(rows):
        x = [Bq[j]["lo"] for j in range(N)]; y = [rows[j]["lo_conv"] for j in range(N)]
        mx, my = sum(x) / N, sum(y) / N
        cov = sum((a - mx) * (b - my) for a, b in zip(x, y)); vx = sum((a - mx) ** 2 for a in x); vy = sum((b - my) ** 2 for b in y)
        return round(cov / (vx * vy) ** 0.5, 3), round(sum(abs(a - b) for a, b in zip(x, y)) / N, 2)
    r_t, m_t = corr(tp2); r_8, m_8 = corr(f8)
    ptok_gen = [j for j in range(N) if Bq[j]["ptok"] != fp1[j]["pt"]]
    ptok_fc = [j for j in range(N) for c, v in Bq[j]["fc"].items() if v["ntok"] != tp2[j]["calls"][c]["pt"]]
    bf, df, dt = byte(fp1), dec_g(fp1), dec_f(tp2)
    ref = dict(fp1_vs_8b_name_text=sum(fp1[j]["text"] == g8[j]["text"] for j in range(N)),
               fp1_vs_8b_name_decisions=sum(same(fp1[j]["dec"], g8[j]["dec"]) for j in range(N)),
               b8_name_vs_tp2_forced_choice=sum((f8[j]["lo_conv"] > 0) == (tp2[j]["lo_conv"] > 0) for j in range(N)),
               fp1_generation_vs_tp2_forced_choice=sum(fp1[j]["dec"] is not None and fp1[j]["dec"] == int(tp2[j]["lo_conv"] > 0) for j in range(N)))
    bat = dict(n=N, text_identical_fp1=bf, text_identical_fp1_pct=pct(bf, N), text_identical_fp1_stripped=byte(fp1, True),
               text_identical_8b_name=byte(g8), text_identical_8b_name_stripped=byte(g8, True),
               decisions_fp1=df, decisions_fp1_pct=pct(df, N), decisions_8b_name=dec_g(g8),
               forced_choice_tp2=dt, forced_choice_tp2_pct=pct(dt, N), forced_choice_8b_name=dec_f(f8),
               logodds_tp2=dict(r=r_t, mean_abs_diff=m_t), logodds_8b_name=dict(r=r_8, mean_abs_diff=m_8),
               q8_unparsed=sum(Bq[j]["dec"] is None for j in range(N)),
               q8_generation_vs_forced_choice=sum(Bq[j]["dec"] is not None and Bq[j]["dec"] == int(Bq[j]["lo"] > 0) for j in range(N)),
               prompt_tokens_mismatch=dict(generation=len(ptok_gen), forced_choice=len(ptok_fc), generation_cells=ptok_gen[:20],
                                           forced_choice_cells=sorted(set(ptok_fc))[:20]),
               q8_answers=dict(Counter(Bq[j]["text"] for j in range(N)).most_common(6)), recorded_references=ref)
    gap = round(100 * (df - dt) / N, 1)
    o, flags = r19_decide(acc, mmlu["shared_minus_q8"]["ci95"], 100 * bf / N, gap)
    shards = json.load(open(os.path.join(run, "shards.json"), encoding="utf-8"))
    return dict(mmlu=mmlu, battery=bat, decision=dict(outcome=o, reading=R19_OUTCOME[o], decisions_gap_fp1_minus_tp2_pts=gap, **flags),
                shards=dict(n=len(shards), certificate_verified=sum(1 for g in shards if g.get("certificate")),
                            gguf_sha256=sorted({g["gguf_sha256"] for g in shards})))
