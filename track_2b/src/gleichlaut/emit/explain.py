"""Plain-language guard findings for the reviewer: one short sentence per finding, in the language of the draft (French
for French drafts, Italian for Italian drafts, English otherwise), with the raw technical finding kept alongside.

Rendering only. The verdict (ready / flagged) and every finding come from the frozen guard stack (core.Pipeline.check);
this module rephrases them and never adds, drops or reweighs a finding. Two additions are labelled as such:
  - "corrects": the draft also changes a number the German does not touch, and the change brings the target closer to
    the German (e.g. Nemluvio IT 'ogni quattro settimane' -> 'ogni otto' where the German says 'alle acht Wochen').
    Findings caused by that change are annotated, not suppressed: the flag stands and a translator decides.
  - "divergence": pre-existing problems of the old target text (numbers / units on which it disagrees with the old
    German, a target text written in another language, editorial problems), from gleichlaut.audit.audit_item when that
    module is importable (skipped silently otherwise). A display-level notice: it never changes a verdict.
Helpers for how the reasons are worded and ranked (emit/xliff.py), wording only: g2_text (a change-not-applied finding
names a German old / new pair only when the two sides are recognisably the same words, else what the check looks for),
mirror (a 'removed more than the German' finding whose lost words sit where the German itself removes text, by aligned
sentence beads), tally_mirrored (a negation / modal-verb count explained by sentences both sides remove) and typography
(spacing the draft introduces; a note, not a check). measure_v2() writes eval/results/explain_v2.json."""
import difflib, re
from collections import Counter
from .. import core

lock, gl2 = core.lock, core.gl2
WTOK = re.compile(r"\d+(?:[.,'’]\d+)*|\w+|[^\w\s]")
QUOTE = {"fr": ("«\u00a0", "\u00a0»"), "it": ("«", "»"), "en": ("“", "”")}
ORDER = ["record", "slot", "unknown", "g2", "g1", "g5", "g3", "lock", "g4", "g6", "g7"]

# Guard names in words (the G-ids stay in tooltips and details).
NAMES = {
    "lock":   {"fr": "Modifications limitées au changement", "it": "Modifiche limitate al cambiamento", "en": "Edits stay inside the change"},
    "slot":   {"fr": "Nombres / négation / verbes modaux", "it": "Numeri / negazione / verbi modali", "en": "Numbers / negation / modal verbs"},
    "unknown": {"fr": "Nombres / négation / verbes modaux", "it": "Numeri / negazione / verbi modali", "en": "Numbers / negation / modal verbs"},
    "g1":     {"fr": "Allemand resté", "it": "Tedesco rimasto", "en": "German left"},
    "g2":     {"fr": "Changement appliqué", "it": "Modifica applicata", "en": "Change applied"},
    "g3":     {"fr": "Contenu perdu", "it": "Contenuto perso", "en": "Content dropped"},
    "g4":     {"fr": "Répétition", "it": "Ripetizione", "en": "Duplication"},
    "g5":     {"fr": "Copié de l'allemand", "it": "Copiato dal tedesco", "en": "Copied from German"},
    "g6":     {"fr": "Terminologie", "it": "Terminologia", "en": "Terminology"},
    "g7":     {"fr": "Vocabulaire", "it": "Vocabolario", "en": "Vocabulary"},
    "reask":  {"fr": "Seconde demande", "it": "Seconda richiesta", "en": "Re-ask"},
    "record": {"fr": "Statut du pipeline", "it": "Stato della pipeline", "en": "Pipeline status"},
}
REASK = {"rule_only": {"fr": "Pas d'appel au modèle : les règles couvraient tout le changement.",
                       "it": "Nessuna chiamata al modello: le regole coprivano tutto il cambiamento.",
                       "en": "No model call: rules covered every change."},
         "not_needed": {"fr": "Pas nécessaire : le premier brouillon passait tous les contrôles.",
                        "it": "Non necessaria: la prima bozza superava tutti i controlli.",
                        "en": "Not needed: the first draft passed."},
         "kept": {"fr": "Utilisée et retenue : le brouillon redemandé passe tous les contrôles.",
                  "it": "Usata e tenuta: la bozza richiesta di nuovo supera tutti i controlli.",
                  "en": "Used and kept: the re-asked draft passed every check."},
         "not_kept": {"fr": "Utilisée, non retenue : le brouillon redemandé échouait encore ; le premier brouillon reste, signalé.",
                      "it": "Usata, non tenuta: la bozza richiesta di nuovo falliva ancora; resta la prima bozza, segnalata.",
                      "en": "Used, not kept: the re-asked draft still failed; the first draft stays, flagged."}}


REVIEW = [("air-gapped", {"fr": "Mode hors ligne (air-gapped)\u00a0: chaque brouillon passe en révision.",
                           "it": "Modalità offline (air-gapped): ogni bozza va in revisione.",
                           "en": "Air-gapped mode: every draft goes to review."}),
          ("statute lane", {"fr": "Voie des lois fédérales\u00a0: chaque brouillon est révisé.",
                            "it": "Corsia delle leggi federali: ogni bozza viene rivista.",
                            "en": "Statute lane: every draft is reviewed."}),
          ("SL lane on a local", {"fr": "Modèle local non certifié\u00a0: chaque brouillon est révisé.",
                                  "it": "Modello locale non certificato: ogni bozza viene rivista.",
                                  "en": "Local, uncertified model: every draft is reviewed."}),
          ("stub", {"fr": "Backend de test\u00a0: le brouillon est l'ancien texte, pas une traduction.",
                    "it": "Backend di prova: la bozza è il vecchio testo, non una traduzione.",
                    "en": "Test backend: the draft is the old text, not a translation."})]
STUB_CODE = {"fr": "Backend de test\u00a0: changement appliqué par le code (aucun modèle nécessaire).",
             "it": "Backend di prova: modifica applicata dal codice (nessun modello necessario).",
             "en": "Test backend: change applied by code (no model needed)."}
REVIEW_OTHER = {"fr": "Marqué pour révision par le pipeline\u00a0: {r}", "it": "Segnalato per revisione dalla pipeline: {r}",
                "en": "Marked for review by the pipeline: {r}"}


def review_text(reason, lang, rule_only=False):
    """A record's own reason for review (air-gapped, statute lane, ...) as one sentence in the reviewer's language.
    A stub record whose change code applied alone (rule_only: no model call was needed) says so instead of 'the draft
    is the old text'."""
    if rule_only and (reason or "").startswith("stub"): return STUB_CODE[rl(lang)]
    for k, T_ in REVIEW:
        if (reason or "").startswith(k): return T_[rl(lang)]
    return REVIEW_OTHER[rl(lang)].format(r=reason or "status flagged")


def record_finding(reason, lang, rule_only=False):
    return dict(gid="record", name=GID["record"], gname=NAMES["record"][rl(lang)], text=review_text(reason, lang, rule_only),
                detail=f"record status flagged: {reason or '(no reason recorded)'}", corrects=False)


def reask_text(v):
    k = "rule_only" if v["rule_only"] else "not_needed" if not v["reasked"] else "kept" if v["replaced"] else "not_kept"
    return REASK[k][rl(v["lang"])]


GID = {"lock": "Lock", "slot": "Slots", "unknown": "Slots", "g1": "G1", "g2": "G2", "g3": "G3", "g4": "G4", "g5": "G5",
       "g6": "G6", "g7": "G7", "reask": "Re-ask", "record": "Record"}

