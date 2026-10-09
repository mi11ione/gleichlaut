"""M6 backtest over the monthly SL snapshots, exactly as pre-registered in eval/prereg/PREREG.md rule R3. CPU only, no model calls.

lag.json        every DE limitation change between consecutive usable 2026 snapshots (sl.mine's unit: product + key, text pair
                <= 60% changed; > 60% rewrites reported separately as the human lane) and whether FR and IT changed in the same
                step, in a later snapshot (months to fix), or never within the window. Counts only, no rates over an unknown population.
since_feb.json  "had it run since February": the recorded 362-item 2026 pool (items_dev + items_oos; 70B, guards v2, one re-ask)
                mapped onto its snapshot transitions; per transition DE changes, FR/IT items, ready vs flagged (flags re-computed
                with the frozen stack the runs used). DEV numbers: guards3 was designed on the 242.
targeted5.json  the 5 hand-verified divergences (+ Keytruda KN045): (a) present in the earliest capture or introduced inside the
                window, (b) what the numbers-not-in-DE check and the slot comparison say about today's FR/IT vs DE, (c) for a DE
                change inside the window, the rules-arm output, the routing, and the recorded 70B draft where one exists.
known_errors_texts.json  the DE/FR/IT texts of those limitations per capture (review UI, demo video).

usage: python3 -m gleichlaut.backtest [--hist DIR] [--wb2025 DIR] [--out DIR]
  --hist    2026 snapshot JSONs (sl.ingest output; default $GLEICHLAUT_HIST or track_2b/out/hist)
  --wb2025  dir holding 20250611/Preparations.xml and 20250731/Preparations.xml (default $GLEICHLAUT_WB2025 or track_2b/out/wb2025)"""
import argparse, datetime, json, os, re, sys
from collections import Counter, defaultdict
from . import core, score
from .sl import hist_dir, OUT
from .sl import mine as M
from .sl.ingest import nrm, load_xml

DEST = os.path.join(core.ROOT, "data", "backtest")
WB = [("20250601", "20250611"), ("20250701", "20250731")]   # release date, Wayback capture dir (results.md S3; build_fresh.SNAPS)
LANGS = ("fr", "it")
DEV_NOTE = ("DEV numbers. The 362 items are the 2026 pool: guards v2 was shaped on the dev 120 (in-sample) and guards3 was designed "
            "on the 242 after the out-of-sample run failed. Only the fresh 2025 set (data/items/items_fresh.json) is held out.")


def days(a, b):
    f = lambda s: datetime.date(int(s[:4]), int(s[4:6]), int(s[6:]))
    return (f(b) - f(a)).days


class Snaps:
    """snapshot access with cached per-product DE maps and the full step matching (every greedy pair, any ratio)."""
    def __init__(self, hist, snaps=M.SNAPS):
        self.H, self.snaps, self._bp = hist, snaps, {}
        self.fwd, self.back = defaultdict(dict), defaultdict(dict)       # (a, b, mpd) -> {old de: new de} / {new de: old de}
        for a, b, m, _, _, _, P in M.steps(hist, snaps):
            for r, g, n in P: self.fwd[(a, b, m)][g] = n; self.back[(a, b, m)][n] = g

    def bp(self, s):
        if s not in self._bp: self._bp[s] = self.H.byprod(s)
        return self._bp[s]

    def tgt(self, s, lang, m, dekey):
        k = M.tkey(self.H, s, lang, m, dekey)
        t = self.H(s, lang)["lim"].get(k) if k else None
        return nrm(t) if t is not None else None


# ------------------------------------------------------------------ 1. lag count
def fate(S, o, lang):
    """what happened to the FR/IT text of one DE change occurrence."""
    a, b, m = o["snap_old"], o["snap_new"], o["mpd"]
    if o["key_old"] in S.H(a)["conflict"] or o["key_new"] in S.H(b)["conflict"]: return dict(status="conflict")
    to, tn = S.tgt(a, lang, m, o["key_old"]), S.tgt(b, lang, m, o["key_new"])
    if to is None or tn is None: return dict(status="target_missing")
    if a <= M.OLD_FORMAT_LAST and ("<" in to or "<" in tn): return dict(status="lt_bug")
    if to != tn: return dict(status="same_step")
    later = S.snaps[S.snaps.index(b) + 1:]
    cur, prev, again = nrm(S.H(b)["lim"][o["key_new"]]), b, []
    for c in later:
        P = S.bp(c)
        if m not in P: return dict(status="never", reason="product_gone", at=c, later_seen=later.index(c))
        T = P[m][1]
        if cur not in T:
            n = S.fwd[(prev, c, m)].get(cur)
            if n is None: return dict(status="never", reason="de_removed", at=c, later_seen=later.index(c))
            cur = n; again.append(c)
        tc = S.tgt(c, lang, m, T[cur])
        if tc is None: return dict(status="never", reason="target_missing_later", at=c, later_seen=later.index(c))
        if tc != tn:
            return dict(status="lagged", fixed_at=c, steps=later.index(c) + 1, days=days(b, c), de_changed_again=again,
                        de_changed_at_fix_step=c in again)
        prev = c
    return dict(status="never", reason="window_end" if later else "no_later_snapshot", later_seen=len(later))


