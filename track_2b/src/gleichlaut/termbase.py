"""Termbase: BAG's own French and Italian renderings of recurring German limitation terms, mined from the register.
Deterministic, stdlib, no model calls, no network.

Input: one SL snapshot (sl.ingest output; the 1,688 limitations of the 6 Oct 2026 feed, aligned DE/FR/IT by id as
audit.load aligns them). Output: data/termbase/termbase_<date>.json and a TBX-Basic file (TBX v3, ISO 30042:2019, DCA
style) for terminology tools (gleichlaut_sl_termbase_<date>.tbx). Rules, fixed before the first mining run (docs/termbase.md):

  H  head terms: the curated German terms in HEADS (picked from the German content words in >= 20 distinct German texts:
     reimbursement, approval, pricing, prescriber and line-of-therapy vocabulary; no drug, company, disease or anatomy
     names, no general words). Each is a regex over the German text (inflected forms included).
  M1 per target language, a limitation counts when it has a German text and a target text written in that language
     (audit's function-word vote, as audit.build_stats). Target tokens: lower-cased words, hyphen compounds kept whole
     ('assureur-maladie' is one token, 'assureur maladie' two), elided articles split off ("l'", "dell'").
  M2 candidates: target n-grams of 1..6 tokens that neither start nor end with a function word, in >= MIN_SUPPORT
     limitations whose German contains the term.
  M3 association: occurrence-level Dice between the term (count in the German) and the n-gram (count in the target),
     2 * sum_d min(cD, cG) / (sum cD + sum cG) over all limitations.
  M4 exclusive evidence: when another German word (outside the term's own matches) is more strongly associated with the
     n-gram than the term, the n-gram is kept only if it is in >= 50% of the limitations that have the term but not that
     word, and more often there than in the limitations that have the word but not the term (>= 3 such limitations).
     This drops co-occurring boilerplate ('consultation' goes with 'Konsultation', not with 'Vertrauensarzt').
  M5 head: the candidate with the highest association. Preferred rendering: the longest candidate that contains the head
     and keeps >= EXTEND of the head's occurrences (and passes M4), so 'prise en charge' becomes 'garantie de prise en
     charge' when most of its occurrences are that phrase.
  M6 dominance: the preferred rendering is recorded as the house rendering when it is in >= MIN_SUPPORT limitations and
     in >= MIN_SHARE of the limitations whose German contains the term; otherwise the entry says 'no dominant rendering'.
  M7 variants: in the limitations with the term but without the preferred rendering, the n-grams (not overlapping the
     preferred one, no word of the German text, >= 2 limitations, >= VAR_LIFT times more frequent there than in the
     limitations without the term, passing M4), picked greedily by how many of those limitations they cover (and extended
     as in M5); at most MAX_VARIANTS. Counts are limitations.

Advisory (presentation only; emit/xliff.py and the review page): for a draft whose new German contains a term with a
house rendering, a low-priority note in the reviewer's language when the draft introduces a recorded minority variant
(more occurrences than the old target text; variants matched spelling-tolerantly, so 'assurance-maladie' is the recorded
'assurance maladie'), or writes the house rendering fewer times than the German has the term while the old text did not
fall short in the same way (the gap is the draft's, not the old text's; the note says how often the draft writes it when
it does, never 'absent'), or writes a recorded variant or another non-standard wording in a sentence it inserted or
rewrote (not one of the old text's sentences: the wording is the draft's own). Softer ("kept"): the draft falls short, the
old text already did, and the draft carries over unchanged a sentence with a non-standard wording the old text used (a
spelling variant such as 'assureur maladie', or a similar wording such as 'caisse maladie'; never one of BAG's own
recorded variants, which are BAG's practice): 'le texte (déjà avant) écrit …'. It never changes a verdict, a draft, or a
score; the first two kinds are measured in eval/results/termbase.json (measure()), all three in
eval/results/explain_v2.json and explain_v3.json (emit.explain). Data files mined from the same snapshot by `gleichlaut
termbase`: the house sentences (gleichlaut.house) and the words the German and target registers share (shared_words)."""
import argparse, difflib, hashlib, json, os, re, sys
from collections import Counter, defaultdict
from . import core

DATE = "20261006"
DEST = os.path.join(core.ROOT, "data", "termbase")
JSON = os.path.join(DEST, f"termbase_{DATE}.json")
TBX = os.path.join(DEST, f"gleichlaut_sl_termbase_{DATE}.tbx")
TBX_NS = "urn:iso:std:iso:30042:ed-2"
LANGS = ("fr", "it")
MIN_SUPPORT, MIN_SHARE, EXTEND, MAX_N, TOP_K = 10, 0.5, 0.6, 6, 25
EXCL_SHARE, EXCL_MIN, VAR_MIN, VAR_LIFT, MAX_VARIANTS = 0.5, 3, 2, 5.0, 5
EXT_LENIENT = True
VAR_DICE = 0.3

# H: (German term as shown, regex over the German text). Order = document frequency in the 6 Oct 2026 German texts.
HEADS = [
    ("Krankenversicherer", r"Krankenversicherer(?:s|n)?"),
    ("Kostengutsprache", r"Kostengutsprachen?"),
    ("Vertrauensarzt", r"Vertrauens(?:arzt(?:es)?|ärzt(?:e|en|in|innen)?)"),
    ("Indikationscode", r"Indikationscodes?"),
    ("Fachärztin / Facharzt", r"Fach(?:arzt(?:es)?|ärzt(?:e|en|in|innen)?)"),
    ("Mehrwertsteuer", r"Mehrwertsteuer"),
    ("Fabrikabgabepreis", r"Fabrikabgabepreis(?:es|e|en)?"),
    ("Monotherapie", r"Monotherapien?"),
    ("Rückerstattung", r"Rückerstattung(?:en)?"),
    ("Vergütung", r"Vergütung(?:en)?"),
    ("Verschreibung", r"Verschreibung(?:en)?"),
    ("Zulassungsinhaberin", r"Zulassungsinhaberin(?:nen)?"),
    ("Preismodell", r"Preismodell(?:e|s|en)?"),
    ("Verordnung", r"Verordnung(?:en)?"),
    ("Limitierung", r"Limitierung(?:en)?"),
    ("Universitätsklinik", r"Universitätsklinik(?:en)?"),
    ("Poliklinik", r"Poliklinik(?:en)?"),
    ("Therapiebeginn", r"Therapiebeginns?"),
    ("Antikörper", r"Antikörpern?"),
    ("Rückvergütung", r"Rückvergütung(?:en)?"),
    ("Stammzelltransplantation", r"Stammzelltransplantation(?:en)?"),
    ("Diagnosestellung", r"Diagnosestellung"),
    ("Körpergewicht", r"Körpergewichts?"),
    ("Originalpräparat", r"Originalpräparat(?:e|es|s|en)?"),
    ("Generikum", r"Generik(?:um|a|ums)"),
    ("Erstlinientherapie", r"Erstlinientherapien?"),
    ("Erhaltungstherapie", r"Erhaltungstherapien?"),
    ("Kombinationstherapie", r"Kombinationstherapien?"),
    ("Erstlinienbehandlung", r"Erstlinienbehandlung(?:en)?"),
    ("Unverträglichkeit", r"Unverträglichkeit(?:en)?"),
    ("Therapiedauer", r"Therapiedauer"),
    ("Behandlungsbeginn", r"Behandlungsbeginns?"),
    ("Indikationsstellung", r"Indikationsstellung"),
    ("Standardtherapie", r"Standardtherapien?"),
    ("Krankheitsprogression", r"Krankheitsprogression(?:en)?"),
    ("Biosimilar", r"Biosimilars?"),
    ("Referenzpräparat", r"Referenzpräparat(?:e|es|s|en)?"),
    ("Kostenübernahme", r"Kostenübernahme"),
    ("Verlaufskontrolle", r"Verlaufskontrolle(?:n)?"),
    ("obligatorische Krankenpflegeversicherung", r"obligatorischen?\s+Krankenpflegeversicherung"),
    ("Kontraindikation", r"Kontraindikation(?:en)?"),
    ("Publikumspreis", r"Publikumspreis(?:es|e)?"),
    ("Vergütungskriterien", r"Vergütungskriteri(?:en|um)"),
    ("Sekundärprävention", r"Sekundärprävention"),
    ("Erstverschreibung", r"Erstverschreibung(?:en)?"),
    ("Weiterbehandlung", r"Weiterbehandlung(?:en)?"),
    ("Therapielinie", r"Therapielinien?"),
    ("Vortherapie", r"Vortherapien?"),
    ("Primärprävention", r"Primärprävention"),
    ("Erstverordnung", r"Erstverordnung(?:en)?"),
    ("Therapieabbruch", r"Therapieabbruchs?"),
    ("Fachinformation", r"Fachinformation(?:en)?"),
    ("Zweitlinientherapie", r"Zweitlinientherapien?"),
    ("Krankenkasse", r"Krankenkassen?"),
]
HEAD_RX = {t: re.compile(r"(?<![\w])(?:" + rx + r")(?![\w])", re.I) for t, rx in HEADS}

