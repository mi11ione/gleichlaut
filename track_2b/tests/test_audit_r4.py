"""Round 4 of the audit: terminology from BAG's own corrections, the likely_equivalent triage field, the --fail-on-findings
exit code, and the MiGeL / Analysenliste xlsx path (on a synthetic workbook; no network, no snapshot dir needed)."""
import csv, io, json, os, tempfile, zipfile
from gleichlaut import audit as A, audit_lists as AL, score

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANG = dict(de="Die Therapie mit X und einem Angiotensin-II-Antagonisten und/oder einem ACE-Hemmer wird nicht vergütet.",
           old="Le traitement de X et d'un inhibiteur de l'enzyme de conversion de l'angiotensine II et/ou d'un inhibiteur de l'ECA n'est pas remboursé.",
           new="Le traitement de X et d’un antagoniste des récepteurs de l'angiotensine II et/ou d'un inhibiteur de l'ECA n'est pas remboursé.")


def test_term_edits_takes_unexplained_phrase_replacements_only():
    e = A.term_edits(ANG["de"], ANG["old"], ANG["de"], ANG["new"])
    assert [(x["old"], x["new"]) for x in e] == [(("inhibiteur", "de", "l'enzyme", "de", "conversion"), ("antagoniste", "des", "récepteurs"))]
    de2 = ANG["de"].replace("Angiotensin-II-Antagonisten", "Sartan")                        # the German changed right there
    assert not A.term_edits(ANG["de"], ANG["old"], de2, ANG["new"])
    de3 = ANG["de"].replace("nicht vergütet", "von der OKP nicht vergütet")                    # changed elsewhere: still taken
    assert A.term_edits(ANG["de"], ANG["old"], de3, ANG["new"])
    assert not A.term_edits("x", "dose de 30 mg par jour", "x", "dose de 15 mg par jour")     # digits: number check
    assert not A.term_edits("x", "le médecin traitant decide", "x", "le médecin traitant décide")   # accent only
    assert not A.term_edits("x", "un texte tout à fait différent ici", "x", "autre chose complètement nouvelle là-bas")


def _units(n, rev=False):
    out = []
    for k in range(n):
        de = ANG["de"].replace("X", f"PROD{k}")
        a, b = ANG["old"].replace("X", f"PROD{k}"), ANG["new"].replace("X", f"PROD{k}")
        out.append(dict(d0="20260101", d1="20260201", id=f"P{k}", lang="fr", de0=de, de1=de, t0=b if rev else a, t1=a if rev else b, source="snapshots"))
    return out


def _reg(texts):
    return {"de": {"lim": {f"R{k}": d for k, (d, f) in enumerate(texts)}}, "fr": {"lim": {f"R{k}": f for k, (d, f) in enumerate(texts)}}}


def test_mine_terms_support_reversal_anchor_and_flag():
    J = _reg([(ANG["de"].replace("X", "A"), ANG["new"].replace("X", "A")), (ANG["de"].replace("X", "B"), ANG["old"].replace("X", "B")),
              ("Kostengutsprache nötig.", "Garantie de prise en charge nécessaire."),
              ("Nicht mit einem ACE-Hemmer kombinieren.", "Ne pas combiner avec un inhibiteur de l'ECA.")])
    P = A.mine_terms(_units(2), J)
    assert len(P) == 1 and P[0]["de_term"] == "angiotensin-ii-antagonist" and P[0]["n_limitations"] == 2 and P[0]["dice"] == 1.0
    assert P[0]["old_phrase"].endswith("de l'angiotensine ii") and "PROD" not in P[0]["de_surface"]
    assert not A.mine_terms(_units(1), J)                                    # one limitation, one transition: not kept
    assert not A.mine_terms(_units(2) + _units(1, rev=True), J)              # reverted once: never kept
    hit = A.term_check(J["de"]["lim"]["R1"], J["fr"]["lim"]["R1"], "fr", P)
    assert len(hit) == 1 and "inhibiteur de l'enzyme" in hit[0][1].group(0)
    assert not A.term_check(J["de"]["lim"]["R0"], J["fr"]["lim"]["R0"], "fr", P)          # already corrected
    assert not A.term_check("Die Therapie mit einem ACE-Hemmer.", J["fr"]["lim"]["R1"], "fr", P)   # no German term


