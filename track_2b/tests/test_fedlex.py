"""Fedlex lane: vendoring, replay with the recorded raw outputs, scorer reproduction, live-slice rule, mining smoke test.
No model is called. Research-tree comparisons skip (unittest.SkipTest) when spikes/gleichschritt is absent."""
import functools, os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from gleichlaut.core import sha256
from gleichlaut.fed import lane, score
from gleichlaut.fed.ingest import Fedlex, SPIKES

GS = os.path.join(SPIKES, "gleichschritt")


def need(path, what):
    if not os.path.exists(os.path.join(GS, path)): raise unittest.SkipTest(f"{what} not present ({GS})")


@functools.lru_cache(None)
def research():
    return score.research_scores()                    # (scores, printed table, sha256 of scores.json)


def test_vendored_hashes():
    assert lane.verify(strict=False) == []


def test_vendored_byte_identical_to_research():
    need("gleich.py", "research tree")
    with open(os.path.join(lane.RES, "SHA256SUMS")) as fh: sums = [l.split() for l in fh if l.strip()]
    for h, f in sums: assert sha256(os.path.join(GS, f)) == h, f
    assert sha256(os.path.join(GS, "lock.py")) == lane.LOCK_SHA          # reused as core.lock, not copied twice
    for mine, theirs in ((lane.ITEMS, "items.json"), (lane.RUN_A, "results/A.jsonl"), (lane.RUN_B, "results/B.jsonl"),
                         (score.CONTAM, "results/s2_contamination.json")):
        assert sha256(mine) == sha256(os.path.join(GS, theirs)), theirs


def test_replay_recorded_raw_outputs():
    """The rigour step: gleich.py's run_A, executed with a fake `ask` that returns the recorded raw generations, rebuilds
    every recorded field of all 150 A records (cleaned outputs, lock checks, retry decisions and prompts, flags); the
    shipped lane (code lane, corrected arm A, slot guard) gives exactly the research scorer's A+code rows; run_B rebuilds B."""
    r = score.replay_check(rows=research()[0]["rows"])
    assert r["mismatches"] == [], r["mismatches"][:5]
    assert (r["n"]["asrun"], r["n"]["armB"], r["n"]["asrun_retried"], r["n"]["shipped_retried"]) == (150, 155, 25, 12)


def test_scores_json_byte_identical_to_research():
    assert research()[2] == score.RESEARCH_SCORES_SHA


def test_results_md_numbers_reproduce():
    bad = [c for c in score.checks(research()[0], score.jl(lane.RUN_A)) if not c["ok"]]
    assert bad == [], bad


def test_fake_ask_sees_the_research_prompt():
    x = lane.load(lane.LIVE5)["items"][0]
    rp = score.Replay(["first", "second"]); r = lane.arm_a(x, rp)
    assert len(rp.prompts) == 1 + r["retried"]
    assert rp.prompts[0].startswith("A Swiss legal provision was amended in German. Apply exactly the same amendment to the French version.")
    assert rp.max_tokens[0] == int(max(1, len(x["tgt_old"]) // 3) * 2.2) + 60


def test_live_selection_rule():
    live = lane.load(lane.LIVE5); xs = live["items"]
    assert [x["key"] for x in lane.select_live(lane.load(lane.ITEMS))] == [x["key"] for x in xs]
    assert live["rule"] == lane.LIVE_RULE
    assert [x["lang"] for x in xs] == ["fr", "it", "fr", "it", "fr"] and len({x["act"] for x in xs}) == 5
    for x in xs:
        assert lane.lock.code_lane(x["de_old"], x["de_new"], x["tgt_old"], x["lang"])[1] is None and not lane.is_cluster(x)


def test_live_slice_with_recorded_outputs():
    A = score.jl(lane.RUN_A); xs = lane.load(lane.LIVE5)["items"]
    def ask(prompt, tag, cap, max_tokens):            # each prompt -> its item's recorded first generation
        x = [x for x in xs if f"(old): {x['tgt_old']}\n" in prompt]
        assert len(x) == 1
        return A[x[0]["key"]]["raw1"], {"model_served": "replay"}
    rows = lane.live_slice(ask)
    assert [r["draft"] for r in rows] == [x["recorded_8b_dwq"]["out"] for x in xs]
    assert [r["exact"] for r in rows] == [x["recorded_8b_dwq"]["exact"] for x in xs]
    assert [r["status"] for r in rows] == [x["recorded_8b_dwq"]["status"] for x in xs]
    assert all(lane.format_row(r) for r in rows)


def test_digit_ban_lifted_only_during_a_fedlex_call():
    class Masked:
        bad = {"fr": [1, 2], "it": [3]}
        def __call__(self, prompt, tag, cap, max_tokens):
            assert all(len(v) == 0 for v in self.bad.values())
            return "x", {}
    b = Masked(); x = lane.load(lane.LIVE5)["items"][0]
    lane.fed_draft(x, b)
    assert b.bad == {"fr": [1, 2], "it": [3]}


EFZ = "cc/2011/251/2026-06-01#art_2/para_1/lbl_e|fr"     # "Köchin EFZ": draft keeps the old job title, writes German "EFZ"


def test_shipped_lane_flags_the_efz_item():
    x = {i["key"]: i for i in lane.load(lane.ITEMS)}[EFZ]
    r = score.replay_record(x, score.jl(lane.RUN_A)[EFZ])
    assert r["status_research"] == "ready" and not r["exact"]          # lock + slot guard alone pass it
    assert r["status"] == "flagged" and r["g14"]["flag"]                 # G1-G4 catch it
    assert lane.g14_text(r["g14"]) != "ok" and "G1-G4=" in lane.format_row(dict(
        key=EFZ, lang="fr", status=r["status"], lane=r["lane"], retried=r["retried"], lock_ok=r["lock_ok"], guard=r["guard"],
        g14=r["g14"], exact=r["exact"], recorded_8b_dwq_exact=False, secs=0.0, de_old="", de_new="", tgt_old="", draft=r["out"]))


def test_shipped_lane_counts_dev():
    """DEV numbers (G1-G4 added after reading these outputs): 25 newly flagged (1 exact), 38/120 flagged, 25 unflagged non-exact."""
    sh, _ = score.shipped()
    a = sh["all"]
    assert (a["n"], a["exact"], a["flagged"], a["newly_flagged_by_g1_g4"], a["newly_flagged_exact"], a["flagged_research"]) == (120, 60, 38, 25, 1, 13)
    assert len(sh["unflagged_non_exact_keys"]) == 25 and EFZ in sh["newly_flagged_keys"]


def test_rm_draft_is_never_ready():
    x = next(i for i in lane.load(lane.ITEMS) if i["lang"] == "rm" and i["src"] == "fed")
    assert lane.fed_draft(x, lambda *a: (x["tgt_new"], {}))["status"] == "flagged"


def test_ingest_offline_miss_fetches_nothing():
    assert Fedlex(online=False, caches=[]).versions("cc/2011/28") == {}


def test_remine_research_items_from_cache():
    need("cache", "research cache")
    from gleichlaut.fed.mine import smoke
    r = smoke()
    assert (r["reproduced"], r["missing"], r["differing"]) == (120, [], []), r


if __name__ == "__main__":
    for n, f in sorted(globals().items()):
        if n.startswith("test_"):
            try: f(); print("ok  ", n)
            except unittest.SkipTest as e: print("skip", n, e)
