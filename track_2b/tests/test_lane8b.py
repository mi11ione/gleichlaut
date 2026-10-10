"""The 8B default lane and the third operations pass: build certificates (import, gate, tamper evidence), the default
backend, llama-cpp-python missing, --prompt-domain, custom check resources, the library API, audit --fail-on-findings,
Prometheus textfile metrics, supply chain (hash-pinned locks, SBOM), packaging, deploy manifests and the shadow workflow.
No model is called: the local 8B is replaced by a stand-in that answers from the recorded responses."""
import contextlib, glob, hashlib, io, json, os, re, shutil, sys, tempfile, unittest
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(H, "..", "src")); sys.path.insert(0, H)
from test_ops import env, tmpdir, run_cli, fresh, write_json
from gleichlaut import api, backends, certify, cli, core, resources, score

ROOT = core.ROOT
SHIPPED = os.path.join(certify.EVIDENCE, certify.BUILD_NAME + ".json")
M1 = os.path.join(ROOT, certify.M1_RUN); M1L = os.path.join(ROOT, certify.M1_LABELS)


def read(rel): return open(os.path.join(ROOT, rel), encoding="utf-8").read()


class FakeLlama:
    """stands in for backends.LlamaCpp: hashes the GGUF like the real one, answers from the recorded responses (the SL
    prompts do not depend on the model), never loads llama.cpp."""
    runtime = "0.3.35"

    def __init__(self, path, lop, n_ctx=8192, n_threads=None, log=None, gguf_sha256=None):
        self.path, self.log, self._sha = path, log, gguf_sha256
        self.cache = backends.Cache(os.path.join(ROOT, "data", "cache", "responses"))
        self.model, self.endpoint, self.n_threads, self.calls = "gguf:" + os.path.basename(path), "local llama.cpp (in process)", 4, 0

    @property
    def gguf_sha256(self):
        if self._sha is None: self._sha = backends.file_sha256(self.path)
        return self._sha

    def __call__(self, prompt, tag, cap, max_tokens):
        self.calls += 1
        return self.cache(prompt, tag, cap, max_tokens)


@contextlib.contextmanager
def fake_llama(installed=True):
    saved = (backends.LlamaCpp, backends.require_llama, backends.llama_version)
    backends.LlamaCpp = FakeLlama
    backends.require_llama = (lambda: None) if installed else saved[1]
    backends.llama_version = (lambda: "0.3.35") if installed else (lambda: None)
    try: yield
    finally: backends.LlamaCpp, backends.require_llama, backends.llama_version = saved


def gguf(d, content=b"not really a GGUF, only its sha256 matters here"):
    os.makedirs(os.path.join(d, "models"), exist_ok=True)
    p = os.path.join(d, "models", "apertus-test.gguf")
    with open(p, "wb") as f: f.write(content)
    return p, hashlib.sha256(content).hexdigest()


# ------------------------------------------------------------------ build certificates
def test_shipped_build_certificate_verifies_and_reproduces_m1():
    c = json.load(open(SHIPPED, encoding="utf-8"))
    assert c["kind"] == "build" and c["status"] == "PASS" and c["files_base"] == "root"
    assert c["gguf"]["sha256"] == certify.GGUF_SHA_Q4 == cli.GGUF_SHA and c["runtime"]["llama_cpp_python"] == "0.3.35"
    assert c["freeze_sha256"] == core.sha256(core.FREEZE)
    m1 = json.load(open(os.path.join(ROOT, "eval", "results", "m1_q4_k_m.json"), encoding="utf-8"))
    for k in ("exact", "ef1", "chrf", "flag_rate", "ready_rate", "unflagged", "unflagged_REAL", "unflagged_stale", "unflagged_german", "pass_rule"):
        assert c["metrics"][k] == m1[k], k
    assert "0.3.35" in read("requirements-offline.txt") and certify.pinned_llama() == "0.3.35"
    with tmpdir() as d, env(GLEICHLAUT_STATE=d):
        cert, why = certify.build_lookup(certify.GGUF_SHA_Q4, "0.3.35")
        assert cert and cert["name"] == certify.BUILD_NAME, why
        assert certify.build_lookup(certify.GGUF_SHA_Q4, "0.3.36")[0] is None                 # another llama-cpp-python
        assert "no build certificate" in certify.build_lookup("0" * 64)[1]
        assert certify.certified("recorded responses (data/cache)", core.M70) is None           # never an endpoint certificate


def test_shipped_q8_0_build_certificate_verifies_and_reproduces_m2():
    c = json.load(open(os.path.join(ROOT, "eval", "certificates", "8b-q8_0-fresh166.json"), encoding="utf-8"))
    assert c["kind"] == "build" and c["status"] == "PASS" and c["gguf"]["sha256"] == certify.GGUF_SHA_Q8 == cli.BUILDS["q8_0"][1]
    m2 = json.load(open(os.path.join(ROOT, "eval", "results", "m1_q8_0.json"), encoding="utf-8"))
    for k in ("exact", "flag_rate", "ready_rate", "unflagged", "unflagged_REAL", "unflagged_stale", "unflagged_german", "pass_rule"):
        assert c["metrics"][k] == m2[k], k
    with tmpdir() as d, env(GLEICHLAUT_STATE=d):
        cert, why = certify.build_lookup(certify.GGUF_SHA_Q8, "0.3.35")
        assert cert and cert["name"] == "8b-q8_0-fresh166", why


def _copy_shipped(d, **edit):
    """the shipped certificate copied into state/certificates, optionally edited by hand."""
    os.makedirs(os.path.join(d, "certificates"), exist_ok=True)
    c = json.load(open(SHIPPED, encoding="utf-8")); c.update(edit); c["name"] = "copy"; c["date"] = "2099-01-01T00:00:00+00:00"
    certify._write_json(os.path.join(d, "certificates", "copy.json"), c)
    return c


