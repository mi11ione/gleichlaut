"""In-span annotator sensitivity (PREREG R14 part B): do the blind annotators of eval/labels/PROTOCOL.md catch a meaning error
written INSIDE the wording the German change touched, as fluent text that reads like part of the amendment? R11 planted
single local edits outside the change; an annotator can find those by diffing the draft against the old text. Here the
error sits in the amended sentence, next to or within the legitimate change. Deterministic (seed 20261017), stdlib only,
no model, no network.

DESIGN (fixed in this file and in PREREG R14 before any annotation)
  Bases      the R11 pool (tools/plant_sensitivity.pool: fresh-166 ready drafts every label calls exact or equivalent, one
             draft per item), restricted to drafts produced by the 70B or the 8B Q8_0 run, minus any draft whose text the
             R13 blind majority marks needs_fix. The boilerplate family 981f07a8 (one sentence, one changed insurer
             term, 34 such bases) is subsampled to 4 FR + 4 IT with random.Random('20261017:family:<lang>'); all other
             bases are kept.
  Plants     eval/labels/inspan_plants.json, written by hand by the pre-registering agent after the base selection and
             before any annotation: per base one (type, old, new, error); the planted copy is the draft with `old`
             (occurring exactly once) replaced by `new`. Types:
               scope        population or indication widened or narrowed within the amended clause
               condition    a condition of the new German half-applied, kept in part from the old text, or changed
                            (limited in time, made conditional) within the amended clause
               number_noun  a number or unit of the amended clause attached to the wrong noun
               and_or       an and/or inside the amended clause
             Checked here: the whole edit (draft -> planted copy) lies inside the touched span, i.e. the sentences of
             the draft (plant_sensitivity.sentences) that overlap a character the draft changed against tgt_old (a pure
             deletion touches the sentences on both sides of it).
  Real       the 30 real labelled drafts of R11 (final label REAL, stale or german), as a base-rate mix.
  Sets       two worklists; every base appears once planted and once untouched, never both in one worklist. Bases are
             grouped (same SL cluster, or the same touched sentence text) and a group's planted copies all go to the same
             worklist, so no worklist holds a planted copy beside an untouched sibling of the same wording; groups are
             assigned largest first to the worklist with fewer planted copies (ties: seeded). Real items alternate.
  Worklists  per set, seeded shuffle, neutral ids (V000.., W000..), fields as PROTOCOL.md (official_new shown). The key
             (id -> item, kind, type, edit) is written apart and never shown.

usage: python3 tools/plant_inspan.py [--check] | --merge DIR
writes eval/labels/inspan_key.json and eval/labels/inspan_set{1,2}_worklist.json; --check verifies the committed files byte
for byte. --merge DIR maps DIR/w_<set><A|B>/labels.tsv (neutral ids) back through the key -> eval/labels/inspan_sensitivity.tsv."""
import difflib, json, os, random, sys
from collections import Counter

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(ROOT, "src")); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plant_sensitivity as PS              # noqa: E402

SEED = 20261017
TYPES = ("scope", "condition", "number_noun", "and_or")
FAMILY, FAMILY_N = "981f07a8", 4
LABELS = os.path.join(ROOT, "eval", "labels")
PREFIX = {1: "V", 2: "W"}
norm = PS.norm


def j(name): return json.load(open(os.path.join(LABELS, name), encoding="utf-8"))


def touched(old, new):
    """[(start, end)] sentence spans of `new` that overlap a character changed against `old` (a pure deletion: both
    neighbouring sentences)."""
    S = PS.sentences(new); out = []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, old, new, autojunk=False).get_opcodes():
        if op == "equal": continue
        a, b = (j1 - 1, j2 + 1) if j1 == j2 else (j1, j2)
        out += [(s, e) for s, e in S if s < b and a < e]
    return sorted(set(out))


def edit_span(a, b):
    """(start, end) in a of everything that differs between a and b."""
    ops = [o for o in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes() if o[0] != "equal"]
    return ops[0][1], ops[-1][2]


