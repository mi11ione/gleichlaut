"""PREREG R24: the shipped audit on the seven federal acts behind the SL. The adapter's extraction and alignment on a
synthetic AKN document; the committed texts match the manifest and reproduce the committed findings with the shipped
defaults (round 5 off, no terminology); the labels merge; the committed result is replay's."""
import json, os
from gleichlaut import audit_fedlex as X, score

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")

AKN = """<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"><act><meta><x>1999</x></meta>
<preface><p>832.10</p></preface><body>
<article eId="art_13_a"><num>Art. 13<sup>a</sup></num><heading>Titel<authorialNote marker="1"><p>Fassung vom 1. Jan. 2020</p></authorialNote></heading>
<paragraph eId="art_13_a/para_1"><num>1</num><content><p>Nach Artikel 13<sup>a</sup> gilt eine Frist von 30 Tagen.</p></content></paragraph>
<paragraph eId="art_13_a/para_2"><num>2</num><blockList eId="art_13_a/para_2/blk">
<listIntroduction eId="art_13_a/para_2/listintro">Es gilt:</listIntroduction>
<item eId="art_13_a/para_2/lbl_a"><num>a.</num><p>bis 18 Jahre;</p></item></blockList></paragraph></article>
<level eId="annex_1/lvl_u1"><content><table><tr><td><p>1.</p></td><td><p>Zeile</p><p>zwei</p></td></tr></table></content></level>
</body></act></akomaNtoso>"""


def test_units_eid_leaves_blocks_labels_and_footnotes():
    U = X.units(AKN.encode())
    assert U["art_13_a/para_1"] == "Nach Artikel 13a gilt eine Frist von 30 Tagen."          # num left out, sup glued
    assert U["art_13_a/para_2/listintro"] == "Es gilt:" and U["art_13_a/para_2/lbl_a"] == "bis 18 Jahre;"
    assert U["art_13_a/heading[0]"] == "Titel"                                                   # footnote left out
    assert U["annex_1/lvl_u1/content[0]/table[0]/tr[0]/td[1]"] == "Zeile zwei"
    assert U["/act[0]/preface[0]/p[0]"] == "832.10" and not any("1999" in t for t in U.values())   # meta skipped
    assert X.ref("art_52_a/para_2_bis/lbl_b") == "Art. 52a para. 2bis let. b" and X.ref("art_25/para_2/lbl_a/lbl_2_bis") == "Art. 25 para. 2 let. a no. 2bis"


def test_corpus_is_the_preregistered_one_and_matches_the_manifest():
    man = json.load(open(X.MANIFEST, encoding="utf-8")); T = X.load_texts()
    assert [a for _, a, _ in X.ACTS] == ["KVG", "KVV", "KLV", "HMG", "VAM", "AMZV", "VAZV"]
    assert set(man["acts"]) == set(T["acts"]) == set(sr for sr, _, _ in X.ACTS)
    for sr, a in man["acts"].items():
        assert not a.get("missing") and a["version"] <= man["run_date"] and set(a["files"]) == set(X.LANGS)
        assert all(f["url"].startswith("https://www.fedlex.admin.ch/filestore/") for f in a["files"].values())
        assert T["manifest_sha256"][sr] == {L: f["sha256"] for L, f in a["files"].items()}
        assert all(set(t) == set(X.LANGS) and all(t.values()) for t in T["acts"][sr]["texts"].values())
    assert sum(len(a["texts"]) for a in T["acts"].values()) == 5991


def test_findings_reproduce_with_the_shipped_defaults():
    T = X.load_texts(); F, S = X.run(T)
    C = json.load(open(X.OUT, encoding="utf-8"))
    assert [(f["id"], f["lang"], f["fid"]) for f in F] == [(f["id"], f["lang"], f["fid"]) for f in C["findings"]]
    assert S["checks"].endswith("r5=False") and set(f["kind"] for f in F) <= {"number", "unit", "language", "editorial"}
    assert len(F) == 26 and S["by_kind"]["number"] == 26


def test_labels_merge_and_result_is_replays():
    rows = X.merge()
    assert open(os.path.join(ROOT, "eval", "labels", "audit_fedlex.tsv"), encoding="utf-8").read().splitlines() == X.merged_lines(rows)
    W = json.load(open(os.path.join(ROOT, "eval", "labels", "audit_fedlex_worklist.json"), encoding="utf-8"))
    assert len(W) == len(rows) == 26 and all(set(w) == {"id", "act", "ref", "kind", "lang", "de", "fr", "it", "finding", "question"} for w in W)
    r = score.audit_fedlex()
    assert json.loads(json.dumps(r)) == json.load(open(os.path.join(ROOT, "eval", "results", "audit_fedlex.json"), encoding="utf-8"))
    assert r["confirmed"] == sum(x["final_confirmed"] == "yes" for x in rows) and r["findings"] == 26
