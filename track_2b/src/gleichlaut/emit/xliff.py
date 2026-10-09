"""XLIFF 2.1 for translators' tools: one file per target language (srcLang de-CH, trgLang fr-CH / it-CH), one unit per
limitation draft (id = item key, name = limitation code), one <segment> per sentence: source = a sentence (or 2-3) of the
new German text, target = the aligned sentence(s) of the draft (emit/segment.py; the segments concatenate back to both
texts exactly).

Verdict -> segment state (XLIFF 2.1 has only initial | translated | reviewed | final; there is no needs-review):
  ready   -> state="translated" subState="gleichlaut:ready"    (every guard passed; checked by code, not by a person)
  flagged -> state="translated" subState="gleichlaut:flagged"  (a guard named a problem; the target is the draft to correct.
             Not "initial": CAT tools may pre-translate over initial segments and the draft would be lost.)
  human   -> state="initial"    subState="gleichlaut:human"    (German rewritten > 60%: no target)
subState is the spec's slot for user-defined status ("prefix:value"; the spec requires state to be set explicitly with it).
Inline annotations (<mrk>, Annotations module of the core):
  source: type="gleichlaut:changed" marks the part of the new German the change inserted or rewrote (ids c1..).
  target: numbers code placed are type="gleichlaut:code-number" translate="no"; a number the model wrote itself is
          type="gleichlaut:model-number" and stays translatable (ids t1..).
Unit <notes>, all in the target language (FR / IT): the verdict, a pre-existing problem of the old text, the German change,
one plain sentence per guard finding (the ones a fixed rule marks as probably fine last, priority 3, with the rule; see
emit/triage.py), numbers written by the model, the old German and old target text, product and limitation code. The raw
guard output stays in the FHIR Provenance.
write(..., decisions=...): the reviewer's decisions from the review page (JSON export) applied to the same units: accepted
drafts (as is or edited) -> state="reviewed" (or "final" with final=True), subState gleichlaut:accepted |
gleichlaut:accepted-edited, target = the accepted text; sent back -> state="initial" subState="gleichlaut:sent-back".
<originalData> is not used for context: it holds only the native data of inline codes (<data> elements referenced by
dataRef), so context there would be invalid use."""
import os
import xml.etree.ElementTree as ET
from . import fhir, model_label, segment, triage

NS = "urn:oasis:names:tc:xliff:document:2.0"
ET.register_namespace("", NS)
STATE = {"ready": ("translated", "gleichlaut:ready"), "flagged": ("translated", "gleichlaut:flagged"), "human": ("initial", "gleichlaut:human")}

