"""Model backends. Each returns ask(prompt, tag, cap, max_tokens) -> (text, meta), the signature the frozen code calls.

cache     hash-addressed replay of recorded responses (data/cache/responses/<sha256>.json). The key is the sha256 of the
          exact request payload {model, messages, max_tokens, temperature}, the same key the development gateway used,
          so a replay hit proves that the prompt was rebuilt byte-for-byte. A miss is an error, never a silent call.
openai    any OpenAI-compatible endpoint: LLM_BASE_URL, LLM_API_KEY, LLM_NAME (the judges' / a user-controlled endpoint).
          Plain user message only (no system message of ours, no prefill; the server's chat template may add its own default turns), 429 back-off, and the response `model` field is
          checked against the requested model on every call.
gateway   development only (Public AI through the team's budget gateway, gw.chat); never used by `make run`.
llamacpp  in-process llama-cpp-python on CPU with a GGUF build of Apertus 8B and the digit / number-word logit mask (the SL
          default lane when the GGUF has a build certificate, certify.build_lookup). Without llama-cpp-python installed
          it raises ConfigError with the fix (the offline image), never an ImportError traceback.
stub      wiring tests only: returns the old target text of the prompt unchanged (no model, no network). Its drafts
          are never a translation; every stub record is marked for review.
Every live call can append a JSON line to a call log: ts, endpoint (scheme://host/path, never the key), model (requested),
model_served, system_fingerprint, seed, prompt_tokens, completion_tokens, secs, key (payload sha256), tag, cached.

Network: requests honour HTTPS_PROXY / HTTP_PROXY / NO_PROXY (urllib reads them from the environment) and an internal CA:
SSL_CERT_FILE (or REQUESTS_CA_BUNDLE) is added to the default trust store of every HTTPS request (ssl_context()).
Timeouts (openai): GLEICHLAUT_TIMEOUT s per attempt (default 120), GLEICHLAUT_RETRIES attempts (default 4) on 429/5xx/
unreachable with exponential back-off GLEICHLAUT_BACKOFF s (default 5: waits 5, 10, 20 s), and at most GLEICHLAUT_DEADLINE s
for one request over all its attempts (default 300): a dead endpoint fails within about five minutes.
(GLEICHLAUT_HTTP_TIMEOUT / _HTTP_RETRIES / _HTTP_BACKOFF are accepted as older names.)

Errors: every failure of a live endpoint (unreachable, timeout, HTTP error after retries, malformed answer, a non-Apertus
model served) raises EndpointError; missing or invalid configuration raises ConfigError. Callers turn both into a one-line
message and a non-zero exit code (docs/operations.md, exit codes)."""
import datetime, hashlib, http.client, json, os, re, socket, ssl, threading, time, unicodedata, urllib.error, urllib.parse, urllib.request

_LOCK = threading.Lock()
TIMEOUT, RETRIES, BACKOFF, DEADLINE = 120.0, 4, 5.0, 300.0


def _env(*names, default=None):
    for n in names:
        v = os.environ.get(n)
        if v not in (None, ""): return v
    return default


def ca_file():
    """the internal CA bundle to trust in addition to the system store: SSL_CERT_FILE, else REQUESTS_CA_BUNDLE, else None."""
    return _env("SSL_CERT_FILE", "REQUESTS_CA_BUNDLE")


def ssl_context():
    """default HTTPS verification plus the CA file named by SSL_CERT_FILE / REQUESTS_CA_BUNDLE (an internal / proxy CA).
    Verification is never switched off."""
    ctx = ssl.create_default_context()
    f = ca_file()
    if f:
        if not os.path.isfile(f):
            raise ConfigError(f"SSL_CERT_FILE / REQUESTS_CA_BUNDLE points at {f!r}, which is not a readable file")
        try: ctx.load_verify_locations(cafile=f)
        except (ssl.SSLError, OSError, ValueError) as e:
            raise ConfigError(f"cannot load the CA file {f!r} (SSL_CERT_FILE / REQUESTS_CA_BUNDLE): {e}")
    return ctx


