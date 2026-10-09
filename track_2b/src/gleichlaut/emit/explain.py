"""Plain-language guard findings for the reviewer: one short sentence per finding, in the language of the draft (French
for French drafts, Italian for Italian drafts, English otherwise), with the raw technical finding kept alongside.

Rendering only. The verdict (ready / flagged) and every finding come from the frozen guard stack (core.Pipeline.check);
this module rephrases them and never adds, drops or reweighs a finding. Two additions are labelled as such:
  - "corrects": the draft also changes a number the German does not touch, and the change brings the target closer to
    the German (e.g. Nemluvio IT 'ogni quattro settimane' -> 'ogni otto' where the German says 'alle acht Wochen').
    Findings caused by that change are annotated, not suppressed: the flag stands and a translator decides.
  - "divergence": numbers on which the old target already disagrees with the old German, from
    gleichlaut.audit.audit_item when that module is importable (skipped silently otherwise)."""
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
REVIEW_OTHER = {"fr": "Marqué pour révision par le pipeline\u00a0: {r}", "it": "Segnalato per revisione dalla pipeline: {r}",
                "en": "Marked for review by the pipeline: {r}"}


def review_text(reason, lang):
    """A record's own reason for review (air-gapped, statute lane, ...) as one sentence in the reviewer's language."""
    for k, T_ in REVIEW:
        if (reason or "").startswith(k): return T_[rl(lang)]
    return REVIEW_OTHER[rl(lang)].format(r=reason or "status flagged")


def record_finding(reason, lang):
    return dict(gid="record", name=GID["record"], gname=NAMES["record"][rl(lang)], text=review_text(reason, lang),
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
    "unknown": {"fr": "Le brouillon contient {n} code(s) de nombre inconnu(s) : vérifier les nombres.",
                "it": "La bozza contiene {n} codice/i numerico/i sconosciuto/i: verificare i numeri.",
                "en": "The draft contains {n} unknown number code(s): check the numbers."},
    "g1": {"fr": "Mots allemands restés dans le texte : {x}", "it": "Parole tedesche rimaste nel testo: {x}",
           "en": "German words left in the text: {x}"},
    "g5": {"fr": "Mots repris de l'allemand sans traduction : {x}", "it": "Parole riprese dal tedesco senza traduzione: {x}",
           "en": "Words copied from the German untranslated: {x}"},
    "g6": {"fr": "Terminologie : {a} s'écrit {b} en français", "it": "Terminologia: {a} in italiano si scrive {b}",
           "en": "Terminology: {a} is written {b} in the target language"},
    "g7": {"fr": "Mot jamais vu dans les limitations françaises (coquille ?) : {x}",
           "it": "Parola mai vista nelle limitazioni italiane (refuso?): {x}",
           "en": "Word never seen in target-language limitations (typo?): {x}"},
    "g2_rep": {"fr": "Le changement allemand {u} → {v} ne semble pas appliqué.",
               "it": "Il cambiamento tedesco {u} → {v} non sembra applicato.",
               "en": "The German change {u} → {v} does not seem to be applied."},
    "g2_add": {"fr": "L'ajout allemand {v} ne semble pas repris.", "it": "L'aggiunta tedesca {v} non sembra ripresa.",
               "en": "The German addition {v} does not seem to be carried over."},
    "g2_del": {"fr": "La suppression allemande de {u} ne semble pas reprise.",
               "it": "La soppressione tedesca di {u} non sembra ripresa.",
               "en": "The German removal of {u} does not seem to be carried over."},
    "g3c": {"fr": "Le brouillon supprime davantage que l'allemand : {x}", "it": "La bozza toglie più del tedesco: {x}",
            "en": "The draft removes more than the German does: {x}"},
    "g3a": {"fr": "Mots de l'ancien texte disparus hors de la partie modifiée : {x}",
            "it": "Parole del vecchio testo scomparse fuori dalla parte modificata: {x}",
            "en": "Words of the old text lost outside the changed part: {x}"},
    "g4": {"fr": "Passage répété (une seule fois dans l'ancien texte) : {x}",
           "it": "Passo ripetuto (una sola volta nel vecchio testo): {x}",
           "en": "Passage repeated (once only in the old text): {x}"},
    "more": {"fr": "et {n} autre(s)", "it": "e altri {n}", "en": "and {n} more"},
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
}
MODAL = {"MUST": {"fr": "obligation : doit", "it": "obbligo: deve", "en": "obligation: must"},
         "MAY": {"fr": "possibilité : peut", "it": "possibilità: può", "en": "permission: may"},
         "SHALL": {"fr": "recommandation : devrait", "it": "raccomandazione: dovrebbe", "en": "recommendation: should"}}


def rl(lang): return lang if lang in ("fr", "it") else "en"
def _fr(s): return re.sub(r" ([;:!?»])", "\u00a0\\1", s).replace("« ", "«\u00a0") if s else s
def tr(lang, k, **kw):
    s = T[k][rl(lang)].format(**kw)
    return _fr(s) if rl(lang) == "fr" else s
