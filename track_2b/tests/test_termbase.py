"""Termbase (gleichlaut.termbase): BAG's house FR/IT renderings mined from the register, a valid TBX-Basic export, and the
display-only advisory (its own low-priority note, never one of the three reasons, never a verdict). The committed
eval/results/termbase.json equals termbase.measure(). Runs under pytest or as `python3 tests/test_termbase.py`."""
import json, os, re, sys, tempfile
import xml.etree.ElementTree as ET
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from gleichlaut import core, termbase as T

RES = os.path.join(core.ROOT, "eval", "results", "termbase.json")


def _entries():
    return {(e["lang"], e["term"]): e for e in json.load(open(T.JSON, encoding="utf-8"))["entries"]}


def test_shipped_termbase_has_the_house_renderings_the_register_uses():
    E = _entries()
    assert len(E) == 2 * len(T.HEADS) and 30 <= len(T.HEADS) <= 60
    assert E[("fr", "Kostengutsprache")]["preferred"] == "garantie de prise en charge"
    assert E[("fr", "Vertrauensarzt")]["preferred"] == "médecin-conseil"
    assert E[("it", "Vertrauensarzt")]["preferred"] == "medico di fiducia"
    assert E[("fr", "obligatorische Krankenpflegeversicherung")]["preferred"] == "assurance obligatoire des soins"
    assert E[("it", "obligatorische Krankenpflegeversicherung")]["preferred"] == "assicurazione obbligatoria delle cure medico-sanitarie"
    kv = E[("fr", "Krankenversicherer")]
    assert kv["preferred"] == "assureur-maladie" and any(v["text"] == "assurance maladie" for v in kv["variants"])
    for e in E.values():
        if not e.get("house"): continue
        assert e["support"] >= T.MIN_SUPPORT and e["share"] > T.MIN_SHARE and e["support"] <= e["limitations_with_term"]
        assert abs(e["share"] - e["support"] / e["limitations_with_term"]) < 1e-3
        for v in e["variants"]:
            assert v["limitations"] >= T.VAR_MIN and not T._inflection(v["tokens"], e["preferred_tokens"])


def test_tbx_is_valid_and_rebuilt_from_the_json():
    assert T.validate_tbx(T.TBX) == []
    d = tempfile.mkdtemp(prefix="gl-tbx-"); p = os.path.join(d, "x.tbx")
    assert T.main(["--from", T.JSON, "--tbx", p, "--quiet"]) == 0
    assert open(p, "rb").read() == open(T.TBX, "rb").read()
    q = lambda t: f"{{{T.TBX_NS}}}{t}"
    r = ET.parse(p).getroot(); E = _entries()
    assert len(r.findall(f".//{q('conceptEntry')}")) == len({t for (L, t), e in E.items() if e.get("house")})
    for ts in r.iter(q("termSec")):
        assert ts.find(q("admin")).get("type") == "source" and re.search(r"BAG SL 06\.10\.2026, \d+ limitations", ts.find(q("admin")).text)
    src = open(p, encoding="utf-8").read()
    bad = {"wf": src.replace("</body>", "", 1), "status": src.replace("preferredTerm-admn-sts", "bestTerm", 1),
           "term": re.sub(r"<term>[^<]*</term>", "", src, count=1), "ns": src.replace(T.TBX_NS, "urn:x", 1)}
    for k, s in bad.items():
        b = os.path.join(d, f"bad-{k}.tbx"); open(b, "w", encoding="utf-8").write(s)
        assert T.validate_tbx(b), k


