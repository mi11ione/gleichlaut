"""Fedlex lane (Gleichschritt): a German federal paragraph was amended -> draft the matching FR/IT amendment.

Nothing here re-implements the research loop. The arm-A prompt (PA), the retry text (RETRY), the cleaner (clean), the
change list (changes_list), the language names (LNAME) and the loops themselves (gen, run_A, run_B) are executed from
the vendored research file research/gleich.py via `ast`, exactly as core.py does for the SL lane. Only model I/O is
injected: gleich.py called MLX `generate(model, tok, prompt=chat(p), max_tokens=...)`; here `generate` calls
`ask(prompt, tag, cap, max_tokens)` (any backend from gleichlaut.backends; they apply the chat template themselves, so
`chat` is the identity) and `tok.encode` only counts tokens for max_tokens = int(2.2 n) + 60.

fed_draft(x, ask)  code lane first (lock.code_lane: numbers, dates, SR/article numbers; no model); otherwise arm A:
                   whole-paragraph locked rewrite -> lock.check -> one retry with the out-of-span complaint -> flag.
                   The lock is computed on apostrophe/space-normalised text and ' -> ’ is restored deterministically,
                   i.e. the corrected pipeline that research/score.py:corrected() replays and that results.md reports.
                   Then the slot guard (negation / modal / number deltas must mirror the German).
arm_a(x, ask, corrected=False) the verbatim as-run loop of the Air run (lock on raw text), for the replay test.
arm_b(x, ask)      free translation of DE_new (the naive contrast).
live_slice(ask)    the 5 fixed items of data/items/fedlex_live5.json (`make run` step 4).

Scope: FR/IT. gleich.py also names Romansh (rm: "Romansh (Rumantsch Grischun)"); RM runs but is exploratory only
(results.md: the model wrote 1/22 RM items exactly)."""
import contextlib, json, os, re, sys, time
from .. import core
from ..core import lock, sha256, _extract

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "research")
DATA = os.path.join(core.ROOT, "data")
ITEMS = os.path.join(DATA, "items", "fedlex_items.json")
LIVE5 = os.path.join(DATA, "items", "fedlex_live5.json")
RUN_A, RUN_B = (os.path.join(DATA, "runs", f"8b_dwq_fedlex_{a}.jsonl") for a in "AB")
LOCK_SHA = "1409b2ad5f5acc68bc9ace45620f86131681ec6e33d9d30d62b3ad0141f9c29f"   # gleichschritt/lock.py == frozen/s2/lock.py
SCOPE = ("fr", "it")
TAG, CAP = "fedlex-8b", 0.5
MEM = "\0gleichlaut-mem"            # OUT dir for run_A/run_B: os.path.exists() is False for it, writes go to _Sink


def load(p):
    with open(p, encoding="utf-8") as f: return json.load(f)


def verify(strict=True):
    """sha256 of the vendored research files (research/SHA256SUMS) and of the shared lock. -> mismatches."""
    bad = []
    with open(os.path.join(RES, "SHA256SUMS")) as fh: sums = [l.split() for l in fh if l.strip()]
    for h, f in sums:
        got = sha256(os.path.join(RES, f)) if os.path.exists(os.path.join(RES, f)) else "MISSING"
        if got != h: bad.append((f, h, got))
    if sha256(lock.__file__) != LOCK_SHA: bad.append(("lock.py", LOCK_SHA, sha256(lock.__file__)))
    if bad and strict: raise SystemExit("FEDLEX RESEARCH MISMATCH: " + ", ".join(f for f, _, _ in bad))
    return bad


verify()


class _NormLock:
    """lock as score.py:corrected() replays it: check() on norm()-alised target text (the as-run lock counted the 8B's
    ’ -> ' as an out-of-span edit). Everything else is the frozen lock."""
    def __getattr__(self, k): return getattr(lock, k)
    @staticmethod
    def check(de_old, de_new, tgt_old, out): return lock.check(de_old, de_new, lock.norm(tgt_old), lock.norm(out))


