"""PREREG R17: (A) real-error sensitivity of the blind Claude annotators and (B) a non-Claude annotator (Apertus 70B).

A juror: "Claude wrote the planted errors and Claude caught them; kappa 1.000 is two copies of one model family agreeing."

(A) Real errors. In the SL snapshot history the backtest uses, every place where BAG changed a French or Italian
    limitation while the German text stayed byte-identical. Each change is classified mechanically (CLASSIFY below); the
    ones that change content (not spacing, punctuation or typography only) are kept, all of them. The text that
    disagrees with the unchanged German is a real, human-made error: normally the OLD text, which BAG later fixed; the
    declared exceptions (REVERSED) are changes where the NEW text drops a sentence the unchanged German still carries,
    so there the new text is the error and the old one the correct version. Records in the PROTOCOL.md worklist shape:
    error record draft = tgt_old = the erroneous text, de_old = de_new = the unchanged German, official_new = the correct
    version (protocol a) or absent (protocol b); control record the same with draft = tgt_old = the correct version.
    A change's error and control records are never in the same worklist.
(B) Apertus 70B through the development gateway labels (i) the 49 audit findings of R14 (the audit uses no model) with
    each record's own question and (ii) the part-A records under both protocols, one record per call, plain user message,
    no system message, no prefill, temperature 0, fixed answer format (parsers: gleichlaut.score.r17_parse_*).

Deterministic, stdlib only. Data: the 2026 snapshot JSONs (sl.ingest output; default the research tree) and the two 2025
Wayback XML captures.

CLASSIFY (per change, old -> new, after nrm()):
  typography  view T(s) = NFC, casefold, apostrophes ’‘` -> ', quotes «»“”„ -> ", dashes –—‑ -> -, then words = \\w+ runs
              (so punctuation, spacing, case and quote/apostrophe style never count). Equal word lists -> 'punctuation'
              (spacing / punctuation / typography only): reported, not used.
  number      the multiset of numbers (\\d+ with . , ' separators) differs
  negation_operator  the multiset of negation / operator words or symbols (NEGOP) differs
  words       otherwise (word lists differ): subtype added (insertions only), removed (deletions only), replaced
  The first that applies, in the order number > negation_operator > words, is the change's type.

usage: python3 tools/r17_real_errors.py build [--check] [--hist DIR] [--wb2025 DIR]
       python3 tools/r17_real_errors.py merge DIR            (DIR/w_<a|b><1|2><A|B>/labels.tsv -> eval/labels/r17_real_errors_{a,b}.tsv)
       PYTHONPATH=src python3 tools/r17_real_errors.py run70b   (development gateway; resumable)"""
import difflib, hashlib, json, os, random, re, sys, time, unicodedata
from collections import Counter

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))
from gleichlaut import core, backends           # noqa: E402
from gleichlaut.sl import mine as M             # noqa: E402
from gleichlaut.sl.ingest import nrm, load_xml  # noqa: E402

SEED = 20261019
HIST = os.path.expanduser("~/Desktop/hackapertus/spikes/gleichlaut/data/hist")
WB = os.path.expanduser("~/Desktop/hackapertus/spikes/gleichlaut/data/wb2025")
WB_STEP = ("20250611", "20250731")             # the two 2025 captures (same XML format); 2025 -> 2026 has no shared key
LABELS = os.path.join(ROOT, "eval", "labels")
RUN = os.path.join(ROOT, "data", "r17", "apertus70b")
PROMPTS = os.path.join(ROOT, "data", "r17", "r17_70b_prompts.json")
MODEL, TAG, MAX_TOKENS = "swiss-ai/apertus-v1.5-70b", "gleichlaut-r17-70b", 300
PREFIX = {("a", 1): "X", ("a", 2): "Y", ("b", 1): "J", ("b", 2): "K"}
CLASSES = ("exact", "equivalent", "preexisting", "cosmetic", "minor", "german", "stale", "REAL")
TYPES = ("number", "negation_operator", "words")

