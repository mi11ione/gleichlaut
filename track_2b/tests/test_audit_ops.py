"""The audit as a federal operator runs it (phase 1 run, 11 Oct 2026): one entry point with the same defaults on every
documented path, output outside the committed evidence, missing snapshots as exit 2, --fail-on-new for the scheduler, the
GGUF download pinned to the recorded Hugging Face revisions. No network: snapshot folders are empty or synthetic, and
gleichlaut.audit.main is replaced where a whole run would need the 6 Oct 2026 feed."""
import contextlib, io, json, os, re, shutil, subprocess, sys, tempfile
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(H, "..", "src"))
from gleichlaut import audit, cli, core

ROOT = core.ROOT


def run_cli(*args):
    o, e = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(o), contextlib.redirect_stderr(e): rc = cli.main(list(args))
    return rc, o.getvalue(), e.getvalue()


@contextlib.contextmanager
def tmp():
    d = tempfile.mkdtemp(prefix="gl-aud-ops-")
    try: yield d
    finally: shutil.rmtree(d, ignore_errors=True)


@contextlib.contextmanager
def clean_env(**kw):
    keys = ("GLEICHLAUT_AUDIT_OUT", "GLEICHLAUT_OUT", "GLEICHLAUT_HIST", "GLEICHLAUT_METRICS_DIR")
    old = {k: os.environ.get(k) for k in keys}
    for k in keys: os.environ.pop(k, None)
    os.environ.update(kw)
    try: yield
    finally:
        for k, v in old.items():
            if v is None: os.environ.pop(k, None)
            else: os.environ[k] = v


def read(p): return open(os.path.join(ROOT, p), encoding="utf-8").read()


# ------------------------------------------------------------------ 1: never into the committed evidence by default
def test_default_output_is_untracked_and_data_audit_needs_evidence():
    with clean_env():
        o = audit.out_dir()
        assert os.path.realpath(o) == os.path.realpath(os.path.join(ROOT, "out", "audit")), o
        assert audit.out_dir(None, evidence=True) == audit.DEST
        for bad in (audit.DEST, os.path.join(audit.DEST, "x"), os.path.join(ROOT, "data", "audit", ".")):
            try: audit.out_dir(bad); raise AssertionError(f"accepted {bad}")
            except ValueError as e: assert "--evidence" in str(e)
        try: audit.out_dir("/elsewhere", evidence=True); raise AssertionError("--evidence with another --out accepted")
        except ValueError: pass
    with clean_env(GLEICHLAUT_AUDIT_OUT="/tmp/x-audit"): assert audit.out_dir() == "/tmp/x-audit"
    with clean_env(GLEICHLAUT_OUT="/tmp/x-out"): assert audit.out_dir() == os.path.join("/tmp/x-out", "audit")
    r = subprocess.run(["git", "check-ignore", "-q", os.path.join(ROOT, "out", "audit", "audit_20261101.json")], cwd=ROOT)
    assert r.returncode in (0, 128), "out/audit/ must be gitignored"       # 128: not a git checkout (an image)
    # an explicit --out data/audit is refused before anything is read or written: the committed files stay as they are
    before = {f: os.path.getmtime(os.path.join(audit.DEST, f)) for f in os.listdir(audit.DEST)}
    with tmp() as h, clean_env():
        rc, out, err = run_cli("audit", "--hist", h, "--date", "20261006", "--out", audit.DEST)
        assert rc == 2 and "refusing to write" in err, (rc, err)
        assert audit.main(["--hist", h, "--date", "20261006", "--out", "data/audit"]) == 2
    assert {f: os.path.getmtime(os.path.join(audit.DEST, f)) for f in os.listdir(audit.DEST)} == before
    mk = read("Makefile")
    rec = mk.split("\nlocal-audit:\n")[1].split("\n\n")[0]
    assert "data/audit" not in rec and "--evidence" not in rec and "$(AUDIT_SEL)" in rec