T = {
    "lock": {"fr": "Le brouillon change aussi un passage que l'allemand ne change pas : {x}",
             "it": "La bozza cambia anche un passo che il tedesco non cambia: {x}",
             "en": "The draft also changes a passage the German leaves as is: {x}"},
    "lock_add": {"fr": "ajout de {v}", "it": "aggiunta di {v}", "en": "adds {v}"},
    "lock_del": {"fr": "suppression de {u}", "it": "soppressione di {u}", "en": "removes {u}"},
    "neg": {"fr": "Négation non reprise : l'allemand {de}, le brouillon {tg}.",
            "it": "Negazione non ripresa: il tedesco {de}, la bozza {tg}.",
            "en": "Negation not mirrored: the German {de}, the draft {tg}."},
    "modal": {"fr": "Verbe modal ({m}) non repris : l'allemand {de}, le brouillon {tg}.",
              "it": "Verbo modale ({m}) non ripreso: il tedesco {de}, la bozza {tg}.",
              "en": "Modal verb ({m}) not mirrored: the German {de}, the draft {tg}."},
    "add_n": {"fr": "en ajoute {n}", "it": "ne aggiunge {n}", "en": "adds {n}"},
    "rem_n": {"fr": "en retire {n}", "it": "ne toglie {n}", "en": "removes {n}"},
    "none_n": {"fr": "n'en change aucun", "it": "non ne cambia nessuno", "en": "changes none"},
    "none_f": {"fr": "n'en change aucune", "it": "non ne cambia nessuna", "en": "changes none"},
    "decimal": {"fr": " Seule différence : le séparateur décimal ({a} / {b}), probablement correct.",
                "it": " Unica differenza: il separatore decimale ({a} / {b}), probabilmente corretto.",
                "en": " The only difference is the decimal separator ({a} / {b}), probably fine."},
    "nums": {"fr": "Les nombres ne suivent pas l'allemand : allemand {de} ; brouillon {tg}.",
             "it": "I numeri non seguono il tedesco: tedesco {de}; bozza {tg}.",
             "en": "Numbers do not follow the German: German {de}; draft {tg}."},
    "n_add": {"fr": "ajoute {x}", "it": "aggiunge {x}", "en": "adds {x}"},
    "n_rem": {"fr": "retire {x}", "it": "toglie {x}", "en": "removes {x}"},
    "n_none": {"fr": "aucun changement", "it": "nessun cambiamento", "en": "no change"},
    "unknown": {"fr": "Le brouillon contient {n} codes de nombre inconnus : vérifier les nombres.",
                "it": "La bozza contiene {n} codici numerici sconosciuti: verificare i numeri.",
                "en": "The draft contains {n} unknown number codes: check the numbers."},
    "unknown_1": {"fr": "Le brouillon contient un code de nombre inconnu : vérifier les nombres.",
                  "it": "La bozza contiene un codice numerico sconosciuto: verificare i numeri.",
                  "en": "The draft contains an unknown number code: check the numbers."},
    "g1": {"fr": "Mots allemands restés dans le texte : {x}", "it": "Parole tedesche rimaste nel testo: {x}",
           "en": "German words left in the text: {x}"},
    "g5": {"fr": "Mots repris de l'allemand sans traduction : {x}", "it": "Parole riprese dal tedesco senza traduzione: {x}",
           "en": "Words copied from the German untranslated: {x}"},
    "g6": {"fr": "Terminologie : {a} s'écrit {b} en français", "it": "Terminologia: {a} in italiano si scrive {b}",
           "en": "Terminology: {a} is written {b} in the target language"},
    "g7": {"fr": "Mot jamais vu dans les limitations françaises (coquille ?) : {x}",
           "it": "Parola mai vista nelle limitazioni italiane (refuso?): {x}",
           "en": "Word never seen in target-language limitations (typo?): {x}"},
    # what the check knows: the change is not found, translated, at its place in the draft (it may be missing, left in
    # German, or written elsewhere: Omvoh wb013 has the addition, untranslated, outside the changed passage)
    "g2_rep": {"fr": "Le changement allemand {u} → {v} n'est pas trouvé, traduit, à sa place dans le brouillon.",
               "it": "Il cambiamento tedesco {u} → {v} non risulta tradotto al posto giusto nella bozza.",
               "en": "The German change {u} → {v} is not found translated in the right place in the draft."},
    "g2_add": {"fr": "L'ajout allemand {v} n'est pas trouvé, traduit, à sa place dans le brouillon.",
               "it": "L'aggiunta tedesca {v} non risulta tradotta al posto giusto nella bozza.",
               "en": "The German addition {v} is not found translated in the right place in the draft."},
    "g2_del": {"fr": "La suppression allemande de {u} n'est pas trouvée à sa place dans le brouillon.",
               "it": "La soppressione tedesca di {u} non risulta ripresa al posto giusto nella bozza.",
               "en": "The German removal of {u} is not found carried over in the right place in the draft."},
    "g2_add_s": {"fr": "L'allemand ajoute ou réécrit ici la phrase {v} : vérifier qu'elle est traduite dans le brouillon.",
                 "it": "Il tedesco aggiunge o riscrive qui la frase {v}: verificare che sia tradotta nella bozza.",
                 "en": "The German adds or rewrites the sentence {v} here: check that the draft translates it."},
    "g2_add_miss": {"fr": "L'allemand ajoute ici la phrase {v} : elle manque dans le brouillon.",
                    "it": "Il tedesco aggiunge qui la frase {v}: manca nella bozza.",
                    "en": "The German adds the sentence {v} here: it is missing from the draft."},
    "g2_add_de": {"fr": "L'allemand ajoute ou réécrit ici la phrase {v} : le brouillon la laisse en allemand ({x}).",
                  "it": "Il tedesco aggiunge o riscrive qui la frase {v}: la bozza la lascia in tedesco ({x}).",
                  "en": "The German adds or rewrites the sentence {v} here: the draft leaves it in German ({x})."},
    "g2_del_kept": {"fr": "L'allemand supprime ici la phrase {u} : le brouillon garde la phrase correspondante {x}.",
                    "it": "Il tedesco sopprime qui la frase {u}: la bozza mantiene la frase corrispondente {x}.",
                    "en": "The German removes the sentence {u} here: the draft keeps the matching sentence {x}."},
    "g2_del_s": {"fr": "L'allemand supprime ici la phrase {u} : vérifier que le brouillon la supprime aussi.",
                 "it": "Il tedesco sopprime qui la frase {u}: verificare che la bozza la sopprima anche.",
                 "en": "The German removes the sentence {u} here: check that the draft removes it too."},
    "g3c": {"fr": "Le brouillon supprime davantage que l'allemand : {x}", "it": "La bozza toglie più del tedesco: {x}",
            "en": "The draft removes more than the German does: {x}"},
    "g3a": {"fr": "Mots de l'ancien texte disparus hors de la partie modifiée : {x}",
            "it": "Parole del vecchio testo scomparse fuori dalla parte modificata: {x}",
            "en": "Words of the old text lost outside the changed part: {x}"},
    "g4": {"fr": "Passage répété (une seule fois dans l'ancien texte) : {x}",
           "it": "Passo ripetuto (una sola volta nel vecchio testo): {x}",
           "en": "Passage repeated (once only in the old text): {x}"},
    "more": {"fr": "et {n} autres", "it": "e altri {n}", "en": "and {n} more"},
    "more_1": {"fr": "et 1 autre", "it": "e 1 altro", "en": "and 1 more"},
    "corr": {"fr": "Le brouillon corrige aussi une divergence de l'ancien texte : {o} → {n} (l'allemand dit {d}). À vérifier.",
             "it": "La bozza corregge anche una divergenza del vecchio testo: {o} → {n} (il tedesco dice {d}). Da verificare.",
             "en": "The draft also corrects a divergence of the old text: {o} → {n} (the German says {d}). Please check."},
    "corr_note": {"fr": "Le brouillon corrige aussi cette divergence — à vérifier",
                  "it": "La bozza corregge anche questa divergenza — da verificare",
                  "en": "The draft also corrects this divergence — please check"},
    "div": {"fr": "L'ancien texte français diverge déjà de l'allemand : {x}",
            "it": "Il vecchio testo italiano diverge già dal tedesco: {x}",
            "en": "The old target text already diverges from the German: {x}"},
    "div_vs": {"fr": "{t} contre {d} en allemand", "it": "{t} contro {d} in tedesco", "en": "{t} vs {d} in the German"},
    "div_de": {"fr": "l'allemand dit {c}, l'ancien texte non", "it": "il tedesco dice {c}, il vecchio testo no",
               "en": "the German says {c}, the old text does not"},
    "div_tg": {"fr": "l'ancien texte dit {c}, l'allemand non", "it": "il vecchio testo dice {c}, il tedesco no",
               "en": "the old text says {c}, the German does not"},
    "div_pair": {"fr": "allemand {d}, français {t}", "it": "tedesco {d}, italiano {t}", "en": "German {d}, target {t}"},
    "lang_is": {"fr": "L'ancien texte français est en {x}.", "it": "Il vecchio testo italiano è in {x}.",
                "en": "The previous target text is in {x}."},
    "term": {"fr": "L'ancien texte dit {a}\u00a0; l'OFSP a déjà corrigé ce terme en {b} ailleurs{w}.",
             "it": "Il vecchio testo dice {a}; l'UFSP ha già corretto questo termine in {b} altrove{w}.",
             "en": "The old text says {a}; BAG already corrected this term to {b} elsewhere{w}."},
    "term_w": {"fr": " ({x})", "it": " ({x})", "en": " ({x})"},
    "lang_not": {"fr": "L'ancien texte français ne semble pas être en français : {x}",
                 "it": "Il vecchio testo italiano non sembra essere in italiano: {x}",
                 "en": "The previous target text does not seem to be in the target language: {x}"},
}
LANGNAME = {"fr": {"de": "allemand", "fr": "français", "it": "italien", "en": "anglais", "rm": "romanche"},
            "it": {"de": "tedesco", "fr": "francese", "it": "italiano", "en": "inglese", "rm": "romancio"},
            "en": {"de": "German", "fr": "French", "it": "Italian", "en": "English", "rm": "Romansh"}}
_LANGWORDS = {"de": r"german|deutsch|allemand|tedesco", "fr": r"french|franz|français|francese", "it": r"italian|italien|italiano",
              "en": r"english|englisch|anglais|inglese", "rm": r"romansh|rätoroman|romanche|romancio"}
KINDS = ("number", "unit", "language", "editorial", "terminology")
MODAL = {"MUST": {"fr": "obligation : doit", "it": "obbligo: deve", "en": "obligation: must"},
         "MAY": {"fr": "possibilité : peut", "it": "possibilità: può", "en": "permission: may"},
         "SHALL": {"fr": "recommandation : devrait", "it": "raccomandazione: dovrebbe", "en": "recommendation: should"}}


def rl(lang): return lang if lang in ("fr", "it") else "en"
def _fr(s): return re.sub(r" ([;:!?»])", "\u00a0\\1", s).replace("« ", "«\u00a0") if s else s
def tr(lang, k, **kw):
    if kw.get("n") == 1 and k + "_1" in T: k += "_1"            # singular form
    s = T[k][rl(lang)].format(**kw)
    return _fr(s) if rl(lang) == "fr" else s
def q(lang, s): a, b = QUOTE[rl(lang)]; return f"{a}{s}{b}"


def clip(s, n=110):
    s = re.sub(r"[ \t\r\n]+", " ", s).strip()          # not \s: French non-breaking spaces stay
    if len(s) <= n: return s
    h = s[:n].rsplit(" ", 1)[0]
    return h + " …"


def detok(s):
    """Join guard tokens ('l ' œsophage ( ESCC') back into readable text."""
    s = re.sub(r"\s+([,.;:)\]%])", r"\1", s)
    s = re.sub(r"([(\[])\s+", r"\1", s)
    s = re.sub(r"(\w)\s*(['’])\s*(\w)", r"\1\2\3", s)
    s = re.sub(r"(\w) - (\w)", r"\1-\2", s)
    s = re.sub(r"(\w) / (\w)", r"\1/\2", s)
    return s.strip()


def recover(tokstr, *texts):
    """The original spelling of a space-joined token string, looked up in `texts` (falls back to detok)."""
    toks = tokstr.split()
    if not toks: return ""
    rx = re.compile(r"\s*".join(re.escape(t) for t in toks), re.I)
    for t in texts:
        m = rx.search(lock.norm(t)) if t else None
        if m: return m.group(0)
    return detok(tokstr)


def strip_punct(s): return re.sub(r"^[\s,.;:()\[\]–—-]+|[\s,.;:(\[–—-]+$", "", s)


def words_list(lang, ws, n=6):
    ws = list(dict.fromkeys(ws))
    out = ", ".join(ws[:n])
    return out + (" " + tr(lang, "more", n=len(ws) - n) if len(ws) > n else "")


def case_in(text, w):
    m = re.search(r"(?<!\w)" + re.escape(w) + r"(?!\w)", text, re.I)
    return m.group(0) if m else w


