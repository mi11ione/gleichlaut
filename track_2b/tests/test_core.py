"""Frozen code, lock, slots, guards: behaviour pinned on real items from the recorded runs."""
import json, os
from gleichlaut import core, score, backends


def test_freeze_matches():
    assert core.verify_freeze(strict=False) == []


def test_frozen_modules_are_the_vendored_copies():
    assert core.lock.__file__.startswith(core.FROZEN) and core.guards.__file__.startswith(core.FROZEN)
    assert core.guards.V2 is True and core.guards3.VMIN == 5


def test_slots_round_trip_and_no_digit_reaches_the_model():
    x = next(i for i in score.load_items("items/items_fresh.json") if any(c.isdigit() for c in i["tgt_old"]))
    S = core.gl2.Slots(x["tgt_old"])
    masked = [S.mask(x["de_old"], "de"), S.mask(x["de_new"], "de"), S.mask(x["tgt_old"], x["lang"])]
    assert not any(c.isdigit() for m in masked for c in m)            # the prompt carries slot codes only
    assert S.unmask(masked[2], x["lang"]) == x["tgt_old"]              # code writes every value back


def test_lock_accepts_identity_and_rejects_an_edit_outside_every_window():
    x = score.load_items("items/items_fresh.json")[0]
    assert core.lock.check(x["de_old"], x["de_new"], x["tgt_old"], x["tgt_old"])["ok"]
    t = core.lock.tok(x["tgt_old"]); W, _ = core.lock.windows(x["de_old"], x["de_new"], x["tgt_old"])
    inside = set(j for lo, hi in W for j in range(lo, hi + 1))
    j = next(j for j in range(len(t)) if j not in inside and t[j].isalpha() and len(t[j]) > 3)
    out = x["tgt_old"].replace(t[j], t[j] + "x", 1)
    assert not core.lock.check(x["de_old"], x["de_new"], x["tgt_old"], out)["ok"]


def test_guards_flag_known_bad_and_pass_known_good():
    """labels from the hand check of the fresh run: a German-left draft is flagged, every labelled-good unflagged one passes."""
    I = {x["key"]: x for x in score.load_items("items/items_fresh.json")}
    F = score.load_jsonl("runs/70b_fresh166_g3_final.jsonl"); P = core.check_only("g3")
    assert P.check(I["wb013-it"], F["wb013-it"]["out"])["flag"]                       # German left in
    good = [k for k, c in score.load_labels("fresh166_unflagged.tsv").items() if c == "equivalent"]
    assert good and not any(P.check(I[k], F[k]["out"])["flag"] for k in good)


def test_guard_names_german_left_in_a_draft():
    x = score.load_items("items/items_fresh.json")[0]
    out = x["tgt_old"] + " Folgender Indikationscode ist zu übermitteln."
    r = core.check_only("g3").check(x, out)
    assert r["flag"] and r["g"]["g1"]


def test_slot_guard_catches_a_changed_number():
    import re
    g = core.lock.guard
    x = next(i for i in score.load_items("items/items_fresh.json")
             if re.search(r"\d", i["tgt_old"]) and not g(i["de_old"], i["de_new"], i["tgt_old"], i["tgt_old"], i["lang"]))
    m = re.search(r"\d+", x["tgt_old"]); out = x["tgt_old"][:m.start()] + str(int(m.group(0)) + 1) + x["tgt_old"][m.end():]
    assert "nums" in g(x["de_old"], x["de_new"], x["tgt_old"], out, x["lang"])


def test_reexecution_from_recorded_responses_small():
    """the first 12 fresh items re-run through the frozen pipeline with the cache backend reproduce their records."""
    I = score.load_items("items/items_fresh.json")[:12]; F = score.load_jsonl("runs/70b_fresh166_g3_final.jsonl")
    ask = backends.Cache(os.path.join(core.ROOT, "data", "cache", "responses")); P = core.Pipeline(ask, "g3")
    for x in I:
        r = P.run(x)
        assert (r["out"], r["guard_flag"]) == (F[x["key"]]["out"], F[x["key"]]["guard_flag"]), x["key"]
    assert not ask.misses


def test_cache_miss_is_an_error_not_a_call():
    ask = backends.Cache(os.path.join(core.ROOT, "data", "cache", "responses"))
    try: ask("a prompt nobody recorded", "t", 0, 10)
    except KeyError: return
    raise AssertionError("cache miss must raise")
