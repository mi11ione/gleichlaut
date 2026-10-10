"""PREREG R8 runners: the failure-mode tests on the shipped Apertus 8B GGUF (Q8_0), on CPU runners (fm workflow).

  python -m gleichlaut.fm.run run --test T --gguf PATH --shard K --of N [--out DIR] [--limit M] [--budget S]
  python -m gleichlaut.fm.run gather --in DIR [DIR ...]       merge the shards into data/runs/8b_q8_0_fm_*

Tests (prompts and loops are the research source itself; only the model call and token counting are injected):
  free    T1 free translation of the new German, dev 120: frozen/s2/s2.py PF + run_3, no logit mask (s2.py:150)
  window  T2 window-only edit, dev 120: frozen/s2/s2.py PW + run_2, digit / number-word mask on (s2.py:134)
  s2b     T5 whole-paragraph rewrite + lock check + one greedy retry, dev 120: frozen/s2/s2b.py PA/RETRY + run, mask on
  judge   T3 yes/no equivalence on the 9 + 36 Fedlex items: round7b/spike7b.py PAIR["de"], both orders, three pairs;
          generation (<= 8 tokens, as rescue70b/fx/fx.py:27) and the Ja/Nein log-probabilities at the first answer position
          of the same call (spike7b.py:100), no mask
  typing  T4 operator typing, Dreiklang 885 prompts: dreiklang/scripts/s1.py INSTR/TAIL/PREFIX/OPTIONS, 41 options as summed
          token log-probabilities after "Antwort:" through a token trie on a shared prefix (s1.py:67-117), no mask

Each shard appends one JSON line per item as it finishes (resumable: done items are skipped). --budget stops cleanly
before a runner's time limit so the partial shard is uploaded and a re-run resumes it. Never run this on a team machine."""
import argparse, hashlib, json, math, os, random, re, sys, time
from .. import core, score, backends
from ..core import gl2, lock, _extract, FROZEN
from . import RES

S2, S2B = os.path.join(FROZEN, "s2", "s2.py"), os.path.join(FROZEN, "s2", "s2b.py")
SPIKE7B = os.path.join(RES, "round7b", "spike7b.py")
FX = os.path.join(RES, "rescue70b", "fx", "fx.py")
S1 = os.path.join(RES, "dreiklang", "scripts", "s1.py")
FED45 = os.path.join(RES, "round7", "fedlex_items.json")
DK = os.path.join(RES, "dreiklang", "s1_items.json")
TESTS = ("free", "window", "s2b", "judge", "typing")
FILE = {"free": "arm3.jsonl", "window": "arm2.jsonl", "s2b": "arm2b.jsonl", "judge": "judge.jsonl", "typing": "s1_scores.jsonl"}
KEY = {"free": "key", "window": "key", "s2b": "key", "judge": "uid", "typing": "pkey"}
RUNS = {"free": "runs/8b_q8_0_fm_free_dev120.jsonl", "window": "runs/8b_q8_0_fm_window_dev120.jsonl",
        "s2b": "runs/8b_q8_0_fm_s2b_dev120.jsonl", "judge": "runs/8b_q8_0_fm_judge_fedlex45.jsonl",
        "typing": "runs/8b_q8_0_fm_typing_dk885.jsonl"}
TYPING_META = "runs/8b_q8_0_fm_typing_meta.json"


class Budget(Exception):
    """the shard's time budget is spent: stop cleanly, the next run resumes."""


def load(p):
    with open(p, encoding="utf-8") as f: return json.load(f)


def items_for(test):
    if test in ("free", "window", "s2b"): return score.load_items("items/items_dev.json")
    if test == "judge": return [dict(x, uid=f"{x['id']}|{x['eid']}") for x in load(FED45)]
    return load(DK)


def log_softmax(np, x):
    x = np.asarray(x, dtype=np.float64); m = float(x.max())
    return x - (m + math.log(float(np.exp(x - m).sum())))