def _reg(n_pref=12, n_var=3):
    """a synthetic aligned register: 'Kostengutsprache' rendered 'garantie de prise en charge' (n_pref) or
    'accord de financement' (n_var), always next to boilerplate that belongs to 'Konsultation'."""
    J = {L: {"lim": {}, "prod": {}} for L in ("de", "fr", "it")}
    DE = ("Die Behandlung mit PRODUKT{k} bedarf der Kostengutsprache nach vorgängiger Konsultation.",
          "Für PRODUKT{k} ist eine Kostengutsprache erforderlich, ausser nach Konsultation.",
          "Eine neue Kostengutsprache für PRODUKT{k} wird jährlich nach Konsultation verlangt.")
    FR = ("Le traitement par PRODUKT{k} nécessite une {t} après une consultation préalable.",
          "Pour PRODUKT{k}, une {t} est requise, sauf après une consultation.",
          "Une nouvelle {t} pour PRODUKT{k} est exigée chaque année après une consultation.")
    IT = ("Il trattamento con PRODUKT{k} richiede la garanzia di assunzione dei costi dopo la consultazione.",
          "Per PRODUKT{k} occorre una garanzia di assunzione dei costi, salvo dopo la consultazione.",
          "Una nuova garanzia di assunzione dei costi per PRODUKT{k} è chiesta ogni anno dopo la consultazione.")
    for k in range(n_pref + n_var + 10):
        i = f"L{k:02d}"
        if k < n_pref + n_var:
            t = "garantie de prise en charge" if k < n_pref else "accord de financement"
            J["de"]["lim"][i] = DE[k % 3].format(k=k); J["fr"]["lim"][i] = FR[k % 3].format(k=k, t=t)
            J["it"]["lim"][i] = IT[k % 3].format(k=k)
        else:
            J["de"]["lim"][i] = f"Die Behandlung mit PRODUKT{k} wird nach Konsultation vergütet."
            J["fr"]["lim"][i] = f"Le traitement par PRODUKT{k} est remboursé après une consultation."
            J["it"]["lim"][i] = f"Il trattamento con PRODUKT{k} è rimborsato dopo la consultazione."
    return J


def test_mining_finds_the_house_rendering_and_its_minority_variant():
    tb = T.mine(_reg(), "20990101", terms=["Kostengutsprache"])
    fr = next(e for e in tb["entries"] if e["lang"] == "fr")
    assert fr["preferred"] == "garantie de prise en charge" and fr["house"] and fr["support"] == 12 and fr["share"] == 0.8
    assert [v["text"] for v in fr["variants"]] == ["accord de financement"] and fr["variants"][0]["limitations"] == 3
    it = next(e for e in tb["entries"] if e["lang"] == "it")
    assert it["preferred"] == "garanzia di assunzione dei costi" and it["share"] == 1.0
    fr2 = next(e for e in T.mine(_reg(5, 11), "20990101", terms=["Kostengutsprache"])["entries"] if e["lang"] == "fr")
    assert fr2["preferred"] == "accord de financement" and fr2["house"]                  # the data decides, not a list
    assert [v["text"] for v in fr2["variants"]] == ["garantie de prise en charge"]
    fr3 = next(e for e in T.mine(_reg(10, 10), "20990101", terms=["Kostengutsprache"])["entries"] if e["lang"] == "fr")
    assert not fr3["house"] and fr3["share"] == 0.5 and "no dominant rendering" in fr3["note"]  # no majority: no house rendering


def test_tokens_keep_hyphen_compounds_and_split_elisions():
    assert T.toks("l’assureur-maladie, et l'assureur maladie") == ["l'", "assureur-maladie", "|", "et", "l'", "assureur", "maladie"]
    assert T.surface("code d' indication") == "code d'indication"
    assert T._loose("assurance obligatoire des soins").search("par l'assurance obligatoire des soins.")
    assert not T._loose("assureur-maladie").search("l'assureur maladie")


def _v(L, de_old, de_new, old, draft, status="ready"):
    return dict(lang=L, de_old=de_old, de_new=de_new, tgt_old=old, draft=draft, status=status)


DE0 = "Die gleichzeitige Therapie wird von der Grundversicherung nicht vergütet."
DE1 = "Die gleichzeitige Therapie wird von der obligatorischen Krankenpflegeversicherung nicht vergütet."