def q(lang, s): a, b = QUOTE[rl(lang)]; return f"{a}{s}{b}"


def clip(s, n=110):
    s = re.sub(r"\s+", " ", s).strip()
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


def _de_ops(de_old, de_new):
    """-> {guard de_txt: (old original substring, new original substring)} for every German op."""
    a, b, ops = lock.de_ops(de_old, de_new)
    sa, sb = lock.tok_spans(de_old), lock.tok_spans(de_new)
    res = {}
    for _, i1, i2, j1, j2 in ops:
        key = f"«{' '.join(a[i1:i2])}» -> «{' '.join(b[j1:j2])}»"
        u = de_old[sa[i1][1]:sa[i2 - 1][2]] if i2 > i1 else ""
        v = de_new[sb[j1][1]:sb[j2 - 1][2]] if j2 > j1 else ""
        res[key] = (u, v)
    return res


def _delta(lang, d, fem=False):
    return tr(lang, "add_n", n=d) if d > 0 else tr(lang, "rem_n", n=-d) if d < 0 else tr(lang, "none_f" if fem else "none_n")


def _numch(lang, add, rem):
    p = []
    if add: p.append(tr(lang, "n_add", x=", ".join(sorted(add))))
    if rem: p.append(tr(lang, "n_rem", x=", ".join(sorted(rem))))
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


def divergence(x):
    """-> [dict(text=..., raw=...)] from gleichlaut.audit.audit_item(x), [] when absent or empty. Accepts a list (or a
    dict with a list under divergences / findings / items) of dicts, (de, tgt) pairs or strings."""
    if _audit_item is None: return []
    try: r = _audit_item(x)
    except Exception: return []
    if isinstance(r, dict):
        r = next((r[k] for k in ("divergences", "findings", "items", "numbers") if isinstance(r.get(k), list)), [r] if r else [])
    if not r: return []
    L, res = x["lang"], []
    for d in r if isinstance(r, (list, tuple)) else [r]:
        raw = d if isinstance(d, str) else repr(d)
        if isinstance(d, dict) and "side" in d and ("context" in d or "value" in d):
            ctxs = d.get("context") or []
            c = ctxs[0] if isinstance(ctxs, list) and ctxs else ctxs if isinstance(ctxs, str) else ""
            m = re.search(r"(\S*\s+)?\[([^\]]+)\](\S*(?:\s+[^\s.,;:)]+)?)?", c)
            phrase = strip_punct(m.group(0).replace("[", "").replace("]", "")) if m else str(d.get("value", ""))
            if d.get("unit") and m and d["unit"] not in phrase: phrase += " " + d["unit"]
            txt = tr(L, "div_de" if d["side"] == "de" else "div_tg", c=q(L, clip(phrase, 60)))
        elif isinstance(d, dict):
            de = next((d[k] for k in _DEK if d.get(k) not in (None, "")), None)
            tg = next((d[k] for k in _TGK if d.get(k) not in (None, "")), None)
            if de is not None and tg is not None:
                fmt = lambda v: ", ".join(map(str, v)) if isinstance(v, (list, tuple, set)) else str(v)
                txt = tr(L, "div_pair", d=q(L, clip(fmt(de), 80)), t=q(L, clip(fmt(tg), 80)))
            else:
                txt = next((str(d[k]) for k in _TXK if d.get(k)), raw)
        elif isinstance(d, (list, tuple)) and len(d) >= 2:
            txt = tr(L, "div_pair", d=q(L, str(d[0])), t=q(L, str(d[1])))
        else:
            txt = str(d)
        res.append(dict(text=clip(txt, 220), raw=raw))
    return res


def banner(x, divs, out=None):
    """The banner sentence for a pre-existing divergence (None when there is none). When the draft changes the diverging
    passage, the old target's phrase is set against the German one ('ogni quattro settimane' vs 'alle acht Wochen')."""
    if not divs: return None
    L = x["lang"]; c = corrections(x, out) if out else None
    if c and c["where"] and c["de"]:
        return tr(L, "div", x=tr(L, "div_vs", t=q(L, c["where"][0][0]), d=q(L, c["de"][0])))
    return tr(L, "div", x="; ".join(d["text"] for d in divs[:3]))


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
    ops = _de_ops(x["de_old"], x["de_new"]) if g["g2"] or g["g3"] else {}
    for kind, de in g["g2"]:
        u, v = ops.get(de, ("", ""))
        U, V = clip(strip_punct(u), 90), clip(strip_punct(v), 90)
        if not U and not V: U, V = u or "∅", v or "∅"
        txt = (tr(L, "g2_rep", u=q(L, U), v=q(L, V)) if U and V else tr(L, "g2_add", v=q(L, V)) if V else tr(L, "g2_del", u=q(L, U)))
        add("g2", txt, f"G2 ({kind}): {de}")

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
