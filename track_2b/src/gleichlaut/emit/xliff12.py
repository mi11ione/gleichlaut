"""XLIFF 1.2 (strict) for CAT tools that read 1.2 only (many do; whether STAR Transit NXT imports XLIFF 2.1 is
unverified, 1.2 is the safe exchange format). One file per target language, one <trans-unit> per item:
  source = the new German text, target = the draft (a pre-translation the translator edits in place),
  target state: ready -> "translated", flagged -> "needs-review-translation" (both in the 1.2 state value list);
  items routed to a translator (no draft) carry no <target>.
  Numbers placed by code are <mrk mtype="protected"> (1.2's "do not translate" marker; <ph> is for native codes, not text),
  in the source as well; a number the model wrote itself stays unmarked and translatable, with a note.
  The part of the new German the change inserted or rewrote is <mrk mtype="x-changed"> in the source (1.2's extension
  value syntax x-...; protected numbers nest inside it).
  <note>s (annotates target / source), all in the target language, are the notes of XLIFF 2.1 (xliff.unit_notes): the
  verdict, at most three plain reasons without internal codes, the product and German change, the old German and the old
  target, the termbase advisory when there is one (priority="9"), and one note from="gleichlaut-checks" priority="10" with the remaining reasons and the raw guard output; <alt-trans alttranstype="previous-version"> holds the old German -> old target pair so the
  CAT tool shows the previous version beside the draft.
  Segmentation: the same segments as XLIFF 2.1 (segment.beads: aligned sentences, very short segments such as a lone
  code number merged into the previous one), written the 1.2 way: <seg-source> and <target> each hold one
  <mrk mtype="seg" mid="k"> per segment, with matching mids; <source> keeps the whole new German text.
Validated against the OASIS XLIFF 1.2 strict XSD (data/schemas/xliff-1.2/) by validate.validate_xliff12."""
import os
import xml.etree.ElementTree as ET
from .. import __version__, core
from . import fhir, segment, xliff

NS = "urn:oasis:names:tc:xliff:document:1.2"
XMLNS = "http://www.w3.org/XML/1998/namespace"
STATE = {"ready": "translated", "flagged": "needs-review-translation"}


def _q(t): return f"{{{NS}}}{t}"


def _source_spans(s):
    return [(m.start(), m.end()) for m in core.gl2.NUMRX.finditer(s)]


def _note(tu, text, annotates="general", priority=None, frm="gleichlaut"):
    n = ET.SubElement(tu, _q("note"), {k: v for k, v in (("from", frm), ("annotates", annotates), ("priority", priority)) if v})
    n.text = text


def _src_marks(el, src, a, b, ch, nums, lang):
    """el gets src[a:b]: x-changed spans with the protected numbers nested inside (and protected numbers outside)."""
    outer = sorted([(x, y, "c") for x, y in ch] + [(x, y, "n") for x, y in nums if not any(c0 <= x and y <= c1 for c0, c1 in ch)])
    num_c, chg_c = xliff.nt(lang, "code_number"), xliff.nt(lang, "changed")

    def mk(span):
        return "mrk", ({"mtype": "x-changed", "comment": chg_c} if span[2] == "c" else {"mtype": "protected", "comment": num_c})
    xliff.inline(el, src, a, b, outer, mk, _q)
    for m in [m for m in el if m.get("mtype") == "x-changed"]:          # numbers inside a changed span
        t = m.text or ""; m.text = ""
        xliff.inline(m, t, 0, len(t), _source_spans(t), lambda sp: ("mrk", {"mtype": "protected", "comment": num_c}), _q)


def _source(tu, v, lang, beads):
    """source = the whole new German; seg-source = the same text, one <mrk mtype="seg"> per segment."""
    src = v["de_new"]; ch, nums = segment.changed(v["de_old"], src), _source_spans(src)
    _src_marks(ET.SubElement(tu, _q("source"), {f"{{{XMLNS}}}lang": "de-CH"}), src, 0, len(src), ch, nums, lang)
    ss = ET.SubElement(tu, _q("seg-source"), {f"{{{XMLNS}}}lang": "de-CH"}); last = None
    for k, (a0, a1, _, _) in enumerate(beads, 1):
        last = ET.SubElement(ss, _q("mrk"), {"mtype": "seg", "mid": str(k)})
        _src_marks(last, src, a0, a1, ch, nums, lang)