DEFINITIVE = ("same_step", "lagged", "never")


def lag(S, C):
    """-> lag.json body. Unit = (step, DE old text, DE new text); its occurrences (products / keys) are checked one by one and
    the unit takes the first definitive verdict (occurrence disagreements are counted)."""
    out = dict(units={}, per_step=[], cases={})
    for lane, pairs in (("draft", C["pairs"]), ("human", C["human"])):
        units = defaultdict(list)
        for p in pairs:
            for o in p["occ"]: units[(o["snap_old"], o["snap_new"], p["de_old"], p["de_new"])].append((p, o))
        rows = []
        for (a, b, g, n), occs in sorted(units.items(), key=lambda kv: (kv[0][0], kv[0][2], kv[0][3])):
            row = dict(step=f"{a}>{b}", ratio=occs[0][0]["ratio"], keys=sorted({f'{o["key_old"]}>{o["key_new"]}' for _, o in occs})[:4],
                       product=occs[0][1]["name"], n_occ=len(occs))
            for lang in LANGS:
                F = [fate(S, o, lang) for _, o in occs]
                d = [f for f in F if f["status"] in DEFINITIVE]
                row[lang] = d[0] if d else F[0]
                row[lang + "_disagree"] = len({f["status"] for f in d}) > 1
            rows.append(row)
        out["units"][lane] = rows
    for lane, rows in out["units"].items():
        s = dict(units=len(rows), occurrences=sum(r["n_occ"] for r in rows))
        for lang in LANGS:
            st = Counter(r[lang]["status"] for r in rows)
            lagged = [r[lang] for r in rows if r[lang]["status"] == "lagged"]
            never = [r[lang] for r in rows if r[lang]["status"] == "never"]
            s[lang] = dict(status=dict(sorted(st.items())),
                           lagged_steps_to_fix=dict(sorted(Counter(f["steps"] for f in lagged).items())),
                           lagged_days_to_fix=sorted(f["days"] for f in lagged),
                           lagged_months_to_fix=dict(sorted(Counter(round(f["days"] / 30.44) for f in lagged).items())),
                           lagged_with_de_change_at_fix_step=sum(f["de_changed_at_fix_step"] for f in lagged),
                           never_reason=dict(sorted(Counter(f["reason"] for f in never).items())),
                           occurrence_disagreements=sum(r[lang + "_disagree"] for r in rows))
        both = Counter("+".join(sorted({r[l]["status"] for l in LANGS})) for r in rows)
        s["fr_and_it"] = dict(sorted(both.items()))
        out["units"][lane] = dict(summary=s, rows=rows)
    steps = sorted({r["step"] for lane in out["units"].values() for r in lane["rows"]} | {f"{a}>{b}" for a, b in zip(S.snaps, S.snaps[1:])})
    for st in steps:
        d = dict(step=st, days=days(*st.split(">")))
        for lane, L in out["units"].items():
            R = [r for r in L["rows"] if r["step"] == st]
            d[lane] = dict(units=len(R), **{lang: dict(sorted(Counter(r[lang]["status"] for r in R).items())) for lang in LANGS})
        out["per_step"].append(d)
    # the non-same-step draft-lane cases in full (small), for hand inspection
    for r in out["units"]["draft"]["rows"]:
        if any(r[l]["status"] in ("lagged", "never") for l in LANGS):
            p = next(p for p in C["pairs"] for o in p["occ"] if f'{o["snap_old"]}>{o["snap_new"]}' == r["step"] and f'{o["key_old"]}>{o["key_new"]}' in r["keys"])
            a, b, ops = core.lock.de_ops(p["de_old"], p["de_new"])
            out["cases"].setdefault("draft_not_same_step", []).append(dict(
                step=r["step"], keys=r["keys"], product=r["product"], fr=r["fr"], it=r["it"],
                de_edit=core.gl2.changes_list(a, b, ops)[:600]))
    return out


