"""sl.ingest / sl.mine / backtest: fixture tests that run everywhere, plus the research reproduction check, which needs the
research snapshots (spikes/gleichlaut; $GLEICHLAUT_RESEARCH) and is skipped with a message where they are absent (e.g. CI).
usage: python3 -m unittest discover -s tests -v   (from track_2b/)"""
import json, os, shutil, subprocess, sys, tempfile, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from gleichlaut.sl import ingest, mine as M

RESEARCH = os.environ.get("GLEICHLAUT_RESEARCH", os.path.expanduser("~/Desktop/hackapertus/spikes/gleichlaut"))
HAVE_RESEARCH = all(os.path.exists(os.path.join(RESEARCH, "data", "hist", f"{s}-{l}.json")) for s in M.SNAPS for l in ("de", "fr", "it"))
NO_RESEARCH = f"research snapshots not found at {RESEARCH}/data/hist (set GLEICHLAUT_RESEARCH); reproduction check skipped"


def bundle_new(mpd, name, cuds):
    e = [{"resource": {"resourceType": "MedicinalProductDefinition", "id": mpd, "name": [{"productName": name}]}}]
    e += [{"resource": {"resourceType": "ClinicalUseDefinition", "id": k,
                        "indication": {"diseaseSymptomProcedure": {"concept": {"text": t}}}}} for k, t in cuds]
    return json.dumps({"entry": e})


def bundle_old(mpd, name, ra, texts):
    ext = [{"url": "http://x/regulatedAuthorization-limitation", "extension": [{"url": "limitationText", "valueString": t}]} for t in texts]
    return json.dumps({"entry": [{"resource": {"resourceType": "MedicinalProductDefinition", "id": mpd, "name": [{"productName": name}]}},
                                 {"resource": {"resourceType": "RegulatedAuthorization", "id": ra, "indication": [{"extension": ext}]}}]})


class TestIngest(unittest.TestCase):
    def test_url(self):
        self.assertEqual(ingest.url("20260601", "de"), "https://epl.bag.admin.ch/static/fhir/foph-sl-export-20260601-de.ndjson")
        self.assertEqual(ingest.url("20260901", "it"), "https://epl.bag.admin.ch/static/sl/publication/fhir/foph-sl-publication-20260901-it.ndjson")
        self.assertTrue(ingest.url("latest", "fr").endswith("foph-sl-publication-latest-fr.ndjson"))

    def test_nrm(self):
        self.assertEqual(ingest.nrm("a&amp;lt;b  c d e \n f"), "a<b c d e f")

    def test_extract_both_formats(self):
        lines = [bundle_new("M1", "Foo Tabl", [("FOO.01", "Text A"), ("FOO.02", "Text B")]),
                 bundle_new("M2", "Foo Kaps", [("FOO.01", "Text A changed")]),       # same id, other text -> conflict
                 bundle_old("M3", "Bar Inj", "R9", ["Old 1", "Old 2"]), ""]
        J = ingest.extract(lines)
        self.assertEqual(J["prod"]["M1"], {"name": "Foo Tabl", "keys": ["FOO.01", "FOO.02"]})
        self.assertEqual(J["lim"]["FOO.01"], "Text A")
        self.assertEqual(J["conflict"], {"FOO.01": ["Text A", "Text A changed"]})
        self.assertEqual(J["prod"]["M3"]["keys"], ["RA:R9#0", "RA:R9#1"])
        self.assertEqual(J["lim"]["RA:R9#1"], "Old 2")

    def test_fhir_id(self):
        self.assertEqual(ingest.fhir_id("DIAPHIN.6%"), "DIAPHIN.6-")


FOO_DE = ["Nach Kostengutsprache. Maximal 4 Packungen pro Jahr bei Erwachsenen. Indikationscode 20819.01.",
          "Nach Kostengutsprache. Maximal 6 Packungen pro Jahr bei Erwachsenen. Indikationscode 20819.01."]
FOO_FR = ["Après garantie. Au maximum 4 emballages par an chez les adultes. Code 20819.01.",
          "Après garantie. Au maximum 6 emballages par an chez les adultes. Code 20819.01."]
FOO_IT = ["Dopo garanzia. Al massimo 4 confezioni all'anno negli adulti. Codice 20819.01.",
          "Dopo garanzia. Al massimo 6 confezioni all'anno negli adulti. Codice 20819.01."]
BAR = ["Zur Behandlung der Migräne bei Erwachsenen.", "Vergütet nur nach Rücksprache mit dem Vertrauensarzt, höchstens drei Monate lang."]


