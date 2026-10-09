"""python3 -m gleichlaut.emit --run fresh166 --n 10 --out DIR
   python3 -m gleichlaut.emit --records R.jsonl --items I.json --n 0 --out DIR
   python3 -m gleichlaut.emit --run fresh166 --decisions gleichlaut-decisions-fresh166.json --out DIR

Writes DIR/fhir/*.fhir.json (one Bundle per target language), DIR/xliff/*.xlf (XLIFF 2.1, one file per target
language), DIR/xliff/*.xliff12.xlf (XLIFF 1.2 strict, unless --no-xliff12) and DIR/validation.json, validates them
(emit/validate.py) and exits 1 on any validation error. --decisions applies the review page's JSON export and also writes
DIR/xliff/*-reviewed.xlf (XLIFF 2.1, accepted targets state=reviewed, or final with --final), validated the same way.
Items routed to a translator (records status "human") have no draft: they appear in XLIFF without a target and are
left out of FHIR. No model calls."""
import argparse, os, sys
from .. import core
from . import dump_json, fhir, load, select, validate, xliff, xliff12


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--run", default="fresh166")
    ap.add_argument("--records", help="records JSONL (gleichlaut month / draft) instead of a recorded run; needs --items")
    ap.add_argument("--items", help="items file (JSON list or JSONL) for --records")
    ap.add_argument("--n", type=int, default=10, help="items to emit (0 = all); alternates ready and flagged in key order")
    ap.add_argument("--out", default=os.path.join(core.ROOT, "out", "emit"))
    ap.add_argument("--xliff12", dest="xliff12", action="store_true", default=True, help="also write XLIFF 1.2 strict (default)")
    ap.add_argument("--no-xliff12", dest="xliff12", action="store_false")
    ap.add_argument("--decisions", help="the review page's JSON export: also write reviewed XLIFF 2.1")
    ap.add_argument("--final", action="store_true", help="with --decisions: accepted targets get state=final (default reviewed)")
    a = ap.parse_args(argv)
    meta, views = load(a.run, a.records, a.items); V = select(views, a.n)
    if a.decisions:                                      # every decided unit is emitted, whatever --n selects
        D = xliff.read_decisions(a.decisions, meta); keep = {v["key"] for v in V} | set(D)
        V = [v for v in views if v["key"] in keep]
    drafts = [v for v in V if v["status"] != "human"]
    fp = fhir.write(drafts, meta, os.path.join(a.out, "fhir")); xp = xliff.write(V, meta, os.path.join(a.out, "xliff"))
    x12 = xliff12.write(V, meta, os.path.join(a.out, "xliff")) if a.xliff12 else []
    if a.decisions: xp += xliff.write(V, meta, os.path.join(a.out, "xliff"), D, a.final)
    rep = validate.validate_files(fp, xp, x12)
    rep.update(run=meta["run"], items=[v["key"] for v in V], ready=sum(v["status"] == "ready" for v in V),
               flagged=sum(v["status"] == "flagged" for v in V), human=sum(v["status"] == "human" for v in V),
               model=meta["model"], pipeline=meta["pipeline"])
    dump_json(rep, os.path.join(a.out, "validation.json"))
    what = {"fhir": "CH EPL CUD profile + R5 base StructureDefinitions, ePL feed parity",
            "xliff": "OASIS XLIFF 2.1 core XSD + core constraints", "xliff12": "OASIS XLIFF 1.2 strict XSD"}
    for kind in ("fhir", "xliff", "xliff12"):
        for fn, r in rep.get(kind, {}).items():
            errs = r.get("errors", []) + r.get("profile_errors", []) + r.get("parity_errors", [])
            print(f"{'OK  ' if not errs else 'FAIL'} {kind:7s} {fn}  [{what[kind]}]" + "".join(f"\n     - {e}" for e in errs[:20]))
    print(f"emit {meta['run']}: {len(V)} items ({rep['ready']} ready, {rep['flagged']} flagged"
          + (f", {rep['human']} routed to a translator" if rep["human"] else "") + f") -> {a.out}; "
          f"validation {'PASSED' if rep['ok'] else 'FAILED'}")
    return 0 if rep["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
