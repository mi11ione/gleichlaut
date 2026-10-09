"""Operations: certification gate, canary, draft / month pipeline, exit codes, ingest of the 'latest' feed.
Live paths are exercised against tests/fake_openai.py, an OpenAI-compatible fake started in-process on 127.0.0.1; no model
and no external service is called."""
import contextlib, io, json, os, shutil, sys, tempfile, threading, unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(H, "..", "src")); sys.path.insert(0, H)
from fake_openai import FakeOpenAI
from gleichlaut import backends, certify, cli, core, score
from gleichlaut.sl import ingest, mine

M70 = core.M70
ENV = ("LLM_BASE_URL", "LLM_API_KEY", "LLM_NAME", "GLEICHLAUT_STATE", "GLEICHLAUT_HTTP_RETRIES", "GLEICHLAUT_HTTP_BACKOFF",
       "GLEICHLAUT_HTTP_TIMEOUT", "GLEICHLAUT_TIMEOUT", "GLEICHLAUT_RETRIES", "GLEICHLAUT_BACKOFF", "GLEICHLAUT_DEADLINE",
       "GLEICHLAUT_GATEWAY_DIR", "SKIP_MODEL", "GLEICHLAUT_GGUF", "GLEICHLAUT_HIST", "GLEICHLAUT_DEBUG", "GLEICHLAUT_CERT_KEY",
       "GLEICHLAUT_CERT_DAYS", "GLEICHLAUT_CANARY_MAX_AGE_DAYS", "HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY", "http_proxy",
       "https_proxy", "no_proxy", "ALL_PROXY", "all_proxy", "SSL_CERT_FILE", "REQUESTS_CA_BUNDLE", "GLEICHLAUT_MODELS",
       "GLEICHLAUT_RESOURCES", "GLEICHLAUT_METRICS_DIR")


@contextlib.contextmanager
def env(**kw):
    old = {k: os.environ.get(k) for k in ENV}
    for k in ENV: os.environ.pop(k, None)
    os.environ.update(GLEICHLAUT_HTTP_RETRIES="1", GLEICHLAUT_HTTP_BACKOFF="0",
                      GLEICHLAUT_MODELS=os.path.join(tempfile.gettempdir(), "gl-ops-no-models"))   # never hash a developer's 5 GB GGUF
    os.environ.update({k: v for k, v in kw.items() if v is not None})
    try: yield
    finally:
        for k, v in old.items():
            if v is None: os.environ.pop(k, None)
            else: os.environ[k] = v


@contextlib.contextmanager
def tmpdir():
    d = tempfile.mkdtemp(prefix="gl-ops-")
    try: yield d
    finally: shutil.rmtree(d, ignore_errors=True)


def run_cli(*args):
    o, e = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(o), contextlib.redirect_stderr(e): rc = cli.main(list(args))
    return rc, o.getvalue(), e.getvalue()


def fresh(n):
    return score.load_items("items/items_fresh.json")[:n]


def write_json(path, obj):
    with open(path, "w", encoding="utf-8") as f: json.dump(obj, f, ensure_ascii=False)
    return path


def ago(days=0, minutes=0):
    import datetime
    return (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days, minutes=minutes)).isoformat(timespec="seconds")


def reference_records():
    F = score.load_jsonl(score.RUNS["fresh166"]["final"])
    return [json.loads(json.dumps(F[x["key"]])) for x in score.load_items(certify.ITEMS)]


def fake_cert(state, endpoint, model=M70, status=None, kind="endpoint", date=None, name="c", R=None, fps=("fp_test_1",)):
    """a real certificate in `state` (GLEICHLAUT_STATE must point there): the recorded reference run (a PASS) as its suite
    records, a call log naming the endpoint, hashes, expiry, HMAC if a key is set. status given: written over by hand."""
    os.makedirs(os.path.join(state, "certificates"), exist_ok=True)
    I = score.load_items(certify.ITEMS); R = R or reference_records(); ep = backends.endpoint_id(endpoint)
    log = os.path.join(state, "certificates", f"{name}.calls.jsonl")
    with open(log, "w", encoding="utf-8") as f:
        for r in R:
            if not r.get("rule_only"): f.write(json.dumps(dict(endpoint=ep, model=model, model_served=model, system_fingerprint=fps[0])) + "\n")
    p, c = certify.write_certificate(name, kind, ep, model, I, R, 1.0, {model}, {"None"}, set(fps), log, date=date or ago(minutes=5))
    if status and status != c["status"]:
        c["status"] = status; certify._write_json(p, c)
    return p


# ------------------------------------------------------------------ 1. certification gate
def test_endpoint_id_never_carries_credentials_or_query():
    e = backends.endpoint_id("HTTPS://user:sk-secret@API.Example.ch:443/v1/chat/completions/?key=abc#x")
    assert e == "https://api.example.ch/v1", e
    assert backends.endpoint_id("http://127.0.0.1:8080/v1/") == "http://127.0.0.1:8080/v1"


def test_shipped_replay_certificate_never_authorises():
    shipped = json.load(open(os.path.join(certify.EVIDENCE, "recorded-fresh166.json"), encoding="utf-8"))
    assert shipped["status"] == "PASS" and shipped["kind"] == "replay"
    with tmpdir() as d, env(GLEICHLAUT_STATE=d):
        os.makedirs(os.path.join(d, "certificates"))
        shutil.copy(os.path.join(certify.EVIDENCE, "recorded-fresh166.json"), os.path.join(d, "certificates"))
        for url in ("https://anything.example/v1", "recorded responses (data/cache)"):
            assert certify.certified(url, M70) is None                     # a model *called* apertus is not enough


def test_fake_endpoint_is_not_certified_until_a_pass_certificate_for_that_exact_endpoint():
    with tmpdir() as d, env(GLEICHLAUT_STATE=d), FakeOpenAI("recorded") as f:
        assert certify.certified(f.url, M70) is None
        fake_cert(d, f.url, kind="replay", name="r")                        # replay kind: never
        assert certify.certified(f.url, M70) is None
        fake_cert(d, f.url, name="ok")
        assert certify.certified(f.url, M70)["name"] == "ok"
        assert certify.certified(f.url + "/chat/completions", M70)                   # same endpoint id
        assert certify.certified(f.url.replace("/v1", "/v2"), M70) is None             # other path
        assert certify.certified(f.url.replace("127.0.0.1", "localhost"), M70) is None # other host
        assert certify.certified(f.url, "swiss-ai/apertus-v1.5-8b") is None            # other model
        fake_cert(d, f.url, status="FAIL", date=ago(minutes=1), name="later")
        assert certify.certified(f.url, M70) is None                        # the newest certificate decides


