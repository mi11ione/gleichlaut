"""XLIFF 2.1 for translators' tools: one file per target language (srcLang de-CH, trgLang fr-CH / it-CH), one unit per
draft, source = the new German text, target = the draft.

Verdict -> segment state (XLIFF 2.1 has only initial | translated | reviewed | final; there is no needs-review):
  ready   -> state="translated" subState="gleichlaut:ready"    (guards passed; a translator still reviews it)
  flagged -> state="initial"    subState="gleichlaut:flagged"  (the draft is a starting point, not a translation)
subState is the spec's slot for user-defined status ("prefix:value"; the spec requires state to be set explicitly with it).
Numbers code placed in the target are <mrk translate="no" type="gleichlaut:code-number"> (Translate Annotation + a
custom type); a number the model wrote itself would be type="gleichlaut:model-number" and stay translatable.
Unit <notes> carry the verdict, the guard findings, the guards' complaint and, as context, the old German and the old
target text. <originalData> is not used for context: it holds only the native data of inline codes (<data> elements
referenced by dataRef), so context there would be invalid use."""
import os
import xml.etree.ElementTree as ET
from . import fhir

NS = "urn:oasis:names:tc:xliff:document:2.0"
ET.register_namespace("", NS)
STATE = {"ready": ("translated", "gleichlaut:ready"), "flagged": ("initial", "gleichlaut:flagged")}
FILE_NOTES = [
    ("about", "Machine drafts of amended SL limitation texts (BAG Spezialitaetenliste). Source = new German text; target = "
              "Gleichlaut draft. Numbers marked gleichlaut:code-number (translate=no) were placed by code from the German; "
              "gleichlaut:model-number marks a number the model wrote itself (check it)."),
    ("states", "state=translated + subState=gleichlaut:ready: every frozen guard passed, review and accept. "
               "state=initial + subState=gleichlaut:flagged: a guard failed, see the unit notes; the target is a starting point.")]


def _q(t): return f"{{{NS}}}{t}"


def _note(parent, text, category, nid=None, applies=None, priority=None):
    n = ET.SubElement(parent, _q("note"), {k: v for k, v in (("id", nid), ("category", category), ("appliesTo", applies),
                                                              ("priority", priority)) if v})
    n.text = text
    return n


def _target(seg, v):
    """Target with every number wrapped in an annotation marker; ids t1.. are unique in the unit (spec: 't' prefix)."""
    t = ET.SubElement(seg, _q("target")); s = v["draft"]; pos = 0; last = None
    for i, (a, b, txt, who, slot) in enumerate(v["numbers"], 1):
        chunk = s[pos:a]
        if last is None: t.text = chunk
        else: last.tail = chunk
        attrs = {"id": f"t{i}", "type": f"gleichlaut:{who}-number"}
        if who == "code": attrs["translate"] = "no"
        if slot: attrs["value"] = slot
        last = ET.SubElement(t, _q("mrk"), attrs); last.text = txt; pos = b
    if last is None: t.text = s
    else: last.tail = s[pos:]


def unit(file_el, v):
    u = ET.SubElement(file_el, _q("unit"), {"id": v["key"], "name": v["cud_id"]})
    notes = ET.SubElement(u, _q("notes"))
    _note(notes, f"{v['status']}" + (" (guards passed)" if v["status"] == "ready" else " (a guard failed; see below)"),
          "gleichlaut:verdict", "verdict", "target", "1")
    if v["complaint"]: _note(notes, v["complaint"], "gleichlaut:complaint", "complaint", "target", "1")
    for gid, lab, state, detail in v["lights"]:
        if state == "fail": _note(notes, f"{lab}: {detail}", "gleichlaut:guard", f"guard-{gid}", "target", "2")
    _note(notes, v["de_old"], "context:previous-source", "de-old", "source", "5")
    _note(notes, v["tgt_old"], "context:previous-target", "tgt-old", "target", "5")
    _note(notes, f"{v['product']}; limitation {v['cud_id']}; SL {v['snap_old']} -> {v['snap_new']}", "context:product", "product", None, "5")
    state, sub = STATE[v["status"]]
    seg = ET.SubElement(u, _q("segment"), {"id": "s1", "state": state, "subState": sub})
    ET.SubElement(seg, _q("source")).text = v["de_new"]
    _target(seg, v)
    return u


def document(views, meta, lang):
    root = ET.Element(_q("xliff"), {"version": "2.1", "srcLang": "de-CH", "trgLang": fhir.LANGS[lang]})
    f = ET.SubElement(root, _q("file"), {"id": "f1", "original": f"gleichlaut:{meta['run']}"})
    notes = ET.SubElement(f, _q("notes"))
    for cat, text in FILE_NOTES: _note(notes, text, f"gleichlaut:{cat}", cat)
    _note(notes, f"model {meta['model']}; {meta['pipeline']}; run {meta['run']}", "gleichlaut:provenance", "provenance")
    for v in views:
        if v["lang"] == lang: unit(f, v)
    return ET.ElementTree(root)


def write(views, meta, out_dir):
    """-> [paths]: out_dir/gleichlaut-<run>-de-CH_<trg>.xlf per target language present."""
    os.makedirs(out_dir, exist_ok=True); paths = []
    for lang in fhir.LANGS:
        if not any(v["lang"] == lang for v in views): continue
        p = os.path.join(out_dir, f"gleichlaut-{meta['run']}-de-CH_{fhir.LANGS[lang]}.xlf")
        document(views, meta, lang).write(p, encoding="utf-8", xml_declaration=True); paths.append(p)   # no indent: mixed content
    return paths