def test_build_certificate_is_tamper_evident():
    certify._VERIFIED.clear()
    with tmpdir() as d, env(GLEICHLAUT_STATE=d):
        m = json.loads(json.dumps(json.load(open(SHIPPED, encoding="utf-8"))["metrics"])); m["exact"]["delta"] = 20.0
        _copy_shipped(d, metrics=m)                                     # newer, edited: it decides, and it fails
        assert "metrics in the certificate differ" in certify.build_lookup(certify.GGUF_SHA_Q4, "0.3.35")[1]
        _copy_shipped(d, status="FAIL")                                 # a newer FAIL revokes the shipped PASS
        assert "has status FAIL" in certify.build_lookup(certify.GGUF_SHA_Q4, "0.3.35")[1]
        _copy_shipped(d, run_records_sha256="0" * 64)
        assert "does not match the sha256" in certify.build_lookup(certify.GGUF_SHA_Q4, "0.3.35")[1]
        _copy_shipped(d, freeze_sha256="0" * 64)
        assert "other frozen code" in certify.build_lookup(certify.GGUF_SHA_Q4, "0.3.35")[1]
    with tmpdir() as d:                                                  # records that do not pass the rule
        R = [json.loads(l) for l in open(M1, encoding="utf-8")]
        lab = [l for l in open(M1L, encoding="utf-8")]
        bad = os.path.join(d, "bad.tsv")
        with open(bad, "w", encoding="utf-8") as f:                      # relabel two ready drafts as meaning errors
            f.write(lab[0]); n = 0
            for l in lab[1:]:
                c = l.rstrip("\n").split("\t"); k = c[0]
                r = next(r for r in R if r["key"] == k)
                if not r["guard_flag"] and n < 3 and c[8] not in ("exact",): c[8] = "REAL"; n += 1
                f.write("\t".join(c) + "\n")
        with env(GLEICHLAUT_STATE=d):
            p, c = certify.import_run(M1, certify.GGUF_SHA_Q4, bad, name="bad")
            assert c["status"] == "FAIL" and not c["metrics"]["pass_rule"]["unflagged_real"][1]


def test_import_run_cli_and_hmac():
    with tmpdir() as d, env(GLEICHLAUT_STATE=d):
        args = ("certify", "--import-run", M1, "--gguf-sha256", certify.GGUF_SHA_Q4, "--labels", M1L)
        rc, out, err = run_cli(*args)
        assert rc == 0 and "kind build  status PASS" in out and "exact +10.8 pts" in out, out + err
        C = [c for _, c in certify.build_certificates() if c.get("files_base") == "state"]
        assert len(C) == 1 and os.path.exists(os.path.join(d, C[0]["run_records"]))     # copied into state, not referenced
        assert run_cli("certify", "--import-run", M1, "--gguf-sha256", "xyz", "--labels", M1L)[0] == 2
        key = os.path.join(d, "k.key")
        with open(key, "wb") as f: f.write(b"0123456789abcdef0123456789abcdef")
        with env(GLEICHLAUT_STATE=d, GLEICHLAUT_CERT_KEY=key):
            for p in glob.glob(os.path.join(d, "certificates", "*.json")): os.remove(p)
            certify._VERIFIED.clear()
            assert "unsigned" in certify.build_lookup(certify.GGUF_SHA_Q4, "0.3.35")[1]   # the shipped one is unsigned
            assert run_cli(*args)[0] == 0                                                    # make certify: a signed copy
            c, why = certify.build_lookup(certify.GGUF_SHA_Q4, "0.3.35")
            assert c and "HMAC ok" in why and c["hmac_sha256"], why


def test_certify_llamacpp_without_llama_cpp_is_one_line():
    if backends.llama_version(): raise unittest.SkipTest("llama-cpp-python is installed here")
    with tmpdir() as d, env(GLEICHLAUT_STATE=d):
        p, _ = gguf(d)
        rc, out, err = run_cli("certify", "--backend", "llamacpp", "--gguf", p)
        assert rc == 2 and "make month-offline" in out and "Traceback" not in out + err, out + err