def test_shipped_pairs_and_audit_item_notice_on_the_fresh_items():
    P = A.load_terms()
    ang = [p for p in P if p["lang"] == "fr" and p["de_term"] == "angiotensin-ii-antagonist"]
    assert len(ang) == 1 and "inhibiteur de l'enzyme de conversion" in ang[0]["old_phrase"] and "récepteurs" in ang[0]["new_phrase"]
    X = score.load_items("items/items_fresh.json")
    hits = {x["key"]: [f for f in A.audit_item(x) if f["kind"] == "terminology"] for x in X}
    fr = sorted(k for k, v in hits.items() if v and k.endswith("-fr"))
    assert fr == [f"wb{n:03d}-fr" for n in range(15, 33)]                       # the 18 old French texts with the old term
    t = hits["wb015-fr"][0]
    assert t["lang"] == "fr" and t["de_term"].startswith("Angiotensin-II-Antagonist") and t["text"].startswith("l'ancien texte dit")
    assert t["detail"].endswith(".") and not ({"side", "value", "values"} & set(t))      # renders as its own text in explain
    x = next(x for x in X if x["key"] == "wb015-fr")
    assert not [f for f in A.audit_item(x, terms=[]) if f["kind"] == "terminology"]
    assert A.audit_item(x, kinds=("number", "unit", "language", "editorial")) == [f for f in A.audit_item(x) if f["kind"] != "terminology"]


def test_shipped_register_terminology_findings():
    F = json.load(open(os.path.join(A.DEST, "audit_20261006.json"), encoding="utf-8"))["findings"]
    T = [f for f in F if f["kind"] == "terminology"]
    four = {"COVERAM-PLUS", "PERAMLIND.me", "PERAMLIND.sp", "PERINDAMLIND"}
    assert {f["id"] for f in T if f["lang"] == "fr" and "conversion" in f["old"]} == four
    assert [f["fid"] for f in T] == [f"T{k:02d}" for k in range(1, len(T) + 1)]
    for f in T: assert f["corrected_in"] and f["de_term"] and f["first_seen"] and f["likely_equivalent"] is False


def test_likely_equivalent_rules():
    eq = A.equivalence
    assert eq("2", "fr", "une fois tous les deux jours", "an jedem zweiten Tag", "de").startswith("Q2")
    assert eq("2", "it", "una volta ogni due giorni", "a giorni alterni", "it").startswith("Q2")
    assert eq("14", "de", "innerhalb von 14 Tagen", "dans les deux semaines", "fr").startswith("Q1")
    assert eq("18", "de", "Patienten ab 18 Jahren", "pazienti adulti", "it").startswith("Q3")
    assert eq("18", "de", "ab 18 Jahren", "dès dix-huit ans", "fr").startswith("Q4")
    assert eq("12", "de", "ab 12 Jahren", "plus de 11 ans", "fr").startswith("Q5")
    assert eq("8", "de", "alle acht Wochen", "ogni quattro settimane", "it") is None             # a real swap
    assert eq("16", "de", "mindestens 16 kg", "au moins 6 ans", "fr") is None
    assert eq("12", "de", "ab 12 Jahren", "dès 11 ans", "fr") is None                          # both inclusive: different
    f = dict(lang="fr", de_only=[dict(value="14")], tgt_only=[], explained_by=[])
    assert A.likely_equivalent(f, "innerhalb von 14 Tagen", "dans les deux semaines")[0]
    assert A.likely_equivalent(dict(f, explained_by=["E01"]), "x", "y") == (True, "typo: E01 explains the difference")
    assert A.likely_equivalent(dict(f, de_only=[dict(value="14"), dict(value="30")]), "14 Tagen, 30 mg", "deux semaines") == (False, None)


def test_likely_equivalent_never_moves_ids_ranks_or_counts_and_spares_the_labelled_real():
    D = json.load(open(os.path.join(A.DEST, "audit_20261006.json"), encoding="utf-8"))
    N = [f for f in D["findings"] if f["kind"] == "number"]
    assert [f["fid"] for f in N] == [f"N{k:02d}" for k in range(1, 22)] and D["summary"]["findings"] == 21
    assert D["summary"]["likely_equivalent"]["number"] == sum(f["likely_equivalent"] for f in N)
    lab = {(r["cud"], r["lang"]): r["real"] for r in csv.DictReader(open(os.path.join(ROOT, "eval", "labels", "audit_20261006.tsv"), encoding="utf-8"), delimiter="\t")}
    real_eq = [f["fid"] for f in N if f["likely_equivalent"] and lab[(f["id"], f["lang"])] == "yes"]
    assert real_eq == []                                                          # check, not a fit: see docs/audit.md
    for f in D["findings"]: assert isinstance(f["likely_equivalent"], bool)