# changes where the NEW text is the defective one (a sentence of the unchanged German dropped from the new text, leaving
# "chimiothérapie. ."): declared by the pre-registering agent after reading the mined changes against the German, before
# any annotation or model call. Key: <lang>:<new key>:<step>.
REVERSED = {"fr:OPDIVO.01---NSCLC-Mono:20260901>20261001": "the German's indication-code sentence dropped, leaving '. .'",
            "fr:OPDIVO.04---Nierenzellkarzinom--RCC-:20260901>20261001": "the German's indication-code sentence dropped, leaving '. .'"}

NEGOP = {"fr": {"ne", "n", "pas", "non", "aucun", "aucune", "jamais", "ni", "sans", "plus", "moins", "maximum", "minimum",
                "max", "min", "maximal", "maximale", "maximaux", "minimal", "minimale", "minimaux", "supérieur", "supérieure",
                "supérieurs", "supérieures", "inférieur", "inférieure", "inférieurs", "inférieures", "dès", "jusqu", "<", ">",
                "≤", "≥"},
         "it": {"non", "né", "nessun", "nessuno", "nessuna", "mai", "senza", "più", "meno", "almeno", "massimo", "massima",
                "massimi", "minimo", "minima", "minimi", "max", "min", "superiore", "superiori", "inferiore", "inferiori",
                "oltre", "sotto", "fino", "<", ">", "≤", "≥"}}
NUM = re.compile(r"\d+(?:[.,'’]\d+)*")
_TY = str.maketrans({"’": "'", "‘": "'", "`": "'", "«": '"', "»": '"', "“": '"', "”": '"', "„": '"', "–": "-", "—": "-", "‑": "-"})


def tview(s): return unicodedata.normalize("NFC", nrm(s)).casefold().translate(_TY)
def words(s): return re.findall(r"\w+", tview(s))
def negop(s, L): return sorted([w for w in words(s) if w in NEGOP[L]] + [c for c in s if c in "<>≤≥"])


def classify(old, new, L):
    wo, wn = words(old), words(new)
    if wo == wn: return dict(type="punctuation", subtype=None)
    ops = {o for o, *_ in difflib.SequenceMatcher(None, wo, wn, autojunk=False).get_opcodes() if o != "equal"}
    sub = "added" if ops == {"insert"} else "removed" if ops == {"delete"} else "replaced"
    flags = dict(number=sorted(NUM.findall(old)) != sorted(NUM.findall(new)), negation_operator=negop(old, L) != negop(new, L))
    ty = "number" if flags["number"] else "negation_operator" if flags["negation_operator"] else "words"
    return dict(type=ty, subtype=sub, **flags)


def word_diff(old, new):
    """[(op, old words, new words)] on the typography view (for the key; never shown to annotators)."""
    a, b = words(old), words(new)
    return [(o, " ".join(a[i1:i2]), " ".join(b[j1:j2])) for o, i1, i2, j1, j2 in
            difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes() if o != "equal"]