def opener(https=True):
    """an opener that reads HTTPS_PROXY / HTTP_PROXY / NO_PROXY now (urllib's global opener keeps the proxies of its first
    use) and verifies HTTPS with ssl_context()."""
    hs = [urllib.request.ProxyHandler()]
    if https: hs.append(urllib.request.HTTPSHandler(context=ssl_context()))
    return urllib.request.build_opener(*hs)


def urlopen(req, timeout):
    """urlopen through opener(): proxies from the environment, internal CA from SSL_CERT_FILE / REQUESTS_CA_BUNDLE."""
    url = req.full_url if isinstance(req, urllib.request.Request) else req
    return opener(url.lower().startswith("https:")).open(req, timeout=timeout)


class EndpointError(RuntimeError):
    """the model endpoint failed (unreachable, HTTP error, malformed answer, wrong model served)."""


class ConfigError(RuntimeError):
    """the backend is not configured (e.g. LLM_BASE_URL unset, gateway dir unset)."""


def endpoint_id(url):
    """canonical endpoint identity: scheme://host[:port]/path, lower-case scheme and host, no credentials, query or fragment,
    no trailing '/' or '/chat/completions'. This (never the key) is what certificates record and match on."""
    u = urllib.parse.urlsplit((url or "").strip())
    host = (u.hostname or "").lower()
    if u.port and not ((u.scheme == "https" and u.port == 443) or (u.scheme == "http" and u.port == 80)): host += f":{u.port}"
    path = re.sub(r"/+$", "", u.path or "")
    if path.endswith("/chat/completions"): path = path[: -len("/chat/completions")]
    return f"{u.scheme.lower()}://{host}{path}"


def _now(): return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


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
        self.endpoint = "recorded responses (data/cache)"

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
    keep = {k: meta[k] for k in ("prompt_tokens", "completion_tokens", "usd", "secs", "model_served", "seed", "backend") if k in meta}
    with open(p, "w", encoding="utf-8") as f: json.dump(dict(text=text, meta=keep), f, ensure_ascii=False, sort_keys=True)


