"""Replay scorer for the Fedlex lane: re-scores the recorded MLX-DWQ 8B outputs with the vendored research scorer
(research/score.py, executed whole, not re-implemented) and checks every headline number of
spikes/gleichschritt/results.md. Also replays the recorded raw generations through the shipped loop (lane.py).

usage: PYTHONPATH=src python3 -m gleichlaut.fed.score [--worklist DIR]   -> eval/results/fedlex.json (+ fedlex_scores.json);
       exit 1 on any mismatch. --worklist writes the blind annotation list of unflagged non-exact shipped drafts."""
import contextlib, io, json, os, shutil, sys, tempfile
from collections import Counter
from .. import core
from ..core import lock, sha256
from . import lane

OUT = os.path.join(core.ROOT, "eval", "results", "fedlex.json")
OUT_ROWS = os.path.join(core.ROOT, "eval", "results", "fedlex_scores.json")
CONTAM = os.path.join(lane.DATA, "items", "fedlex_rm_contamination.json")
RESEARCH_SCORES_SHA = "43b170708d4c3a6b94d85642cd639261c7825ddd5a9630ecd3d71b5ba1c33f23"   # spikes/gleichschritt/results/scores.json
ISECS = ("secs", "secs1", "secs2")


def jl(p):
    with open(p, encoding="utf-8") as f: return {r["key"]: r for r in map(json.loads, f)}


def research_scores():
    """Stage the copied inputs under the research file names and exec research/score.py; its main() writes scores.json.
    -> (scores dict, printed table, sha256 of the scores.json bytes)."""
    d = tempfile.mkdtemp(prefix="gleichschritt-"); os.makedirs(os.path.join(d, "results"))
    try:
        for src, dst in ((lane.ITEMS, "items.json"), (lane.RUN_A, "results/A.jsonl"), (lane.RUN_B, "results/B.jsonl"),
                         (CONTAM, "results/s2_contamination.json")): shutil.copyfile(src, os.path.join(d, dst))
        path = os.path.join(lane.RES, "score.py")
        ns = {"__name__": "gleichschritt_score", "__file__": os.path.join(d, "score.py")}
        buf = io.StringIO()
        with open(path, encoding="utf-8") as f: code = compile(f.read(), path, "exec")
        try:
            exec(code, ns)    # `import lock` -> the frozen lock (already imported)
            assert ns["lock"] is lock, ns["lock"].__file__
            with contextlib.redirect_stdout(buf): ns["main"]()
        finally:
            if d in sys.path: sys.path.remove(d)
        p = os.path.join(d, "results", "scores.json")
        return lane.load(p), buf.getvalue(), sha256(p)
    finally:
        shutil.rmtree(d, ignore_errors=True)


class Replay:
    """Fake backend: hands back recorded generations in order and records the prompts it was sent."""
    def __init__(self, texts): self.q, self.prompts, self.max_tokens = list(texts), [], []
    def __call__(self, prompt, tag, cap, max_tokens):
        assert self.q, "the loop asked the model more often than the recorded run did"
        self.prompts.append(prompt); self.max_tokens.append(max_tokens)
        return self.q.pop(0), {"model_served": "replay:8b_dwq_fedlex", "cached": True}


def _raws(rec): return [rec["raw1"]] + ([rec["raw2"]] if rec.get("retried") else [])


def replay_record(x, rec):
    """the shipped lane (fed_draft) fed with the recorded raw outputs."""
    rp = Replay(_raws(rec)); r = lane.fed_draft(x, rp); r["unused_raw"] = len(rp.q)
    return r


