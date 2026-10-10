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
    a = side("fedlex_shipped_unflagged.tsv", n, s8["all"]["exact"], s8["all"]["flagged"])
    b = side("fedlex70b_shipped_unflagged.tsv", n, sum(bool(r.get("exact")) for r in R70), sum(r["flagged"] for r in R70))
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


def shadow_month(run="20260901-20261001"):
    """PREREG R7: the first shadow month on the public feed (items mined by the shadow workflow from BAG's feeds of the two
    dates), drafted by Q4_K_M and Q8_0 (shadow workflow, CPU, --network none) and by the 70B (development gateway), same
    items and routing. Labels: every ready draft that differs from BAG's published text, pooled, blind (R1 protocol)."""
    import re
    D = os.path.join(DATA, "shadow", run); I = {x["key"]: x for x in json.load(open(os.path.join(D, "items.json"), encoding="utf-8"))}
    lines = open(os.path.join(LABELS, f"shadow_{run.replace('-', '_')}_ready.tsv"), encoding="utf-8").read().splitlines()
    hdr = lines[0].split("\t"); lab = [dict(zip(hdr, l.split("\t"))) for l in lines[1:]]
    norm = core.lock.norm; out = {}
    cmp_ = [k for k, x in I.items() if x.get("tgt_new")]
    for m in ("q4_k_m", "q8_0", "70b"):
        R = {json.loads(l)["key"]: json.loads(l) for l in open(os.path.join(D, m, "records.jsonl"), encoding="utf-8")}
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
    q4 = {json.loads(l)["key"]: json.loads(l) for l in open(os.path.join(D, "q4_k_m", "records.jsonl"), encoding="utf-8")}
    dr = [k for k in cmp_ if q4[k]["status"] != "human"]
    rules = sum(norm(core.gl2.rules(I[k]["de_old"], I[k]["de_new"], I[k]["tgt_old"], I[k]["lang"])[0]) == norm(I[k]["tgt_new"]) for k in dr)
    new = "Indikationscode dieser Limitierung"
    boiler = [k for k in dr if new in I[k]["de_new"] and new not in I[k]["de_old"]]
    fr = Counter()
    for k in cmp_:
        x = I[k]
        if x["lang"] == "fr" and new in x["de_new"]:
            m_ = re.search(r"code d.indication de cette limitation[^.]*?transmis à l.(assureur-maladie|assurance maladie)", x["tgt_new"])
            if m_: fr[m_.group(1)] += 1
    return dict(run=run, mining=json.load(open(os.path.join(D, "q4_k_m", "summary.json"), encoding="utf-8"))["mining"],
                rules_exact=rules, compared=len(dr), boilerplate_items=len(boiler), bag_fr_rendering_of_new_sentence=dict(fr),
                labelled=len(lab), annotators_agree=sum((r["A_fix"], r["A_class"]) == (r["B_fix"], r["B_class"]) for r in lab),
                ready_total=sum(v["ready"] for v in out.values()), ready_errors_total=sum(v["ready_errors"] for v in out.values()),
                **out)


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


def audit_eval():
    """The divergence audit on the 6 Oct 2026 feed (data/audit), against a blind annotation of every finding."""
    S = json.load(open(os.path.join(DATA, "audit", "audit_20261006_summary.json"), encoding="utf-8"))
    rows = [l.split("\t") for l in open(os.path.join(LABELS, "audit_20261006.tsv"), encoding="utf-8").read().splitlines()[1:]]
    real = [r for r in rows if r[6] == "yes"]; held = [r for r in rows if r[5] == "held"]
    rows2 = [l.split("\t") for l in open(os.path.join(LABELS, "audit2_20261006.tsv"), encoding="utf-8").read().splitlines()[1:]]
    real2 = [r for r in rows2 if r[4] == "yes"]
    allf = len(rows) + len(rows2); allreal = len(real) + len(real2)
    v2 = dict(findings_all_kinds=allf, real_all_kinds=allreal, precision_all_pct=round(100 * allreal / allf, 1),
              new_kinds_findings=len(rows2), new_kinds_real=len(real2),
              by_kind={k: [sum(r[1] == k for r in rows2), sum(r[1] == k and r[4] == "yes" for r in real2)] for k in sorted({r[1] for r in rows2})},
              real_new_beyond_known=len(real2), language_swaps=sum(r[1] == "language" and r[4] == "yes" for r in rows2),
              editorial_real=sum(r[1] == "editorial" and r[4] == "yes" for r in rows2))
    return dict(findings=len(rows), real=len(real), precision_pct=round(100 * len(real) / len(rows), 1), v2=v2,
                precision_wilson95=[round(v, 1) for v in wilson(len(real), len(rows))],
                real_new=sum(r[4] != "True" for r in real), known_found=sum(r[4] == "True" for r in rows),
                held_findings=len(held), held_real=sum(r[6] == "yes" for r in held),
                limitations_found=len({r[1] for r in rows}), summary=S)


def baseline_plus():
    """Apertus 70B (fresh 166) against rules+ (gleichlaut.baseline): exact match, paired cluster bootstrap over German
    changes, and token edits still needed to reach BAG's text."""
    from .baseline import rules_plus
    I = load_items("items/items_fresh.json"); F = load_jsonl(RUNS["fresh166"]["final"]); norm = core.lock.norm
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


def audit_more():
    """Audit round 3: terminology findings learned from BAG's own corrections (6 Oct 2026 SL), and the same audit on two
    other trilingual BAG lists it was never designed on (MiGeL, Analysenliste, 1 Jul 2026), each against a blind annotation."""
    def lab(name):
        rows = [l.split("\t") for l in open(os.path.join(LABELS, name), encoding="utf-8").read().splitlines()[1:]]
        return dict(findings=len(rows), real=sum(r[4] == "yes" for r in rows),
                    by_kind={k: [sum(r[1] == k for r in rows), sum(r[1] == k and r[4] == "yes" for r in rows)] for k in sorted({r[1] for r in rows})})
    t, m, a = lab("audit3_terminology_20261006.tsv"), lab("audit_migel_20260701.tsv"), lab("audit_al_20260701.tsv")
    lists_f, lists_r = m["findings"] + a["findings"], m["real"] + a["real"]
    return dict(terminology=t, migel=m, al=a, lists_findings=lists_f, lists_real=lists_r,
                lists_precision_pct=round(100 * lists_r / lists_f, 1))
