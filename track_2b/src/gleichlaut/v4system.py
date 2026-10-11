"""Pipeline variant "v4-system" (PREREG R21; experimental, not the certified default): the v3-terms variant (PREREG R12,
gleichlaut.v3terms: BAG's house wording as one block in the drafting prompt, unchanged) plus ONE fixed system message
that replaces the chat template's default system turn ("You are Apertus 1.5 Omni, a multimodal assistant ...";
docs/research/chat-template.md). The developer turn the template always adds ("Deliberation: disabled / Tool
Capabilities: disabled") stays as it is.

Everything else is the frozen code, executed as gleichlaut.core runs it (prompt, lock check and retry, guards3, one
re-ask, slot codes, routing), through v3terms.TermsPipeline. frozen/ is not touched. The system message is added at the
model call: every request the pipeline sends (draft, lock retry, re-ask) carries it, and nothing else changes. With the
variant off, no backend is ever given a system message, so the request is the frozen one byte for byte
(tests/test_r21.py).

House wording per item (no leakage): mined by the unchanged mining code from the snapshot BEFORE the item's change, the
item's own `snap_old`: 20250601 / 20250701 for the fresh 166 (BAG's 2025 XML captures, tools/r21_system.py mine ->
data/termbase/r21/), 20260801 / 20260901 for the live months (the R12 files, data/termbase/r12/)."""
import hashlib, os
from . import core, v3terms

VARIANT = "v4-system"
SYSTEM = ("You maintain the French and Italian versions of Swiss drug-reimbursement limitations (BAG Spezialitätenliste). "
          "When the German text of a limitation is amended, you amend the French or Italian text: change only what the "
          "German change requires, keep every other word of the old text, use BAG's established terminology given in the "
          "request, and output only the amended paragraph.")
SYSTEM_SHA256 = hashlib.sha256(SYSTEM.encode("utf-8")).hexdigest()
DIRS = (os.path.join(core.ROOT, "data", "termbase", "r12"), os.path.join(core.ROOT, "data", "termbase", "r21"))


def paths(date):
    """(termbase, house sentences) of the snapshot `date`: data/termbase/r12 (2026 live months) or r21 (2025 captures)."""
    for d in DIRS:
        tp, hp = os.path.join(d, f"termbase_{date}.json"), os.path.join(d, f"house_sentences_{date}.json")
        if os.path.exists(tp) and os.path.exists(hp): return tp, hp
    raise FileNotFoundError(f"v4-system: no mined house wording for snapshot {date} in data/termbase/r12 or r21 "
                            f"(tools/r21_system.py mine for the 2025 captures)")


def resources(date):
    from . import termbase, house
    tp, hp = paths(date)
    return termbase.load(tp), house.load(hp)


def terms_date(x, date=None):
    """the snapshot the item's house wording comes from: `date` if given, else the item's own old snapshot."""
    d = date or (x.get("snap_old") or "").replace("-", "")[:8]
    if not d: raise ValueError(f"{x.get('key')}: no snap_old and no terms date")
    return d


class SystemAsk:
    """wraps a backend: every call carries the system message (backends take `system=`; None = the frozen request)."""

    def __init__(self, ask, system=SYSTEM):
        object.__setattr__(self, "ask", ask); object.__setattr__(self, "system", system)

    def __getattr__(self, k): return getattr(self.ask, k)

    def __call__(self, prompt, tag, cap, max_tokens):
        return self.ask(prompt, tag, cap, max_tokens, system=self.system)


class SystemPipeline(v3terms.TermsPipeline):
    """v3terms.TermsPipeline (the house-wording block, per item from the item's own old snapshot unless `date` is given)
    whose model calls all carry SYSTEM."""

    def __init__(self, ask, date=None, stack="g3"):
        core.Pipeline.__init__(self, SystemAsk(ask), stack)
        self.date, self.RR, self.PA0 = date, {}, self.ns["PA"]
        assert self.PA0.count(v3terms.ANCHOR) == 1

    def _R(self, x):
        d = terms_date(x, self.date)
        if d not in self.RR: self.RR[d] = resources(d)
        return d, self.RR[d]

    def block(self, x):
        d, R = self._R(x)
        return v3terms.block(x, d, R)

    def prompt_template(self, x):
        return v3terms.template(self.PA0, self.block(x))

    def run(self, x):
        r = self.reask(self.draft(x), x)
        return dict(r, variant=VARIANT, terms_date=terms_date(x, self.date), terms_block=self.block(x), system_sha256=SYSTEM_SHA256)


class Captured(Exception):
    def __init__(self, prompt, max_tokens, system): self.prompt, self.max_tokens, self.system = prompt, max_tokens, system


def capture(prompt, tag, cap, max_tokens, system=None):
    """a backend that sends nothing: raises Captured with the request (for the pre-registered prompt record)."""
    raise Captured(prompt, max_tokens, system)


def first_request(P, x):
    """-> (user prompt, max_tokens, system) of the first model call for item x, or None (rule-only: no model call)."""
    try: P.draft(x)
    except Captured as c: return c.prompt, c.max_tokens, c.system
    return None


class Recorded:
    """replays a run's own exchanges.jsonl (one line per model call: the full request and the response text as the
    pipeline received it). The key is
    the sha256 of the rebuilt request (backends.payload_key, system message included), so a hit proves the request was
    rebuilt byte for byte. A miss raises KeyError."""

    def __init__(self, path):
        import json
        self.E = {}
        for l in open(path, encoding="utf-8"):
            e = json.loads(l); self.E[e["key"]] = e
        self.model = next(iter(self.E.values()))["request"]["model"] if self.E else None
        self.hits, self.misses = 0, []

    def __call__(self, prompt, tag, cap, max_tokens, system=None):
        from . import backends
        k = backends.payload_key(self.model, prompt, max_tokens, 0.0, system=system)
        if k not in self.E:
            self.misses.append(k); raise KeyError(f"no recorded exchange for request {k[:16]}")
        self.hits += 1
        return self.E[k]["response"], dict(cached=True, key=k)


class Recorder:
    """wraps a live backend and appends every exchange (request as sent, response text) to a JSONL file."""

    def __init__(self, ask, path):
        object.__setattr__(self, "ask", ask); object.__setattr__(self, "path", path)

    def __getattr__(self, k): return getattr(self.ask, k)

    def __call__(self, prompt, tag, cap, max_tokens, system=None):
        import json
        from . import backends
        text, meta = self.ask(prompt, tag, cap, max_tokens, system=system)
        msgs = ([{"role": "system", "content": system}] if system is not None else []) + [{"role": "user", "content": prompt}]
        rec = dict(key=backends.payload_key(self.ask.model, prompt, max_tokens, 0.0, system=system),
                   request=dict(model=self.ask.model, messages=msgs, max_tokens=max_tokens, temperature=0.0),
                   response=text, prompt_tokens=meta.get("prompt_tokens"),
                   completion_tokens=meta.get("completion_tokens"), secs=meta.get("secs"), tag=tag)
        assert rec["key"] == meta.get("key", rec["key"]), "backend key differs from the recorded request"
        with open(self.path, "a", encoding="utf-8") as f: f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        return text, meta
