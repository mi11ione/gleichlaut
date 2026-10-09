"""XLIFF 2.1 for translators' tools: one file per target language (srcLang de-CH, trgLang fr-CH / it-CH), one unit per
draft, source = the new German text, target = the draft.

Verdict -> segment state (XLIFF 2.1 has only initial | translated | reviewed | final; there is no needs-review):
  ready   -> state="translated" subState="gleichlaut:ready"    (guards passed; a translator still reviews it)
  flagged -> state="initial"    subState="gleichlaut:flagged"  (the draft is a starting point, not a translation)
subState is the spec's slot for user-defined status ("prefix:value"; the spec requires state to be set explicitly with it).
Numbers code placed in the target are <mrk translate="no" type="gleichlaut:code-number"> (Translate Annotation + a
custom type); a number the model wrote itself would be type="gleichlaut:model-number" and stay translatable.
Unit <notes> carry the verdict, the guard findings, the guards' complaint and, as context, the old German and the old
target text, and the guard findings as one plain sentence each in the target language (category gleichlaut:finding).
Items routed to a translator (German rewritten > 60%, records status "human") get no target: state="initial"
subState="gleichlaut:human".
write(..., decisions=...): the reviewer's decisions from the review page (JSON export) applied to the same units: accepted drafts
(as is or edited) -> state="reviewed" (or "final" with final=True), subState gleichlaut:accepted | gleichlaut:accepted-edited,
target = the accepted text; sent back -> state="initial" subState="gleichlaut:sent-back" with the reason as a note.
<originalData> is not used for context: it holds only the native data of inline codes (<data> elements
referenced by dataRef), so context there would be invalid use."""
import os
import xml.etree.ElementTree as ET
from . import fhir

NS = "urn:oasis:names:tc:xliff:document:2.0"
ET.register_namespace("", NS)
STATE = {"ready": ("translated", "gleichlaut:ready"), "flagged": ("initial", "gleichlaut:flagged"), "human": ("initial", "gleichlaut:human")}
VERDICT = {"ready": "ready (guards passed)", "flagged": "flagged (a guard failed; see below)",
           "human": "routed to a translator (German rewritten > 60%): no machine draft"}
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


def _target(seg, v, text=None):
    """Target with every number wrapped in an annotation marker; ids t1.. are unique in the unit (spec: 't' prefix).
    text: a reviewer's edited text instead of the draft (then no number markers: their provenance is the reviewer's)."""
    t = ET.SubElement(seg, _q("target")); s = v["draft"] if text is None else text; pos = 0; last = None
    for i, (a, b, txt, who, slot) in enumerate(v["numbers"] if text is None else [], 1):
        chunk = s[pos:a]
        if last is None: t.text = chunk
        else: last.tail = chunk
        attrs = {"id": f"t{i}", "type": f"gleichlaut:{who}-number"}
        if who == "code": attrs["translate"] = "no"
        if slot: attrs["value"] = slot
        last = ET.SubElement(t, _q("mrk"), attrs); last.text = txt; pos = b
    if last is None: t.text = s
    else: last.tail = s[pos:]


def finding_text(f, lang):
    """One finding as a note: '[guard name] sentence' (+ the correction remark when the finding is caused by the draft
    correcting a pre-existing divergence)."""
    from . import explain
    return ((f"[{f['gname']}] " if f["gname"] else "") + f["text"]
            + (f" ({explain.corr_note(lang)})" if f["corrects"] and f["gid"] != "corr" else ""))