def _xlsx(path, sheets):
    """a minimal xlsx with inline strings: {sheet name: [[cell, ...], ...]}."""
    col = lambda i: "ABCDEFGHIJKLMNOPQRSTUVWXYZ"[i]
    z = zipfile.ZipFile(path, "w")
    z.writestr("[Content_Types].xml", '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>')
    wb = "".join(f'<sheet name="{n}" sheetId="{k + 1}" r:id="rId{k + 1}"/>' for k, n in enumerate(sheets))
    z.writestr("xl/workbook.xml", '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
               'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>' + wb + "</sheets></workbook>")
    rel = "".join(f'<Relationship Id="rId{k + 1}" Target="worksheets/sheet{k + 1}.xml" Type="x"/>' for k in range(len(sheets)))
    z.writestr("xl/_rels/workbook.xml.rels", '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">' + rel + "</Relationships>")
    for k, rows in enumerate(sheets.values()):
        x = "".join(f'<row r="{i + 1}">' + "".join(f'<c r="{col(j)}{i + 1}" t="inlineStr"><is><t>{v}</t></is></c>' for j, v in enumerate(r) if v) + "</row>"
                    for i, r in enumerate(rows))
        z.writestr(f"xl/worksheets/sheet{k + 1}.xml", '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>' + x + "</sheetData></worksheet>")
    z.close()


def test_list_audit_on_a_synthetic_analysenliste():
    d = tempfile.mkdtemp(prefix="gl-al-"); p = os.path.join(d, "al_20260701.xlsx")
    head = {"de": ["Kapitel", "Pos.-Nr.", "TP", "Bezeichnung", "Limitationen"], "fr": ["Chapitre", "No. Pos.", "PT", "Dénomination", "Limitation"],
            "it": ["Capitolo", "No. pos.", "PT", "Denominazione", "Limitazioni"]}
    rows = {"de": [["A", "1000", "5", "Vitamin D", "Höchstens 4 Mal pro Jahr"], ["A", "1001", "5", "Ferritin", "nach 4Wochen wiederholen"]],
            "fr": [["A", "1000", "5", "Vitamine D", "Au maximum 2 fois par an"], ["A", "1001", "5", "Ferritine", "répéter après 4 semaines"]],
            "it": [["A", "1000", "5", "Vitamina D", "Al massimo 4 volte all'anno"], ["A", "1001", "5", "Ferritina", "ripetere dopo 4 settimane"]]}
    _xlsx(p, {"Deutsch": [head["de"]] + rows["de"], "Français": [head["fr"]] + rows["fr"], "Italiano": [head["it"]] + rows["it"]})
    J, names, info = AL.parse_list("al", p)
    assert info["positions_aligned"] == 2 and J["fr"]["lim"]["1000|Limitation"] == "Au maximum 2 fois par an"
    out = os.path.join(d, "out"); wl = os.path.join(d, "wl")
    rc = A.main(["--list", "al", "--file", p, "--out", out, "--worklist", wl, "--fail-on-findings"])
    R = json.load(open(os.path.join(out, "audit_al_20260701.json"), encoding="utf-8"))
    kinds = sorted((f["kind"], f["lang"], f["position"]) for f in R["findings"])
    assert ("number", "fr", "1000") in kinds and ("editorial", "de", "1001") in kinds and rc == 1
    W = json.load(open(os.path.join(wl, "worklist.json"), encoding="utf-8"))
    assert len(W) == len(R["findings"]) and all("fid" not in w and "rank" not in w for w in W)
    assert A.main(["--list", "al", "--file", p, "--out", out]) == 0          # without the flag the exit code stays 0


if __name__ == "__main__":
    fs = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    for n, f in fs: f(); print("ok", n)
    print(f"{len(fs)} passed")