def mine(hist=HIST, wbd=WB):
    """-> (changes, stats). A change = (lang, German, old, new) with its first occurrence; German byte-identical."""
    H = M.Hist(hist); found, st = {}, Counter()
    for a, b in zip(M.SNAPS, M.SNAPS[1:]):
        Da, Db = H(a, "de"), H(b, "de")
        for m in sorted(set(Da["prod"]) & set(Db["prod"])):
            ta, tb = {}, {}
            for k in Da["prod"][m]["keys"]: ta.setdefault(Da["lim"][k], k)
            for k in Db["prod"][m]["keys"]: tb.setdefault(Db["lim"][k], k)
            for de in sorted(set(ta) & set(tb)):              # the raw German string, byte-identical in both snapshots
                st["de_unchanged_pairs"] += 1
                if ta[de] in Da["conflict"] or tb[de] in Db["conflict"]: st["conflict"] += 1; continue
                for L in ("fr", "it"):
                    ko, kn = M.tkey(H, a, L, m, ta[de]), M.tkey(H, b, L, m, tb[de])
                    to = H(a, L)["lim"].get(ko) if ko else None; tn = H(b, L)["lim"].get(kn) if kn else None
                    if to is None or tn is None: st["target_missing"] += 1; continue
                    to, tn = nrm(to), nrm(tn)
                    if to == tn: continue
                    if a <= M.OLD_FORMAT_LAST and ("<" in to or "<" in tn or "<" in de): st["lt_bug"] += 1; continue
                    found.setdefault((L, de, to, tn), []).append(dict(step=f"{a}>{b}", key_old=ta[de], key_new=tb[de], mpd=m,
                                                                      product=Db["prod"][m]["name"]))
    X = {}
    for s in WB_STEP:
        p = os.path.join(wbd, s, "Preparations.xml")
        if not os.path.exists(p): raise SystemExit(f"missing {p}")
        X[s] = {}
        for k, Ls in load_xml(p).items():
            for d in Ls: X[s].setdefault((k, d["de"]), d)
    A, B = X[WB_STEP[0]], X[WB_STEP[1]]
    for kd in sorted(set(A) & set(B)):
        st["de_unchanged_pairs_2025"] += 1
        for L in ("fr", "it"):
            if A[kd][L] and B[kd][L] and A[kd][L] != B[kd][L]:
                found.setdefault((L, kd[1], A[kd][L], B[kd][L]), []).append(dict(step=f"{WB_STEP[0]}>{WB_STEP[1]}", key_old=kd[0],
                                                                                  key_new=kd[0], mpd=None, product=A[kd]["product"]))
    ch = []
    for (L, de, to, tn), occ in sorted(found.items(), key=lambda kv: (kv[1][0]["step"], kv[0][0], kv[1][0]["key_new"], kv[0][2])):
        o = occ[0]; c = classify(to, tn, L)
        ch.append(dict(uid=f"{L}:{o['key_new']}:{o['step']}", lang=L, step=o["step"], key=o["key_new"], product=o["product"],
                       n_occ=len(occ), de=nrm(de), old=to, new=tn, **c, word_diff=word_diff(to, tn),
                       family=hashlib.md5(repr(M.sig(to, tn)).encode()).hexdigest()[:8]))
    assert len({c["uid"] for c in ch}) == len(ch)
    st["changes"] = len(ch)
    return ch, dict(st)


def build(hist=HIST, wbd=WB):
    ch, st = mine(hist, wbd)
    keep = [c for c in ch if c["type"] != "punctuation"]
    assert set(REVERSED) <= {c["uid"] for c in keep}, sorted(set(REVERSED) - {c["uid"] for c in keep})
    items = {}
    for c in keep:
        rev = c["uid"] in REVERSED
        err, ok = (c["new"], c["old"]) if rev else (c["old"], c["new"])
        com = dict(lang=c["lang"], type=c["type"], subtype=c["subtype"], family=c["family"], step=c["step"], product=c["product"],
                   reversed=rev, error_text=err, correct_text=ok)
        items[f"{c['uid']}|error"] = dict(com, uid=c["uid"], kind="error", draft=err)
        items[f"{c['uid']}|control"] = dict(com, uid=c["uid"], kind="control", draft=ok)
    # groups: same edit family or the same German (union-find); a group's error records all go to one worklist
    par = {c["uid"]: c["uid"] for c in keep}
    def find(u):
        while par[u] != u: u = par[u]
        return u
    by = {}
    for c in keep:
        for g in (("f", c["family"]), ("d", c["de"])):
            if g in by: par[find(c["uid"])] = find(by[g])
            else: by[g] = c["uid"]
    groups = {}
    for c in keep: groups.setdefault(find(c["uid"]), []).append(c["uid"])
    rng = random.Random(SEED); G = sorted(sorted(g) for g in groups.values()); rng.shuffle(G); G.sort(key=len, reverse=True)
    n, err_set = {1: 0, 2: 0}, {}
    for g in G:
        s = 1 if n[1] < n[2] else 2 if n[2] < n[1] else rng.choice((1, 2))
        for u in g: err_set[u] = s
        n[s] += len(g)
    for k, it in items.items(): it["set"] = err_set[it["uid"]] if it["kind"] == "error" else 3 - err_set[it["uid"]]
    W, ids = {}, {}
    de = {c["uid"]: c["de"] for c in keep}
    for p in ("a", "b"):
        for s in (1, 2):
            ks = sorted(k for k, it in items.items() if it["set"] == s); random.Random(f"{SEED}:{p}:{s}").shuffle(ks)
            assert len({items[k]["uid"] for k in ks}) == len(ks)
            recs = []
            for i, k in enumerate(ks):
                it = items[k]; rid = f"{PREFIX[(p, s)]}{i:03d}"; ids[rid] = k
                r = dict(id=rid, lang=it["lang"], de_old=de[it["uid"]], de_new=de[it["uid"]], tgt_old=it["draft"], draft=it["draft"])
                if p == "a": r["official_new"] = it["correct_text"]
                recs.append(r)
            W[f"r17_{p}_set{s}_worklist.json"] = recs
    counts = dict(changes_mined=len(ch), by_type=dict(Counter(c["type"] for c in ch)), content=len(keep),
                  content_by_type=dict(Counter(c["type"] for c in keep)),
                  content_by_type_subtype=dict(Counter(f"{c['type']}/{c['subtype']}" for c in keep)),
                  content_by_lang=dict(Counter(c["lang"] for c in keep)), content_by_step=dict(Counter(c["step"] for c in keep)),
                  families=dict(Counter(c["family"] for c in keep)), reversed=len(REVERSED),
                  per_set={s: dict(Counter(it["kind"] for it in items.values() if it["set"] == s)) for s in (1, 2)})
    key = dict(prereg="eval/prereg/PREREG.md R17 (part A)", seed=SEED, snapshots=M.SNAPS, wb2025_step=list(WB_STEP),
               mining=st, counts=counts, reversed=REVERSED,
               changes=[{k: v for k, v in c.items()} for c in ch],
               items={k: {f: v for f, v in it.items() if f != "draft"} for k, it in sorted(items.items())}, ids=ids)
    return W, key


