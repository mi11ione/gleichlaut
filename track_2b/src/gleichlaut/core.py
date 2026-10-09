"""Loads the frozen research code (frozen/, hash-checked) and exposes the pipeline pieces it defines.

Nothing here re-implements the pipeline. Prompts, cleaners, the drafting loop (run_2b), the guard stack (full_check),
the complaint text and the re-ask (run) are executed from the frozen source files via `ast`, the same way the
original fresh-set run (frozen/run_v2.py) executed them, with only the model call (`ask`) injected."""
import ast, hashlib, json, os, re, sys, time

PKG = os.path.dirname(os.path.abspath(__file__))
FROZEN = os.path.join(PKG, "frozen")
ROOT = os.path.dirname(os.path.dirname(PKG))           # track_2b/
FREEZE = os.path.join(ROOT, "eval", "prereg", "freeze.json")
LNAME = {"fr": "French", "it": "Italian"}
M70 = "swiss-ai/apertus-v1.5-70b"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()


def verify_freeze(strict=True):
    """-> list of (path, expected, actual) mismatches. strict: raise on any mismatch."""
    rec = json.load(open(FREEZE))
    bad = []
    for e in rec["files"]:
        p = os.path.join(ROOT, e["path"])
        got = sha256(p) if os.path.exists(p) else "MISSING"
        if got != e["sha256"]: bad.append((e["path"], e["sha256"], got))
    if bad and strict:
        raise SystemExit("FREEZE MISMATCH:\n" + "\n".join(f"  {p}: expected {a[:12]} got {b[:12]}" for p, a, b in bad))
    return bad


# ---------------------------------------------------------------- import the frozen modules
# frozen/s2 first on sys.path and lock/gl2 pre-imported, so the inert absolute sys.path lines inside the frozen files
# can never shadow these copies.
for _d in (os.path.join(FROZEN, "s2"), os.path.join(FROZEN, "gl"), os.path.join(FROZEN, "g3")):
    if _d not in sys.path: sys.path.insert(0, _d)
import lock, gl2                     # noqa: E402  (frozen/s2)
import guards3                       # noqa: E402  (frozen/g3; imports frozen/gl/guards.py and sets V2 = True)
import guards                        # noqa: E402
assert guards.V2 is True
assert os.path.dirname(os.path.abspath(lock.__file__)) == os.path.join(FROZEN, "s2"), lock.__file__
assert os.path.dirname(os.path.abspath(guards.__file__)) == os.path.join(FROZEN, "gl"), guards.__file__


def _extract(path, names, ns):
    """exec only the top-level definitions/assignments called `names` from a frozen file into ns."""
    src = open(path, encoding="utf-8").read(); found = set()
    for node in ast.parse(src).body:
        n = None
        if isinstance(node, ast.FunctionDef): n = node.name
        elif isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name): n = node.targets[0].id
        if n in names:
            exec(compile(ast.Module([node], []), path, "exec"), ns); found.add(n)
    missing = set(names) - found
    assert not missing, (path, missing)
    return ns


def _ntok(s): return max(1, len(s) // 3)
def _digits(s): return len(re.findall(r"\d", s))


class Pipeline:
    """One configured pipeline: frozen code + an `ask(prompt, tag, cap, max_tokens) -> (text, meta)` backend.

    draft(x)       -> run_2b record (whole-paragraph locked rewrite, lock check, one retry)       [frozen gl70.run_2b]
    reask(rec, x)  -> final record (full guard stack; one re-ask kept only if it passes all)     [frozen reask.run]
    check(x, out)  -> full guard verdict                                                          [frozen reask.full_check]"""

    def __init__(self, ask, stack="g3"):
        """stack: "g3" = guards3 (G1-G7; the frozen guard of the fresh-set test, the shipped default);
                  "v2" = guards.py V2 only (G1-G4; the guard of the dev-120 and out-of-sample-242 runs)."""
        assert stack in ("g3", "v2"), stack
        self.stack = stack
        ns = {"re": re, "time": time, "json": json, "LNAME": LNAME, "lock": lock, "gl2": gl2,
              "guards": guards3 if stack == "g3" else guards,
              "ntok": _ntok, "digits": _digits, "ask": ask, "TAG": "gl-70b-v2", "CAP": 1.0}
        _extract(os.path.join(FROZEN, "s2", "s2b.py"), ("PA", "RETRY", "clean", "chk"), ns)
        ns["clean_full"] = ns["clean"]
        _extract(os.path.join(FROZEN, "gl", "gl70.py"), ("run_2b",), ns)
        _extract(os.path.join(FROZEN, "gl", "reask.py"), ("FIX", "full_check", "complaints", "run"), ns)
        self.ns = ns
        self.PA, self.RETRY, self.FIX = ns["PA"], ns["RETRY"], ns["FIX"]

    def draft(self, x):
        return self.ns["run_2b"](x)

    def reask(self, rec, x):
        self.ns.setdefault("items", {})[x["key"]] = x       # reask.run looks the item up by key
        return self.ns["run"](rec)

    def check(self, x, out):
        return self.ns["full_check"](x, out)

    def complaints(self, x, out):
        S = gl2.Slots(x["tgt_old"])
        S.mask(x["de_old"], "de"); S.mask(x["de_new"], "de"); S.mask(x["tgt_old"], x["lang"])
        return self.ns["complaints"](x, S, self.check(x, out), LNAME[x["lang"]])

    def run(self, x):
        return self.reask(self.draft(x), x)


def check_only(stack="g3"):
    """A pipeline whose backend refuses to be called: for re-guarding cached outputs."""
    def ask(*a, **k): raise RuntimeError("check-only pipeline: no model calls")
    return Pipeline(ask, stack)


SCORE = _extract(os.path.join(FROZEN, "s2", "score2.py"), ("edits", "f1", "chrf", "score_one", "boot_diff"),
                 {"re": re, "difflib": __import__("difflib"), "random": __import__("random"),
                  "Counter": __import__("collections").Counter, "defaultdict": __import__("collections").defaultdict,
                  "gl2": gl2, "lock": lock, "tok": lock.tok, "norm": lock.norm})
