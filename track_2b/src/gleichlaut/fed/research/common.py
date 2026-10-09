"""Shared text utilities: tokenisation, change ratio, repeal detection, normalisation. stdlib only."""
import re, difflib
TOK = re.compile(r"\d+(?:[.,'’]\d+)*|\w+|[^\w\s]")


def tok(s): return TOK.findall(s)


def norm(s):
    s = s.replace(" ", " ").replace(" ", " ").replace("’", "'").replace("­", "")
    return re.sub(r"\s+", " ", s).strip()


def ops(a, b):
    """token opcodes a->b (non-equal only)."""
    ta, tb = tok(a), tok(b)
    sm = difflib.SequenceMatcher(None, ta, tb, autojunk=False)
    return ta, tb, [o for o in sm.get_opcodes() if o[0] != "equal"]


def change_ratio(a, b):
    ta, tb = tok(a), tok(b)
    sm = difflib.SequenceMatcher(None, ta, tb, autojunk=False)
    same = sum(m.size for m in sm.get_matching_blocks())
    return 1 - same / max(1, max(len(ta), len(tb)))


REPEAL = re.compile(r"^\s*(?:\d+[a-z]*\s*)?(?:…|\.\.\.)?\s*(aufgehoben|abrogé|abrogée|abrogés|abrogées|abrogato|abrogata|abrogati|abrogate|abolì|abolida|abolids|abolidas|abolì\.|\.\.\.|…)?\s*\.?\s*$", re.I)


def is_repeal(s):
    return bool(REPEAL.match(s))