# function words that may not start or end a rendering (audit's unambiguous ones plus articles / short prepositions)
_FW_EXTRA = {"fr": "le la les l' d' de du des un une et ou à au aux en par pour sur dans avec que qui ne n' qu' s' c' se sa son "
                   "ses ce cette ces est sont a été y il elle ils cas",
             "it": "il lo la i gli le l' un un' uno una di da in a e o con per su dell' all' dall' nell' sull' è al del della "
                   "dello dei degli delle ai agli alle nel nei negli nelle sul dal dai che non si ha caso"}
# a rendering (a noun phrase) never spans a coordination or a finite / modal / auxiliary verb
COORD = {"fr": set("et ou est sont être été doit doivent peut peuvent sera seront a ont".split()),
         "it": set("e ed o od è sono essere stato deve devono può possono sarà saranno ha hanno".split())}
TOK = re.compile(r"[^\W\d_]+'|[^\W_]\w*(?:-\w+)*|[.,;:!?()\[\]«»\"/=+<>≥≤–—]")
BR = "|"                                  # punctuation: no rendering spans it
DTOK = re.compile(r"[^\W\d_]\w*(?:-\w+)*")


def _stop():
    from . import audit
    return {L: frozenset(audit.FW[L]) | frozenset(_FW_EXTRA[L].split()) for L in LANGS}


_STOP = {}


def stop(L):
    if not _STOP: _STOP.update(_stop())
    return _STOP[L]


def _nrm(t):
    from .sl.ingest import nrm
    return nrm(t or "").replace("’", "'")


def toks(t):
    """target tokens: lower-cased, hyphen compounds whole, elided articles split off (l', d', dell', un' ...); every
    punctuation mark becomes the break token '|' (no n-gram spans it)."""
    out = []
    for w in TOK.findall(_nrm(t)):
        w = BR if not (w[0].isalnum() or w[0] == "_") else w.lower()
        if not (w == BR and out and out[-1] == BR): out.append(w)
    return out


def surface(g):
    """'code d' indication' -> "code d'indication" (no space after an elided article)."""
    return re.sub(r"' ", "'", g)


def _okgram(g, L):
    S = stop(L)
    return (BR not in g and not COORD[L].intersection(g) and g[0] not in S and g[-1] not in S and not g[0].isdigit() and not g[-1].isdigit()
            and any(len(w) >= 3 and not w.endswith("'") for w in g) and not g[-1].endswith("'"))


def grams(ws, L, nmax=MAX_N):
    """-> Counter of the candidate n-grams (M2) of a token list."""
    c = Counter(); S = stop(L)
    for i in range(len(ws)):
        if ws[i] in S or ws[i] == BR or ws[i].isdigit(): continue
        for n in range(1, nmax + 1):
            g = ws[i:i + n]
            if len(g) < n or g[-1] == BR: break
            if _okgram(g, L): c[" ".join(g)] += 1
    return c


def count(g, ws_joined):
    """occurrences of n-gram g (space-joined tokens) in ' '.join(tokens) padded with spaces."""
    return ws_joined.count(" " + g + " ")


def _pad(ws): return " " + " ".join(ws) + " "


def de_count(term, de):
    return len(HEAD_RX[term].findall(_nrm(de)))


def _lang_ok(t, L):
    from . import audit
    h = audit.fw_hits(audit.words(t))
    return not any(h[X] >= max(audit.LID_MIN, audit.LID_RATIO * h[L]) for X in h if X != L)


# ------------------------------------------------------------------------------------------------------- mining
class Corpus:
    """one target language of one snapshot, as aligned sentence units (M1): every limitation's German and target text cut
    into the sentence beads of emit.segment.align (the XLIFF segmentation), so a rendering is counted against the German
    sentence it translates, not against boilerplate elsewhere in the text. Per unit: German term counts, German word
    counts, target n-grams; self.lim maps a unit to its limitation id (counts are reported in limitations)."""
    def __init__(self, J, L):
        from .emit.segment import align
        self.L = L; self.ids, self.de, self.tg, self.lim = [], {}, {}, {}
        lims = [i for i in sorted(J["de"]["lim"]) if J[L]["lim"].get(i) and J["de"]["lim"][i] and _lang_ok(J[L]["lim"][i], L)]
        self.n_lim = len(lims)
        for i in lims:
            de, tg = _nrm(J["de"]["lim"][i]), _nrm(J[L]["lim"][i])
            for k, (a0, a1, b0, b1) in enumerate(align(de, tg)):
                u = (i, k); self.ids.append(u); self.de[u] = de[a0:a1]; self.tg[u] = tg[b0:b1]; self.lim[u] = i
        self.tw = {i: toks(self.tg[i]) for i in self.ids}
        self.pad = {i: _pad(self.tw[i]) for i in self.ids}
        self.G = {i: grams(self.tw[i], L) for i in self.ids}
        self.tot, self.inv = Counter(), defaultdict(list)
        for i, c in self.G.items():
            self.tot.update(c)
            for g in c: self.inv[g].append(i)
        self.dw = {i: Counter(w.lower() for w in DTOK.findall(self.de[i])) for i in self.ids}
        self.dwdf = Counter()
        for c in self.dw.values(): self.dwdf.update(c.keys())
        self.dwtot = Counter()
        for c in self.dw.values(): self.dwtot.update(c)

    def gcount(self, g): return {i: self.G[i][g] for i in self.inv.get(g, ())}