# ------------------------------------------------------------------ instructions (Claude annotators and Apertus 70B)
CONTEXT_A = ('Context: Swiss drug-reimbursement conditions (BAG Spezialitätenliste "limitations"). Here the German text '
             'was not amended (de_old = de_new). The French or Italian text (lang) under review is draft (tgt_old is the '
             'same text); judge it against the German as if it were a new draft: a problem already in tgt_old counts '
             'against the draft, and "the German change" in the definitions below means "the German text". official_new '
             'is what the authorities published.')
CONTEXT_B = CONTEXT_A.replace("official_new is what the authorities published.",
                              "No published version is available for these records: there is no official_new field.")
TASK = ('For each record, read de_old, de_new, tgt_old, draft and official_new in full and decide:\n'
        '1. needs_fix: "no" if a translator could accept the draft as the correct amendment (applies exactly the German change,\n'
        '   meaning-preserving; wording may differ from official_new), "yes" otherwise.\n'
        '2. class, exactly one of: exact (equals official_new ignoring whitespace and apostrophe style); equivalent (correctly\n'
        '   applies the German change; differences are only extra fixes the official translators made or harmless wording);\n'
        '   preexisting (only problem was already in tgt_old and untouched by the German change); cosmetic (correct meaning,\n'
        '   cosmetic defect e.g. spacing, product name spelling); minor (small defect, no condition changed, no German left,\n'
        '   e.g. a calque or non-standard term); german (German words, German abbreviations, Germanised compounds or German\n'
        '   hyphenation artefacts left in the draft); stale (the German change is not or only partly applied); REAL (the draft\n'
        "   changes a condition's meaning relative to the new German: dropped/added condition, changed and/or, changed\n"
        '   obligation, wrong scope, reversed direction, wrong number). If several apply, pick the most severe:\n'
        '   REAL > stale > german > minor > cosmetic > preexisting > equivalent > exact.')
LONG = ("Some lines of the file are longer than 2,000 characters; if your file viewer truncates long lines, read the file "
        "so that every line is shown in full (for example with cat or python3), still only this file.")