def test_advice_names_the_house_rendering_and_what_the_draft_wrote():
    old = "Le traitement combiné ne sera pas remboursé par l'assurance de base."
    A = T.advice(_v("fr", DE0, DE1, old, "Le traitement combiné ne sera pas remboursé par l'assurance obligatoire de maladie."))
    assert [a["preferred"] for a in A] == ["assurance obligatoire des soins"] and A[0]["wrote"] == "assurance obligatoire de maladie"
    txt = T.advisory_text(A, "fr").replace("\u00a0", " ")
    assert txt.startswith("Terme maison pour « obligatorische Krankenpflegeversicherung »") and "le brouillon écrit « assurance obligatoire de maladie »" in txt
    assert "(33 limitations)" in txt.replace(" ", " ")
    it = T.advisory_text(T.advice(_v("it", DE0, DE1, "La terapia non sarà rimborsata dall'assicurazione di base.",
                                     "La terapia non sarà rimborsata dall'assicurazione obbligatoria di malattia.")), "it")
    assert it.startswith("Termine in uso all'UFSP per «obligatorische Krankenpflegeversicherung»: «assicurazione obbligatoria delle cure medico-sanitarie»")
    # the house rendering (inflected too) -> nothing; a variant only carried over from the old text -> nothing
    assert T.advice(_v("fr", DE0, DE1, old, "Le traitement ne sera pas remboursé par l'assurance obligatoire des soins.")) == []
    de = "Die Behandlung bedarf der Kostengutsprache durch den Krankenversicherer."
    kept = "Le traitement nécessite une garantie de prise en charge par l'assurance maladie."
    assert T.advice(_v("fr", de, de + " Neu.", kept, kept + " Nouveau.")) == []
    intro = T.advice(_v("fr", de, de + " Neu.", kept.replace("l'assurance maladie", "l'assureur-maladie"), kept + " Nouveau."))
    assert [(a["kind"], a["wrote"]) for a in intro] == [("variant", "assurance maladie")]
    assert T.advice(_v("fr", DE0, DE1, old, "", status="human")) == [] and T.advice(_v("rm", DE0, DE1, old, "x")) == []


def test_advisory_is_its_own_low_priority_note_and_changes_no_verdict():
    from gleichlaut import score
    from gleichlaut.emit import load, xliff
    meta, views = load("fresh166"); V = {v["key"]: v for v in views}
    F = score.load_jsonl(score.RUNS["fresh166"]["final"])
    for v in views:
        assert (v["status"] == "ready") == (not F[v["key"]]["guard_flag"]), v["key"]
        N = xliff.unit_notes(v)
        tb = [n for n in N if n[1] == "gleichlaut:termbase"]
        assert len(tb) == (1 if v["termbase"] else 0)
        assert len([n for n in N if n[1] in ("gleichlaut:finding", "gleichlaut:divergence", "gleichlaut:model-numbers")]) <= 3
        if tb:
            assert tb[0][3] == "9" and tb[0][0] == "termbase" and [n[0] for n in N][-2:] in (["termbase", "checks"], ["tgt-old", "termbase"])
    v = V["wb032-it"]                                       # the 70B's one ready draft with an insurance-term fix
    assert v["status"] == "ready" and "assicurazione obbligatoria delle cure medico-sanitarie" in xliff.termbase_note(v)
    d = tempfile.mkdtemp(prefix="gl-tb-xlf-")
    from gleichlaut.emit import validate, xliff12
    for p in xliff.write([v], meta, d): assert validate.validate_xliff(p) == [], p
    for p in xliff12.write([v], meta, d): assert validate.validate_xliff12(p) == [], p


def test_measure_equals_the_committed_results():
    from gleichlaut import replay
    got = json.loads(json.dumps(T.measure()))
    assert replay._cmp(got, json.load(open(RES, encoding="utf-8"))) == []
    r = got["runs"]
    assert r["8b_q4_k_m"]["ready_minor"] == 29 and r["8b_q8_0"]["ready_minor"] == 23          # = m1_<build>.json
    assert all(x["ready_minor_with_advisory"] <= x["ready_minor"] <= x["ready_needs_fix"] <= x["ready"] for x in r.values())


if __name__ == "__main__":
    fs = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    for n, f in fs: f(); print("ok", n)
