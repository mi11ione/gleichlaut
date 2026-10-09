"""python3 -m gleichlaut.emit --run fresh166 --n 10 --out DIR

Writes DIR/fhir/*.fhir.json (one Bundle per target language), DIR/xliff/*.xlf (one file per target language) and
DIR/validation.json, validates them (emit/validate.py) and exits 1 on any validation error. No model calls."""
import argparse, os, sys
from .. import core
from . import dump_json, fhir, load, select, validate, xliff


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--run", default="fresh166")
    ap.add_argument("--n", type=int, default=10, help="items to emit (0 = all); alternates ready and flagged in key order")
    ap.add_argument("--out", default=os.path.join(core.ROOT, "out", "emit"))
    a = ap.parse_args(argv)
    meta, views = load(a.run); V = select(views, a.n)
    fp = fhir.write(V, meta, os.path.join(a.out, "fhir")); xp = xliff.write(V, meta, os.path.join(a.out, "xliff"))
    rep = validate.validate_files(fp, xp)
    rep.update(run=a.run, items=[v["key"] for v in V], ready=sum(v["status"] == "ready" for v in V),
               flagged=sum(v["status"] == "flagged" for v in V), model=meta["model"], pipeline=meta["pipeline"])
    dump_json(rep, os.path.join(a.out, "validation.json"))
    for kind in ("fhir", "xliff"):
        for fn, r in rep[kind].items():
            errs = r.get("errors", []) + r.get("profile_errors", []) + r.get("parity_errors", [])
            what = ("CH EPL CUD profile + R5 base StructureDefinitions, ePL feed parity" if kind == "fhir"
                    else "OASIS XLIFF 2.1 core XSD + core constraints")
            print(f"{'OK  ' if not errs else 'FAIL'} {kind:5s} {fn}  [{what}]" + "".join(f"\n     - {e}" for e in errs[:20]))
    print(f"emit {a.run}: {len(V)} items ({rep['ready']} ready, {rep['flagged']} flagged) -> {a.out}; "
          f"validation {'PASSED' if rep['ok'] else 'FAILED'}")
    return 0 if rep["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