def replay_check(items=None, A=None, B=None, rows=None):
    """The rigour step. (1) as-run: gleich.py run_A, executed with a fake ask that returns the recorded raw1/raw2, must
    rebuild every recorded field of every A record (out1, check1, retry decision, out2, check2, out, flags); the retry
    prompt must equal the first prompt + RETRY filled from the recorded check1. (2) shipped: fed_draft (code lane, then
    corrected arm A, slot guard) on the same recorded raws must give exactly the research scorer's "A+code" rows.
    (3) arm B: run_B on the recorded raw must give the recorded out."""
    items = items or {x["key"]: x for x in lane.load(lane.ITEMS)}
    A, B = A or jl(lane.RUN_A), B or jl(lane.RUN_B)
    if rows is None: rows = research_scores()[0]["rows"]
    AC = {r["key"]: r for r in rows if r["arm"] == "A+code"}
    bad, n = [], Counter()
    for k, rec in A.items():
        x = items[k]
        rp = Replay(_raws(rec)); r = lane.arm_a(x, rp)
        want = {a: b for a, b in rec.items() if a not in ISECS}
        got = {a: b for a, b in r.items() if a not in ISECS + ("calls",)}
        if got != want: bad.append((k, "asrun", sorted(a for a in want if want[a] != got.get(a))))
        if rp.q: bad.append((k, "asrun", "unused recorded raw"))
        p0 = lane.PA.format(L=lane.LNAME[x["lang"]], de_old=x["de_old"], de_new=x["de_new"],
                            changes=lane.changes_list(x["de_old"], x["de_new"]), tgt_old=x["tgt_old"])
        if rp.prompts[0] != p0: bad.append((k, "prompt1"))
        if rec["retried"]:
            b = "; ".join(f"«{a}» -> «{c}»" for a, c in rec["check1"]["outside"][:4])
            if rp.prompts[1] != p0 + lane.RETRY.format(prev=rec["out1"], L=lane.LNAME[x["lang"]], bad=b): bad.append((k, "prompt2"))
        n["asrun"] += 1; n["asrun_retried"] += rec["retried"]
        s = replay_record(x, rec); row = AC[k]
        if (lock.norm(s["out"]), s["flagged_research"], s["guard"]) != (row["out"], row["flagged"], row["guard"]): bad.append((k, "shipped"))
        n["shipped"] += 1; n["shipped_code_lane"] += s["lane"] == "code"; n["shipped_retried"] += s["retried"]
        n["shipped_unused_recorded_retry"] += s["lane"] == "model" and s["unused_raw"]
        if s["retried"]:                    # the corrected lock words its complaint on normalised text
            n["shipped_retry_prompt_differs_from_recorded"] += s["calls"][1]["prompt"] != rp.prompts[1] if len(rp.prompts) > 1 else 0
    for k, rec in B.items():
        r = lane.arm_b(items[k], Replay([rec["raw"]]))
        if (r["raw"], r["out"]) != (rec["raw"], rec["out"]): bad.append((k, "armB"))
        n["armB"] += 1
    return dict(n=dict(n), mismatches=bad, ok=not bad)


# ---------------------------------------------------------------- results.md headline numbers
# results.md §2 table: group|arm -> n, exact, strict, edit-F1, chrF, 0 chars outside, out-of-span chars, flagged, flips, unflagged flips, s/par
TABLE = """fr|A 60 50.0 50.0 69.5 89.1 90 4.7 17 6.7 0.0 6.8
fr|B 60 0.0 0.0 32.9 63.0 12 65.2 0 20.0 20.0 4.5
it|A 60 50.0 50.0 75.9 89.8 93 1.8 8 3.3 1.7 6.7
it|B 60 0.0 0.0 30.8 57.4 10 82.2 0 23.3 23.3 4.7
fr+it|A 120 50.0 50.0 72.7 89.4 92 3.2 12 5.0 0.8 6.7
fr+it|B 120 0.0 0.0 31.8 60.2 11 73.7 0 21.7 21.7 4.6
fr+it-noSEFRI|A 82 28.0 28.0 60.2 84.6 88 4.7 18 7.3 1.2 7.0
fr+it-noSEFRI|B 82 0.0 0.0 34.9 58.5 16 84.0 0 31.7 31.7 4.5
rm|A 30 26.7 26.7 65.9 91.2 87 2.5 17 13.3 3.3 8.5
rm|B 30 0.0 0.0 38.6 69.8 3 64.8 0 23.3 23.3 5.5
rm-clean|A 11 36.4 - 57.1 90.3 91 0.5 18 9.1 0.0 9.2
rm-contam|A 11 0.0 - 55.9 92.2 82 0.7 18 27.3 9.1 10.8"""
COLS = (("n", "{:d}", 1), ("exact", "{:.1f}", 100), ("exact_strict", "{:.1f}", 100), ("edit_f1", "{:.1f}", 1), ("chrf", "{:.1f}", 1),
        ("zero_outside", "{:.0f}", 100), ("outside_chars_mean", "{:.1f}", 1), ("flagged", "{:.0f}", 100), ("flips", "{:.1f}", 100),
        ("unflagged_flips", "{:.1f}", 100), ("secs", "{:.1f}", 1))