def test_certify_against_fake_endpoint_then_gate_and_canary():
    """the full suite (285 requests) against the fake serving the recorded answers reproduces the PASS; the certificate
    names the endpoint, never the key; draft is then allowed; the canary passes, and fails on a model that drifts."""
    with tmpdir() as d, FakeOpenAI("recorded") as f, env(LLM_BASE_URL=f.url, LLM_API_KEY="sk-secret-test-key", GLEICHLAUT_STATE=d):
        rc, out, err = run_cli("certify", "--workers", "4")
        assert rc == 0, out + err
        assert "exact +11.4 pts vs rules-only (95% CI +4.8 to +18.7)" in out and "+-" not in out, out
        assert len(f.requests) == 285 and f.requests[0]["auth"] == "Bearer sk-secret-test-key"
        c = certify.certified(f.url, M70)
        assert c and c["kind"] == "endpoint" and c["status"] == "PASS" and c["endpoint"] == backends.endpoint_id(f.url)
        assert c["system_fingerprints"] == ["fp_test_1"] and c["models_served"] == [M70]
        for root, _, files in os.walk(d):
            for fn in files: assert "sk-secret-test-key" not in open(os.path.join(root, fn), encoding="utf-8", errors="ignore").read()
        assert os.path.exists(os.path.join(d, c["run_records"]))
        rc, out, _ = run_cli("certify", "--canary", "10")
        assert rc == 0 and "CANARY PASSED" in out, out
        f.mode = "echo"                                                      # a model that stops applying changes
        rc, out, _ = run_cli("certify", "--canary", "10")
        assert rc == 3 and "CANARY FAILED" in out and "flag agreement" in out, out
        f.mode = "recorded"
        with tmpdir() as o:
            items = write_json(os.path.join(o, "i.json"), fresh(2))
            rc, out, err = run_cli("draft", "--items", items, "--out", os.path.join(o, "r"), "--allow-stale-canary")
            assert rc == 3 and "FAILED" in err and not os.path.exists(os.path.join(o, "r", "records.jsonl")), (rc, out, err)
            assert run_cli("certify", "--canary", "10")[0] == 0                 # a later passing canary lifts the refusal
            rc, out, err = run_cli("draft", "--items", items, "--out", os.path.join(o, "r"))
            assert rc == 0 and "certification gate" in out and "canary gate" in out, out + err
        assert len(os.listdir(os.path.join(d, "canary"))) == 6                  # 3 reports + 3 call logs, none overwritten


def test_canary_tolerances_ignore_byte_drift_but_not_flag_drift():
    I = fresh(20); ref = {x["key"]: dict(out=x["tgt_old"], guard_flag=i % 2 == 0) for i, x in enumerate(I)}
    R = [dict(key=x["key"], out=x["tgt_old"] + " ", guard_flag=ref[x["key"]]["guard_flag"]) for x in I]   # every byte differs
    rep = certify.canary_report(I, R, ref)
    assert rep["ok"] and rep["info"]["byte_identical"] == 0
    for r in R[:4]: r["guard_flag"] = not r["guard_flag"]                    # 80% flag agreement < 0.85
    rep = certify.canary_report(I, R, ref)
    assert not rep["ok"] and "flag agreement" in rep["reasons"][0]


def test_uncertified_endpoint_is_refused_for_sl_and_air_gapped_is_reviewed():
    with tmpdir() as d, FakeOpenAI("recorded") as f, env(LLM_BASE_URL=f.url, GLEICHLAUT_STATE=d):
        items = write_json(os.path.join(d, "i.json"), fresh(2))
        rc, out, err = run_cli("draft", "--items", items, "--out", os.path.join(d, "r"))
        assert rc == 4 and "no endpoint certificate" in err and not f.requests, (rc, err)
        rc, out, err = run_cli("draft", "--items", items, "--out", os.path.join(d, "r"), "--air-gapped")
        assert rc == 0, out + err
        R = [json.loads(l) for l in open(os.path.join(d, "r", "records.jsonl"), encoding="utf-8")]
        assert len(R) == 2 and all(r["status"] in ("flagged", "human") for r in R)
        assert all(r.get("review_reason", "").startswith("air-gapped") for r in R if r["status"] != "human")


def test_gateway_backend_needs_env_and_has_no_developer_default():
    with env():
        rc, out, _ = run_cli("certify", "--backend", "gateway")
        assert rc == 2 and "GLEICHLAUT_GATEWAY_DIR" in out
    assert "Desktop" not in open(certify.__file__, encoding="utf-8").read()


# ------------------------------------------------------------------ 5. draft: resume, dry run, stub, friendly errors
def test_draft_stub_writes_incrementally_and_resumes():
    with tmpdir() as d, env():
        items = write_json(os.path.join(d, "i.json"), fresh(4)); out = os.path.join(d, "r")
        rc, o, e = run_cli("draft", "--items", items, "--out", out, "--backend", "stub")
        assert rc == 0, o + e
        p = os.path.join(out, "records.jsonl"); R = [json.loads(l) for l in open(p, encoding="utf-8")]
        assert [r["key"] for r in R] == [x["key"] for x in fresh(4)]
        assert all(r["status"] != "ready" for r in R)                       # stub drafts are never ready
        assert all("shadow_exact" in r for r in R if r["status"] != "human")
        with open(p, "rb+") as f:                                           # simulate a crash: drop the last record, tear a line
            lines = f.read().splitlines(keepends=True); f.seek(0); f.truncate()
            f.write(b"".join(lines[:2]) + lines[2][:40])
        rc, o, e = run_cli("draft", "--items", items, "--out", out, "--backend", "stub")
        assert rc == 0 and "resuming: 2 of 4" in o, o + e
        R = [json.loads(l) for l in open(p, encoding="utf-8")]
        assert sorted(r["key"] for r in R) == sorted(x["key"] for x in fresh(4)) and len(R) == 4
        s = json.load(open(os.path.join(out, "summary.json"), encoding="utf-8"))
        assert s["records"] == 4 and s["shadow"]["compared"] >= 1 and any("--records" in n for n in s["next"])