# Every note text in the target language. (French spacing: explain._fr adds the non-breaking spaces.)
NOTE = {
 "fr": {"ready": "Prêt : tous les contrôles automatiques sont passés. Vérifié par le code, pas encore par une personne : à réviser.",
        "flagged": "Signalé : un contrôle automatique a relevé un problème (voir les remarques). La cible est le brouillon, à corriger.",
        "human": "Confié à un traducteur : l'allemand a été réécrit à plus de 60 % ; pas de brouillon automatique.",
        "about": "Brouillons automatiques des textes de limitation modifiés de la liste des spécialités (LS, OFSP). Source = nouveau "
                 "texte allemand, un segment par phrase ; cible = brouillon Gleichlaut. Dans la source, gleichlaut:changed marque la "
                 "partie que l'allemand a changée. Dans la cible, gleichlaut:code-number (translate=no) marque un nombre placé par le "
                 "code à partir de l'allemand, gleichlaut:model-number un nombre écrit par le modèle (à vérifier).",
        "states": "state=translated + subState=gleichlaut:ready : tous les contrôles sont passés, réviser et accepter. "
                  "state=translated + subState=gleichlaut:flagged : un contrôle a relevé un problème, voir les remarques de l'unité ; "
                  "la cible est le brouillon à corriger, ne pas la remplacer par une prétraduction. "
                  "state=initial + subState=gleichlaut:human : pas de brouillon, à traduire.",
        "about12": "Brouillons automatiques des textes de limitation modifiés de la liste des spécialités (LS, OFSP). Source = "
                   "nouveau texte allemand ; cible = brouillon Gleichlaut (prétraduction). mrk mtype=x-changed : partie que "
                   "l'allemand a changée ; mrk mtype=protected : nombre placé par le code à partir de l'allemand.",
        "states12": "state=translated : tous les contrôles automatiques sont passés. state=needs-review-translation : un contrôle a "
                    "relevé un problème (voir les remarques de l'unité). Pas de cible : confié à un traducteur.",
        "prov": "Modèle {model} ; {pipeline} ; série {run}",
        "prov_run": "Série enregistrée {run} (modèle non indiqué dans les enregistrements) ; {pipeline}",
        "product": "{product} ; limitation {code} ; LS {old} → {new}",
        "prev_de": "Allemand précédent : {t}", "prev_tgt": "Texte français précédent : {t}",
        "change": "Changement allemand : {t}", "fine": "probablement sans problème, règle {r} : {why}",
        "model_nums": "Nombres écrits par le modèle lui-même (à vérifier) : {x}",
        "review": "Révision : {d}", "reviewed": "Export révisé : {n} unité(s) décidée(s)",
        "accept": "accepté", "accept-edited": "accepté modifié", "send-back": "renvoyé",
        "code_number": "nombre placé par le code à partir de l'allemand", "changed": "partie changée par l'allemand",
        "T1": "mot français bien formé, seulement absent du vocabulaire connu",
        "T2": "« ist … zu » allemand rendu par « doit être … »",
        "T3": "les nombres changent exactement comme dans l'allemand",
        "T4": "chiffre romain ou sigle, pas de l'allemand",
        "T5": "seuls des nombres changent hors du passage modifié, exactement ceux que l'allemand change ailleurs",
        "T6": "le changement allemand n'est qu'orthographique (umlaut, trait d'union, majuscule, ponctuation, terminaison)",
        "T7": "négation comptée comme un lecteur la compte (« nicht- » préfixe, « ne … pas » une seule fois) : le compte suit l'allemand",
        "T8": "mêmes valeurs ajoutées et retirées des deux côtés, seul le nombre d'occurrences diffère",
        "product_nodate": "{product} ; limitation {code}"},
 "it": {"ready": "Pronta: tutti i controlli automatici superati. Verificata dal codice, non ancora da una persona: da rivedere.",
        "flagged": "Segnalata: un controllo automatico ha rilevato un problema (vedi le note). La destinazione è la bozza, da correggere.",
        "human": "Affidata a un traduttore: il tedesco è stato riscritto per oltre il 60%; nessuna bozza automatica.",
        "about": "Bozze automatiche dei testi di limitazione modificati dell'elenco delle specialità (ES, UFSP). Fonte = nuovo testo "
                 "tedesco, un segmento per frase; destinazione = bozza Gleichlaut. Nella fonte, gleichlaut:changed marca la parte "
                 "modificata dal tedesco. Nella destinazione, gleichlaut:code-number (translate=no) marca un numero inserito dal codice "
                 "a partire dal tedesco, gleichlaut:model-number un numero scritto dal modello (da verificare).",
        "states": "state=translated + subState=gleichlaut:ready: tutti i controlli superati, rivedere e accettare. "
                  "state=translated + subState=gleichlaut:flagged: un controllo ha rilevato un problema, vedi le note dell'unità; "
                  "la destinazione è la bozza da correggere, non sostituirla con una pretraduzione. "
                  "state=initial + subState=gleichlaut:human: nessuna bozza, da tradurre.",
        "about12": "Bozze automatiche dei testi di limitazione modificati dell'elenco delle specialità (ES, UFSP). Fonte = "
                   "nuovo testo tedesco; destinazione = bozza Gleichlaut (pretraduzione). mrk mtype=x-changed: parte modificata "
                   "dal tedesco; mrk mtype=protected: numero inserito dal codice a partire dal tedesco.",
        "states12": "state=translated: tutti i controlli automatici superati. state=needs-review-translation: un controllo ha "
                    "rilevato un problema (vedi le note dell'unità). Nessuna destinazione: affidata a un traduttore.",
        "prov": "Modello {model}; {pipeline}; serie {run}",
        "prov_run": "Serie registrata {run} (modello non indicato nelle registrazioni); {pipeline}",
        "product": "{product}; limitazione {code}; ES {old} → {new}",
        "prev_de": "Tedesco precedente: {t}", "prev_tgt": "Testo italiano precedente: {t}",
        "change": "Modifica tedesca: {t}", "fine": "probabilmente in ordine, regola {r}: {why}",
        "model_nums": "Numeri scritti dal modello stesso (da verificare): {x}",
        "review": "Revisione: {d}", "reviewed": "Esportazione rivista: {n} unità decise",
        "accept": "accettata", "accept-edited": "accettata modificata", "send-back": "rinviata",
        "code_number": "numero inserito dal codice a partire dal tedesco", "changed": "parte modificata dal tedesco",
        "T1": "parola italiana ben formata, solo assente dal vocabolario noto",
        "T2": "«ist … zu» tedesco reso con «deve essere …»",
        "T3": "i numeri cambiano esattamente come nel tedesco",
        "T4": "numero romano o sigla, non tedesco",
        "T5": "cambiano solo numeri fuori dal passo modificato, esattamente quelli che il tedesco cambia altrove",
        "T6": "la modifica tedesca è solo ortografica (umlaut, trattino, maiuscola, punteggiatura, desinenza)",
        "T7": "negazione contata come la conta un lettore («nicht-» prefisso, «ne … pas» una volta sola): il conteggio segue il tedesco",
        "T8": "stessi valori aggiunti e tolti da entrambe le parti, cambia solo il numero di occorrenze",
        "product_nodate": "{product}; limitazione {code}"}}


