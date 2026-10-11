"""Audit round 5b (PREREG R22): the stricter-alignment rule set for the operator and negation module, on synthetic pairs;
its frozen fingerprint; the R15 block untouched; the committed R22 results internally consistent and, with the 6 Oct 2026
snapshot, reproduced."""
import json, os, unittest
from gleichlaut import audit as A, score

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
H = os.environ.get("GLEICHLAUT_HIST") or os.path.expanduser("~/Desktop/hackapertus/spikes/gleichlaut/data/hist")
kinds = lambda de, t, L="fr": sorted(f["kind"] for f in A.r22_findings("X", de, t, L))


def test_operator_per_aligned_pair_ranges_and_negated_bounds():
    de = "Patienten mit einem Körpergewicht von mindestens 40 kg. Behandlung über maximal 2 Jahre."
    assert kinds(de, "Patients pesant au moins 40 kg. Traitement pendant 2 ans au maximum.") == []
    assert kinds(de, "Patients pesant au plus 40 kg. Traitement pendant 2 ans au maximum.") == ["operator"]
    # a range has no direction at either end; a negated bound against an un-negated one is not judged (stop rules)
    assert kinds("Kinder von 15 bis 30 kg.", "Enfants de 15 kg à moins de 30 kg.") == []
    assert kinds("Abbruch, wenn die Thrombozytenzahl mindestens 20 nicht erreicht.", "Interruzione se la conta è ancora inferiore a 20.", "it") == []
    # a negation covers an enumeration of bounds, and lives in the bound (no negation finding either)
    assert kinds("Es werden höchstens 60 g pro Monat und höchstens 120 g pro Quartal vergütet.",
                 "Non sono rimborsati più di 60 g al mese e più di 120 g per trimestre.", "it") == []
    o = A.r22_findings("X", "mindestens 30 kg", "au plus 30 kg", "fr")[0]
    assert (o["value"], o["de_dir"], o["tgt_dir"]) == ("30", "min", "max") and o["tgt_spans"] == [[0, 10]]


def test_negation_clause_word_restriction_and_neighbours():
    de = "Die Behandlung wird nicht vergütet, wenn der Patient vorbehandelt ist. Die Dosis beträgt 10 mg."
    ok = "Le traitement n'est pas remboursé si le patient a été prétraité. La dose est de 10 mg."
    assert kinds(de, ok) == [] and kinds(de, ok.replace("n'est pas", "est")) == ["negation"]
    assert kinds("X darf nicht mit anderen Arzneimitteln kombiniert werden.", "X on deve essere combinato con altri medicamenti.", "it") == ["negation"]
    # word negations do not raise a finding (attributive 'nicht', hyphen compounds) unless the other side states the word
    assert kinds("Bei nicht abgeschlossener Familienplanung.", "Lorsque le patient souhaite encore avoir des enfants.") == []
    assert kinds("Patienten mit nicht-mutiertem Gen.", "Patients présentant le gène de type sauvage.") == []
    assert kinds("Patienten mit Non-Hodgkin-Lymphom.", "Patients atteints d'un lymphome hodgkinien.") == ["negation"]
    assert kinds("Patienten mit Non-Hodgkin-Lymphom.", "Patients atteints d'un lymphome non hodgkinien.") == []
    # restriction words: an unpaired 'nur' stands for 'ne ... que'; 'nur' against 'seulement' cancels
    assert kinds("Darf nur von Fachärzten verordnet werden.", "Ne peut, en principe, être prescrit que par des spécialistes.") == []
    assert kinds("Wird nur für Erwachsene vergütet.", "N'est pas remboursé seulement pour les adultes.") == ["negation"]