# ------------------------------------------------------------------ the gate in draft / month
def test_certified_local_8b_drafts_get_guard_status_and_uncertified_ones_go_to_review():
    I = fresh(6)
    with tmpdir() as d, fake_llama(), env(GLEICHLAUT_STATE=os.path.join(d, "state"), GLEICHLAUT_MODELS=os.path.join(d, "models")):
        p, sha = gguf(d)
        items = write_json(os.path.join(d, "i.json"), I)
        rc, out, err = run_cli("draft", "--items", items, "--out", os.path.join(d, "u"))      # no certificate for this file
        assert rc == 2 and "no drafting backend" in err, err                                  # default: no certified GGUF
        rc, out, err = run_cli("draft", "--items", items, "--out", os.path.join(d, "u"), "--backend", "llamacpp")
        assert rc == 0 and "uncertified model build" in out, out + err
        R = [json.loads(l) for l in open(os.path.join(d, "u", "records.jsonl"), encoding="utf-8")]
        assert all(r["status"] != "ready" and r["review_reason"].startswith("SL lane on a local") for r in R if r["status"] != "human")
        certify.import_run(M1, sha, M1L, name="test-build")                                   # certify this file (stand-in)
        rc, out, err = run_cli("draft", "--items", items, "--out", os.path.join(d, "c"))      # default backend: llamacpp
        assert rc == 0 and "backend: llamacpp (default)" in out and "certification gate: build certificate test-build" in out, out + err
        R = {r["key"]: r for r in map(json.loads, open(os.path.join(d, "c", "records.jsonl"), encoding="utf-8"))}
        assert all("review_reason" not in r for r in R.values())
        assert all(r["status"] == r["guard_status"] for r in R.values() if r["status"] != "human")
        F = score.load_jsonl(score.RUNS["fresh166"]["final"])
        assert all(r["out"] == F[k]["out"] for k, r in R.items() if r["status"] != "human")   # the pipeline is unchanged
        s = json.load(open(os.path.join(d, "c", "summary.json"), encoding="utf-8"))
        assert s["gate"]["kind"] == "build" and s["gate"]["gguf_sha256"] == sha and s["backend"]["name"] == "llamacpp"
        assert s["shadow"]["compared"] >= 1 and "exact_rate" in s["shadow"] and "flag_rate" in s["shadow"]
        rc, out, _ = run_cli("draft", "--items", items, "--out", os.path.join(d, "x"), "--dry-run")
        assert rc == 0 and "build certificate gate: would PASS" in out, out
        with env(GLEICHLAUT_STATE=os.path.join(d, "state"), GLEICHLAUT_MODELS=os.path.join(d, "models"), LLM_BASE_URL="http://127.0.0.1:9/v1"):
            rc, out, _ = run_cli("draft", "--items", items, "--out", os.path.join(d, "y"), "--dry-run")
            assert "backend: llamacpp (default)" in out                                        # the certified 8B wins over the endpoint
        with open(p, "ab") as f: f.write(b"x")                                                 # another file: no certificate
        rc, out, _ = run_cli("draft", "--items", items, "--out", os.path.join(d, "z"), "--backend", "llamacpp", "--dry-run")
        assert "no valid certificate, every item would go to review" in out, out


def test_llamacpp_without_llama_cpp_python_is_one_line_with_the_fix():
    if backends.llama_version(): raise unittest.SkipTest("llama-cpp-python is installed here")
    with tmpdir() as d, env(GLEICHLAUT_MODELS=os.path.join(d, "models")):
        p, _ = gguf(d); items = write_json(os.path.join(d, "i.json"), fresh(1))
        rc, out, err = run_cli("draft", "--items", items, "--out", os.path.join(d, "r"), "--backend", "llamacpp")
        assert rc == 2 and err.startswith("error: llama-cpp-python is not installed") and "make month-offline" in err, err
        assert "Traceback" not in err and len(err.strip().splitlines()) == 1
        rc, out, err = run_cli("month", "--items", items, "--out", os.path.join(d, "m"), "--backend", "llamacpp")
        assert rc == 2 and "make month-offline" in err, err


def test_prompt_domain_rewrites_only_the_first_sentence_and_reviews_everything():
    x = fresh(1)[0]; seen = []
    a = backends.DomainAsk(lambda p, t, c, m: (seen.append(p), ("", {}))[1], "paragraph of a cantonal ordinance")
    P = core.Pipeline(a, "g3")
    try: P.draft(x)
    except Exception: pass
    assert seen and seen[0].startswith("A paragraph of a cantonal ordinance was amended in German. Apply exactly")
    assert "Spezialitätenliste, BAG" not in seen[0].split("\n")[0] and P.PA.startswith(backends.DomainAsk.FIRST)
    d = api.dry_run(x, prompt_domain="An article of a federal ordinance was amended in German.")
    assert d["prompt"] is None or d["prompt"].startswith("An article of a federal ordinance was amended in German.")
    with tmpdir() as t, env():
        items = write_json(os.path.join(t, "i.json"), fresh(3))
        rc, out, err = run_cli("draft", "--items", items, "--out", os.path.join(t, "r"), "--backend", "stub", "--prompt-domain", "ordinance text")
        assert rc == 0, out + err
        R = [json.loads(l) for l in open(os.path.join(t, "r", "records.jsonl"), encoding="utf-8")]
        assert all(r["status"] != "ready" for r in R)
        rc, out, err = run_cli("draft", "--items", items, "--out", os.path.join(t, "q"), "--backend", "stub", "--corpus", "fedlex", "--prompt-domain", "x")
        assert rc == 2 and "statute lane" in err, err


