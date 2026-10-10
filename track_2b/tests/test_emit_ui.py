"""Review page (gleichlaut.ui.build): self-contained (no external request, fonts embedded), the lanes it carries (the
certified 8B Q8_0 run first, header figures from score.m1 as in its certificate; the 70B fewer-edits lane from
score.score_run; the live months from their records), the default lane's data < 1.3 MB and the whole page < 3.2 MB
(each lane is parsed only when shown), light/dark tokens, --fragment without document wrapper, a single run by --run
(q8_0_rerun included), and readable diffs (phrase-level; whole sentence struck/underlined when most of it changed).
Runs under pytest or as `python3 tests/test_emit_ui.py`."""
import json, os, re, sys, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from gleichlaut import score
from gleichlaut.ui import build

_C = {}
def _page(fragment=False):
    k = "frag" if fragment else "full"
    if k not in _C:
        p = os.path.join(tempfile.mkdtemp(prefix="gl-ui-"), "index.html"); _, D = build.build(out=p, fragment=fragment)
        _C[k] = (open(p, encoding="utf-8").read(), D, os.path.getsize(p))
    return _C[k]


def _blobs(s):
    return {m.group(1): json.loads(m.group(2).replace("<\\/", "</"))
            for m in re.finditer(r'<script type="application/json" id="(data[^"]*)">(.*?)</script>', s, re.S)}


def test_self_contained_and_small():
    s, D, size = _page()
    assert size < 3.2 * 1024 * 1024, size
    B = _blobs(s); assert list(B) == ["data", "data-70b", "data-aug2026", "data-sep2026"]
    assert len(json.dumps(B["data"], ensure_ascii=False)) < 1.3 * 1024 * 1024
    assert s.startswith("<!doctype html>") and "<title>Gleichlaut Review</title>" in s
    assert not re.search(r"""(?:src|href)\s*=\s*["']?(?:https?:)?//""", s)
    assert not re.search(r"url\((?!data:)", s) and "@import" not in s
    assert s.count("@font-face") == 3 and "data:font/woff2;base64," in s
    for fam in ("Public Sans", "Archivo", "Fragment Mono"): assert f"font-family:'{fam}'" in s, fam
    assert "IBM Plex" not in s and "Source Sans" not in s   # full audit texts (officer request) included, in the default lane only
    assert all(B[k]["audit"] is None for k in B if k != "data")


def test_tokens_light_dark_and_mobile():
    s, _, _ = _page()
    assert '@media (prefers-color-scheme:dark){:root:not([data-theme="light"])' in s and ':root[data-theme="dark"]' in s
    assert "--sig:#ff4f00" in s and "--sig:#ff6a26" in s and "--red" not in s and "border-top:5px" not in s
    assert "--paper:#fbfbf9" in s and "--paper:#121412" in s
    assert "@media (max-width:900px)" in s and "@media print" in s and '<header class="bar">' in s
    assert 'class="tblock"' not in s and 'tr class="grid"' not in s and "registration marks" not in s   # no drawing-sheet furniture


