"""gold-level cross-language flags + hand adjudication -> gold_flags.tsv
verdicts: real = the languages state different conditions; minor = boundary/inclusivity shift of the same threshold;
benign = same condition, different wording/number expression or a candidate-generator gap."""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import gold as G, compare as K

# (cud-family, odd, value-in-days-or-native, subj) -> verdict, note   (keys checked against the generated flags)
ADJ = {
 ("NEMLUVIO.01", "it", 56): ("real", "maintenance interval: DE/FR every 8 weeks, IT every 4 weeks"),
 ("DIAPHIN.6-", "it", 12): ("real", "surcharge 6% DE/FR vs 12% IT"),
 ("DIAPHIN.6-", "it", 6): ("real", "surcharge 6% DE/FR vs 12% IT"),
 ("NEPEXTO", "fr", 62.5): ("real", "FR-only weight >= 62.5 kg on JIA"),
 ("BENEPALI4", "fr", 62.5): ("real", "FR-only weight >= 62.5 kg on JIA"),
 ("ERELZI2", "fr", 62.5): ("real", "FR-only weight >= 62.5 kg on JIA"),
 ("CRESE.Kps.IM", "fr", 16): ("real", "FR omits body weight >= 16 kg"),
 ("DUPIXENT.02", "fr", 28): ("real", "FR omits the 15-<30 kg tier (q4w, start 4 weeks after day 15)"),
 ("DUPIXENT.02", "fr", 1): ("real", "FR omits the 15-<30 kg tier (day 1)"),
 ("DUPIXENT.02", "fr", 15): ("real", "FR omits the 15-<30 kg tier (>=15 kg, day 15)"),
 ("DUPIXENT.02", "fr", 30): ("real", "FR omits 15-<30 tier and the >=30 kg lower bound of the middle tier"),
 ("DUPIXENT.02", "de", 60): ("minor", "boundary at 60 kg: DE 'ab 60' (>=) vs FR/IT 'plus de/superiore a' (>)"),
 ("DUPIXENT.05a", "fr", 15): ("real", "FR lower weight bound 30 kg vs DE/IT 15 kg"),
 ("DUPIXENT.05a", "fr", 30): ("real", "FR lower weight bound 30 kg vs DE/IT 15 kg"),
 ("DUPIXENT.05a", "fr", 60): ("minor", "boundary at 60 kg: FR 'supérieur à' (>) vs DE/IT >="),
 ("DUPIXENT.05a", "fr", 1): ("benign", "FR 'une fois par an' = DE 'jährlich' / IT 'a cadenze annuali' (no number)"),
 ("FORXIGA.HFPM", "fr", 1): ("benign", "FR 'au moins l'un' is not a candidate (generator gap)"),
 ("TREMFYAPE.04", "de", 1): ("benign", "DE 'maximal eine Dosis von X mg' vs FR/IT 'une dose maximale de X mg': same cap"),
 ("TREMFYAPE.04", "de", 100): ("benign", "same as above (maintenance 100 mg)"),
 ("TREMFYAPE.04", "de", 200): ("benign", "same as above (induction 200 mg)"),
 ("KEYTRUDA.26", "fr", 2): ("benign", "FR 'les deux premiers emballages' masked by the BOTH rule (generator gap)"),
}
COPY = {"DUPIXENT.02P": "DUPIXENT.02", "DUPIXENT.05P": "DUPIXENT.05a"}


def build():
    D, I, gold, _, _ = G.load()
    rows = []
    for it in D["items"]:
        cud = it["cud"]
        per = {l: K.tuples(it["langs"][l]["cands"], gold[(cud, l)], use_label_unit=True)[0] for l in K.LANGS}
        _, fl = K.compare(per)
        for f in fl:
            if f["kind"] == "count":
                continue
            key = (COPY.get(cud, cud), f["odd"], f["t"][2])
            v, note = ADJ[key]
            rows.append(dict(cud=cud, split=it["split"], kind=f["kind"], odd=f["odd"], t=list(f["t"]), verdict=v, note=note))
    return rows


if __name__ == "__main__":
    rows = build()
    with open(os.path.join(HERE, "..", "gold_flags.tsv"), "w") as f:
        f.write("cud\tsplit\tkind\todd\ttuple\tverdict\tnote\n")
        for r in rows:
            f.write("\t".join([r["cud"], r["split"], r["kind"], r["odd"], K.fmt_t(tuple(r["t"])), r["verdict"], r["note"]]) + "\n")
    import collections
    print(collections.Counter((r["split"], r["verdict"]) for r in rows))