def claude_instructions(p, worklist, n, output, reverse=False):
    """the PROTOCOL.md instructions with the R17 context paragraph (p = 'a' reference shown, 'b' hidden) + R11's note."""
    return ("You are a blind annotator for a translation-quality evaluation. Read ONLY this file: `" + worklist + f"` ({n} records). "
            "Do NOT open, search or list any other file or directory. Use only the read of that file and one write of your "
            "output file. No web access.\n\n" + (CONTEXT_A if p == "a" else CONTEXT_B) + "\n\n" + TASK +
            (" [Label the records in reverse order: start with the last record of the file and end with the first.]" if reverse else "") +
            "\n\nWrite a TSV to `" + output + "` with header `id\\tneeds_fix\\tclass\\tnote` (note <= 20 words). Read every "
            'record fully; do not skim long paragraphs. Report back only "done" plus counts per class, computed from the file '
            "you wrote.\n\n" + LONG)


def apertus_prompt_record(p, rec):
    return ("You are a blind annotator for a translation-quality evaluation.\n\n" + (CONTEXT_A if p == "a" else CONTEXT_B) +
            "\n\n" + TASK.replace("For each record,", "For the record below,") + "\n\nRecord (JSON):\n" +
            json.dumps(rec, ensure_ascii=False, indent=1) +
            "\n\nAnswer in exactly this format, three lines, nothing else:\nneeds_fix: <yes or no>\nclass: <one class>\nnote: <at most 20 words>")


AUDIT_CONTEXT = ("Context: Swiss federal lists of reimbursed medicines, medical devices and laboratory analyses (BAG "
                 "Spezialitätenliste, MiGeL, Analysenliste) are published in German, French and Italian, and the language "
                 "versions should state the same conditions. An automatic audit flagged each record below; `finding` says what "
                 "it flagged and `lang` names the language version concerned. Each record carries the texts and its own "
                 "`question`.")


def apertus_prompt_audit(rec):
    return ("You are a blind annotator for an evaluation of a divergence audit.\n\n" + AUDIT_CONTEXT.replace("each record below", "the record below") +
            "\n\nRead the texts and the finding of the record below in full and answer the record's `question` with exactly "
            "one of: real, minor, not (as that question defines them).\n\nRecord (JSON):\n" + json.dumps(rec, ensure_ascii=False, indent=1) +
            "\n\nAnswer in exactly this format, two lines, nothing else:\nanswer: <real, minor or not>\nnote: <at most 20 words>")


def prompts(W=None):
    """-> the Apertus request list: the 49 R14 audit records, then every part-A record under (a) and under (b)."""
    if W is None: W = {n: json.load(open(os.path.join(LABELS, n), encoding="utf-8")) for n in
                       (f"r17_{p}_set{s}_worklist.json" for p in "ab" for s in (1, 2))}
    out = [dict(task="audit", id=r["id"], prompt=apertus_prompt_audit(r))
           for r in json.load(open(os.path.join(LABELS, "audit_relabel_worklist.json"), encoding="utf-8"))]
    for p in "ab":
        for s in (1, 2):
            out += [dict(task=p, id=r["id"], prompt=apertus_prompt_record(p, r)) for r in W[f"r17_{p}_set{s}_worklist.json"]]
    for d in out: d["payload_key"] = backends.payload_key(MODEL, d["prompt"], MAX_TOKENS)
    return dict(prereg="eval/prereg/PREREG.md R17 (part B)", model=MODEL, max_tokens=MAX_TOKENS, temperature=0.0, tag=TAG,
                message="one plain user message, no system message, no assistant prefill", requests=out)


def dumps(o): return json.dumps(o, ensure_ascii=False, indent=1) + "\n"


def cmd_build(argv):
    hist = argv[argv.index("--hist") + 1] if "--hist" in argv else HIST
    wbd = argv[argv.index("--wb2025") + 1] if "--wb2025" in argv else WB
    W, key = build(hist, wbd)
    files = {os.path.join(LABELS, n): o for n, o in W.items()}
    files[os.path.join(LABELS, "r17_key.json")] = key
    files[PROMPTS] = prompts(W)
    bad = []
    for p, o in files.items():
        if "--check" in argv:
            if not os.path.exists(p) or open(p, encoding="utf-8").read() != dumps(o): bad.append(os.path.relpath(p, ROOT))
        else:
            os.makedirs(os.path.dirname(p), exist_ok=True); open(p, "w", encoding="utf-8").write(dumps(o))
    if "--check" in argv:
        print("r17_real_errors:", "OK" if not bad else "DIFFERS " + ", ".join(bad)); return 1 if bad else 0
    print("mining", key["mining"]); print("counts", json.dumps(key["counts"], ensure_ascii=False))
    for n, r in W.items(): print(n, len(r), "records")
    print("apertus requests", len(files[PROMPTS]["requests"]))
    return 0


