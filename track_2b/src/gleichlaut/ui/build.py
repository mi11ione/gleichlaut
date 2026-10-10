"""python3 -m gleichlaut.ui.build [--run q8_0 | fresh166 | q8_0_rerun | ... | --records R.jsonl --items I.json] [--out PATH]
                                 [--fragment] [--audit data/audit/audit_20261006.json] [--hist DIR]

One self-contained HTML review page (inline CSS/JS/data and embedded fonts; no request at view time; works from
file://) with two views shown as one system: "Register audit" (code only; the landing view, #audit) and "Drafts"
(Apertus drafts, code checks; #drafts, #wbNNN opens a draft), each tab with its count.
Lanes: without --run / --records the page carries the drafts of every lane of LANES, each as its own JSON block, and
parses only the one it shows: the default SL lane first (the certified Apertus 8B GGUF Q8_0 run on CPU over the
held-out set, score.RUNS["q8_0"] = data/runs/8b_q8_0_fresh166_g3_final.jsonl, figures from score.m1("q8_0") as in its
build certificate), then the optional 70B endpoint lane on the same changes ("fewer edits"; score.RUNS["fresh166"]),
then the default 8B on the two live months (the shadow records of data/shadow/<month>/q8_0 over the public feed). A
select in the drafts context line switches lanes; the hash carries a lane other than the default as a prefix (#70b,
#70b/wb013, #aug2026/drafts) so that #wbNNN keeps working on whichever lane is shown; decisions are stored per run.
The context line names the lane and its figures from the run shown (ready, flagged, identical to BAG's published text:
the scored summary of a recorded run, else the counts of the records). With --run or --records the page has that one
run (python3 -m gleichlaut.ui.build --run q8_0_rerun works: emit.MODEL names the 8B GGUF of the Q8_0 runs).
"Register audit": one row per finding of the pre-existing DE/FR/IT audit (ui/audit_view.py), the conflicting statements
side by side, and the officer's two decisions (which language is right; correct ex officio / raise with the holder in the
triennial review / language service / no action / unclear) with a note and the reviewer's name, keyed by the finding's
signature so they carry over to the next audit run; likely-equivalent number findings collapsed under their own heading,
terminology notices (old and new term, where BAG already corrected it) in their own group and counted apart, as in the
README (27 findings + 11 terminology notices, from eval/results/audit.json and audit_more.json). "Drafts": a register of
German changes on the left, numbered by their address (wbNNN), and the case under review on the right (German change,
FR/IT drafts editable in place, the per-draft explanation, decision). The explanation shows at most three reasons, most
actionable first, in plain wording in the reviewer's language without internal codes (xliff.reasons, the same as the
XLIFF notes), labelled "explanation (FR/IT)", then, apart from those three, one grey line of low-priority notes (a deletion
that mirrors the German's, typography the draft introduced, the house-sentence advisory when a fixed German sentence is
written otherwise than BAG's dominant wording, the termbase advisory when the draft departs from BAG's house rendering of
a German term; xliff.explanation); the full checks ledger with its codes is collapsed below. The header of a flagged
draft ("n issues to check, m probably fine") counts what that list shows (xliff.counts), and the register's three-level
mark follows it (to check when one item is). Compact legends
sit next to the marks they explain. Diffs, number provenance and the plain-language guard findings are computed
here in Python from the same per-item views the emitters use (gleichlaut.emit.load); the header figures come from
score.score_run(run)["summary"]["all"] (score.m1 for q8_0; counts only for --records) and, for the audit, eval/results/audit.json.
Flag triage (emit/triage.py, rules T1-T8) and the reworded reasons (xliff.reasons) only order and collapse findings and
split the flagged drafts into "to check" and "all findings probably fine" for display; pre-existing problems of the old text are a display notice ("ready
(old text needs attention)"); neither changes a verdict or a metric. A flagged draft can be restarted from the old text
plus the rules lane's number changes (core.gl2.rules); a family's open ready drafts can be accepted at once after an
in-page confirmation. Reviewer decisions stay in the browser (localStorage) and leave it through the one "Export
decisions (JSON)" control in the title block (the system of record is ePL and the XLIFF round trip, not the page), and
through Export XLIFF 2.1 / XLIFF 1.2 / Export CSV / Copy decisions; Import decisions loads an exported JSON back.
--fragment writes the page without <!doctype>/<html>/<head>/<body> (title + style + content + script) for publishing as
a claude.ai artifact; the default output is a complete standalone HTML document."""
import argparse, base64, difflib, html, json, os, re
from collections import Counter
from .. import core, score
from ..emit import explain, load, model_label, segment, triage, xliff
from ..emit.segment import SENT_END, sentences          # noqa: F401  (one sentence splitter for page and XLIFF)
from . import audit_view

