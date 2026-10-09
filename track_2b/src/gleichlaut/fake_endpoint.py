"""A fake OpenAI-compatible chat endpoint for test environments and the operations tests. No model is called.

  python -m gleichlaut.fake_endpoint --port 8099 [--host 127.0.0.1] [--mode recorded|echo|non-apertus|error|hang]
  then: LLM_BASE_URL=http://127.0.0.1:8099/v1 gleichlaut certify / canary / draft / month / live

Modes:
  recorded     answer from the recorded 70B responses (data/cache/responses, looked up by the sha256 of the request payload, the
               same key the cache backend uses), else echo. A certification run against it reproduces the recorded fresh-166 run
               (PASS), so it exercises certify -> canary -> draft end to end without a model.
  echo         answer with the old target text of the prompt, unchanged (a model that never applies the change; the canary fails)
  non-apertus  a valid answer, but served by a non-Apertus model id (every runtime backend must refuse it)
  error        HTTP 500 on every request (retries, back-off, exit 6)
  hang         accept the connection and never answer (timeouts and the request deadline)
Older names: error500 = error, wrongmodel = non-apertus. GET {path}/models lists the requested model.

Every answer carries system_fingerprint (--fingerprint, default fp_test_1). Requests are kept in .requests (path, Authorization
header, body) for tests. Binds to 127.0.0.1 by default; never expose it: it answers anyone with recorded public texts.

In-process: with FakeOpenAI(mode="recorded") as f: os.environ["LLM_BASE_URL"] = f.url"""
import argparse, json, os, re, sys, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))      # track_2b/
CACHE = os.path.join(ROOT, "data", "cache", "responses")
RX = re.compile(r"\n(?:French|Italian) \(old\): (.*?)\n\nOutput only", re.S)
MODES = ("recorded", "echo", "non-apertus", "error", "hang")
ALIASES = {"error500": "error", "wrongmodel": "non-apertus"}


class FakeOpenAI:
    def __init__(self, mode="recorded", fingerprint="fp_test_1", path="/v1", host="127.0.0.1", port=0, verbose=False):
        self.mode, self.fingerprint, self.path, self.requests, self.verbose = mode, fingerprint, path, [], verbose
        self.stop = threading.Event()
        fake = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, fmt, *a):
                if fake.verbose: sys.stderr.write("fake_endpoint: " + fmt % a + "\n")

            def _send(self, code, obj):
                out = json.dumps(obj).encode()
                self.send_response(code); self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(out))); self.end_headers(); self.wfile.write(out)

            def do_GET(self):
                if self.path.rstrip("/").endswith("/models"):
                    return self._send(200, dict(object="list", data=[dict(id="swiss-ai/apertus-v1.5-70b", object="model", owned_by="fake")]))
                self._send(404, {"error": "fake: only POST {path}/chat/completions and GET {path}/models"})

            def do_POST(self):
                n = int(self.headers.get("Content-Length", 0))
                try: body = json.loads(self.rfile.read(n) or b"{}")
                except ValueError: return self._send(400, {"error": "fake: body is not JSON"})
                fake.requests.append(dict(path=self.path, auth=self.headers.get("Authorization"), body=body))
                mode = ALIASES.get(fake.mode, fake.mode)
                if mode == "hang":
                    while not fake.stop.wait(0.05): pass
                    return
                if mode == "error": return self._send(500, {"error": "fake: mode error"})
                if not self.path.endswith("/chat/completions"): return self._send(404, {"error": "fake: unknown path"})
                try:
                    prompt = body["messages"][-1]["content"]; model = body["model"]
                except (KeyError, IndexError, TypeError):
                    return self._send(400, {"error": "fake: expected {model, messages:[...]}"})
                text = None
                if mode == "recorded":
                    from gleichlaut.backends import payload_key
                    extra = {"seed": body["seed"]} if "seed" in body else {}
                    k = payload_key(model, prompt, body.get("max_tokens"), body.get("temperature", 0.0), **extra)
                    p = os.path.join(CACHE, k[:2], k + ".json")
                    if os.path.exists(p):
                        with open(p, encoding="utf-8") as f: text = json.load(f)["text"]
                if text is None:
                    m = RX.search(prompt); text = m.group(1) if m else "?"
                served = "openai/gpt-4o" if mode == "non-apertus" else model
                self._send(200, dict(id="fake", object="chat.completion", created=int(time.time()), model=served,
                                     system_fingerprint=fake.fingerprint,
                                     choices=[dict(index=0, message=dict(role="assistant", content=text), finish_reason="stop")],
                                     usage=dict(prompt_tokens=len(prompt) // 3, completion_tokens=len(text) // 3)))

        self.srv = ThreadingHTTPServer((host, port), Handler)
        self.srv.daemon_threads = True
        self.url = f"http://{host}:{self.srv.server_address[1]}{self.path}"

    def __enter__(self):
        threading.Thread(target=self.srv.serve_forever, daemon=True).start(); return self

    def __exit__(self, *a):
        self.stop.set(); self.srv.shutdown(); self.srv.server_close()


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m gleichlaut.fake_endpoint", description=__doc__.split("\n\n")[0])
    ap.add_argument("--port", type=int, default=8099)
    ap.add_argument("--host", default="127.0.0.1", help="bind address (default 127.0.0.1; 0.0.0.0 only inside a test network)")
    ap.add_argument("--mode", default="recorded", choices=MODES + tuple(ALIASES))
    ap.add_argument("--fingerprint", default="fp_test_1", help="system_fingerprint to report (change it to test the canary warning)")
    ap.add_argument("--path", default="/v1")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args(argv)
    f = FakeOpenAI(a.mode, a.fingerprint, a.path, a.host, a.port, verbose=not a.quiet)
    print(f"fake OpenAI-compatible endpoint ({a.mode}) at {f.url}  ->  export LLM_BASE_URL={f.url}", flush=True)
    try: f.srv.serve_forever()
    except KeyboardInterrupt: pass
    finally: f.stop.set(); f.srv.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