def frac(a, b): return f"{a}/{b}"


def derived(sc, A):
    """counts quoted in the results.md prose (verdict, §2 code lane / lock and retry / flips, §6)."""
    R = {(r["key"], r["arm"]): r for r in sc["rows"]}; C = {c["key"]: c for c in sc["code"]}
    Ak = [k for k, a in R if a == "A"]
    fi = [k for k in Ak if R[k, "A"]["lang"] in lane.SCOPE]; rm = [k for k in Ak if R[k, "A"]["lang"] == "rm"]
    ex = lambda ks, arm="A": sum(R[k, arm]["exact"] for k in ks)
    fi_code = [k for k in fi if C[k]["applicable"]]; fi_model = [k for k in fi if not C[k]["applicable"]]
    rm_model = [k for k in rm if not C[k]["applicable"]]; src = lambda ks, s: [k for k in ks if R[k, "A"]["src"] == s]
    unfl = lambda ks: [k for k in ks if not R[k, "A"]["flagged"]]; fl = lambda ks: [k for k in ks if R[k, "A"]["flagged"]]
    sefri = [k for k in fi if R[k, "A"]["cluster"]]; rt = [k for k in Ak if R[k, "A"]["retried"]]; S = sc["summary"]
    d = {
        "FR/IT exact (A)": frac(ex(fi), len(fi)),
        "FR/IT exact without SEFRI (A)": frac(ex([k for k in fi if k not in sefri]), len(fi) - len(sefri)),
        "SEFRI cluster items / exact": frac(ex(sefri), len(sefri)),
        "RM exact (A)": frac(ex(rm), len(rm)),
        "FR/IT code lane applicable": len(fi_code),
        "FR/IT code lane exact = A exact on those": f"{sum(C[k]['exact'] for k in fi_code)}/{len(fi_code)} = {ex(fi_code)}/{len(fi_code)}",
        "FR/IT code-lane exact items where A is also exact": frac(sum(C[k]["exact"] and R[k, "A"]["exact"] for k in fi_code), sum(C[k]["exact"] for k in fi_code)),
        "FR/IT model-lane exact (A)": frac(ex(fi_model), len(fi_model)),
        "FR/IT model-lane exact that are SEFRI": sum(R[k, "A"]["exact"] and R[k, "A"]["cluster"] for k in fi_model),
        "RM model-written exact": frac(ex(rm_model), len(rm_model)),
        "RM federal exact (A)": frac(ex(src(rm, "fed")), len(src(rm, "fed"))),
        "RM federal exact by code lane": sum(C[k]["exact"] for k in src(rm, "fed")),
        "RM Graubuenden exact (A)": frac(ex(src(rm, "gr")), len(src(rm, "gr"))),
        "RM Graubuenden model-written exact": frac(ex(src(rm_model, "gr")), len(src(rm_model, "gr"))),
        "RM code-lane exact items where A is also exact": frac(sum(C[k]["exact"] and R[k, "A"]["exact"] for k in rm if C[k]["applicable"]), sum(C[k]["exact"] for k in rm)),
        "code lane FR": frac(sum(C[k]["exact"] for k in fi if R[k, "A"]["lang"] == "fr"), 60),
        "code lane IT": frac(sum(C[k]["exact"] for k in fi if R[k, "A"]["lang"] == "it"), 60),
        "code lane RM": frac(sum(C[k]["exact"] for k in rm), len(rm)),
        "code lane applicable FR/IT/RM": "/".join(str(sc["code_lane"][l]["applicable"]) for l in ("fr", "it", "rm")),
        "gold inside lock windows FR/IT/RM": " ".join(frac(*sc["gold_fit"][l]) for l in ("fr", "it", "rm")),
        "FR/IT unflagged exact (A)": frac(ex(unfl(fi)), len(unfl(fi))),
        "RM unflagged exact (A)": frac(ex(unfl(rm)), len(unfl(rm))),
        "FR/IT flagged exact (A)": frac(ex(fl(fi)), len(fl(fi))),
        "A flip hits (FR/IT + RM), adjudicated by hand": sum(bool(R[k, "A"]["flip"]) for k in Ak),
        "A unflagged flip hits FR/IT / RM": f"{sum(bool(R[k, 'A']['flip']) and not R[k, 'A']['flagged'] for k in fi)}/{len(fi)} {sum(bool(R[k, 'A']['flip']) and not R[k, 'A']['flagged'] for k in rm)}/{len(rm)}",
        "retries / fixed / retry identical to first output (corrected lock)": "{} / {} / {}".format(
            len(rt), sum(A[k]["lock_ok"] for k in rt), sum(A[k]["out2"] == A[k]["out1"] for k in rt)),
        "edit-F1 A-B FR/IT, of the rounded table values": f"{round(S['fr+it|A']['edit_f1'], 1) - round(S['fr+it|B']['edit_f1'], 1):+.1f}",
        "edit-F1 A-B RM, of the rounded table values": f"{round(S['rm|A']['edit_f1'], 1) - round(S['rm|B']['edit_f1'], 1):+.1f}",
        "A-asrun FR/IT flagged": f"{100 * sc['summary']['fr+it|A-asrun']['flagged']:.0f}%",
        "A-asrun IT strict exact": f"{100 * sc['summary']['it|A-asrun']['exact_strict']:.0f}%",
        "A+code FR/IT exact, s/paragraph": f"{100 * sc['summary']['fr+it|A+code']['exact']:.1f}% {sc['summary']['fr+it|A+code']['secs']:.1f}",
        "B exact FR/IT": f"{100 * sc['summary']['fr+it|B']['exact']:.1f}%",
    }
    return d