def vision_check(C, S):
    """the two figures the vision quotes: '216 DE changes over 7 monthly steps' and '~14 rewrites > 60%' (per month)."""
    span = days(S.snaps[0], S.snaps[-1]); over = sum(s["over60"] for s in C["stats"])
    return dict(
        steps=len(C["stats"]), snapshots=S.snaps, span_days=span, span_months=round(span / 30.44, 2),
        note_steps="8 transitions between 9 usable snapshots; 6 are ~1 month, 01.04>01.06 is 2 months (May excluded) and "
                   "01.10>06.10 is 5 days. '7 monthly steps' is the 7-month denominator, not the number of steps.",
        distinct_draft_pairs=len(C["pairs"]), distinct_draft_pairs_per_month=round(len(C["pairs"]) / (span / 30.44), 1),
        quoted_31_per_month_is=f"{len(C['pairs'])}/7 = {len(C['pairs']) / 7:.1f}",
        over60_matched_occurrences=over, over60_distinct_text_pairs=len(C["human"]),
        over60_by_step=[dict(step=f'{s["a"]}>{s["b"]}', occurrences=s["over60"]) for s in C["stats"]],
        quoted_14_per_month_is=f"{over}/7 = {over / 7:.1f}: matched product occurrences, not distinct rewrites "
                               f"(distinct: {len(C['human'])}, i.e. {len(C['human']) / (span / 30.44):.1f}/month)")


# ------------------------------------------------------------------ 2. had it run since February (DEV)
def since_feb(S, C):
    B = M.build(C["pairs"], S.H)
    where = {(x["lang"], x["de_old"], x["de_new"], x["tgt_old"], x["tgt_new"]): f'{x["snap_old"]}>{x["snap_new"]}' for x in B["items_all"]}
    first = {(p["de_old"], p["de_new"]): "{}>{}".format(*p["first"]) for p in C["pairs"]}
    per = defaultdict(lambda: dict(items=Counter(), v2=Counter(), g3=Counter()))
    unmapped = []
    for run in ("dev120", "oos242"):
        R = score.RUNS[run]; I = score.load_items(R["items"]); F = score.load_jsonl(R["final"]); lab = score.load_labels(R["labels"])
        Pv, P3 = core.check_only(R["stack"]), core.check_only("g3")
        for x in I:
            st = where.get((x["lang"], x["de_old"], x["de_new"], x["tgt_old"], x["tgt_new"]))
            if x.get("snap_old") and st != f'{x["snap_old"]}>{x["snap_new"]}': unmapped.append(x["key"]); continue
            if st is None: unmapped.append(x["key"]); continue
            f = F[x["key"]]; out = f["out"]
            fl = Pv.check(x, out)["flag"]; assert fl == f["guard_flag"], (run, x["key"])    # re-guarded = recorded
            exact = bool(core.SCORE["score_one"](x, out, "1")["exact"])
            d = per[st]; d["items"][x["lang"]] += 1; d["items"]["all"] += 1; d.setdefault("fam", Counter())[x["cluster"]] += 1
            d["v2"]["flagged" if fl else "ready"] += 1
            if not fl: d["v2"]["ready_exact" if exact else "ready_" + lab.get(x["key"], "unlabelled")] += 1
            d["g3"]["flagged" if P3.check(x, out)["flag"] else "ready"] += 1
            d["v2"]["exact"] += exact; d["v2"]["rule_only"] += bool(f["rule_only"])
    stats = {f'{s["a"]}>{s["b"]}': s for s in C["stats"]}
    excl = defaultdict(Counter)
    for p in C["pairs"]:
        if len(p["de_old"]) > M.MAXCH or len(p["de_new"]) > M.MAXCH: excl[first[(p["de_old"], p["de_new"])]]["too_long"] += 1
    human = Counter("{}>{}".format(*h["first"]) for h in C["human"])
    pool = Counter(f'{c["o"]["snap_old"]}>{c["o"]["snap_new"]}' for c in B["cands"])
    rows = []
    for st, s in stats.items():
        d = per.get(st, dict(items=Counter(), v2=Counter(), g3=Counter()))
        rows.append(dict(step=st, days=days(*st.split(">")),
                         de_changes=dict(matched=s["matched"], draft_lane_new_distinct=s["new_distinct_pairs"],
                                         human_lane_over60_occurrences=s["over60"], human_lane_over60_new_distinct=human[st],
                                         excluded_too_long=excl[st]["too_long"],
                                         excluded_target_unchanged_or_missing=s["new_distinct_pairs"] - excl[st]["too_long"] - pool[st],
                                         in_pool=pool[st]),
                         items=dict(sorted(d["items"].items())), exact=d["v2"].get("exact", 0), rule_only=d["v2"].get("rule_only", 0),
                         ready_v2=d["v2"].get("ready", 0), flagged_v2=d["v2"].get("flagged", 0),
                         ready_v2_by_label={k[6:]: v for k, v in sorted(d["v2"].items()) if k.startswith("ready_")},
                         ready_g3_recheck=d["g3"].get("ready", 0), flagged_g3_recheck=d["g3"].get("flagged", 0),
                         families=len(d.get("fam", {})), largest_family=(lambda f: dict(family=f[0][0], items=f[0][1]) if f else None)(d.get("fam", Counter()).most_common(1))))
    tot = lambda f: sum(f(r) for r in rows)
    return dict(
        status=DEV_NOTE,
        what="Recorded 70B outputs (whole-paragraph locked rewrite, guards v2, one re-ask: data/runs/70b_dev120_v2_final.jsonl, "
             "70b_oos242_v2_final.jsonl) on the 362-item 2026 pool, placed on the snapshot transition where the DE change first "
             "qualified. ready/flagged = core.check_only(score.RUNS[run]['stack']='v2').check(x, out)['flag'] (asserted equal to "
             "the recorded flag). ready_g3_recheck = the same recorded outputs re-guarded with guards3 (the shipped stack); the outputs "
             "themselves came from the v2 re-ask loop, so this is not what a guards3 run would have produced.",
        pool_stats=B["stats"], unmapped_items=unmapped, per_transition=rows,
        totals=dict(items=tot(lambda r: r["items"].get("all", 0)), ready_v2=tot(lambda r: r["ready_v2"]), flagged_v2=tot(lambda r: r["flagged_v2"]),
                    ready_g3_recheck=tot(lambda r: r["ready_g3_recheck"]), exact=tot(lambda r: r["exact"]),
                    rule_only=tot(lambda r: r["rule_only"]),
                    ready_v2_by_label=dict(sum((Counter(r["ready_v2_by_label"]) for r in rows), Counter()))))


