"""XLIFF 1.2 (strict) for CAT tools that read 1.2 only (many do; whether STAR Transit NXT imports XLIFF 2.1 is
unverified, 1.2 is the safe exchange format). One file per target language, one <trans-unit> per item:
  source = the new German text, target = the draft (a pre-translation the translator edits in place),
  target state: ready -> "translated", flagged -> "needs-review-translation" (both in the 1.2 state value list);
  items routed to a translator (no draft) carry no <target>.
  Numbers placed by code are <mrk mtype="protected"> (1.2's "do not translate" marker; <ph> is for native codes, not text),
  in the source as well; a number the model wrote itself stays unmarked and translatable, with a note.
  <note>s (annotates target / source) carry the verdict, each guard finding as one sentence in the target language, the
  divergence notice, the old German and the old target; <alt-trans alttranstype="previous-version"> holds the old
  German -> old target pair so the CAT tool shows the previous version beside the draft.
Validated against the OASIS XLIFF 1.2 strict XSD (data/schemas/xliff-1.2/) by validate.validate_xliff12."""
import os
import xml.etree.ElementTree as ET
from .. import __version__, core
from . import fhir, xliff

NS = "urn:oasis:names:tc:xliff:document:1.2"
XMLNS = "http://www.w3.org/XML/1998/namespace"
STATE = {"ready": "translated", "flagged": "needs-review-translation"}


def _q(t): return f"{{{NS}}}{t}"


def _marked(parent, text, spans, comment):
    """parent.text/children = text with each (start, end) span wrapped in <mrk mtype="protected">."""
    pos, last = 0, None
    for a, b in spans:
        chunk = text[pos:a]
        if last is None: parent.text = chunk
        else: last.tail = chunk
        last = ET.SubElement(parent, _q("mrk"), {"mtype": "protected", "comment": comment})
        last.text = text[a:b]; pos = b
    if last is None: parent.text = text
    else: last.tail = text[pos:]


def _source_spans(s):
    return [(m.start(), m.end()) for m in core.gl2.NUMRX.finditer(s)]


def _note(tu, text, annotates="general", priority=None):
    n = ET.SubElement(tu, _q("note"), {k: v for k, v in (("from", "gleichlaut"), ("annotates", annotates), ("priority", priority)) if v})
    n.text = text


def trans_unit(body, v):
    lang = fhir.LANGS[v["lang"]]
    tu = ET.SubElement(body, _q("trans-unit"), {"id": v["key"], "resname": v["cud_id"], "approved": "no",
                                                 f"{{{XMLNS}}}space": "preserve"})
    _marked(ET.SubElement(tu, _q("source"), {f"{{{XMLNS}}}lang": "de-CH"}), v["de_new"], _source_spans(v["de_new"]), "number")
    if v["status"] != "human":
        t = ET.SubElement(tu, _q("target"), {"state": STATE[v["status"]], f"{{{XMLNS}}}lang": lang})
        _marked(t, v["draft"], [(a, b) for a, b, _, who, _ in v["numbers"] if who == "code"],
                "number placed by code from the German")
    verdict = {"ready": "Gleichlaut: ready, every frozen guard passed; review and accept.",
               "flagged": "Gleichlaut: flagged, a guard named a problem (see the notes); the target is a starting point.",
               "human": "Gleichlaut: routed to a translator (German rewritten > 60%); no machine draft."}[v["status"]]
    _note(tu, verdict, "target", "1")
    if v.get("banner"): _note(tu, v["banner"], "target", "1")
    for f in v.get("findings", []):
        _note(tu, xliff.finding_text(f, v["lang"]), "target", "2")
    model = [t for _, _, t, who, _ in v["numbers"] if who == "model"]
    if model: _note(tu, "Numbers written by the model itself (check them): " + ", ".join(model), "target", "1")
    _note(tu, "Previous German: " + v["de_old"], "source", "5")
    _note(tu, "Previous target: " + v["tgt_old"], "target", "5")
    _note(tu, f"{v['product']}; limitation {v['cud_id']}; SL {v['snap_old']} -> {v['snap_new']}", "general", "5")
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
                                  "tool-company": "Hack Apertus track 2B"})
    for text in ("Machine drafts of amended SL limitation texts (BAG Spezialitaetenliste). Source = new German text; "
                 "target = Gleichlaut draft (pre-translation). mrk mtype=protected = number placed by code from the German.",
                 "state=translated: every frozen guard passed. state=needs-review-translation: a guard named a problem "
                 "(see the unit notes). No target: routed to a translator.",
                 f"model {meta['model']}; {meta['pipeline']}; run {meta['run']}"):
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