def _dice(cd, cg, sd, sg):
    """occurrence-level Dice (M3): cd, cg = {id: count}."""
    a = sum(min(n, cg.get(i, 0)) for i, n in cd.items())
    return 2 * a / (sd + sg) if sd + sg else 0.0


def _exclusive(C, term, cd, g, cg, own):
    """M4 -> (ok, rival word or None)."""
    sd, sg = sum(cd.values()), sum(cg.values())
    a_t = _dice(cd, cg, sd, sg)
    best, rival = a_t, None
    co = Counter()
    for i, n in cg.items():
        for w, m in C.dw[i].items(): co[w] += min(n, m)
    for w, a in co.items():
        if w in own or C.dwdf[w] < 3: continue
        d = 2 * a / (sg + C.dwtot[w])
        if d > best: best, rival = d, w
    if rival is None: return True, None
    t_not_w = [i for i in cd if not C.dw[i].get(rival)]
    w_not_t = [i for i in C.ids if i not in cd and C.dw[i].get(rival)]
    if len(t_not_w) < EXCL_MIN: return False, rival
    p1 = sum(1 for i in t_not_w if cg.get(i)) / len(t_not_w)
    p2 = sum(1 for i in w_not_t if cg.get(i)) / len(w_not_t) if w_not_t else 0.0
    return (p1 >= EXCL_SHARE and p1 > p2), rival


def _contains(big, small): return (" " + big + " ").find(" " + small + " ") >= 0


def _own_words(C, term):
    """German words inside the term's own matches (never rivals of it)."""
    own = set()
    for i in C.ids:
        for m in HEAD_RX[term].finditer(C.de[i]): own.update(w.lower() for w in DTOK.findall(m.group(0)))
    return own


def _select(C, cd, ok, avoid=(), min_sup=MIN_SUPPORT, ok_ext=None, extend=True, block=None):
    """M2-M5 on the limitations in cd ({id: count of the term}) -> (rendering, its Dice) or (None, None). avoid: n-grams a
    rendering may not contain or be contained in."""
    D = list(cd); sd = sum(cd.values())
    sup, occ, a = Counter(), Counter(), Counter()
    for i in D:
        for g, n in C.G[i].items():
            if any(_contains(g, x) or _contains(x, g) for x in avoid): continue
            sup[g] += 1; occ[g] += n; a[g] += min(n, cd[i])
    cands = [g for g in sup if sup[g] >= min_sup and not (block and block(g))]
    if not cands: return None, None
    sc = {g: 2 * a[g] / (sd + C.tot[g]) for g in cands}
    head = next((g for g in sorted(cands, key=lambda g: (-sc[g], len(g.split()), g))[:TOP_K] if ok(g)), None)
    ok_ext = ok_ext or ok
    if head is None: return None, None
    best = head
    for g in () if not extend else sorted((g for g in cands if g != head and _contains(g, head) and occ[g] >= EXTEND * occ[head]),
                    key=lambda g: (-len(g.split()), -occ[g], g)):
        added = [w for w in _minus(g, head) if w not in stop(C.L) and len(w) >= 3]
        if all(ok_ext(w) for w in added): best = g; break
    return best, round(sc[best], 3)


def _minus(g, head):
    """the tokens of g outside its (first) occurrence of head."""
    G, Hh = g.split(), head.split()
    for k in range(len(G) - len(Hh) + 1):
        if G[k:k + len(Hh)] == Hh: return G[:k] + G[k + len(Hh):]
    return G


def mine_term(C, term, block=None):
    """-> entry dict for one term and one language (M2-M7). block(g): candidates explained by another term (M8)."""
    cd = {i: n for i in C.ids for n in (len(HEAD_RX[term].findall(C.de[i])),) if n}
    D = sorted(cd); nl = lambda us: len({C.lim[u] for u in us})
    e = dict(term=term, lang=C.L, limitations_with_term=nl(D), preferred=None, support=0, share=0.0, variants=[], house=False)
    if nl(D) < MIN_SUPPORT: e["note"] = "term in fewer than MIN_SUPPORT limitations"; return e
    own = _own_words(C, term); memo = {}

    def ex(g):
        if g not in memo: memo[g] = _exclusive(C, term, cd, g, C.gcount(g), own)
        return memo[g]

    def ok(g): return ex(g)[1] is None                  # M4 for a rendering: the term is its strongest German associate

    def ok_ext(w): return ex(w)[0] if EXT_LENIENT else ex(w)[1] is None
    pref, dice = _select(C, cd, ok, ok_ext=ok_ext, block=block)
    if pref is None: e["note"] = "no candidate rendering passes M2-M4"; return e
    has = [i for i in D if count(pref, C.pad[i])]
    e.update(preferred_tokens=pref, preferred=surface(pref), support=nl(has), share=round(nl(has) / nl(D), 3), dice=dice)
    # M7: the same selection on the limitations with the term but without the preferred rendering, repeatedly
    R = {i: cd[i] for i in D if not count(pref, C.pad[i])}
    e["without_preferred"] = nl(R)
    avoid = [pref]
    while R and len(e["variants"]) < MAX_VARIANTS:
        v, vd = _select(C, R, lambda g: ok(g) and _not_german(C, g, R), avoid, VAR_MIN, ok_ext, block=block)
        if v is None: break
        cov = [i for i in R if count(v, C.pad[i])]
        if vd < VAR_DICE or _inflection(v, pref): avoid.append(v); continue
        lift_in = len(cov) / len(R); out_ = (len(C.inv.get(v, ())) - sum(1 for i in D if count(v, C.pad[i]))) / max(1, len(C.ids) - len(D))
        avoid.append(v)
        if lift_in < VAR_LIFT * out_: continue
        e["variants"].append(dict(tokens=v, text=surface(v), limitations=nl(i for i in D if count(v, C.pad[i])),
                                  without_preferred=nl(cov), dice=vd))
        R = {i: n for i, n in R.items() if i not in set(cov)}
    e["dominance"] = round(e["support"] / (e["support"] + sum(v["without_preferred"] for v in e["variants"])), 3)
    e["house"] = e["support"] >= MIN_SUPPORT and e["share"] > MIN_SHARE
    if not e["house"]: e["note"] = f"no dominant rendering (share {e['share']:.2f} not above {MIN_SHARE})"
    return e


def _blocker(C, term, claims):
    """M8 (second pass): a candidate that contains another term's house rendering, in units where that other term is in
    the German (>= half of the candidate's units), is that term's rendering plus context ('altro biosimilare' next to
    'Biosimilar'), not a rendering of this term."""
    others = [(u, c) for u, c in claims.items() if u != term]

    def block(g):
        for u, c in others:
            if g != c and _contains(g, c):
                us = C.inv.get(g, ())
                if us and sum(1 for x in us if HEAD_RX[u].search(C.de[x])) >= 0.5 * len(us): return True
        return False
    return block


def _inflection(a, b):
    """a and b differ only by inflection: same number of tokens, each pair equal or sharing its first 5 letters with at
    most 2 letters different in length (audit's T1 rule, one letter longer: 'spécialiste' / 'spécialistes')."""
    A, B = a.split(), b.split()
    return len(A) == len(B) and all(x == y or (x[:5] == y[:5] and abs(len(x) - len(y)) <= 2) for x, y in zip(A, B))


