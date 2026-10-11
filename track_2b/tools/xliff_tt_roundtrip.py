"""Translation round trip through translate-toolkit (the open-source toolkit behind Pootle and Weblate): writes the fixtures
in tests/fixtures/xliff-roundtrip/ and prints what survived. Dev step, not part of `make run`; no model, no network.

  python3 -m venv /tmp/tt && /tmp/tt/bin/pip install translate-toolkit==3.20.0
  PYTHONPATH=src python3 -m gleichlaut emit --run q8_0 --n 10 --out /tmp/gl-emit          # the default 8B lane
  /tmp/tt/bin/python tools/xliff_tt_roundtrip.py /tmp/gl-emit/xliff tests/fixtures/xliff-roundtrip
  PYTHONPATH=src python3 -m gleichlaut xliff-import tests/fixtures/xliff-roundtrip/returned-tt-fr-CH.xliff12.xlf

The translator's actions on the FR files (translate.storage.xliff.xlifffile for 1.2, xliff2.Xliff2File for 2.1; text
edits through tt's rich_target, which keeps the inline <mrk> markup):
  wb000  edited and signed off. 1.2: the whole target replaced by one plain text (its <mrk mtype="seg"> segments gone),
         state signed-off, approved=yes. 2.1: segments s1 + s2 joined into one (on the store's lxml tree, as a CAT
         tool's join does), markapproved -> state reviewed
  wb001  edited, not signed off (1.2 needs-review-translation, 2.1 translated)
  wb002  edited, not signed off (1.2 translated; 2.1 segment s2 split into s2 + s3, s3 edited)
  wb003  unchanged, signed off (1.2 final + approved=yes; 2.1 state final on both segments, set on the element: tt has
         no API for final in 2.x)
  wb004  target cleared, needs-translation (1.2) / initial (2.1)
Then the returned 1.2 file goes through tt's gettext bridge, xliff2po -> PO -> po2xliff (returned-po2xliff-*.xlf)."""
import os, subprocess, sys, xml.etree.ElementTree as ET
import translate.__version__ as ttv
from translate.storage import xliff, xliff2
from translate.storage.placeables import StringElem

PIN = "3.20.0"
NS2 = "{urn:oasis:names:tc:xliff:document:2.0}"


def edit(u, a, b):
    """Replace a by b in the target text through tt's rich model (inline mrk elements kept)."""
    r = u.rich_target
    def walk(e):
        for i, s in enumerate(e.sub):
            if isinstance(s, str):
                if a in s: e.sub[i] = s.replace(a, b); return True
            elif walk(s): return True
        return False
    assert any(walk(x) for x in r), (u.getid(), a)
    u.rich_target = r


def clear(u): u.rich_target = [StringElem("")]


def cut(el, at, head):
    """Keep the text of el before (head) or from `at` (inline elements flattened: a split moves text, not markup)."""
    txt = "".join(el.itertext()); i = txt.index(at)
    for c in list(el): el.remove(c)
    el.text = txt[:i] if head else txt[i:]


def run12(src, dst):
    st = xliff.xlifffile.parsefile(src); U = {u.getid().split("\x04")[-1]: u for u in st.units}; S = xliff.xliffunit.statemap
    U["wb000-fr"].rich_target = [StringElem(U["wb000-fr"].target.replace("l'assurance maladie: ", "l'assureur-maladie : "))]
    U["wb000-fr"].set_state_n(S["signed-off"]); U["wb000-fr"].markapproved(True)
    edit(U["wb001-fr"], "contenant du platine", "à base de platine")
    edit(U["wb002-fr"], "par Osimertinib", "par osimertinib")
    U["wb003-fr"].set_state_n(S["final"]); U["wb003-fr"].markapproved(True)
    clear(U["wb004-fr"]); U["wb004-fr"].set_state_n(S["needs-translation"])
    open(dst, "wb").write(bytes(st))