class Model:
    """Apertus 8B GGUF in process with the shipped backend's settings (backends.LlamaCpp: the GGUF's chat template through
    create_chat_completion, greedy, temperature 0, the same digit / number-word mask). chat(lang=None) runs without the
    mask; chat(first=True) also returns the log-softmax at the first answer position. chat_text/toks/eval_from serve
    the forced-choice test (T4), with the prompt rendered and tokenised exactly as create_chat_completion does."""

    def __init__(self, gguf, n_ctx=8192, log=None, deadline=None):
        self.b = backends.LlamaCpp(gguf, backends.lang_of_prompt, n_ctx=n_ctx)
        self.llm, self.np = self.b.llm, self.b.np
        from llama_cpp import LogitsProcessorList
        from llama_cpp.llama_chat_format import Jinja2ChatFormatter
        self.LP, self.log, self.deadline = LogitsProcessorList, log, deadline
        self.none = self.np.array([], dtype=self.np.int64)
        L = self.llm
        eos, bos = L.token_eos(), L.token_bos()
        self.template = L.metadata.get("tokenizer.chat_template", "")
        self.fmt = Jinja2ChatFormatter(template=self.template, eos_token=L._model.token_get_text(eos) if eos != -1 else "",
                                       bos_token=L._model.token_get_text(bos) if bos != -1 else "", stop_token_ids=[eos])
        self.n_vocab = L.n_vocab()

    def _check_time(self):
        if self.deadline and time.time() > self.deadline: raise Budget()

    def chat(self, prompt, max_tokens, lang=None, first=False, tag=""):
        self._check_time()
        np, bad, cap = self.np, (self.b.bad[lang] if lang else self.none), []

        def proc(ids, logits):
            if first and not cap: cap.append(np.array(logits, dtype=np.float64))
            if len(bad): logits[bad] = -np.inf
            return logits
        t0 = time.time()
        r = self.llm.create_chat_completion(messages=[{"role": "user", "content": prompt}], max_tokens=max_tokens, temperature=0.0,
                                            logits_processor=self.LP([proc]))
        text = r["choices"][0]["message"]["content"]; u = r.get("usage", {})
        meta = dict(secs=round(time.time() - t0, 2), prompt_tokens=u.get("prompt_tokens"), completion_tokens=u.get("completion_tokens"),
                    masked=bool(lang), finish=r["choices"][0].get("finish_reason"))
        if self.log:
            with open(self.log, "a", encoding="utf-8") as f:
                f.write(json.dumps(dict(meta, tag=tag, max_tokens=max_tokens, mask_lang=lang,
                                        prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(), raw=text), ensure_ascii=False) + "\n")
        if first: meta["first"] = log_softmax(np, cap[0]) if cap else None
        return backends.strip_think(text), meta

    def ntok(self, s):
        """the research runners' tok.encode(s) count (MLX/HF tokenizer, special tokens added): here the GGUF tokenizer."""
        return len(self.llm.tokenize(s.encode("utf-8"), add_bos=True, special=False))

    def chat_text(self, user):
        return self.fmt(messages=[{"role": "user", "content": user}]).prompt

    def toks(self, text):
        return self.llm.tokenize(text.encode("utf-8"), add_bos=False, special=True)

    def eval_from(self, keep, tokens):
        """keep the first `keep` positions of the KV cache, evaluate `tokens` after them -> log-softmax at the last one."""
        self.llm.n_tokens = keep
        self.llm.eval(list(tokens))
        x = self.np.ctypeslib.as_array(self.llm._ctx.get_logits_ith(-1), shape=(self.n_vocab,))
        return log_softmax(self.np, x)


class _Tok:
    def __init__(self, m): self.m = m
    def encode(self, s): return [0] * self.m.ntok(s)


def _ns(model, out, items, tag):
    def _print(*a, **k): print(*a, flush=True)
    return {"json": json, "os": os, "time": time, "re": re, "gl2": gl2, "lock": lock, "items": items, "OUT": out,
            "tok": _Tok(model), "print": _print, "__tag__": tag}


# ---------------------------------------------------------------- T1, T2: frozen/s2/s2.py run_3 / run_2
def run_s2(model, out, items, test):
    ns = _ns(model, out, items, test)
    _extract(S2, ("LNAME", "clean_first", "clean_window", "clean_full", "PW", "PF", "done_ids", "run_2", "run_3"), ns)

    def gen(prompt, max_tokens, lang=None):        # s2.py:58-66: MLX generate -> llama.cpp; the mask iff a language is given
        text, meta = model.chat(prompt, max_tokens, lang=lang, tag=test)
        return text, meta["secs"]
    ns["gen"] = gen
    (ns["run_3"] if test == "free" else ns["run_2"])()