# ------------------------------------------------------------------ 3. targeted run on the hand-verified divergences
KN045 = "KEYTRUDA.07---Inj-L-s---Urothelkarzinom--Monotherapie--KN045"
# (case, CUD, tests). A test is (lang, kind, value): 'lacks' = value in DE but not in the target, 'adds' = in the target but not
# in DE, 'is_fr' = the Italian slot holds French. Values and languages are the hand-check labels (spikes/gleichlaut/out/
# handcheck50.tsv, sweep25.tsv; results.md "The 10 clearest examples"). The divergence is present iff every test holds.
CASES = [
    ("Nemluvio", "NEMLUVIO.01", [("it", "lacks", "8")]),
    ("Diaphin", "DIAPHIN.6-", [("it", "adds", "12"), ("it", "lacks", "6")]),
    ("etanercept", "NEPEXTO", [("fr", "adds", "62.5")]),
    ("etanercept", "BENEPALI4", [("fr", "adds", "62.5")]),
    ("etanercept", "ERELZI2", [("fr", "adds", "62.5")]),
    ("Cresemba", "CRESE.Kps.IM", [("fr", "lacks", "16")]),
    ("Dupixent", "DUPIXENT.02P", [("fr", "lacks", "15")]),
    ("Dupixent", "DUPIXENT.02", [("fr", "lacks", "15")]),
    ("Dupixent", "DUPIXENT.05a", [("fr", "adds", "30"), ("fr", "lacks", "15")]),
    ("Dupixent", "DUPIXENT.05P", [("fr", "adds", "30"), ("fr", "lacks", "15")]),
    ("Keytruda (bonus)", KN045, [("it", "is_fr", None)]),
]
FRW = set("le la les des du de et avec pour est en au aux par chez une un sur dans ou".split())
ITW = set("il lo la le gli dei degli delle della del di e con per è in nel nella nei da dal una un su o".split())


def test(t, v):
    """t = {de, fr, it}; -> True / False / None (text missing)."""
    lang, kind, val = v
    if not t.get("de") or not t.get(lang): return None
    if kind == "is_fr":
        w = re.findall(r"\w+", t["it"].lower())
        return t["it"] == t["fr"] or sum(x in FRW for x in w) > sum(x in ITW for x in w)
    de, tg = core.gl2.numbers_in(t["de"], "de"), core.gl2.numbers_in(t[lang], lang)
    return (val in de and val not in tg) if kind == "lacks" else (val in tg and val not in de)