def write_hist(d, snaps):
    """snaps: {date: {lang: {mpd: (name, [(key, text)])}}} -> hist JSONs."""
    for s, L in snaps.items():
        for lang, P in L.items():
            J = dict(lim={}, prod={}, conflict={})
            for m, (name, kt) in P.items():
                J["prod"][m] = dict(name=name, keys=[k for k, _ in kt])
                for k, t in kt: J["lim"][k] = t
            with open(os.path.join(d, f"{s}-{lang}.json"), "w", encoding="utf-8") as f: json.dump(J, f, ensure_ascii=False)


class TestMineFixture(unittest.TestCase):
    """3 new-format snapshots: FOO changes 4 -> 6 (FR same step, IT one month later), BAR is rewritten (> 60%), BAZ changes spacing only."""
    SN = ["20260601", "20260701", "20260801"]

    @classmethod
    def setUpClass(cls):
        cls.d = tempfile.mkdtemp()
        def snap(i_de, i_fr, i_it, bar, baz):
            T = {"de": (FOO_DE[i_de], BAR[bar], "Nur bei Kindern ( unter 12 Jahren )" if baz else "Nur bei Kindern (unter 12 Jahren)"),
                 "fr": (FOO_FR[i_fr], "Traitement A" if not bar else "Traitement B", "Seulement enfants"),
                 "it": (FOO_IT[i_it], "Trattamento A" if not bar else "Trattamento B", "Solo bambini")}
            return {l: {"M1": ("Foo Tabl", [("FOO.01", t[0])]), "M2": ("Bar Tabl", [("BAR.01", t[1])]), "M3": ("Baz Sirup", [("BAZ.01", t[2])])}
                    for l, t in T.items()}
        write_hist(cls.d, {"20260601": snap(0, 0, 0, 0, 0), "20260701": snap(1, 1, 0, 1, 1), "20260801": snap(1, 1, 1, 1, 1)})
        cls.H = M.Hist(cls.d); cls.C = M.mine(cls.H, cls.SN, log=False)

    @classmethod
    def tearDownClass(cls): shutil.rmtree(cls.d)

    def test_stats(self):
        self.assertEqual(self.C["stats"][0], dict(a="20260601", b="20260701", matched=3, over60=1, new_distinct_pairs=1))
        self.assertEqual(self.C["stats"][1]["matched"], 0)

    def test_pairs_and_routing(self):
        (p,) = self.C["pairs"]
        self.assertEqual((p["de_old"], p["de_new"]), (FOO_DE[0], FOO_DE[1]))
        self.assertEqual(p["occ"][0]["key_new"], "FOO.01")
        self.assertLessEqual(p["ratio"], M.MAXRATIO); self.assertEqual(M.route(p["ratio"]), "draft")
        (h,) = self.C["human"]
        self.assertEqual(h["de_new"], BAR[1]); self.assertEqual(M.route(h["ratio"]), "human")

    def test_build(self):
        B = M.build(self.C["pairs"], self.H)
        self.assertEqual(B["stats"]["excl_tgt_unchanged"], 1)        # IT unchanged in the step -> pair excluded
        self.assertEqual(B["stats"]["eligible"], 0)

    def test_lag(self):
        from gleichlaut import backtest as BT
        S = BT.Snaps(self.H, self.SN); L = BT.lag(S, self.C)
        (row,) = L["units"]["draft"]["rows"]
        self.assertEqual(row["fr"]["status"], "same_step")
        self.assertEqual((row["it"]["status"], row["it"]["fixed_at"], row["it"]["steps"], row["it"]["days"]), ("lagged", "20260801", 1, 31))


class TestMineRules(unittest.TestCase):
    def test_family_masks_digits(self):
        self.assertEqual(M.family("Code 20819.01 gilt.", "Code 20819.02 gilt."), M.family("Code 11111.01 gilt.", "Code 11111.05 gilt."))
        self.assertNotEqual(M.family("Code 1 gilt.", "Code 2 gilt."), M.family("Code 1 gilt.", "Kode 1 gilt."))

    def test_lt_rule_and_tkey_old_format(self):
        d = tempfile.mkdtemp()
        try:
            a, b = "Kinder < 12 Jahre ab 30 kg, sonst 2 Dosen.", "Kinder < 12 Jahre ab 35 kg, sonst 2 Dosen."
            mk = lambda de, fr: {"de": {"M1": ("X", [("RA:d#0", de), ("RA:d#1", "Zweite Limitierung.")])},
                                 "fr": {"M1": ("X", [("RA:f#0", fr), ("RA:f#1", "Deuxième limitation.")])}}
            write_hist(d, {"20260304": mk(a, "Enfants dès 30 kg."), "20260401": mk(b, "Enfants dès 35 kg.")})
            H = M.Hist(d); C = M.mine(H, ["20260304", "20260401"], log=False)
            self.assertEqual(C["stats"][0]["matched"], 1); self.assertEqual(C["pairs"], [])   # '<' in an old-format pair: dropped
            self.assertEqual(M.tkey(H, "20260401", "fr", "M1", "RA:d#1"), "RA:f#1")
        finally:
            shutil.rmtree(d)