def test_dry_run_prints_prompts_and_slot_map_without_any_request():
    with tmpdir() as d, FakeOpenAI("recorded") as f, env(LLM_BASE_URL=f.url, GLEICHLAUT_STATE=d):
        items = write_json(os.path.join(d, "i.json"), fresh(3))
        rc, out, err = run_cli("draft", "--items", items, "--out", os.path.join(d, "r"), "--dry-run")
        assert rc == 0 and not f.requests, err
        assert "would REFUSE" in out and "slot map" in out and "German (old):" in out and "No request was sent" in out
        assert not os.path.exists(os.path.join(d, "r", "records.jsonl"))


def test_bad_items_files_fail_with_a_message_and_no_traceback():
    good = fresh(1)[0]
    cases = {"missing.json": None, "broken.json": "{not json", "lang.json": [dict(good, lang="de")],
             "notgt.json": [{k: v for k, v in good.items() if k != "tgt_old"}], "dup.json": [good, good], "empty.json": []}
    with tmpdir() as d, env():
        for name, content in cases.items():
            p = os.path.join(d, name)
            if content is not None:
                with open(p, "w", encoding="utf-8") as f: f.write(content if isinstance(content, str) else json.dumps(content))
            rc, out, err = run_cli("draft", "--items", p, "--out", os.path.join(d, "r"), "--backend", "stub")
            assert rc == 2 and err.startswith("error:") and "Traceback" not in err, (name, rc, err)
        assert "'de' not one of" in run_cli("draft", "--items", os.path.join(d, "lang.json"), "--out", d, "--backend", "stub")[2]


def test_missing_and_unreachable_endpoint_and_wrong_model_exit_cleanly():
    with tmpdir() as d:
        items = write_json(os.path.join(d, "i.json"), fresh(2))
        with env():
            rc, out, err = run_cli("draft", "--items", items, "--out", os.path.join(d, "a"))
            assert rc == 2 and "LLM_BASE_URL is not set" in err, err
        with env(LLM_BASE_URL="http://127.0.0.1:9/v1", GLEICHLAUT_STATE=d):            # discard port: nothing listens
            rc, out, err = run_cli("draft", "--items", items, "--out", os.path.join(d, "b"), "--air-gapped")
            assert rc == 6 and "cannot reach http://127.0.0.1:9/v1" in err and "resume" in err, err
        with FakeOpenAI("wrongmodel") as f, env(LLM_BASE_URL=f.url, GLEICHLAUT_STATE=d):
            rc, out, err = run_cli("draft", "--items", items, "--out", os.path.join(d, "c"), "--air-gapped")
            assert rc == 6 and "not an Apertus model" in err, err
        with FakeOpenAI("error500") as f, env(LLM_BASE_URL=f.url, GLEICHLAUT_STATE=d):
            rc, out, err = run_cli("draft", "--items", items, "--out", os.path.join(d, "e"), "--air-gapped")
            assert rc == 6 and "HTTP 500" in err, err


def test_change_ratio_is_computed_when_missing_and_rewrites_go_to_a_human():
    x = {k: v for k, v in fresh(1)[0].items() if k not in ("de_ratio", "change_ratio")}
    y = dict(x, key="rewrite-fr", de_new="Völlig neuer Text ohne Bezug zum alten Wortlaut, vergütet nur nach Kostengutsprache.")
    with tmpdir() as d:
        items = cli.load_items(write_json(os.path.join(d, "i.json"), [x, y]))
    assert items[0]["change_ratio"] == round(mine.change_ratio(x["de_old"], x["de_new"]), 3)
    assert cli.route(items[0])[0] == "draft" and cli.route(items[1])[0] == "human" and items[1]["change_ratio"] > 0.6


def test_research_item_files_match_the_schema():
    S = json.load(open(cli.SCHEMA, encoding="utf-8"))
    for f in ("items_fresh.json", "items_dev.json", "items_oos.json"):
        assert cli.validate(S, score.load_items(f"items/{f}")) == [], f


# ------------------------------------------------------------------ 6. exit codes of live / run
def test_live_exit_code_and_run_status_line():
    with tmpdir() as d, FakeOpenAI("error500") as f, env(LLM_BASE_URL=f.url):
        old = cli.OUT; cli.OUT = d
        try:
            rc, out, _ = run_cli("live")
            assert rc == 6 and "LIVE SLICE FAILED: " in out, out
            from gleichlaut import replay
            saved = (replay.main, cli.cmd_emit, cli.cmd_ui)
            replay.main = lambda argv: 0; cli.cmd_emit = lambda: 0; cli.cmd_ui = lambda: 0
            try: rc, out, _ = run_cli("run")
            finally: replay.main, cli.cmd_emit, cli.cmd_ui = saved
            assert rc == 0 and "LIVE SLICE FAILED: " in out and out.rstrip().endswith("reproduction PASSED; live slice FAILED"), out
            assert "USD 0.0028" in out and "CHF 0.0024" in out
        finally: cli.OUT = old
    with env(SKIP_MODEL="1"):
        assert run_cli("live")[0] == 0


# ------------------------------------------------------------------ 4. month pipeline on fixture snapshots
def _bundle(mpd, name, cuds):
    e = [{"resource": {"resourceType": "MedicinalProductDefinition", "id": mpd, "name": [{"productName": name}]}}]
    e += [{"resource": {"resourceType": "ClinicalUseDefinition", "id": k, "indication": {"diseaseSymptomProcedure": {"concept": {"text": t}}}}}
          for k, t in cuds]
    return json.dumps({"resourceType": "Bundle", "entry": e})


SNAP = {  # (old, new) per language for FOO.01 (an amendment), BAR.01 (a rewrite), BAZ.01 (no change)
    "de": [("Nach Kostengutsprache. Maximal 4 Packungen pro Jahr bei Erwachsenen mit schwerer Erkrankung.",
            "Nach Kostengutsprache. Maximal 6 Packungen pro Jahr bei Erwachsenen mit schwerer Erkrankung."),
           ("Vergütet zur Behandlung der Migräne.", "Nur nach vorgängiger Kostengutsprache durch den Vertrauensarzt, ab dem dritten Zyklus."),
           ("Unverändert.", "Unverändert.")],
    "fr": [("Après garantie de prise en charge. Au maximum 4 emballages par an chez les adultes atteints d'une maladie grave.",
            "Après garantie de prise en charge. Au maximum 6 emballages par an chez les adultes atteints d'une maladie grave."),
           ("Remboursé pour le traitement de la migraine.", "Remboursé pour le traitement de la migraine."), ("Inchangé.", "Inchangé.")],
    "it": [("Previa garanzia di assunzione dei costi. Al massimo 4 confezioni all'anno negli adulti con malattia grave.",
            "Previa garanzia di assunzione dei costi. Al massimo 4 confezioni all'anno negli adulti con malattia grave."),
           ("Rimborsato per il trattamento dell'emicrania.", "Rimborsato per il trattamento dell'emicrania."), ("Invariato.", "Invariato.")],
}