# ------------------------------------------------------------------ custom resources
def test_resources_build_ports_the_frozen_rules_and_voids_certificates():
    rows = [{"de": "Meldung an das BAG, Behandlung im SNC.", "fr": "Annonce à l'OFSP, traitement au CNS.",
             "it": "Notifica all'UFSP, trattamento nel CNS.", "names_fr": ["Dupixent Fertigspritze"]},
            {"de": "Nur durch das SNC, Meldung an das BAG.", "fr": "Uniquement par le CNS, annonce à l'OFSP.", "it": "Solo tramite CNS, notifica all'UFSP."},
            {"de": "Ein Text ohne <b>Abkürzung</b>.", "fr": "Un texte <b>sans</b> abréviation.<br>Fin."}]
    with tmpdir() as d:
        corpus = os.path.join(d, "c.jsonl")
        with open(corpus, "w", encoding="utf-8") as f: f.write("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n")
        out = os.path.join(d, "res")
        rc, o, e = run_cli("resources", "build", "--corpus", corpus, "--out", out)
        assert rc == 0, o + e
        terms = json.load(open(os.path.join(out, "terms_fr.json"), encoding="utf-8"))
        vocab = json.load(open(os.path.join(out, "vocab_fr.json"), encoding="utf-8"))
        assert terms == {"BAG": "OFSP", "SNC": "CNS"}, terms                # paired in order, seen twice, A != B
        assert vocab["texte"] == 1 and vocab["annonce"] == 2 and "b" not in vocab  # tags removed, per-text counts
        assert json.load(open(os.path.join(out, "whitelist_fr.json"))) == ["dupixent", "fertigspritze"]
        assert not os.path.exists(os.path.join(out, "whitelist_it.json"))  # no Italian names: the frozen whitelist stays
        assert json.load(open(os.path.join(out, "manifest.json")))["certified"] is False
        bad = os.path.join(d, "bad.jsonl")
        with open(bad, "w") as f: f.write("{nope\n")
        assert run_cli("resources", "build", "--corpus", bad, "--out", out)[0] == 2
        g = core.guards3; frozen = (g.WL, g.VOC, g.TERMS)
        try:
            with env(GLEICHLAUT_RESOURCES=out):
                assert sorted(resources.apply()) == ["terms_fr.json", "terms_it.json", "vocab_fr.json", "vocab_it.json", "whitelist_fr.json"]
                assert g.TERMS["fr"] == terms and g.WL["it"] is not None and resources.active()
                certify._VERIFIED.clear()
                assert "custom check resources" in certify.build_lookup(certify.GGUF_SHA_Q4, "0.3.35")[1]
                assert api.verdict(fresh(1)[0], fresh(1)[0]["tgt_new"])["certified"] is False
                items = write_json(os.path.join(d, "i.json"), fresh(2))
                rc, o, e = run_cli("draft", "--items", items, "--out", os.path.join(d, "r"), "--backend", "stub")
                assert rc == 0 and "UNCERTIFIED" not in e and "custom check resources" in o, o + e
        finally:
            os.environ.pop("GLEICHLAUT_RESOURCES", None); resources.apply(); api._RES["done"] = False; certify._VERIFIED.clear()
        assert (g.WL, g.VOC, g.TERMS) == frozen and resources.active() is None
        assert certify.build_lookup(certify.GGUF_SHA_Q4, "0.3.35")[0]


# ------------------------------------------------------------------ library API
def test_api_check_agrees_with_the_frozen_verdict_and_speaks_the_items_language():
    I = {x["key"]: x for x in score.load_items("items/items_fresh.json")}; F = score.load_jsonl(score.RUNS["fresh166"]["final"])
    for k in list(I)[:40]:
        cs = api.check(I[k], F[k]["out"])
        assert [c["check"] for c in cs][:9] == ["lock", "slot", "g1", "g2", "g3", "g4", "g5", "g6", "g7"]
        assert any(c["severity"] == "flag" for c in cs) == F[k]["guard_flag"], k
        assert all(set(c) == {"check", "name", "ok", "severity", "sentence", "detail"} and c["sentence"] for c in cs)
    x = next(x for x in I.values() if x["lang"] == "it")
    assert "Controllo" in api.check(x, x["tgt_new"])[0]["sentence"]
    x = I["wb079-fr"]
    v = api.verdict(x, x["tgt_old"])
    assert v["status"] == "flagged" and next(c for c in v["checks"] if c["check"] == "slot")["sentence"].startswith("Les nombres")
    assert api.verdict(x, x["tgt_new"])["status"] == "ready"
    d = api.dry_run(x)
    assert d["route"] == "draft" and not d["model_call"] and d["code_output"] == x["tgt_new"]
    d = api.dry_run(I["wb010-fr"])
    assert d["model_call"] and "⟨A⟩" in d["prompt"] and d["slots"]
    assert isinstance(api.audit_item(x), list)
    for bad in ({"lang": "de", "de_old": "", "de_new": "", "tgt_old": ""}, {"lang": "fr"}):
        try: api.check(bad, ""); raise AssertionError("bad item accepted")
        except ValueError: pass


# ------------------------------------------------------------------ monitoring
def test_audit_fail_on_findings_and_metrics_textfile():
    from gleichlaut import audit
    real = audit.main
    def fake(argv=None):
        ap = __import__("argparse").ArgumentParser(); ap.add_argument("--date"); ap.add_argument("--out"); ap.add_argument("--hist")
        ap.add_argument("--fail-on-findings", action="store_true")              # the audit module's own flag: exit 1
        a = ap.parse_args(argv); os.makedirs(a.out, exist_ok=True)
        json.dump(dict(by_kind=dict(number=2, unit=0, language=1, editorial=5, terminology=0), limitations_with_any_finding=7,
                       n_limitations=1688), open(os.path.join(a.out, f"audit_{a.date}_summary.json"), "w"))
        return 1 if a.fail_on_findings else 0
    audit.main = fake
    try:
        with tmpdir() as d, env():
            base = ("audit", "--date", "20261006", "--out", d, "--hist", d)
            assert run_cli(*base)[0] == 0
            rc, out, err = run_cli(*base, "--fail-on-findings")                    # passed through; its exit 1 -> 8
            assert rc == 8 and "not marked likely equivalent" in err, err
            rc, out, err = run_cli(*base, "--fail-on-findings=number,unit,language,editorial,terminology")
            assert rc == 8 and "8 finding(s)" in err, err
            assert run_cli(*base, "--fail-on-findings=unit")[0] == 0
            assert run_cli(*base, "--fail-on-findings=language,unit")[0] == 8
            assert run_cli(*base, "--fail-on-findings=bogus")[0] == 2
            m = os.path.join(d, "m", "audit.prom")
            assert run_cli(*base, "--fail-on-findings", "--metrics-file", m)[0] == 8
            t = open(m).read()
            assert 'gleichlaut_last_run_exit_code{job="audit"} 8' in t and 'gleichlaut_audit_findings{job="audit",kind="editorial"} 5' in t
            assert "# TYPE gleichlaut_last_run_duration_seconds gauge" in t and not glob.glob(os.path.join(d, "m", ".*tmp"))
    finally: audit.main = real
    with tmpdir() as d, env(GLEICHLAUT_METRICS_DIR=os.path.join(d, "metrics")):
        items = write_json(os.path.join(d, "i.json"), fresh(3))
        assert run_cli("draft", "--items", items, "--out", os.path.join(d, "r"), "--backend", "stub")[0] == 0
        t = open(os.path.join(d, "metrics", "gleichlaut_draft.prom")).read()
        assert 'gleichlaut_last_run_success{job="draft"} 1' in t and 'gleichlaut_items_total{job="draft"} 3' in t
        assert 'gleichlaut_shadow_rate_percent{job="draft",what="exact_rate"}' in t
        assert run_cli("draft", "--items", os.path.join(d, "missing.json"), "--out", d, "--backend", "stub")[0] == 2
        assert 'gleichlaut_last_run_exit_code{job="draft"} 2' in open(os.path.join(d, "metrics", "gleichlaut_draft.prom")).read()