class TestDivergenceTests(unittest.TestCase):
    def test_kinds(self):
        from gleichlaut import backtest as BT
        t = dict(de="Erhaltungsdosis alle acht Wochen, ab 16 kg.", fr="dose toutes les huit semaines, poids ≥ 62.5 kg",
                 it="dose ogni quattro settimane, almeno 16 kg")
        self.assertTrue(BT.test(t, ("it", "lacks", "8"))); self.assertFalse(BT.test(t, ("fr", "lacks", "8")))
        self.assertTrue(BT.test(t, ("fr", "adds", "62.5"))); self.assertTrue(BT.test(t, ("fr", "lacks", "16")))
        self.assertIsNone(BT.test(dict(de="x", fr=None), ("fr", "adds", "1")))
        self.assertTrue(BT.test(dict(de="a", fr="Le carcinome est traité avec les doses", it="Le carcinome est traité avec les doses"), ("it", "is_fr", None)))
        self.assertFalse(BT.test(dict(de="a", fr="Le carcinome", it="Il carcinoma è trattato con le dosi della terapia"), ("it", "is_fr", None)))


@unittest.skipUnless(HAVE_RESEARCH, NO_RESEARCH)
class TestReproducesResearch(unittest.TestCase):
    """the port reproduces spikes/gleichlaut/s2/{changes_de,pool_stats,items,items_all}.json from the 9 research snapshots."""
    @classmethod
    def setUpClass(cls):
        cls.R = os.path.join(RESEARCH, "s2"); cls.H = M.Hist(os.path.join(RESEARCH, "data", "hist"))
        cls.C = M.mine(cls.H, log=False); cls.ref = json.load(open(os.path.join(cls.R, "changes_de.json"), encoding="utf-8"))

    def test_mine_stats_exact(self):
        self.assertEqual(self.C["stats"], self.ref["stats"])
        self.assertEqual(len(self.C["pairs"]), 216)

    def test_mine_pairs_exact(self):
        key = lambda ps: {(p["de_old"], p["de_new"]): (p["ratio"], tuple(p["first"]), sorted(json.dumps(o, sort_keys=True) for o in p["occ"])) for p in ps}
        self.assertEqual(key(json.loads(json.dumps(self.C["pairs"]))), key(self.ref["pairs"]))

    def test_build_exact_given_research_order(self):
        """the research iterated a set of products (order = PYTHONHASHSEED); fed the research pair order, build() is byte-exact."""
        B = M.build(self.ref["pairs"], self.H)
        self.assertEqual(B["stats"], json.load(open(os.path.join(self.R, "pool_stats.json"))))
        self.assertEqual(B["items"], json.load(open(os.path.join(self.R, "items.json"), encoding="utf-8")))
        ra = json.load(open(os.path.join(self.R, "items_all.json"), encoding="utf-8"))
        self.assertEqual([{k: x[k] for k in r} for x, r in zip(B["items_all"], ra)], ra)

    def test_build_pool_on_port_order(self):
        """on the port's own (sorted) order: identical pool stats and identical 362-item pool content."""
        B = M.build(self.C["pairs"], self.H)
        self.assertEqual(B["stats"], json.load(open(os.path.join(self.R, "pool_stats.json"))))
        F = ("lang", "de_old", "de_new", "tgt_old", "tgt_new", "cluster")
        ra = json.load(open(os.path.join(self.R, "items_all.json"), encoding="utf-8"))
        self.assertEqual(sorted(tuple(x[f] for f in F) for x in B["items_all"]), sorted(tuple(x[f] for f in F) for x in ra))
        self.assertEqual([x["cluster"] for x in B["items"]], [x["cluster"] for x in json.load(open(os.path.join(self.R, "items.json")))])

    def test_extract_matches_research_script(self):
        src = os.path.join(RESEARCH, "data", "sl-de.ndjson")
        if not os.path.exists(src): self.skipTest(f"{src} absent")
        d = tempfile.mkdtemp()
        try:
            sl = os.path.join(d, "slice.ndjson")
            with open(src, encoding="utf-8") as f, open(sl, "w", encoding="utf-8") as g:
                for i, line in zip(range(300), f): g.write(line)
            out = os.path.join(d, "ref.json")
            with open(sl, "rb") as f:
                subprocess.run([sys.executable, "-I", os.path.join(self.R, "extract.py"), out], stdin=f, check=True, capture_output=True)
            with open(sl, encoding="utf-8") as f: mine_out = ingest.extract(f)
            with open(out, encoding="utf-8") as f: self.assertEqual(mine_out, json.load(f))
        finally:
            shutil.rmtree(d)


if __name__ == "__main__":
    unittest.main()
