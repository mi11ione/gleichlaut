"""Edits saved on the live months: re-derived from the recorded shadow drafts and the committed result."""
import json, os, sys
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(H, "..", "src"))
from gleichlaut import score

def test_live_edits_match_committed_result_and_save_edits():
    r = score.live_edits()
    c = json.load(open(os.path.join(H, "..", "eval", "results", "live_edits.json"), encoding="utf-8"))
    assert r == c
    q, b = r["q8_0"]["pooled"], r["70b"]["pooled"]
    assert q["n"] == b["n"] == 63
    assert q["edits_saved_ci95"][0] > 0 and b["edits_saved_ci95"][0] > 0      # both lanes save edits on live data