def _loose(g):
    """regex for n-gram g in a text, inflection-tolerant: every token of >= 5 letters may change its last 1-2 letters
    (singular / plural, gender), hyphens and apostrophes as written."""
    parts = g.split(" "); rx = ""
    for k, w in enumerate(parts):
        if len(w) >= 5 and w[-1].isalpha():
            st = re.sub(r"(?:[sx]|[eiao]|e[sx]|[ia]e)$", "", w)
            rx += re.escape(st).replace(r"\-", "-") + r"[^\W\d_]{0,3}"
        else:
            rx += re.escape(w).replace("'", "['’]").replace(r"\-", "-")
        if k < len(parts) - 1: rx += r"\s*" if w.endswith("'") else r"\s+"
    return re.compile(r"(?<![\w-])" + rx + r"(?![\w-])", re.I)


def _not_german(C, g, R):
    """False when a word of g (>= 3 letters) is written in the German text of a limitation where g occurs (a name, an INN)."""
    for i in R:
        if C.G[i].get(g) and any(re.search(r"(?<![\w-])" + re.escape(w) + r"(?![\w-])", C.de[i], re.I) for w in g.split() if len(w) >= 3):
            return False
    return True


# Review of the mined output (10 Oct 2026, read by the team's coding agent against the register; no human linguist):
# renderings that are fragments of the real term are not exported or used (house=false, note says why); variants that are
# not renderings of the term are dropped. Everything else is exactly what the mining produced.
REJECT = {("fr", "Universitätsklinik"): "fragment (« universitaires »)", ("fr", "Therapiebeginn"): "fragment (« début »)",
          ("fr", "Originalpräparat"): "fragment (« originale »)", ("fr", "Therapiedauer"): "fragment (« durée »)",
          ("fr", "Standardtherapie"): "fragment (« standard »)", ("it", "Standardtherapie"): "fragment («standard»)",
          ("fr", "Therapielinie"): "fragment (« lignes »)", ("it", "Therapielinie"): "fragment («linee»)",
          ("fr", "Zweitlinientherapie"): "fragment (« traitement de deuxième »)",
          ("fr", "Stammzelltransplantation"): "fragment (« cellules souches »)",
          ("it", "Stammzelltransplantation"): "fragment («cellule staminali»)",
          ("it", "Verlaufskontrolle"): "fragment («effettuati»; house only in the 1 Sep 2026 snapshot, PREREG R12)"}
DROP_VARIANTS = {("fr", "Mehrwertsteuer"): {"récupérée", "réclamée"}, ("fr", "Körpergewicht"): {"pesant"},
                 ("it", "Erstlinienbehandlung"): {"linea di pazienti adulti"}}


def review(entries):
    for e in entries:
        k = (e["lang"], e["term"])
        if k in DROP_VARIANTS: e["variants"] = [v for v in e["variants"] if v["text"] not in DROP_VARIANTS[k]]
        if k in REJECT and e.get("house"): e["house"] = False; e["note"] = f"rejected on review: {REJECT[k]}"
    return entries


def mine(J, date=DATE, terms=None):
    """-> termbase dict (meta + entries) from one aligned snapshot J (audit.load)."""
    entries = []
    for L in LANGS:
        C = Corpus(J, L); T = [t for t, _ in HEADS if not terms or t in terms]
        first = {t: mine_term(C, t) for t in T}
        claims = {t: e["preferred_tokens"] for t, e in first.items() if e.get("house")}
        for t in T:
            entries.append(mine_term(C, t, _blocker(C, t, claims)))
    for e in entries:
        e.pop("head", None)
    review(entries)
    meta = dict(generated_by=f"gleichlaut termbase --date {date}", date=date, source=f"BAG Spezialitätenliste, public ePL FHIR feed {_d(date)}",
                limitations=len(J["de"]["lim"]), unit="aligned sentence bead (emit.segment.align)", heads=len(HEADS) if not terms else len(terms),
                rules=dict(min_support=MIN_SUPPORT, min_share=MIN_SHARE, extend=EXTEND, max_ngram=MAX_N, top_k=TOP_K,
                           exclusive_share=EXCL_SHARE, exclusive_min=EXCL_MIN, variant_min=VAR_MIN, variant_lift=VAR_LIFT,
                           max_variants=MAX_VARIANTS),
                note="Mined from the register itself (docs/termbase.md). 'support' and variant counts are limitations; "
                     "'share' = support / limitations whose German contains the term. house=false: no dominant rendering.")
    return dict(meta=meta, entries=entries)


SHARED = os.path.join(DEST, f"shared_words_{DATE}.json")
SWORD = re.compile(r"[^\W\d_]+(?:-[^\W\d_]+)*")


def shared_words(J, date=DATE):
    """Words the German and a target register share (presentation only: an 'untranslated German' finding on such a word is
    worded as probably fine, emit.explain.lexicon_fine): per target language, the lower-cased words of 3+ letters that are
    in at least one German limitation text and in at least as many target-language texts of that language as German ones
    (document frequency; a target field written in another language is skipped, as M1). 'allergie' (2 French, 2 German)
    is in; 'die', 'in', 'colitis' (German far more often) are not. Mined, never written by hand."""
    df = {}
    for L in ("de",) + LANGS:
        c = Counter()
        for t in J[L]["lim"].values():
            if not t or (L != "de" and not _lang_ok(t, L)): continue
            c.update({w.lower() for w in SWORD.findall(_nrm(t))})
        df[L] = c
    out = dict(meta=dict(generated_by=f"gleichlaut termbase --date {date}", date=date, source=f"BAG Spezialitätenliste, public "
                         f"ePL FHIR feed {_d(date)}", rule="lower-cased words of >= 3 letters with df(target) >= df(German) >= 1 "
                         "(document frequency over the limitation texts; target fields in another language skipped)"))
    for L in LANGS:
        out[L] = sorted(w for w, n in df[L].items() if len(w) >= 3 and df["de"][w] and n >= df["de"][w])
    return out


_SW = {}


def shared(L, path=SHARED):
    """-> frozenset of the words the German and target register L share (shared_words), empty when the file is absent."""
    if path not in _SW:
        try: d = json.load(open(path, encoding="utf-8")); _SW[path] = {k: frozenset(d[k]) for k in LANGS}
        except (OSError, ValueError, KeyError): _SW[path] = {k: frozenset() for k in LANGS}
    return _SW[path].get(L, frozenset())


def _d(d): return f"{d[6:8]}.{d[4:6]}.{d[:4]}" if isinstance(d, str) and re.fullmatch(r"\d{8}", d) else str(d)