def _snapshots(d, a="20261001", b="20261101"):
    for lang, rows in SNAP.items():
        for date, i in ((a, 0), (b, 1)):
            lines = [_bundle("M1", "Foo Tabl", [("FOO.01", rows[0][i]), ("BAZ.01", rows[2][i])]), _bundle("M2", "Bar Inj", [("BAR.01", rows[1][i])])]
            ingest.save(ingest.extract(lines), os.path.join(d, f"{date}-{lang}.json"))


def test_month_from_snapshots_shadow_mode_with_stub():
    with tmpdir() as d, env():
        with contextlib.redirect_stderr(io.StringIO()): _snapshots(d)
        out = os.path.join(d, "m")
        rc, o, e = run_cli("month", "--from", "20261001", "--to", "20261101", "--snapshots", d, "--backend", "stub", "--out", out)
        assert rc == 0, o + e
        I = {x["key"]: x for x in json.load(open(os.path.join(out, "items.json"), encoding="utf-8"))}
        assert len(I) == 4                                                   # FOO.01 and BAR.01 x fr/it
        foo_fr = next(x for x in I.values() if x["cud_new"] == "FOO.01" and x["lang"] == "fr")
        foo_it = next(x for x in I.values() if x["cud_new"] == "FOO.01" and x["lang"] == "it")
        assert "tgt_new" in foo_fr and "tgt_new" not in foo_it and foo_it["tgt_published"] == "unchanged"
        assert foo_fr["product"] == "Foo Tabl" and foo_fr["snap_old"] == "20261001" and 0 < foo_fr["change_ratio"] <= 0.6
        R = {r["key"]: r for r in map(json.loads, open(os.path.join(out, "records.jsonl"), encoding="utf-8"))}
        assert all(R[k]["status"] == "human" for k, x in I.items() if x["cud_new"] == "BAR.01")
        assert R[foo_fr["key"]]["status"] in ("flagged", "ready") and "shadow_exact" in R[foo_fr["key"]]
        s = json.load(open(os.path.join(out, "summary.json"), encoding="utf-8"))
        assert s["mode"].startswith("shadow") and s["mining"]["de_changes"] == 1 and s["status"]["human"] == 2
        # resumable: a second run drafts nothing new
        rc, o, e = run_cli("month", "--from", "20261001", "--to", "20261101", "--snapshots", d, "--backend", "stub", "--out", out)
        assert rc == 0 and "resuming: 4 of 4" in o, o
        # missing snapshots without --fetch: a clear message, exit 2
        rc, o, e = run_cli("month", "--from", "20261001", "--to", "20261201", "--snapshots", d, "--backend", "stub")
        assert rc == 2 and "20261201-de.json" in e and "--fetch" in e, e
        rc, o, e = run_cli("month", "--from", "20260401", "--to", "20260504", "--snapshots", d)
        assert rc == 2 and "excluded" in e, e


def test_month_pre_publication_items_and_certification_gate():
    with tmpdir() as d, FakeOpenAI("echo") as f, env(LLM_BASE_URL=f.url, GLEICHLAUT_STATE=d):
        items = [{k: v for k, v in x.items() if k in ("key", "lang", "de_old", "de_new", "tgt_old")} for x in fresh(2)]
        p = write_json(os.path.join(d, "sl-team.json"), items)
        rc, o, e = run_cli("month", "--items", p, "--out", os.path.join(d, "m"))
        assert rc == 4 and not f.requests, e                                  # SL lane: endpoint not certified
        fake_cert(d, f.url)
        rc, o, e = run_cli("month", "--items", p, "--out", os.path.join(d, "m"))
        assert rc == 0 and f.requests, o + e
        s = json.load(open(os.path.join(d, "m", "summary.json"), encoding="utf-8"))
        assert s["mode"] == "pre-publication" and "shadow" not in s and s["calls"]["n"] == len(f.requests)
        calls = [json.loads(l) for l in open(os.path.join(d, "m", "calls.jsonl"), encoding="utf-8")]
        assert {"ts", "endpoint", "model", "model_served", "system_fingerprint", "prompt_tokens", "completion_tokens", "secs", "key", "tag"} <= set(calls[0])


def test_mine_dates_are_parameters():
    import inspect
    assert "snaps" in inspect.signature(mine.mine).parameters
    for bad in (["20260504", "20260601"], ["20261001", "20260901"], ["2026-10-01", "20261101"]):
        try: mine.check_snaps(bad); raise AssertionError(bad)
        except ValueError: pass


def test_emit_and_ui_passthrough_of_month_records():
    if not cli._accepts("gleichlaut.emit.__main__", "--records"):
        rc, out, _ = run_cli("emit", "--records", "r.jsonl", "--items", "i.json")
        assert rc == 2 and "does not accept" in out; return
    try: import lxml  # noqa: F401
    except ImportError: raise unittest.SkipTest("lxml not installed (emit validation needs it)")
    with tmpdir() as d, env():
        with contextlib.redirect_stderr(io.StringIO()): _snapshots(d)
        out = os.path.join(d, "m")
        rc, o, e = run_cli("month", "--from", "20261001", "--to", "20261101", "--snapshots", d, "--backend", "stub", "--out", out, "--emit")
        assert rc == 0, o + e
        assert os.listdir(os.path.join(out, "emit", "xliff")) and os.path.exists(os.path.join(out, "ui", "index.html"))


