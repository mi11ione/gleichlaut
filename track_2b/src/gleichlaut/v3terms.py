"""Pipeline variant "v3-terms" (PREREG R12; experimental, not the certified default): the frozen pipeline with ONE added
block in the drafting prompt listing BAG's own house French/Italian wording for the terms and fixed sentences that occur in
the item's new German text.

Everything else is the frozen code, executed exactly as gleichlaut.core runs it: the same prompt PA (the block is
inserted between the list of German changes and the old target text), the same lock check and retry, the same guard
stack (frozen guards3), the same single re-ask (whose prompt starts with the drafting prompt, so it carries the block
too), the same slot codes. frozen/ is not touched: the variant sets the template the frozen run_2b / reask.run read, per
item, and restores it afterwards. An item whose new German has no house term and no house sentence gets the frozen
prompt byte for byte.

House wording source (no leakage): the termbase (gleichlaut.termbase) and the house sentences (gleichlaut.house), mined
by the unchanged mining code from ONE snapshot given by date, data/termbase/r12/{termbase,house_sentences}_<date>.json.
For a shadow month <from> -> <to> the snapshot is <from>: it holds only FR/IT published before the month, never the
month's own published FR/IT (which first appears in <to>).

Block rules (fixed with R12, before any run):
  T  terms: every termbase entry of the item's language with a house rendering (house=true) whose German term (the
     termbase's own regex, HEAD_RX) occurs in de_new; shown as "German term -> house rendering", in order of first
     occurrence in de_new.
  S  sentences: every sentence of de_new (emit.segment.sentences) whose normalised key (house.key) has a house sentence
     (house=true) in the item's language; shown as the German sentence as written in de_new -> BAG's house wording. The
     house wording shows numbers as '…'; they are filled with the German sentence's numbers in order when the counts
     match, else the sentence is left out. Then both sides are written with the prompt's slot codes (gl2.Slots, the
     same assignment as the prompt: de_old, de_new, target old, change list), so no digit reaches the model.
  No entry with 'no dominant rendering' is used (as the termbase/house advisories). Duplicates are listed once."""
import json, os, re
from . import core

VARIANT = "v3-terms"
DIR = os.path.join(core.ROOT, "data", "termbase", "r12")
ANCHOR = "\n\n{L} (old): {tgt_old}"
HEAD = ("BAG's established {L} wording in the Spezialitätenliste for terms and sentences of the German (new) text, "
        "taken from BAG's published {L} texts. Where the amended part contains them, use exactly this {L} wording:")
NUM = re.compile(r"\d+(?:[.,'’]\d+)*")


def paths(date):
    return (os.path.join(DIR, f"termbase_{date}.json"), os.path.join(DIR, f"house_sentences_{date}.json"))


def resources(date):
    """-> (terms {(lang, term): entry}, sentences {(lang, key): entry}) mined from the snapshot `date`; both must exist."""
    from . import termbase, house
    tp, hp = paths(date)
    for p in (tp, hp):
        if not os.path.exists(p):
            raise FileNotFoundError(f"v3-terms: {p} missing (mine it: gleichlaut termbase --date {date} --json ... --house ...)")
    return termbase.load(tp), house.load(hp)


def entries(x, date, R=None):
    """-> [dict(kind 'term'|'sentence', de, tgt)] for item x (unmasked text), in order of first occurrence in de_new."""
    from . import termbase, house
    from .emit.segment import sentences
    T, H = R or resources(date)
    L, de = x["lang"], x["de_new"]
    out, seen = [], set()
    for (lang, term), e in T.items():
        if lang != L: continue
        m = termbase.HEAD_RX[term].search(de)
        if m: out.append((m.start(), dict(kind="term", de=term, tgt=e["preferred"])))
    d = house._nrm(de)
    for a, b in sentences(d):
        s = d[a:b].strip(); e = H.get((L, house.key(s)))
        if not e: continue
        nums = NUM.findall(s); t = e["text"]
        if t.count("…") != len(nums): continue                      # S: numbers cannot be placed: left out
        for n in nums: t = t.replace("…", n, 1)
        out.append((a, dict(kind="sentence", de=s, tgt=t)))
    res = []
    for _, r in sorted(out, key=lambda p: (p[0], p[1]["kind"] != "sentence")):
        k = (r["kind"], r["de"], r["tgt"])
        if k not in seen: seen.add(k); res.append(r)
    return res


def block(x, date, R=None):
    """-> the block as it appears in the prompt (slot codes for numbers), or "" when the item has no house wording."""
    E = entries(x, date, R)
    if not E: return ""
    gl2, lock = core.gl2, core.lock
    S = gl2.Slots(x["tgt_old"]); L = x["lang"]
    S.mask(x["de_old"], "de"); S.mask(x["de_new"], "de"); S.mask(x["tgt_old"], L)
    a, b, ops = lock.de_ops(x["de_old"], x["de_new"]); S.mask(gl2.changes_list(a, b, ops), "de")
    lines = [HEAD.format(L=core.LNAME[L])]
    for e in E:
        de, tg = S.mask(e["de"], "de"), S.mask(e["tgt"], L)
        lines.append(f"- {de} -> {tg}" if e["kind"] == "term" else f"- «{de}» -> «{tg}»")
    return "\n".join(lines)


def template(PA, blk):
    """the frozen template PA with the block inserted before the old target text ('' -> PA unchanged)."""
    assert PA.count(ANCHOR) == 1, "frozen prompt anchor not found once"
    if not blk: return PA
    esc = blk.replace("{", "{{").replace("}", "}}")
    return PA.replace(ANCHOR, "\n\n" + esc + ANCHOR)


class TermsPipeline(core.Pipeline):
    """core.Pipeline with the v3-terms block: per item the frozen template is swapped for the template with the block
    (draft, retry and re-ask all format it), then restored."""

    def __init__(self, ask, date, stack="g3"):
        super().__init__(ask, stack)
        self.date, self.R, self.PA0 = date, resources(date), self.ns["PA"]
        assert self.PA0.count(ANCHOR) == 1

    def prompt_template(self, x):
        return template(self.PA0, block(x, self.date, self.R))

    def _with(self, x, fn):
        self.ns["PA"] = self.prompt_template(x)
        try: return fn()
        finally: self.ns["PA"] = self.PA0

    def draft(self, x):
        return self._with(x, lambda: core.Pipeline.draft(self, x))

    def reask(self, rec, x):
        return self._with(x, lambda: core.Pipeline.reask(self, rec, x))

    def run(self, x):
        r = self.reask(self.draft(x), x)
        return dict(r, variant=VARIANT, terms_date=self.date, terms_block=block(x, self.date, self.R))


def blocks(items, date):
    """-> {key: block} for an item list (the prompt additions, for the record committed with R12)."""
    R = resources(date)
    return {x["key"]: block(x, date, R) for x in items}