class _Tok:
    """Stands in for the MLX tokenizer; gleich.py uses it only to count target tokens for max_tokens."""
    def __init__(self, n=None): self.n = n or (lambda s: max(1, len(s) // 3))
    def encode(self, s): return [0] * self.n(s)


class _Sink:
    """open(path, "a").write(line) of run_A/run_B lands here instead of a file."""
    def __init__(self): self.lines = []
    def __call__(self, path, mode="r", *a, **k):
        assert path.startswith(MEM) and mode == "a", (path, mode)
        return self
    def write(self, s): self.lines.append(s)


_SRC = {}
def _ns(ask, corrected, ntok=None):
    """fresh namespace with the gleich.py definitions and the model I/O injected."""
    calls = []
    def generate(model, tok, prompt, max_tokens, verbose=False):
        text, meta = ask(prompt, TAG, CAP, max_tokens); calls.append(dict(prompt=prompt, max_tokens=max_tokens, meta=meta))
        return text
    ns = {"json": json, "os": os, "time": time, "re": re, "lock": _NormLock() if corrected else lock,
          "generate": generate, "model": None, "chat": lambda user: user, "tok": _Tok(ntok), "OUT": MEM,
          "open": _Sink(), "print": lambda *a, **k: None, "_calls": calls}
    return _extract(os.path.join(RES, "gleich.py"),
                    ("LNAME", "gen", "clean", "changes_list", "PA", "RETRY", "PB", "done_ids", "run_A", "run_B"), ns)


G = _ns(None, False)                                   # the research definitions, for inspection
LNAME, PA, RETRY, PB, clean, changes_list = (G[k] for k in ("LNAME", "PA", "RETRY", "PB", "clean", "changes_list"))
S = _extract(os.path.join(RES, "score.py"), ("restore_apos", "is_cluster", "flip"), {"lock": lock, "re": re})
restore_apos, is_cluster = S["restore_apos"], S["is_cluster"]


def _ntok_of(ask):
    llm = getattr(ask, "llm", None)                    # backends.LlamaCpp: count with the real Apertus tokenizer
    return (lambda s: len(llm.tokenize(s.encode("utf-8"), add_bos=False))) if llm is not None else None


def _run(fn, x, ask, corrected):
    ns = _ns(ask, corrected, _ntok_of(ask)); ns["items"] = [x]
    ns[fn]()
    assert len(ns["open"].lines) == 1, (fn, x["key"], "no record (empty tgt_old?)")
    return dict(json.loads(ns["open"].lines[0]), calls=ns["_calls"])


def arm_a(x, ask, corrected=False):
    """gleich.py run_A on one item -> its record {key, raw1, out1, check1, secs1, retried, [raw2, out2, check2, secs2],
    out, lock_ok, flagged_lock, secs} plus `calls` (prompt, max_tokens, backend meta per model call)."""
    return _run("run_A", x, ask, corrected)


def arm_b(x, ask):
    return _run("run_B", x, ask, False)


@contextlib.contextmanager
def nomask(backend):
    """backends.LlamaCpp bans digit tokens and number words (the SL lane's slot design). The Fedlex prompt carries the
    numbers verbatim and the research run had no ban, so the ban is lifted for the duration of a Fedlex call."""
    bad = getattr(backend, "bad", None)
    if bad is not None: backend.bad = {L: v[:0] for L, v in bad.items()}
    try: yield backend
    finally:
        if bad is not None: backend.bad = bad


def sl_guards(x, out):
    """The frozen SL guard stack v2 (core.guards = frozen/gl/guards.py, V2 = True): G1 German left in the target, G2 change
    not applied, G3 content dropped / removed without a German reason, G4 duplication. Not guards3 G5-G7 (their
    whitelist / vocabulary / term resources are built from the SL corpus). FR/IT only: guards.py has no RM function-word
    list, so an RM draft gets g=None and is never ready (RM is exploratory)."""
    if x["lang"] not in SCOPE: return None
    return core.guards.run(dict(de_old=x["de_old"], de_new=x["de_new"], tgt_old=x["tgt_old"], lang=x["lang"]), out)


def fed_draft(x, ask):
    """The shipped Fedlex lane: code lane, else corrected arm A; lock + slot guard (= the research verdict of results.md
    "A+code", kept as flagged_research / status_research); then G1-G4 (sl_guards). Ready only if all of them pass.
    DEV caveat: adding G1-G4 to this lane was decided after seeing these recorded outputs."""
    told = x["tgt_old"]
    app, code = lock.code_lane(x["de_old"], x["de_new"], told, x["lang"])
    if code is not None:
        r = dict(key=x["key"], lane="code", out=code, retried=False, lock_ok=True, flagged_lock=False, secs=0.0, calls=[])
    else:
        with nomask(ask): r = dict(arm_a(x, ask, corrected=True), lane="model")
        r["out"] = restore_apos(told, r["out"])
    g = lock.guard(x["de_old"], x["de_new"], lock.norm(told), lock.norm(r["out"]), x["lang"])
    r.update(code_applicable=app, guard=g, flagged_research=r["flagged_lock"] or bool(g))
    r["status_research"] = "flagged" if r["flagged_research"] else "ready"
    G = sl_guards(x, r["out"])
    r.update(g14=G, flagged=r["flagged_research"] or G is None or G["flag"])
    r["status"] = "flagged" if r["flagged"] else "ready"
    if x.get("tgt_new"): r["exact"] = lock.norm(r["out"]) == lock.norm(x["tgt_new"])
    return r


# ---------------------------------------------------------------- live slice (make run step 4)
LIVE_RULE = """From data/items/fedlex_items.json take the federal FR/IT items (src == "fed") that the model must draft:
lock.code_lane() produces no output and the item is not in the SEFRI mass-amendment cluster (score.py:is_cluster).
Sort them by (len(de_old) + len(de_new) + len(tgt_old), key) and pick greedily, shortest first: pick i must be in
language ("fr", "it")[i % 2] and from an act not picked yet. Stop at 5 (3 FR + 2 IT, 5 distinct acts)."""


def select_live(items, n=5):
    cand = [x for x in items if x["src"] == "fed" and x["lang"] in SCOPE and not is_cluster(x)
            and lock.code_lane(x["de_old"], x["de_new"], x["tgt_old"], x["lang"])[1] is None]
    cand.sort(key=lambda x: (len(x["de_old"]) + len(x["de_new"]) + len(x["tgt_old"]), x["key"]))
    out, acts = [], set()
    for x in cand:
        if len(out) == n: break
        if x["lang"] == SCOPE[len(out) % 2] and x["act"] not in acts: out.append(x); acts.add(x["act"])
    return out


def build_live5(path=LIVE5):
    """(re)write data/items/fedlex_live5.json: the 5 items plus what the recorded MLX-DWQ 8B run did on them."""
    items = load(ITEMS)
    from .score import replay_record, jl
    A = jl(RUN_A)
    sel = []
    for x in select_live(items):
        r = replay_record(x, A[x["key"]])
        sel.append(dict(x, recorded_8b_dwq=dict(out=r["out"], exact=r["exact"], status=r["status"], status_research=r["status_research"],
                                                guard=r["guard"], g14=r["g14"],
                                                retried=r["retried"], secs=round(A[x["key"]]["secs"], 2))))
    with open(path, "w", encoding="utf-8") as fh: json.dump(dict(rule=LIVE_RULE, source="data/items/fedlex_items.json", recorded="data/runs/8b_dwq_fedlex_A.jsonl",
                   items=sel), fh, ensure_ascii=False, indent=1)
    return sel


def live_slice(ask, path=LIVE5):
    """Draft the 5 live items with `ask`; lock check + slot guard + G1-G4; -> printable rows."""
    rows = []
    for x in load(path)["items"]:
        t0 = time.time(); r = fed_draft(x, ask)
        rows.append(dict(key=x["key"], lang=x["lang"], de_old=x["de_old"], de_new=x["de_new"], tgt_old=x["tgt_old"],
                         draft=r["out"], lane=r["lane"], retried=r["retried"], lock_ok=r["lock_ok"], guard=r["guard"],
                         g14=r["g14"], status=r["status"], status_research=r["status_research"], exact=r.get("exact"), secs=round(time.time() - t0, 2),
                         recorded_8b_dwq_exact=x["recorded_8b_dwq"]["exact"],
                         served=[c["meta"].get("model_served") for c in r["calls"]]))
    return rows


def g14_text(G):
    if G is None: return "n/a (RM: not ready)"
    bad = [f"{k.upper()}:{G[k]}" for k in ("g1", "g2", "g3", "g4") if G[k]]
    return "; ".join(bad) if bad else "ok"


def format_row(r):
    head = (f"--- {r['key']}  [{r['lang']}]  {r['status'].upper()}  lane={r['lane']} retried={r['retried']} "
            f"lock={'ok' if r['lock_ok'] else 'FAIL'} slot-guard={','.join(r['guard']) or 'ok'} G1-G4={g14_text(r['g14'])}  "
            f"exact-vs-official={'yes' if r['exact'] else 'no'} (recorded MLX-DWQ 8B: {'yes' if r['recorded_8b_dwq_exact'] else 'no'})  {r['secs']:.1f}s")
    return "\n".join([head] + [f"  {k:8s} {r[k]}" for k in ("de_old", "de_new", "tgt_old", "draft")])


def show(rows, file=sys.stdout):
    for r in rows: print(format_row(r), file=file)
    n = len(rows)
    print(f"live slice: {sum(r['status'] == 'ready' for r in rows)}/{n} ready, {sum(bool(r['exact']) for r in rows)}/{n} exact vs official, "
          f"{sum(r['secs'] for r in rows):.1f}s", file=file)