def nt(lang, k, **kw):
    from . import explain
    s = NOTE[lang][k].format(**kw)
    return explain._fr(s) if lang == "fr" else s


def review_text(lang, d, at=None, why=""):
    from . import explain
    s = NOTE[lang]["review"].format(d=NOTE[lang].get(d, d)) + (f" ({at})" if at else "") + (f": {why}" if why else "")
    return explain._fr(s) if lang == "fr" else s


def provenance_note(meta, lang):
    """'Modèle <id> ; <pipeline> ; série <run>', or 'Série enregistrée <run> (…)' when the records do not name the model."""
    if not meta.get("model_known", True): return nt(lang, "prov_run", run=meta["run"], pipeline=meta["pipeline"])
    return nt(lang, "prov", model=model_label(meta), pipeline=meta["pipeline"], run=meta["run"])


def _q(t): return f"{{{NS}}}{t}"


def _note(parent, text, category, nid=None, applies=None, priority=None):
    n = ET.SubElement(parent, _q("note"), {k: v for k, v in (("id", nid), ("category", category), ("appliesTo", applies),
                                                              ("priority", priority)) if v})
    n.text = text
    return n


def inline(parent, text, a, b, spans, make, q=_q):
    """parent gets text[a:b] with each span of `spans` (clipped to [a, b)) wrapped in an element from make(k, span)
    -> (tag, attrs); k counts from 1 across calls through make's own counter."""
    pos, last = a, None
    for s, e, *rest in spans:
        s, e = max(s, a), min(e, b)
        if s >= e: continue
        tag, attrs = make((s, e, *rest))
        chunk = text[pos:s]
        if last is None: parent.text = (parent.text or "") + chunk
        else: last.tail = chunk
        last = ET.SubElement(parent, q(tag), attrs); last.text = text[s:e]; pos = e
    if last is None: parent.text = (parent.text or "") + text[pos:b]
    else: last.tail = text[pos:b]


def finding_text(f, lang, rule=None):
    """One finding as a note: '[guard name] sentence' (+ the correction remark when the finding is caused by the draft
    correcting a pre-existing divergence; + 'probably fine, rule Tn: why' when a triage rule applies)."""
    from . import explain
    s = ((f"[{f['gname']}] " if f["gname"] else "") + f["text"]
         + (f" ({explain.corr_note(lang)})" if f["corrects"] and f["gid"] != "corr" else ""))
    if rule and lang in NOTE: s += f" ({nt(lang, 'fine', r=rule, why=NOTE[lang][rule])})"
    return s


def ordered_findings(v):
    """-> [(finding, rule or None)]: findings to check first, then the ones a triage rule marks probably fine."""
    F = list(zip(v.get("findings", []), triage.triage(v)))
    return [p for p in F if not p[1]] + [p for p in F if p[1]]


def change_summary(v, n=320):
    """Every change of the German as 'old → new' / '+ new' / '− old', joined by ' | ' (cut at n characters)."""
    import re
    from ..ui.build import diff
    parts, d, i = [], "", ""
    for s in diff(v["de_old"], v["de_new"]) + [["e", "x"]]:
        if s[0] == "e" and s[1].strip():
            if d or i:
                d, i = re.sub(r"\s+", " ", d).strip(), re.sub(r"\s+", " ", i).strip()
                parts.append(f"{d} → {i}" if d and i else f"+ {i}" if i else f"− {d}"); d = i = ""
            continue
        if s[0] == "d": d += " " + s[1]
        elif s[0] == "i": i += s[1]
    t = " | ".join(parts) or "—"
    return t if len(t) <= n else t[:n].rsplit(" ", 1)[0] + " …"


def product_note(v, lang):
    """'<product> ; limitation <code> ; LS <old> → <new>', without the LS part when either snapshot date is unknown."""
    o, n = v.get("snap_old"), v.get("snap_new")
    if o in (None, "", "?") or n in (None, "", "?"): return nt(lang, "product_nodate", product=v["product"], code=v["cud_id"])
    return nt(lang, "product", product=v["product"], code=v["cud_id"], old=date(o), new=date(n))


