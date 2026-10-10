"""Dreiklang comparison (code): typed candidates -> normalised condition tuples per language -> multiset comparison.

tuple = (subject, operator, value, unit) with time units in days (year 365, month 30, week 7), g/ug in mg.
For each CUD and each tuple t, with counts c_l = number of candidates in language l typed as t:
  present in all three          -> ACCEPTED (distinct tuple); if the counts differ also a COUNT flag (secondary)
  present in exactly two        -> 2:1 flag, odd language = the missing one
  present in exactly one        -> PRESENCE flag, odd language = the one that has it
"""
import collections, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cands import norm_value_unit  # noqa: E402

LANGS = ("de", "fr", "it")


def tuples(cands, labels, use_label_unit=False):
    """cands: candidate dicts; labels: list of None | dict(subj, op[, unit]) -> Counter of tuples and tuple->candidate idxs"""
    cnt, src = collections.Counter(), collections.defaultdict(list)
    for c, g in zip(cands, labels):
        if g is None:
            continue
        u = g.get("unit") if use_label_unit else (c["u"] or "")
        v, un = norm_value_unit(c["v"], u)
        t = (g["subj"], g["op"], v, un)
        cnt[t] += 1
        src[t].append(c["idx"])
    return cnt, src


def compare(per_lang):
    """per_lang: {lang: Counter(tuple)} -> accepted set, flags list"""
    allt = set().union(*[set(per_lang[l]) for l in LANGS])
    accepted, flags = set(), []
    for t in sorted(allt, key=str):
        c = {l: per_lang[l][t] for l in LANGS}
        present = [l for l in LANGS if c[l] > 0]
        if len(present) == 3:
            accepted.add(t)
            if len(set(c.values())) > 1:
                vals = list(c.values())
                odd = next((l for l in LANGS if vals.count(c[l]) == 1), None) if len(set(vals)) == 2 else None
                flags.append(dict(kind="count", t=t, counts=c, odd=odd))
        elif len(present) == 2:
            flags.append(dict(kind="2:1", t=t, counts=c, odd=next(l for l in LANGS if c[l] == 0)))
        else:
            flags.append(dict(kind="presence", t=t, counts=c, odd=present[0]))
    return accepted, flags


def fmt_t(t):
    s, o, v, u = t
    return f"{s}{o}{v}{(' ' + u) if u else ''}"