def present(t, tests):
    r = [test(t, v) for v in tests]
    return None if None in r else all(r)


def locate(S, cud, wb):
    """-> {capture: [variant]}; variant = dict(de, fr, it, method, where[, old_format]).
    2026 new-format snapshots: the CUD id itself. Earlier 2026 snapshots: per product holding the CUD at its first usable
    capture, the DE text is followed backwards through sl.mine's step matching (identical text, else the greedy pair = the
    predecessor the DE change replaced); FR/IT under the same key (old format: by product and position).
    2025 XML: LimitationCode == CUD id, else the same product's limitation with the nearest DE text (ratio <= 0.60)."""
    caps = {}
    new = [s for s in S.snaps if s > M.OLD_FORMAT_LAST]
    for s in [*new, "20260504"]:
        if not S.H.has(s): continue
        lim = {l: S.H(s, l)["lim"] for l in ("de", "fr", "it") if S.H.has(s, l)}
        get = lambda l: nrm(lim[l][cud]) if l in lim and cud in lim[l] else None
        caps[s] = [dict(de=get("de"), fr=get("fr"), it=get("it"), method="CUD id", where=cud)] if cud in lim["de"] else []
    anchor = next((s for s in new if caps.get(s)), None)
    if not anchor: return caps, None
    mpds = [m for m, p in S.H(anchor)["prod"].items() if cud in p["keys"]]
    names = sorted({(S.H(anchor)["prod"][m]["name"] or "").split(" ")[0].lower() for m in mpds} - {""})
    earlier = [s for s in S.snaps if s < anchor]
    for s in earlier: caps[s] = []
    lt_risk = any("<" in (caps[anchor][0][l] or "") for l in ("de", "fr", "it"))
    for m in mpds:
        cur, nxt = caps[anchor][0]["de"], anchor
        for s in reversed(earlier):
            P = S.bp(s)
            if m not in P: break
            T = P[m][1]
            g = cur if cur in T else S.back[(s, nxt, m)].get(cur)
            if g is None: break
            k = T[g]; v = dict(de=g, fr=S.tgt(s, "fr", m, k), it=S.tgt(s, "it", m, k), where=f"{m}:{k}",
                               method="identical DE text" if g == cur else f"predecessor: sl.mine paired it with the text of {nxt}")
            if s <= M.OLD_FORMAT_LAST:
                v["old_format"] = True
                if lt_risk: v["caveat"] = "old-format export drops '<...>' spans and this limitation contains '<' from June on: text may be truncated"
            caps[s].append(v); cur, nxt = g, s
    for s in earlier: caps[s] = _dedupe(caps[s])
    ref = caps[anchor][0]["de"]                            # new-format text: old-format ones may be truncated by the '<' bug
    first = next(s for s in S.snaps if caps.get(s))
    origin = None
    if first != S.snaps[0]:                                # introduced inside the window: nearest limitation of the same brand before it
        prev = S.snaps[S.snaps.index(first) - 1]; J = S.H(prev)
        keys = {k for m, p in J["prod"].items() if (p["name"] or "").split(" ")[0].lower() in names for k in p["keys"]}
        best = min(sorted(keys), key=lambda k: M.change_ratio(nrm(J["lim"][k]), ref), default=None)
        if best:
            m = next(m for m, p in J["prod"].items() if best in p["keys"])
            origin = dict(snapshot=prev, key=best, product=J["prod"][m]["name"], change_ratio=round(M.change_ratio(nrm(J["lim"][best]), ref), 3),
                          de=nrm(J["lim"][best]), fr=S.tgt(prev, "fr", m, best), it=S.tgt(prev, "it", m, best))
    for date, xml in wb:
        V = [dict(de=e["de"], fr=e["fr"], it=e["it"], method="xml LimitationCode", where=e["code"]) for e in xml.get(cud, [])]
        if not V and not origin:                           # history reaches Feb 2026: the same product's nearest 2025 text
            same = [e for es in xml.values() for e in es if e["product"].split(" ")[0].lower() in names and e["de"]]
            best = min(same, key=lambda e: M.change_ratio(e["de"], ref), default=None)
            if best and M.change_ratio(best["de"], ref) <= M.MAXRATIO:
                r = M.change_ratio(best["de"], ref)
                V = [dict(de=best["de"], fr=best["fr"], it=best["it"], where=best["code"],
                          method=f"xml: code absent; same product's nearest DE text (code {best['code']}, change ratio {r:.3f} to the first 2026 text)")]
        caps[date] = _dedupe(V)
    return caps, origin