def date(s):
    """20260219 -> 19.02.2026 (other values unchanged)."""
    return f"{s[6:8]}.{s[4:6]}.{s[:4]}" if isinstance(s, str) and len(s) == 8 and s.isdigit() else (s or "?")


def unit(file_el, v, dec=None, final=False):
    L = v["lang"]
    u = ET.SubElement(file_el, _q("unit"), {"id": v["key"], "name": v["cud_id"]})
    notes = ET.SubElement(u, _q("notes"))
    _note(notes, nt(L, v["status"]), "gleichlaut:verdict", "verdict", "target", "1")
    if v.get("banner"): _note(notes, v["banner"], "gleichlaut:divergence", "divergence", "target", "1")
    _note(notes, nt(L, "change", t=change_summary(v)), "gleichlaut:change", "change", "source", "2")
    for i, (f, r) in enumerate(ordered_findings(v), 1):
        _note(notes, finding_text(f, L, r), "gleichlaut:finding", f"finding-{i}", "target", "3" if r else "1")
    model = [t for _, _, t, who, _ in v["numbers"] if who == "model"]
    if model: _note(notes, nt(L, "model_nums", x=", ".join(model)), "gleichlaut:model-numbers", "model-numbers", "target", "1")
    _note(notes, nt(L, "prev_de", t=v["de_old"]), "context:previous-source", "de-old", "source", "5")
    _note(notes, nt(L, "prev_tgt", t=v["tgt_old"]), "context:previous-target", "tgt-old", "target", "5")
    _note(notes, product_note(v, L), "context:product", "product", None, "5")
    state, sub = STATE[v["status"]]; text = None
    d = (dec or {}).get("decision")
    if d in ("accept", "accept-edited") and (v["draft"] or (dec.get("text") or "").strip()):
        text = dec.get("text") if d == "accept-edited" and dec.get("text") else None
        state, sub = ("final" if final else "reviewed"), ("gleichlaut:accepted-edited" if text is not None else "gleichlaut:accepted")
    elif d == "send-back":
        state, sub = "initial", "gleichlaut:sent-back"
    if d:
        why = "; ".join(x for x in (dec.get("reason"), dec.get("note")) if x)
        _note(notes, review_text(L, d, dec.get("at"), why), "gleichlaut:review", "review", "target", "1")
    segments(u, v, state, sub, text, with_target=v["status"] != "human" or text is not None)
    return u


def segments(u, v, state, sub, text=None, with_target=True):
    """One <segment> per aligned sentence bead. text: a reviewer's edited target (then no number markers)."""
    src = v["de_new"]; tgt = (v["draft"] if text is None else text) if with_target else ""
    nums = [(a, b, who, slot) for a, b, _, who, slot in v["numbers"]] if text is None and with_target else []
    beads = segment.beads(src, tgt if with_target else None, [(a, b) for a, b, *_ in nums])
    ch = segment.changed(v["de_old"], src); cnt = {"c": 0, "t": 0}

    def mk_changed(span):
        cnt["c"] += 1; return "mrk", {"id": f"c{cnt['c']}", "type": "gleichlaut:changed"}

    def mk_num(span):
        cnt["t"] += 1; who, slot = span[2], span[3]
        attrs = {"id": f"t{cnt['t']}", "type": f"gleichlaut:{who}-number"}
        if who == "code": attrs["translate"] = "no"
        if slot: attrs["value"] = slot
        return "mrk", attrs

    for k, (a0, a1, b0, b1) in enumerate(beads, 1):
        seg = ET.SubElement(u, _q("segment"), {"id": f"s{k}", "state": state, "subState": sub})
        inline(ET.SubElement(seg, _q("source")), src, a0, a1, ch, mk_changed)
        if with_target: inline(ET.SubElement(seg, _q("target")), tgt, b0, b1, nums, mk_num)


def document(views, meta, lang, decisions=None, final=False):
    ET.register_namespace("", NS)        # (xliff12 maps the default prefix to the 1.2 namespace; the map is global)
    root = ET.Element(_q("xliff"), {"version": "2.1", "srcLang": "de-CH", "trgLang": fhir.LANGS[lang]})
    f = ET.SubElement(root, _q("file"), {"id": "f1", "original": f"gleichlaut:{meta['run']}"})
    notes = ET.SubElement(f, _q("notes"))
    for cat in ("about", "states"): _note(notes, nt(lang, cat), f"gleichlaut:{cat}", cat)
    _note(notes, provenance_note(meta, lang), "gleichlaut:provenance", "provenance")
    if decisions is not None:
        _note(notes, nt(lang, "reviewed", n=sum(1 for v in views if v["lang"] == lang and v["key"] in decisions)),
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