OUT = os.path.join(core.ROOT, "out", "ui", "index.html")
FONTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
TOK = re.compile(core.gl2.NUMRX.pattern + r"|\w+|\s+|[^\w\s]")        # numbers first: a number is one token
WHOLE = 0.40          # a sentence block with more than this share of changed words is shown old-struck / new-underlined
LABEL = {"fresh166": "held-out set (SL changes 06.2025–02.2026)", "m3_seed1": "held-out set, rerun seed 1", "oos242": "out-of-sample 2026 set",
         "dev120": "development set (in-sample)", "dev120_8b": "development set, 8B", "q8_0": "held-out set (SL changes 06.2025–02.2026)",
         "q8_0_rerun": "held-out set, 8B Q8_0 rerun"}
PERIOD = {"fresh166": "06.2025–02.2026", "m3_seed1": "06.2025–02.2026", "q8_0": "06.2025–02.2026",
          "q8_0_rerun": "06.2025–02.2026"}      # the SL changes a recorded run drafts (drafts banner)
# Header figures of a recorded run: score.score_run(run)["summary"]; the certified 8B run is scored with its blind labels
# (eval/labels/m1_q8_0_fresh166.tsv plus the labels inherited from identical outputs: score.m1), as in the certificate.
SUMMARY = {"q8_0": lambda: dict(all=score.m1("q8_0"))}
_SH = "data/shadow/{m}/q8_0/{f}"
# The drafts the default page carries, one lane each; the first is the one the Drafts tab opens with: the default SL lane
# (Apertus 8B GGUF Q8_0 on CPU, the certified run on the held-out set), then the optional 70B endpoint lane on the same
# changes ("fewer edits"), then the default 8B on the two live months (shadow runs over the public feed after BAG had
# published; BAG's FR/IT never shown to the model). The page parses only the lane it shows (#70b/..., #aug2026/...).
LANES = (dict(id="8b", run="q8_0"), dict(id="70b", run="fresh166"),
         dict(id="aug2026", records=_SH.format(m="20260801-20260901", f="records.jsonl"), items="data/shadow/20260801-20260901/items.json",
              live="08.2026", span=("01.08.2026", "01.09.2026"), label="live month 08.2026 (SL 01.08.2026 → 01.09.2026)", name="shadow_20260801-20260901_q8_0"),
         dict(id="sep2026", records=_SH.format(m="20260901-20261001", f="records.jsonl"), items="data/shadow/20260901-20261001/items.json",
              live="09.2026", span=("01.09.2026", "01.10.2026"), label="live month 09.2026 (SL 01.09.2026 → 01.10.2026)", name="shadow_20260901-20261001_q8_0"))
GLUE = 2              # changed runs separated by at most this many unchanged words merge into one phrase


def _toks(s): return [(m.start(), m.group(0)) for m in TOK.finditer(s)]