# ------------------------------------------------------------------ supply chain, packaging, docs, deploy, workflows
def test_requirements_are_hash_pinned_and_the_sbom_is_current():
    from importlib import util
    for f in ("requirements.txt", "requirements-offline.txt"):
        t = read(f).replace("\\\n", " ")
        reqs = [l for l in t.splitlines() if l.strip() and not l.startswith("#")]
        assert reqs and all(re.match(r"[a-z0-9_.-]+==\S+ ", l) and "--hash=sha256:" in l for l in reqs), f
    assert "pip install --require-hashes -r /tmp/requirements.txt" in read("Dockerfile")
    assert "pip install --require-hashes -r /app/requirements-offline.txt" in read("Dockerfile")
    spec = util.spec_from_file_location("supply_chain", os.path.join(ROOT, "tools", "supply_chain.py"))
    sc = util.module_from_spec(spec); spec.loader.exec_module(sc)
    assert sc.sbom() == read("docs/sbom.json"), "docs/sbom.json is stale: python3 tools/supply_chain.py sbom"
    b = json.loads(read("docs/sbom.json"))
    names = {c["name"]: c for c in b["components"]}
    assert b["bomFormat"] == "CycloneDX" and names["lxml"]["version"] == "6.0.2"
    assert names["apertus-v1.5-8b-text-q4_k_m.gguf"]["hashes"][0]["content"] == cli.GGUF_SHA
    assert sc.base_image()[1].split(":")[1] in json.dumps(names)
    assert "cosign" in read("docs/dependencies.md") and "cosign" in read("docs/operations.md")


def test_pyproject_console_script_and_package_data():
    t = read("pyproject.toml")
    assert 'gleichlaut = "gleichlaut.cli:main"' in t and 'requires-python = ">=3.9"' in t and '"" = "src"' in t
    for pat in ("frozen/g3/*.json", "frozen/s2/*.py", "frozen/gl/*.py", "ui/fonts/*"): assert pat in t, pat
    assert glob.glob(os.path.join(ROOT, "src", "gleichlaut", "frozen", "g3", "*.json"))
    assert os.path.basename(core.ROOT) == "track_2b" or os.path.exists(os.path.join(core.ROOT, "pyproject.toml"))


def test_docs_and_help_say_the_same_about_the_lanes():
    docs = {f: read(f) for f in ("docs/operations.md", "docs/dependencies.md", "docs/target-architecture.md", "docs/deploy/README.md")}
    docs["cli"] = cli.__doc__
    for f, t in docs.items():
        assert re.search(r"8B.{0,80}(default|SL default)|default.{0,120}8B", t, re.S), f
        assert "8 GiB" in t or f == "cli", f
        assert "certified" in t, f
    ops = docs["docs/operations.md"]
    assert "no IT approval" not in ops and "wherever your\nIT already allows Python or Docker" in ops
    assert "153.4 s" in ops and "2.4 h" in ops and "24.5 h" in ops and "1.7 calls per item" in ops
    assert "4 GB RAM" not in ops and "review-only on SL" not in ops and "Air-gapped 8B lane (optional)" not in ops
    assert "SL default lane" not in docs["docs/dependencies.md"].split("Apertus v1.5 70B")[1].split("\n")[0]
    assert "What a self-hosted 70B costs" in docs["docs/target-architecture.md"]
    assert "corpus sl -> 70B on a certified endpoint" not in cli.__doc__ and "8 audit --fail-on-findings" in cli.__doc__
    assert "make month-offline" in backends.LLAMA_MISSING


def test_make_targets_run_the_8b_lane_by_default():
    mk = read("Makefile")
    month = mk.split("\nmonth:\n")[1].split("\n\n")[0]
    assert "--target offline" in month and "--backend llamacpp" in month and "/models" in month and "$(STATE)" in month
    assert "LLM_BASE_URL" not in month.replace("$(ENVS8B)", "")
    m70 = mk.split("\nmonth-70b:\n")[1].split("\n\n")[0]
    assert "--target base" in m70 and "--backend openai" in m70
    cert = mk.split("\ncertify:\n")[1].split("\n\n")[0]
    assert "--import-run data/runs/8b_$(BUILD)_fresh166_g3_final.jsonl" in cert and "--network none" in cert
    assert "\nBUILD    ?= q4_k_m\n" in mk and "SHA_q8_0" in mk
    assert "\ncertify-endpoint:\n" in mk and "\nmonth-offline: month" in mk and "\ncertify-build:\n" in mk
    assert "ENVS8B" in mk and "-e LLM_" not in mk.split("ENVS8B   =")[1].split("\n")[0]


K8S = "docs/deploy/kubernetes"