# ------------------------------------------------------------------------------------------------------- TBX
def tbx(tb):
    """TBX-Basic, TBX v3 (ISO 30042:2019) DCA style: one conceptEntry per German term with at least one house rendering;
    the house rendering is preferredTerm-admn-sts, BAG's own minority variants admittedTerm-admn-sts, each with its
    source ('mined from BAG SL <date>, n limitations')."""
    import xml.etree.ElementTree as ET
    ET.register_namespace("", TBX_NS)
    q = lambda t: f"{{{TBX_NS}}}{t}"
    XL = "{http://www.w3.org/XML/1998/namespace}lang"
    m = tb["meta"]; date = _d(m["date"])
    root = ET.Element(q("tbx"), {"type": "TBX-Basic", "style": "dca", XL: "de"})
    fd = ET.SubElement(ET.SubElement(root, q("tbxHeader")), q("fileDesc"))
    ET.SubElement(ET.SubElement(fd, q("titleStmt")), q("title")).text = f"Gleichlaut SL termbase {date} (DE-FR-IT)"
    ET.SubElement(ET.SubElement(fd, q("sourceDesc")), q("p")).text = (
        f"Mined by Gleichlaut (no model) from the {m['limitations']} limitation texts of the BAG Spezialitätenliste, public ePL "
        f"FHIR feed {date}: per German term, the French / Italian n-gram most associated with it in the limitations whose "
        "German contains it. preferredTerm = the register's dominant rendering; admittedTerm = a minority variant the "
        "register also uses. Counts are limitations. Unreviewed: check before adopting.")
    body = ET.SubElement(ET.SubElement(root, q("text")), q("body"))
    by = defaultdict(dict)
    for e in tb["entries"]: by[e["term"]][e["lang"]] = e
    k = 0
    for term, _ in HEADS:
        E = {L: e for L, e in by.get(term, {}).items() if e.get("house")}
        if not E: continue
        k += 1
        ce = ET.SubElement(body, q("conceptEntry"), {"id": f"sl{k:03d}"})
        de = ET.SubElement(ce, q("langSec"), {XL: "de"})
        ts = ET.SubElement(de, q("termSec")); ET.SubElement(ts, q("term")).text = term.split(" / ")[-1]
        n_de = max(e["limitations_with_term"] for e in E.values())
        ET.SubElement(ts, q("admin"), {"type": "source"}).text = f"BAG SL {date}, {n_de} limitations"
        for L in LANGS:
            e = E.get(L)
            if not e: continue
            ls = ET.SubElement(ce, q("langSec"), {XL: L})
            ts = ET.SubElement(ls, q("termSec")); ET.SubElement(ts, q("term")).text = e["preferred"]
            ET.SubElement(ts, q("termNote"), {"type": "administrativeStatus"}).text = "preferredTerm-admn-sts"
            ET.SubElement(ts, q("admin"), {"type": "source"}).text = f"mined from BAG SL {date}, {e['support']} limitations"
            ET.SubElement(ts, q("note")).text = (f"{e['support']} of {e['limitations_with_term']} limitations whose German "
                                                 f"contains the term ({round(100 * e['share'])}%)")
            for v in e["variants"]:
                vs = ET.SubElement(ls, q("termSec")); ET.SubElement(vs, q("term")).text = v["text"]
                ET.SubElement(vs, q("termNote"), {"type": "administrativeStatus"}).text = "admittedTerm-admn-sts"
                ET.SubElement(vs, q("admin"), {"type": "source"}).text = f"mined from BAG SL {date}, {v['limitations']} limitations"
                ET.SubElement(vs, q("note")).text = f"minority variant in the register; house rendering: {e['preferred']}"
    return ET.ElementTree(root)


ADMN = {"preferredTerm-admn-sts", "admittedTerm-admn-sts", "deprecatedTerm-admn-sts", "supersededTerm-admn-sts"}


def validate_tbx(path):
    """Well-formedness and the TBX v3 core structure this file uses -> [errors] (empty = valid)."""
    import xml.etree.ElementTree as ET
    q = lambda t: f"{{{TBX_NS}}}{t}"
    XL = "{http://www.w3.org/XML/1998/namespace}lang"
    try: r = ET.parse(path).getroot()
    except ET.ParseError as e: return [f"not well-formed: {e}"]
    err = []
    if r.tag != q("tbx"): err.append(f"root is {r.tag}, not tbx in {TBX_NS}")
    if r.get("type") != "TBX-Basic" or r.get("style") != "dca": err.append("tbx needs type=TBX-Basic style=dca")
    if not r.get(XL): err.append("tbx needs xml:lang")
    if [c.tag for c in r] != [q("tbxHeader"), q("text")]: err.append("tbx must hold tbxHeader then text")
    if r.find(f"{q('tbxHeader')}/{q('fileDesc')}/{q('sourceDesc')}") is None: err.append("tbxHeader/fileDesc/sourceDesc missing")
    body = r.find(f"{q('text')}/{q('body')}")
    if body is None: return err + ["text/body missing"]
    ids = set()
    for ce in body:
        if ce.tag != q("conceptEntry"): err.append(f"body child {ce.tag}"); continue
        i = ce.get("id")
        if not i or not re.fullmatch(r"[A-Za-z_][\w.-]*", i) or i in ids: err.append(f"conceptEntry id {i!r} missing, not an NCName or duplicate")
        ids.add(i)
        LS = list(ce)
        if len(LS) < 2 or any(x.tag != q("langSec") or not x.get(XL) for x in LS): err.append(f"{i}: needs >= 2 langSec with xml:lang")
        for ls in LS:
            if not len(ls) or any(t.tag != q("termSec") for t in ls): err.append(f"{i}: langSec must hold termSec only"); continue
            for ts in ls:
                kids = list(ts)
                if not kids or kids[0].tag != q("term") or not (kids[0].text or "").strip(): err.append(f"{i}: termSec must start with a term")
                if sum(k.tag == q("term") for k in kids) != 1: err.append(f"{i}: one term per termSec")
                seen_aux = False
                for k in kids[1:]:
                    if k.tag == q("termNote"):
                        if seen_aux: err.append(f"{i}: termNote after admin/note")
                        if k.get("type") == "administrativeStatus" and k.text not in ADMN: err.append(f"{i}: bad administrativeStatus {k.text}")
                    elif k.tag in (q("admin"), q("note"), q("descrip")): seen_aux = True
                    else: err.append(f"{i}: unexpected {k.tag} in termSec")
            pref = [ts for ts in ls if any(k.get("type") == "administrativeStatus" and k.text == "preferredTerm-admn-sts" for k in ts)]
            if ls.get(XL) != "de" and len(pref) != 1: err.append(f"{i}/{ls.get(XL)}: exactly one preferred term")
    if not ids: err.append("no conceptEntry")
    return err


# ------------------------------------------------------------------------------------------------------- advisory
_TB = {}


def load(path=JSON):
    """-> {(lang, term): entry} of the house renderings (house=true), {} when the file is absent."""
    if path not in _TB:
        try:
            d = json.load(open(path, encoding="utf-8"))
            _TB[path] = {(e["lang"], e["term"]): e for e in d["entries"] if e.get("house") and e.get("preferred")}
        except (OSError, ValueError, KeyError):
            _TB[path] = {}
    return _TB[path]


NOTE = {"fr": dict(head="Terme maison pour {de} : {pref} ({n} limitations)", wrote="le brouillon écrit {x}",
                   absent="absent du brouillon", carried="", kept="le texte (déjà avant) écrit {x}",
                   fewer="le brouillon l'écrit {k} fois, l'allemand a le terme {n} fois"),
        "it": dict(head="Termine in uso all'UFSP per {de}: {pref} ({n} limitazioni)", wrote="la bozza scrive {x}",
                   absent="assente dalla bozza", carried="", kept="il testo (già prima) scrive {x}",
                   fewer="la bozza lo scrive {k} volta/e, il tedesco ha il termine {n} volte")}