def test_header_figures_from_score_run():
    s, D, _ = _page()
    assert D["meta"]["run"] == "q8_0" and D["meta"]["lane"] == "8b" and D["meta"]["lane_id"] == "8b"     # the default lane first
    assert D["all"] == score.m1("q8_0")                       # scored with its blind labels, as in the build certificate
    cert = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "eval", "certificates", "8b-q8_0-fresh166.json"), encoding="utf-8"))
    m = cert["metrics"]
    assert (D["all"]["exact"]["model"], D["all"]["ready_rate"], D["all"]["unflagged"], D["all"]["pass"]) == (m["exact"]["model"], m["ready_rate"], m["unflagged"], True)
    assert (m["exact"]["model"], m["ready_rate"], m["unflagged"]) == (17.5, 37.3, 62)                        # the README's numbers
    assert D["meta"]["run_sha256"] == cert["run_records_sha256"] and D["meta"]["model"] == cert["models_served"][0]
    assert D["counts"]["items"] == 166 and D["counts"]["ready"] == D["all"]["unflagged"]
    B = _blobs(s); L = {x["id"]: x for x in D["lanes"]}
    assert [x["id"] for x in D["lanes"]] == ["8b", "70b", "aug2026", "sep2026"] and L["70b"]["lane"] == "70b"
    assert all(L[k]["lane"] == "8b" for k in ("8b", "aug2026", "sep2026"))
    assert B["data-70b"]["all"] == score.score_run("fresh166")["summary"]["all"] and B["data-70b"]["meta"]["run"] == "fresh166"
    for k, m in (("aug2026", "20260801-20260901"), ("sep2026", "20260901-20261001")):           # live months: the shadow records
        sm = json.load(open(os.path.join(score.DATA, "shadow", m, "q8_0", "summary.json"), encoding="utf-8"))
        c = B["data-" + k]["counts"]
        assert (c["items"], c["ready"], c["flagged"], c["human"]) == (sm["items"], sm["status"]["ready"], sm["status"]["flagged"], sm["status"]["human"])
        assert (c["exact"], c["exact_of"]) == (sm["shadow"]["exact"], sm["shadow"]["compared"]), (k, c)
        assert B["data-" + k]["meta"]["model"] == D["meta"]["model"] and B["data-" + k]["meta"]["live"]


def test_single_run_pages_including_the_q8_0_rerun():
    from gleichlaut.emit import load, MODEL, M8_Q8_0
    assert MODEL["q8_0"] == MODEL["q8_0_rerun"] == M8_Q8_0
    meta, V = load("q8_0_rerun"); assert meta["model"] == M8_Q8_0 and len(V) == 166
    p = os.path.join(tempfile.mkdtemp(prefix="gl-ui-r-"), "index.html"); _, D = build.build("q8_0_rerun", out=p, audit=None)
    s = open(p, encoding="utf-8").read()
    assert D["meta"]["lane"] == "8b" and [x["id"] for x in D["lanes"]] == ["run"] and 'id="data-' not in s
    assert D["counts"]["ready"] == D["all"]["unflagged"] == 62           # the rerun repeats the certified run's outputs


def test_fragment_has_no_document_wrapper():
    s, _, _ = _page(fragment=True)
    assert not re.search(r"<!doctype|<html[\s>]|<head[\s>]|<body[\s>]", s, re.I)
    assert s.startswith("<title>Gleichlaut Review</title>") and "<style>" in s and "<script>" in s


def test_every_draft_rebuilds_from_its_segments():
    _, D, _ = _page()
    from gleichlaut.emit import load
    V = {v["key"]: v for v in load("q8_0")[1]}
    for g in D["groups"]:
        for it in g["items"].values():
            assert "".join(s[1] for s in it["segs"] if s[0] != "d") == V[it["key"]]["draft"], it["key"]
        assert "".join(s[1] for s in g["de"] if s[0] != "d") == V[next(iter(g["items"].values()))["key"]]["de_new"]


def test_phrase_level_and_whole_sentence_diffs():
    S = build.diff("Die Therapie wird alle vier Wochen vergütet. Danach Ende.", "Die Therapie wird alle acht Wochen vergütet. Danach Ende.")
    assert [s for s in S if s[0] != "e"] == [["d", "vier"], ["i", "acht"]]
    S = build.diff("Gleich. Der Patient muss vorher zum Arzt.", "Gleich. Eine neue Regel gilt ab sofort für alle.")
    assert ["d", "Der Patient muss vorher zum Arzt.", "s"] in S and ["i", "Eine neue Regel gilt ab sofort für alle."] in S
    S = build.diff("a b c d e f g h i j", "a X c Y e f g h i j")             # changes 1 word apart merge into one phrase
    assert [s for s in S if s[0] != "e"] == [["d", "b c d"], ["i", "X c Y"]]


if __name__ == "__main__":
    fs = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    for n, f in fs: f(); print("ok", n)
    print(f"{len(fs)} passed")
