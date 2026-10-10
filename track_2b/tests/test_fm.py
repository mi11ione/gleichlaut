"""PREREG R8 (gleichlaut.fm): the vendored research files are intact, the scorers reproduce every recorded MLX / 70B number
of the failure-mode table from the recorded outputs, and the runners execute the frozen loops with an injected model."""
import json, os, re, shutil, tempfile, unittest
from gleichlaut import fm
from gleichlaut.fm import measure as M, run as R


def test_vendored_research_hashes():
    assert fm.verify(strict=False) == []


def test_mlx_and_70b_numbers_reproduce():
    w = M.window()
    assert (w["mlx"]["disobeyed"], w["mlx"]["windows"]) == (165, 226) and w["70b"]["disobeyed"] == 183
    f = M.free()["mlx"]
    assert (f["exact"], f["ef1"], f["chrf"], f["lexicon_flips"]) == (0.0, 28.2, 71.2, 78)
    j = M.judge()
    m = j["mlx_logprob"]
    assert (m["hits_at_half"], m["false_flags"], m["auroc_item"], m["argmax_hits"]) == (0, 0, 0.812, 6)
    assert (m["auroc_item_ab"], m["auroc_item_ba"]) == (0.616, 0.821)
    g = j["70b_generation"]
    assert (g["hits"], g["false_flags"], g["nein_answers"], g["calls"]) == (0, 0, 2, 270)
    t = M.typing()["mlx"]
    assert (t["operator_correct"], t["gold_conditions"], t["operator_acc_pct"]) == (296, 831, 35.6)
    assert (t["held_wrong_all_three"], t["held_triples"], t["held_identical_wrong"], t["tau"]) == (53, 77, 24, 9.009)
    r = M.retry()
    assert (r["mlx"]["retried"], r["mlx"]["retry_fixed"], r["mlx"]["flag_rate"], r["mlx"]["ready_real"]) == (26, 0, 85.0, 1)


def test_runners_with_an_injected_model():
    try: import numpy as np
    except ImportError: raise unittest.SkipTest("numpy not installed (it comes with the offline requirements)")
    V = 64

    class LLM:
        chat_format = "chat_template.default"
        def __init__(self): self.n_tokens, self.kv = 0, []
        def tokenize(self, b, add_bos=True, special=False): return ([1] if add_bos else []) + [3 + ord(c) % (V - 3) for c in b.decode()]
        def reset(self): self.n_tokens = 0
        def eval(self, t): self.kv = self.kv[:self.n_tokens] + list(t); self.n_tokens += len(t)

    class Fake(R.Model):
        def __init__(self, gguf, n_ctx=8192, log=None, deadline=None):
            self.np, self.llm, self.log, self.deadline, self.template, self.n_vocab = np, LLM(), log, deadline, "T", V
            self.none = np.array([], dtype=np.int64)
        def chat(self, prompt, max_tokens, lang=None, first=False, tag=""):
            m = re.search(r"\n(?:French|Italian) \(old\): (.*?)\n\nOutput only", prompt, re.S)
            text = "Ja" if "Antworte nur mit" in prompt else m.group(1) if m else prompt[-80:]
            meta = dict(secs=0.0, prompt_tokens=len(prompt))
            if first: meta["first"] = R.log_softmax(np, np.arange(V, dtype=float))
            return text, meta
        def chat_text(self, user): return "<u>" + user + "<a>"
        def toks(self, text): return self.llm.tokenize(text.encode(), add_bos=False)
        def eval_from(self, keep, tokens):
            self.llm.n_tokens = keep; self.llm.eval(tokens)
            return R.log_softmax(np, np.cos(np.arange(V) * (1 + sum(self.llm.kv) % 7)))

    real, R.Model = R.Model, Fake
    d = tempfile.mkdtemp()
    try:
        for t in R.TESTS:
            R.main(["run", "--test", t, "--gguf", "x", "--shard", "1", "--of", "60" if t != "judge" else "30", "--out", d, "--limit", "1"])
            p = os.path.join(d, f"{t}_shard1of{'60' if t != 'judge' else '30'}", R.FILE[t])
            assert sum(1 for _ in open(p, encoding="utf-8")) == 1, t
        rec = json.loads(open(os.path.join(d, "judge_shard1of30", "judge.jsonl"), encoding="utf-8").read())
        assert set(rec["pairs"]) == {"de-fr", "de-it", "fr-it"} and rec["pairs"]["de-fr"]["ab"]["ans"] == "ja"
    finally:
        R.Model = real; shutil.rmtree(d, ignore_errors=True)