def phrases(bag, text, lang, maxlen=110):
    """Group a bag of guard lemmas (content words of the old text) into the readable phrases of `text` they come from.
    -> (phrases, leftover words)."""
    need = Counter(w.lower() for w in bag.split())
    toks = [(m.group(0), m.start(), m.end()) for m in WTOK.finditer(text)]
    occ = [i for i, (t, _, _) in enumerate(toks) if t.lower() in need]
    clusters, cur = [], []
    for i in occ:
        if cur and i - cur[-1] > 4: clusters.append(cur); cur = []
        cur.append(i)
    if cur: clusters.append(cur)
    def gain(c, rem): return sum(min(n, rem[w]) for w, n in Counter(toks[i][0].lower() for i in c).items())
    chosen, rem = [], Counter(need)
    while +rem:
        best = max(clusters, key=lambda c: (gain(c, rem), -c[0]), default=None)
        if not best or gain(best, rem) == 0: break
        chosen.append(best); clusters.remove(best)
        rem -= Counter(toks[i][0].lower() for i in best)
    chosen.sort()
    ph = [clip(text[toks[c[0]][1]:toks[c[-1]][2]], maxlen) for c in chosen]
    left = [w for w in rem.elements()]
    return ph, left


def _quoted(lang, items, n=2):
    s = " ; ".join(q(lang, p) for p in items[:n]) if rl(lang) == "fr" else "; ".join(q(lang, p) for p in items[:n])
    return s + (" " + tr(lang, "more", n=len(items) - n) if len(items) > n else "")


def _de_spans(de_old, de_new):
    """-> {guard de_txt: (old original substring, new original substring, (a0, a1) in de_old, (b0, b1) in de_new)} for
    every German op (a span is None when that side is empty)."""
    a, b, ops = lock.de_ops(de_old, de_new)
    sa, sb = lock.tok_spans(de_old), lock.tok_spans(de_new)
    res = {}
    for _, i1, i2, j1, j2 in ops:
        key = f"«{' '.join(a[i1:i2])}» -> «{' '.join(b[j1:j2])}»"
        A = (sa[i1][1], sa[i2 - 1][2]) if i2 > i1 else None
        B = (sb[j1][1], sb[j2 - 1][2]) if j2 > j1 else None
        res[key] = (de_old[A[0]:A[1]] if A else "", de_new[B[0]:B[1]] if B else "", A, B)
    return res


def _de_ops(de_old, de_new):
    """-> {guard de_txt: (old original substring, new original substring)} for every German op."""
    return {k: (u, v) for k, (u, v, _, _) in _de_spans(de_old, de_new).items()}


# ------------------------------------------------------------------------------------------- change applied (G2) wording
# The guard pairs the German op's old and new side as difflib aligned them; across a rewritten passage that pairs
# unrelated fragments ('Das Dosierungsschema' -> 'Eine Kostengutsprache hat den … Indikationscode'). The sentence names
# the pair only when the two sides are recognisably the same words (an orthographic or inflectional change, a renamed
# product); otherwise it names only what the check looks for: the German addition (kind 'add') or removal ('remove'),
# as the whole sentence when the op covers most of one ('the German adds a sentence here; check it is translated').
RELATED = 0.75        # character similarity (folded) from which the two sides of a German op are shown as a pair
RELATED_PREFIX = 5    # ... or a shared start of this many letters with a similarity of at least 0.5 (Nemolizumab / NEMLUVIO
                      # is not a pair; Monaten / Monate, Zeitpunkt / Zeit-punkt are)
SENT_COVER = 0.6      # an op covering this share of a sentence's characters is shown as that sentence


def _fold_txt(s):
    return re.sub(r"[^\w]+", "", s.lower().replace("ß", "ss"))


def related(u, w):
    """True when the old and new side of a German op are recognisably the same words (Zeitpunkt / Zeit-punkt,
    Nemolizumab / NEMLUVIO), so 'u → w' reads as a change and not as two unrelated fragments."""
    a, b = _fold_txt(u), _fold_txt(w)
    if not a or not b: return False
    if a.isdigit() and b.isdigit(): return True
    if all(re.search(r"\d", t) and len(t.split()) <= 4 for t in (u, w)): return True          # 48 Wochen -> 18 Monaten
    r = difflib.SequenceMatcher(None, a, b, autojunk=False).ratio()
    return r >= RELATED or (r >= 0.5 and len(a) >= RELATED_PREFIX and a[:RELATED_PREFIX] == b[:RELATED_PREFIX])


def covered_sentences(text, span):
    """The sentence(s) of text that span covers to at least SENT_COVER of their characters (stripped), as one passage,
    or None. A 'sentence' of fewer than three words (a code number after 'zu übermitteln:') does not count."""
    if not span: return None
    from .segment import sentences
    a, b = span; hit = []
    for s0, s1 in sentences(text):
        n = len(text[s0:s1].strip())
        if len(re.findall(r"[^\W\d_]{2,}", text[s0:s1])) < 3: continue
        if n and max(0, min(b, s1) - max(a, s0)) >= SENT_COVER * n: hit.append((s0, s1))
    return text[hit[0][0]:hit[-1][1]].strip() if hit else None


def _balance(s):
    """'ohne Preismodell) NEMLUVIO' -> '(ohne Preismodell) NEMLUVIO': an unmatched bracket gets its partner."""
    if s.count(")") > s.count("("): s = "(" + s
    if s.count("(") > s.count(")"): s = s + ")"
    return s


def g2_text(lang, kind, x, u, w, sa, sb, out=None):
    """The plain sentence of one change-not-applied finding (see the comment above). With the draft (out), a sentence the
    German adds or rewrites is stated, not hedged, when the draft's aligned sentences say it (counterpart()): missing (the
    draft only carries over old sentences there) or left in German; a sentence the German removes that the draft carries
    over unchanged is named (kept_sentence())."""
    U, W = (_balance(clip(strip_punct(t), 90)) for t in (u, w))
    if U and W and related(u, w): return tr(lang, "g2_rep", u=q(lang, U), v=q(lang, W))
    if kind == "remove" or not W:
        s = covered_sentences(x["de_old"], sa)
        if s:
            k = kept_sentence(x, out, sa) if out else None
            if k: return tr(lang, "g2_del_kept", u=q(lang, clip(s, 120)), x=q(lang, clip(k, 120)))
            return tr(lang, "g2_del_s", u=q(lang, clip(s, 120)))
        return tr(lang, "g2_del", u=q(lang, U or "∅"))
    s = covered_sentences(x["de_new"], sb)
    if s:
        c = counterpart(x, out, sb, sa) if out else None
        if c and c[0] == "missing": return tr(lang, "g2_add_miss", v=q(lang, clip(s, 120)))
        if c and c[0] == "german": return tr(lang, "g2_add_de", v=q(lang, clip(s, 120)), x=q(lang, clip(c[1], 80)))
        return tr(lang, "g2_add_s", v=q(lang, clip(s, 120)))
    return tr(lang, "g2_add", v=q(lang, W))


GERMAN_SHARE = 0.5    # a draft passage with at least this share of the German sentence's content words, verbatim, is German


def _skey(s):
    from ..house import key
    return key(s)


def _sents(text):
    from .segment import sentences
    return [(a, b) for a, b in sentences(text) if text[a:b].strip()]


def counterpart(x, out, sb, sa=None):
    """What the draft has where the German adds or rewrites the sentence(s) at span sb of the new German, by aligned
    sentence beads (emit.segment.align, new German / draft): ("german", passage) when the draft's aligned text holds at
    least GERMAN_SHARE (and two or more) of the German sentence's content words verbatim, not counting words the old target
    text has too (names); ("missing", None) when every draft sentence there is carried over unchanged from the old text,
    i.e. nothing in the draft translates it; else None (not decided: the hedged wording stays)."""
    from .segment import align
    de, dr = x["de_new"], out
    a, b = sb
    B = [(a0, a1, b0, b1) for a0, a1, b0, b1 in align(de, dr) if a0 < b and a < a1]
    if not B: return None
    tgt = dr[B[0][2]:B[-1][3]]
    cw = [w for w in re.findall(r"[^\W\d_]{3,}", de[a:b]) if core.guards.content(w, "de")                   # names the old
          and not re.search(r"(?<!\w)" + re.escape(w) + r"(?!\w)", x["tgt_old"], re.I)]                    # text has too: not German
    if cw:
        hit = [w for w in cw if re.search(r"(?<!\w)" + re.escape(w) + r"(?!\w)", tgt)]
        if len(hit) >= GERMAN_SHARE * len(cw) and len(hit) >= 2:
            m = re.search(r"(?<!\w)" + re.escape(hit[0]) + r"(?!\w).*?(?<!\w)" + re.escape(hit[-1]) + r"(?!\w)", tgt)
            return ("german", m.group(0) if m else ", ".join(hit[:4]))
    olds = {_skey(x["tgt_old"][p:r]) for p, r in _sents(x["tgt_old"])}
    S = [(p, r) for p, r in _sents(tgt)]
    if not S or any(_skey(tgt[p:r]) not in olds for p, r in S): return None
    return ("missing", None)


def kept_sentence(x, out, sa):
    """The old target sentence(s) aligned (emit.segment.align, old German / old target) to the German sentence(s) at span
    sa of the old German, when the draft still carries every one of them over unchanged; else None."""
    from .segment import align
    a, b = sa; to = x["tgt_old"]
    B = [(a0, a1, b0, b1) for a0, a1, b0, b1 in align(x["de_old"], to) if a0 < b and a < a1]
    if not B or len(B) > 1: return None
    sub = to[B[0][2]:B[0][3]]; S = [sub[p:r] for p, r in _sents(sub)]
    drs = {_skey(out[p:r]) for p, r in _sents(out)}
    if S and all(_skey(t) in drs for t in S) and len(re.findall(r"[^\W\d_]{2,}", " ".join(S))) >= 3: return " ".join(t.strip() for t in S)
    return None


