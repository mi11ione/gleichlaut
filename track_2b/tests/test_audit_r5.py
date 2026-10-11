"""Audit round 5 (PREREG R15): operator direction, negation and number words on synthetic pairs; the existing kinds are
untouched by the round (run_all(..., r5=False) is the default, number findings only gain a display field); the committed
R15 results are internally consistent (no snapshot needed)."""
import importlib.util, json, os, random, unittest
from gleichlaut import audit as A, score

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
H = os.environ.get("GLEICHLAUT_HIST") or os.path.expanduser("~/Desktop/hackapertus/spikes/gleichlaut/data/hist")
_spec = importlib.util.spec_from_file_location("audit_inject", os.path.join(ROOT, "tools", "audit_inject.py"))
I = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(I)
kinds = lambda de, t, L="fr": sorted(f["kind"] for f in A.r5_findings("X", de, t, L))


def test_operator_direction():
    de = "Patienten mit einem Körpergewicht von mindestens 40 kg. Behandlung über maximal 2 Jahre."
    assert kinds(de, "Patients pesant au moins 40 kg. Traitement pendant 2 ans au maximum.") == []
    assert kinds(de, "Patients pesant au plus 40 kg. Traitement pendant 2 ans au maximum.") == ["operator"]
    assert kinds(de, "Pazienti di almeno 40 kg. Trattamento per al massimo 2 anni.", "it") == []
    assert kinds(de, "Pazienti di al massimo 40 kg. Trattamento per al massimo 2 anni.", "it") == ["operator"]
    # same direction, inclusive vs strict: not a finding; a range end has no direction; a negated bound is left out
    assert kinds("ab 12 Jahren", "plus de 12 ans") == []
    assert kinds("Kinder von 15 bis 30 kg.", "Enfants de 15 kg à moins de 30 kg.") == []
    assert kinds("Patienten, die keine Reduktion von mindestens 50% erreichen.", "Patients qui n'atteignent pas une réduction d'au moins 50%.") == []
    o = A.r5_findings("X", "mindestens 30 kg", "au plus 30 kg", "fr")[0]
    assert (o["value"], o["de_dir"], o["tgt_dir"]) == ("30", "min", "max") and o["tgt_spans"] == [[0, 10]]


def test_negation_per_aligned_sentence():
    de = "Die Behandlung wird nicht vergütet, wenn der Patient vorbehandelt ist. Die Dosis beträgt 10 mg."
    ok = "Le traitement n'est pas remboursé si le patient a été prétraité. La dose est de 10 mg."
    assert kinds(de, ok) == [] and kinds(de, ok.replace("n'est pas", "est")) == ["negation"]
    assert kinds(de, "Il trattamento non è rimborsato se il paziente è stato pretrattato. La dose è di 10 mg.", "it") == []
    assert kinds(de, "Il trattamento è rimborsato se il paziente è stato pretrattato. La dose è di 10 mg.", "it") == ["negation"]
    # 'ne ... que' (= nur), a word negation on the other side, an expletive: not a finding
    assert kinds("Darf nur von Fachärzten verordnet werden.", "Ne peut être prescrit que par des spécialistes.") == []
    assert kinds("Bei unzureichendem Ansprechen auf 2 Therapien.", "En cas de réponse insuffisante à 2 traitements.") == []
    assert kinds("Weiterbehandlung bis zur Bestätigung der Progression.", "Trattamento fino a quando la progressione non è confermata.", "it") == []
    g = A.r5_findings("X", de, ok.replace("n'est pas", "est"), "fr")[0]
    assert g["side"] == "de" and g["negations"] == ["nicht"] and g["tgt_span"][0] == 0


def test_number_words_per_aligned_sentence_and_dedup():
    de = "Die Patienten haben mindestens zwei Therapielinien erhalten. Kontrolle alle 6 Monate."
    assert kinds(de, "Les patients ont reçu au moins deux lignes de traitement. Contrôle tous les 6 mois.") == []
    w = [f for f in A.r5_findings("X", de, "Les patients ont reçu au moins trois lignes de traitement. Contrôle tous les 6 mois.", "fr")
         if f["kind"] == "number_word"]
    assert len(w) == 1 and [x["value"] for x in w[0]["de_only"]] == ["2"] and [x["value"] for x in w[0]["tgt_only"]] == ["3"]
    # beide = 2, an ordinal word on the other side, a '-fach' compound: not a finding
    assert kinds("Behandlung beider Augen.", "Traitement des deux yeux.") == []
    assert kinds("an jedem zweiten Tag 10 mg", "tous les deux jours 10 mg") == []
    assert kinds("als Zweifachkombination mit Metformin", "en bithérapie avec la metformine") == []
    # a value the existing number finding names is not repeated
    nf = dict(de_only=[dict(value="8")], tgt_only=[dict(value="4")])
    assert not [f for f in A.r5_findings("X", "alle acht Wochen", "toutes les quatre semaines", "fr", nf) if f["kind"] == "number_word"]


def test_counterpart_display_field():
    de, it = "danach alle acht Wochen 30 mg", "successivamente ogni quattro settimane 30 mg"
    f = dict(lang="it", de_only=[dict(value="8", unit="Wochen")], tgt_only=[])
    assert A.counterpart(f, de, it) == {"it": [dict(value="4", unit="settimane", src="word", for_value="8")]}