EXPECT = {   # results.md, quoted
    "FR/IT exact (A)": "60/120", "FR/IT exact without SEFRI (A)": "23/82", "SEFRI cluster items / exact": "37/38", "RM exact (A)": "8/30",
    "FR/IT code lane applicable": 48, "FR/IT code lane exact = A exact on those": "42/48 = 42/48",
    "FR/IT code-lane exact items where A is also exact": "42/42", "FR/IT model-lane exact (A)": "18/72",
    "FR/IT model-lane exact that are SEFRI": 6, "RM model-written exact": "1/22", "RM federal exact (A)": "7/10",
    "RM federal exact by code lane": 6, "RM Graubuenden exact (A)": "1/20", "RM Graubuenden model-written exact": "0/19",
    "RM code-lane exact items where A is also exact": "7/7", "code lane FR": "21/60", "code lane IT": "21/60", "code lane RM": "7/30",
    "code lane applicable FR/IT/RM": "24/24/8", "gold inside lock windows FR/IT/RM": "45/60 48/60 15/30",
    "FR/IT unflagged exact (A)": "57/105", "RM unflagged exact (A)": "8/25", "FR/IT flagged exact (A)": "3/15",
    "A flip hits (FR/IT + RM), adjudicated by hand": 10, "A unflagged flip hits FR/IT / RM": "1/120 1/30",
    "retries / fixed / retry identical to first output (corrected lock)": "14 / 0 / 11",
    "edit-F1 A-B FR/IT, of the rounded table values": "+40.9", "edit-F1 A-B RM, of the rounded table values": "+27.3",
    "A-asrun FR/IT flagged": "21%", "A-asrun IT strict exact": "13%", "A+code FR/IT exact, s/paragraph": "50.0% 4.2", "B exact FR/IT": "0.0%",
}