FUZZY = 0.6
KEPT_FUZZY = 0.7       # "kept", a wording found by similarity: at least this similar, two words or more, no word of the house rendering
NEAR = 4              # "kept": tokens around the draft's own insertions count as inserted ('à transmettre à la caisse maladie')


def _q(L, s): return f"« {s} »" if L == "fr" else f"«{s}»"


def _surface_in(text, g):
    """the n-gram g (space-joined tokens) as written in text, or None."""
    parts = g.split(" ")
    rx = ""
    for k, w in enumerate(parts):
        rx += re.escape(w).replace("'", "['’]").replace(r"\-", "-")
        if k < len(parts) - 1: rx += r"\s*" if w.endswith("'") else r"\s+"
    m = re.search(r"(?<![\w-])" + rx + r"(?![\w-])", text, re.I)
    return m.group(0) if m else None


def _fuzzy(pref, draft_ws, old_pad, L, in_old=False, within=None, ratio=None):
    """the draft's n-gram (one token shorter to one longer than the house rendering) most similar to it (ratio >= FUZZY),
    not in the old text (in_old=True: only one the old text has too) and not containing the house rendering itself, or
    None. within: draft token positions the n-gram must touch (None: anywhere)."""
    n = len(pref.split()); best = None; rx = _loose(pref)
    for k in range(max(1, n - 1), n + 2):
        for i in range(len(draft_ws) - k + 1):
            if within is not None and not any(j in within for j in range(i, i + k)): continue
            g = draft_ws[i:i + k]
            if not _okgram(g, L): continue
            s = " ".join(g)
            if s == pref or bool(count(s, old_pad)) != in_old or rx.search(surface(s)): continue
            r = difflib.SequenceMatcher(None, s, pref).ratio()
            if r >= (ratio or FUZZY) and (best is None or r > best[0]): best = (r, s)
    return best[1] if best else None


def advice(v, tb=None):
    """-> [dict(term, preferred, support, wrote, kind, n_de, n_draft[, rewrote])] for one draft view (lang, de_old, de_new,
    tgt_old, draft). kind: "variant" (the draft introduces a recorded minority variant, or writes one in a sentence it
    inserted or rewrote), "missing" (the draft falls short of the house rendering where the old text did not, or writes a
    non-standard wording in a sentence it inserted or rewrote), or "kept" (softer: the draft falls short, the old text
    already did, and the draft carries over unchanged a sentence with a non-standard wording the old text used that is not
    one of BAG's recorded variants: a spelling variant of the house rendering, or the wording most similar to it; _kept).
    Recorded variants are matched spelling-tolerantly (_ortho: 'assurance-maladie' is the variant 'assurance maladie').
    rewrote=True: the wording sits in text the draft wrote (a sentence it inserted, or an edited sentence whose old version
    did not have the wording; _rewritten).
    n_de / n_draft: how often the new German has the term and the draft the house rendering. eval/results/termbase.json
    measures the first two kinds (measure()); all three are counted in explain_v2.json / explain_v3.json."""
    L = v.get("lang"); draft = (v.get("draft") or "").replace("\u02bc", "'")
    if L not in LANGS or not draft or v.get("status") == "human": return []
    tb = load() if tb is None else tb
    if not tb: return []
    old = (v.get("tgt_old") or "").replace("\u02bc", "'")
    ws = toks(draft); wo = toks(old); pd, po = _pad(ws), _pad(wo); fd, fo = _fpad(ws), _fpad(wo)
    dn, on = _nrm(draft), _nrm(old)
    new_idx = {j for op, _, _, j1, j2 in difflib.SequenceMatcher(None, wo, ws, autojunk=False).get_opcodes()
               if op in ("insert", "replace") for j in range(j1 - NEAR, j2 + NEAR)}   # draft text the draft inserted / rewrote
    olds = _old_sentences(old)
    out = []
    for term, _ in HEADS:
        e = tb.get((L, term))
        if not e: continue
        n_new = de_count(term, v.get("de_new") or "")
        if not n_new: continue
        n_old = de_count(term, v.get("de_old") or "")
        p = e.get("preferred_tokens") or " ".join(toks(e["preferred"]))
        rx = _loose(p); p_new, p_old = len(rx.findall(dn)), len(rx.findall(on))
        fp = _ortho(surface(p))
        V = [(w, f) for w in e["variants"] for f in (_ortho(surface(w["tokens"])),) if f != fp]
        intro = [w for w, f in V if _fcount(f, fd) > _fcount(f, fo)]
        gap = max(0, n_new - p_new) > max(0, n_old - p_old)
        a = dict(term=term.split(" / ")[-1], preferred=e["preferred"], support=e["support"], n_de=n_new, n_draft=p_new)
        if intro:
            w = intro[0]; out.append(dict(a, wrote=_surface_in(draft, w["tokens"]) or _first(draft, _vrx(w["tokens"])) or w["text"], kind="variant"))
        elif gap:
            f = None if p_new else _fuzzy(p, ws, po, L)          # the house rendering is there, only too few times
            out.append(dict(a, wrote=(_surface_in(draft, f) or surface(f)) if f else None, kind="missing"))
        elif p_new < n_new:
            r = next((m for w, _ in V for m in (_rewritten(draft, olds, _vrx(w["tokens"])),) if m), None)
            if r:                                   # a recorded variant in a sentence the draft wrote: the draft's own wording
                out.append(dict(a, wrote=r, kind="variant", rewrote=True)); continue
            f = _kept(e, p, ws, pd, po, L, new_idx)
            if f:
                r = _rewritten(draft, olds, _vrx(f))
                out.append(dict(a, wrote=r or _surface_in(draft, f) or surface(f), kind="missing" if r else "kept", rewrote=bool(r)))
    return out


def _fpad(ws):
    """the token list folded for spelling (_ortho), space-padded: 'assurance-maladie' reads as 'assurance maladie'."""
    return " " + " ".join(w if w == BR else _ortho(w) for w in ws) + " "


def _fcount(f, fpad): return fpad.count(" " + f + " ")


def _vrx(g):
    """regex for the n-gram g (space-joined tokens) as written, spelling-tolerant as _ortho folds it: hyphen, apostrophe
    or space between the words, a plural -s / -x on each."""
    parts = [w for w in g.split(" ") if w]
    body = r"[\s'’-]*".join(re.escape(w.rstrip("'")).replace(r"\-", r"[\s-]") + (r"['’]" if w.endswith("'") else r"[sx]?")
                            for w in parts)
    return re.compile(r"(?<![\w-])" + body + r"(?![\w-])", re.I)


def _first(text, rx):
    m = rx.search(text)
    return m.group(0) if m else None


def _skey(s):
    """a sentence normalised for 'carried over unchanged' (house.key: spacing, apostrophes, numbers)."""
    from .house import key
    return key(s)


def _old_sentences(old):
    """-> {sentence key: sentence} of the old target text."""
    from .emit.segment import sentences
    return {_skey(old[a:b]): old[a:b] for a, b in sentences(old)}


EDITED = 0.5          # a draft sentence at least this similar to an old sentence is that sentence, edited


