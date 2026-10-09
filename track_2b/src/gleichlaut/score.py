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
    return dict(n=n, agree=agree, kappa=round((pa - pe) / (1 - pe), 3),
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
    def side(labels_file, n, exact, flagged):
        lines = open(os.path.join(LABELS, labels_file), encoding="utf-8").read().splitlines()[1:]
        c = Counter(l.split("\t")[2] for l in lines); real, su = c.get("REAL", 0), c.get("stale", 0) + c.get("german", 0)
        return dict(n=n, exact=exact, exact_pct=round(100 * exact / n, 1), flagged=flagged, flag_rate=round(100 * flagged / n, 1),
                    ready=n - flagged, ready_nonexact_labelled=len(lines), classes=dict(sorted(c.items())),
                    unflagged_real=real, unflagged_real_pct=round(100 * real / n, 2),
                    unflagged_stale_untranslated=su, unflagged_stale_untranslated_pct=round(100 * su / n, 2),
                    passes=(100 * real / n <= PASS_RULE["unflagged_real_max_pct"] and 100 * su / n <= PASS_RULE["unflagged_stale_untranslated_max_pct"]
                            and 100 * flagged / n <= PASS_RULE["flag_rate_max_pct"] and 100 * (exact - rules) / n >= PASS_RULE["exact_gain_min_pts"]))
    n = len(items)
    a = side("fedlex_shipped_unflagged.tsv", n, s8["all"]["exact"], s8["all"]["flagged"])
    b = side("fedlex70b_shipped_unflagged.tsv", n, sum(bool(r.get("exact")) for r in R70), sum(r["flagged"] for r in R70))
    assert len(R70) == n
    return {"n": n, "rules_exact": rules, "rules_exact_pct": round(100 * rules / n, 1), "8b_mlx_dwq": a, "70b": b,
            "decision": "Fedlex stays 8B; every draft goes to review" if not b["passes"] else "70B passes R0"}
