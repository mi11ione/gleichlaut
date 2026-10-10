"""Audit relabel (PREREG R14 part A): every finding of the three labelled audit sets read again by two fresh blind Claude
annotators (the second in reverse order) and a third on every disagreement, with each record's own audit question
unchanged. Deterministic, stdlib only, no model, no network.

  python3 tools/audit_relabel.py            write the pooled worklist and the id -> finding map (eval/labels/audit_relabel_*)
  python3 tools/audit_relabel.py --check    reproduce them byte for byte (exit 1 if they differ)
  python3 tools/audit_relabel.py --ab DIR   read DIR/A/labels.tsv and DIR/B/labels.tsv (by neutral id), write
                                            audit_relabel_{A,B}.tsv and the tie-break worklist + its key
  python3 tools/audit_relabel.py --t DIR    read DIR/T/labels.tsv, write audit_relabel_T.tsv and the merged
                                            audit_relabel.tsv (score.audit_relabel_merge)

Sets (the first annotation is the `real` column of each file, one annotator per finding):
  register     6 Oct 2026 SL register: audit_20261006 (21 number findings) + audit2_20261006 (6 language/editorial) = 27
  terminology  audit3_terminology_20261006 (11)
  lists        audit_migel_20260701 (8) + audit_al_20260701 (3) = 11
Records: the committed worklist records of these files, every field kept (texts, finding, question) except the id, which
becomes a neutral R00.. id; pooled and shuffled with random.Random(20261016). Tie-break ids T00.., random.Random(20261018).
Answers: real / minor / not, as each question defines them; confirmed = real or minor (the first annotation's yes)."""
import json, os, random, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))
from gleichlaut import score          # noqa: E402

LABELS = os.path.join(ROOT, "eval", "labels")
SEED, TSEED = 20261016, 20261018
P = "audit_relabel"
SETS = {"register": ("audit_20261006", "audit2_20261006"), "terminology": ("audit3_terminology_20261006",),
        "lists": ("audit_migel_20260701", "audit_al_20260701")}
ANSWERS = ("real", "minor", "not")


def dumps(o): return json.dumps(o, ensure_ascii=False, indent=1) + "\n"


def j(name): return json.load(open(os.path.join(LABELS, name), encoding="utf-8"))


def findings():
    """-> {uid 'file:id': (set, record)} in file order."""
    out = {}
    for st, files in SETS.items():
        for f in files:
            for r in j(f"{f}_worklist.json"): out[f"{f}:{r['id']}"] = (st, r)
    return out


def record(rid, r): return dict([("id", rid)] + [(k, v) for k, v in r.items() if k != "id"])


def build():
    F = findings(); uids = sorted(F); random.Random(SEED).shuffle(uids)
    W, ids = [], {}
    for i, u in enumerate(uids):
        rid = f"R{i:02d}"; ids[rid] = u; W.append(record(rid, F[u][1]))
    key = dict(prereg="eval/prereg/PREREG.md R14 (part A)", seed=SEED, sets={k: list(v) for k, v in SETS.items()},
               counts={st: sum(F[u][0] == st for u in F) for st in SETS}, ids=ids)
    return W, key


def read_ann(path, want):
    lines = open(path, encoding="utf-8").read().splitlines()
    assert lines[0].split("\t")[:2] == ["id", "answer"], lines[0]
    got = {}
    for l in lines[1:]:
        if not l.strip(): continue
        c = l.split("\t") + [""]
        rid, ans = c[0].strip(), c[1].strip().lower()
        assert ans in ANSWERS and rid in want and rid not in got, (path, l)
        got[rid] = (ans, " ".join(x.strip() for x in c[2:] if x.strip()))
    assert set(got) == set(want), (path, sorted(set(want) - set(got))[:5])
    return got


def write_tsv(name, got):
    out = ["id\tanswer\tnote"] + ["\t".join((i, *got[i])) for i in sorted(got)]
    open(os.path.join(LABELS, name), "w", encoding="utf-8").write("\n".join(out) + "\n")


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    if "--ab" in argv:
        d = argv[argv.index("--ab") + 1]
        key = j(f"{P}_key.json"); ids = key["ids"]
        A = read_ann(os.path.join(d, "A", "labels.tsv"), ids); B = read_ann(os.path.join(d, "B", "labels.tsv"), ids)
        write_tsv(f"{P}_A.tsv", A); write_tsv(f"{P}_B.tsv", B)
        tie = sorted(ids[i] for i in ids if A[i][0] != B[i][0]); random.Random(TSEED).shuffle(tie)
        F = findings(); TW, tids = [], {}
        for i, u in enumerate(tie):
            rid = f"T{i:02d}"; tids[rid] = u; TW.append(record(rid, F[u][1]))
        open(os.path.join(LABELS, f"{P}_tiebreak_worklist.json"), "w", encoding="utf-8").write(dumps(TW))
        open(os.path.join(LABELS, f"{P}_tiebreak_key.json"), "w", encoding="utf-8").write(dumps(dict(seed=TSEED, ids=tids)))
        print(f"A/B: {len(ids)} records; tie-break worklist {len(TW)} records"); return 0
    if "--t" in argv:
        d = argv[argv.index("--t") + 1]
        tids = j(f"{P}_tiebreak_key.json")["ids"]
        write_tsv(f"{P}_T.tsv", read_ann(os.path.join(d, "T", "labels.tsv"), tids) if tids else {})
        rows = score.audit_relabel_merge()
        out = ["\t".join(score.AUDIT_RELABEL_COLS)] + ["\t".join(r[h] for h in score.AUDIT_RELABEL_COLS) for r in rows]
        open(os.path.join(LABELS, f"{P}.tsv"), "w", encoding="utf-8").write("\n".join(out) + "\n")
        print(f"{P}.tsv", len(rows), "findings"); return 0
    W, key = build(); files = {f"{P}_worklist.json": W, f"{P}_key.json": key}
    bad = []
    for name, o in files.items():
        p = os.path.join(LABELS, name)
        if "--check" in argv:
            if not os.path.exists(p) or open(p, encoding="utf-8").read() != dumps(o): bad.append(name)
        else:
            open(p, "w", encoding="utf-8").write(dumps(o))
    if "--check" in argv:
        print("audit_relabel:", "OK" if not bad else "DIFFERS " + ", ".join(bad)); return 1 if bad else 0
    print(f"worklist {len(W)} records:", key["counts"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
