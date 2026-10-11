"""PREREG R21: the experimental variant v4-system (gleichlaut.v4system) = v3-terms + one fixed system message. With the
variant off, the request a backend sends is the frozen one byte for byte; with it on, the system message is the only
difference from v3-terms (and from the frozen prompt where no house wording applies). Runs under pytest or as
`python3 tests/test_r21.py`."""
import hashlib, json, os, re, subprocess, sys, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from gleichlaut import core, cli, backends, v3terms, v4system as V

ROOT = core.ROOT
SETS = ("fresh166", "20260801-20260901", "20260901-20261001")


def _items(s):
    if s == "fresh166": return json.load(open(os.path.join(ROOT, "data", "items", "items_fresh.json"), encoding="utf-8"))
    return [x for x in json.load(open(os.path.join(ROOT, "data", "shadow", s, "items.json"), encoding="utf-8")) if cli.route(x)[0] != "human"]


def _called(s):
    """items of set s whose drafting calls the model (not rule-only)."""
    return [x for x in _items(s) if V.first_request(V.SystemPipeline(V.capture), x)]


class _FakeLlm:
    def __init__(self): self.sent = []
    def create_chat_completion(self, **kw):
        self.sent.append(kw); return dict(choices=[dict(message=dict(content="texte"))], usage=dict(prompt_tokens=3, completion_tokens=1))


def _llamacpp():
    b = object.__new__(backends.LlamaCpp)
    b.llm, b.LP, b.np, b.lang_of_prompt, b.log, b.record_to = _FakeLlm(), list, None, backends.lang_of_prompt, None, None
    b.model, b.endpoint, b.bad = "gguf:q8_0.gguf", "local", {"fr": [], "it": []}
    return b


def test_frozen_code_untouched():
    assert core.verify_freeze(strict=False) == []