def _rewritten(draft, olds, rx):
    """the first occurrence of rx in the draft that sits in text the draft wrote, as written, or None. Carried over (None)
    is an occurrence in a sentence of the old text (unchanged), or in an edited version of one (word similarity >= EDITED
    to its most similar old sentence) that already had the wording; written is an occurrence in a sentence the
    draft inserted, or in an edited sentence whose old version did not have it."""
    from .emit.segment import sentences
    S = sentences(draft)
    for m in rx.finditer(draft):
        s = next(((a, b) for a, b in S if a <= m.start() < b), None)
        if not s: continue
        k = _skey(draft[s[0]:s[1]])
        if k in olds: continue
        sim = lambda o: difflib.SequenceMatcher(None, k.split(), o.split(), autojunk=False).ratio()
        best = max(olds, key=sim, default=None)
        if best is not None and sim(best) >= EDITED and rx.search(olds[best]): continue
        return m.group(0)
    return None


def _ortho(g):
    """an n-gram folded for spelling: lower case, no accents, hyphens and apostrophes as spaces, no plural -s / -x
    ('assureur maladie', 'assureurs-maladie' and 'assureur-maladie' fold alike)."""
    import unicodedata
    g = "".join(c for c in unicodedata.normalize("NFD", g.lower()) if unicodedata.category(c) != "Mn")
    g = re.sub(r"[-'’\s]+", " ", g).strip()
    return " ".join(re.sub(r"(?<=\w{4})[sx]$", "", w) for w in g.split())


def _kept(e, p, ws, pd, po, L, new_idx):
    """the non-standard wording of a term that the draft keeps from the old text (advice, kind "kept"), or None: a
    spelling variant of the house rendering both have ('assureur maladie', 'médecin conseil'); else, in text the draft
    inserted or rewrote (within NEAR tokens), the wording most similar to the house rendering (as _fuzzy) that the old
    text also uses ('caisse maladie'). Never one of BAG's own recorded minority variants ('assurance maladie', 266
    limitations: BAG's practice, not the draft's), nor a plural or other inflection of the house rendering itself."""
    V = [_ortho(surface(w["tokens"])) for w in e["variants"]]
    def recorded(g):
        o = _ortho(surface(g))
        return any(o == v or _contains(o, v) or _contains(v, o) for v in V)
    n, fp = len(p.split()), _ortho(surface(p))
    for k in range(1, n + 3):
        for i in range(len(ws) - k + 1):
            g = " ".join(ws[i:i + k])
            if BR not in g and g != p and _ortho(surface(g)) == fp and count(g, po) and not _inflection(g, p) and not recorded(g):
                return g
    if not new_idx: return None
    f = _fuzzy(p, ws, po, L, in_old=True, within=new_idx, ratio=KEPT_FUZZY)
    if f is None or _inflection(f, p) or _ortho(surface(f)) == fp or recorded(f): return None
    if len(f.split()) < 2 and "-" not in f: return None                     # one plain word ('maladie') names no term
    if set(f.split()) & {w for w in p.split() if len(w) >= 5}: return None   # a fragment around the house rendering itself
    return f


def advisory_text(A, L):
    """one low-priority note in the reviewer's language, or None: per term (the softer "kept" ones last), the house
    rendering and what the draft writes instead ("kept": what the text already wrote before), or how often it writes the
    house rendering against how often the German has the term, or that the draft does not write it at all."""
    if not A or L not in NOTE: return None
    N = NOTE[L]; parts = []
    for a in sorted(A, key=lambda a: a["kind"] == "kept")[:3]:
        s = N["head"].format(de=_q(L, a["term"]), pref=_q(L, a["preferred"]), n=a["support"])
        s += " ; " if L == "fr" else "; "
        if a["kind"] == "kept": s += N["kept"].format(x=_q(L, a["wrote"]))
        elif a["wrote"]: s += N["wrote"].format(x=_q(L, a["wrote"]))
        elif a.get("n_draft"): s += N["fewer"].format(k=a["n_draft"], n=a["n_de"])
        else: s += N["absent"]
        parts.append(s + ".")
    return " ".join(parts)


# ------------------------------------------------------------------------------------------------------- measurement
RUNS = (("70b", "runs/70b_fresh166_g3_final.jsonl"), ("8b_q4_k_m", "runs/8b_q4_k_m_fresh166_g3_final.jsonl"),
        ("8b_q8_0", "runs/8b_q8_0_fresh166_g3_final.jsonl"))


def _labels_70b():
    """ready-draft labels of the 70B fresh-166 run: needs-fix by majority of three blind annotators, class from the
    tie-breaker or the second annotator (score.agreement's rule)."""
    from . import score
    L = score.LABELS
    U = score.load_labels("fresh166_unflagged.tsv")
    B = {c[0]: dict(fix=c[1], cls=c[2]) for c in (l.split("\t") for l in open(os.path.join(L, "fresh166_second_annotator.tsv"), encoding="utf-8").read().splitlines()[1:])}
    T = {c[0]: dict(fix=c[1], cls=c[2]) for c in (l.split("\t") for l in open(os.path.join(L, "fresh166_tiebreak.tsv"), encoding="utf-8").read().splitlines()[1:])}
    out = {}
    for k, c in U.items():
        a = "no" if c in ("equivalent", "preexisting", "exact") else "yes"
        fix = a if a == B[k]["fix"] else T[k]["fix"]
        cls = c if fix == "no" else (T[k]["cls"] if k in T else B[k]["cls"])
        out[k] = dict(fix=fix, cls=cls)
    return out


def _labels_8b(build):
    """ready-draft labels of an 8B run: the blind labels (final column), or the label inherited from an identical
    labelled 70B draft (score.m1's rule)."""
    from . import score
    from .certify import reference_labels
    lines = open(os.path.join(score.LABELS, f"m1_{build}_fresh166.tsv"), encoding="utf-8").read().splitlines()
    hdr = lines[0].split("\t"); new = {c[0]: dict(zip(hdr, c)) for c in (l.split("\t") for l in lines[1:])}
    ref = reference_labels(); R = score.load_jsonl(f"runs/8b_{build}_fresh166_g3_final.jsonl"); out = {}
    for k, r in R.items():
        if k in new: out[k] = dict(fix=new[k]["final_fix"], cls=new[k]["final"])
        else:
            c = ref.get(k, {}).get(core.lock.norm(r["out"]))
            if c: out[k] = dict(fix="no" if c in ("equivalent", "preexisting", "exact") else "yes", cls=c)
    return out


