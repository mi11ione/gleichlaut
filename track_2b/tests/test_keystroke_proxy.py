"""Typing-time lower bound (keystroke-level model): the counting rule on small cases, and the committed result re-derived."""
import json, os, sys
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(H, "..", "src"))
from gleichlaut import score


def test_keystroke_counting_rule():
    assert score.keystrokes("abc", "abc") == (0, 0)
    assert score.keystrokes("", "abc") == (3, 3)                   # every inserted character is one keystroke
    assert score.keystrokes("abcdef", "af") == (1, 4)              # one deleted run: 1 (conservative) vs 4 per character
    assert score.keystrokes("le 5 mai", "le 6 mai") == (2, 2)      # a replaced character: delete run + insert
    assert score.KLM_K["good_typist_90wpm"] == 0.12 and score.KLM_K["average_non_secretary_typist_40wpm"] == 0.28


def test_keystroke_proxy_matches_committed_result():
    r = score.keystroke_proxy()
    c = json.load(open(os.path.join(H, "..", "eval", "results", "keystroke_proxy.json"), encoding="utf-8"))
    assert r == c
    q = r["fresh166"]["q8_0"]; vol = r["method"]["fr_it_items_per_month"]
    assert q["n"] == 166 and q["keystrokes_saved"] == q["keystrokes_from_rules"] - q["keystrokes_from_draft"]
    assert q["keystrokes_saved_per_text_ci95"][0] > 0                 # the default saves keystrokes on the held-out set
    m = q["keystrokes_saved"] / q["n"] * score.KLM_K["good_typist_90wpm"] * vol / 60
    assert abs(m - q["minutes_per_month_at_volume"]["good_typist_90wpm"]) < 0.05
    # the conservative variant (deleted runs) never claims more than counting every deleted character
    for lane in ("q8_0", "70b"):
        e = r["fresh166"][lane]
        assert e["keystrokes_saved_per_text"] <= e["per_char_deletion"]["keystrokes_saved_per_text"]
    assert r["live"]["q8_0"]["pooled"]["n"] == r["live"]["70b"]["pooled"]["n"] == 63