def run2(src, dst):
    st = xliff2.Xliff2File.parsefile(src); S = {u.getid(): u for u in st.units}
    s1, s2 = S["wb000-fr::s1"].xmlelement, S["wb000-fr::s2"].xmlelement
    for tag in ("source", "target"):
        e1, e2 = s1.find(NS2 + tag), s2.find(NS2 + tag)
        if e2.text:
            if len(e1): e1[-1].tail = (e1[-1].tail or "") + e2.text
            else: e1.text = (e1.text or "") + e2.text
        for c in list(e2): e1.append(c)
    s2.getparent().remove(s2)
    st = xliff2.Xliff2File.parsestring(bytes(st)); S = {u.getid(): u for u in st.units}
    edit(S["wb000-fr::s1"], "l'assurance maladie: ", "l'assureur-maladie : "); S["wb000-fr::s1"].markapproved(True)
    edit(S["wb001-fr::s1"], "contenant du platine", "à base de platine")
    import copy
    seg = S["wb002-fr::s2"].xmlelement; new = copy.deepcopy(seg); new.set("id", "s3"); seg.addnext(new)
    for e, at in (("source", "ist an den"), ("target", "doit être")):
        cut(seg.find(NS2 + e), at, True); cut(new.find(NS2 + e), at, False)
    st = xliff2.Xliff2File.parsestring(bytes(st)); S = {u.getid(): u for u in st.units}
    edit(S["wb002-fr::s3"], "l'assurance maladie: ", "l'assureur-maladie : ")
    for sid in ("s1", "s2"):
        S[f"wb003-fr::{sid}"].xmlelement.set("state", "final")
        clear(S[f"wb004-fr::{sid}"]); S[f"wb004-fr::{sid}"].markfuzzy(True)
    open(dst, "wb").write(bytes(st))


def survived(a, b):
    """Stdlib comparison of the export and the tt-written return: ids, attributes, notes, German source, alt-trans."""
    A, B = ET.parse(a).getroot(), ET.parse(b).getroot(); ns = A.tag.split("}")[0] + "}"
    U = "unit" if A.get("version", "").startswith("2") else "trans-unit"
    ua, ub = ({u.get("id"): u for u in r.iter(ns + U)} for r in (A, B))
    sig = lambda u: [(e.tag, sorted(e.attrib.items()), (e.text or "").strip() if len(e) else e.text)
                     for at in u.iter(ns + "alt-trans") for e in at.iter()]
    notes = lambda r: [(n.attrib, n.text) for n in r.iter(ns + "note")]
    attrs = lambda u: {k: v for k, v in u.attrib.items() if k != "approved"}
    print(f"{os.path.basename(b)}: XLIFF {A.get('version')} -> {B.get('version')}; unit ids identical and in order: {list(ua) == list(ub)}; "
          f"unit attributes (id, name / resname) kept: {all(attrs(ua[k]) == attrs(ub[k]) for k in ua)}; "
          f"notes kept (file + units, text and attributes): {notes(A) == notes(B)}; "
          f"German source text kept: {all(''.join(''.join(s.itertext()) for s in ua[k].iter(ns + 'source')) == ''.join(''.join(s.itertext()) for s in ub[k].iter(ns + 'source')) for k in ua)}"
          + (f"; alt-trans kept: {all(sig(ua[k]) == sig(ub[k]) for k in ua)}" if U == "trans-unit" else
             f"; subState kept (every returned segment has one of its unit's exported values): "
             f"{all({s.get('subState') for s in ub[k].iter(ns + 'segment')} <= {s.get('subState') for s in ua[k].iter(ns + 'segment')} for k in ua)}"))


def main(src_dir, out_dir):
    assert ttv.sver == PIN, f"translate-toolkit {ttv.sver}, the fixtures were made with {PIN}"
    os.makedirs(out_dir, exist_ok=True)
    s12, s2 = (os.path.join(src_dir, f"gleichlaut-q8_0-de-CH_fr-CH{x}.xlf") for x in (".xliff12", ""))
    r12, r2 = (os.path.join(out_dir, f"returned-tt-fr-CH{x}.xlf") for x in (".xliff12", ""))
    run12(s12, r12); run2(s2, r2)
    bindir = os.path.dirname(sys.executable); po = "returned-fr-CH.po"          # relative: po2xliff writes it as file/@original
    subprocess.run([os.path.join(bindir, "xliff2po"), "--progress=none", "-i", os.path.basename(r12), "-o", po], check=True, cwd=out_dir)
    subprocess.run([os.path.join(bindir, "po2xliff"), "--progress=none", "-i", po, "-o", "returned-po2xliff-fr-CH.xliff12.xlf"],
                   check=True, cwd=out_dir)
    os.remove(os.path.join(out_dir, po))
    print(f"translate-toolkit {ttv.sver}")
    survived(s12, r12); survived(s2, r2)
    try:                                                   # the vendored OASIS XSDs (lxml), as in `make run`
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
        from gleichlaut.emit import validate
        for p, f in ((r12, validate.validate_xliff12), (r2, validate.validate_xliff)):
            e = f(p); print(f"{os.path.basename(p)}: {'valid' if not e else f'{len(e)} XSD errors, e.g. ' + e[0]}")
    except ImportError as e:
        print("XSD check skipped:", e)


if __name__ == "__main__":
    main(*sys.argv[1:3])