# ---------------------------------------------------------------- T5: frozen/s2/s2b.py run
def run_s2b(model, out, items):
    ns = _ns(model, out, items, "s2b")
    _extract(S2B, ("LNAME", "clean", "PA", "RETRY", "chk", "done_ids", "run"), ns)

    def gen(prompt, n_tgt_tokens, lang):           # s2b.py:55-60 (max tokens as s2b.py:56), mask on
        mt = int(n_tgt_tokens * 2.2) + 60
        text, meta = model.chat(prompt, mt, lang=lang, tag="s2b")
        return text, meta["secs"]
    ns["gen"] = gen
    ns["run"]()


# ---------------------------------------------------------------- T3: round7b PAIR["de"], generation + first-token log-probs
def judge_prompts():
    ns = {}; _extract(SPIKE7B, ("PAIR", "PAIRS"), ns)
    fx = {"re": re}; _extract(FX, ("Q", "PAIRS", "parse"), fx)
    P = ns["PAIR"]["de"]
    assert P["q"] == fx["Q"] and ns["PAIRS"] == fx["PAIRS"], "spike7b PAIR['de'] and fx.py Q differ"
    return P, ns["PAIRS"], fx["parse"]


def run_judge(model, out, items):
    P, PAIRS, parse = judge_prompts()
    np = model.np
    ids = {w: model.llm.tokenize(w.encode(), add_bos=False, special=False) for w in (P["yes"], P["no"])}
    path = os.path.join(out, FILE["judge"])
    done = {json.loads(l)["uid"] for l in open(path, encoding="utf-8")} if os.path.exists(path) else set()
    for x in items:
        if x["uid"] in done: continue
        r = dict(uid=x["uid"], id=x["id"], kind=x["kind"], oc=x["oc"], eid=x["eid"], gold=x["gold"], pairs={}, token_ids=ids)
        for a, b in PAIRS:                                                     # spike7b.py:109-110
            la, ta, lb, tb = a.upper(), x[a], b.upper(), x[b]; res = {}
            for oname, (l1, t1, l2, t2, o1, o2) in (("ab", (la, ta, lb, tb, P["yes"], P["no"])),    # spike7b.py:97-98
                                                     ("ba", (lb, tb, la, ta, P["no"], P["yes"]))):
                prompt = P["q"].format(la=l1, lb=l2, ta=t1, tb=t2, o1=o1, o2=o2)
                text, meta = model.chat(prompt, 8, lang=None, first=True, tag="judge")             # fx.py:27: 8 tokens
                lp = meta["first"]
                if len(ids[P["yes"]]) == 1 and len(ids[P["no"]]) == 1:
                    ly, ln = float(lp[ids[P["yes"]][0]]), float(lp[ids[P["no"]][0]])
                else:                                  # multi-token answer word: summed log-probs by forced choice
                    pre = model.toks(model.chat_text(prompt)); ly, ln = (forced(model, pre, ids[w]) for w in (P["yes"], P["no"]))
                m = max(ly, ln); py, pn = math.exp(ly - m), math.exp(ln - m)
                res[oname] = dict(lp_yes=ly, lp_no=ln, p_diff=pn / (py + pn), mass=math.exp(ly) + math.exp(ln),
                                  ntok=meta["prompt_tokens"], raw=text, ans=parse(text), secs=meta["secs"])
            res["p_diff"] = (res["ab"]["p_diff"] + res["ba"]["p_diff"]) / 2
            r["pairs"][f"{a}-{b}"] = res
        with open(path, "a", encoding="utf-8") as f: f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print("judge", x["kind"][0], x["oc"], x["gold"], {k: v["ab"]["ans"] + "/" + v["ba"]["ans"] if v["ab"]["ans"] and v["ba"]["ans"] else "?"
                                                         for k, v in r["pairs"].items()}, flush=True)


def forced(model, pre, seq):
    lp = model.eval_from(0, pre); s = 0.0
    for j, t in enumerate(seq):
        s += float(lp[t])
        if j + 1 < len(seq): lp = model.eval_from(len(pre) + j, [t])
    return s