def k8s_docs():
    """-> [(file, document text)] of every manifest (split on '---' lines; comment-only parts dropped)."""
    out = []
    for f in sorted(glob.glob(os.path.join(ROOT, K8S, "*.yaml"))):
        for d in re.split(r"(?m)^---\s*$", open(f, encoding="utf-8").read()):
            body = "\n".join(l for l in d.splitlines() if l.strip() and not l.lstrip().startswith("#"))
            if body.strip(): out.append((os.path.basename(f), d))
    return out


def test_deploy_manifests_for_the_8b_lane():
    k = read(f"{K8S}/gleichlaut.yaml")
    assert "gleichlaut-offline" in k and "requests: { cpu: \"4\", memory: 8Gi }" in k
    assert "{ name: models, mountPath: /models, readOnly: true }" in k and "--fail-on-findings" in k
    np_ = read(f"{K8S}/networkpolicy.yaml")
    assert "kind: NetworkPolicy" in np_ and "epl.bag.admin.ch" in np_ and "toFQDNs" in np_ and "lane: 70b" in np_
    cj = read(f"{K8S}/certify-job.yaml")
    assert "--import-run" in cj and "--backend, llamacpp" in cj and "--backend, openai" in cj
    assert "--backend, openai" in read(f"{K8S}/gleichlaut-70b.yaml")
    sm = read("docs/deploy/systemd/gleichlaut-month.service")
    assert "--backend llamacpp" in sm and "ReadOnlyPaths=/var/lib/gleichlaut/models" in sm and "MemoryMax=10G" in sm
    assert "--backend openai" in read("docs/deploy/systemd/gleichlaut-month-70b.service")
    assert "8) sev=reviewer" in read("docs/deploy/alert.sh")


def test_models_volume_is_written_once_then_mounted_read_only():
    docs = k8s_docs()
    pvc = [d for f, d in docs if "kind: PersistentVolumeClaim" in d and "name: gleichlaut-models" in d]
    assert len(pvc) == 1 and "accessModes: [ReadWriteOnce]" in pvc[0], "models PVC must be provisionable as RWO"
    assert not any(re.search(r"ReadOnlyMany|ReadWriteMany", d) for f, d in docs if "kind: PersistentVolumeClaim" in d)
    writers = []
    for f, d in docs:
        claims = re.findall(r"persistentVolumeClaim: \{ claimName: gleichlaut-models(, readOnly: true)? \}", d)
        if not claims: continue
        mounts = re.findall(r"\{ name: models, mountPath: /models(, readOnly: true)? \}", d)
        if not all(claims): writers.append(re.search(r"name: (gleichlaut-[a-z0-9-]+)", d).group(1))
        else: assert mounts and all(mounts), (f, "outside the two writers every models mount is read-only")
    assert sorted(writers) == ["gleichlaut-fetch-gguf", "gleichlaut-models-loader"], writers
    loader = read(f"{K8S}/models-loader.yaml")
    assert "kubectl -n gleichlaut cp" in loader and "sha256sum" in loader and "job: models-loader" in loader
    fetch = next(d for f, d in docs if "name: gleichlaut-fetch-gguf" in d and "kind: Job" in d)
    assert "envFrom: [{ configMapRef: { name: gleichlaut-config } }]" in fetch, "fetch Job must get proxy/CA/MODEL_URL"
    assert "{ name: ca, mountPath: /etc/gleichlaut/ca, readOnly: true }" in fetch and "name: gleichlaut-ca, optional: true" in fetch
    assert "# GLEICHLAUT_MODEL_URL:" in read(f"{K8S}/gleichlaut.yaml") and "# GLEICHLAUT_BUILD: q8_0" in read(f"{K8S}/gleichlaut.yaml")
    rd = read("docs/deploy/README.md")
    assert "Operator FAQ" in rd and "dea904ad80cd725ec89962abae464477f5d8114d1f4377514f381f7dc2ed202d" in rd and "kubectl cp" in rd


def _window(sched, deadline):
    """'M H DOM * *' + activeDeadlineSeconds -> (start, end) in minutes from the 1st of a month at 00:00."""
    mi, h, dom = sched.split()[:3]
    start = (int(dom) - 1) * 1440 + int(h) * 60 + int(mi)
    return start, start + int(deadline) // 60


def test_cronjobs_never_overlap_on_the_same_claim():
    jobs = []
    for f, d in k8s_docs():
        if "kind: CronJob" not in d: continue
        name = re.search(r"metadata: \{ name: ([a-z0-9-]+)", d).group(1)
        sched = re.search(r'schedule: "([^"]+)"', d).group(1)
        deadline = re.search(r"activeDeadlineSeconds: (\d+)", d).group(1)
        assert re.search(r"concurrencyPolicy: Forbid", d), name
        jobs.append((name, sched, _window(sched, deadline), set(re.findall(r"claimName: ([a-z0-9-]+)", d))))
    assert {j[0] for j in jobs} >= {"gleichlaut-month", "gleichlaut-month-70b", "gleichlaut-audit"}
    for i, a in enumerate(jobs):
        for b in jobs[i + 1:]:
            if not (a[3] & b[3]): continue
            assert a[1] != b[1], (a[0], b[0], "same schedule on the same claim")
            assert a[2][1] <= b[2][0] or b[2][1] <= a[2][0], (a[0], a[2], b[0], b[2], "windows overlap on", a[3] & b[3])
    t8, t70 = (read(f"docs/deploy/systemd/gleichlaut-month{x}.timer") for x in ("", "-70b"))
    on = lambda t: re.search(r"^OnCalendar=(.+)$", t, re.M).group(1)
    assert on(t8) != on(t70) and "gleichlaut-month.service" in read("docs/deploy/systemd/gleichlaut-month-70b.service")