class _Segs:
    """Collects [kind, text(, who, slot)] segments; kind e(qual) | i(nserted) | d(eleted). Numbers of the new text whose
    start is in `chip` become their own segment carrying who placed them."""
    def __init__(self, new, nums):
        self.new, self.S = new, []
        self.chip = {s: (e, who, slot) for s, e, t, who, slot in nums}

    def put(self, kind, text):
        if not text: return
        if self.S and self.S[-1][0] == kind and len(self.S[-1]) == 2: self.S[-1][1] += text
        else: self.S.append([kind, text])

    def new_range(self, kind, a, b):
        """new[a:b] as kind (e or i), with number chips."""
        pos = a
        for s in sorted(k for k in self.chip if a <= k < b):
            e, who, slot = self.chip[s]
            self.put(kind, self.new[pos:s]); self.S.append([kind, self.new[s:e], who, slot]); pos = e
        self.put(kind, self.new[pos:b])


def _words(toks): return sum(1 for _, t in toks if re.match(r"\w", t))


def _changed(o, n):
    """Share of words (old + new) in changed runs of a word diff of o -> n."""
    A, B = _toks(o), _toks(n)
    ops = difflib.SequenceMatcher(None, [t for _, t in A], [t for _, t in B], autojunk=False).get_opcodes()
    return sum(_words(B[j1:j2]) + _words(A[i1:i2]) for op, i1, i2, j1, j2 in ops if op != "equal") / max(1, _words(A) + _words(B))


def _block(S, old, new, a0, a1, b0, b1):
    """A changed block old[a0:a1] -> new[b0:b1]: whole-sentence when most of it changed, else phrase-level."""
    A = [(s, t) for s, t in _toks(old[a0:a1])]; B = [(s, t) for s, t in _toks(new[b0:b1])]
    sm = difflib.SequenceMatcher(None, [t for _, t in A], [t for _, t in B], autojunk=False)
    ops = sm.get_opcodes()
    changed = sum(_words(B[j1:j2]) + _words(A[i1:i2]) for op, i1, i2, j1, j2 in ops if op != "equal")
    total = max(1, _words(A) + _words(B))
    if changed / total > WHOLE:
        o = old[a0:a1].rstrip()
        if o: S.S.append(["d", o, "s"])                           # whole old sentence(s), struck
        S.new_range("i", b0, b1)
        return
    groups, cur = [], None                                     # merge changed runs separated by <= GLUE words
    for k, (op, i1, i2, j1, j2) in enumerate(ops):
        if op == "equal":
            short = _words(A[i1:i2]) <= GLUE and 0 < k < len(ops) - 1
            if cur and short: cur[1], cur[3] = i2, j2; cur[4].append((i1, i2, j1, j2)); continue
            if cur: groups.append(cur); cur = None
            groups.append(("eq", i1, i2, j1, j2)); continue
        if cur: cur[1], cur[3] = i2, j2
        else: cur = [i1, i2, j1, j2, []]
    if cur: groups.append(cur)
    def off(T, i, base, text): return base + (T[i][0] if i < len(T) else len(text))
    for g in groups:
        if g[0] == "eq":
            _, i1, i2, j1, j2 = g; S.new_range("e", off(B, j1, b0, new[b0:b1]), off(B, j2, b0, new[b0:b1])); continue
        i1, i2, j1, j2, _ = g
        oa, ob = off(A, i1, a0, old[a0:a1]), off(A, i2, a0, old[a0:a1])
        na, nb = off(B, j1, b0, new[b0:b1]), off(B, j2, b0, new[b0:b1])
        d, n = old[oa:ob], new[na:nb]
        if d.strip() == "" and n.strip() == "": S.new_range("e", na, nb); continue
        lead = len(n) - len(n.lstrip()) if d.strip() else 0       # keep a shared leading space outside the marks
        if d.strip(): S.put("d", d.strip())
        if d.strip() and n[:lead]: S.new_range("e", na, na + lead)
        S.new_range("i", na + lead, nb)