def unit(file_el, v, dec=None, final=False):
    u = ET.SubElement(file_el, _q("unit"), {"id": v["key"], "name": v["cud_id"]})
    notes = ET.SubElement(u, _q("notes"))
    _note(notes, VERDICT[v["status"]], "gleichlaut:verdict", "verdict", "target", "1")
    if v.get("banner"): _note(notes, v["banner"], "gleichlaut:divergence", "divergence", "target", "1")
    for i, f in enumerate(v.get("findings", []), 1):
        _note(notes, finding_text(f, v["lang"]), "gleichlaut:finding", f"finding-{i}", "target", "1")
    if v["complaint"]: _note(notes, v["complaint"], "gleichlaut:complaint", "complaint", "target", "1")
    for gid, lab, state, detail in v["lights"]:
        if state == "fail": _note(notes, f"{lab}: {detail}", "gleichlaut:guard", f"guard-{gid}", "target", "2")
    _note(notes, v["de_old"], "context:previous-source", "de-old", "source", "5")
    _note(notes, v["tgt_old"], "context:previous-target", "tgt-old", "target", "5")
    _note(notes, f"{v['product']}; limitation {v['cud_id']}; SL {v['snap_old']} -> {v['snap_new']}", "context:product", "product", None, "5")
    state, sub = STATE[v["status"]]; text = None
    d = (dec or {}).get("decision")
    if d in ("accept", "accept-edited") and (v["draft"] or (dec.get("text") or "").strip()):
        text = dec.get("text") if d == "accept-edited" and dec.get("text") else None
        state, sub = ("final" if final else "reviewed"), ("gleichlaut:accepted-edited" if text is not None else "gleichlaut:accepted")
    elif d == "send-back":
        state, sub = "initial", "gleichlaut:sent-back"
    if d:
        why = "; ".join(x for x in (dec.get("reason"), dec.get("note")) if x)
        _note(notes, f"reviewer: {d}" + (f" ({dec['at']})" if dec.get("at") else "") + (f": {why}" if why else ""),
              "gleichlaut:review", "review", "target", "1")
    seg = ET.SubElement(u, _q("segment"), {"id": "s1", "state": state, "subState": sub})
    ET.SubElement(seg, _q("source")).text = v["de_new"]
    if v["status"] != "human" or text is not None: _target(seg, v, text)
    return u


def document(views, meta, lang, decisions=None, final=False):
    ET.register_namespace("", NS)        # (xliff12 maps the default prefix to the 1.2 namespace; the map is global)
    root = ET.Element(_q("xliff"), {"version": "2.1", "srcLang": "de-CH", "trgLang": fhir.LANGS[lang]})
    f = ET.SubElement(root, _q("file"), {"id": "f1", "original": f"gleichlaut:{meta['run']}"})
    notes = ET.SubElement(f, _q("notes"))
    for cat, text in FILE_NOTES: _note(notes, text, f"gleichlaut:{cat}", cat)
    _note(notes, f"model {meta['model']}; {meta['pipeline']}; run {meta['run']}", "gleichlaut:provenance", "provenance")
    if decisions is not None:
        _note(notes, f"reviewed export: {sum(1 for v in views if v['lang'] == lang and v['key'] in decisions)} decided unit(s)",
              "gleichlaut:review", "review")
    for v in views:
        if v["lang"] == lang: unit(f, v, (decisions or {}).get(v["key"]), final)
    return ET.ElementTree(root)


def write(views, meta, out_dir, decisions=None, final=False):
    """-> [paths]: out_dir/gleichlaut-<run>-de-CH_<trg>.xlf per target language present (…-reviewed.xlf with decisions)."""
    os.makedirs(out_dir, exist_ok=True); paths = []
    for lang in fhir.LANGS:
        if not any(v["lang"] == lang for v in views): continue
        tail = "-reviewed" if decisions is not None else ""
        p = os.path.join(out_dir, f"gleichlaut-{meta['run']}-de-CH_{fhir.LANGS[lang]}{tail}.xlf")
        document(views, meta, lang, decisions, final).write(p, encoding="utf-8", xml_declaration=True); paths.append(p)   # no indent: mixed content
    return paths


def read_decisions(path, meta=None):
    """The review page's JSON export -> {key: decision}. Refuses a file exported from a different run."""
    import json
    d = json.load(open(path, encoding="utf-8"))
    if meta and d.get("run_sha256") and d["run_sha256"] != meta["run_sha256"]:
        raise SystemExit(f"decisions {path}: exported from outputs sha256 {d['run_sha256'][:12]}, not {meta['run_sha256'][:12]}")
    return d.get("decisions", d)
