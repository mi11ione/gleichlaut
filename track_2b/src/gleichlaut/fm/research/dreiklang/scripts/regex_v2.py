"""Dreiklang S2: typed-regex v2 (no model). Types each shared candidate as (subject, operator) or None.
Same candidates (cands.py, frozen) and same comparison (compare.py) as S1; only the typer differs.
Built only against dev gold (scripts/dev_regex.py prints dev errors); frozen (sha256 in results) before held-out scoring.
Census noise classes handled here: unit conversions (compare.py normalises to days), number words / articles
(kind 'one' is a condition only with a strong operator, "einmal/une fois/una volta", or a time unit), operator
phrasings (census lexicons + look-back windows, 'oder mehr', 'bis unter', 'spätestens'), "insuffisance" is never
used (no negation counting at all), names/codes/scales/presentations -> not a condition.
"""
import re, os, sys
sys.path.insert(0, os.path.expanduser("~/Desktop/hackapertus/spikes/gleichlaut/scripts"))
import census as C  # noqa: E402

OPMAP = {"GE": ">=", "GT": ">", "LE": "<=", "LT": "<"}

AGE_CTX = r"(?:alter|lebensjahr|jährig|jahre?n?\b|ans?\b|âgé|anni\b|età|kinder|jugendlich|erwachsen|enfants?|adolescent|adultes?|bambini|adolescenti|adulti|patient)"
TIME_PRE = r"(?:nach|après|au-delà d[e']|dopo|während|pendant|per|durante|weiterbehandlung|poursuite|prosecuzione|innerhalb|seit|depuis|da almeno)\s*(?:\S+\s+){0,2}$"
INT_PRE = r"(?:alle|toutes les|tous les|ogni|jede[nrs]?|chaque)\s+$"
PRICE_CTX = r"(?:zuschlag|prime|supplement|preis|prix|prezzo|rückerstatt|rembours|rimbors|fabrikabgabe|fabrique|fabbrica|\bfr\.|chf)"
MEAS_PRE = r"(?:IGA|SCORAD|EASI|FeNO|ECOG|GINA(?:-Stufe)?|TPS|PASI|DAS28|BASDAI|HbA1c|LVEF|FEVG|eGFR|Grad|grade|grado|Stadium|stade|stadio|Status|Score|score|punteggio|palier|Stufe|T2a)\s*(?:égal à\s*|von\s*|de\s*|di\s*)?[≥≤<>]?\s*$"
NAME_PRE = r"(?:(?<![A-Za-zÀ-ÿ])(?:Typ|type|tipo|PD-|CTLA-|CD|Exon|exon|esone|RS|SR|Anhang|annexe|allegato|Ziffer|chiffre|cifra|Art\.|art\.|Rezeptor-|récepteur|KN|Code|code|codice|Indikationscode)|\(del|\bt|;)\s*[-(;]?\s*$"
PRESENT = r"(?:packung|durchstechflasche|fertigspritze|fertigpen|einzelpackung|flacon|emballage|seringue|stylo|confezione|flaconcino|siringa|penna|dosierungen|dosages|dosaggi|stk|pièces?|pezz[oi]|boîte|kps|kaps|tabl)"


def _norm_space(x):
    return re.sub(r"\s+", " ", x)