# ------------------------------------------------------------------------------------------- deletions that mirror the German
# A 'removed more than the German' finding (G3c) is the guard's net content loss in the target window of a German op.
# When the German itself drops a sentence, the draft dropping the aligned French / Italian sentence is the expected
# change. mirror() decides that by position: the old German and old target are cut into aligned sentence beads
# (emit.segment.align, the XLIFF segmentation); a bead mirrors a German deletion when the German change removes at
# least MIRROR_DE of the bead's German content words and the draft removes at most MIRROR_SLACK more of the bead's
# target content words than that. The finding's lost words are looked up among the target words the draft removed inside
# the target edits the guard counts for the finding's German ops (an edit touching one of their lock windows), occurrences
# outside mirroring beads first.
# Wording only: the finding, its triage status and the verdict are unchanged.
MIRROR_DE, MIRROR_SLACK = 0.5, 0.25
WHOLE = 0.8           # a sentence both sides remove (nearly) whole: this share of its content words on each side
PHRASE_TOL, PHRASE_RATIO = 0.15, 2


def _gone(a, b):
    """-> (token spans of a, [token of a removed or replaced in b]) (lock tokens, difflib as the guards use it)."""
    A = lock.tok_spans(a); B = lock.tok(b); out = [False] * len(A)
    for op, i1, i2, _, _ in difflib.SequenceMatcher(None, [t for t, _, _ in A], B, autojunk=False).get_opcodes():
        if op in ("replace", "delete"):
            for i in range(i1, i2): out[i] = True
    return A, out


def _share(T, gone, lo, hi, lang):
    idx = [i for i, (t, s, _) in enumerate(T) if lo <= s < hi and core.guards.content(t, lang)]
    return sum(gone[i] for i in idx) / len(idx) if idx else 0.0


def _runs(T, gone, lo, hi, lang):
    """-> [[start, end, content words]] of the runs of removed tokens of T inside [lo, hi)."""
    out, cur = [], None
    for i, (t, s, e) in enumerate(T):
        if not (lo <= s < hi): continue
        if gone[i]:
            if cur is None: cur = [s, e, 0]; out.append(cur)
            cur[1] = e; cur[2] += core.guards.content(t, lang)
        else: cur = None
    return [r for r in out if r[2]]


def mirror(x, out, des, bag):
    """-> dict(lost=n words of the bag, mirrored=n of them where the draft mirrors a German deletion, de=the German
    passage removed there, replaced=whether the German wrote something in its place) for one G3c finding (des: its German
    ops as the guard writes them, bag: its lost content words). A lost word mirrors a German deletion when its sentence
    bead does (MIRROR_DE, MIRROR_SLACK), or, for a phrase, when the German removes a passage of the same bead at the same
    relative place (within PHRASE_TOL of the bead's length) and the draft's lost words there are at most PHRASE_RATIO
    times the passage's content words plus one ('nicht-kleinzelligem Lungenkarzinom (NSCLC)' -> 'NSCLC', 'carcinoma
    polmonare non a piccole cellule (NSCLC)' -> 'NSCLC'). whole: every lost word sits in sentence beads that the German and
    the draft both remove whole (>= WHOLE of their content words on each side): the draft drops the sentence that
    translates the sentence the German drops, one to one (tgt: those old target sentences)."""
    L = x["lang"]
    do, dn, to, tn = lock.norm(x["de_old"]), lock.norm(x["de_new"]), lock.norm(x["tgt_old"]), lock.norm(out)
    DA, dgone = _gone(do, dn); TA, tgone = _gone(to, tn)
    beads = segment_align(do, to)
    mir = [_share(DA, dgone, a0, a1, "de") >= MIRROR_DE and
           _share(TA, tgone, b0, b1, L) <= _share(DA, dgone, a0, a1, "de") + MIRROR_SLACK for a0, a1, b0, b1 in beads]
    druns = [_runs(DA, dgone, a0, a1, "de") for a0, a1, _, _ in beads]
    budget = {(k, j): PHRASE_RATIO * r[2] + 1 for k, R in enumerate(druns) for j, r in enumerate(R)}
    a, b, dops = lock.de_ops(x["de_old"], x["de_new"]); W, _ = lock.windows(x["de_old"], x["de_new"], to)     # as the guard
    keys = [f"«{' '.join(a[i1:i2])}» -> «{' '.join(b[j1:j2])}»" for _, i1, i2, j1, j2 in dops]
    win = [W[k] for k, key in enumerate(keys) if key in set(des)]
    _, _, E = core.guards.tgt_ops(to, tn)                       # the guard's target edits, kept when they touch a window
    near = {i for e in E if any(core.guards.in_win(e, lo, hi) for lo, hi in win) for i in range(e[1], e[2])}
    bead_of = lambda s: next((k for k, (_, _, b0, b1) in enumerate(beads) if b0 <= s < b1), None)

    def phrase(k, s):
        """the German run of bead k at the relative place of target offset s, with budget left, or None"""
        a0, a1, b0, b1 = beads[k]; rt = (s - b0) / max(1, b1 - b0)
        for j, (rs, re_, _) in enumerate(druns[k]):
            if budget[(k, j)] >= 1 and (rs - a0) / max(1, a1 - a0) - PHRASE_TOL <= rt <= (re_ - a0) / max(1, a1 - a0) + PHRASE_TOL:
                return j
        return None
    cand = [(i, bead_of(s)) for i, (t, s, _) in enumerate(TA) if tgone[i] and i in near]
    cand.sort(key=lambda c: (c[1] is not None and mir[c[1]], c[0]))                 # non-mirroring occurrences first
    need = Counter(bag.split()); used = Counter()
    for i, k in cand:
        w = TA[i][0].lower()
        if need[w] <= 0: continue
        need[w] -= 1
        if k is None: continue
        if mir[k]: used[(k, None)] += 1; continue
        j = phrase(k, TA[i][1])
        if j is not None: budget[(k, j)] -= 1; used[(k, j)] += 1
    lost, hit = sum(Counter(bag.split()).values()), sum(used.values())
    whole = bool(used) and all(j is None and _share(DA, dgone, beads[k][0], beads[k][1], "de") >= WHOLE
                               and _share(TA, tgone, beads[k][2], beads[k][3], L) >= WHOLE for k, j in used)
    K = sorted({k for k, _ in used})
    tg = " ".join(re.sub(r"\s+", " ", to[beads[k][2]:beads[k][3]]).strip() for k in K) if whole else ""
    de, replaced = "", False
    if used:                                  # the German passage removed where most of the lost words are
        k, j = used.most_common(1)[0][0]
        R = druns[k]
        if R:
            r = R[j] if j is not None else max(R, key=lambda r: r[1] - r[0]); de = do[r[0]:r[1]]
            sm = difflib.SequenceMatcher(None, [t for t, _, _ in DA], lock.tok(dn), autojunk=False)
            first = next(i for i, (_, s, _) in enumerate(DA) if s == r[0])
            replaced = any(op == "replace" and i1 <= first < i2 for op, i1, i2, _, _ in sm.get_opcodes())
        if whole: de = " ".join(re.sub(r"\s+", " ", do[beads[k][0]:beads[k][1]]).strip() for k in K)
    return dict(lost=lost, mirrored=hit, de=de, replaced=replaced, whole=whole, tgt=tg)


def tally_mirrored(x, out, detail):
    """A negation / modal-verb count finding ('Slots: neg …', 'Slots: modal:K …') that is only the effect of sentences
    the German and the draft both remove: with every aligned sentence bead that both remove (>= WHOLE of its
    content words on each side) left out of the old texts, the German and the draft change the count alike. Wording only
    (the review page and the XLIFF notes rank it like a count a triage rule calls probably fine); the finding stays."""
    m = re.match(r"Slots: (neg|modal:(\w+)) ", detail or "")
    if not m: return False
    key = (lambda c: c["neg"]) if m.group(1) == "neg" else (lambda c, k=m.group(2): c["modal"][k])
    L = x["lang"]; cnt = lambda s, lang: key(lock.slots(s, lang))
    do, dn, to, tn = lock.norm(x["de_old"]), lock.norm(x["de_new"]), lock.norm(x["tgt_old"]), lock.norm(out)
    DA, dgone = _gone(do, dn); TA, tgone = _gone(to, tn)
    gone = [(a0, a1, b0, b1) for a0, a1, b0, b1 in segment_align(do, to)
            if _share(DA, dgone, a0, a1, "de") >= WHOLE and _share(TA, tgone, b0, b1, L) >= WHOLE]
    if not gone: return False
    dd = cnt(x["de_new"], "de") - cnt(x["de_old"], "de") + sum(cnt(do[a0:a1], "de") for a0, a1, _, _ in gone)
    dt = cnt(out, L) - cnt(x["tgt_old"], L) + sum(cnt(to[b0:b1], L) for _, _, b0, b1 in gone)
    return dd == dt


def segment_align(src, tgt):
    from .segment import align
    return align(src, tgt)


# ------------------------------------------------------------------------------------------- repetitions the German has too
# A 'passage repeated' finding (G4) names 6-grams the draft writes more often than the old text. When the German repeats
# the corresponding passage too ('ou d'une perte de vision' x2 where the German says 'oder eines Visusverlustes durch' x2),
# the repetition is the translation's, not a duplication: german_repeats() decides it by position (aligned sentence beads,
# new German / draft): every occurrence of the repeated passage in the draft lies in a bead whose German side has an
# occurrence of one German word trigram (words cut to their first STEM letters, at least one word of 4+ letters) that the
# new German has at least as many times as the draft has the passage, at the same relative place (within REP_TOL of the
# bead's length). Wording only: a low-priority 'the German repeats it too'.
STEM, REP_TOL = 5, 0.2
_GW = re.compile(r"[^\W\d_]+")


def _stem_grams(text, a0, a1):
    W = [(m.group(0).lower()[:STEM], m.start(), len(m.group(0))) for m in _GW.finditer(text, a0, a1)]
    return [(" ".join(w for w, _, _ in W[i:i + 3]), W[i][1]) for i in range(len(W) - 2) if any(n >= 4 for _, _, n in W[i:i + 3])]


