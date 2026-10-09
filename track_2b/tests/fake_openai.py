"""A local, in-process fake of an OpenAI-compatible chat endpoint (http.server on 127.0.0.1) for the operations tests.
No model is called. Modes:
  recorded    answer from the recorded responses (data/cache/responses, looked up by the request payload hash, the same key
              the cache backend uses), else echo; so a certification run against it reproduces the recorded fresh-166 run
  echo        answer with the old target text of the prompt, unchanged (a model that never applies the change)
  error500    HTTP 500 on every request
  wrongmodel  a valid answer, but served by a non-Apertus model id
usage: with FakeOpenAI(mode="recorded") as f: os.environ["LLM_BASE_URL"] = f.url"""
import json, os, re, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

H = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(H, "..", "data", "cache", "responses")
RX = re.compile(r"\n(?:French|Italian) \(old\): (.*?)\n\nOutput only", re.S)


class FakeOpenAI:
    def __init__(self, mode="recorded", fingerprint="fp_test_1", path="/v1"):
        self.mode, self.fingerprint, self.path, self.requests = mode, fingerprint, path, []
        fake = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *a): pass

            def do_POST(self):
                n = int(self.headers.get("Content-Length", 0)); body = json.loads(self.rfile.read(n) or b"{}")
                fake.requests.append(dict(path=self.path, auth=self.headers.get("Authorization"), body=body))
                if fake.mode == "error500" or not self.path.endswith("/chat/completions"):
                    self.send_response(500 if fake.mode == "error500" else 404); self.end_headers(); self.wfile.write(b'{"error":"fake"}'); return
                prompt = body["messages"][-1]["content"]; text = None
                if fake.mode == "recorded":
                    from gleichlaut.backends import payload_key
                    extra = {"seed": body["seed"]} if "seed" in body else {}
                    k = payload_key(body["model"], prompt, body["max_tokens"], body.get("temperature", 0.0), **extra)
                    p = os.path.join(CACHE, k[:2], k + ".json")
                    if os.path.exists(p): text = json.load(open(p, encoding="utf-8"))["text"]
                if text is None:
                    m = RX.search(prompt); text = m.group(1) if m else "?"
                served = "openai/gpt-4o" if fake.mode == "wrongmodel" else body["model"]
                out = json.dumps(dict(id="fake", object="chat.completion", model=served, system_fingerprint=fake.fingerprint,
                                      choices=[dict(index=0, message=dict(role="assistant", content=text), finish_reason="stop")],
                                      usage=dict(prompt_tokens=len(prompt) // 3, completion_tokens=len(text) // 3))).encode()
                self.send_response(200); self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(out))); self.end_headers(); self.wfile.write(out)

        self.srv = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.srv.server_address[1]}{self.path}"

    def __enter__(self):
        threading.Thread(target=self.srv.serve_forever, daemon=True).start(); return self

    def __exit__(self, *a):
        self.srv.shutdown(); self.srv.server_close()