class OpenAI:
    """OpenAI-compatible chat endpoint (LLM_BASE_URL). Records every response into `record_to` (a cache root) if given.
    expect_served: if given, a set of model ids; an answer served by any other model is refused (certified serving set)."""

    def __init__(self, base_url=None, api_key=None, model=None, seed=None, log=None, record_to=None, timeout=None,
                 retries=None, backoff=None, expect_served=None):
        base = base_url or os.environ.get("LLM_BASE_URL", "")
        if not base.strip():
            raise ConfigError("LLM_BASE_URL is not set: point it at an OpenAI-compatible endpoint serving Apertus "
                              "(see .env.example), or choose another backend")
        if urllib.parse.urlsplit(base.strip()).scheme not in ("http", "https") or not urllib.parse.urlsplit(base.strip()).hostname:
            raise ConfigError(f"LLM_BASE_URL is not an http(s) URL: {endpoint_id(base)!r}")
        self.base = base.strip().rstrip("/")
        self.endpoint = endpoint_id(self.base)
        self.key = api_key if api_key is not None else os.environ.get("LLM_API_KEY", "")
        self.model = model or os.environ.get("LLM_NAME") or "swiss-ai/apertus-v1.5-70b"
        self.seed, self.log, self.record_to = seed, log, record_to
        try:
            self.timeout = float(timeout or _env("GLEICHLAUT_TIMEOUT", "GLEICHLAUT_HTTP_TIMEOUT", default=TIMEOUT))
            self.retries = max(1, int(retries or _env("GLEICHLAUT_RETRIES", "GLEICHLAUT_HTTP_RETRIES", default=RETRIES)))
            self.backoff = float(backoff if backoff is not None else _env("GLEICHLAUT_BACKOFF", "GLEICHLAUT_HTTP_BACKOFF", default=BACKOFF))
            self.deadline = float(_env("GLEICHLAUT_DEADLINE", default=DEADLINE))
        except ValueError as e:
            raise ConfigError(f"GLEICHLAUT_TIMEOUT / _RETRIES / _BACKOFF / _DEADLINE must be numbers: {e}")
        self.expect_served = set(expect_served) if expect_served else None
        self.opener = opener(self.base.lower().startswith("https:"))
        self.dead = None                     # set on the first EndpointError: parallel workers stop instead of waiting it out

    def _post(self, url, body, hdr):
        last, t0, n = None, time.monotonic(), 0
        for k in range(self.retries):
            if self.dead: raise EndpointError(self.dead)
            left = self.deadline - (time.monotonic() - t0)
            if left <= 0: break
            n += 1
            try:
                req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=hdr, method="POST")
                with self.opener.open(req, timeout=min(self.timeout, left)) as r: raw = r.read()
                try: return json.loads(raw)
                except ValueError: raise EndpointError(f"{self.endpoint} answered with something that is not JSON: {raw[:120]!r}")
            except urllib.error.HTTPError as e:
                try: detail = e.read()[:200].decode("utf-8", "replace")
                except Exception: detail = ""
                last = f"HTTP {e.code} from {self.endpoint}" + (f": {detail.strip()}" if detail.strip() else "")
                if e.code in (401, 403):
                    self.dead = last + " (check LLM_API_KEY)"; raise EndpointError(self.dead)
                if e.code not in (429, 500, 502, 503, 504): raise EndpointError(last)
            except (urllib.error.URLError, socket.timeout, ConnectionError, OSError, http.client.HTTPException) as e:
                last = f"cannot reach {self.endpoint}: {getattr(e, 'reason', None) or e}"
            if k < self.retries - 1:
                wait = min(60.0, self.backoff * 2 ** k, max(0.0, self.deadline - (time.monotonic() - t0)))
                time.sleep(wait)
        self.dead = (f"{last or 'no answer'} (after {n} attempt{'s' if n > 1 else ''} in {time.monotonic() - t0:.0f} s; "
                     f"GLEICHLAUT_TIMEOUT {self.timeout:g} s, GLEICHLAUT_RETRIES {self.retries}, GLEICHLAUT_DEADLINE {self.deadline:g} s)")
        raise EndpointError(self.dead)

    def __call__(self, prompt, tag, cap, max_tokens):
        extra = {} if self.seed is None else {"seed": self.seed}
        body = dict(model=self.model, messages=[{"role": "user", "content": prompt}], max_tokens=max_tokens, temperature=0.0, **extra)
        url = self.base + ("/chat/completions" if not self.base.endswith("/chat/completions") else "")
        hdr = {"Content-Type": "application/json", "User-Agent": "gleichlaut/0.1"}
        if self.key: hdr["Authorization"] = f"Bearer {self.key}"
        t0 = time.time()
        d = self._post(url, body, hdr)
        try:
            text = d["choices"][0]["message"]["content"]
            if not isinstance(text, str): raise TypeError("content is not a string")
        except (KeyError, IndexError, TypeError) as e:
            raise EndpointError(f"{self.endpoint} returned no chat completion ({type(e).__name__}: {e})")
        served, fp = d.get("model", "") or "", d.get("system_fingerprint")
        if served and served.split("/")[-1].lower() != self.model.split("/")[-1].lower() and "apertus" not in served.lower():
            # never accept an answer that a provider served from a non-Apertus model
            raise EndpointError(f"endpoint served {served!r} for {self.model!r}: not an Apertus model, refusing the output")
        if self.expect_served is not None and served not in self.expect_served:
            raise EndpointError(f"endpoint served {served!r}, which is not among the models seen at certification "
                                f"{sorted(self.expect_served)}: re-certify this endpoint")
        u = d.get("usage") or {}
        meta = dict(prompt_tokens=u.get("prompt_tokens"), completion_tokens=u.get("completion_tokens"),
                    secs=round(time.time() - t0, 2), model_served=served, seed=self.seed, cached=False, backend=fp,
                    system_fingerprint=fp)
        key = payload_key(self.model, prompt, max_tokens, 0.0, **extra)
        if self.record_to: write_cache(self.record_to, key, text, meta)
        _log(self.log, dict(meta, ts=_now(), endpoint=self.endpoint, key=key, tag=tag, model=self.model))
        return strip_think(text), dict(meta, key=key)