def _dedupe(V):
    out = {}
    for v in V:
        k = (v["de"], v["fr"], v["it"])
        if k in out: out[k]["where"] += ", " + v["where"]
        else: out[k] = dict(v)
    return list(out.values())


_CO = {}
def _check_only(stack):
    if stack not in _CO: _CO[stack] = core.check_only(stack)
    return _CO[stack]


def gl_draft(S, x, recorded):
    """what Gleichlaut would have done with one DE change for one language (no model call)."""
    r = M.change_ratio(x["de_old"], x["de_new"]); d = dict(change_ratio=round(r, 3), route=M.route(r))
    if d["route"] == "human": return d
    rules, subs = core.gl2.rules(x["de_old"], x["de_new"], x["tgt_old"], x["lang"])
    pl = core.gl2.plan(x["de_old"], x["de_new"], x["tgt_old"], x["lang"])
    d.update(rules_out=rules, rules_subs=subs, rule_only=pl["rule_only"], model_windows=len(pl["windows"]))
    P = _check_only("g3")
    try:
        rec = P.run(x); d.update(model_called=False, draft=rec["out"], draft_source="rule-only (code)", flagged_g3=rec["guard_flag"])
    except RuntimeError:
        d.update(model_called=True, draft=None, draft_source="needs the model (not run here: no model calls in the backtest)")
    k = (x["lang"], x["de_old"], x["de_new"], x["tgt_old"])
    if k in recorded:
        run, item, f = recorded[k]
        d.update(recorded_run=run, recorded_key=item["key"], recorded_draft=f["out"], recorded_flag_v2=f["guard_flag"],
                 recorded_flag_g3_recheck=_check_only("g3").check(item, f["out"])["flag"])
    return d