def selection():
    I, bases, real = PS.pool()
    blind = {}
    F = PS.score.load_jsonl("runs/70b_fresh166_g3_final.jsonl")
    for l in open(os.path.join(LABELS, "fresh166_blind.tsv"), encoding="utf-8").read().splitlines()[1:]:
        c = l.split("\t")
        if c[7] == "yes": blind[c[0]] = norm(F[c[0]]["out"])
    keep = {k: d for k, d in bases.items() if set(d["runs"]) & {"70b", "q8_0"} and blind.get(k) != norm(d["text"])}
    sel = sorted(k for k in keep if I[k]["cluster"] != FAMILY)
    for L in ("fr", "it"):
        fam = sorted(k for k in keep if I[k]["cluster"] == FAMILY and I[k]["lang"] == L)
        sel += random.Random(f"{SEED}:family:{L}").sample(fam, FAMILY_N)
    return I, {k: keep[k] for k in sorted(sel)}, real


def build():
    I, bases, real = selection()
    spec = {p["key"]: p for p in j("inspan_plants.json")["plants"]}
    assert set(spec) == set(bases), (sorted(set(bases) - set(spec)), sorted(set(spec) - set(bases)))
    items = {}
    for k, d in bases.items():
        p = spec[k]; t = d["text"]; x = I[k]
        assert p["type"] in TYPES and t.count(p["old"]) == 1, k
        new = t.replace(p["old"], p["new"]); s, e = edit_span(t, new)
        T = touched(x["tgt_old"], t)
        assert T and any(a <= s and e <= b for a, b in T), (k, "edit outside the touched span")
        span = next((a, b) for a, b in T if a <= s and e <= b)
        common = dict(key=k, lang=x["lang"], base_class="exact" if any(c == "exact" for _, c, _ in d["labels"]) else "equivalent",
                      base_runs=d["runs"], family=FAMILY if x["cluster"] == FAMILY else "other")
        items[f"{k}|planted"] = dict(common, kind="planted", type=p["type"], old=p["old"], new=p["new"], error=p["error"],
                                     touched_sentence=t[span[0]:span[1]], draft=new)
        items[f"{k}|untouched"] = dict(common, kind="untouched", type=None, draft=t)
    for k, d in sorted(real.items()):
        items[f"{k}|real"] = dict(key=k, lang=I[k]["lang"], kind="real", existing=d["existing"], base_runs=d["runs"],
                                  ready=any(d["ready"]), draft=d["text"])
    # groups: same cluster, or the same touched sentence text (union-find)
    par = {k: k for k in bases}
    def find(k):
        while par[k] != k: k = par[k]
        return k
    by = {}
    for k in bases:
        for g in (("c", I[k]["cluster"]), ("t", norm(items[f"{k}|planted"]["touched_sentence"]))):
            if g in by: par[find(k)] = find(by[g])
            else: by[g] = k
    groups = {}
    for k in sorted(bases): groups.setdefault(find(k), []).append(k)
    rng = random.Random(SEED)
    G = sorted(groups.values()); rng.shuffle(G); G.sort(key=len, reverse=True)
    n, plant_set = {1: 0, 2: 0}, {}
    for g in G:
        st = 1 if n[1] < n[2] else 2 if n[2] < n[1] else rng.choice((1, 2))
        for k in g: plant_set[k] = st
        n[st] += len(g)
    rk = sorted(real); rng.shuffle(rk); real_set = {k: 1 + i % 2 for i, k in enumerate(rk)}
    for u, it in items.items():
        k = it["key"]
        it["set"] = plant_set[k] if it["kind"] == "planted" else 3 - plant_set[k] if it["kind"] == "untouched" else real_set[k]
    W, ids = {}, {}
    for st in (1, 2):
        uids = sorted(u for u, it in items.items() if it["set"] == st); random.Random(f"{SEED}:{st}").shuffle(uids)
        assert len({items[u]["key"] for u in uids}) == len(uids)
        recs = []
        for i, u in enumerate(uids):
            it = items[u]; x = I[it["key"]]; rid = f"{PREFIX[st]}{i:03d}"; ids[rid] = u
            recs.append(dict(id=rid, lang=x["lang"], de_old=x["de_old"], de_new=x["de_new"], tgt_old=x["tgt_old"],
                             draft=it["draft"], official_new=x["tgt_new"]))
        W[f"inspan_set{st}_worklist.json"] = recs
    key = dict(prereg="eval/prereg/PREREG.md R14 (part B)", seed=SEED, types=list(TYPES),
               counts=dict(bases=len(bases), planted=len(bases), untouched=len(bases), real=len(real),
                           by_type_lang={f"{t}/{L}": sum(items[f"{k}|planted"]["type"] == t and I[k]["lang"] == L for k in bases)
                                         for t in TYPES for L in ("fr", "it")},
                           family=sum(I[k]["cluster"] == FAMILY for k in bases),
                           per_set={st: dict(Counter(it["kind"] for it in items.values() if it["set"] == st)) for st in (1, 2)}),
               items={u: {k: v for k, v in it.items() if k != "draft"} for u, it in sorted(items.items())}, ids=ids)
    return W, key