class Stub:
    """Wiring tests only: answers every SL drafting prompt with the (slot-coded) old target text it contains, unchanged.
    No model, no network. The pipeline then usually flags 'change not applied'; callers mark every stub record for review."""
    RX = re.compile(r"\n(?:French|Italian) \(old\): (.*?)\n\nOutput only", re.S)

    def __init__(self, log=None):
        self.model, self.endpoint, self.log, self.calls = "stub", "stub://local", log, 0

    def __call__(self, prompt, tag, cap, max_tokens):
        m = self.RX.search(prompt); self.calls += 1
        text = m.group(1) if m else ""
        meta = dict(prompt_tokens=0, completion_tokens=0, secs=0.0, model_served="stub", seed=None, cached=False, backend="stub",
                    system_fingerprint=None)
        _log(self.log, dict(meta, ts=_now(), endpoint=self.endpoint, key=payload_key("stub", prompt, max_tokens), tag=tag, model="stub"))
        return text, meta


class Gateway:
    """Development only: Public AI through the team's budget gateway (caps, cache, ledger). Not shipped in any runtime path."""

    def __init__(self, gw_dir, tag, cap, model="swiss-ai/apertus-v1.5-70b", seed=None, log=None, record_to=None):
        import sys
        if not gw_dir or not os.path.isdir(gw_dir):
            raise ConfigError("the gateway backend is development-only and needs GLEICHLAUT_GATEWAY_DIR (or --gw-dir) pointing "
                              f"at the team's gateway checkout (got {gw_dir!r}); production uses --backend openai")
        sys.path.insert(0, gw_dir)
        from gw import chat                  # noqa: E402  (reads its key itself; never printed)
        self.chat, self.tag, self.cap, self.model = chat, tag, cap, model
        self.endpoint = "Public AI via development gateway (evaluation only; may route outside Switzerland)"
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
        resp = meta.get("resp") or {}
        served, fp = resp.get("model", ""), resp.get("system_fingerprint")
        if not meta.get("cached") and served.split("/")[-1].lower() != self.model.split("/")[-1].lower():
            raise RuntimeError(f"gateway served {served!r} for {self.model!r}: refusing the output")
        text = choice["message"]["content"]
        key = payload_key(self.model, prompt, max_tokens, 0.0, **extra)
        meta = dict(prompt_tokens=meta.get("prompt_tokens"), completion_tokens=meta.get("completion_tokens"), usd=meta.get("usd"),
                    secs=meta.get("secs"), model_served=served, seed=self.seed, cached=meta.get("cached", False), backend=fp)
        if self.record_to: write_cache(self.record_to, key, text, meta)
        _log(self.log, dict(meta, key=key, tag=self.tag, model=self.model))
        return strip_think(text), dict(meta, key=key)


LLAMA_MISSING = ("llama-cpp-python is not installed here, and the local Apertus 8B lane needs it: use the offline image: "
                 "make month-offline (= make month), or "
                 "`pip install --require-hashes -r requirements-offline.txt`; or draft through a certified 70B endpoint "
                 "(--backend openai, make month-70b)")


def llama_version():
    """the installed llama-cpp-python version, or None when it is not installed (base image, plain Python)."""
    try:
        import importlib.metadata as md
        return md.version("llama-cpp-python")
    except Exception:
        try:
            import llama_cpp
            return getattr(llama_cpp, "__version__", None)
        except Exception:
            return None


def require_llama():
    """raise ConfigError (one line, exit 2) when llama-cpp-python cannot be imported."""
    try:
        import llama_cpp, numpy          # noqa: F401
    except ImportError:
        raise ConfigError(LLAMA_MISSING)


def file_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""): h.update(b)
    return h.hexdigest()


