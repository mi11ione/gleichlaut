"""parse gold_raw.txt against items.json -> gold.tsv (one row per candidate) ; validates counts and checkpoints."""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
SUBJ = {"age", "wt", "dose", "int", "time", "cnt", "meas", "price"}
OPS = {">=", ">", "<=", "<", "="}


def parse_tok(t):
    if t == "N":
        return None
    unit = None
    if ":" in t:
        t, unit = t.split(":", 1)
    m = re.match(r"^([a-z]+)(>=|<=|>|<|=)$", t)
    assert m and m.group(1) in SUBJ and m.group(2) in OPS, t
    return dict(subj=m.group(1), op=m.group(2), unit=unit)


def load(strict=True):
    D = json.load(open(os.path.join(ROOT, "items.json")))
    I = {it["cud"]: it for it in D["items"]}
    lines, copies = {}, []
    for ln in open(os.path.join(ROOT, "gold_raw.txt"), encoding="utf-8"):
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        if ln.startswith("COPY"):
            a, b = re.match(r"COPY (\S+) = (\S+)", ln).groups(); copies.append((a, b)); continue
        head, toks = ln.split(":", 1)
        cud, lang = head.split()
        lines[(cud, lang)] = toks.split()
    for a, b in copies:
        for l in ("de", "fr", "it"):
            lines[(a, l)] = lines[(b, l)]
    gold, errs = {}, []
    for (cud, lang), toks in lines.items():
        cs = I[cud]["langs"][lang]["cands"]; labs = []
        for t in toks:
            if t.startswith("#"):
                if int(t[1:]) != len(labs): errs.append(f"{cud} {lang}: checkpoint {t} at {len(labs)}")
                continue
            labs.append(parse_tok(t))
        if len(labs) != len(cs):
            errs.append(f"{cud} {lang}: {len(labs)} labels for {len(cs)} candidates")
            continue
        for c, g in zip(cs, labs):
            if g is not None and g["unit"] is None:
                g["unit"] = c["u"] or ""
        gold[(cud, lang)] = labs
    missing = [(c, l) for c in I for l in ("de", "fr", "it") if (c, l) not in gold]
    if strict and (errs or missing):
        print("\n".join(errs)); print("missing:", len(missing), sorted(set(c for c, _ in missing)))
    return D, I, gold, errs, missing


if __name__ == "__main__":
    D, I, gold, errs, missing = load()
    if not errs and not missing:
        with open(os.path.join(ROOT, "gold.tsv"), "w") as f:
            f.write("cud\tsplit\tstratum\tlang\tidx\tsurface\tvalue\tcode_unit\tgold\tsubj\top\tunit\tcontext\n")
            sys.path.insert(0, HERE); import cands
            for it in D["items"]:
                for l in ("de", "fr", "it"):
                    s = it["langs"][l]["text"]
                    for c, g in zip(it["langs"][l]["cands"], gold[(it["cud"], l)]):
                        ctx = cands.context(s, c["a"], c["b"], 60).replace("\t", " ")
                        lab = "N" if g is None else f"{g['subj']}{g['op']}"
                        f.write("\t".join(map(str, [it["cud"], it["split"], it["stratum"], l, c["idx"], c["surface"], c["v"], c["u"] or "",
                                                    lab, g["subj"] if g else "", g["op"] if g else "", g["unit"] if g else "", ctx])) + "\n")
        print("gold.tsv written")