# ------------------------------------------------------------------ 3: missing snapshots are exit 2, as documented
def test_missing_snapshots_exit_2_on_every_path_and_the_table_says_so():
    with tmp() as h, tmp() as o, clean_env():
        rc, _, err = run_cli("audit", "--hist", h, "--out", o)                      # empty folder, --date latest (default)
        assert rc == 2 and "no snapshot" in err and "--fetch" in err, (rc, err)
        rc, _, err = run_cli("audit", "--hist", h, "--out", o, "--date", "20261006", "--fail-on-new")
        assert rc == 2 and "20261006-de.json" in err, (rc, err)
        open(os.path.join(h, "20261006-de.json"), "w").write("{}")              # one language only: still 2, the others named
        rc, _, err = run_cli("audit", "--hist", h, "--out", o, "--date", "20261006", "--fail-on-findings")
        assert rc == 2 and "20261006-fr.json" in err and "20261006-it.json" in err and "20261006-de.json," not in err, err
        assert run_cli("audit", "--hist", h, "--out", o, "--date", "2026-10-06")[0] == 2
        env_ = dict(os.environ, PYTHONPATH=os.path.join(ROOT, "src"))
        for mod in (["-m", "gleichlaut", "audit"], ["-m", "gleichlaut.audit"]):        # the plain-Python commands
            r = subprocess.run([sys.executable] + mod + ["--hist", h, "--out", o], capture_output=True, text=True, env=env_, cwd=ROOT)
            assert r.returncode == 2 and "no snapshot" in r.stderr and "Traceback" not in r.stderr, (mod, r.returncode, r.stderr)
        assert not os.listdir(o)
    ops = read("docs/operations.md")
    t6 = ops[ops.index("## 6. Exit codes"):ops.index("## 6b.")]
    row = {l.split("|")[1].strip(): l for l in t6.splitlines() if re.match(r"\| \d+ \|", l)}
    assert "missing snapshots" in row["2"] and "audit" in row["2"] and "audit" not in row["1"]
    assert "--fail-on-new" in row["8"] and "--fail-on-findings" in row["8"]
    s0 = ops[ops.index("## 0. Use it tomorrow"):ops.index("## 1. Install")]
    assert "2 no snapshot for the date" in s0 and "6 the feed could not be fetched" in s0
    assert "missing snapshots" in read("docs/deploy/alert.sh").split("\n  2)")[1].split("\n")[0]
    assert "missing configuration or snapshots" in cli.__doc__


# ------------------------------------------------------------------ 2: one entry point, the same defaults
def test_one_entry_point_with_the_same_defaults_everywhere():
    want = "gleichlaut audit --date latest --fetch"
    mk = read("Makefile")
    assert re.search(r"^AUDIT_DATE \?= latest$", mk, re.M)
    rec = mk.split("\naudit:\n")[1].split("\n\n")[0]
    assert "python -m gleichlaut audit --date $(AUDIT_DATE) --fetch $(AUDIT_ARGS)" in rec, rec
    assert "AUDIT_SEL = --date $(AUDIT_DATE) --fetch" in mk
    unit = read("docs/deploy/systemd/gleichlaut-audit.service")
    ex = [l for l in unit.splitlines() if l.startswith("ExecStart=")]
    assert ex == ["ExecStart=/opt/gleichlaut/venv/bin/python -m gleichlaut audit --date latest --fetch --fail-on-new"], ex
    k8 = read("docs/deploy/kubernetes/gleichlaut.yaml")
    assert "exec python -m " + want + " --fail-on-new" in k8
    ops = read("docs/operations.md"); s0 = ops[ops.index("## 0. Use it tomorrow"):ops.index("## 1. Install")]
    assert "PYTHONPATH=src python3 -m " + want in s0 and "make local-audit" in s0
    dep = read("docs/deploy/README.md")
    assert "`" + want + " --fail-on-new`" in dep
    for name, txt in (("Makefile audit", rec), ("unit", unit), ("k8s", k8), ("operations §0", s0)):
        assert "--terms data/audit" not in txt and "gleichlaut.sl.ingest" not in txt and "feeds --latest" not in txt, name
    # the terminology default lives in gleichlaut.audit, so every path gets it: the shipped pairs unless the folder holds
    # at least as many usable snapshots of the year as they were mined from
    need = len(json.load(open(audit.TERMS, encoding="utf-8"))["meta"]["snapshots"])
    with tmp() as h:
        def snap(d):
            for L in ("de", "fr", "it"): open(os.path.join(h, f"{d}-{L}.json"), "w").write("{}")
        snap("20261006")
        assert audit.terms_source(h, "20261006") == audit.TERMS and audit.latest_local(h) == "20261006"
        open(os.path.join(h, "20261106-de.json"), "w").write("{}")              # incomplete: not the latest local snapshot
        assert audit.latest_local(h) == "20261006"
        for m in range(1, need):
            snap(f"2026{m:02d}01")
        assert len(audit.snapshots(h, "20261006")) == need and audit.terms_source(h, "20261006") is None
        assert audit.terms_source(h, "20270101") in (audit.TERMS,)                 # another year: its own snapshots count