def diff(old, new, nums=()):
    """-> [[kind, text, (who, slot) | ("s",)]]: sentence-aligned, phrase-level diff. Unchanged sentences are kept;
    changed sentence blocks are shown word-phrase by phrase, or as old sentence struck + new sentence underlined when
    more than WHOLE of their words changed. A 3-element d segment ["d", text, "s"] marks a whole struck sentence."""
    S = _Segs(new, nums)
    A, B = sentences(old), sentences(new)
    key = lambda s, sp: re.sub(r"\s+", " ", s[sp[0]:sp[1]]).strip()
    sm = difflib.SequenceMatcher(None, [key(old, x) for x in A], [key(new, x) for x in B], autojunk=False)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        a0 = A[i1][0] if i1 < len(A) else len(old); a1 = A[i2 - 1][1] if i2 > i1 else a0
        b0 = B[j1][0] if j1 < len(B) else len(new); b1 = B[j2 - 1][1] if j2 > j1 else b0
        if op == "equal": S.new_range("e", b0, b1)
        elif op == "delete": S.S.append(["d", old[a0:a1].rstrip(), "s"])
        elif op == "insert": S.new_range("i", b0, b1)
        else: _replace(S, old, new, A[i1:i2], B[j1:j2])
    return S.S


def _ratio(a, b):
    return difflib.SequenceMatcher(None, [t for _, t in _toks(a)], [t for _, t in _toks(b)], autojunk=False).ratio()


def _replace(S, old, new, As, Bs):
    """Changed run of sentences: pair each new sentence with the most similar remaining old one (in order, ratio >= .5)
    and diff the pair; unpaired old sentences are struck, unpaired new ones underlined."""
    i = 0
    for b0, b1 in Bs:
        best, bi = 0.0, None
        for k in range(i, len(As)):
            r = _ratio(old[As[k][0]:As[k][1]], new[b0:b1])
            if r > best: best, bi = r, k
        if bi is None or best < 0.5:
            S.new_range("i", b0, b1); continue
        if bi > i and _changed(old[As[i][0]:As[bi][1]], new[b0:b1]) <= WHOLE:      # unpaired old sentences join the pair
            _block(S, old, new, As[i][0], As[bi][1], b0, b1); i = bi + 1; continue
        for a0, a1 in As[i:bi]: S.S.append(["d", old[a0:a1].rstrip(), "s"])
        _block(S, old, new, As[bi][0], As[bi][1], b0, b1); i = bi + 1
    for a0, a1 in As[i:]: S.S.append(["d", old[a0:a1].rstrip(), "s"])


def summary(segs, n=110):
    """One-line description of the first change of a diff: 'old → new', '+ new' or '− old'."""
    d, i, started = "", "", False
    for s in segs:
        if s[0] == "e":
            if started and (d or i) and s[1].strip(): break
            continue
        started = True
        if s[0] == "d": d += (" " if d else "") + s[1]
        else: i += s[1]
    d, i = re.sub(r"\s+", " ", d).strip(), re.sub(r"\s+", " ", i).strip()
    t = f"{d} → {i}" if d and i else f"+ {i}" if i else f"− {d}" if d else "(no textual change)"
    return t if len(t) <= n else t[:n].rsplit(" ", 1)[0] + " …"


def _date(s):
    return f"{s[6:8]}.{s[4:6]}.{s[:4]}" if re.fullmatch(r"\d{8}", s or "") else (s or "?")


def _ledger(v, rules):
    """Checks ledger rows for one draft: [gid, name, state, [dict(t=sentence, c=corrects, r=triage rule)], raw detail,
    g-id label]. Order (display only): failed checks with a finding to check, failed checks whose findings are all
    probably fine, passed checks, checks not run."""
    L = v["lang"]; by = {}
    for f, r in zip(v["findings"], rules):
        if f["gid"] != "corr": by.setdefault("slot" if f["gid"] == "unknown" else f["gid"], []).append((f, r))
    rows = []
    for gid, lab, state, detail in v["lights"]:
        fs = by.get(gid, [])
        txt = [dict(t=f["text"], c=f["corrects"], r=r) for f, r in fs]
        txt = [x for x in txt if not x["r"]] + [x for x in txt if x["r"]]
        if gid == "reask": txt = [dict(t=explain.reask_text(v), c=False, r=None)]
        rows.append([gid, explain.name(gid, L), state, txt, detail if state == "fail" else "", lab])
    def key(r):
        if r[2] == "fail" and r[0] == "reask": return 1                # how the draft was obtained, not a finding
        if r[2] == "fail": return 0 if (not r[3] or any(not x["r"] for x in r[3])) else 1
        return 2 if r[2] == "pass" else 3
    return sorted(rows, key=key)