class LlamaCpp:
    """Apertus 8B GGUF on CPU (llama-cpp-python), greedy, with the 8B digit ban of the research runs: every token that
    decodes to a digit, and every word-initial FR/IT number word 2-12 (gl2.BANWORDS), gets logit -inf.
    record_to: a cache root; every call is written there as a hash-addressed entry (write_cache), replayable by Cache.
    gguf_sha256 / runtime: what a build certificate (certify.build_lookup) is matched against."""

    def __init__(self, gguf_path, lang_of_prompt, n_ctx=8192, n_threads=None, log=None, gguf_sha256=None, record_to=None):
        if not gguf_path or not os.path.isfile(gguf_path):
            raise ConfigError(f"GGUF file not found: {gguf_path!r} (gleichlaut fetch-gguf downloads the pinned build into "
                              f"GLEICHLAUT_MODELS)")
        require_llama()
        from llama_cpp import Llama, LogitsProcessorList   # noqa: E402  (runtime dependency of the offline image only)
        import numpy as np
        from .core import gl2
        self.gguf_path, self.runtime = gguf_path, llama_version()
        self._sha = gguf_sha256
        self.endpoint = "local llama.cpp (in process)"
        self.n_threads = int(n_threads or os.environ.get("GLEICHLAUT_THREADS") or cpu_count())
        self.llm = Llama(model_path=gguf_path, n_ctx=n_ctx, n_threads=self.n_threads, n_threads_batch=self.n_threads,
                         logits_all=False, verbose=False)
        self.LP, self.np, self.lang_of_prompt, self.log, self.record_to = LogitsProcessorList, np, lang_of_prompt, log, record_to
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
        # The key is the sha256 of the request sent above (model, the one user message, max_tokens, temperature), as for the
        # 70B. The digit / number-word mask is not part of it: it acts on the logits during generation, not on the request.
        key = payload_key(self.model, prompt, max_tokens, 0.0)
        if self.record_to: write_cache(self.record_to, key, text, {k: meta[k] for k in ("prompt_tokens", "completion_tokens", "secs")})
        _log(self.log, dict(meta, tag=tag, ts=_now(), endpoint=self.endpoint, model=self.model, key=key))
        return strip_think(text), dict(meta, key=key)

    @property
    def gguf_sha256(self):
        if self._sha is None: self._sha = file_sha256(self.gguf_path)
        return self._sha


class DomainAsk:
    """--prompt-domain: wraps a backend and replaces the first sentence of every SL drafting prompt (the frozen PA template
    names the Spezialitaetenliste) by a sentence about another kind of text. The frozen files are never touched; the
    prompt string is rewritten on its way to the model. Uncertified by construction: callers mark every draft for review."""
    FIRST = "A Swiss reimbursement limitation (Spezialitätenliste, BAG) was amended in German."

    def __init__(self, ask, domain):
        d = (domain or "").strip()
        if not d: raise ConfigError("--prompt-domain needs a non-empty text")
        self.ask = ask
        self.sentence = d if d.endswith((".", "!", "?")) else f"A {d} was amended in German."
        self.rewritten = 0

    def __getattr__(self, k):            # model, endpoint, expect_served, hits ... of the wrapped backend
        return getattr(self.ask, k)

    def __setattr__(self, k, v):
        if k in ("ask", "sentence", "rewritten"): object.__setattr__(self, k, v)
        else: setattr(self.ask, k, v)

    def __call__(self, prompt, tag, cap, max_tokens):
        if prompt.startswith(self.FIRST):
            prompt = self.sentence + prompt[len(self.FIRST):]; object.__setattr__(self, "rewritten", self.rewritten + 1)
        return self.ask(prompt, tag, cap, max_tokens)


def cpu_count():
    """CPUs this process may use (the container's CPU set, not the host's), for llama.cpp n_threads."""
    try: return max(1, len(os.sched_getaffinity(0)))
    except (AttributeError, OSError): return max(1, os.cpu_count() or 1)


def lang_of_prompt(prompt):
    """target language of an SL or Fedlex drafting prompt (both name it in English before any target text)."""
    m = re.search(r"\b(French|Italian)\b", prompt)
    return {"French": "fr", "Italian": "it"}[m.group(1)] if m else "fr"