# ------------------------------------------------------------------ 4: --fail-on-new
def _finding(fid, lim, val, eq=False, lang="it"):
    return dict(fid=fid, id=lim, product=[lim.split(".")[0].title()], lang=lang, kind="number", likely_equivalent=eq,
                de_only=[dict(value=val, unit="mg", context=["… [" + val + "] mg …"])], tgt_only=[],
                description=f"DE has {val} (mg), {lang.upper()} does not")


def test_fail_on_new_pages_once_per_new_finding_and_respects_decisions():
    real = audit.main
    state = {"F": []}
    def fake(argv=None):
        import argparse
        ap = argparse.ArgumentParser(); ap.add_argument("--date"); ap.add_argument("--out"); ap.add_argument("--hist")
        ap.add_argument("--fail-on-findings", action="store_true")
        a = ap.parse_args(argv); os.makedirs(a.out, exist_ok=True)
        F = state["F"]
        json.dump(dict(summary=dict(date=a.date), findings=F), open(os.path.join(a.out, f"audit_{a.date}.json"), "w"))
        json.dump(dict(date=a.date, by_kind=dict(number=len(F)), limitations_with_any_finding=len(F)),
                  open(os.path.join(a.out, f"audit_{a.date}_summary.json"), "w"))
        return 1 if a.fail_on_findings and any(not f["likely_equivalent"] for f in F) else 0
    audit.main = fake
    try:
        with tmp() as d, clean_env():
            base = lambda date, *x: run_cli("audit", "--date", date, "--out", d, "--hist", d, *x)
            state["F"] = [_finding("N01", "NEMLUVIO.01", "8"), _finding("N02", "DIAPHIN.6-", "6"), _finding("N03", "X.1", "2", eq=True)]
            rc, _, err = base("20261006", "--fail-on-new")                         # first run: every open finding is new
            assert rc == 8 and "2 new finding(s) of 2 open" in err, err
            N = json.load(open(os.path.join(d, "audit_20261006_new.json")))
            assert N["new"] == 2 and N["previous_run"] is None and {f["fid"] for f in N["findings"]} == {"N01", "N02"}
            rc, _, err = base("20261106", "--fail-on-new")                         # the same findings a month later: no page
            assert rc == 0 and "no new finding" in err, err
            assert base("20261106", "--fail-on-new")[0] == 0                       # a re-run of the same date: still none
            assert base("20261106", "--fail-on-findings")[0] == 8                  # the old flag still pages on any open one
            # a new finding, ranked first so every rank number shifts: only it is new (matched by signature, not by N01..)
            state["F"] = [_finding("N01", "BEYFORTUS.1", "50")] + [dict(f, fid=f"N0{i + 2}") for i, f in enumerate(state["F"])]
            rc, _, err = base("20261206", "--fail-on-new", "--metrics-file", os.path.join(d, "m.prom"))
            assert rc == 8 and "1 new finding(s) of 3 open" in err, err
            N = json.load(open(os.path.join(d, "audit_20261206_new.json")))
            assert [f["id"] for f in N["findings"]] == ["BEYFORTUS.1"] and N["previous_run"]["date"] == "20261106"
            sig = N["findings"][0]["signature"]
            assert sig.startswith("BEYFORTUS.1|number|it|"), sig
            assert 'gleichlaut_audit_new_findings{job="audit"} 1' in open(os.path.join(d, "m.prom")).read()
            # decided in the review page (its export), dropped into out/audit/decisions/: not new any more
            os.makedirs(os.path.join(d, "decisions"))
            json.dump(dict(audit_date="20261206", audit_rows={sig: dict(decided=True, remedy="exofficio", wrong=["IT"])}),
                      open(os.path.join(d, "decisions", "gleichlaut-audit-decisions-20261206.json"), "w"))
            os.remove(os.path.join(d, "audit_20261206.json"))                       # compare with 20261106 again
            rc, _, err = base("20261206", "--fail-on-new")
            assert rc == 0 and "1 decided" not in err and "no new finding" in err, err
            dec2 = os.path.join(d, "other.json")                                    # --decided FILE; an undecided row does not count
            json.dump(dict(audit_rows={sig: dict(decided=False)}), open(dec2, "w"))
            os.remove(os.path.join(d, "audit_20261206.json"))
            assert base("20261206", "--fail-on-new", "--decided", dec2)[0] == 8
            assert base("20261206", "--decided", dec2)[0] == 2                      # --decided without --fail-on-new
            assert base("20261206", "--fail-on-new", "--fail-on-findings")[0] == 2
    finally:
        audit.main = real
    # the signature is the one the review page stores decisions under
    from gleichlaut.ui import audit_view as av
    A = json.load(open(av.AUDIT, encoding="utf-8")); D = av.data(hist=None)
    S = audit.signatures(A["findings"])
    assert len(set(S)) == len(S) == len(A["findings"]) and set(S) == {r["sig"] for r in D["rows"]}