# ------------------------------------------------------------------ 9. ingest: the 'latest' feed under its publication date
def test_ingest_latest_is_stored_under_its_publication_date_with_an_alias():
    body = (_bundle("M1", "Foo Tabl", [("FOO.01", "Text A")]) + "\n").encode()

    class Feed(BaseHTTPRequestHandler):
        def log_message(self, *a): pass
        def do_GET(self):
            self.send_response(200); self.send_header("Last-Modified", "Mon, 05 Oct 2026 22:30:00 GMT")   # = 6 Oct in Zurich
            self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)

    srv = ThreadingHTTPServer(("127.0.0.1", 0), Feed); threading.Thread(target=srv.serve_forever, daemon=True).start()
    old = ingest.BASE; ingest.BASE = f"http://127.0.0.1:{srv.server_address[1]}"
    try:
        with tmpdir() as d:
            with contextlib.redirect_stderr(io.StringIO()): snap, date = ingest.fetch("latest", "de", d)
            try:
                from zoneinfo import ZoneInfo; ZoneInfo("Europe/Zurich"); want = "20261006"
            except Exception: want = "20261005"
            assert date == want and os.path.exists(os.path.join(d, f"{want}-de.json"))
            assert json.load(open(os.path.join(d, "latest-de.json"), encoding="utf-8"))["lim"] == {"FOO.01": "Text A"}
            rec = json.load(open(os.path.join(d, "latest.json"), encoding="utf-8"))["de"]
            assert rec["date"] == want and rec["source"] == "HTTP Last-Modified"
            assert not any(f.startswith("latest-") and f != "latest-de.json" for f in os.listdir(d))
    finally:
        ingest.BASE = old; srv.shutdown(); srv.server_close()
    assert ingest.publication_date("2026-09-30T23:30:00Z")[1] == "feed timestamp"


def test_pending_review_certificate_is_resolved_by_human_labels():
    """outputs that differ from every hand-labelled output need a human label before the certificate holds."""
    real = certify.reference_labels
    def fewer():                                    # forget the labels of three non-exact outputs: they become 'new'
        ref = real(); drop = sorted(k for k, d in ref.items() if "exact" not in d.values())[:3]
        return {k: d for k, d in ref.items() if k not in drop}
    certify.reference_labels = fewer
    try:
        with tmpdir() as d, FakeOpenAI("recorded") as f, env(LLM_BASE_URL=f.url, GLEICHLAUT_STATE=d):
            rc, out, err = run_cli("certify", "--workers", "4")
            assert rc == 7 and "PENDING_REVIEW" in out, out + err
            assert certify.certified(f.url, M70) is None
            (p, c), = certify.certificates()
            assert len(c["needs_review"]) == 3
            tsv = os.path.join(d, "labels.tsv")
            with open(tsv, "w", encoding="utf-8") as fh:
                fh.write("key\tclass\n" + "".join(f"{k}\tbogus\n" for k in c["needs_review"]))
            assert run_cli("certify", "--resolve", p, "--labels", tsv)[0] == 2           # unknown class: refused
            with open(tsv, "w", encoding="utf-8") as fh:
                fh.write("key\tclass\n" + "".join(f"{k}\tequivalent\n" for k in c["needs_review"]))
            rc, out, err = run_cli("certify", "--resolve", p, "--labels", tsv)
            assert rc == 0 and "PENDING_REVIEW -> PASS" in out, out + err
            assert certify.certified(f.url, M70)["review_labels"]["n"] == 3
    finally:
        certify.reference_labels = real


# ------------------------------------------------------------------ round 2: tamper-evident certificates
def _edit(p, **kw):
    c = json.load(open(p, encoding="utf-8")); c.update(kw); write_json(p, c); certify._VERIFIED.clear(); return c


def test_hand_edited_or_tampered_certificates_never_open_the_gate():
    with tmpdir() as d, env(GLEICHLAUT_STATE=d):
        ep = "https://llm.internal.example/v1"
        I = score.load_items(certify.ITEMS)
        echo = [dict(r, out=x["tgt_old"], guard_flag=True, rule_only=False) for x, r in zip(I, reference_records())]
        echo = [dict(r, guard_flag=core.check_only("g3").check(x, r["out"])["flag"]) for x, r in zip(I, echo)]
        p = fake_cert(d, ep, name="echo", R=echo)                            # records of a model that never applies a change
        assert json.load(open(p))["status"] == "FAIL" and certify.certified(ep, M70) is None
        _edit(p, status="PASS")                                              # the juror's attack: flip the status by hand
        c, why = certify.lookup(ep, M70)
        assert c is None and ("re-score to FAIL" in why or "differ" in why), why
        p = fake_cert(d, ep, name="good", date=ago(minutes=1))
        assert certify.certified(ep, M70)["name"] == "good"
        runs = os.path.join(d, "runs", "certify_good.jsonl"); good = open(runs, encoding="utf-8").read()
        lines = good.splitlines(); r0 = json.loads(lines[0]); r0["out"] = r0["out"] + " Texte ajouté."
        with open(runs, "w", encoding="utf-8") as f: f.write("\n".join([json.dumps(r0, ensure_ascii=False)] + lines[1:]) + "\n")
        certify._VERIFIED.clear()
        assert "does not match the sha256" in certify.lookup(ep, M70)[1]     # edited records
        _edit(p, run_records_sha256=core.sha256(runs))                       # ... with the hash updated too
        why = certify.lookup(ep, M70)[1]
        assert "guard verdict differs" in why or "differ" in why or "re-score" in why, why
        with open(runs, "w", encoding="utf-8") as f: f.write(good)
        c = _edit(p, run_records_sha256=core.sha256(runs))
        assert certify.certified(ep, M70)
        os.remove(os.path.join(d, "certificates", "good.calls.jsonl")); certify._VERIFIED.clear()
        assert "call log file is missing" in certify.lookup(ep, M70)[1]


