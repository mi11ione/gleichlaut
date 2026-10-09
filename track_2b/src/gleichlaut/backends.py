"""Model backends. Each returns ask(prompt, tag, cap, max_tokens) -> (text, meta), the signature the frozen code calls.

cache     hash-addressed replay of recorded responses (data/cache/responses/<sha256>.json). The key is the sha256 of the
          exact request payload {model, messages, max_tokens, temperature}, the same key the development gateway used,
          so a replay hit proves that the prompt was rebuilt byte-for-byte. A miss is an error, never a silent call.
openai    any OpenAI-compatible endpoint: LLM_BASE_URL, LLM_API_KEY, LLM_NAME (the judges' / a user-controlled endpoint).
          Plain user message only (no system message, no prefill), 429 back-off, and the response `model` field is
          checked against the requested model on every call.
gateway   development only (Public AI through the team's budget gateway, gw.chat); never used by `make run`.
llamacpp  in-process llama-cpp-python on CPU with a GGUF build of Apertus 8B and the digit / number-word logit mask.
Every live call can append a JSON line to a call log (model requested, model served, seed, tokens, seconds)."""
import hashlib, json, os, re, threading, time, unicodedata, urllib.error, urllib.request

_LOCK = threading.Lock()


def payload_key(model, prompt, max_tokens, temperature=0.0, **extra):
    payload = dict(model=model, messages=[{"role": "user", "content": prompt}], max_tokens=max_tokens,
                   temperature=temperature, **extra)
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def strip_think(text):
    return text.split("</think>", 1)[1] if "</think>" in text else text      # frozen/common.py ask()


def _log(path, rec):
    if not path: return
    with _LOCK, open(path, "a", encoding="utf-8") as f: f.write(json.dumps(rec, ensure_ascii=False) + "\n")


class Cache:
    """Replay recorded responses. model = the model name the recording was made with."""

    def __init__(self, root, model="swiss-ai/apertus-v1.5-70b", extra=None):
        self.root, self.model, self.extra = root, model, extra or {}
        self.hits, self.misses = 0, []

    def __call__(self, prompt, tag, cap, max_tokens):
        h = payload_key(self.model, prompt, max_tokens, 0.0, **self.extra)
        p = os.path.join(self.root, h[:2], h + ".json")
        if not os.path.exists(p):
            self.misses.append(h)
            raise KeyError(f"cache miss {h[:16]} (prompt not recorded; the pipeline or its inputs changed)")
        d = json.load(open(p, encoding="utf-8"))
        self.hits += 1
        return strip_think(d["text"]), dict(d.get("meta", {}), cached=True, key=h)


def write_cache(root, key, text, meta):
    p = os.path.join(root, key[:2], key + ".json")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    keep = {k: meta[k] for k in ("prompt_tokens", "completion_tokens", "usd", "secs", "model_served", "seed") if k in meta}
    with open(p, "w", encoding="utf-8") as f: json.dump(dict(text=text, meta=keep), f, ensure_ascii=False, sort_keys=True)


class OpenAI:
    """OpenAI-compatible chat endpoint (LLM_BASE_URL). Records every response into `record_to` (a cache root) if given."""

    def __init__(self, base_url=None, api_key=None, model=None, seed=None, log=None, record_to=None, timeout=300):
        self.base = (base_url or os.environ["LLM_BASE_URL"]).rstrip("/")
        self.key = api_key if api_key is not None else os.environ.get("LLM_API_KEY", "")
        self.model = model or os.environ.get("LLM_NAME") or "swiss-ai/apertus-v1.5-70b"
        self.seed, self.log, self.record_to, self.timeout = seed, log, record_to, timeout

    def __call__(self, prompt, tag, cap, max_tokens):
        extra = {} if self.seed is None else {"seed": self.seed}
        body = dict(model=self.model, messages=[{"role": "user", "content": prompt}], max_tokens=max_tokens, temperature=0.0, **extra)
        url = self.base + ("/chat/completions" if not self.base.endswith("/chat/completions") else "")
        hdr = {"Content-Type": "application/json", "User-Agent": "gleichlaut/0.1"}
        if self.key: hdr["Authorization"] = f"Bearer {self.key}"
        t0 = time.time()
        for k in range(8):
            try:
                req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=hdr, method="POST")
                with urllib.request.urlopen(req, timeout=self.timeout) as r: d = json.loads(r.read())
                break
            except urllib.error.HTTPError as e:
                if e.code not in (429, 502, 503, 504) or k == 7: raise
                time.sleep(min(120, 10 * (k + 1)))
        served = d.get("model", "")
        if served and served.split("/")[-1].lower() != self.model.split("/")[-1].lower() and "apertus" not in served.lower():
            # the measured hazard: a provider silently answering an Apertus request from another model
            raise RuntimeError(f"endpoint served {served!r} for {self.model!r}: not an Apertus model, refusing the output")
        text = d["choices"][0]["message"]["content"]
        u = d.get("usage", {})
        meta = dict(prompt_tokens=u.get("prompt_tokens"), completion_tokens=u.get("completion_tokens"),
                    secs=round(time.time() - t0, 2), model_served=served, seed=self.seed, cached=False)
        key = payload_key(self.model, prompt, max_tokens, 0.0, **extra)
        if self.record_to: write_cache(self.record_to, key, text, meta)
        _log(self.log, dict(meta, key=key, tag=tag, model=self.model))
        return strip_think(text), dict(meta, key=key)