def targeted(S, wb):
    recorded = {}
    for run in ("dev120", "oos242"):
        R = score.RUNS[run]; F = score.load_jsonl(R["final"])
        for x in score.load_items(R["items"]): recorded[(x["lang"], x["de_old"], x["de_new"], x["tgt_old"])] = (run, x, F[x["key"]])
    order = [d for d, _ in WB] + S.snaps
    res, texts = [], {}
    for case, cud, tests in CASES:
        caps, origin = locate(S, cud, wb); texts[cud] = {c: caps[c] for c in [*order, "20260504"] if c in caps}
        if "20260504" in texts[cud]:
            for v in texts[cud]["20260504"]: v["note"] = "excluded from the analysis: " + M.EXCLUDED["20260504"]
        tl = []
        for c in order:
            V = caps.get(c)
            if V is None: tl.append(dict(capture=c, located=None, note="capture not available (no 2025 XML given)")); continue
            if not V: tl.append(dict(capture=c, located=False)); continue
            tl.append(dict(capture=c, located=True, variants=len(V), methods=sorted({v["method"] for v in V}),
                           divergence=[present(v, tests) for v in V], **({"caveat": V[0]["caveat"]} if V[0].get("caveat") else {})))
        seen = [t for t in tl if t.get("located")]
        a = dict(earliest_capture=seen[0]["capture"] if seen else None)
        if seen:
            first_div = next((t for t in seen if any(t["divergence"])), None)
            dv = seen[0]["divergence"]
            a["present_in_earliest_capture"] = True if True in dv else (None if None in dv else False)
            a["first_capture_with_divergence"] = first_div and first_div["capture"]
            if first_div and first_div is not seen[0]:
                i = seen.index(first_div); p = seen[i - 1]["capture"]; c = first_div["capture"]
                A, Bv = caps[p][0], caps[c][0]
                a["appears_at_step"] = f"{p}>{c}"
                a["step_inside_2026_window"] = p in S.snaps and c in S.snaps
                a["de_changed_at_that_step"] = A["de"] != Bv["de"]
                a["target_changed_at_that_step"] = {l: A[l] != Bv[l] for l in LANGS}
            a["introduced_inside_2026_window"] = seen[0]["capture"] in S.snaps[1:]
            if a["introduced_inside_2026_window"] and a["present_in_earliest_capture"]:
                a["note"] = ("the limitation (or a traceable predecessor) first appears inside the window and is divergent from its first "
                             "publication: a new limitation, not an amendment of an existing one")
        # (b) today's texts against the DE
        b = {}
        cur = caps.get(S.snaps[-1]) or []
        if cur:
            t = cur[0]
            for lang in LANGS:
                n, vals = core.gl2.numbers_not_in_de(t[lang], t["de"], lang)
                de_n, tg_n = core.gl2.numbers_in(t["de"], "de"), core.gl2.numbers_in(t[lang], lang)
                b[lang] = dict(numbers_not_in_de=dict(count=n, values=vals),
                               de_numbers_missing_in_target=sorted(v for v in de_n if v not in tg_n),
                               slot_diff_de_vs_target=core.lock.slot_diff(core.lock.slots(t["de"], "de"), core.lock.slots(t[lang], lang)),
                               divergence_tests=[list(v) + [test(t, v)] for v in tests if v[0] == lang])
            b["catches"] = {f"{l} {k} {v}": _caught(b[l], k, v) for l, k, v in tests}
        # (c) DE changes of this limitation inside the window
        ch = []
        for p, c in zip(S.snaps, S.snaps[1:]):
            A, Bv = caps.get(p) or [], caps.get(c) or []
            if not A or not Bv or A[0]["de"] == Bv[0]["de"]: continue
            e = dict(step=f"{p}>{c}", divergence_before=present(A[0], tests), divergence_after_official=present(Bv[0], tests), langs={})
            if p <= M.OLD_FORMAT_LAST and ("<" in A[0]["de"] or "<" in Bv[0]["de"]):
                e["not_a_real_change"] = ("publisher bug: the old-format snapshot dropped a '<...>' span that the next snapshot has; "
                                          "sl.mine drops such pairs, so Gleichlaut would not have drafted anything here")
                a_, b_, ops = core.lock.de_ops(A[0]["de"], Bv[0]["de"]); e["de_edit"] = core.gl2.changes_list(a_, b_, ops)[:600]
                ch.append(e); continue
            for lang in LANGS:
                if not A[0][lang] or not Bv[0][lang]: e["langs"][lang] = dict(note="target text missing"); continue
                if p <= M.OLD_FORMAT_LAST and ("<" in A[0][lang] or "<" in Bv[0][lang]):
                    e["langs"][lang] = dict(note="publisher '<...>' bug in the target text (build_items drops it)"); continue
                x = dict(key=f"bt:{cud}:{lang}:{p}>{c}", lang=lang, de_old=A[0]["de"], de_new=Bv[0]["de"], tgt_old=A[0][lang], tgt_new=Bv[0][lang])
                g = gl_draft(S, x, recorded)
                for fld in ("rules_out", "draft", "recorded_draft"):
                    if g.get(fld): g["divergence_in_" + fld] = present(dict(Bv[0], **{lang: g[fld]}), [v for v in tests if v[0] == lang]) if any(v[0] == lang for v in tests) else None
                g["tgt_changed_officially"] = A[0][lang] != Bv[0][lang]
                for fld in ("rules_out", "draft", "recorded_draft"):
                    if g.get(fld): g[fld + "_equals_official"] = core.lock.norm(g[fld]) == core.lock.norm(Bv[0][lang])
                g["de_chars"] = max(len(x["de_old"]), len(x["de_new"]))
                if g["de_chars"] > M.MAXCH: g["pool_note"] = f"DE longer than {M.MAXCH} chars: sl.mine.build leaves it out of the item pool, so no recorded draft exists"
                e["langs"][lang] = g
            ch.append(e)
        r = dict(case=case, cud=cud, tests=[list(v) for v in tests], timeline=tl, a=a, b_current=b,
                 c_de_changes_in_window=ch or "no DE change of this limitation between consecutive usable 2026 snapshots")
        if origin:
            first = next(t["capture"] for t in tl if t.get("located") and t["capture"] in S.snaps)
            Bv = caps[first][0]; o = dict(origin, divergence=present(origin, tests),
                note="context only, not part of R3: the limitation is new in the window; its nearest existing limitation of the same brand "
                     "in the previous snapshot is treated as the old text, to show what an amendment-style draft from it would have been")
            for lang in LANGS:
                if origin[lang] and Bv[lang]:
                    x = dict(key=f"bt:{cud}:{lang}:origin", lang=lang, de_old=origin["de"], de_new=Bv["de"], tgt_old=origin[lang], tgt_new=Bv[lang])
                    g = gl_draft(S, x, recorded); tl_ = [v for v in tests if v[0] == lang]
                    for fld in ("rules_out", "draft"):
                        if g.get(fld) and tl_: g["divergence_in_" + fld] = present(dict(Bv, **{lang: g[fld]}), tl_)
                    o[lang + "_draft"] = g
            r["origin_context"] = o; texts[cud]["origin_" + origin["snapshot"]] = [dict(de=origin["de"], fr=origin["fr"], it=origin["it"],
                                                                                        method="nearest existing limitation (context)", where=origin["key"])]
        res.append(r)
    return res, texts