def dumps(o): return json.dumps(o, ensure_ascii=False, indent=1) + "\n"


def merge(d):
    key = j("inspan_key.json"); ids = key["ids"]; rows = {}
    for st in (1, 2):
        want = {r["id"] for r in j(f"inspan_set{st}_worklist.json")}
        for ann in "AB":
            lines = open(os.path.join(d, f"w_{st}{ann}", "labels.tsv"), encoding="utf-8").read().splitlines()
            assert lines[0].split("\t")[:3] == ["id", "needs_fix", "class"], lines[0]
            got = {}
            for l in lines[1:]:
                if not l.strip(): continue
                c = l.split("\t") + [""]
                fix, cls = c[1].strip().lower(), c[2].strip()
                cls = {x.lower(): x for x in PS.CLASSES}.get(cls.lower(), cls)
                assert fix in ("yes", "no") and cls in PS.CLASSES and c[0] in want and c[0] not in got, (st, ann, l)
                got[c[0]] = (fix, cls, " ".join(x.strip() for x in c[3:] if x.strip()))
            assert set(got) == want, (st, ann, sorted(want - set(got))[:5])
            for i, (fix, cls, note) in got.items():
                rows.setdefault(ids[i], {}).update({f"{ann}_fix": fix, f"{ann}_class": cls, f"note_{ann}": note})
    out = ["uid\tkind\ttype\tlang\tA_fix\tA_class\tB_fix\tB_class\tnote_A\tnote_B"]
    for u in sorted(rows):
        it = key["items"][u]; r = rows[u]
        out.append("\t".join((u, it["kind"], it.get("type") or "", it["lang"], r["A_fix"], r["A_class"], r["B_fix"], r["B_class"],
                              r["note_A"], r["note_B"])))
    open(os.path.join(LABELS, "inspan_sensitivity.tsv"), "w", encoding="utf-8").write("\n".join(out) + "\n")
    print("inspan_sensitivity.tsv", len(rows), "items")


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    if "--merge" in argv: return merge(argv[argv.index("--merge") + 1]) or 0
    W, key = build(); files = dict(W, **{"inspan_key.json": key})
    bad = []
    for name, o in files.items():
        p = os.path.join(LABELS, name)
        if "--check" in argv:
            if not os.path.exists(p) or open(p, encoding="utf-8").read() != dumps(o): bad.append(name)
        else:
            open(p, "w", encoding="utf-8").write(dumps(o))
    if "--check" in argv:
        print("plant_inspan:", "OK" if not bad else "DIFFERS " + ", ".join(bad)); return 1 if bad else 0
    c = key["counts"]; print(f"bases {c['bases']} (family {c['family']})  real {c['real']}  per set {c['per_set']}")
    print("by type/lang", c["by_type_lang"])
    for n, r in W.items(): print(n, len(r), "records", sum(len(json.dumps(x, ensure_ascii=False)) for x in r), "chars")
    return 0


if __name__ == "__main__":
    sys.exit(main())
