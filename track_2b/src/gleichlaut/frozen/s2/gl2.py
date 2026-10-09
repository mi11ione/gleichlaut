"""Gleichlaut S2 shared logic (stdlib only; used by s2.py on the Air and by score2.py locally).
rules():  arm 1 - copy old FR/IT, apply number/date/all-caps-name substitutions read off the DE diff (partial: whatever applies).
plan():   arm 2 - rule ops applied by code; every other DE op is a model op; its lock window (lock.windows, unchanged from
          Gleichschritt) is merged with overlapping ones; the model writes only the text of each merged window.
slots:    every number (digits) and German number word is shown to the model as a slot code ⟨A⟩, ⟨B⟩ ...; the model cannot
          emit digits (logit mask) and code writes the values back."""
import re, unicodedata
from collections import Counter
import lock
from lock import tok, tok_spans, de_ops, ISNUM, MONTHS

NUMW = {"de": "null eins zwei drei vier fünf sechs sieben acht neun zehn elf zwölf".split(),
        "fr": "zéro un deux trois quatre cinq six sept huit neuf dix onze douze".split(),
        "it": "zero uno due tre quattro cinque sei sette otto nove dieci undici dodici".split()}
# number words the model must not write (logit-banned as whole words). Exactly the words that mask() turns into slots, so an
# unchanged "deux" in the context is copied as its slot code. 'un/une/uno/una' are articles and stay allowed; 'cent/cento' stay
# allowed ("pour cent", "per cento").
BANWORDS = {L: set(NUMW[L][2:]) for L in ("fr", "it")}
CAPS = re.compile(r"^[A-ZÄÖÜ][A-ZÄÖÜ0-9\-]{2,}$")


def is_sub_token(x, y):
    return (ISNUM.match(x) and ISNUM.match(y)) or (x in MONTHS["de"] and y in MONTHS["de"]) or (CAPS.match(x) and CAPS.match(y))


def op_subs(a, b, op, lang):
    """1:1 substitutions for a replace op whose differing tokens are all numbers / months / ALLCAPS names; else None."""
    o, i1, i2, j1, j2 = op
    if o != "replace" or (i2 - i1) != (j2 - j1): return None
    subs = []
    for x, y in zip(a[i1:i2], b[j1:j2]):
        if x == y: continue
        if not is_sub_token(x, y): return None
        if x in MONTHS["de"]: subs.append((MONTHS[lang][MONTHS["de"].index(x)], MONTHS[lang][MONTHS["de"].index(y)]))
        else: subs.append((x, y))
    return subs


def apply_sub(text, x, y, cnt_de):
    pat = re.compile(r"(?<![\w.,'’])" + re.escape(x) + r"(?![\w]|[.,'’]\d)")
    hits = len(pat.findall(text))
    if hits == 0 or (hits != 1 and not (ISNUM.match(x) and hits == cnt_de)): return text, False
    return pat.sub(y, text), True


def rules(de_old, de_new, tgt_old, lang):
    """arm 1. Also handles number swaps inside larger replace ops (equal count of numbers on both sides)."""
    a, b, ops = de_ops(de_old, de_new)
    cnt = Counter(a); out = tgt_old; done = []
    for op in ops:
        s = op_subs(a, b, op, lang)
        if s is None:
            o, i1, i2, j1, j2 = op
            on = [x for x in a[i1:i2] if ISNUM.match(x)]; nn = [y for y in b[j1:j2] if ISNUM.match(y)]
            s = [(x, y) for x, y in zip(on, nn) if x != y] if len(on) == len(nn) else []
        for x, y in s:
            out, ok = apply_sub(out, x, y, cnt[x]); done.append((x, y, ok))
    return out, done


def merge(W):
    W = sorted(W); out = []
    for lo, hi in W:
        if out and lo <= out[-1][1]: out[-1] = (out[-1][0], max(out[-1][1], hi))
        else: out.append((lo, hi))
    return out