def type_cand(s, c, lang):
    a, b, v, u, kind = c["a"], c["b"], c["v"], c["u"], c["kind"]
    pre = s[max(0, a - 80):a]
    post = s[b:b + 80]
    low_pre, low_post = pre.lower(), post.lower()
    surf = s[a:b]
    # ---------------------------------------------------------------- not a condition
    if re.fullmatch(r"\d{5}\.\d{2}", surf) or (isinstance(v, (int, float)) and v >= 10000 and "." in surf):
        return None  # indication codes
    if re.search(r"(?:code|codice|indikationscode)[^.]{0,60}$", low_pre) and v >= 1000:
        return None
    if re.search(NAME_PRE, pre[-25:]) and not re.search(r"(?:IGA|EASI|SCORAD|ECOG|GINA)\s*$", pre[-12:]):
        return None
    if re.match(r"\s*[-–]?\s*(?:mercapto|MP\b|q\d|\)?\s*\^)", post) or re.match(r"[-–](?:[A-Za-z])", post):
        return None  # 6-Mercaptopurin, 1q21, 10^9
    if re.match(r"\s*\^", post) or re.search(r"x\s*$", pre[-3:]) and re.match(r"\^", post):
        return None
    if re.search(r"\(\s*(?:EASI|SCORAD|PASI|ACR|DAS)\s*$", pre[-10:]) and re.match(r"\s*\)", post):
        return None  # endpoint names "(EASI 50)"
    if re.search(r"(?:skala|échelle|scala)[^.;:]{0,15}$", low_pre[-30:]) and re.match(r"\s*(?:[-–à]|a\b|\))", low_post) is not None:
        return None  # scale bounds "Skala von 0-4"
    if re.search(r"(?:skala|échelle|scala)[^.;:]{0,25}\d\s*(?:[-–]|à|a)\s*$", low_pre[-40:]):
        return None
    if re.search(r"(?:ausgabe|édition|edizione)", low_post[:14]):
        return None
    if u == "ml" or re.match(r"\s*mg\s*/\s*\d", post) or re.search(r"mg\s*/\s*$", pre[-6:]):
        return None  # volumes and concentrations "200mg/20 ml"
    if re.match(r"\s*(?:x|×)\s*\d+\s*ml", post) or re.search(r"(?:x|×)\s*$", pre[-3:]) and u == "ml":
        return None  # pack formats "12 x 500 ml"
    if re.match(r"\s*(?:stk|pièces|pezz[oi]|flacon\b)", low_post):
        return None
    if u in ("mg", "ug", "g") and (re.search(PRESENT + r"[^.;:]{0,30}$", low_pre[-45:]) or
                                   re.search(r"\b[A-Z]{4,}\s*$", pre[-14:]) or re.search(r"(?:\boder|\bou|\bo)\s*$", low_pre[-6:]) and
                                   re.search(PRESENT, low_pre[-60:])):
        return None  # presentation strengths
    if kind == "one":
        if re.search(r"^(?:einmal|une fois|una volta)", (surf + post).lower()) or re.match(r"\s*(?:fois|volta|mal)\b", low_post):
            pass
        elif u in ("year", "month", "week", "day"):
            pass
        else:
            if not re.search(r"(?:mindestens|maximal|höchstens|wenigstens|au moins|au maximum|au plus|almeno|al massimo|non più di|pas plus de|plus d['e]|moins d['e]|mehr als|weniger als|più di|meno di)\s*$", low_pre[-20:]):
                return None
    # ---------------------------------------------------------------- local unit re-detection (code unit missing)
    if u is None:
        mu = re.match(r"\s*(?:\.|ème|e|er|°|ª|a)?\s*(?:\S+\s+)?(zyklus|cycle|ciclo)\b", low_post) or \
            re.match(r"\s*(?:\.|ème|e|er|°|ª|a)?\s*(?:\S+\s+)?(mois|semaines?|jours?|ans|années?|monate\w*|wochen|tage\w*|mesi|settiman[ae]|giorni|anni)\b", low_post)
        if mu:
            w = mu.group(1)
            u = ("cycle" if w in ("zyklus", "cycle", "ciclo") else "month" if w.startswith(("mois", "monat", "mes")) else
                 "week" if w.startswith(("sem", "woch", "settim")) else "day" if w.startswith(("jour", "tag", "giorn")) else "year")
    # ---------------------------------------------------------------- subject
    subj = None
    if re.match(r"\s*L\b", post) or re.match(r"L\b", post):
        return ("cnt", "=")  # "2L NSCLC" line of therapy
    if u == "line" or re.search(r"(?:linie|ligne|linea|linee)", (surf + post[:12]).lower()):
        subj = "cnt"
    elif u == "kg":
        subj = "wt"
    elif u in ("mg", "ug", "g", "mg/kg", "mg/m2", "IU"):
        subj = "dose"
    elif u == "pct":
        subj = "price" if re.search(PRICE_CTX, low_pre[-60:]) else "meas"
    elif u == "year":
        subj = "time" if (re.search(TIME_PRE, low_pre[-40:]) or
                          (kind == "one" and not re.search(r"(?:\bab|dès|à partir d[eu']|a partire da\w*|\bdai?)\s*$", low_pre[-14:]))) else "age"
    elif u in ("month", "week", "day", "hour"):
        subj = "int" if (re.search(INT_PRE, low_pre[-14:]) or
                         re.search(r"(?:dosierungsintervall\w*|dosisintervall\w*|intervalle de dosage|intervallo di dosaggio)\s+(?:\S+\s+){0,1}$", low_pre[-45:])) else "time"
    elif u in ("cycle", "dose", "inj", "tab", "pack"):
        subj = "cnt"
    elif u == "times":
        subj = "meas" if re.search(r"(?:grenzwert|normwert|limite|valeur|uln|oberen)", low_post[:50]) else "cnt"
    elif u in ("point", "mmol/l", "g/l", "mg/dl", "g/dl", "cells", "mmHg", "umol", "mmol", "kg/m2"):
        subj = "meas"
    else:
        if re.search(MEAS_PRE, pre[-25:]) or re.match(r"\s*(?:cm|ppb|zellen|cellule|cellules|G/L|%)", post, re.I):
            subj = "meas"
        elif re.search(r"\bfr\.\s*$", low_pre[-6:]):
            subj = "price"
        elif re.search(r"(?:exazerbation|exacerbation|esacerbazion|therapie|traitement|terapi|vortherap|zigarett|cigarett|sigarett|anzeichen|signes|segni|regim|schém|schem|chimio)", low_post[:40]) \
                or re.search(r"(?:\bein(?:es|er|em)?\b|l'un|uno)\s+der", low_post[:10]):
            subj = "cnt"
        elif re.search(r"(?:zyklen|cycles|cicli)", low_pre[-40:] + low_post[:20]):
            subj = "cnt"
        else:
            return None
    # ---------------------------------------------------------------- operator
    op = None
    tail_pre = pre[-40:]
    msym = re.search(r"([≥≤<>])\s*=?\s*$", tail_pre)
    if msym:
        op = {"≥": ">=", "≤": "<=", ">": ">", "<": "<"}[msym.group(1)]
        if re.search(r"(?:-|–)\s*<\s*$", tail_pre) or re.search(r"bis\s*<\s*$", tail_pre):
            op = "<"
    if op is None and re.search(MEAS_PRE, pre[-25:]):
        op = "="  # "GINA 4", "IGA 4": an acronym right before the number takes no distant operator
    if op is None and re.match(r"\s*(?:kg|mg|jahre?n?|ans|anni)?\s*(?:-|–|bis|à|a)\s*(?:<|moins de|meno di|unter)\s*\d", low_post):
        op = ">="  # lower bound of "15 - < 60 kg", "30 kg à moins de 60", "da 30 kg a meno di 60"
    if op is None and subj == "time" and re.search(r"(?:beginnend|a partire da|à partir de)\s*$", low_pre[-20:]) \
            and re.match(r"\s*\S+\s+(?:nach|après|dopo)\b", low_post):
        op = "="  # offsets: "beginnend vier Wochen nach Tag 15", "a partire da quattro settimane dopo"
    if op is None and re.search(r"(?:nombre maximal|numero massimo|maximale anzahl|maximal vergütete anzahl|höchstzahl)[^.;]{0,50}$", low_pre[-70:]):
        op = "<="
    if op is None and re.search(r"(?:a partire dall?'?(?:età di)?|a partire da(?:i|l|lla)?)\s*$", low_pre[-30:]):
        op = ">="
    if op is None:
        lo = low_pre[-60:]
        if re.search(r"(?:spätestens|au plus tard|al più tardi)\s+(?:nach|après|dopo)\s*(?:la\s+)?(?:woche\s+|semaine\s+|settimana\s+)?$", lo):
            op = "<="
        elif re.search(r"(?:bis unter|à moins de|a meno di)\s*$", lo):
            op = "<"
        elif re.search(r"(?:bis zur woche|bis woche|jusqu'à la semaine|fino alla settimana|entro la)\s*$", lo):
            op = "<="
        elif subj == "time" and re.search(r"(?:innerhalb (?:der letzten|von)|in den (?:letzten|vorausgegangenen|vergangenen)|während der (?:letzten|vergangenen)|au cours des|dans les|nei|negli ultimi|entro|durante)\s*$", lo):
            op = "<="
        elif re.search(r"(?:seit mindestens|depuis au moins|da almeno)\s*$", lo):
            op = ">="
    if op is None:
        o, _txt, _ex = C.classify_op(s, a, b, lang)
        if o:
            op = OPMAP[o]
        if lang == "de" and re.search(r"über\s*$", low_pre[-6:]) and subj in ("time", "int"):
            op = None
    if op is None and re.match(r"\s*(?:\S+\s+)?(?:oder mehr|ou plus|o più|o superiore)", low_post):
        op = ">="
    if op is None:
        op = "="
    # durations "nach N Wochen" / "après" stay "=", look-back windows "<=" (handled above)
    return (subj, op)
