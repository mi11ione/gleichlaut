"""PREREG R12: the experimental pipeline variant v3-terms (gleichlaut.v3terms). The frozen code is untouched and still
hash-verified; the variant adds exactly one block to the drafting prompt and nothing else; the block's house wording comes
only from the month's OLD snapshot; numbers appear as the prompt's slot codes. Runs under pytest or as
`python3 tests/test_v3terms.py`."""
import json, os, re, subprocess, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from gleichlaut import core, cli, v3terms as V

MONTHS = {"20260801-20260901": "20260801", "20260901-20261001": "20260901"}


def _items(m): return json.load(open(os.path.join(core.ROOT, "data", "shadow", m, "items.json"), encoding="utf-8"))


def _prompt(P, x):
    try: P.draft(x)
    except cli._Captured as c: return c.prompt
    return None


def test_frozen_code_untouched():
    assert core.verify_freeze(strict=False) == []


def test_variant_adds_only_the_block():
    for m, d in MONTHS.items():
        F, T = core.Pipeline(cli._capture, "g3"), V.TermsPipeline(cli._capture, d)
        n = changed = 0
        for x in _items(m):
            if cli.route(x)[0] == "human": continue
            pf, pv = _prompt(F, x), _prompt(T, x)
            if pf is None: assert pv is None; continue
            n += 1; b = V.block(x, d)
            if not b: assert pv == pf; continue
            changed += 1
            assert pv.replace("\n\n" + b, "", 1) == pf, x["key"]          # frozen prompt + one block, nothing else
            assert pv.index(b) < pv.index("\n\n" + core.LNAME[x["lang"]] + " (old): ")      # before the old target text
            assert not re.search(r"\d", b), (x["key"], b)                  # numbers only as slot codes
            assert T.ns["PA"] is T.PA0                                     # template restored after every call
        assert n and changed


def test_house_wording_from_the_old_snapshot_only():
    for m, d in MONTHS.items():
        tp, hp = V.paths(d)
        for p in (tp, hp):
            meta = json.load(open(p, encoding="utf-8"))["meta"]
            assert meta["date"] == d and meta["date"] < m[9:], (p, meta["date"])
        assert all(x["snap_old"].replace("-", "")[:8] == d for x in _items(m) if x.get("snap_old")), m


def test_block_rules():
    x = dict(key="t", lang="fr", de_old="Folgender Code ist an den Krankenversicherer zu übermitteln: 20481.01",
             de_new="Folgender Indikationscode ist an den Krankenversicherer zu übermitteln: 20481.01",
             tgt_old="Le code suivant doit être transmis à l'assurance maladie: 20481.01")
    E = V.entries(x, "20260801")
    assert dict(kind="sentence", de="Folgender Indikationscode ist an den Krankenversicherer zu übermitteln:",
                tgt="Le code d'indication suivant doit être transmis à l'assureur-maladie:") in E
    assert dict(kind="term", de="Krankenversicherer", tgt="assureur-maladie") in E
    b = V.block(x, "20260801")
    assert b.startswith("BAG's established French wording") and "\n- Krankenversicherer -> assureur-maladie" in b
    none = dict(x, de_new="Keine Fachbegriffe hier.", de_old="Keine Begriffe hier.", tgt_old="Pas de termes ici.")
    assert V.entries(none, "20260801") == [] and V.block(none, "20260801") == ""
    PA = core.Pipeline(cli._capture, "g3").PA
    assert V.template(PA, "") is PA and V.template(PA, "a {b}").format(L="French", de_old="", de_new="", changes="", tgt_old="").count("a {b}") == 1


def test_committed_blocks_reproduce():
    r = subprocess.run([sys.executable, os.path.join(core.ROOT, "tools", "r12_terms.py"), "--check"], capture_output=True, text=True,
                       env=dict(os.environ, PYTHONPATH=os.path.join(core.ROOT, "src")))
    assert r.returncode == 0, r.stdout + r.stderr


def test_cli_variant_dry_run_and_usage():
    import io
    x = [y for y in _items("20260801-20260901") if cli.route(y)[0] != "human"][:2]
    buf = io.StringIO(); cli.dry_run(x, "sl", out=buf, variant="v3-terms", terms_date="20260801")
    assert "BAG's established" in buf.getvalue()
    for bad in (dict(variant="v3-terms", terms_date=None), dict(variant="v3-terms", terms_date="19990101"), dict(variant="nope")):
        try: cli._pipeline(cli._capture, **bad); raise AssertionError(bad)
        except cli.UsageError: pass


def test_r12_scorer_frozen_arm_matches_r10():
    """the R12 scorer's frozen columns are the R10 numbers for August (same records, labels and criteria)."""
    import unittest
    from gleichlaut import score
    if not all(os.path.exists(os.path.join(core.ROOT, "data", "shadow", m, f"v3_terms_{mo}", "records.jsonl"))
               for m in MONTHS for mo in ("q8_0", "70b")):
        raise unittest.SkipTest("R12 runs not recorded")
    r = score.r12_terms(); s = score.shadow_month("20260801-20260901", r0=True)
    for m in ("q8_0", "70b"):
        f, ref = r["months"]["20260801-20260901"][m]["frozen"], s["r0"][m]["month"]
        assert f["criteria"] == ref["criteria"] and f["meets_r0"] == ref["meets_r0"] and f["n"] == ref["n"] and f["exact"] == ref["exact"]
        assert r["months"]["20260801-20260901"][m]["paired"]["prompt_unchanged"] >= 1


if __name__ == "__main__":
    for n, f in sorted(globals().items()):
        if n.startswith("test_"): f(); print("ok", n)