def test_variant_off_request_is_byte_identical():
    """no system message: the same messages and the same request key as before R21 (the R9 key formula, written out)."""
    b = _llamacpp(); p = "Apply exactly the same amendment to the French version.\nFrench (old): x"
    _, meta = b(p, "gl-70b-v2", 1.0, 401)
    assert b.llm.sent[0]["messages"] == [{"role": "user", "content": p}]
    old = hashlib.sha256(json.dumps(dict(model="gguf:q8_0.gguf", messages=[{"role": "user", "content": p}], max_tokens=401,
                                         temperature=0.0), sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    assert meta["key"] == old == backends.payload_key("gguf:q8_0.gguf", p, 401, 0.0)
    _, meta2 = b(p, "gl-70b-v2", 1.0, 401, system=V.SYSTEM)
    assert b.llm.sent[1]["messages"] == [{"role": "system", "content": V.SYSTEM}, {"role": "user", "content": p}]
    a0, a1 = b.llm.sent
    assert meta2["key"] != old and set(a0) == set(a1) and all(a0[k] == a1[k] for k in a0 if k not in ("messages", "logits_processor"))
    # the frozen and the v3-terms pipelines never pass a system message
    seen = []
    def ask(prompt, tag, cap, mt, **kw): seen.append(kw); raise cli._Captured(prompt, mt)
    x = _called("20260901-20261001")[0]
    for P in (core.Pipeline(ask, "g3"), v3terms.TermsPipeline(ask, "20260901")):
        try: P.draft(x)
        except cli._Captured: pass
    assert seen == [{}, {}]
    # replay of the recorded frozen runs is unchanged: the R9 cache keys still resolve
    c = backends.Cache(os.path.join(ROOT, "data", "cache", "responses_8b", "q8_0"), model="gguf:q8_0.gguf")
    P = core.Pipeline(c, "g3"); x = json.load(open(os.path.join(ROOT, "data", "items", "items_fresh.json"), encoding="utf-8"))[0]
    P.run(x); assert c.hits >= 1 and not c.misses


def test_system_message_is_the_only_difference():
    for s in SETS:
        F = core.Pipeline(cli._capture, "g3"); Vp = V.SystemPipeline(V.capture); n = same = 0
        for x in _items(s):
            try: F.draft(x); pf = None
            except cli._Captured as c: pf = c.prompt
            r = V.first_request(Vp, x)
            if pf is None: assert r is None; continue
            prompt, mt, system = r; n += 1
            assert system == V.SYSTEM
            d = V.terms_date(x); b = v3terms.block(x, d, V.resources(d))
            assert prompt == (pf.replace("\n\n" + core.LNAME[x["lang"]] + " (old): ", "\n\n" + b + "\n\n" + core.LNAME[x["lang"]] + " (old): ", 1) if b else pf), x["key"]
            same += not b
            assert Vp.ns["PA"] is Vp.PA0
        assert n
    # the live months: the user prompt is exactly R12's v3-terms prompt (its pre-registered sha256)
    r12 = json.load(open(os.path.join(ROOT, "eval", "prereg", "r12_blocks.json"), encoding="utf-8"))["months"]
    r21 = json.load(open(os.path.join(ROOT, "eval", "prereg", "r21_prompts.json"), encoding="utf-8"))["sets"]
    for m in SETS[1:]:
        for k, r in r12[m]["items"].items():
            assert r21[m]["items"][k]["prompt_sha256_v4"] == r["prompt_sha256_v3"] and r21[m]["items"][k]["block"] == r["block"], (m, k)


def test_system_text_and_hash_as_registered():
    assert V.SYSTEM_SHA256 == hashlib.sha256(V.SYSTEM.encode("utf-8")).hexdigest()
    pre = open(os.path.join(ROOT, "eval", "prereg", "PREREG.md"), encoding="utf-8").read()
    sec = pre[pre.index("## R21."):]; sec = sec[:sec.index("\n## ", 5)]
    assert V.SYSTEM_SHA256 in sec and V.SYSTEM in re.sub(r"\s*\n\s*", " ", sec)
    d = json.load(open(os.path.join(ROOT, "eval", "prereg", "r21_prompts.json"), encoding="utf-8"))
    assert d["system"] == V.SYSTEM and d["system_sha256"] == V.SYSTEM_SHA256
    assert not re.search(r"\d", V.SYSTEM)                       # no digit reaches the model (slot codes only)


def test_house_wording_from_each_items_old_snapshot():
    for s in SETS:
        for x in _items(s):
            d = V.terms_date(x); assert d == x["snap_old"].replace("-", "")[:8] < x["snap_new"].replace("-", "")[:8]
            for p in V.paths(d): assert json.load(open(p, encoding="utf-8"))["meta"]["date"] == d
    for d in ("20250601", "20250701"):
        m = json.load(open(V.paths(d)[0], encoding="utf-8"))["meta"]
        assert "XML capture" in m["source"] and m["r21_rejected"]
        rej = {(r["lang"], r["term"]) for r in m["r21_rejected"]}
        T, _ = V.resources(d); assert not rej & set(T)              # rejected renderings never reach a block


def test_committed_prompts_reproduce():
    r = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "r21_system.py"), "--check"], capture_output=True, text=True,
                       env=dict(os.environ, PYTHONPATH=os.path.join(ROOT, "src")))
    assert r.returncode == 0, r.stdout + r.stderr


def test_recorder_and_replay_roundtrip():
    """every exchange the live run records is replayed by its key; the replayed run equals the live one."""
    x = _called("20260901-20261001")[:3]
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "exchanges.jsonl"); live = V.Recorder(backends.Stub(), p)
        R1 = [V.SystemPipeline(live).run(y) for y in x]
        rec = V.Recorded(p); R2 = [V.SystemPipeline(rec).run(y) for y in x]
        assert rec.hits and not rec.misses and [r["out"] for r in R1] == [r["out"] for r in R2]
        for l in open(p, encoding="utf-8"):
            e = json.loads(l); assert e["request"]["messages"][0] == {"role": "system", "content": V.SYSTEM}
            assert e["key"] == backends.payload_key(e["request"]["model"], e["request"]["messages"][1]["content"], e["request"]["max_tokens"], 0.0, system=V.SYSTEM)


def test_cli_variant():
    P = cli._pipeline(cli._capture, "v4-system", None)
    assert isinstance(P, V.SystemPipeline) and isinstance(P.ns["ask"], V.SystemAsk)
    try: cli._pipeline(cli._capture, "v4-system", "19990101"); raise AssertionError("missing snapshot accepted")
    except cli.UsageError: pass


if __name__ == "__main__":
    for n, f in sorted(globals().items()):
        if n.startswith("test_") and callable(f): f(); print("ok", n)