def test_audit_item_default_kinds_unchanged():
    x = dict(de_old="mindestens 30 kg", tgt_old="au plus 30 kg", lang="fr")
    assert all(f["kind"] in A.KINDS_ALL for f in A.audit_item(x, terms=[]))
    r = A.audit_item(x, kinds=A.KINDS_ALL + A.KINDS_R5, terms=[])
    assert [f["kind"] for f in r if f["kind"] in A.KINDS_R5] == ["operator"] and r[-1]["values"] == ["30"]


def test_negation_add_injector():
    t = "Le traitement est remboursé pendant 12 mois. Il y a 2 cycles."
    S = I.negadd_sites(t, "fr"); assert len(S) == 2
    a = I.inj_negation_add(t, "fr", random.Random(3)); b = I.inj_negation_add(t, "fr", random.Random(3))
    assert a == b and ("n'est pas remboursé" in a["new"] or "n'y a pas" in a["new"])
    assert I.inj_negation_add("Le traitement n'est pas remboursé pendant 12 mois.", "fr", random.Random(1)) is None
    assert "non è rimborsato" in I.inj_negation_add("Il trattamento è rimborsato per 12 mesi.", "it", random.Random(1))["new"]


def test_existing_kinds_unchanged_on_the_register():
    if not os.path.exists(os.path.join(H, "20261006-de.json")): raise unittest.SkipTest("no 20261006 snapshot in " + H)
    F, _, _ = A.run_all(H, "20261006")
    com = json.load(open(os.path.join(A.DEST, "audit_20261006.json"), encoding="utf-8"))
    key = lambda f: json.dumps({k: v for k, v in f.items() if k not in ("counterpart", "first_seen", "seen_in")}, sort_keys=True, ensure_ascii=False)
    assert sorted(map(key, F)) == sorted(map(key, com["findings"]))
    assert {k: sum(f["kind"] == k for f in F) for k in A.KINDS_ALL} == dict(number=21, unit=0, language=1, editorial=5, terminology=11)


def test_committed_r15_results_are_consistent():
    p = os.path.join(ROOT, "eval", "results", "audit_injection_r15_held.json")
    if not os.path.exists(p): raise unittest.SkipTest("R15 held run not committed yet")
    R = json.load(open(p, encoding="utf-8"))
    assert R["model_calls"] == 0 and R["half"] == "held" and R["seed"] == 20261016 and set(R["types"]) == set(I.TYPES_R15)
    for t, v in R["types"].items():
        assert v["n"] == sum(x["n"] for x in v["by_lang"].values()) and v["detected_before"] <= v["detected_after"] <= v["n"]
        assert v["wilson95_after"] == I.wilson(v["detected_after"], v["n"]) and len(v["misses"]) == v["n"] - v["detected_after"]
    s = score.audit_r15()
    assert set(s["recall"]) == set(I.TYPES_R15) and set(s["decision"]) == set(A.KINDS_R5)
    for k, d in s["decision"].items(): assert d["on"] == A.R5_ON[k] == d["pass"]


def test_round5_rule_fingerprint_matches_the_frozen_rules():
    """The R15 freeze (commit 6a2c269) holds: the round-5 rule logic (syntax tree without comments, docstrings or layout)
    is the frozen one, and the committed audit summary and R15 result record it. The byte fingerprint R15 recorded
    (rules_sha256) is that of the frozen commit; it is kept as recorded (PREREG results log, R15 post-freeze note).
    A change to the rules makes this test fail: it needs a new pre-registration, not a new fingerprint."""
    assert A.r5_logic_sha() == A.R5_FROZEN["logic_sha256"]
    S = json.load(open(os.path.join(ROOT, "data", "audit", "audit_20261006_summary.json"), encoding="utf-8"))["round5"]
    R = json.load(open(os.path.join(ROOT, "eval", "results", "audit_r15.json"), encoding="utf-8"))
    assert S["rules_logic_sha256"] == R["rules_logic_sha256"] == A.R5_FROZEN["logic_sha256"]
    assert S["rules_sha256"] == R["rules_sha256"] == A.R5_FROZEN["block_sha256"]
    # a comment or docstring edit leaves the logic fingerprint alone; a constant does not
    s = open(A.__file__, encoding="utf-8").read(); b = A._r5_block(s)
    assert A.r5_logic_sha(s.replace(b, b.replace("# set by", "# (edited) set by").replace('KINDS_R5 = (', '# a new comment\nKINDS_R5 = ('))) == A.r5_logic_sha()
    assert A.r5_logic_sha(s.replace(b, b.replace("ALIGN_MAX, ALIGN_MAX_UNEVEN = 0.4, 0.2", "ALIGN_MAX, ALIGN_MAX_UNEVEN = 0.4, 0.3"))) != A.r5_logic_sha()
    import shutil, subprocess
    if not shutil.which("git"): raise unittest.SkipTest("no git: the frozen commit's bytes are not checked")
    r = subprocess.run(["git", "show", A.R5_FROZEN["commit"] + ":track_2b/src/gleichlaut/audit.py"], cwd=ROOT, capture_output=True, text=True)
    if r.returncode: raise unittest.SkipTest("frozen commit not in this checkout")
    assert A.r5_block_sha(r.stdout) == A.R5_FROZEN["block_sha256"] and A.r5_logic_sha(r.stdout) == A.R5_FROZEN["logic_sha256"]
