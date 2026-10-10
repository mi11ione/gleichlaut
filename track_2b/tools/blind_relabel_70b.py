"""Fully blind relabel of the headline 70B fresh-166 run (PREREG R13) under eval/labels/PROTOCOL.md.
Deterministic, stdlib only, no model, no network.

  python3 tools/blind_relabel_70b.py            write the worklist and the id -> key map (eval/labels/fresh166_blind_*)
  python3 tools/blind_relabel_70b.py --check    reproduce them byte for byte (exit 1 if they differ)
  python3 tools/blind_relabel_70b.py --ab DIR   read DIR/A/labels.tsv and DIR/B/labels.tsv (annotators A and B, by neutral
                                                id), write fresh166_blind_{A,B}.tsv and the tie-break worklist + its key
  python3 tools/blind_relabel_70b.py --t DIR    read DIR/T/labels.tsv, write fresh166_blind_T.tsv and the merged
                                                fresh166_blind.tsv (score.blind_relabel_70b_merge)

Items: every ready non-exact draft of runs/70b_fresh166_g3_final.jsonl (flag re-computed with guards3, exact by the frozen
scorer) plus the seeded 20 flagged drafts of R1 (random.Random(20261009).sample of the sorted flagged keys). Worklist ids
H00.., shuffled with random.Random(20261013); tie-break ids T00.., shuffled with random.Random(20261014)."""
import json, os, random, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))
from gleichlaut import score          # noqa: E402

LABELS = os.path.join(ROOT, "eval", "labels")
SEED, TSEED, FSEED = 20261013, 20261014, 20261009
P = "fresh166_blind"
FIELDS = ("id", "lang", "de_old", "de_new", "tgt_old", "draft", "official_new")


def dumps(o): return json.dumps(o, ensure_ascii=False, indent=1) + "\n"


def record(rid, x, out): return dict(zip(FIELDS, (rid, x["lang"], x["de_old"], x["de_new"], x["tgt_old"], out, x["tgt_new"])))


def build():
    I, _, rows = score.rows_for("fresh166")                   # flag re-computed with the frozen guards3 stack
    F = score.load_jsonl(score.RUNS["fresh166"]["final"])
    ready = sorted(r["key"] for r in rows if not r["flagged"] and not r["exact"])
    flagged = sorted(r["key"] for r in rows if r["flagged"])
    sample = random.Random(FSEED).sample(flagged, min(20, len(flagged)))
    keys = sorted(set(ready) | set(sample)); random.Random(SEED).shuffle(keys)
    W, ids = [], {}
    for i, k in enumerate(keys):
        rid = f"H{i:02d}"; ids[rid] = k; W.append(record(rid, I[k], F[k]["out"]))
    key = dict(prereg="eval/prereg/PREREG.md R13", run=score.RUNS["fresh166"]["final"], seed=SEED, flagged_seed=FSEED,
               ready=ready, flagged_sample=sorted(sample), ids=ids)
    return W, key


def read_ann(path, want):
    lines = open(path, encoding="utf-8").read().splitlines()
    assert lines[0].split("\t")[:3] == ["id", "needs_fix", "class"], lines[0]
    C = {c.lower(): c for c in score.BLIND_CLASSES}; got = {}
    for l in lines[1:]:
        if not l.strip(): continue
        c = l.split("\t") + [""]
        rid, fix, cls = c[0].strip(), c[1].strip().lower(), C.get(c[2].strip().lower(), c[2].strip())
        assert fix in ("yes", "no") and cls in score.BLIND_CLASSES and rid in want and rid not in got, (path, l)
        got[rid] = (fix, cls, " ".join(x.strip() for x in c[3:] if x.strip()))
    assert set(got) == set(want), (path, sorted(set(want) - set(got))[:5])
    return got


def write_tsv(name, got):
    out = ["id\tneeds_fix\tclass\tnote"] + ["\t".join((i, *got[i])) for i in sorted(got)]
    open(os.path.join(LABELS, name), "w", encoding="utf-8").write("\n".join(out) + "\n")


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    if "--ab" in argv:
        d = argv[argv.index("--ab") + 1]
        key = json.load(open(os.path.join(LABELS, f"{P}_key.json"), encoding="utf-8")); ids = key["ids"]
        A = read_ann(os.path.join(d, "A", "labels.tsv"), ids); B = read_ann(os.path.join(d, "B", "labels.tsv"), ids)
        write_tsv(f"{P}_A.tsv", A); write_tsv(f"{P}_B.tsv", B)
        ready = set(key["ready"])
        tie = sorted(ids[i] for i in ids if score.blind_needs_tiebreak(A[i][:2], B[i][:2], ids[i] in ready))
        random.Random(TSEED).shuffle(tie)
        I = {x["key"]: x for x in score.load_items("items/items_fresh.json")}; F = score.load_jsonl(score.RUNS["fresh166"]["final"])
        TW, tids = [], {}
        for i, k in enumerate(tie):
            rid = f"T{i:02d}"; tids[rid] = k; TW.append(record(rid, I[k], F[k]["out"]))
        open(os.path.join(LABELS, f"{P}_tiebreak_worklist.json"), "w", encoding="utf-8").write(dumps(TW))
        open(os.path.join(LABELS, f"{P}_tiebreak_key.json"), "w", encoding="utf-8").write(dumps(dict(seed=TSEED, ids=tids)))
        print(f"A/B: {len(ids)} records; tie-break worklist {len(TW)} records"); return 0
    if "--t" in argv:
        d = argv[argv.index("--t") + 1]
        tids = json.load(open(os.path.join(LABELS, f"{P}_tiebreak_key.json"), encoding="utf-8"))["ids"]
        write_tsv(f"{P}_T.tsv", read_ann(os.path.join(d, "T", "labels.tsv"), tids) if tids else {})
        rows = score.blind_relabel_70b_merge()
        hdr = ("key", "A_fix", "A_class", "B_fix", "B_class", "T_fix", "T_class", "final_fix", "final", "note_A")
        out = ["\t".join(hdr)] + ["\t".join(r[h] for h in hdr) for r in rows]
        open(os.path.join(LABELS, f"{P}.tsv"), "w", encoding="utf-8").write("\n".join(out) + "\n")
        print(f"{P}.tsv", len(rows), "items"); return 0
    W, key = build(); files = {f"{P}_worklist.json": W, f"{P}_key.json": key}
    bad = []
    for name, o in files.items():
        p = os.path.join(LABELS, name)
        if "--check" in argv:
            if not os.path.exists(p) or open(p, encoding="utf-8").read() != dumps(o): bad.append(name)
        else:
            open(p, "w", encoding="utf-8").write(dumps(o))
    if "--check" in argv:
        print("blind_relabel_70b:", "OK" if not bad else "DIFFERS " + ", ".join(bad)); return 1 if bad else 0
    print(f"worklist {len(W)} records: ready non-exact {len(key['ready'])}, flagged sample {len(key['flagged_sample'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