def _old_text(v):
    """Pre-existing problems of the old target text (display notice): [dict(k=kind, t=sentence, f=found language)]
    (+ o / n / w: old term, new term, where BAG already corrected it, for kind 'terminology')."""
    out = []
    for d in v.get("divergence") or []:
        o = dict(k=d.get("kind", "number"), t=d["text"], f=d.get("found"))
        if o["k"] == "terminology": o.update(o=d.get("old"), n=d.get("new"), w=d.get("where") or [])
        out.append(o)
    return out


def _xliff_notes(v, rules=None):
    """The unit notes the page's XLIFF export writes (xliff.unit_notes, target language), minus the old texts (rebuilt
    in the page from the diff segments, placed before the low-priority checks note) and the review note (written at
    export time)."""
    return [[i, c, a, int(p), t] for i, c, a, p, t in xliff.unit_notes(v, prev=False)]


def _why(v, E=None):
    """The per-draft explanation of the page: at most xliff.SHOW reasons, most actionable first, plain wording in the
    draft's language without internal codes ([text, low]), and how many items there are in all (shown + left to the
    checks detail). The pre-existing divergence and the correction notice are left out: the page shows them in its notice
    next to the draft. The low-priority notes (a deletion that mirrors the German's, typography, the termbase advisory)
    are not reasons: _note gives them as the one grey line under the explanation."""
    E = E or xliff.explanation(v)
    return E["top"], len(E["top"]) + E["more"]


def _note(v, E=None):
    """The grey line under the explanation (the page's `tb`): the low-priority notes, then the termbase advisory; None
    when there is none (xliff.explanation)."""
    return (E or xliff.explanation(v))["note"]


FORMS = {"filmtabl", "tabl", "lactab", "kaps", "inj", "inf", "lös", "trockensub", "schmelztabl", "ret", "konz", "susp",
         "gran", "plv", "supp", "creme", "salbe", "gel", "tropfen", "sirup", "amp", "brausetabl", "markierungsbesteck",
         "inhal", "emuls", "pen", "fertspr", "fertpen", "durchstf", "lyophilisat", "dragées", "drag", "solution"}


def brand(product):
    """'Darzalex SC Inj Lös 1800 mg/15ml' -> 'Darzalex SC': the product name up to its dosage form or strength."""
    out = []
    for w in product.split():
        if out and (w.lower().strip(".,") in FORMS or re.search(r"\d", w)): break
        out.append(w)
    return " ".join(out) or product


def _family_labels(views):
    """family id -> the product names of the family, most frequent first ('Darzalex, Darzalex SC'; '+n' beyond four)."""
    names = {}
    for v in views:
        names.setdefault(v["family"], Counter())[brand(v["product"])] += 1
    out = {}
    for f, c in names.items():
        ns = [n for n, _ in sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))]
        out[f] = ", ".join(ns[:4]) + (f" +{len(ns) - 4}" if len(ns) > 4 else "")
    return out