def test_one_cert_key_secret_digest_images_and_pod_hardening():
    docs = k8s_docs()
    allt = "\n".join(d for f, d in docs)
    secrets = re.findall(r"secret: \{ secretName: ([a-z0-9-]+)(, optional: true)?, items: \[\{ key: cert\.key", allt)
    assert secrets and {s for s, _ in secrets} == {"gleichlaut-cert-key"}, secrets
    assert "key: cert.key" not in re.sub(r"secretName: gleichlaut-cert-key[^\n]*", "", allt), "cert.key outside gleichlaut-cert-key"
    m8 = next(d for f, d in docs if "name: gleichlaut-month," in d)
    assert "\n                - { name: key, mountPath: /var/run/secrets/gleichlaut, readOnly: true }" in m8
    assert "secretName: gleichlaut-cert-key, optional: true" in m8 and "# - name: key" not in m8
    images = re.findall(r"image: (\S+)", allt)
    assert images and all(re.fullmatch(r"registry\.example\.ch/gleichlaut(-offline)?@sha256:CHANGE-ME", i) for i in images), images
    assert allt.count("fsGroup: 10001") == allt.count("fsGroupChangePolicy: OnRootMismatch") > 0
    assert "cosign" in read("docs/operations.md")


def test_networkpolicy_has_a_proxy_variant_and_no_open_egress():
    np_ = read(f"{K8S}/networkpolicy.yaml")
    assert "0.0.0.0/0" not in np_ and "networkpolicy-proxy.yaml" in np_
    px = read(f"{K8S}/networkpolicy-proxy.yaml")
    rules = [d for d in re.split(r"(?m)^---\s*$", px) if "kind: NetworkPolicy" in d]
    assert len(rules) == 3 and "0.0.0.0/0" not in px and "port: 443" not in px
    assert all("policyTypes" in d for d in rules) and "fetch-gguf" in px and "lane: 70b" in px


def test_deploy_yaml_parses():
    """every manifest is valid YAML: PyYAML if installed, else Ruby's Psych; skipped when neither is there."""
    import shutil as sh, subprocess
    files = sorted(glob.glob(os.path.join(ROOT, K8S, "*.yaml")))
    try:
        import yaml
        parse = lambda f: [x for x in yaml.safe_load_all(open(f, encoding="utf-8")) if x is not None]
    except ImportError:
        if not sh.which("ruby"): raise unittest.SkipTest("no YAML parser (PyYAML or ruby)")
        rb = ("require 'yaml'; require 'json'; t = File.read(ARGV[0]); "             # Psych 4 needs aliases: true, Psych 3 has no such keyword
              "d = begin; YAML.load_stream(t, aliases: true); rescue ArgumentError; YAML.load_stream(t); end; puts JSON.generate(d.compact)")
        parse = lambda f: json.loads(subprocess.run(["ruby", "-e", rb, f], capture_output=True, text=True, check=True).stdout)
    kinds = []
    for f in files:
        ds = parse(f)
        assert ds and all(isinstance(d, dict) and d.get("apiVersion") and d.get("kind") for d in ds), f
        for d in ds:
            kinds.append(d["kind"])
            spec = d.get("spec", {})
            pod = (spec.get("jobTemplate", {}).get("spec", {}).get("template", {}).get("spec")
                   or spec.get("template", {}).get("spec") or (spec if d["kind"] == "Pod" else None))
            if pod is None: continue
            vols = {v["name"]: v for v in pod.get("volumes", [])}
            for c in pod.get("initContainers", []) + pod["containers"]:
                for m in c.get("volumeMounts", []):
                    assert m["name"] in vols, (f, m)
                    pvc = vols[m["name"]].get("persistentVolumeClaim")
                    if pvc and pvc["claimName"] == "gleichlaut-models" and pvc.get("readOnly"): assert m.get("readOnly"), (f, m)
            assert pod["securityContext"].get("fsGroupChangePolicy") == "OnRootMismatch", f
    assert kinds.count("CronJob") == 3 and kinds.count("NetworkPolicy") == 7 and "Pod" in kinds


def test_fetch_gguf_resumes_a_partial_download():
    """an interrupted download keeps models/<file>.part; the next fetch asks for the rest (HTTP Range) and appends it;
    a server that ignores Range (200) starts over; 416 on a complete .part keeps it. The sha256 check decides."""
    body = os.urandom(3000) + b"gguf"; sha = hashlib.sha256(body).hexdigest(); seen = []

    class Resp(io.BytesIO):
        def __init__(self, data, status): super().__init__(data); self.status = status

    def server(mode):
        def urlopen(req, timeout):
            rng = req.get_header("Range"); seen.append(rng)
            if mode == "range" and rng:
                return Resp(body[int(rng.split("=")[1].rstrip("-")):], 206)
            if mode == "416" and rng:
                import urllib.error
                raise urllib.error.HTTPError(req.full_url, 416, "Range Not Satisfiable", {}, None)
            return Resp(body, 200)
        return urlopen

    saved = (backends.urlopen, cli.GGUF_URL, cli.GGUF_SHA)
    try:
        cli.GGUF_URL, cli.GGUF_SHA = "https://mirror.example/models/test.gguf", sha
        for mode, part in (("range", body[:1234]), ("ignore", b"x" * 99), ("416", body), ("range", b"")):
            with tmpdir() as d, env(GLEICHLAUT_MODELS=d):
                if part: open(os.path.join(d, "test.gguf.part"), "wb").write(part)
                backends.urlopen = server(mode); seen.clear()
                with contextlib.redirect_stdout(io.StringIO()): p = cli.fetch_gguf()
                assert open(p, "rb").read() == body and not os.path.exists(p + ".part"), mode
                assert seen == ([f"bytes={len(part)}-"] if part else [None]), (mode, seen)
                with contextlib.redirect_stdout(io.StringIO()) as o: cli.fetch_gguf()       # verified: no second request
                assert len(seen) == 1 and "GGUF verified" in o.getvalue()
    finally:
        backends.urlopen, cli.GGUF_URL, cli.GGUF_SHA = saved