def _caught(bl, kind, val):
    if kind == "adds": return dict(numbers_not_in_de=val in bl["numbers_not_in_de"]["values"],
                                   slot_diff_mentions=any(val in s for s in bl["slot_diff_de_vs_target"]))
    if kind == "lacks": return dict(numbers_not_in_de=False, note="the check only looks for target numbers absent from the DE; a number "
                                    "the target drops is not its target", slot_diff_mentions=any(val in s for s in bl["slot_diff_de_vs_target"]))
    return dict(numbers_not_in_de=False, slot_diff_mentions=False, note="no numeric signal: the Italian slot carries the French text")


def _dump(obj, path):
    with open(path, "w", encoding="utf-8") as f: json.dump(obj, f, ensure_ascii=False, indent=1)
    print("wrote", os.path.relpath(path, core.ROOT), f"{os.path.getsize(path) / 1e3:.0f} kB", file=sys.stderr)


def main(argv=None):
    ap = argparse.ArgumentParser(description="M6 backtest (PREREG R3)")
    ap.add_argument("--hist"); ap.add_argument("--wb2025"); ap.add_argument("--out", default=DEST)
    a = ap.parse_args(argv)
    hist = hist_dir(a.hist); wbd = a.wb2025 or os.environ.get("GLEICHLAUT_WB2025") or os.path.join(OUT, "wb2025")
    gen = "PYTHONPATH=src python3 -m gleichlaut.backtest --hist <2026 snapshot dir> --wb2025 <2025 XML dir>"
    H = M.Hist(hist); missing = [s for s in M.SNAPS for l in ("de", "fr", "it") if not H.has(s, l)]
    if missing: raise SystemExit(f"missing snapshots in {hist}: {missing[:6]}")
    core.verify_freeze()
    S = Snaps(H); C = M.mine(H, log=False)
    wb = []
    for d, sub in WB:
        p = os.path.join(wbd, sub, "Preparations.xml")
        if os.path.exists(p): wb.append((d, load_xml(p)))
        else: print("no 2025 capture at", p, file=sys.stderr)
    os.makedirs(a.out, exist_ok=True)
    home = lambda q: q.replace(os.path.expanduser("~"), "~")
    inputs = {f"{s}-{l}.json": core.sha256(os.path.join(hist, f"{s}-{l}.json")) for s in M.SNAPS for l in ("de", "fr", "it")}
    inputs.update({f"{sub}/Preparations.xml": core.sha256(os.path.join(wbd, sub, "Preparations.xml")) for d, sub in WB if d in dict(wb)})
    common = dict(generated_by=gen, inputs=dict(hist=home(os.path.abspath(hist)), wb2025=home(os.path.abspath(wbd)), sha256=inputs),
                  prereg="eval/prereg/PREREG.md R3", snapshots=M.SNAPS, excluded=M.EXCLUDED, wb2025=[d for d, _ in wb], model_calls=0)
    L = lag(S, C)
    _dump(dict(common, vision_figures_check=vision_check(C, S), summary={k: v["summary"] for k, v in L["units"].items()},
               per_step=L["per_step"], draft_not_same_step=L["cases"].get("draft_not_same_step", []),
               rows={k: v["rows"] for k, v in L["units"].items()},
               definitions=dict(unit="distinct (step, DE old text, DE new text) found by sl.mine; occurrences = its products/keys",
                                draft="<= 60% of DE tokens changed (sl.mine's change); human = > 60% rewrite",
                                same_step="the FR/IT text under the same key changed in the same step",
                                lagged="FR/IT unchanged in that step, changed in a later snapshot (fixed_at; days/steps). A later "
                                       "change is not verified to implement the DE change",
                                never="FR/IT unchanged until the end of the window, or until the DE text/product disappeared",
                                target_missing="no FR/IT text under the key (or positional alignment failed for old-format keys)",
                                lt_bug="old-format snapshot and a '<' in the FR/IT text (publisher bug, untrustworthy)")),
          os.path.join(a.out, "lag.json"))
    _dump(dict(common, **since_feb(S, C)), os.path.join(a.out, "since_feb.json"))
    T, X = targeted(S, wb)
    _dump(dict(common, cases=T), os.path.join(a.out, "targeted5.json"))
    _dump(dict(common, note="DE/FR/IT texts (nrm-normalised; 2025 XML through the frozen exporter emulation) per capture; "
                            "several variants when products disagree", texts=X), os.path.join(a.out, "known_errors_texts.json"))


if __name__ == "__main__":
    main()
