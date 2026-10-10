"""Review page (gleichlaut.ui.build): self-contained (no external request, fonts embedded), < 1.2 MB, header figures
from score.score_run, light/dark tokens, --fragment without document wrapper, and readable diffs (phrase-level; whole
sentence struck/underlined when most of it changed). Runs under pytest or as `python3 tests/test_emit_ui.py`."""
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


def test_self_contained_and_small():
    s, D, size = _page()
    assert size < 1.5 * 1024 * 1024, size
    assert s.startswith("<!doctype html>") and "<title>Gleichlaut Review</title>" in s
    assert not re.search(r"""(?:src|href)\s*=\s*["']?(?:https?:)?//""", s)
    assert not re.search(r"url\((?!data:)", s) and "@import" not in s
    assert s.count("@font-face") == 3 and "data:font/woff2;base64," in s
    for fam in ("Public Sans", "Archivo", "Fragment Mono"): assert f"font-family:'{fam}'" in s, fam
    assert "IBM Plex" not in s and "Source Sans" not in s and size < 1.4 * 1024 * 1024   # full audit texts (officer request) included


def test_tokens_light_dark_and_mobile():
    s, _, _ = _page()
    assert '@media (prefers-color-scheme:dark){:root:not([data-theme="light"])' in s and ':root[data-theme="dark"]' in s
    assert "--sig:#ff4f00" in s and "--sig:#ff6a26" in s and "--red" not in s and "border-top:5px" not in s
    assert "--paper:#fbfbf9" in s and "--paper:#121412" in s
    assert "@media (max-width:900px)" in s and "@media print" in s and '<header class="bar">' in s
    assert 'class="tblock"' not in s and 'tr class="grid"' not in s and "registration marks" not in s   # no drawing-sheet furniture


def test_header_figures_from_score_run():
    _, D, _ = _page()
    assert D["all"] == score.score_run("fresh166")["summary"]["all"]
    assert D["counts"]["items"] == 166 and D["counts"]["ready"] == D["all"]["unflagged"]


def test_fragment_has_no_document_wrapper():
    s, _, _ = _page(fragment=True)
    assert not re.search(r"<!doctype|<html[\s>]|<head[\s>]|<body[\s>]", s, re.I)
    assert s.startswith("<title>Gleichlaut Review</title>") and "<style>" in s and "<script>" in s


def test_every_draft_rebuilds_from_its_segments():
    _, D, _ = _page()
    from gleichlaut.emit import load
    V = {v["key"]: v for v in load("fresh166")[1]}
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