def german_repeats(x, out, detail):
    """True when every passage of a G4 finding (detail 'G4 repeated 6-grams: «…»; «…»') repeats where the German repeats
    the corresponding passage too (see above)."""
    grams = re.findall(r"«([^«»]+)»", detail or "")
    if not grams: return False
    de, dr = lock.norm(x["de_new"]), lock.norm(out)
    beads = segment_align(de, dr)
    G = [_stem_grams(de, a0, a1) for a0, a1, _, _ in beads]
    tot = Counter(g for gs in G for g, _ in gs)
    for g in grams:
        occ = [m.start() for m in re.finditer(r"\W+".join(re.escape(w) for w in g.split()), dr, re.I)]
        if len(occ) < 2: return False
        ok_for = None
        for s in occ:
            k = next((k for k, (_, _, b0, b1) in enumerate(beads) if b0 <= s < b1), None)
            if k is None: return False
            a0, a1, b0, b1 = beads[k]; rt = (s - b0) / max(1, b1 - b0)
            here = {gg for gg, p in G[k] if abs((p - a0) / max(1, a1 - a0) - rt) <= REP_TOL and tot[gg] >= len(occ)}
            ok_for = here if ok_for is None else ok_for & here
            if not ok_for: return False
    return True


# ------------------------------------------------------------------------------------------- German-looking target words
def lexicon_fine(v, f):
    """-> (words of a German-left / copied-from-German finding (G1, G5) that are probably fine, the other words): a word is
    probably fine when the old target text has it (as a whole word) or when it is a word the German and the target register
    share (termbase.shared: 'allergie' is French too), unless it is a German function word. Wording only."""
    if f.get("gid") not in ("g1", "g5"): return [], []
    from .. import audit, termbase
    L = v["lang"]; W = [w.strip() for w in (f.get("detail") or "").split(":", 1)[-1].split(",") if w.strip()]
    if f["gid"] == "g5":
        g1 = next((g for g in v.get("findings", []) if g.get("gid") == "g1"), None)
        seen = {w.strip().lower() for w in (g1["detail"].split(":", 1)[-1].split(",") if g1 else [])}
        W = [w for w in W if w.lower() not in seen]
    S, FW = termbase.shared(L), set(audit.FW["de"])
    old = v.get("tgt_old") or ""
    fine = [w for w in W if w.lower() not in FW and (w.lower() in S or re.search(r"(?<!\w)" + re.escape(w) + r"(?!\w)", old, re.I))]
    return fine, [w for w in W if w not in fine]


# ------------------------------------------------------------------------------------------- typography (not a check)
# Spacing artefacts the draft introduces around text it inserted ('( sans modèle de prix )', 'et / ou', 'maladie ,'):
# counted in the draft and in the old text; a pattern the draft has more often than the old text is named in one
# low-priority note. Display only, never a check, never a verdict. French spaces before ; : ! ? » are correct and
# are not counted.
SP = r"[   ]"
TYPO = [("open", re.compile(r"\(" + SP + r"+(?=\S)")), ("close", re.compile(r"(?<=\S)" + SP + r"+\)")),
        ("comma", re.compile(r"(?<=\w)" + SP + r"+,")), ("stop", re.compile(r"(?<=\w)" + SP + r"+\.(?!\d)")),
        ("slash", re.compile(r"(?<=\w)" + SP + r"+/" + SP + r"*(?=\w)|(?<=\w)/" + SP + r"+(?=\w)")),
        ("double", re.compile(r"[.,;:]" + SP + r"*[.,;:](?!\.)")), ("space", re.compile(r"(?<=\S)" + SP + r"{2,}(?=\S)"))]


def typography(old, draft):
    """-> [(pattern id, snippet of the draft around its first new occurrence)] for every pattern of TYPO the draft has
    more often than the old text (a number like 1.5 or an ellipsis '...' is not a pattern)."""
    out = []
    for k, rx in TYPO:
        if len(rx.findall(draft)) <= len(rx.findall(old or "")): continue
        olds = {re.sub(r"\s+", " ", old[max(0, m.start() - 12):m.end() + 12]) for m in rx.finditer(old or "")}
        for m in rx.finditer(draft):
            a = max(0, m.start() - 18); b = min(len(draft), m.end() + 18)
            snip = draft[a:b]
            if re.sub(r"\s+", " ", draft[max(0, m.start() - 12):m.end() + 12]) in olds: continue
            snip = (snip.split(" ", 1)[1] if a > 0 and " " in snip[:10] else snip)
            snip = (snip.rsplit(" ", 1)[0] if b < len(draft) and " " in snip[-10:] else snip)
            out.append((k, snip.strip())); break
    return out


def _delta(lang, d, fem=False):
    return tr(lang, "add_n", n=d) if d > 0 else tr(lang, "rem_n", n=-d) if d < 0 else tr(lang, "none_f" if fem else "none_n")


def _times(c):
    """'20481 (×2), 56': each value once, with how often when more than once (so equal-looking lists show their counts)."""
    return ", ".join(k + (f" (×{c[k]})" if c[k] > 1 else "") for k in sorted(c))


def _numch(lang, add, rem):
    p = []
    if add: p.append(tr(lang, "n_add", x=_times(add)))
    if rem: p.append(tr(lang, "n_rem", x=_times(rem)))
    return ", ".join(p) if p else tr(lang, "n_none")


# ------------------------------------------------------------------------------------------- number values (corrections)
def values(s, lang):
    """Counter of number values in s: digits (lock.nums normalisation) + number words 2..12 of the language."""
    c = Counter()
    for k, n in lock.nums(s).items(): c[k.replace(",", ".")] += n
    for i, w in enumerate(gl2.NUMW[lang]):
        if i < 2: continue
        n = len(re.findall(r"(?<!\w)" + re.escape(w) + r"(?!\w)", s, re.I))
        if n: c[str(i)] += n
    return c


def _surface(s, lang, v):
    """How value v is written in s (the number word if s writes it as a word, else the digits)."""
    if v.isdigit() and 2 <= int(v) <= 12:
        w = gl2.NUMW[lang][int(v)]
        if re.search(r"(?<!\w)" + re.escape(w) + r"(?!\w)", s, re.I): return w
    return v


def _around(text, a, b):
    """text[a:b] widened by one word on each side (punctuation trimmed)."""
    pre = re.search(r"(\S+\s+)?$", text[:a]).group(0); post = re.match(r"(\s+\S+)?", text[b:]).group(0)
    return strip_punct(pre + text[a:b] + post)


def _val(tok, lang):
    t = tok.lower()
    if t in gl2.NUMW[lang][2:]: return str(gl2.NUMW[lang].index(t))
    return re.sub(r"[ '’]", "", tok).replace(",", ".") if re.match(r"\d", tok) else None


def _where(x, out, gone, came):
    """Phrase pairs (old target, draft) around the tokens the draft changed for the corrected values."""
    L = x["lang"]; A = list(WTOK.finditer(x["tgt_old"])); B = list(WTOK.finditer(out))
    sm = difflib.SequenceMatcher(None, [m.group(0) for m in A], [m.group(0) for m in B], autojunk=False)
    res = []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal": continue
        if any(_val(m.group(0), L) in gone for m in A[i1:i2]) or any(_val(m.group(0), L) in came for m in B[j1:j2]):
            o = _around(x["tgt_old"], A[i1].start(), A[i2 - 1].end()) if i2 > i1 else ""
            n = _around(out, B[j1].start(), B[j2 - 1].end()) if j2 > j1 else ""
            res.append((o, n))
    return res


def corrections(x, out):
    """Numbers the German does not touch, on which the old target disagreed with the old German and the draft moves
    the target towards the German. -> dict(old=[surface], new=[surface], de=[surface], values=set) or None."""
    L = x["lang"]
    so, sn, to, tn = values(x["de_old"], "de"), values(x["de_new"], "de"), values(x["tgt_old"], L), values(out, L)
    gone, came = [], []
    for v in set(so) | set(to) | set(tn):
        if so[v] != sn[v]: continue                                   # the German change touches v: not a correction
        before, after = to[v] - so[v], tn[v] - sn[v]
        if abs(after) < abs(before):
            (gone if before > 0 else came).append(v)
    if not gone and not came: return None
    de = []
    for v in sorted(came):
        w = _surface(x["de_new"], "de", v)
        m = re.search(r"(?<!\w)" + re.escape(w) + r"(?!\w)", x["de_new"], re.I)
        de.append(_around(x["de_new"], m.start(), m.end()) if m else w)
    return dict(old=[_surface(x["tgt_old"], L, v) for v in sorted(gone)], new=[_surface(out, L, v) for v in sorted(came)],
                de=de, values=set(gone) | set(came), where=_where(x, out, set(gone), set(came)))


# ------------------------------------------------------------------------------------------- audit (teammate module)
try:
    from ..audit import audit_item as _audit_item          # noqa: F401
except Exception:                                          # not built / not importable: no divergence banner
    _audit_item = None

_DEK = ("de", "de_value", "de_old", "german", "de_num", "de_text", "de_surface", "de_ctx", "src")
_TGK = ("tgt", "tgt_value", "tgt_old", "target", "tgt_num", "tgt_text", "tgt_surface", "tgt_ctx", "fr", "it", "trg")
_TXK = ("text", "msg", "message", "note", "summary", "detail", "what")


_OLDK = ("old_term", "term_old", "old", "from", "surface", "stale", "x")
_NEWK = ("new_term", "term_new", "new", "to", "suggestion", "corrected", "y")
_WHEREK = ("corrected_in", "where", "fixed_in", "corrected", "examples", "ids", "limitations", "seen_corrected", "evidence")


_PRODUCTS = {}
def _item_product(key):
    """The product (brand) of a recorded item key (wb021-fr -> 'Exforge HCT'), from the shipped item sets; None if unknown."""
    if not key: return None
    if not _PRODUCTS:
        try:
            from .. import score
            from ..ui.build import brand
            for run in ("fresh166", "oos242"):
                for x in score.load_items(score.RUNS[run]["items"]):
                    if x.get("product"): _PRODUCTS.setdefault(x["key"], brand(x["product"]))
        except Exception: _PRODUCTS["-"] = None
    return _PRODUCTS.get(key)