def test_number_words_substitutions_only():
    de = "Die Patienten haben mindestens zwei Therapielinien erhalten. Kontrolle alle 6 Monate."
    w = [f for f in A.r22_findings("X", de, "Les patients ont reçu au moins trois lignes de traitement. Contrôle tous les 6 mois.", "fr")
         if f["kind"] == "number_word"]
    assert len(w) == 1 and [x["value"] for x in w[0]["de_only"]] == ["2"]
    # an omission (a list announced in one language), a glued word and a multiplier compound: not a finding
    assert kinds("eine der folgenden drei Therapien (A, B, C)", "un des traitements suivants (A, B, C)") == []
    assert kinds("nach zwei oder mehr Therapielinien", "après au moins deuxlignes de traitement") == []
    assert kinds("das Fünffache der Norm", "cinque volte il limite", "it") == []
    assert kinds("Behandlung beider Augen.", "Traitement des quatre yeux.") == ["number_word"]


def test_r22_fingerprint_frozen_and_r15_untouched():
    assert A.r22_logic_sha() == A.R22_FROZEN["logic_sha256"] and A.r5_logic_sha() == A.R5_FROZEN["logic_sha256"]
    D = json.load(open(os.path.join(ROOT, "data", "audit", "audit_r22_20261006.json"), encoding="utf-8"))
    R = json.load(open(os.path.join(ROOT, "eval", "results", "audit_r22.json"), encoding="utf-8"))
    assert D["rules_logic_sha256"] == R["rules_logic_sha256"] == A.R22_FROZEN["logic_sha256"]
    assert D["rules_sha256"] == R["rules_sha256"] == A.R22_FROZEN["block_sha256"]
    s = open(A.__file__, encoding="utf-8").read(); b = A._r22_block(s)
    assert A.r22_logic_sha(s.replace(b, b.replace("# OPERATOR (R22 1, 2).", "# (edited) OPERATOR (R22 1, 2)."))) == A.r22_logic_sha()
    assert A.r22_logic_sha(s.replace(b, b.replace('OP_ALIGN = "aligned"', 'OP_ALIGN = "all"'))) != A.r22_logic_sha()
    import shutil, subprocess
    if not shutil.which("git"): raise unittest.SkipTest("no git: the frozen commit's bytes are not checked")
    r = subprocess.run(["git", "show", A.R22_FROZEN["commit"] + ":track_2b/src/gleichlaut/audit.py"], cwd=ROOT, capture_output=True, text=True)
    if r.returncode: raise unittest.SkipTest("frozen commit not in this checkout")
    assert A.r22_block_sha(r.stdout) == A.R22_FROZEN["block_sha256"] and A.r22_logic_sha(r.stdout) == A.R22_FROZEN["logic_sha256"]


def test_committed_r22_results_are_consistent():
    s = score.audit_r22()
    assert s["planted_copies_reproduce_r15"] and s["rules_logic_matches_code"] and s["op_align"] == A.OP_ALIGN
    assert s["register"]["findings"] == sum(s["register"]["by_kind"].values()) == len(s["register"]["findings_list"])
    assert all(r["final"] in ("real", "minor", "not") for r in s["register"]["findings_list"])
    assert s["ship_on_by_default"] == all(s["criteria"].values())
    assert s["precision"]["r15"]["held"]["findings"] == 21 and s["precision"]["r15"]["dev"]["findings"] == 10
    assert A.R5_ON == {"operator": False, "negation": False, "number_word": False}     # the default is not changed here


def test_register_findings_reproduce():
    if not os.path.exists(os.path.join(H, "20261006-de.json")): raise unittest.SkipTest("no 20261006 snapshot in " + H)
    J, names = A.load(H, "20261006"); F, _ = A.run(H, "20261006", J, names)
    D = json.load(open(os.path.join(ROOT, "data", "audit", "audit_r22_20261006.json"), encoding="utf-8"))
    key = lambda f: json.dumps({k: v for k, v in f.items() if k != "label_source"}, sort_keys=True, ensure_ascii=False)
    assert sorted(map(key, A.run_r22(J, names, F))) == sorted(map(key, D["findings"]))