def data(run="fresh166", records=None, items=None, audit=audit_view.AUDIT, hist=None, name=None):
    meta, views = load(run, records, items)
    if name: meta["run"] = name                  # a records file named records.jsonl: the run name its lane gives it
    if meta["custom"]:
        from ..emit import _read_items
        summ = None; I = {x["key"]: x for x in _read_items(meta["items_path"]) if x.get("tgt_new")}     # BAG's published text, where known
    else:
        summ = SUMMARY[run]() if run in SUMMARY else score.score_run(run)["summary"]; I = {}
    groups = {}
    for v in views:
        g = groups.setdefault(v["pair"], dict(pair=v["pair"], product=v["product"], code=v["cud_id"], snap_old=_date(v["snap_old"]),
                                              snap_new=_date(v["snap_new"]), family=v["family"], de=diff(v["de_old"], v["de_new"]),
                                              ch=segment.changed(v["de_old"], v["de_new"]), sn=segment.number_spans(v["de_new"]),
                                              brand=brand(v["product"]), items={}))
        g["sum"] = summary(g["de"])
        corr = next((f for f in v["findings"] if f["gid"] == "corr"), None)
        rules = triage.triage(v); E = xliff.explanation(v)
        it = dict(key=v["key"], lang=v["lang"], status=v["status"], lvl=triage.level(v), rule_only=v["rule_only"], cud=v["cud_id"],
                  banner=v.get("banner"), corr=corr["text"] if corr else None, corr_note=explain.corr_note(v["lang"]) if corr else None,
                  old=_old_text(v), xn=_xliff_notes(v, rules), why=_why(v, E), tb=_note(v, E),
                  findings=[[f["gname"], f["text"], f["corrects"], r] for f, r in zip(v["findings"], rules) if f["gid"] != "corr"])
        it["tri"] = E["counts"] if v["status"] == "flagged" else [0, 0]          # the header counts what the reasons list shows
        if v["status"] == "flagged": it["lvl"] = "check" if it["tri"][0] else "fine"
        if v["status"] == "human":
            r = v.get("change_ratio")
            it.update(segs=[["e", v["tgt_old"]]], ledger=[], ratio=(round(100 * float(r)) if r not in (None, "") else None),
                      reason=v.get("reason") or "", bd=[list(b) for b in segment.beads(v["de_new"])], nm=[])
        else:
            nm = [[a, b, who, slot] for a, b, _, who, slot in v["numbers"]]
            it.update(segs=diff(v["tgt_old"], v["draft"], v["numbers"]), ledger=_ledger(v, rules),
                      model_numbers=sum(n[3] == "model" for n in v["numbers"]), nm=nm,
                      bd=[list(x) for x in segment.beads(v["de_new"], v["draft"], [(a, b) for a, b, *_ in nm])])
            if v["status"] == "flagged":                 # "start from the old text": old target + the rules lane's number changes
                rt, done = core.gl2.rules(v["de_old"], v["de_new"], v["tgt_old"], v["lang"])
                ops = difflib.SequenceMatcher(None, v["tgt_old"], rt, autojunk=False).get_opcodes()
                it["rt"] = [[[i1, i2, rt[j1:j2]] for op, i1, i2, j1, j2 in ops if op != "equal"], sum(1 for d in done if d[2])]
            if v["key"] in I: it["exact"] = core.lock.norm(v["draft"]) == core.lock.norm(I[v["key"]].get("tgt_new", ""))
        g["items"][v["lang"]] = it
    fam = Counter(v["family"] for v in views); flab = _family_labels(views)
    counts = dict(items=len(views), changes=len(groups), ready=sum(v["status"] == "ready" for v in views),
                  flagged=sum(v["status"] == "flagged" for v in views), human=sum(v["status"] == "human" for v in views),
                  divergent=sum(bool(v.get("banner")) or bool(v.get("divergence")) or any(f["gid"] == "corr" for f in v["findings"]) for v in views),
                  old_text=sum(bool(v.get("divergence")) for v in views),
                  code_numbers=sum(n[3] == "code" for v in views for n in v["numbers"]),
                  model_numbers=sum(n[3] == "model" for v in views for n in v["numbers"]))
    G = list(groups.values())
    counts["to_check"] = sum(it["tri"][0] for g in G for it in g["items"].values())
    counts["probably_fine"] = sum(it["tri"][1] for g in G for it in g["items"].values())
    counts["lvl_fine"] = sum(it["lvl"] == "fine" for g in G for it in g["items"].values())
    counts["lvl_check"] = sum(it["lvl"] == "check" for g in G for it in g["items"].values())
    if I:                         # exact among the drafts with a published text (status human: no draft, not compared)
        counts["exact"] = sum(1 for g in G for it in g["items"].values() if it.get("exact"))
        counts["exact_of"] = sum(1 for g in G for it in g["items"].values() if "exact" in it)
    m = {k: meta[k] for k in ("run", "what", "stack", "model", "pipeline", "items_sha256", "run_sha256", "custom", "has_tgt_new")}
    m["model"] = model_label(meta)
    m["label"] = LABEL.get(meta["run"], meta["what"]) if not meta["custom"] else "records " + meta["run"]
    m["rev"] = git_rev()
    m["period"] = None if meta["custom"] else PERIOD.get(meta["run"])
    ml = (m["model"] or "").lower()
    m["lane"] = "70b" if "70b" in ml else "8b" if "8b" in ml else None      # SL lanes: 8B on CPU (default) | 70B endpoint (fewer edits)
    xn = {L: dict(prev_de=xliff.NOTE[L]["prev_de"], prev_tgt=xliff.NOTE[L]["prev_tgt"], product=xliff.NOTE[L]["product"],
                  about=xliff.nt(L, "about"), states=xliff.nt(L, "states"), prov=xliff.provenance_note(meta, L),
                  review=xliff.NOTE[L]["review"], reviewed=xliff.NOTE[L]["reviewed"],
                  about12=xliff.nt(L, "about12"), states12=xliff.nt(L, "states12"), code_number=xliff.nt(L, "code_number"),
                  changed=xliff.nt(L, "changed"),
                  dec={k: xliff.NOTE[L][k] for k in ("accept", "accept-edited", "send-back")}) for L in ("fr", "it")}
    snaps = sorted({v["snap_new"] for v in views if re.fullmatch(r"\d{8}", str(v.get("snap_new") or ""))})
    return dict(meta=m, all=summ["all"] if summ else None, groups=G, xn=xn, snap=snaps[-1] if snaps else None,
                families=[[f, n, flab.get(f, f)] for f, n in sorted(fam.items(), key=lambda kv: (-kv[1], kv[0]))], counts=counts,
                audit=audit_view.data(audit, audit_view.RESULTS, hist) if audit else None)