def term_parts(d, lang=None):
    """-> (old term, new term, [where BAG already corrected it]) of an audit finding of kind 'terminology', from whichever
    keys the audit uses (old_term / new_term / corrected_in, values {old, new}, a 'X -> Y' string, ...); None / [] when
    absent."""
    def pick(keys):
        for k in keys:
            v = d.get(k)
            if isinstance(v, dict) and lang in v: v = v[lang]
            if isinstance(v, (list, tuple)) and v and all(isinstance(x, str) for x in v) and k not in _WHEREK: v = v[0]
            if isinstance(v, str) and v.strip(): return v.strip()
        return None
    o, n = pick(_OLDK), pick(_NEWK)
    V = d.get("values")
    if isinstance(V, dict):
        o = o or (V.get("old") if isinstance(V.get("old"), str) else None); n = n or (V.get("new") if isinstance(V.get("new"), str) else None)
    elif isinstance(V, (list, tuple)) and len(V) == 2 and all(isinstance(x, str) for x in V) and not (o or n):
        o, n = V
    if not (o and n):
        m = re.search(r"[«“\"']([^»”\"']+)[»”\"']\s*(?:->|→|to|en|in)\s*[«“\"']([^»”\"']+)[»”\"']", str(d.get("detail") or d.get("description") or ""))
        if m: o, n = o or m.group(1), n or m.group(2)
    where = []
    for k in _WHEREK:
        v = d.get(k)
        if k in ("corrected", "examples") and isinstance(v, str): continue
        if isinstance(v, str) and v.strip(): where = [v.strip()]; break
        if isinstance(v, (list, tuple)) and v:
            for x in v:
                if isinstance(x, str): where.append(x)
                elif isinstance(x, dict):
                    p = x.get("product") or x.get("name"); i = x.get("id") or x.get("limitation") or x.get("code")
                    p = ", ".join(p) if isinstance(p, (list, tuple)) else p
                    src = str(x.get("source") or "")
                    if isinstance(i, str) and i.startswith("RA:"):            # old-format key: name the item it came from
                        k = src.split(":", 1)[1] if src.startswith("items:") else None
                        p = p or _item_product(k)
                        i = None if p else (k or i[:11] + "…")
                    if isinstance(i, str): i = i.split("---")[0]
                    when = x.get("after") or x.get("date")
                    lab = f"{p} ({i})" if p and i else str(p or i or "")
                    if lab and isinstance(when, str) and re.fullmatch(r"\d{8}", when): lab += f", {when[6:8]}.{when[4:6]}.{when[:4]}"
                    if lab: where.append(lab)
            if where: break
    return o, n, where


def found_language(d, lang):
    """The language an old text was found to be in, from an audit finding of kind 'language' (None when not stated):
    a found / detected / actual / is_lang key, values[lang], or a language name in the detail sentence."""
    for k in ("found", "detected", "actual", "is_lang", "found_lang", "detected_lang"):
        v = d.get(k)
        if isinstance(v, str) and v.lower()[:2] in LANGNAME["en"] and v.lower()[:2] != lang: return v.lower()[:2]
    v = d.get("values")
    if isinstance(v, dict):
        v = v.get(lang)
        if isinstance(v, (list, tuple)) and v: v = v[0]
        if isinstance(v, str) and v.lower()[:2] in LANGNAME["en"] and v.lower()[:2] != lang: return v.lower()[:2]
    txt = " ".join(str(d.get(k) or "") for k in ("detail", "text", "description", "message"))
    m = re.search(r"\b(?:is|in|carries|contains|written in|est en|è in)\s+(\w+)", txt, re.I)
    for code, rx in _LANGWORDS.items():
        if code != lang and m and re.match(rx, m.group(1), re.I): return code
    hits = [code for code, rx in _LANGWORDS.items() if code != lang and re.search(rx, txt, re.I)]
    return hits[0] if len(hits) == 1 else None


def _kind(d):
    k = str(d.get("kind") or "").lower()
    if k in KINDS: return k
    if k in ("numeric", "num", "numbers"): return "number"
    if k in ("lang", "wrong_language", "wrong-language"): return "language"
    if k in ("term", "terms", "terminology", "term_pair"): return "terminology"
    return "number" if ("side" in d or "value" in d or "values" in d) else "editorial"


def divergence(x):
    """-> [dict(text=..., raw=..., kind=number|unit|language|editorial, found=lang or None)] from
    gleichlaut.audit.audit_item(x), [] when absent or empty. Accepts the current shape (dicts with side / value / unit /
    context), the extended one (dicts with kind, lang, detail, values, odd_one_out), a dict with a list under
    divergences / findings / items, (de, tgt) pairs or strings. Findings for the other target language are skipped."""
    if _audit_item is None: return []
    try: r = _audit_item(x)
    except Exception: return []
    if isinstance(r, dict):
        r = next((r[k] for k in ("divergences", "findings", "items", "numbers") if isinstance(r.get(k), list)), [r] if r else [])
    if not r: return []
    L, res = x["lang"], []
    for d in r if isinstance(r, (list, tuple)) else [r]:
        raw = d if isinstance(d, str) else repr(d)
        kind, found = "number", None
        if isinstance(d, dict):
            kind = _kind(d)
            dl = d.get("lang") if d.get("lang") is not None else d.get("langs")
            if isinstance(dl, str) and dl in ("fr", "it") and dl != L: continue
            if isinstance(dl, (list, tuple)) and set(dl) & {"fr", "it"} and L not in dl: continue
        if isinstance(d, dict) and kind == "terminology":
            old_t, new_t, where = term_parts(d, L)
            given = d.get("text") if isinstance(d.get("text"), str) and d.get("text").strip() else None
            if given: txt = given
            elif old_t and new_t:
                w = tr(L, "term_w", x=", ".join(where[:3]) + (f" {tr(L, 'more', n=len(where) - 3)}" if len(where) > 3 else "")) if where else ""
                txt = tr(L, "term", a=q(L, old_t), b=q(L, new_t), w=w)
            else: txt = next((str(d[k]) for k in _TXK if d.get(k)), raw)
            res.append(dict(text=clip(txt, 260), raw=raw, kind=kind, found=None, old=old_t, new=new_t, where=where))
            continue
        if isinstance(d, dict) and kind == "language":
            found = found_language(d, L)
            det = next((str(d[k]) for k in _TXK if d.get(k)), "")
            txt = tr(L, "lang_is", x=LANGNAME[rl(L)][found]) if found else tr(L, "lang_not", x=clip(det or raw, 120))
        elif isinstance(d, dict) and "side" in d and ("context" in d or "value" in d):
            ctxs = d.get("context") or []
            c = ctxs[0] if isinstance(ctxs, list) and ctxs else ctxs if isinstance(ctxs, str) else ""
            m = re.search(r"(\S*\s+)?\[([^\]]+)\](\S*(?:\s+[^\s.,;:)]+)?)?", c)
            phrase = strip_punct(m.group(0).replace("[", "").replace("]", "")) if m else str(d.get("value", ""))
            if d.get("unit") and m and d["unit"] not in phrase: phrase += " " + d["unit"]
            txt = tr(L, "div_de" if d["side"] == "de" else "div_tg", c=q(L, clip(phrase, 60)))
        elif isinstance(d, dict):
            vals = d.get("values") if isinstance(d.get("values"), dict) else {}
            de = next((d[k] for k in _DEK if d.get(k) not in (None, "")), vals.get("de"))
            tg = next((d[k] for k in _TGK if d.get(k) not in (None, "")), vals.get(L))
            if de not in (None, "", []) and tg not in (None, "", []):
                fmt = lambda v: ", ".join(map(str, v)) if isinstance(v, (list, tuple, set)) else str(v)
                txt = tr(L, "div_pair", d=q(L, clip(fmt(de), 80)), t=q(L, clip(fmt(tg), 80)))
            else:
                txt = next((str(d[k]) for k in _TXK if d.get(k)), raw)
        elif isinstance(d, (list, tuple)) and len(d) >= 2:
            txt = tr(L, "div_pair", d=q(L, str(d[0])), t=q(L, str(d[1])))
        else:
            txt = str(d)
        res.append(dict(text=clip(txt, 220), raw=raw, kind=kind, found=found))
    return res


def banner(x, divs, out=None):
    """The banner sentence for a pre-existing divergence (None when there is none). When the draft changes the diverging
    passage, the old target's phrase is set against the German one ('ogni quattro settimane' vs 'alle acht Wochen')."""
    if not divs: return None
    L = x["lang"]; c = corrections(x, out) if out else None
    lang = [d["text"] for d in divs if d.get("kind") == "language"]
    term = [d["text"] for d in divs if d.get("kind") == "terminology"]
    rest = [d for d in divs if d.get("kind") not in ("language", "terminology")]
    if not rest: return " ".join(lang + term)
    if c and c["where"] and c["de"]:
        num = tr(L, "div", x=tr(L, "div_vs", t=q(L, c["where"][0][0]), d=q(L, c["de"][0])))
    else:
        num = tr(L, "div", x="; ".join(d["text"] for d in rest[:3]))
    return " ".join(lang + [num] + term)