class Gateway:
    """Development only: Public AI through the team's budget gateway (caps, cache, ledger). Not shipped in any runtime path."""

    def __init__(self, gw_dir, tag, cap, model="swiss-ai/apertus-v1.5-70b", seed=None, log=None, record_to=None):
        import sys
        sys.path.insert(0, gw_dir)
        from gw import chat                  # noqa: E402  (reads its key itself; never printed)
        self.chat, self.tag, self.cap, self.model = chat, tag, cap, model
        self.seed, self.log, self.record_to = seed, log, record_to

    def __call__(self, prompt, tag, cap, max_tokens):
        extra = {} if self.seed is None else {"seed": self.seed}
        for k in range(8):
            try:
                choice, meta = self.chat([{"role": "user", "content": prompt}], model=self.model, max_tokens=max_tokens,
                                         temperature=0.0, tag=self.tag, tag_cap_usd=self.cap, full=True, **extra)
                break
            except urllib.error.HTTPError as e:
                if e.code != 429 or k == 7: raise
                time.sleep(20 * (k + 1))
        served = (meta.get("resp") or {}).get("model", "")
        if not meta.get("cached") and served.split("/")[-1].lower() != self.model.split("/")[-1].lower():
            raise RuntimeError(f"gateway served {served!r} for {self.model!r}: refusing the output")
        text = choice["message"]["content"]
        key = payload_key(self.model, prompt, max_tokens, 0.0, **extra)
        meta = dict(prompt_tokens=meta.get("prompt_tokens"), completion_tokens=meta.get("completion_tokens"), usd=meta.get("usd"),
                    secs=meta.get("secs"), model_served=served, seed=self.seed, cached=meta.get("cached", False))
        if self.record_to: write_cache(self.record_to, key, text, meta)
        _log(self.log, dict(meta, key=key, tag=self.tag, model=self.model))
        return strip_think(text), dict(meta, key=key)


class LlamaCpp:
    """Apertus 8B GGUF on CPU (llama-cpp-python), greedy, with the 8B digit ban of the research runs: every token that
    decodes to a digit, and every word-initial FR/IT number word 2-12 (gl2.BANWORDS), gets logit -inf."""

    def __init__(self, gguf_path, lang_of_prompt, n_ctx=8192, n_threads=None, log=None):
        from llama_cpp import Llama, LogitsProcessorList   # noqa: E402  (runtime dependency of the offline image only)
        import numpy as np
        from .core import gl2
        self.llm = Llama(model_path=gguf_path, n_ctx=n_ctx, n_threads=n_threads or os.cpu_count(), logits_all=False, verbose=False)
        self.LP, self.np, self.lang_of_prompt, self.log = LogitsProcessorList, np, lang_of_prompt, log
        self.model = "gguf:" + os.path.basename(gguf_path)
        n = self.llm.n_vocab(); bad = {"fr": [], "it": []}
        for i in range(n):
            s = self.llm.detokenize([i]).decode("utf-8", "ignore")
            if any(unicodedata.category(c) == "Nd" for c in s):
                bad["fr"].append(i); bad["it"].append(i); continue
            w = s.strip().lower()
            for L in ("fr", "it"):
                if s[:1].isspace() and w in gl2.BANWORDS[L]: bad[L].append(i)
        self.bad = {L: np.array(v, dtype=np.int64) for L, v in bad.items()}

    def __call__(self, prompt, tag, cap, max_tokens):
        lang = self.lang_of_prompt(prompt)
        bad, np = self.bad[lang], self.np
        def mask(ids, logits):
            logits[bad] = -np.inf
            return logits
        t0 = time.time()
        r = self.llm.create_chat_completion(messages=[{"role": "user", "content": prompt}], max_tokens=max_tokens, temperature=0.0,
                                            logits_processor=self.LP([mask]))
        text = r["choices"][0]["message"]["content"]
        meta = dict(secs=round(time.time() - t0, 2), model_served=self.model, completion_tokens=r.get("usage", {}).get("completion_tokens"),
                    prompt_tokens=r.get("usage", {}).get("prompt_tokens"), cached=False)
        _log(self.log, dict(meta, tag=tag))
        return strip_think(text), meta


def lang_of_prompt(prompt):
    """target language of an SL or Fedlex drafting prompt (both name it in English before any target text)."""
    m = re.search(r"\b(French|Italian)\b", prompt)
    return {"French": "fr", "Italian": "it"}[m.group(1)] if m else "fr"
