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
Unit <notes>, all in the target language (FR / IT), see unit_notes(): the verdict; at most three reasons, the most
actionable first, in plain wording without internal codes (a pre-existing problem of the old text, guard findings,
numbers written by the model; the ones a fixed rule marks as probably fine last, priority 3, see emit/triage.py; a count
a triage rule calls probably fine never takes one of the three); product, limitation code and the German change; the old
German and old target text; one low-priority note (category gleichlaut:note, priority 8, not one of the three reasons)
with a deletion that mirrors the German's (a statement when the draft drops, one to one, the sentence that translates
the sentence the German drops; else worded as a question) and typography the draft introduced; when a sentence the draft
wrote departs from BAG's dominant wording of a fixed German sentence (data/termbase/house_sentences_*, gleichlaut.house),
one advisory note (category gleichlaut:house, priority 9); when the draft departs from BAG's house rendering of a German
term (data/termbase, gleichlaut.termbase), one advisory note (category gleichlaut:termbase, priority 9); one low-priority
note (category gleichlaut:checks, priority 10) with the remaining reasons in plain words. Every note is in the language
of the file: the raw guard output with its internal codes is not written into the XLIFF (round 13: a translator read it
as untranslated check output); it stays in the FHIR Provenance (debug_note gives the same text for support).
write(..., decisions=...): the reviewer's decisions from the review page (JSON export) applied to the same units: accepted
drafts (as is or edited) -> state="reviewed" (or "final" with final=True), subState gleichlaut:accepted |
gleichlaut:accepted-edited, target = the accepted text, segmented on sentence boundaries like the draft (segment.beads
of the new German and the accepted text); a signed-off unit keeps only the notes that do not describe the draft
(SIGNED_KEEP: the German change, the old German and old target); sent back -> state="initial" subState="gleichlaut:sent-back".
<originalData> is not used for context: it holds only the native data of inline codes (<data> elements referenced by
dataRef), so context there would be invalid use."""
import os, re
import xml.etree.ElementTree as ET
from collections import Counter
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
                  "state=initial + subState=gleichlaut:human : pas de brouillon, à traduire. "
                  "state=initial + subState=gleichlaut:sent-back : brouillon rejeté à la révision, pas de cible, à traduire.",
        "about12": "Brouillons automatiques des textes de limitation modifiés de la liste des spécialités (LS, OFSP). Source = "
                   "nouveau texte allemand ; cible = brouillon Gleichlaut (prétraduction). mrk mtype=x-changed : partie que "
                   "l'allemand a changée ; mrk mtype=protected : nombre placé par le code à partir de l'allemand.",
        "states12": "state=translated : tous les contrôles automatiques sont passés. state=needs-review-translation : un contrôle a "
                    "relevé un problème (voir les remarques de l'unité). state=needs-translation avec une cible vide : "
                    "brouillon rejeté à la révision (dans alt-trans rejected), à traduire. Pas de cible : confié à un traducteur.",
        "prov": "Modèle {model} ; {pipeline} ; série {run}",
        "prov_run": "Série enregistrée {run} (modèle non indiqué dans les enregistrements) ; {pipeline}",
        "product": "{product} ; limitation {code} ; LS {old} → {new}",
        "prev_de": "Allemand précédent : {t}", "prev_tgt": "Texte français précédent : {t}",
        "change": "Modification du texte allemand : {t}", "fine": "probablement sans problème, règle {r} : {why}",
        "model_nums": "Nombres écrits par le modèle lui-même (à vérifier) : {x}",
        "review": "Révision : {d}", "reviewed": "Export révisé : {n} unités décidées", "reviewed_1": "Export révisé : 1 unité décidée",
        "accept": "accepté", "accept-edited": "accepté modifié", "send-back": "renvoyé",
        "code_number": "nombre placé par le code à partir de l'allemand", "changed": "partie changée par l'allemand",
        "T1": "mot français bien formé, seulement absent du vocabulaire connu",
        "T2": "« ist … zu » allemand rendu par « doit être … »",
        "T3": "les nombres changent exactement comme dans l'allemand",
        "T4": "chiffre romain ou sigle, pas de l'allemand",
        "T5": "seuls des nombres changent hors du passage modifié, exactement ceux que l'allemand change ailleurs",
        "T6": "la modification du texte allemand n'est qu'orthographique (umlaut, trait d'union, majuscule, ponctuation, terminaison)",
        "T7": "négation comptée comme un lecteur la compte (« nicht- » préfixe, « ne … pas » une seule fois) : le compte suit l'allemand",
        "T8": "mêmes valeurs ajoutées et retirées des deux côtés, seul le nombre d'occurrences diffère",
        "product_nodate": "{product} ; limitation {code}",
        "fine_plain": "probablement sans problème : {why}",
        "del_de": "Suppression conforme à l'allemand ? À vérifier : l'allemand {verb} ici {u} ; le brouillon supprime {x}.",
        "del_verb": ("retire", "remplace"),
        "tally_only": "Signalé seulement pour {x} ; probablement sans problème, à vérifier.",
        "only_tally": "des décomptes (nombres, négation, verbes modaux) qui suivent l'allemand une fois recomptés",
        "only_mirror": "une suppression qui semble suivre celle de l'allemand (note ci-dessous)",
        "only_and": " et ",
        "tally_mirror": "la différence vient de phrases que l'allemand et le brouillon suppriment tous deux",
        "typo": "Typographie (pas un contrôle) : le brouillon introduit {x}.",
        "typo_open": "une espace après « ( »", "typo_close": "une espace avant « ) »", "typo_comma": "une espace avant la virgule",
        "typo_stop": "une espace avant le point", "typo_slash": "des espaces autour de « / »",
        "typo_double": "une ponctuation doublée", "typo_space": "une espace double",
        "del_whole": "Suppression conforme à l'allemand : l'allemand retire la phrase {u} ; le brouillon retire la phrase correspondante {x}.",
        "only_mirror_whole": "une suppression qui suit celle de l'allemand (note ci-dessous)",
        "lex": "aussi employé dans les limitations françaises de l'OFSP", "lex_old": "déjà dans l'ancien texte",
        "lex_both": "déjà dans l'ancien texte ou aussi employé dans les limitations françaises de l'OFSP",
        "lex_words": "{w} ({why})", "g4_de": "l'allemand le répète aussi",
        "checks_more": "{n} autres points relevés par les contrôles, non repris ci-dessus : {x}",
        "checks_more_1": "1 autre point relevé par les contrôles, non repris ci-dessus : {x}",
        "accepted": "Révisé et accepté : la cible est le texte retenu à la révision. Les remarques des contrôles sur le "
                    "brouillon d'origine ({v}) ne s'appliquent plus et ne sont pas reprises.",
        "sent_back": "Renvoyé à la révision : à traduire. Pas de cible ; le brouillon rejeté figure dans la remarque "
                     "« Brouillon rejeté », pas dans la cible.",
        "rejected": "Brouillon rejeté à la révision (ne pas le reprendre tel quel) : {t}",
        "v_ready": "prêt", "v_flagged": "signalé", "v_human": "confié à un traducteur",
        "reasons": {"Number wrong": "nombre erroné", "German change not applied": "modification du texte allemand non appliquée",
                    "Content lost": "contenu perdu", "German left / untranslated": "allemand non traduit",
                    "Terminology": "terminologie", "Wording": "formulation", "Other": "autre"},
        "order": "Ordre des mots allemand ? Le brouillon écrit {x} (allemand {d}) : en français, le complément suit en principe le nom ; à vérifier.",
        "lock_mirror": "À la place d'une phrase que l'allemand retire (note ci-dessous), le brouillon écrit autre chose : {x} ; à vérifier.",
        "novel_all": "Aucun mot à vérifier : {n} mots absents des limitations françaises, tous bien formés ou de la famille d'un mot du registre.",
        "novel_more": "{n} autres mots absents des limitations, bien formés ou de la famille d'un mot du registre, ne sont pas repris",
        "novel_more_1": "1 autre mot absent des limitations, bien formé ou de la famille d'un mot du registre, n'est pas repris",
        "debug": "Sortie brute des contrôles (codes internes de Gleichlaut, pour l'assistance technique ; pas une remarque de traduction) : {x}"},
 "it": {"ready": "Pronta: tutti i controlli automatici superati. Verificata dal codice, non ancora da una persona: da rivedere.",
        "flagged": "Segnalata: un controllo automatico ha rilevato un problema (vedi le note). Il testo d'arrivo è la bozza, da correggere.",
        "human": "Affidata a un traduttore: il tedesco è stato riscritto per oltre il 60%; nessuna bozza automatica.",
        "about": "Bozze automatiche dei testi di limitazione modificati dell'elenco delle specialità (ES, UFSP). Fonte = nuovo testo "
                 "tedesco, un segmento per frase; testo d'arrivo = bozza Gleichlaut. Nella fonte, gleichlaut:changed marca la parte "
                 "modificata dal tedesco. Nel testo d'arrivo, gleichlaut:code-number (translate=no) marca un numero inserito dal codice "
                 "a partire dal tedesco, gleichlaut:model-number un numero scritto dal modello (da verificare).",
        "states": "state=translated + subState=gleichlaut:ready: tutti i controlli superati, rivedere e accettare. "
                  "state=translated + subState=gleichlaut:flagged: un controllo ha rilevato un problema, vedi le note dell'unità; "
                  "il testo d'arrivo è la bozza da correggere, non sostituirla con una pretraduzione. "
                  "state=initial + subState=gleichlaut:human: nessuna bozza, da tradurre. "
                  "state=initial + subState=gleichlaut:sent-back: bozza respinta in revisione, nessun testo d'arrivo, da tradurre.",
        "about12": "Bozze automatiche dei testi di limitazione modificati dell'elenco delle specialità (ES, UFSP). Fonte = "
                   "nuovo testo tedesco; testo d'arrivo = bozza Gleichlaut (pretraduzione). mrk mtype=x-changed: parte modificata "
                   "dal tedesco; mrk mtype=protected: numero inserito dal codice a partire dal tedesco.",
        "states12": "state=translated: tutti i controlli automatici superati. state=needs-review-translation: un controllo ha "
                    "rilevato un problema (vedi le note dell'unità). state=needs-translation con testo d'arrivo vuoto: "
                    "bozza respinta in revisione (in alt-trans rejected), da tradurre. Nessun testo d'arrivo: affidata a un traduttore.",
        "prov": "Modello {model}; {pipeline}; serie {run}",
        "prov_run": "Serie registrata {run} (modello non indicato nelle registrazioni); {pipeline}",
        "product": "{product}; limitazione {code}; ES {old} → {new}",
        "prev_de": "Tedesco precedente: {t}", "prev_tgt": "Testo italiano precedente: {t}",
        "change": "Modifica tedesca: {t}", "fine": "probabilmente in ordine, regola {r}: {why}",
        "model_nums": "Numeri scritti dal modello stesso (da verificare): {x}",
        "review": "Revisione: {d}", "reviewed": "Esportazione rivista: {n} unità decise", "reviewed_1": "Esportazione rivista: 1 unità decisa",
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
        "product_nodate": "{product}; limitazione {code}",
        "fine_plain": "probabilmente in ordine: {why}",
        "del_de": "Soppressione conforme al tedesco? Da verificare: il tedesco qui {verb} {u}; la bozza sopprime {x}.",
        "del_verb": ("toglie", "sostituisce"),
        "tally_only": "Segnalata solo per {x}; probabilmente in ordine, da verificare.",
        "only_tally": "conteggi (numeri, negazione, verbi modali) che, ricontati, seguono il tedesco",
        "only_mirror": "una soppressione che sembra seguire quella del tedesco (nota qui sotto)",
        "only_and": " e ",
        "tally_mirror": "la differenza viene da frasi che il tedesco e la bozza sopprimono entrambi",
        "typo": "Tipografia (non un controllo): la bozza introduce {x}.",
        "typo_open": "uno spazio dopo «(»", "typo_close": "uno spazio prima di «)»", "typo_comma": "uno spazio prima della virgola",
        "typo_stop": "uno spazio prima del punto", "typo_slash": "spazi attorno a «/»",
        "typo_double": "una punteggiatura doppia", "typo_space": "uno spazio doppio",
        "del_whole": "Soppressione conforme al tedesco: il tedesco toglie la frase {u}; la bozza toglie la frase corrispondente {x}.",
        "only_mirror_whole": "una soppressione che segue quella del tedesco (nota qui sotto)",
        "lex": "usata anche nelle limitazioni italiane dell'UFSP", "lex_old": "già nel vecchio testo",
        "lex_both": "già nel vecchio testo o usata anche nelle limitazioni italiane dell'UFSP",
        "lex_words": "{w} ({why})", "g4_de": "anche il tedesco lo ripete",
        "checks_more": "{n} altri punti rilevati dai controlli, non ripresi sopra: {x}",
        "checks_more_1": "1 altro punto rilevato dai controlli, non ripreso sopra: {x}",
        "accepted": "Rivista e accettata: il testo d'arrivo è quello accettato in revisione. Le note dei controlli sulla "
                    "bozza originale ({v}) non si applicano più e non sono riprese.",
        "sent_back": "Rinviata in revisione: da tradurre. Nessun testo d'arrivo; la bozza respinta figura nella nota «Bozza "
                     "respinta», non nel testo d'arrivo.",
        "rejected": "Bozza respinta in revisione (da non riprendere così com'è): {t}",
        "v_ready": "pronta", "v_flagged": "segnalata", "v_human": "affidata a un traduttore",
        "reasons": {"Number wrong": "numero errato", "German change not applied": "modifica tedesca non applicata",
                    "Content lost": "contenuto perso", "German left / untranslated": "tedesco rimasto / non tradotto",
                    "Terminology": "terminologia", "Wording": "formulazione", "Other": "altro"},
        "order": "Ordine delle parole tedesco? La bozza scrive {x} (tedesco {d}): in italiano il complemento segue di norma il nome; da verificare.",
        "lock_mirror": "Al posto di una frase che il tedesco toglie (nota qui sotto), la bozza scrive altro: {x}; da verificare.",
        "novel_all": "Nessuna parola da verificare: {n} parole assenti dalle limitazioni italiane, tutte ben formate o della famiglia di una parola del registro.",
        "novel_more": "altre {n} parole assenti dalle limitazioni, ben formate o della famiglia di una parola del registro, non sono riprese",
        "novel_more_1": "un'altra parola assente dalle limitazioni, ben formata o della famiglia di una parola del registro, non è ripresa",
        "debug": "Uscita grezza dei controlli (codici interni di Gleichlaut, per l'assistenza tecnica; non una nota di traduzione): {x}"}}


def nt(lang, k, **kw):
    """A note text in the target language; a key with a singular form (k + "_1") takes it when n == 1."""
    from . import explain
    if kw.get("n") == 1 and k + "_1" in NOTE[lang]: k += "_1"
    s = NOTE[lang][k].format(**kw)
    return explain._fr(s) if lang == "fr" else s


def reason_text(lang, reason):
    """A review reason as stored by the page (English value of its list) in the target language; free text unchanged."""
    return NOTE[lang]["reasons"].get(reason, reason) if lang in NOTE else reason


def decided_notes(v, d):
    """-> [[id, category, appliesTo, priority, text]] replacing the verdict note of a decided unit: accepted -> the
    reviewed note (the 'flagged … to correct' verdict no longer describes the target), sent back -> the sent-back note
    plus the rejected draft as a note (it is never the target). [] when undecided."""
    L = v["lang"]
    if d in ("accept", "accept-edited"):
        return [["verdict", "gleichlaut:verdict", "target", "1", nt(L, "accepted", v=NOTE[L]["v_" + v["status"]])]]
    if d == "send-back":
        N = [["verdict", "gleichlaut:verdict", None, "1", nt(L, "sent_back")]]
        if v.get("draft"): N.append(["rejected", "gleichlaut:rejected-draft", None, "2", nt(L, "rejected", t=v["draft"])])
        return N
    return []


# A signed-off unit (accepted as is or edited) keeps only the notes that do not describe the draft: the German change and
# the old German / old target (the reviewed note replaces the verdict). The reasons, the low-priority notes, the house and
# termbase advisories and the checks note all describe the draft the reviewer has now decided on, so none is carried over.
SIGNED_KEEP = ("change", "de-old", "tgt-old")


def decided_unit_notes(v, d, prev=True):
    """-> the notes of a unit with the reviewer's decision d (None: undecided): decided_notes, then unit_notes without
    its verdict; for a signed-off unit only the SIGNED_KEEP notes of unit_notes."""
    N = unit_notes(v, prev=prev)
    if not d: return N
    head = decided_notes(v, d)
    if d in ("accept", "accept-edited"): return head + [n for n in N if n[0] in SIGNED_KEEP]
    return head + [n for n in N if n[0] != "verdict"]


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


# ------------------------------------------------------------------------------------------- translator-facing notes
# A unit carries: the verdict; at most SHOW reasons, the most actionable first, in plain reviewer-language wording without
# internal codes (rule ids, guard ids); the product and German change; the old German and old target text; low-priority
# notes apart from the reasons (a deletion that mirrors the German's, typography the draft introduced: category
# gleichlaut:note, priority 8; the house-sentence and termbase advisories: gleichlaut:house / gleichlaut:termbase, priority
# 9); and one low-priority note (category gleichlaut:checks, priority 10) with the reasons not shown above, in plain words.
# The raw guard output with its codes (debug_note) is not an XLIFF note (it stays in the FHIR Provenance). Presentation
# only: every finding is still there, no verdict changes.
#
# Every item of reasons() has a tier:
#   "reason"  may take one of the SHOW slots: findings to check, numbers the model wrote, the pre-existing divergence and
#             the correction notice, pipeline status, and findings a triage rule calls probably fine that are not tallies
#             (those low, after the rest), as are a German-left / copied word that is a target word too (in the words the
#             German and target registers share, or already in the old text: explain.lexicon_fine) and a repeated passage
#             the German repeats too (explain.german_repeats);
#   "note"    never a reason: a 'removed more than the German' finding whose lost words all sit in sentences the German
#             itself removes (explain.mirror): a statement when the draft drops the matching sentence one to one, else a
#             question; and the typography note;
#   "detail"  only in the checks note: tallies (numbers / negation / modal-verb counts) a triage rule calls probably fine,
#             negation / modal-verb counts that follow the German once sentences both remove whole are left out
#             (explain.tally_mirrored), a reason repeated word for word, and a second deletion note on the same German
#             passage.
# Ranking among reasons: numbers first (a number is never the model's to change), then the change not applied, German
# left or copied, content lost, edits outside the change, and only then negation / modal-verb counts still to check.
# A flagged draft whose findings are all notes or details gets one plain reason saying so (never an empty explanation).
# counts(R) is the review page's header ("n issues to check, m probably fine") over the same items.
SHOW = 3
RANK = {"corr": 0, "slot": 1, "unknown": 1, "g2": 2, "g1": 3, "g5": 3, "g3": 4, "lock": 5, "g4": 6, "g6": 7, "g7": 8, "record": 9}
RANK_COUNT = 5.5          # a negation / modal-verb count still to check: after the findings that name words
TALLY = ("Slots: neg", "Slots: modal", "Slots: nums")


def tally(f):
    """A slot finding that is a count (numbers, negation, modal verbs), as opposed to the words of the text."""
    return f.get("gid") == "slot" and (f.get("detail") or "").startswith(TALLY)


def _g3c_parts(f):
    """-> (German ops, lost words) of a 'removed more than the German' finding, from its detail
    ('G3c removed beyond the German change: near «a» -> «b»: bag | near …'), or None."""
    import re
    d = f.get("detail") or ""
    if f.get("gid") != "g3" or not d.startswith("G3c"): return None
    P = re.findall(r"near («[^«»]*» -> «[^«»]*»): ([^|]*?)(?= \| near «|$)", d)
    return ([k for k, _ in P], P[0][1].strip()) if P else None


def deleted_by_german(f, v):
    """A 'removed more than the German' finding (G3c) whose lost words all sit in sentences the German change itself
    removes (explain.mirror: aligned sentence beads, position-based): -> (old German passage, replaced?, whole?, old target
    sentences), else None. Wording only: such a finding is a low-priority note, a statement when the draft drops the
    sentence that translates the sentence the German drops, one to one (whole), else phrased as a question ('deletion
    matching the German? check'); its triage status and the verdict stay."""
    p = _g3c_parts(f)
    if not p or not v.get("draft"): return None
    from . import explain
    m = explain.mirror(v, v["draft"], p[0], p[1])
    return (m["de"], m["replaced"], m["whole"], m["tgt"]) if m["lost"] and m["mirrored"] == m["lost"] and m["de"] else None


def _lex_text(v, f, rule):
    """A German-left / copied-from-German finding with words that are probably fine (explain.lexicon_fine), reworded:
    -> (text, all words fine?) or None. The words still to check stay in the sentence; the others follow as probably fine."""
    if rule or f.get("gid") not in ("g1", "g5") or v["lang"] not in NOTE: return None
    from . import explain
    fine, other = explain.lexicon_fine(v, f)
    if not fine: return None
    L = v["lang"]; old = v.get("tgt_old") or ""
    import re
    in_old = [w for w in fine if re.search(r"(?<!\w)" + re.escape(w) + r"(?!\w)", old, re.I)]
    why = NOTE[L]["lex_old" if len(in_old) == len(fine) else "lex" if not in_old else "lex_both"]
    shown = [explain.case_in(v.get("draft") or "", w) for w in fine]
    if not other: return f"{f['text']} ({nt(L, 'fine_plain', why=why)})", True
    head = explain.tr(L, f["gid"], x=explain.words_list(L, [explain.case_in(v.get("draft") or "", w) for w in other]))
    return f"{head} ({nt(L, 'fine_plain', why=nt(L, 'lex_words', w=', '.join(shown), why=why))})", False


def _novel_text(v, f, rule):
    """An out-of-vocabulary finding (G7) with words that are probably ordinary (explain.novel_fine), reworded: -> (text,
    all words ordinary?) or None. Only the words still to check are named; the ordinary ones are counted, not listed
    (round 13: 17 ordinary words such as « composant », « danger » were listed as never seen)."""
    if rule or f.get("gid") != "g7" or v["lang"] not in NOTE: return None
    from . import explain
    fine, other = explain.novel_fine(v, f)
    if not fine: return None
    L = v["lang"]
    if not other: return nt(L, "novel_all", n=len(fine)), True
    head = explain.tr(L, "g7", x=explain.words_list(L, [explain.case_in(v.get("draft") or "", w) for w in other]))
    return f"{head} ({nt(L, 'novel_more', n=len(fine))})", False


def _removed_sentences(v):
    """The old target sentences the draft drops one to one where the German drops their sentence (deleted_by_german,
    whole), as one string; '' when there are none."""
    out = []
    for g in v.get("findings", []):
        dl = deleted_by_german(g, v)
        if dl and dl[2]: out.append(dl[3])
    return " ".join(out)


def _lock_text(v, f, removed):
    """A lock finding ('the draft also changes a passage the German leaves as is') whose every changed passage lies in a
    sentence the German itself removes and the draft drops with it (_removed_sentences): the German does change that
    passage, so the finding is worded as what it is, text the draft writes in place of a removed sentence, still to check
    (round 13, wb004: the lock wording contradicted the deletion note). -> text or None."""
    import re
    from . import explain
    if f.get("gid") != "lock" or not removed or v["lang"] not in NOTE: return None
    P = re.findall(r"«([^«»]*)» -> «([^«»]*)»", f.get("detail") or "")
    rw = Counter(w.lower() for w in re.findall(r"\w+", removed))
    for u, _ in P:
        W = [w.lower() for w in re.findall(r"\w+", u)]
        if not W or sum(1 for w in W if rw[w]) < 0.8 * len(W): return None
    if not P: return None
    pre = explain.tr(v["lang"], "lock", x="")
    x = f["text"][len(pre):] if f["text"].startswith(pre) else re.split(r"\s?:\s", f["text"], maxsplit=1)[-1]
    return nt(v["lang"], "lock_mirror", x=x.strip())


def _typo_note(v):
    from . import explain
    L = v["lang"]
    if L not in NOTE or not v.get("draft") or v.get("status") == "human": return None
    T = explain.typography(v.get("tgt_old") or "", v["draft"])
    if not T: return None
    x = ", ".join(f"{NOTE[L]['typo_' + k]} ({explain.q(L, s)})" for k, s in T[:3])
    return nt(L, "typo", x=x)


# a code of a German compound ('CD38 Antikörper', 'CD38-Antikörper') right before a target noun: German word order
# ('un CD38 anticorps')
ORDER_DE = re.compile(r"(?<![\w-])([A-Z][A-Za-z]{0,4}\d[\w]*)[- ]([A-ZÄÖÜ][a-zäöüß]{3,})")


def _order_note(v):
    """A low-priority note (not a check, never a verdict): the draft writes a code of a German hyphen compound right before
    a target-language noun ('un CD38 anticorps' for 'CD38-Antikörper'), German word order, where the old text did not."""
    import re
    from . import explain
    L, d = v["lang"], v.get("draft") or ""
    if L not in NOTE or not d or v.get("status") == "human": return None
    for m in ORDER_DE.finditer(v.get("de_new") or ""):
        code = m.group(1)
        k = re.search(r"(?<![\w-])" + re.escape(code) + r"\s+([^\W\d_A-Z][^\W\d_]{3,})", d)
        if k and k.group(0) not in (v.get("tgt_old") or ""):
            return nt(L, "order", x=explain.q(L, k.group(0)), d=explain.q(L, m.group(0)))
    return None


def mirror_text(f, v):
    """The low-priority note of a 'removed more than the German' finding whose lost words all sit in sentences the German
    itself removes (deleted_by_german): a statement when the draft drops the matching sentence one to one, else a question;
    None otherwise. The same text in the explanation's grey line and in the checks detail."""
    import re
    from . import explain
    L = v["lang"]; dl = deleted_by_german(f, v)
    if not dl or L not in NOTE: return None
    if dl[2]: return nt(L, "del_whole", u=explain.q(L, explain.clip(dl[0], 120)), x=explain.q(L, explain.clip(dl[3], 120)))
    x = re.split(r"\s?:\s", f["text"], maxsplit=1)[-1]
    return nt(L, "del_de", verb=NOTE[L]["del_verb"][dl[1]], u=explain.q(L, explain.clip(dl[0], 90)), x=x)


def reasons(v, old=True):
    """-> [dict(kind=divergence|finding|model-numbers|summary|typography, text, low, rank, gid, rule, tier[, tally])]: the items
    of tier "reason" first (most actionable first, low ones last), then the notes, then the details (see the comment
    above). old=True includes the pre-existing divergence and the correction notice (the review page shows those in its
    own notice). Text in the draft's language, no internal codes. Every finding of the view is one item."""
    import re
    from . import explain
    L = v["lang"]; R = []; removed = _removed_sentences(v) if any(f["gid"] == "lock" for f in v.get("findings", [])) else ""
    if old and v.get("banner"): R.append(dict(kind="divergence", text=v["banner"], low=False, rank=-1, gid="div", rule=None, tier="reason"))
    for f, r in zip(v.get("findings", []), triage.triage(v)):
        if f["gid"] == "corr" and not old: continue
        base = f["text"] + (f" ({explain.corr_note(L)})" if f["corrects"] and f["gid"] != "corr" else "")
        dl = None if r else deleted_by_german(f, v)
        lx = _lex_text(v, f, r) or _novel_text(v, f, r)
        lk = None if r else _lock_text(v, f, removed)
        rank, tier = RANK.get(f["gid"], 8), "reason"
        if lx:                                         # German-looking words that are target words too (or were there); new
            text, low = lx                             # words that are ordinary target words
        elif lk:                                       # text in place of a sentence the German removes: still to check
            text, low = lk, False
        elif not r and L in NOTE and f["gid"] == "g4" and v.get("draft") and explain.german_repeats(v, v["draft"], f.get("detail")):
            text, low = f"{base} ({nt(L, 'fine_plain', why=NOTE[L]['g4_de'])})", True
        elif r and L in NOTE:
            text, low = f"{base} ({nt(L, 'fine_plain', why=NOTE[L][r])})", True
            if tally(f): tier = "detail"
        elif L in NOTE and tally(f) and v.get("draft") and explain.tally_mirrored(v, v["draft"], f["detail"]):
            text, low, tier = f"{base} ({nt(L, 'fine_plain', why=NOTE[L]['tally_mirror'])})", True, "detail"
        elif dl and L in NOTE:
            text = mirror_text(f, v)
            low, tier = True, "note"
        else:
            text, low = base, f["gid"] == "record"
            if tally(f) and not f["detail"].startswith("Slots: nums"): rank = RANK_COUNT
        R.append(dict(kind="finding", text=text, low=low, rank=rank, gid=f["gid"], rule=r, tier=tier, tally=tally(f),
                      **({"de": dl[0], "whole": dl[2]} if tier == "note" else {})))
    model = [t for _, _, t, who, _ in v.get("numbers", []) if who == "model"]
    if model: R.append(dict(kind="model-numbers", text=nt(L, "model_nums", x=", ".join(model)), low=False, rank=1.5, gid="model", rule=None, tier="reason"))
    seen = set()
    for x in sorted(R, key=lambda x: (x["low"], x["rank"])):
        k = x.get("de") or x["text"]                    # one note per German passage a deletion mirrors
        if x["tier"] in ("reason", "note") and k in seen: x["tier"] = "detail"; x["dup"] = True
        seen.add(k)
    t = _typo_note(v)
    if t: R.append(dict(kind="typography", text=t, low=True, rank=10, gid="typo", rule=None, tier="note"))
    o = _order_note(v)
    if o: R.append(dict(kind="order", text=o, low=False, rank=7.5, gid="order", rule=None, tier="reason"))      # to check (round 13)
    if v.get("status") == "flagged" and L in NOTE and not any(x["tier"] == "reason" for x in R):
        F = [x for x in R if x["kind"] == "finding"]
        M = [x for x in F if x["tier"] == "note"]
        parts = ([NOTE[L]["only_tally"]] if any(x["tier"] == "detail" and not x.get("dup") for x in F) else []) + \
                ([NOTE[L]["only_mirror_whole" if all(x.get("whole") for x in M) else "only_mirror"]] if M else [])
        if parts:
            R.append(dict(kind="summary", text=nt(L, "tally_only", x=NOTE[L]["only_and"].join(parts)), low=True, rank=9.5,
                          gid="summary", rule=None, tier="reason"))
    order = {"reason": 0, "note": 1, "detail": 2}
    return sorted(R, key=lambda x: (order[x["tier"]], x["low"], x["rank"]))


def top(R):
    """The reasons shown (at most SHOW, tier "reason")."""
    return [x for x in R if x["tier"] == "reason"][:SHOW]


def rest(R):
    """The items left to the checks note: reasons beyond SHOW and the details (the notes have their own note)."""
    T = top(R)
    return [x for x in R if x["tier"] != "note" and not any(x is y for y in T)]


def notes(R):
    """The low-priority notes apart from the reasons (a deletion that mirrors the German's, typography)."""
    return [x for x in R if x["tier"] == "note"]


def counts(R):
    """-> [to check, probably fine]: the review page's header over the reasons (the same classification as the list):
    findings and model-written numbers shown as reasons to check (record status included); probably fine = every other
    finding (a low reason, a low-priority note, a detail). A reason repeated word for word counts once."""
    chk = sum(1 for x in R if x["kind"] in ("finding", "model-numbers", "order") and x["tier"] == "reason" and (not x["low"] or x["gid"] == "record"))
    fine = sum(1 for x in R if x["kind"] == "finding" and not x.get("dup") and x["gid"] != "record"
               and (x["tier"] != "reason" or x["low"]))
    return [chk, fine]


def explanation(v):
    """-> dict(top=[[text, low]], more=n reasons in the checks detail, note=one line of low-priority notes, the house-
    sentence and the termbase advisory, or None, counts=[to check, probably fine]): what the review page shows under a
    draft (the same as the XLIFF notes)."""
    R = reasons(v, old=False)
    line = " ".join([x["text"] for x in notes(R)] + [t for t in (house_note(v), termbase_note(v)) if t]) or None
    return dict(top=[[x["text"], x["low"]] for x in top(R)], more=len(rest(R)), note=line, counts=counts(R))


def checks_note(v, R=None):
    """The low-priority note with the reasons not shown above, in plain words (None when there are none). No internal
    codes (debug_note has them, for support; not written into the XLIFF)."""
    L = v["lang"]; R = reasons(v) if R is None else R; more = [x for x in rest(R) if not x.get("dup")]
    if not more or L not in NOTE: return None
    return nt(L, "checks_more", n=len(more), x=" | ".join(x["text"] for x in more))


def debug_note(v):
    """The one note with the raw guard output and its internal codes (Slots, G3c, T7 …), for technical support, not for
    the translator; not written into the XLIFF (the FHIR Provenance keeps the raw output). None when the draft has no
    finding."""
    from . import explain
    F = [(f, r) for f, r in zip(v.get("findings", []), triage.triage(v)) if f.get("detail")]
    if not F or v["lang"] not in NOTE: return None
    raw = " · ".join(explain.clip(f["detail"], 220) + (f" [{r}]" if r else "") for f, r in F)      # verbatim (no French spacing)
    return nt(v["lang"], "debug", x="").rstrip() + " " + raw


def unit_notes(v, prev=True):
    """-> [[id, category, appliesTo, priority, text]] of one unit, in order (prev=False: without the old German / old
    target notes, which the review page writes from its own diff)."""
    L = v["lang"]; R = reasons(v)
    N = [["verdict", "gleichlaut:verdict", "target", "1", nt(L, v["status"])]]
    k = 0
    for x in top(R):
        if x["kind"] == "finding": k += 1; nid, cat = f"finding-{k}", "gleichlaut:finding"
        else: nid, cat = x["kind"], f"gleichlaut:{x['kind']}"
        N.append([nid, cat, "target", "3" if x["low"] else "1", x["text"]])
    N.append(["change", "gleichlaut:change", "source", "2", product_note(v, L) + ". " + nt(L, "change", t=change_summary(v))])
    if prev:
        N.append(["de-old", "context:previous-source", "source", "5", nt(L, "prev_de", t=v["de_old"])])
        N.append(["tgt-old", "context:previous-target", "target", "5", nt(L, "prev_tgt", t=v["tgt_old"])])
    lo = notes(R)
    if lo: N.append(["notes", "gleichlaut:note", "target", "8", " ".join(x["text"] for x in lo)])
    h = house_note(v)
    if h: N.append(["house", "gleichlaut:house", "target", "9", h])
    t = termbase_note(v)
    if t: N.append(["termbase", "gleichlaut:termbase", "target", "9", t])
    c = checks_note(v, R)
    if c: N.append(["checks", "gleichlaut:checks", None, "10", c])
    return N


def termbase_note(v):
    """The termbase advisory (termbase.advice, in the view as v["termbase"]): BAG's house rendering of a German term of the
    new text where the draft introduces a minority variant or falls short of the house rendering, or, softer, where the
    draft carries over unchanged a non-standard rendering the old text already used. Its own low-priority note (priority
    9), never one of the SHOW reasons and never a verdict; a wording that sits in a sentence the house-sentence note
    already names is left out. None when there is nothing to say."""
    from .. import termbase
    H = [h["wrote"].lower() for h in v.get("house") or []]
    A = [a for a in v.get("termbase") or [] if not (a.get("wrote") and any(a["wrote"].lower() in h for h in H))]
    return termbase.advisory_text(A, v["lang"])


def house_note(v):
    """The house-sentence advisory (house.advice, in the view as v["house"]): BAG's dominant wording of a fixed German
    sentence where the draft's aligned sentence departs from it. Its own low-priority note (priority 9), never one of the
    SHOW reasons and never a verdict; a termbase note on a wording inside the same sentence is left out (termbase_note).
    None when there is nothing to say."""
    from .. import house
    return house.advisory_text(v.get("house") or [], v["lang"])


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
    state, sub = STATE[v["status"]]; text = None
    d = (dec or {}).get("decision")
    if d in ("accept", "accept-edited") and not (v["draft"] or (dec.get("text") or "").strip()): d = None
    if d in ("accept", "accept-edited"):
        text = dec.get("text") if d == "accept-edited" and dec.get("text") else None
        state, sub = ("final" if final else "reviewed"), ("gleichlaut:accepted-edited" if text is not None else "gleichlaut:accepted")
    elif d == "send-back":
        state, sub = "initial", "gleichlaut:sent-back"
    for nid, cat, ap, pr, t in decided_unit_notes(v, d):
        _note(notes, t, cat, nid, ap, pr)
    if d:
        why = "; ".join(x for x in (reason_text(L, dec.get("reason") or ""), dec.get("note")) if x)
        _note(notes, review_text(L, d, dec.get("at"), why), "gleichlaut:review", "review", "target", "1")
    # a sent-back unit carries no target: the rejected draft is in its note, never a pre-translation
    segments(u, v, state, sub, text, with_target=d != "send-back" and (v["status"] != "human" or text is not None))
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