def notes(sc, A):
    """Where results.md wording and the recomputation part ways (none of them moves a headline)."""
    S = sc["summary"]; ar = [a for a in A.values() if a["retried"]]
    return {
        "as-run retries": f"The Air run itself retried {len(ar)} items ({sum(a['lock_ok'] for a in ar)} fixed, "
            f"{sum(a['out2'] == a['out1'] for a in ar)} identical to the first output; raw/gleich_air.log: {len(ar)} FLAG lines). "
            "results.md's '14 retries' (Setup and §2) is the count under the corrected, apostrophe-normalised lock that the "
            "reported numbers use; the Setup sentence '150 arm-A items (plus 14 retries)' should read 25 for the as-run timing.",
        "edit-F1 RM gap": f"exact difference {S['rm|A']['edit_f1'] - S['rm|B']['edit_f1']:+.2f} (+27.2 at one decimal); results.md's "
            "+27.3 subtracts the rounded 65.9 and 38.6. FR/IT: "
            f"{S['fr+it|A']['edit_f1'] - S['fr+it|B']['edit_f1']:+.2f}.",
    }


def checks(sc, A):
    out = []
    for line in TABLE.splitlines():
        g, *v = line.split(); s = sc["summary"][g]
        for (col, fmt, mul), want in zip(COLS, v):
            if want == "-": continue
            got = fmt.format(int(s[col]) if col == "n" else s[col] * mul)
            out.append(dict(claim=f"{g} {col}", expected=want, got=got, ok=got == want))
    for k, v in derived(sc, A).items():
        out.append(dict(claim=k, expected=EXPECT[k], got=v, ok=v == EXPECT[k]))
    return out


SHIPPED_LABEL = "shipped lane = A+code + lock + slot + G1–G4 (DEV: guard choice made after seeing these outputs)"


def shipped(items=None, A=None):
    """The shipped verdict on the recorded run: fed_draft (code lane, corrected arm A, lock, slot guard, G1-G4) replayed
    on every recorded FR/IT A record. DEV: G1-G4 were added to this lane after these outputs had been read."""
    items = items or {x["key"]: x for x in lane.load(lane.ITEMS)}
    A = A or jl(lane.RUN_A)
    R = [dict(replay_record(items[k], rec), lang=items[k]["lang"]) for k, rec in A.items() if items[k]["lang"] in lane.SCOPE]
    def agg(rs):
        n = len(rs); c = lambda f: sum(1 for r in rs if f(r))
        return dict(n=n, exact=c(lambda r: r["exact"]), flagged=c(lambda r: r["flagged"]), ready=c(lambda r: not r["flagged"]),
                    exact_flagged=c(lambda r: r["exact"] and r["flagged"]), ready_exact=c(lambda r: r["exact"] and not r["flagged"]),
                    flagged_research=c(lambda r: r["flagged_research"]),
                    newly_flagged_by_g1_g4=c(lambda r: r["flagged"] and not r["flagged_research"]),
                    newly_flagged_exact=c(lambda r: r["exact"] and r["flagged"] and not r["flagged_research"]),
                    g14_hits={g: c(lambda r, g=g: bool(r["g14"][g])) for g in ("g1", "g2", "g3", "g4")})
    out = dict(label=SHIPPED_LABEL, all=agg(R), **{l: agg([r for r in R if r["lang"] == l]) for l in lane.SCOPE})
    out["unflagged_non_exact_keys"] = sorted(r["key"] for r in R if not r["flagged"] and not r["exact"])
    out["newly_flagged_keys"] = sorted(r["key"] for r in R if r["flagged"] and not r["flagged_research"])
    return out, {r["key"]: r for r in R}


def annotation_worklist(out_dir, sh=None, R=None, seed=7):
    """Blind worklist of the unflagged non-exact shipped drafts: shuffled with random.Random(seed), ids F00.. ; the
    id -> key map goes to a separate file that annotators must not see."""
    import random
    if sh is None: sh, R = shipped()
    items = {x["key"]: x for x in lane.load(lane.ITEMS)}
    keys = list(sh["unflagged_non_exact_keys"]); random.Random(seed).shuffle(keys)
    W, M = [], {}
    for i, k in enumerate(keys):
        x = items[k]; fid = f"F{i:02d}"; M[fid] = k
        W.append(dict(id=fid, lang=x["lang"], de_old=x["de_old"], de_new=x["de_new"], tgt_old=x["tgt_old"], draft=R[k]["out"],
                      official_new=x["tgt_new"]))
    os.makedirs(out_dir, exist_ok=True)
    for f, d in (("worklist.json", W), ("key_map_DO_NOT_SHOW.json", M)):
        with open(os.path.join(out_dir, f), "w", encoding="utf-8") as fh: json.dump(d, fh, ensure_ascii=False, indent=1)
    return W, M