def test_scheduled_units_and_docs_use_fail_on_new():
    unit = read("docs/deploy/systemd/gleichlaut-audit.service")
    assert "--fail-on-new" in unit and "--fail-on-findings" not in unit.split("[Service]")[1]
    assert "--fail-on-new" in read("docs/deploy/kubernetes/gleichlaut.yaml")
    alert = read("docs/deploy/alert.sh"); assert "8) sev=reviewer" in alert and "--fail-on-new" in alert.split("\n  8)")[1].split("\n")[0]
    ops = read("docs/operations.md")
    assert "`gleichlaut audit --fail-on-new` (the default of the systemd unit and the CronJob)" in ops
    assert "--fail-on-new" in cli.cmd_audit.__doc__ and "--fail-on-new" in cli.__doc__


# ------------------------------------------------------------------ 8: the GGUF URLs name the recorded revisions
def test_model_urls_are_pinned_to_the_recorded_revisions():
    dep = read("docs/dependencies.md")
    rev = {"q8_0": re.search(r"Q8_0-GGUF` \(revision `([0-9a-f]{40})`", dep).group(1),
           "q4_k_m": re.search(r"Q4_K_M-GGUF` \(revision `([0-9a-f]{40})`", dep).group(1)}
    for b, (url, sha) in cli.BUILDS.items():
        assert f"/resolve/{rev[b]}/" in url and "/resolve/main/" not in url, url
        assert url in dep and len(sha) == 64
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import supply_chain as sc
    assert sc.GGUF_Q8["url"] == cli.BUILDS["q8_0"][0] and sc.GGUF_Q4["url"] == cli.BUILDS["q4_k_m"][0]
    files = ["src/gleichlaut/cli.py", "tools/supply_chain.py", "docs/sbom.json", "docs/dependencies.md", "docs/operations.md",
             "docs/deploy/README.md"]
    wf = os.path.join(ROOT, "..", ".github", "workflows")
    files += [os.path.join("..", ".github", "workflows", f) for f in (os.listdir(wf) if os.path.isdir(wf) else [])]
    for f in files:
        assert "huggingface.co" not in read(f) or "/resolve/main/" not in read(f), f