# ------------------------------------------------------------------------------------------- findings
def findings(x, out, fc, g14):
    """-> [dict(gid, name, gname, text, detail, corrects)] in display order; text in the draft's language.
    fc = Pipeline.check(x, out); g14 = frozen guards.run(x, out) (G1 alone, before guards3 merges G5-G7 into it)."""
    L = x["lang"]; told, F = x["tgt_old"], []
    corr = corrections(x, out)
    csurf = set((corr["old"] + corr["new"]) if corr else [])
    def hit(s): return bool(csurf) and any(re.search(r"(?<!\w)" + re.escape(w) + r"(?!\w)", s, re.I) for w in csurf)
    def add(gid, text, detail, corrects=False):
        F.append(dict(gid=gid, name=GID[gid], gname=NAMES[gid][rl(L)], text=text, detail=detail, corrects=bool(corrects)))

    if not fc["lock"]["ok"]:
        parts, cor = [], False
        for u, v in fc["lock"]["outside"][:3]:
            U, V = recover(u, told), recover(v, out)
            parts.append(tr(L, "lock_add", v=q(L, clip(V, 70))) if not U else tr(L, "lock_del", u=q(L, clip(U, 70))) if not V
                         else f"{q(L, clip(U, 60))} → {q(L, clip(V, 60))}")
            cor = cor or hit(u) or hit(v)
        more = len(fc["lock"]["outside"]) - 3
        add("lock", tr(L, "lock", x="; ".join(parts) + (" " + tr(L, "more", n=more) if more > 0 else "")),
            "Lock: outside the edit windows " + "; ".join(f"«{u}» -> «{v}»" for u, v in fc["lock"]["outside"]), cor)

    if fc["slot"]:
        so, sn = lock.slots(x["de_old"], "de"), lock.slots(x["de_new"], "de")
        to, tn = lock.slots(told, L), lock.slots(out, L)
        for s in fc["slot"]:
            if s == "neg":
                add("slot", tr(L, "neg", de=_delta(L, sn["neg"] - so["neg"], True), tg=_delta(L, tn["neg"] - to["neg"], True)),
                    f"Slots: neg DE {so['neg']}->{sn['neg']}, target {to['neg']}->{tn['neg']}")
            elif s.startswith("modal:"):
                k = s.split(":", 1)[1]
                add("slot", tr(L, "modal", m=MODAL.get(k, {}).get(rl(L), k), de=_delta(L, sn["modal"][k] - so["modal"][k]),
                               tg=_delta(L, tn["modal"][k] - to["modal"][k])),
                    f"Slots: {s} DE {so['modal'][k]}->{sn['modal'][k]}, target {to['modal'][k]}->{tn['modal'][k]}")
            elif s == "nums":
                da, dr = sn["nums"] - so["nums"], so["nums"] - sn["nums"]; ta, tr_ = tn["nums"] - to["nums"], to["nums"] - tn["nums"]
                dec = lambda c: Counter({k.replace(",", "."): n for k, n in c.items()})
                hint = ""
                if (dec(da), dec(dr)) == (dec(ta), dec(tr_)):
                    a_ = next((k for k in list(da) + list(dr) if "." in k), ""); b_ = next((k for k in list(ta) + list(tr_) if "," in k), "")
                    hint = tr(L, "decimal", a=a_, b=b_)
                add("slot", tr(L, "nums", de=_numch(L, da, dr), tg=_numch(L, ta, tr_)) + hint,
                    f"Slots: nums DE +{dict(da)} -{dict(dr)}, target +{dict(ta)} -{dict(tr_)}",
                    corr is not None and bool(set(ta) | set(tr_)) and (set(ta) | set(tr_)) <= corr["values"])
            else:
                add("slot", s, "Slots: " + s)
    if fc["unknown"]:
        add("unknown", tr(L, "unknown", n=fc["unknown"]), f"Slots: {fc['unknown']} unknown slot code(s)")

    g = fc["g"]
    ops = _de_spans(x["de_old"], x["de_new"]) if g["g2"] or g["g3"] else {}
    for kind, de in g["g2"]:
        u, v, sa, sb = ops.get(de, ("", "", None, None))
        add("g2", g2_text(L, kind, x, u, v, sa, sb, out), f"G2 ({kind}): {de}")

    g1 = sorted(set(g14["g1"])) if g14 else []
    if g1: add("g1", tr(L, "g1", x=words_list(L, g1)), "G1: " + ", ".join(g1))
    seen = {w.lower() for w in g1}
    g5 = [w for w in g.get("g5", []) if w.lower() not in seen]
    if g5: add("g5", tr(L, "g5", x=words_list(L, [case_in(out, w) for w in g5])), "G5: " + ", ".join(g.get("g5", [])))
    seen |= {w.lower() for w in g.get("g5", [])}

    bags = {}
    for d in g["g3"]:
        if d[0] == "outside-lost":
            ph, left = phrases(d[2], told, L)
            items = ph + ([", ".join(left)] if left and not ph else [])
            add("g3", tr(L, "g3a", x=_quoted(L, items) + (f" (+ {', '.join(left[:4])})" if left and ph else "")),
                f"G3a lost outside every edit window: {d[2]}", hit(d[2]))
        else:
            bags.setdefault(d[2], []).append(d[1])
    for bag, des in bags.items():
        ph, left = phrases(bag, told, L)
        items = ph + ([", ".join(left)] if left and not ph else [])
        add("g3", tr(L, "g3c", x=_quoted(L, items)),
            "G3c removed beyond the German change: " + " | ".join(f"near {de}: {bag}" for de in des), hit(bag))

    if g["g4"]:
        spans = []
        norm_out = lock.norm(out)
        for n in g["g4"]:
            m = re.search(r"\W+".join(re.escape(w) for w in n.split()), norm_out, re.I)
            if m: spans.append([m.start(), m.end()])
        spans.sort(); merged = []
        for a, b in spans:
            if merged and a <= merged[-1][1]: merged[-1][1] = max(merged[-1][1], b)
            else: merged.append([a, b])
        ph = [clip(norm_out[a:b], 100) for a, b in merged] or g["g4"]
        add("g4", tr(L, "g4", x=_quoted(L, ph)), "G4 repeated 6-grams: " + "; ".join(f"«{n}»" for n in g["g4"]))

    for t in g.get("g6", []):
        a, _, b = t.partition(" -> ")
        add("g6", tr(L, "g6", a=q(L, a), b=q(L, b)), "G6: " + t)
    g7 = [w for w in g.get("g7", []) if w.lower() not in seen]
    if g7: add("g7", tr(L, "g7", x=words_list(L, [case_in(out, w) for w in g7])), "G7: " + ", ".join(g.get("g7", [])))

    F.sort(key=lambda f: ORDER.index(f["gid"]))
    if corr:
        c = dict(gid="corr", name="—", gname="", corrects=True, detail=f"number values {sorted(corr['values'])}: old target "
                 "diverged from the old German, the German change does not touch them, the draft moves them towards the German",
                 text=tr(L, "corr", o=", ".join(q(L, o) for o, _ in corr["where"][:2]) or ", ".join(q(L, s) for s in corr["old"]) or "∅",
                         n=", ".join(q(L, n) for _, n in corr["where"][:2]) or ", ".join(q(L, s) for s in corr["new"]) or "∅",
                         d=", ".join(q(L, s) for s in corr["de"]) or "∅"))
        F.insert(0, c)
    return F


def corr_note(lang): return T["corr_note"][rl(lang)]
def name(gid, lang): return NAMES.get(gid, {}).get(rl(lang), GID.get(gid, gid))


# ------------------------------------------------------------------------------------------- measurement (explain v2)
RESULT_V2 = ("eval", "results", "explain_v2.json")


def _v1_top(v):
    """The reasons the page showed before explain v2 (commit d6671fa): every finding and the model-number note sorted by
    (low, rank), the first three; low = a triage rule applies, a G3c finding whose German ops each remove >= 3 words, or
    pipeline status. Restated here only to measure the change; -> [(finding or None, rule)]."""
    from . import triage, xliff
    R = []
    for f, r in zip(v.get("findings", []), triage.triage(v)):
        if f["gid"] == "corr": continue
        d = f.get("detail") or ""; ops = triage.PAIR.findall(d)
        dl = not r and f["gid"] == "g3" and d.startswith("G3c") and ops and all(len(re.findall(r"\w+", u)) >= 3 for u, _ in ops)
        R.append(((bool(r) or bool(dl) or f["gid"] == "record"), xliff.RANK.get(f["gid"], 8), f, r))
    if any(who == "model" for _, _, _, who, _ in v.get("numbers", [])): R.append((False, 1.5, None, None))
    return [(f, r) for _, _, f, r in sorted(R, key=lambda x: (x[0], x[1]))[:3]]


def _labels(run):
    from .. import termbase
    return termbase._labels_70b() if run == "70b" else termbase._labels_8b(run.split("_", 1)[1])


def measure_v2():
    """eval/results/explain_v2.json: the per-draft explanation before (v1, restated in _v1_top) and after this change, on
    the fresh-166 drafts of the 70B and both 8B builds. Per run and per language: reasons shown per flagged draft, the
    share of the shown reasons that are counts (numbers / negation / modal verbs; tallies) and of those a triage rule calls
    probably fine, the low-priority notes (deletion mirroring the German's, typography), the termbase notes on ready drafts
    (v1 kinds: introduced variant, new gap; v2 adds 'kept'; how many of those drafts the labels call 'no fix needed'; for
    'kept', how often BAG's own published text of the amendment has the house rendering: evaluation data, never shown),
    and how many ready drafts the blind labels call 'minor' (needs a small fix) get any named reason or note. Display
    only: verdicts come from the frozen guards, unchanged."""
    import os
    from .. import core, score, termbase
    from . import load, load_records, xliff
    out = dict(note="explain v2 (presentation only): verdicts, drafts and scores unchanged; 'before' = the page before "
                    "this change (top three of every finding by (low, rank)); 'after' = xliff.reasons / xliff.explanation. "
                    "tally = a count finding (numbers, negation, modal verbs); probably fine = a triage rule applies.",
               runs={})
    I = {x["key"]: x for x in score.load_items("items/items_fresh.json")}
    for run, rel in termbase.RUNS:
        views = run_views(run)
        lab = _labels(run); row = {}
        for L in ("all", "fr", "it"):
            V = [v for v in views if L == "all" or v["lang"] == L]
            b = dict(drafts=len(V), flagged=0, shown=0, tally=0, tally_fine=0, ready_tb=0, ready_tb_notes=0, ready_tb_no_fix=0)
            a = dict(b, mirrored_note=0, typography_note=0, summary_only=0, kept_tb=0, kept_tb_bag_house=0)
            minor = dict(ready_minor=0, named_before=0, named_after=0, unnamed_after=[])
            for v in V:
                fl = v["status"] == "flagged"
                tb1 = [x for x in v.get("termbase") or [] if x["kind"] != "kept"]
                if fl:
                    b["flagged"] += 1; a["flagged"] += 1
                    T1 = _v1_top(v); b["shown"] += len(T1)
                    b["tally"] += sum(1 for f, _ in T1 if f and xliff.tally(f)); b["tally_fine"] += sum(1 for f, r in T1 if f and r and xliff.tally(f))
                    R = xliff.reasons(v, old=False); T2 = xliff.top(R); a["shown"] += len(T2)
                    a["tally"] += sum(1 for x in T2 if x.get("tally")); a["tally_fine"] += sum(1 for x in T2 if x.get("tally") and x["rule"])
                    a["summary_only"] += any(x["kind"] == "summary" for x in T2)
                    a["mirrored_note"] += any(x["kind"] == "finding" and x["tier"] == "note" for x in R)
                    a["typography_note"] += any(x["kind"] == "typography" for x in R)
                elif v["status"] == "ready":
                    R = xliff.reasons(v, old=False)
                    a["typography_note"] += any(x["kind"] == "typography" for x in R)
                    b["ready_tb"] += bool(tb1); b["ready_tb_notes"] += len(tb1)
                    a["ready_tb"] += bool(v.get("termbase")); a["ready_tb_notes"] += len(v.get("termbase") or [])
                    a["kept_tb"] += sum(1 for x in v.get("termbase") or [] if x["kind"] == "kept")
                    k = v["key"]; x = I[k]
                    lb = lab.get(k) or (dict(fix="no", cls="exact") if core.lock.norm(v["draft"]) == core.lock.norm(x["tgt_new"]) else None)
                    nofix = bool(lb and lb["fix"] == "no")
                    b["ready_tb_no_fix"] += bool(tb1) and nofix; a["ready_tb_no_fix"] += bool(v.get("termbase")) and nofix
                    for t in v.get("termbase") or []:          # BAG's published text of the amendment has the house rendering
                        if t["kind"] == "kept":
                            e = next(e for (l2, h), e in termbase.load().items() if l2 == v["lang"] and h.split(" / ")[-1] == t["term"])
                            a["kept_tb_bag_house"] += bool(termbase._loose(e.get("preferred_tokens") or " ".join(termbase.toks(e["preferred"])))
                                                           .search(termbase._nrm(x["tgt_new"])))
                    if lb and lb["fix"] == "yes" and lb["cls"] == "minor":
                        E = xliff.explanation(v); minor["ready_minor"] += 1
                        minor["named_before"] += bool(tb1)
                        named = bool(E["top"] or E["note"]); minor["named_after"] += named
                        if not named: minor["unnamed_after"].append(k)
            for d in (b, a):
                d["reasons_per_flagged"] = round(d["shown"] / d["flagged"], 3) if d["flagged"] else 0.0
                d["tally_share"] = round(d["tally"] / d["shown"], 3) if d["shown"] else 0.0
            row[L] = dict(before=b, after=a, minor=minor)
        out["runs"][run] = row
    return out