def test_certificate_expiry_freeze_hash_and_hmac():
    with tmpdir() as d, env(GLEICHLAUT_STATE=d):
        ep = "https://llm.internal.example/v1"
        p = fake_cert(d, ep, date=ago(days=91), name="old")
        assert "expired" in certify.lookup(ep, M70)[1]
        fake_cert(d, ep, date=ago(days=20), name="mid")
        assert certify.certified(ep, M70)["name"] == "mid"
        assert json.load(open(os.path.join(d, "certificates", "mid.json")))["expires"]
        with env(GLEICHLAUT_STATE=d, GLEICHLAUT_CERT_DAYS="10"):
            assert "expired" in certify.lookup(ep, M70)[1]                   # the validity configured at check time also applies
        p = fake_cert(d, ep, name="new")
        _edit(p, freeze_sha256="0" * 64)
        assert "other frozen code" in certify.lookup(ep, M70)[1]
        key = os.path.join(d, "..", os.path.basename(d) + ".key")
        with open(key, "wb") as f: f.write(os.urandom(32))
        try:
            p = fake_cert(d, ep, name="unsigned")
            with env(GLEICHLAUT_STATE=d, GLEICHLAUT_CERT_KEY=key):
                assert "unsigned" in certify.lookup(ep, M70)[1]
                p = fake_cert(d, ep, name="signed")
                assert "hmac_sha256" in json.load(open(p)) and certify.certified(ep, M70)["name"] == "signed"
                assert "HMAC ok" in certify.lookup(ep, M70)[1]
                _edit(p, expires="2099-01-01T00:00:00+00:00")
                assert "HMAC does not match" in certify.lookup(ep, M70)[1]
            with env(GLEICHLAUT_STATE=d, GLEICHLAUT_CERT_KEY=key + ".missing"):
                rc, out, _ = run_cli("certify", "--list")
                assert rc == 2 and "GLEICHLAUT_CERT_KEY" in out
        finally:
            os.remove(key)


# ------------------------------------------------------------------ round 2: the canary gates drafting
def test_stale_or_failed_canary_refuses_drafting_and_overrides_are_logged():
    with tmpdir() as d, FakeOpenAI("recorded") as f, env(LLM_BASE_URL=f.url, GLEICHLAUT_STATE=d):
        fake_cert(d, f.url, date=ago(days=40))
        items = write_json(os.path.join(d, "i.json"), fresh(2))
        rc, out, err = run_cli("draft", "--items", items, "--out", os.path.join(d, "a"))
        assert rc == 3 and "40 days old" in err and "--allow-stale-canary" in err and not f.requests, (rc, err)
        rc, out, err = run_cli("draft", "--items", items, "--out", os.path.join(d, "a"), "--dry-run")
        assert rc == 0 and "would REFUSE" in out and "stale" in out
        rc, out, err = run_cli("draft", "--items", items, "--out", os.path.join(d, "a"), "--allow-stale-canary")
        assert rc == 0 and "WARNING: canary gate overridden" in out, out + err
        log = [json.loads(l) for l in open(os.path.join(d, "gate-overrides.jsonl"), encoding="utf-8")]
        assert log[0]["override"] == "--allow-stale-canary" and log[0]["certificate"] == "c"
        s = json.load(open(os.path.join(d, "a", "summary.json"), encoding="utf-8"))
        assert s["gate"]["override"] == "--allow-stale-canary" and s["gate"]["canary"] == "stale"
        with env(LLM_BASE_URL=f.url, GLEICHLAUT_STATE=d, GLEICHLAUT_CANARY_MAX_AGE_DAYS="45"):
            assert run_cli("draft", "--items", items, "--out", os.path.join(d, "b"))[0] == 0
        assert run_cli("certify", "--canary", "5")[0] == 0                   # a fresh canary: no override needed
        rc, out, err = run_cli("draft", "--items", items, "--out", os.path.join(d, "c"))
        assert rc == 0 and "canary gate: latest check: canary" in out, out + err


def test_canary_fingerprint_change_is_a_warning_and_reports_are_never_overwritten():
    with tmpdir() as d, FakeOpenAI("recorded", fingerprint="fp_test_2") as f, env(LLM_BASE_URL=f.url, GLEICHLAUT_STATE=d):
        fake_cert(d, f.url, fps=("fp_test_1",))
        for _ in range(2):
            rc, out, _ = run_cli("certify", "--canary", "5")
            assert rc == 0 and "WARNING: system_fingerprint changed" in out, out
        R = [r for _, r in certify.canary_reports()]
        assert len(R) == 2 and len({r["name"] for r in R}) == 2
        assert all(r["fingerprint_changed"] and r["certificate"] == "c" and r["system_fingerprints"] == ["fp_test_2"] for r in R)


def test_canary_default_is_documented_consistently():
    assert certify.CANARY_N == 40 and "CANARY_N ?= 40" in open(os.path.join(core.ROOT, "Makefile"), encoding="utf-8").read()
    for doc in ("operations.md", "target-architecture.md"):
        t = open(os.path.join(core.ROOT, "docs", doc), encoding="utf-8").read()
        assert "--canary 5`" not in t and "5-item canary" not in t, doc


# ------------------------------------------------------------------ round 2: timeouts, proxy, CA
def test_timeout_defaults_and_a_dead_endpoint_fails_within_the_deadline():
    import time
    with env():
        for k in ("GLEICHLAUT_HTTP_RETRIES", "GLEICHLAUT_HTTP_BACKOFF"): os.environ.pop(k, None)
        b = backends.OpenAI(base_url="http://127.0.0.1:9/v1")
        assert (b.timeout, b.retries, b.backoff, b.deadline) == (120.0, 4, 5.0, 300.0)
        assert 4 * 0 + b.deadline + 5 <= 330                                   # worst case per request ~5 min
    with tmpdir() as d, FakeOpenAI("hang") as f:
        items = write_json(os.path.join(d, "i.json"), fresh(3))
        with env(LLM_BASE_URL=f.url, GLEICHLAUT_STATE=d, GLEICHLAUT_TIMEOUT="0.3", GLEICHLAUT_RETRIES="4", GLEICHLAUT_BACKOFF="0"):
            t = time.time(); rc, out, err = run_cli("draft", "--items", items, "--out", os.path.join(d, "a"), "--air-gapped")
            assert rc == 6 and time.time() - t < 5 and "after 4 attempts" in err, (rc, err)
        with env(LLM_BASE_URL=f.url, GLEICHLAUT_STATE=d, GLEICHLAUT_TIMEOUT="120", GLEICHLAUT_RETRIES="4", GLEICHLAUT_DEADLINE="1"):
            t = time.time(); rc, out, err = run_cli("draft", "--items", items, "--out", os.path.join(d, "b"), "--air-gapped")
            assert rc == 6 and time.time() - t < 4 and "GLEICHLAUT_DEADLINE 1" in err, (rc, err)
    with tmpdir() as d, FakeOpenAI("error") as f, env(LLM_BASE_URL=f.url, GLEICHLAUT_STATE=d):
        t = time.time(); rc, out, _ = run_cli("certify", "--workers", "2")
        assert rc == 6 and len(f.requests) <= 4 and time.time() - t < 10, (rc, len(f.requests))   # queued items are cancelled