def plan(de_old, de_new, tgt_old, lang):
    """-> dict(base, windows=[(lo,hi)] in base tokens (model ops only, merged), ops_per_window, rule_only, n_ops)."""
    a, b, ops = de_ops(de_old, de_new)
    W, t = lock.windows(de_old, de_new, tgt_old)
    cnt = Counter(a); base = tgt_old; model_w = []; model_ops = []
    for op, w in zip(ops, W):
        s = op_subs(a, b, op, lang)
        ok = s is not None
        if ok:
            trial = base
            for x, y in s:
                trial, hit = apply_sub(trial, x, y, cnt[x]); ok = ok and hit
            if ok and len(tok(trial)) == len(t): base = trial
            else: ok = False
        if not ok: model_w.append(w); model_ops.append((op, w))
    MW = merge(model_w)
    opw = [[o for o, w in model_ops if not (w[1] < lo or w[0] > hi)] for lo, hi in MW]
    return dict(base=base, windows=MW, ops_per_window=opw, rule_only=not MW, n_ops=len(ops))


def char_span(text, lo, hi):
    sp = tok_spans(text)
    if lo < hi: return sp[lo][1], sp[hi - 1][2]
    pos = sp[lo][1] if lo < len(sp) else len(text)
    return pos, pos


def stitch(text, lo, hi, repl):
    s, e = char_span(text, lo, hi)
    repl = repl.strip()
    left, right = text[:s], text[e:]
    if not repl:
        out = left.rstrip() + (" " if right[:1].isalnum() or right[:1] in "(«" else "") + right.lstrip()
    else:
        if left and not left[-1].isspace() and lo == hi: repl = " " + repl
        if right and not right[0].isspace() and lo == hi and right[0].isalnum(): repl = repl + " "
        out = left + repl + right
    return re.sub(r"  +", " ", out).strip()


def changes_list(a, b, ops):
    out = []
    for op, i1, i2, j1, j2 in ops:
        o, n = " ".join(a[i1:i2]), " ".join(b[j1:j2]); ctx = " ".join(a[max(0, i1 - 3):i1])
        if op == "replace": out.append(f"- replace «{o}» with «{n}»")
        elif op == "delete": out.append(f"- delete «{o}»")
        else: out.append(f"- insert «{n}» after «{ctx}»")
    return "\n".join(out)


# ------------------------------------------------------------ number slots
NUMRX = re.compile(r"\d+(?:[.,'’]\d+)*")
LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def nval(s):
    return re.sub(r"[ '’]", "", s).replace(",", ".")


class Slots:
    """Slot codes ⟨A⟩, ⟨B⟩ ... One code per (form, value): digits ('d', '1.8') keep their surface; number words ('w', 2) are
    written back as the number word of the output language (DE 'zwei' and FR 'deux' share a code)."""
    def __init__(self, tgt_old):
        self.code, self.surf, self.tgt_seen = {}, {}, set()

    def _c(self, key, surface, from_tgt=False):
        if key in self.code and from_tgt and key not in self.tgt_seen:  # the target's own surface form wins
            self.surf[self.code[key]] = surface
        if from_tgt: self.tgt_seen.add(key)
        if key not in self.code:
            i = len(self.code); self.code[key] = "⟨" + (LETTERS[i] if i < 26 else LETTERS[i // 26 - 1] + LETTERS[i % 26]) + "⟩"
            self.surf[self.code[key]] = surface
        return self.code[key]

    def mask(self, s, lang):
        def num(m):
            sf = m.group(0)
            return self._c(("d", nval(sf)), sf, lang != "de")
        s = NUMRX.sub(num, s)
        words = NUMW[lang][2:]
        def w(m):
            i = [x.lower() for x in NUMW[lang]].index(m.group(0).lower())
            return self._c(("w", i), {"w": i}, lang != "de")
        return re.sub(r"\b(?:" + "|".join(words) + r")\b", w, s, flags=re.I)

    def unmask(self, s, lang):
        def f(m):
            v = self.surf.get(m.group(0))
            if v is None: return m.group(0)
            if isinstance(v, dict): return NUMW[lang][v["w"]]
            return v
        return re.sub(r"⟨[A-Z]{1,2}⟩", f, s)


def numbers_in(s, lang):
    """normalised numeric values in a text: digits + spelled number words (2..12 and tens)."""
    vals = Counter(nval(m.group(0)) for m in NUMRX.finditer(s))
    low = s.lower()
    for i, w in enumerate(NUMW[lang]):
        if i >= 2:
            for _ in re.finditer(r"\b" + w + r"\b", low): vals[str(i)] += 1
    return vals


def numbers_not_in_de(out, de_new, lang):
    """count of numeric values in the output that the new German text does not contain (as digits or number words)."""
    de = set(numbers_in(de_new, "de")); o = numbers_in(out, lang)
    return sum(c for v, c in o.items() if v not in de), sorted(v for v in o if v not in de)