_RV = {}


def run_views(run):
    """The per-item views (emit.load / load_records, current wording) of a fresh-166 run of termbase.RUNS ('70b',
    '8b_q4_k_m', '8b_q8_0') or of a shadow-month build ('shadow:q4_k_m' …), memoised for the measurements."""
    import os
    from .. import score, termbase, house
    from . import load, load_records
    if run not in _RV:
        if run.startswith("shadow:"):
            D = os.path.join(score.DATA, house.SHADOW[0])
            _RV[run] = load_records(os.path.join(D, run.split(":", 1)[1], "records.jsonl"), os.path.join(D, "items.json"))[1]
        elif run == "70b": _RV[run] = load("fresh166")[1]
        else:
            rel = dict(termbase.RUNS)[run]
            _RV[run] = load_records(os.path.join(score.DATA, rel), os.path.join(score.DATA, "items/items_fresh.json"))[1]
    return _RV[run]


# ------------------------------------------------------------------------------------------- measurement (explain v3)
RESULT_V3 = ("eval", "results", "explain_v3.json")
CODE = re.compile(r"\b(?:r[èe]gle|regola) T\d|\bT[1-8]\b|\bG\d[a-z]?\b|\b(?:Lock|Slots):|\[T\d\]")


def measure_v3():
    """eval/results/explain_v3.json: the translator-facing changes after the BAG French translator's third review, per run
    (the fresh-166 drafts of the 70B and both 8B builds; the shadow month 01.09 -> 01.10.2026 of Q4_K_M, Q8_0 and the 70B),
    before (the round-7 wording) and after. Display only: verdicts, drafts and scores unchanged.
      house: the house-sentence advisory (gleichlaut.house): drafts and notes, and per note BAG's published sentence of the
        same amendment at that German sentence (evaluation data, never shown): differs from the draft's, is the house
        wording, is the draft's wording, unknown.
      termbase: advisories by kind; 'rewrote' = a non-standard wording in a sentence the draft inserted or rewrote, now a
        normal note (before: the softer 'kept' note, or no note for a recorded variant such as 'assurance-maladie');
        'left_to_house' = termbase items left out because the house-sentence note names the same sentence.
      noise: German-left / copied findings whose words are all target words too (lexicon or old text: before a reason to
        check, after probably fine) or partly; repetitions the German has too (before a reason, after low); deletions that
        mirror the German's, one to one (now a statement) or partly (still a question); flagged drafts whose header count
        (before: triage rules over the guard findings) differed from the reasons list (after: xliff.counts, equal by
        construction).
      hedged: change-not-applied sentence findings: before all hedged ('vérifier qu'elle est traduite'); after missing /
        left in German / kept (a removed sentence the draft carries over) / still hedged.
      codes: units whose translator-facing XLIFF notes carried internal codes (before: every unit with a finding, through
        the checks note's raw output; after: none outside the gleichlaut:debug note)."""
    import os
    from .. import core, score, house, termbase
    from . import triage, xliff
    I = {x["key"]: x for x in score.load_items("items/items_fresh.json")}
    D = os.path.join(score.DATA, house.SHADOW[0])
    import json
    IS = {x["key"]: x for x in json.load(open(os.path.join(D, "items.json"), encoding="utf-8"))}
    out = dict(note="explain v3 (presentation only; BAG French translator's third review): verdicts, drafts and scores "
                    "unchanged. 'before' = the round-7 wording, 'after' = this change. BAG's published text is evaluation "
                    "data, never shown.",
               house_sentences=dict(file=os.path.relpath(house.JSON, core.ROOT), house={L: sum(1 for (l, _) in house.load() if l == L) for L in house.LANGS}),
               runs={})
    names = [r for r, _ in termbase.RUNS] + ["shadow:" + m for m in house.SHADOW[1]]
    for run in names:
        V = run_views(run); items = IS if run.startswith("shadow:") else I
        row = dict(house=house.measure_views(V, items))
        tb = dict(notes=Counter(), rewrote_variant=0, rewrote_wording=0, left_to_house=0)
        nz = dict(lexicon_all_fine=0, lexicon_partly=0, g4_german_repeats=0, g4_other=0, deletion_whole=0, deletion_question=0,
                  header_mismatch_before=0, header_mismatch_after=0, flagged=0)
        hd = dict(add_before_hedged=0, add_missing=0, add_german=0, add_hedged=0, del_before_hedged=0, del_kept=0, del_hedged=0)
        cd = dict(units=0, before=0, after=0)
        for v in V:
            if v["status"] == "human": continue
            A = v.get("termbase") or []
            for a in A:
                tb["notes"][a["kind"]] += 1
                if a.get("rewrote"): tb["rewrote_variant" if a["kind"] == "variant" else "rewrote_wording"] += 1
            Hw = [h["wrote"].lower() for h in v.get("house") or []]
            tb["left_to_house"] += sum(1 for a in A if a.get("wrote") and any(a["wrote"].lower() in h for h in Hw))
            R = xliff.reasons(v, old=False); T = triage.triage(v)
            for f, r in zip(v.get("findings", []), T):
                if f["gid"] in ("g1", "g5") and v["status"] == "flagged" and not r:
                    fi, ot = lexicon_fine(v, f)
                    if fi and not ot: nz["lexicon_all_fine"] += 1
                    elif fi: nz["lexicon_partly"] += 1
                if f["gid"] == "g4" and v["status"] == "flagged":
                    nz["g4_german_repeats" if german_repeats(v, v["draft"], f["detail"]) else "g4_other"] += 1
                if f["gid"] == "g2":
                    m = re.match(r"G2 \((\w+)\): (.*)$", f["detail"] or "")
                    if not m: continue
                    u, w, sa, sb = _de_spans(v["de_old"], v["de_new"]).get(m.group(2), ("", "", None, None))
                    t0 = g2_text(v["lang"], m.group(1), v, u, w, sa, sb)
                    t1 = f["text"]
                    for k, b, keys in (("add", "g2_add_s", (("g2_add_miss", "add_missing"), ("g2_add_de", "add_german"))),
                                       ("del", "g2_del_s", (("g2_del_kept", "del_kept"),))):
                        if _is(t0, v["lang"], b):
                            hd[f"{k}_before_hedged"] += 1
                            hit = next((n for kk, n in keys if _is(t1, v["lang"], kk)), None)
                            hd[hit or f"{k}_hedged"] += 1
            for x in R:
                if x["kind"] == "finding" and x["tier"] == "note": nz["deletion_whole" if x.get("whole") else "deletion_question"] += 1
            if v["status"] == "flagged":
                nz["flagged"] += 1
                g = [r for f, r in zip(v.get("findings", []), T) if f["gid"] != "corr"]
                c = xliff.counts(R)
                nz["header_mismatch_before"] += [sum(1 for r in g if not r), sum(1 for r in g if r)] != c
                nz["header_mismatch_after"] += xliff.explanation(v)["counts"] != c
            cd["units"] += 1
            cd["before"] += any(f.get("detail") for f in v.get("findings", []))
            cd["after"] += any(CODE.search(t) for nid, _, _, _, t in xliff.unit_notes(v, prev=False) if nid != "debug")
        tb["notes"] = dict(sorted(tb["notes"].items()))
        row.update(termbase=tb, noise=nz, hedged=hd, codes=cd)
        out["runs"][run] = row
    return out


def _is(text, lang, k):
    """True when text is an instance of the wording T[k] (its fixed part before the first placeholder and after the last)."""
    t = T[k][rl(lang)]; head = t.split("{", 1)[0]; tail = t.rsplit("}", 1)[-1]
    if rl(lang) == "fr": head, tail = _fr(head + "x")[:-1], _fr("x" + tail)[1:]
    return text.startswith(head) and text.endswith(tail)


def write_v3(path=None):
    """Write measure_v3() to eval/results/explain_v3.json -> path."""
    import json, os
    from .. import core
    path = path or os.path.join(core.ROOT, *RESULT_V3)
    with open(path, "w", encoding="utf-8") as fh: json.dump(measure_v3(), fh, ensure_ascii=False, indent=1, sort_keys=True)
    return path


def write_v2(path=None):
    """Write measure_v2() to eval/results/explain_v2.json (the layout replay.write uses) -> path."""
    import json, os
    from .. import core
    path = path or os.path.join(core.ROOT, *RESULT_V2)
    with open(path, "w", encoding="utf-8") as fh: json.dump(measure_v2(), fh, ensure_ascii=False, indent=1, sort_keys=True)
    return path