def test_proxy_and_internal_ca_are_honoured():
    import ssl
    with tmpdir() as d, FakeOpenAI("recorded") as proxy:
        items = write_json(os.path.join(d, "i.json"), fresh(1))
        with env(LLM_BASE_URL="http://llm.internal.example/v1", HTTP_PROXY=proxy.url.rsplit("/v1", 1)[0], GLEICHLAUT_STATE=d):
            rc, out, err = run_cli("draft", "--items", items, "--out", os.path.join(d, "a"), "--air-gapped")
            assert rc == 0 and proxy.requests and proxy.requests[0]["path"] == "http://llm.internal.example/v1/chat/completions", (rc, err)
        with env(LLM_BASE_URL="https://llm.internal.example/v1", SSL_CERT_FILE=os.path.join(d, "missing-ca.pem"), GLEICHLAUT_STATE=d):
            rc, out, err = run_cli("draft", "--items", items, "--out", os.path.join(d, "b"), "--air-gapped")
            assert rc == 2 and "SSL_CERT_FILE" in err, err
    ca = ssl.get_default_verify_paths().cafile or ssl.get_default_verify_paths().openssl_cafile
    if ca and os.path.isfile(ca):
        with env(REQUESTS_CA_BUNDLE=ca):
            assert backends.ca_file() == ca and isinstance(backends.ssl_context(), ssl.SSLContext)
    mk = open(os.path.join(core.ROOT, "Makefile"), encoding="utf-8").read()
    for v in ("HTTPS_PROXY", "HTTP_PROXY", "NO_PROXY", "SSL_CERT_FILE", "REQUESTS_CA_BUNDLE"): assert v in mk, v


# ------------------------------------------------------------------ round 2: routing of long code-lane items
def test_long_numbers_only_change_is_drafted_by_the_code_lane_never_routed_to_a_human():
    pad_de = " Die Behandlung ist nur in Kombination mit einer topischen Therapie zu vergüten und durch einen Facharzt zu verordnen." * 24
    pad_fr = " Le traitement n'est remboursé qu'en association avec un traitement topique et doit être prescrit par un spécialiste." * 24
    x = dict(key="DUPIXENT-long-fr", lang="fr", de_old="Nach 16 Wochen ist der Therapieerfolg zu überprüfen." + pad_de,
             de_new="Nach 24 Wochen ist der Therapieerfolg zu überprüfen." + pad_de,
             tgt_old="Le succès thérapeutique doit être vérifié après 16 semaines." + pad_fr)
    y = dict(x, key="long-needs-model-fr", de_new=x["de_new"].replace("zu überprüfen", "durch den Vertrauensarzt zu überprüfen"))
    with tmpdir() as d, env():
        p = write_json(os.path.join(d, "i.json"), [x, y]); X = cli.load_items(p)
        assert len(x["de_old"]) > cli.MAXCH and cli.code_only(X[0]) and not cli.code_only(X[1])
        assert cli.route(X[0]) == ("draft", None) and cli.route(X[1])[0] == "human"
        rc, out, err = run_cli("draft", "--items", p, "--out", os.path.join(d, "r"), "--backend", "stub")
        assert rc == 0, out + err
        R = {r["key"]: r for r in map(json.loads, open(os.path.join(d, "r", "records.jsonl"), encoding="utf-8"))}
        a = R["DUPIXENT-long-fr"]
        assert a["status"] != "human" and a["rule_only"] and "après 24 semaines" in a["out"] and "route_note" in a
        assert R["long-needs-model-fr"]["status"] == "human"
        calls = os.path.join(d, "r", "calls.jsonl")
        assert not os.path.exists(calls) or not open(calls).read().strip()     # no model call for either


# ------------------------------------------------------------------ round 2: audit pass-through, fake endpoint module
def test_audit_command_passes_argv_through():
    from gleichlaut import audit
    seen = []; real = audit.main; audit.main = lambda argv=None: seen.append(argv) or 0
    try:
        assert run_cli("audit", "--date", "20261006", "--hist", "/x", "--anything")[0] == 0
    finally: audit.main = real
    assert seen == [["--date", "20261006", "--hist", "/x", "--anything"]]
    mk = open(os.path.join(core.ROOT, "Makefile"), encoding="utf-8").read()
    assert "\naudit:" in mk and "gleichlaut audit" in mk


def test_fake_endpoint_runs_standalone():
    import subprocess, time
    env_ = dict(os.environ, PYTHONPATH=os.path.join(core.ROOT, "src"))
    pr = subprocess.Popen([sys.executable, "-m", "gleichlaut.fake_endpoint", "--port", "0", "--mode", "non-apertus", "--quiet"],
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env_)
    try:
        line = pr.stdout.readline(); url = line.split("LLM_BASE_URL=")[1].strip()
        with env(LLM_BASE_URL=url):
            b = backends.OpenAI()
            try: b("x\nFrench (old): a\n\nOutput only", "t", 1.0, 10); raise AssertionError("non-Apertus answer accepted")
            except backends.EndpointError as e: assert "not an Apertus model" in str(e)
    finally:
        pr.terminate(); pr.wait(5)


# ------------------------------------------------------------------ round 2: feeds, --to latest, --from previous
def _fake_bag(published, latest):
    calls = []

    class BAG(BaseHTTPRequestHandler):
        def log_message(self, *a): pass
        def _file(self):
            import re as _re
            m = _re.search(r"-(\d{8})-de\.ndjson$", self.path)
            return m and m.group(1) in published
        def do_HEAD(self):
            calls.append(("HEAD", self.path, self.headers.get("User-Agent")))
            self.send_response(200 if self._file() else 404); self.send_header("Content-Length", "123"); self.end_headers()
        def do_GET(self):
            calls.append(("GET", self.path, self.headers.get("User-Agent")))
            if self.path.endswith("/resources/current"):
                b = json.dumps({"fhir": {"fileUrl": f"sl/publication/fhir/foph-sl-publication-{latest}-de.ndjson",
                                         "lastUpdated": f"{latest[:4]}-{latest[4:6]}-{latest[6:]}"}}).encode()
                self.send_response(200); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
            else:
                self.send_response(404); self.end_headers()
    srv = ThreadingHTTPServer(("127.0.0.1", 0), BAG); threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, calls