def test_closed_network_build_args_and_sbom_coverage():
    df = read("Dockerfile")
    base, offline = df.split("FROM base AS offline")
    for stage in (base, offline):
        assert "ARG PIP_INDEX_URL=" in stage and "ARG PIP_TRUSTED_HOST=" in stage
        assert '[ -n "$PIP_INDEX_URL" ] || unset PIP_INDEX_URL' in stage
    assert "ARG APT_MIRROR=" in offline and 's|http://deb.debian.org|$APT_MIRROR|g' in offline
    assert 'ARG APT_BUILD="build-essential cmake"' in offline and 'ARG APT_RUNTIME="libgomp1"' in offline
    assert re.search(r"^ARG BASE=mirror\.gcr\.io/library/python:3\.12-slim@sha256:[0-9a-f]{64}$", df, re.M)
    b = json.loads(read("docs/sbom.json"))
    names = {c["name"]: c for c in b["components"]}
    q8 = names["apertus-v1.5-8b-text-q8_0.gguf"]
    assert q8["type"] == "machine-learning-model" and q8["hashes"][0]["content"] == cli.BUILDS["q8_0"][1]
    assert {"name": "gleichlaut:size-bytes", "value": "8567121856"} in q8["properties"]
    assert q8["externalReferences"][0]["url"] == cli.BUILDS["q8_0"][0]
    assert names["apertus-v1.5-8b-text-q4_k_m.gguf"]["externalReferences"][0]["url"] == cli.BUILDS["q4_k_m"][0]
    assert names["libgomp1"]["scope"] == "required" and names["cmake"]["scope"] == "excluded"
    assert names["scikit-build-core"]["scope"] == "excluded"
    hosts = json.dumps(b["services"])
    assert "epl.bag.admin.ch" in hosts and "huggingface.co" in hosts and len(b["services"]) == 3
    dep = read("docs/dependencies.md")
    assert "deb.debian.org" in dep.split("## Build time")[1].split("## GGUF provenance")[0]
    assert "Known gap" in read("docs/deploy/README.md")


def test_shadow_workflow_plan_split_and_gather_code_runs():
    """the shadow workflow's own Python (split into shards, merge and grade) on fixture snapshots, with the stub backend."""
    wf = open(os.path.join(ROOT, "..", ".github", "workflows", "shadow.yml"), encoding="utf-8").read()
    assert '- cron: "0 6 2 * *"' in wf and "workflow_dispatch" in wf and "name: shadow-${{ needs.plan.outputs.from }}-${{ needs.plan.outputs.to }}" in wf
    assert "make month BUILD=$BUILD ITEMS=out/plan/shard-${{ matrix.k }}.json" in wf and "gleichlaut ui --records" in wf
    blocks = re.findall(r"<<'EOF'.*?\n(.*?)\n\s*EOF", wf, re.S)
    split = next(b for b in blocks if "shard-{i}.json" in b); gather = next(b for b in blocks if "cli.summarise" in b)
    ded = lambda b: "\n".join(l[10:] if l.startswith(" " * 10) else l for l in b.splitlines())
    from test_ops import _snapshots
    with tmpdir() as d, env(GLEICHLAUT_HIST=os.path.join(d, "hist")):
        a, b = "20261001", "20261101"
        os.makedirs(os.path.join(d, "hist"))
        with contextlib.redirect_stderr(io.StringIO()): _snapshots(os.path.join(d, "hist"), a, b)
        old = os.getcwd(); os.chdir(d); saved_out = cli.OUT; cli.OUT = os.path.join(d, "out")
        try:
            os.makedirs("out/plan")
            rc, out, err = run_cli("month", "--from", a, "--to", b, "--snapshots", os.path.join(d, "hist"), "--dry-run", "--backend", "stub")
            assert rc == 0, out + err
            os.environ["SHARDS"] = "2"
            code = ded(split).replace("${{ steps.dates.outputs.from }}", a).replace("${{ steps.dates.outputs.to }}", b)
            o = io.StringIO()
            with contextlib.redirect_stdout(o): exec(compile(code, "split", "exec"), {})
            assert "idx=[0, 1]" in o.getvalue() or "idx=[0]" in o.getvalue(), o.getvalue()
            for i in range(2 if "1]" in o.getvalue() else 1):
                rc, out, err = run_cli("month", "--items", f"out/plan/shard-{i}.json", "--out", f"out/shards/shadow-shard-{i}/shard-{i}", "--backend", "stub")
                assert rc == 0, out + err
            os.environ["RUN"] = f"out/month/{a}-{b}"
            with contextlib.redirect_stdout(io.StringIO()): exec(compile(ded(gather), "gather", "exec"), {})
            s = json.load(open(f"out/month/{a}-{b}/summary.json", encoding="utf-8"))
            I = json.load(open(f"out/month/{a}-{b}/items.json", encoding="utf-8"))
            assert s["records"] == len(I) and s["missing"] == 0 and s["shards"] >= 1 and s["mining"]["snap_new"] == b
            assert "shadow" in s and "exact_rate" in s["shadow"]
        finally:
            os.chdir(old); cli.OUT = saved_out
            for k in ("SHARDS", "RUN"): os.environ.pop(k, None)