def measure(path=JSON):
    """eval/results/termbase.json: the termbase and the advisory on the fresh-166 drafts of the 70B and both 8B builds.
    Ready = the recorded guard verdict (replay re-guards every run and checks it). 'agrees_with_bag' = BAG's published
    text of the same amendment (tgt_new, evaluation data, never shown) contains the house rendering (inflection-tolerant,
as the advisory matches it)."""
    from . import score
    tb = load(path); d = json.load(open(path, encoding="utf-8"))
    I = score.load_items("items/items_fresh.json"); norm = core.lock.norm
    res = dict(termbase=dict(file=os.path.relpath(path, core.ROOT), sha256=hashlib.sha256(open(path, "rb").read()).hexdigest(),
                             heads=d["meta"]["heads"], entries=len(d["entries"]),
                             house={L: sum(1 for e in d["entries"] if e["lang"] == L and e.get("house")) for L in LANGS},
                             house_total=sum(1 for e in d["entries"] if e.get("house")),
                             variants={L: sum(len(e["variants"]) for e in d["entries"] if e["lang"] == L and e.get("house")) for L in LANGS}),
               runs={})
    labels = {"70b": _labels_70b(), "8b_q4_k_m": _labels_8b("q4_k_m"), "8b_q8_0": _labels_8b("q8_0")}
    for name, rel in RUNS:
        R = score.load_jsonl(rel); lab = labels[name]
        row = dict(run=rel, drafts=len(I), ready=0, flagged=0, ready_with_advisory=0, flagged_with_advisory=0,
                   advisories_ready=0, advisories_ready_agree_with_bag=0, ready_exact_with_advisory=0,
                   ready_needs_fix=0, ready_needs_fix_with_advisory=0, ready_minor=0, ready_minor_with_advisory=0,
                   ready_minor_keys_explained=[], ready_minor_keys_not_explained=[], ready_advisory_keys=[],
                   ready_advisory_keys_labelled_no_fix=[], ready_advisory_keys_bag_differs=[], by_term=Counter(), by_kind=Counter())
        for x in I:
            k = x["key"]; r = R[k]
            v = dict(lang=x["lang"], de_old=x["de_old"], de_new=x["de_new"], tgt_old=x["tgt_old"], draft=r["out"], status="draft")
            A = [a for a in advice(v, tb) if a["kind"] != "kept"]; ready = not r["guard_flag"]      # the v1 kinds (advice)
            if not ready:
                row["flagged"] += 1; row["flagged_with_advisory"] += bool(A); continue
            row["ready"] += 1
            lb = lab.get(k) or (dict(fix="no", cls="exact") if norm(r["out"]) == norm(x["tgt_new"]) else None)
            exact = norm(r["out"]) == norm(x["tgt_new"])
            if A:
                row["ready_with_advisory"] += 1; row["ready_advisory_keys"].append(k); row["ready_exact_with_advisory"] += exact
                row["advisories_ready"] += len(A)
                gold = _nrm(x["tgt_new"])
                for a in A:
                    p = tb[(x["lang"], next(t for t, _ in HEADS if t.split(" / ")[-1] == a["term"]))]
                    agree = bool(_loose(p.get("preferred_tokens") or " ".join(toks(p["preferred"]))).search(gold))
                    row["advisories_ready_agree_with_bag"] += agree
                    if not agree: row["ready_advisory_keys_bag_differs"].append(k)
                    row["by_term"][f"{x['lang']}:{a['term']}"] += 1; row["by_kind"][a["kind"]] += 1
            if A and lb and lb["fix"] == "no": row["ready_advisory_keys_labelled_no_fix"].append(k)
            if lb and lb["fix"] == "yes":
                row["ready_needs_fix"] += 1; row["ready_needs_fix_with_advisory"] += bool(A)
                if lb["cls"] == "minor":
                    row["ready_minor"] += 1; row["ready_minor_with_advisory"] += bool(A)
                    (row["ready_minor_keys_explained"] if A else row["ready_minor_keys_not_explained"]).append(k)
        row["by_term"] = dict(sorted(row["by_term"].items())); row["by_kind"] = dict(sorted(row["by_kind"].items()))
        res["runs"][name] = row
    return res


# ------------------------------------------------------------------------------------------------------- CLI
def write_json(tb, path):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh: json.dump(tb, fh, ensure_ascii=False, indent=1); fh.write("\n")


def write_tbx(tb, path):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    t = tbx(tb)
    try:
        import xml.etree.ElementTree as ET
        ET.indent(t, space=" ")                                   # Python >= 3.9
    except AttributeError:
        pass
    t.write(path, encoding="utf-8", xml_declaration=True)
    err = validate_tbx(path)
    if err: raise SystemExit(f"termbase: TBX {path} invalid: {'; '.join(err[:5])}")
    return path


def table(tb, out=sys.stdout):
    for e in tb["entries"]:
        if not e.get("preferred"): print(f"  {e['lang']}  {e['term'][:38]:38s}  —  ({e.get('note', '')})", file=out); continue
        vs = ", ".join(f"{v['text']} {v['limitations']}" for v in e["variants"][:3])
        print(f"  {e['lang']}  {e['term'][:38]:38s}  {'*' if e.get('house') else ' '} {e['preferred']}  "
              f"{e['support']}/{e['limitations_with_term']} ({100 * e['share']:.0f}%)" + (f"  | {vs}" if vs else ""), file=out)


def main(argv=None):
    """gleichlaut termbase [--hist DIR] [--date YYYYMMDD] [--json OUT] [--tbx OUT] [--house OUT] [--from JSON] [--quiet]
    Mining from a snapshot also writes the house sentences (gleichlaut.house) of the same snapshot."""
    ap = argparse.ArgumentParser(prog="gleichlaut termbase", description="mine BAG's house FR/IT renderings of recurring German "
                                 "limitation terms from one SL snapshot (no model); write the termbase JSON and a TBX-Basic file")
    ap.add_argument("--hist", help="snapshot dir (default: $GLEICHLAUT_HIST or track_2b/out/hist)")
    ap.add_argument("--date", default=DATE, help=f"snapshot date YYYYMMDD (default {DATE})")
    ap.add_argument("--json", help="termbase JSON to write (default data/termbase/termbase_<date>.json)")
    ap.add_argument("--tbx", help="TBX file to write (default data/termbase/gleichlaut_sl_termbase_<date>.tbx)")
    ap.add_argument("--house", help="house-sentence JSON to write (default data/termbase/house_sentences_<date>.json); the "
                    "shared-word list (shared_words_<date>.json) goes next to the termbase JSON")
    ap.add_argument("--from", dest="src", help="no mining: export the TBX from this termbase JSON (e.g. the shipped one)")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args(argv)
    jp = a.json or os.path.join(DEST, f"termbase_{a.date}.json"); tp = a.tbx or os.path.join(DEST, f"gleichlaut_sl_termbase_{a.date}.tbx")
    if a.src:
        tb = json.load(open(a.src, encoding="utf-8"))
        if a.json: write_json(tb, jp)
    else:
        from .sl import hist_dir
        from . import audit
        H = hist_dir(a.hist)
        if not os.path.exists(os.path.join(H, f"{a.date}-de.json")):
            print(f"termbase: no snapshot {a.date} in {H} (python -m gleichlaut.sl.ingest {a.date}, or export the shipped "
                  f"termbase with --from {os.path.relpath(JSON, os.getcwd())})", file=sys.stderr)
            return 2
        J, _ = audit.load(H, a.date)
        tb = mine(J, a.date); write_json(tb, jp)
        from . import house
        hp = house.write_json(house.mine(J, a.date), a.house or os.path.join(DEST, f"house_sentences_{a.date}.json"))
        write_json(shared_words(J, a.date), os.path.join(os.path.dirname(os.path.abspath(jp)), f"shared_words_{a.date}.json"))
    write_tbx(tb, tp)
    if not a.quiet:
        table(tb)
        h = sum(1 for e in tb["entries"] if e.get("house"))
        print(f"termbase {tb['meta']['date']}: {h} house renderings ({len(tb['entries'])} term x language entries)"
              + ("" if a.src and not a.json else f" -> {jp}") + f"; TBX -> {tp} (valid)" + ("" if a.src else f"; house sentences -> {hp}"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