def _target(t, v, beads, lang):
    """target = the draft, one <mrk mtype="seg"> per segment (mids as in seg-source), code numbers protected inside."""
    out = v["draft"]; code = [(a, b) for a, b, _, who, _ in v["numbers"] if who == "code"]; num_c = xliff.nt(lang, "code_number")
    for k, (_, _, b0, b1) in enumerate(beads, 1):
        m = ET.SubElement(t, _q("mrk"), {"mtype": "seg", "mid": str(k)})
        xliff.inline(m, out, b0, b1, code, lambda sp: ("mrk", {"mtype": "protected", "comment": num_c}), _q)


def beads_of(v):
    """The unit's segments, as in XLIFF 2.1 (segment.beads)."""
    if v["status"] == "human": return segment.beads(v["de_new"])
    return segment.beads(v["de_new"], v["draft"], [(a, b) for a, b, *_ in v["numbers"]])


def trans_unit(body, v):
    lang = fhir.LANGS[v["lang"]]; L = v["lang"]
    tu = ET.SubElement(body, _q("trans-unit"), {"id": v["key"], "resname": v["cud_id"], "approved": "no",
                                                 f"{{{XMLNS}}}space": "preserve"})
    B = beads_of(v)
    _source(tu, v, L, B)
    if v["status"] != "human":
        t = ET.SubElement(tu, _q("target"), {"state": STATE[v["status"]], f"{{{XMLNS}}}lang": lang})
        _target(t, v, B, L)
    for nid, cat, ap, pr, text in xliff.unit_notes(v, prev=True):           # the same notes as XLIFF 2.1
        _note(tu, text, {None: "general"}.get(ap, ap), pr, "gleichlaut-checks" if nid == "checks" else "gleichlaut")
    alt = ET.SubElement(tu, _q("alt-trans"), {"alttranstype": "previous-version", "origin": "SL previous version", "tool-id": "gleichlaut"})
    ET.SubElement(alt, _q("source"), {f"{{{XMLNS}}}lang": "de-CH"}).text = v["de_old"]
    ET.SubElement(alt, _q("target"), {f"{{{XMLNS}}}lang": lang}).text = v["tgt_old"]
    return tu


def document(views, meta, lang):
    ET.register_namespace("", NS)
    root = ET.Element(_q("xliff"), {"version": "1.2"})
    f = ET.SubElement(root, _q("file"), {"original": f"gleichlaut:{meta['run']}", "source-language": "de-CH",
                                         "target-language": fhir.LANGS[lang], "datatype": "plaintext", "tool-id": "gleichlaut"})
    h = ET.SubElement(f, _q("header"))
    ET.SubElement(h, _q("tool"), {"tool-id": "gleichlaut", "tool-name": "Gleichlaut", "tool-version": __version__,
                                  "tool-company": "Gleichlaut"})
    for text in (xliff.nt(lang, "about12"), xliff.nt(lang, "states12"), xliff.provenance_note(meta, lang)):
        ET.SubElement(h, _q("note"), {"from": "gleichlaut"}).text = text
    body = ET.SubElement(f, _q("body"))
    for v in views:
        if v["lang"] == lang: trans_unit(body, v)
    return ET.ElementTree(root)


def write(views, meta, out_dir):
    """-> [paths]: out_dir/gleichlaut-<run>-de-CH_<trg>.xliff12.xlf per target language present."""
    os.makedirs(out_dir, exist_ok=True); paths = []
    for lang in fhir.LANGS:
        if not any(v["lang"] == lang for v in views): continue
        p = os.path.join(out_dir, f"gleichlaut-{meta['run']}-de-CH_{fhir.LANGS[lang]}.xliff12.xlf")
        document(views, meta, lang).write(p, encoding="utf-8", xml_declaration=True); paths.append(p)
    return paths