def test_feeds_listing_and_month_latest_previous():
    from gleichlaut.sl import feeds
    assert ingest.MIN_INTERVAL >= 1.0                                         # <= 1 request per second to BAG
    srv, calls = _fake_bag({"20260801", "20260901", "20261001", "20261006"}, "20261006")
    base = f"http://127.0.0.1:{srv.server_address[1]}"
    old = (ingest.BASE, feeds.API, ingest.MIN_INTERVAL, cli.OUT)
    ingest.BASE, feeds.API, ingest.MIN_INTERVAL = base + "/static", base + "/api/sl/public/resources/current", 0.0
    try:
        with tmpdir() as d, env():
            cli.OUT = os.path.join(d, "out")
            L = feeds.listing(d, months=3)
            assert L["latest"] == "20261006" and {"20260901", "20261001", "20261006"} <= set(L["published"]), L
            assert all(ua == ingest.UA for _, _, ua in calls) and any(m == "HEAD" for m, _, _ in calls)
            n = len(calls); feeds.listing(d, months=3)
            assert len(calls) == n + 1                                         # published dates are not probed again
            rc, out, err = run_cli("feeds", "--snapshots", d, "--months", "3")
            assert rc == 0 and "20261006" in out and "latest" in out, out + err
            assert feeds.resolve_latest(d)[0] == "20261006"
            assert feeds.resolve_previous("20261006", d, os.path.join(cli.OUT, "month"))[0] == "20261001"
            with contextlib.redirect_stderr(io.StringIO()): _snapshots(d, "20261001", "20261006")
            rc, out, err = run_cli("month", "--from", "previous", "--to", "latest", "--snapshots", d, "--backend", "stub")
            assert rc == 0 and "--to latest = 20261006" in out and "--from previous = 20261001" in out, out + err
            assert os.path.exists(os.path.join(cli.OUT, "month", "20261001-20261006", "summary.json"))
            prev = feeds.resolve_previous("20261101", d, os.path.join(cli.OUT, "month"))
            assert prev[0] == "20261006" and "last completed month run" in prev[1]   # consecutive runs leave no gap
    finally:
        ingest.BASE, feeds.API, ingest.MIN_INTERVAL, cli.OUT = old; srv.shutdown(); srv.server_close()


# ------------------------------------------------------------------ round 2: ePL bridge
def _ndjson(path, rows, i):
    lines = [_bundle("M1", "Foo Tabl", [("FOO.01", rows[0][i]), ("BAZ.01", rows[2][i])]), _bundle("M2", "Bar Inj", [("BAR.01", rows[1][i])])]
    with open(path, "w", encoding="utf-8") as f: f.write("\n".join(lines) + "\n")
    return path


def test_items_from_fhir_exports_shadow_draft_bundle_and_translations():
    with tmpdir() as d, env():
        for lang, rows in SNAP.items():
            _ndjson(os.path.join(d, f"foph-sl-publication-20261001-{lang}.ndjson"), rows, 0)
            _ndjson(os.path.join(d, f"foph-sl-publication-20261101-{lang}.ndjson"), rows, 1)
        old, new = (os.path.join(d, f"foph-sl-publication-{x}-de.ndjson") for x in ("20261001", "20261101"))
        out = os.path.join(d, "items.json")
        rc, o, e = run_cli("items", "--from-fhir", old, new, "--out", out)
        assert rc == 0 and "shadow" in o, o + e
        I = {x["key"]: x for x in json.load(open(out, encoding="utf-8"))}
        assert len(I) == 4 and any("tgt_new" in x for x in I.values()) and all(x["snap_old"] == "20261001" for x in I.values())
        # pre-publication: one draft Bundle (a Bundle of product Bundles) in which only the German changed
        draft = {"resourceType": "Bundle", "type": "collection", "entry": [{"resource": json.loads(l)} for l in
                 open(new, encoding="utf-8").read().splitlines() if l.strip()]}
        dp = write_json(os.path.join(d, "draft.json"), draft)
        out2 = os.path.join(d, "pre.json")
        rc, o, e = run_cli("items", "--from-fhir", old, dp, "--out", out2, "--lang", "fr")
        assert rc == 0 and "pre-publication" in o, o + e
        P = json.load(open(out2, encoding="utf-8"))
        assert len(P) == 2 and all(x["lang"] == "fr" and "tgt_new" not in x and x["tgt_published"] == "absent" for x in P)
        assert {x["key"] for x in P} <= set(I)                                  # same change, same keys as the shadow run
        # one multilingual export: FR/IT as FHIR translation extensions of the German text
        def multi(i):
            T = "http://hl7.org/fhir/StructureDefinition/translation"
            out = []
            for m, name, ids in (("M1", "Foo Tabl", (0, 2)), ("M2", "Bar Inj", (1,))):
                e = [{"resource": {"resourceType": "MedicinalProductDefinition", "id": m, "name": [{"productName": name}]}}]
                for j in ids:
                    k = ["FOO.01", "BAR.01", "BAZ.01"][j]
                    c = {"text": SNAP["de"][j][i], "_text": {"extension": [
                        {"url": T, "extension": [{"url": "lang", "valueCode": f"{L}-CH"}, {"url": "content", "valueString": SNAP[L][j][i]}]}
                        for L in ("fr", "it")]}}
                    e.append({"resource": {"resourceType": "ClinicalUseDefinition", "id": k, "indication": {"diseaseSymptomProcedure": {"concept": c}}}})
                out.append(json.dumps({"resourceType": "Bundle", "entry": e}, ensure_ascii=False))
            return "\n".join(out) + "\n"
        for nm, i in (("old.ndjson", 0), ("new.ndjson", 1)):
            with open(os.path.join(d, nm), "w", encoding="utf-8") as f: f.write(multi(i))
        out3 = os.path.join(d, "multi.json")
        rc, o, e = run_cli("items", "--from-fhir", os.path.join(d, "old.ndjson"), os.path.join(d, "new.ndjson"), "--out", out3)
        assert rc == 0, o + e
        M = {x["key"]: x for x in json.load(open(out3, encoding="utf-8"))}
        assert set(M) == set(I) and all(M[k]["tgt_old"] == I[k]["tgt_old"] for k in M)
        rc, o, e = run_cli("draft", "--items", out2, "--out", os.path.join(d, "r"), "--backend", "stub")
        assert rc == 0, o + e
        rc, o, e = run_cli("items", "--from-fhir", os.path.join(d, "nope.ndjson"), new, "--out", out)
        assert rc == 2 and "not found" in e