def merge(d):
    key = json.load(open(os.path.join(LABELS, "r17_key.json"), encoding="utf-8")); ids = key["ids"]
    for p in "ab":
        rows = {}
        for s in (1, 2):
            want = {r["id"] for r in json.load(open(os.path.join(LABELS, f"r17_{p}_set{s}_worklist.json"), encoding="utf-8"))}
            for ann in "AB":
                lines = open(os.path.join(d, f"w_{p}{s}{ann}", "labels.tsv"), encoding="utf-8").read().splitlines()
                assert lines[0].split("\t")[:3] == ["id", "needs_fix", "class"], lines[0]
                got = {}
                for l in lines[1:]:
                    if not l.strip(): continue
                    c = l.split("\t") + [""]
                    fix, cls = c[1].strip().lower(), c[2].strip()
                    cls = {x.lower(): x for x in CLASSES}.get(cls.lower(), cls)
                    assert fix in ("yes", "no") and cls in CLASSES and c[0] in want and c[0] not in got, (p, s, ann, l)
                    got[c[0]] = (fix, cls, " ".join(x.strip() for x in c[3:] if x.strip()))
                assert set(got) == want, (p, s, ann, sorted(want - set(got))[:5])
                for i, (fix, cls, note) in got.items():
                    rows.setdefault(ids[i], {}).update({"id": i if ann == "A" else rows.get(ids[i], {}).get("id", i),
                                                        f"{ann}_fix": fix, f"{ann}_class": cls, f"note_{ann}": note})
        out = ["key\tid\tkind\ttype\tlang\tA_fix\tA_class\tB_fix\tB_class\tnote_A\tnote_B"]
        for k in sorted(rows):
            it = key["items"][k]; r = rows[k]
            out.append("\t".join((k, r["id"], it["kind"], it["type"], it["lang"], r["A_fix"], r["A_class"], r["B_fix"], r["B_class"],
                                  r["note_A"], r["note_B"])))
        open(os.path.join(LABELS, f"r17_real_errors_{p}.tsv"), "w", encoding="utf-8").write("\n".join(out) + "\n")
        print(f"r17_real_errors_{p}.tsv", len(rows), "records")
    return 0


def run70b():
    D = json.load(open(PROMPTS, encoding="utf-8"))
    assert D["model"] == MODEL and D["tag"] == TAG
    os.makedirs(RUN, exist_ok=True); resp = os.path.join(RUN, "responses")
    ask = backends.Gateway(os.path.expanduser("~/Desktop/hackapertus/gateway"), TAG, 2.0, model=MODEL,
                           log=os.path.join(RUN, "calls.jsonl"))
    done = 0
    for i, r in enumerate(D["requests"]):
        k = r["payload_key"]; assert k == backends.payload_key(MODEL, r["prompt"], D["max_tokens"])
        if os.path.exists(os.path.join(resp, k[:2], k + ".json")): continue
        text, meta = ask(r["prompt"], "r17", 2.0, D["max_tokens"])
        if meta.get("model_served") != MODEL:                      # checked on every call, cached or not
            raise SystemExit(f"served {meta.get('model_served')!r}, not {MODEL}: refused, nothing recorded")
        backends.write_cache(resp, k, text, meta)
        done += 1
        print(f"{i + 1:3d}/{len(D['requests'])} {r['task']} {r['id']} served={meta['model_served']} {text[:70]!r}", flush=True)
        time.sleep(1.0)
    print("calls made:", done)
    return 0


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    if not argv or argv[0] == "build": return cmd_build(argv[1:])
    if argv[0] == "merge": return merge(argv[1])
    if argv[0] == "run70b": return run70b()
    raise SystemExit(__doc__)


if __name__ == "__main__":
    sys.exit(main())