def main():
    lane.verify()
    sc, table, sha = research_scores()
    A = jl(lane.RUN_A)
    C = checks(sc, A)
    rp = replay_check(A=A, rows=sc["rows"])
    S = sc["summary"]; pct = lambda g, c: round(100 * S[g][c], 1)
    res = dict(
        source="spikes/gleichschritt/results.md (8 Oct 2026); model Apertus v1.5 8B text, MLX 4-bit DWQ "
               "(m1rkocasu/Apertus-v1.5-8B-text-MLX-4bit-DWQ), greedy, M2 Air. Not the GGUF that `make run` ships.",
        command="PYTHONPATH=src python3 -m gleichlaut.fed.score",
        inputs={p: sha256(os.path.join(core.ROOT, p)) for p in ("data/items/fedlex_items.json", "data/items/fedlex_rm_contamination.json",
                                                                "data/runs/8b_dwq_fedlex_A.jsonl", "data/runs/8b_dwq_fedlex_B.jsonl")},
        research_scorer=dict(file="src/gleichlaut/fed/research/score.py", sha256=sha256(os.path.join(lane.RES, "score.py"))),
        scores_json_sha256=sha, scores_json_identical_to_research=sha == RESEARCH_SCORES_SHA,
        headline={"FR/IT exact, shipped lane (A+code)": pct("fr+it|A+code", "exact"), "FR/IT exact (A)": pct("fr+it|A", "exact"),
                  "FR/IT exact without SEFRI (A)": pct("fr+it-noSEFRI|A", "exact"),
                  "FR exact (A)": pct("fr|A", "exact"), "IT exact (A)": pct("it|A", "exact"),
                  "code lane alone FR/IT exact": round(100 * (sc["code_lane"]["fr"]["exact"] + sc["code_lane"]["it"]["exact"]) / 120, 1),
                  "free translation (B) FR/IT exact": pct("fr+it|B", "exact"), "free translation (B) FR lexicon flips": pct("fr|B", "flips"),
                  "free translation (B) IT lexicon flips": pct("it|B", "flips"),
                  "FR/IT flagged (A)": pct("fr+it|A", "flagged"), "FR/IT unflagged lexicon flips (A)": pct("fr+it|A", "unflagged_flips"),
                  "FR/IT flagged, shipped lane (A+code)": pct("fr+it|A+code", "flagged"),
                  "FR/IT unflagged lexicon flips, shipped lane (A+code)": pct("fr+it|A+code", "unflagged_flips"),
                  "real unflagged flips, by hand (A, FR/IT/RM)": "0/150 (hand adjudication of the 10 flip hits; not recomputable)",
                  "s/paragraph A, A+code (FR/IT)": [round(S["fr+it|A"]["secs"], 1), round(S["fr+it|A+code"]["secs"], 1)],
                  "RM exact (A), exploratory": pct("rm|A", "exact")},
        summary=S, code_lane=sc["code_lane"], gold_fit=sc["gold_fit"], derived=derived(sc, A), notes=notes(sc, A),
        checks=C, n_checks=len(C), all_checks_ok=all(c["ok"] for c in C), replay=rp, research_table=table)
    sh, R = shipped(A=A)
    res[SHIPPED_LABEL] = sh
    if "--worklist" in sys.argv: annotation_worklist(sys.argv[sys.argv.index("--worklist") + 1], sh, R)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    for p, d in ((OUT, res), (OUT_ROWS, sc)):
        with open(p, "w", encoding="utf-8") as f: json.dump(d, f, ensure_ascii=False, indent=1)
    print(table, end="")
    for c in C:
        if not c["ok"]: print("MISMATCH", c)
    print(f"fedlex: {sum(c['ok'] for c in C)}/{len(C)} results.md numbers reproduced; scores.json identical to research: "
          f"{res['scores_json_identical_to_research']}; replay {rp['n']} mismatches {len(rp['mismatches'])}")
    return 0 if res["all_checks_ok"] and rp["ok"] and res["scores_json_identical_to_research"] else 1


if __name__ == "__main__":
    sys.exit(main())