def git_rev():
    """The short commit for the title block: $GIT_COMMIT, else `git rev-parse --short HEAD` at build time, else None."""
    c = os.environ.get("GIT_COMMIT", "").strip()
    if c: return c[:12]
    try:
        import subprocess
        r = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=core.ROOT, capture_output=True, text=True, timeout=5)
        return (r.stdout.strip() or None) if r.returncode == 0 else None
    except Exception:
        return None


def fonts_css():
    """@font-face rules with the vendored woff2 files inlined (base64), real fallback stacks in the CSS below."""
    rules = []
    for fam, fn, w, st in (("Public Sans", "PublicSans-latin-wght.woff2", "400 600", "normal"),
                           ("Archivo", "Archivo-latin-wdth75-wght500-600.woff2", "500 600", "75%"),
                           ("Fragment Mono", "FragmentMono-400-latin.woff2", "400", "normal")):
        p = os.path.join(FONTS, fn)
        if not os.path.exists(p): continue
        b64 = base64.b64encode(open(p, "rb").read()).decode()
        rules.append(f"@font-face{{font-family:'{fam}';font-style:normal;font-weight:{w};font-stretch:{st};font-display:swap;"
                     f"src:url(data:font/woff2;base64,{b64}) format('woff2')}}")
    return "\n".join(rules)