# ---------------------------------------------------------------- T4: dreiklang/scripts/s1.py with llama.cpp
def typing_defs():
    ns = {}; _extract(S1, ("SUBJ", "OPS", "NONE", "OPTIONS", "INSTR", "TAIL", "PREFIX"), ns)
    return ns


def run_typing(model, out, items, all_items, gguf_sha=None):
    D = typing_defs(); OPTIONS, INSTR, TAIL, PREFIX = D["OPTIONS"], D["INSTR"], D["TAIL"], D["PREFIX"]
    enc = model.toks

    def prompt_text(x):                                 # s1.py:67-68
        return model.chat_text(INSTR + x["ctx"] + TAIL.replace("{surface}", x["surface"])) + PREFIX

    def option_ids(ptxt, pre):                          # s1.py:71-77
        seqs = []
        for o in OPTIONS:
            full = enc(ptxt + o)
            assert full[:len(pre)] == pre, ("boundary", o)
            seqs.append(full[len(pre):])
        return seqs

    a, b = enc(prompt_text(all_items[0])), enc(prompt_text(all_items[-1]))   # s1.py:80-84: shared static prefix
    lcp = 0
    while lcp < min(len(a), len(b)) and a[lcp] == b[lcp]: lcp += 1
    static = a[:max(1, lcp - 2)]

    def score_trie(first, seqs, base):                  # s1.py:89-106: one single-token forward per internal trie node
        out_, calls = [0.0] * len(seqs), [0]

        def rec(lp, depth, idxs):
            groups = {}
            for i in idxs: groups.setdefault(seqs[i][depth], []).append(i)
            for tid, mem in groups.items():
                s = float(lp[tid])
                for i in mem: out_[i] += s
                cont = [i for i in mem if len(seqs[i]) > depth + 1]
                if cont:
                    nlp = model.eval_from(base + depth, [tid]); calls[0] += 1
                    rec(nlp, depth + 1, cont)
        rec(first, 0, list(range(len(seqs))))
        return out_, calls[0]

    def score_item(x):                                  # s1.py:108-117
        ptxt = prompt_text(x); pre = enc(ptxt); seqs = option_ids(ptxt, pre)
        if pre[:len(static)] != static: raise RuntimeError("static prefix mismatch")
        first = model.eval_from(len(static), pre[len(static):])
        sc, calls = score_trie(first, seqs, len(pre))
        return sc, len(pre), calls, seqs

    def naive(x, which):                                # s1.py:119-126: a fresh full prefill per option, no shared prefix
        ptxt = prompt_text(x); pre = enc(ptxt); seqs = option_ids(ptxt, pre); res = []
        for i in which: res.append(forced(model, pre, seqs[i]))
        return res

    model.llm.reset(); model.eval_from(0, static)
    x0 = all_items[0]
    sc0, _, _, seqs0 = score_item(x0)
    which = [0, 7, 22, 33, len(OPTIONS) - 1]
    ref = naive(x0, which)
    diff = max(abs(sc0[i] - r) for i, r in zip(which, ref))
    model.llm.reset(); model.eval_from(0, static)
    meta = dict(model="gguf:q8_0", gguf_sha256=gguf_sha, runtime=backends.llama_version(), chat_format=model.llm.chat_format,
                options=OPTIONS, instr=INSTR, tail=TAIL, prefix=PREFIX, static_tokens=len(static), selfcheck_maxdiff=diff,
                option_ids=seqs0, instr_sha256=hashlib.sha256((INSTR + TAIL + PREFIX).encode()).hexdigest(),
                template_sha256=hashlib.sha256(model.chat_text("X").encode()).hexdigest(), template_tail=model.chat_text("X")[-120:],
                gguf_template_sha256=hashlib.sha256(model.template.encode()).hexdigest())
    json.dump(meta, open(os.path.join(out, "s1_meta.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("typing: static prefix", len(static), "tokens; self-check max|diff|", round(diff, 4), "; template tail", repr(meta["template_tail"]), flush=True)
    path = os.path.join(out, FILE["typing"])
    done = {json.loads(l)["pkey"] for l in open(path, encoding="utf-8")} if os.path.exists(path) else set()
    t0, n = time.time(), 0
    for x in items:
        if x["pkey"] in done: continue
        model._check_time()
        t1 = time.time(); sc, ntok, calls, _ = score_item(x); n += 1
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(dict(pkey=x["pkey"], lp=dict(zip(OPTIONS, sc)), ntok=ntok, calls=calls, secs=round(time.time() - t1, 3)),
                               ensure_ascii=False) + "\n")
        if n % 10 == 0: print(f"typing {n} scored, {(time.time() - t0) / n:.1f} s/prompt", flush=True)


# ---------------------------------------------------------------- CLI
def run(a):
    assert a.test in TESTS, a.test
    out = os.path.join(a.out, f"{a.test}_shard{a.shard}of{a.of}"); os.makedirs(out, exist_ok=True)
    allx = items_for(a.test)
    mine = [x for i, x in enumerate(allx) if i % a.of == a.shard]
    if a.limit: mine = mine[:a.limit]
    deadline = time.time() + a.budget if a.budget else None
    model = Model(a.gguf, n_ctx=a.ctx, log=os.path.join(out, "calls.jsonl"), deadline=deadline)
    print(f"R8 {a.test}: shard {a.shard}/{a.of}, {len(mine)} items, runtime llama-cpp-python {backends.llama_version()}, "
          f"chat format {model.llm.chat_format}", flush=True)
    try:
        if a.test in ("free", "window"): run_s2(model, out, mine, a.test)
        elif a.test == "s2b": run_s2b(model, out, mine)
        elif a.test == "judge": run_judge(model, out, mine)
        else: run_typing(model, out, mine, allx, a.gguf_sha256)
    except Budget:
        print("BUDGET_SPENT: stopping cleanly; re-run with resume_run to continue", flush=True)
        return 0
    print("SHARD_DONE", a.test, a.shard, flush=True)
    return 0


def gather(a):
    recs = {t: {} for t in TESTS}; meta = None
    for d in a.inp:
        for root, _, files in os.walk(d):
            t = next((t for t in TESTS if os.path.basename(root).startswith(t + "_shard")), None)
            if not t: continue
            for f in files:
                if f == FILE[t]:
                    for l in open(os.path.join(root, f), encoding="utf-8"):
                        r = json.loads(l); recs[t][r[KEY[t]]] = r
                if f == "s1_meta.json" and t == "typing" and (meta is None or "shard0of" in root):
                    meta = load(os.path.join(root, f))
    for t in TESTS:
        if not recs[t]: print(t, "no shards found"); continue
        I = items_for(t); missing = [x[KEY[t]] for x in I if x[KEY[t]] not in recs[t]]
        if missing and not a.partial: raise SystemExit(f"{t}: {len(missing)} items missing, e.g. {missing[:5]}")
        with open(os.path.join(score.DATA, RUNS[t]), "w", encoding="utf-8") as f:
            for x in I:
                if x[KEY[t]] in recs[t]: f.write(json.dumps(recs[t][x[KEY[t]]], ensure_ascii=False) + "\n")
        print(f"{t}: {len(recs[t])} of {len(I)} items -> data/{RUNS[t]}")
    if meta is not None:
        json.dump(meta, open(os.path.join(score.DATA, TYPING_META), "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="gleichlaut.fm.run"); sp = ap.add_subparsers(dest="cmd", required=True)
    r = sp.add_parser("run"); r.add_argument("--test", required=True, choices=TESTS); r.add_argument("--gguf", required=True)
    r.add_argument("--gguf-sha256", default=None); r.add_argument("--shard", type=int, default=0); r.add_argument("--of", type=int, default=1)
    r.add_argument("--out", default="out/fm"); r.add_argument("--ctx", type=int, default=8192)
    r.add_argument("--limit", type=int, default=0, help="smoke run: at most this many items per shard")
    r.add_argument("--budget", type=float, default=0, help="seconds; stop cleanly after this (0 = no limit)")
    g = sp.add_parser("gather"); g.add_argument("--in", dest="inp", nargs="+", required=True); g.add_argument("--partial", action="store_true")
    a = ap.parse_args(argv)
    return run(a) if a.cmd == "run" else gather(a)


if __name__ == "__main__":
    sys.exit(main())
