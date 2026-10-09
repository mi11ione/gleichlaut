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
       "GLEICHLAUT_GATEWAY_DIR", "SKIP_MODEL", "GLEICHLAUT_GGUF", "GLEICHLAUT_HIST", "GLEICHLAUT_DEBUG")


@contextlib.contextmanager
def env(**kw):
    old = {k: os.environ.get(k) for k in ENV}
    for k in ENV: os.environ.pop(k, None)
    os.environ.update(GLEICHLAUT_HTTP_RETRIES="1", GLEICHLAUT_HTTP_BACKOFF="0")
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


def fake_cert(state, endpoint, model=M70, status="PASS", kind="endpoint", date="2026-10-09T10:00:00+00:00", name="c"):
    os.makedirs(os.path.join(state, "certificates"), exist_ok=True)
    c = dict(name=name, kind=kind, date=date, endpoint=backends.endpoint_id(endpoint), model_requested=model, status=status,
             models_served=[model], freeze_sha256=core.sha256(core.FREEZE),
             suite=dict(sha256=core.sha256(os.path.join(core.ROOT, "data", certify.ITEMS))))
    return write_json(os.path.join(state, "certificates", f"{name}.json"), c)


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
        fake_cert(d, f.url, status="FAIL", date="2026-10-10T10:00:00+00:00", name="later")
        assert certify.certified(f.url, M70) is None                        # the newest certificate decides


def test_certify_against_fake_endpoint_then_gate_and_canary():
    """the full suite (285 requests) against the fake serving the recorded answers reproduces the PASS; the certificate
    names the endpoint, never the key; draft is then allowed; the canary passes, and fails on a model that drifts."""
    with tmpdir() as d, FakeOpenAI("recorded") as f, env(LLM_BASE_URL=f.url, LLM_API_KEY="sk-secret-test-key", GLEICHLAUT_STATE=d):
        rc, out, err = run_cli("certify", "--workers", "4")
        assert rc == 0, out + err
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
            rc, out, err = run_cli("draft", "--items", items, "--out", os.path.join(o, "r"))
            assert rc == 0 and "certification gate" in out, out + err


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