def _blob(D): return json.dumps(D, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def lanes_data(lanes, audit=audit_view.AUDIT, hist=None):
    """-> [(lane id, data)] for each lane (dict(id, run | records + items, optional live = the month, label)); only the
    first carries the audit. Each data's meta names its lane (meta.lane_id, meta.live) and the first lists them all
    (lanes: [{id, lane (8b | 70b), live, items, ready, flagged}])."""
    out = []
    for i, ln in enumerate(lanes):
        rec = os.path.join(core.ROOT, ln["records"]) if ln.get("records") else None
        its = os.path.join(core.ROOT, ln["items"]) if ln.get("items") else None
        D = data(ln.get("run") or "fresh166", rec, its, audit if i == 0 else None, hist, ln.get("name"))
        D["meta"].update(lane_id=ln["id"], live=ln.get("live"), live_span=list(ln["span"]) if ln.get("span") else None)
        if ln.get("label"): D["meta"]["label"] = ln["label"]
        out.append((ln["id"], D))
    out[0][1]["lanes"] = [dict(id=k, lane=D["meta"]["lane"], live=D["meta"]["live"], items=D["counts"]["items"], ready=D["counts"]["ready"],
                               flagged=D["counts"]["flagged"]) for k, D in out]
    return out


def build(run=None, out=OUT, records=None, items=None, fragment=False, audit=audit_view.AUDIT, hist=None, lanes=None):
    """Writes the page; -> (path, data of the lane it opens with). No run and no records: the LANES page (8B default,
    70B fewer-edits lane, the live months); a run or records: a page with that one run."""
    if lanes is None:
        lanes = LANES if not (run or records) else [dict(id="run", run=run or "fresh166", records=records, items=items)]
    L = lanes_data(lanes, audit, hist); D = L[0][1]
    body = BODY.replace("__DATA__", _blob(D)).replace("__LANES__", "".join(
        f'<script type="application/json" id="data-{k}">{_blob(X)}</script>\n' for k, X in L[1:]))
    head = HEAD.replace("__FONTS__", fonts_css())
    page = (head + body) if fragment else ("<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
           "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n" + head + "</head>\n<body>\n" + body + "</body>\n</html>\n")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f: f.write(page)
    return out, D


from .page import HEAD, BODY          # noqa: E402  (the template lives in page.py)


def main(argv=None):
    ap = argparse.ArgumentParser(description="build the static translator review page")
    ap.add_argument("--run", help="one recorded run of score.RUNS (q8_0, fresh166, q8_0_rerun, ...); default: the lanes page "
                    "(8B Q8_0 default, 70B fewer edits, the live months)"); ap.add_argument("--out", default=OUT)
    ap.add_argument("--records", help="records JSONL (gleichlaut month / draft) instead of a recorded run; needs --items")
    ap.add_argument("--items", help="items file for --records")
    ap.add_argument("--fragment", action="store_true", help="no doctype/html/head/body (for a claude.ai artifact)")
    ap.add_argument("--audit", default=audit_view.AUDIT, help="audit findings file for the Register audit tab ('' = no tab)")
    ap.add_argument("--hist", help="SL snapshot dir (default $GLEICHLAUT_HIST or out/hist): fills audit snippets a finding lacks")
    a = ap.parse_args(argv)
    from ..sl import hist_dir
    p, D = build(a.run, a.out, a.records, a.items, a.fragment, a.audit, hist_dir(a.hist))
    c = D["counts"]
    au = D.get("audit")
    if len(D.get("lanes") or []) > 1:
        print("ui lanes: " + "; ".join(f"{x['id']} {x['items']} drafts ({x['ready']} ready, {x['flagged']} flagged)" for x in D["lanes"]))
    print(f"ui: {c['items']} drafts in {c['changes']} German changes ({c['ready']} ready, {c['flagged']} flagged"
          + (f", {c['human']} routed to a translator" if c["human"] else "") + f"; flag findings {c['to_check']} to check, "
          f"{c['probably_fine']} probably fine; flagged drafts {c['lvl_check']} to check, {c['lvl_fine']} with every finding probably fine)" + (f"; audit {au['meta']['main']} findings + {au['meta']['term']} terminology notices" + (" (snippets from the SL snapshot)" if au["meta"]["hist"] else "") if au else "")
          + f" -> {p} ({os.path.getsize(p) // 1024} KB)")


if __name__ == "__main__":
    main()
