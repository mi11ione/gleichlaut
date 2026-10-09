"""Sentence segmentation and DE -> FR/IT sentence alignment for the XLIFF hand-off (one <segment> per sentence), and the
German change as character spans of the new German text (marked in the XLIFF source).

sentences(s): spans ending at . ; : ! ? followed by whitespace and an upper-case letter, digit, quote, bracket or dash
  (the trailing whitespace belongs to the sentence, so the spans cover s exactly).
align(src, tgt): a monotone alignment of source and target sentences in beads of 1:1, 1:2, 2:1, 2:2, 1:3 or 3:1 sentences,
  chosen by dynamic programming on (a) length ratio against the text's overall ratio, (b) the numbers written in digits on
  each side, (c) a fixed penalty for every bead that is not 1:1 (Gale-Church style, no model). Each bead becomes one
  segment; concatenating the segments gives back both texts exactly.
beads(src, tgt, keep): align + keep_whole + merge_short, the one segmentation every XLIFF writer and the page use.
changed(old, new): the inserted / replaced runs of the new German (the same phrase-level diff the review page shows)."""
import math, re
from .. import core

SENT_END = re.compile(r"[.;:!?](\s+)(?=[A-ZÄÖÜÀÂÉÈÊÎÔÛÇ0-9(«\"–-])")
BEADS = {(1, 1): 0.0, (1, 2): 1.2, (2, 1): 1.2, (2, 2): 1.8, (1, 3): 2.4, (3, 1): 2.4}
DIGITS = re.compile(r"\d+(?:[.,'’]\d+)*")


def sentences(s):
    """-> [(start, end)] sentence spans covering s (the trailing space belongs to the sentence)."""
    out, a = [], 0
    for m in SENT_END.finditer(s):
        out.append((a, m.end(1))); a = m.end(1)
    if a < len(s) or not out: out.append((a, len(s)))
    return out


def _nums(s): return {re.sub(r"[.,'’]", ".", m.group(0)) for m in DIGITS.finditer(s)}


def align(src, tgt):
    """-> [(a0, a1, b0, b1)]: source span, target span per segment, in order, covering both texts."""
    S, T = sentences(src), sentences(tgt)
    if not tgt.strip() or not src.strip(): return [(0, len(src), 0, len(tgt))]
    r = max(1, len(tgt)) / max(1, len(src)); INF = float("inf")
    n, m = len(S), len(T)
    best = [[INF] * (m + 1) for _ in range(n + 1)]; back = [[None] * (m + 1) for _ in range(n + 1)]
    best[0][0] = 0.0
    for i in range(n + 1):
        for j in range(m + 1):
            if best[i][j] == INF: continue
            for (di, dj), pen in BEADS.items():
                if i + di > n or j + dj > m: continue
                a0, a1, b0, b1 = S[i][0], S[i + di - 1][1], T[j][0], T[j + dj - 1][1]
                ls, lt = len(src[a0:a1].strip()), len(tgt[b0:b1].strip())
                cost = 3 * abs(math.log((lt + 1) / (r * ls + 1))) + pen + len(_nums(src[a0:a1]) ^ _nums(tgt[b0:b1]))
                if best[i][j] + cost < best[i + di][j + dj]:
                    best[i + di][j + dj] = best[i][j] + cost; back[i + di][j + dj] = (i, j)
    if best[n][m] == INF: return [(0, len(src), 0, len(tgt))]
    out, i, j = [], n, m
    while (i, j) != (0, 0):
        pi, pj = back[i][j]; out.append((S[pi][0], S[i - 1][1], T[pj][0], T[j - 1][1])); i, j = pi, pj
    return out[::-1]


def keep_whole(beads, spans, side):
    """Merge neighbouring beads so that no (start, end) span of `spans` crosses a bead boundary on `side` (0 = source,
    1 = target)."""
    out = list(beads)
    k = 0
    while k < len(out) - 1:
        cut = out[k][1] if side == 0 else out[k][3]
        if any(a < cut < b for a, b in spans):
            a, b = out[k], out[k + 1]; out[k:k + 2] = [(a[0], b[1], a[2], b[3])]
        else: k += 1
    return out


SHORT = 20            # a segment side shorter than this (stripped), or without a word of 2+ letters, is merged


def _short(t):
    t = t.strip()
    return len(t) < SHORT or not re.search(r"[^\W\d_]{2,}", t)


def merge_short(beads, src, tgt=None):
    """Merge every bead whose source (or target, when there is one) is very short into the previous bead (the first
    one into the next): a lone code number like '21658.01' after 'zu übermitteln:' never becomes its own segment."""
    out = list(beads)
    k = 0
    while len(out) > 1 and k < len(out):
        a0, a1, b0, b1 = out[k]
        if _short(src[a0:a1]) or (tgt is not None and _short(tgt[b0:b1])):
            if k == 0: n = out[1]; out[0:2] = [(a0, n[1], b0, n[3])]
            else: p = out[k - 1]; out[k - 1:k + 1] = [(p[0], a1, p[2], b1)]; k -= 1
            continue
        k += 1
    return out


def beads(src, tgt=None, keep=()):
    """The segments of one unit, used alike by XLIFF 2.1, XLIFF 1.2 and the review page's export: aligned sentence
    beads (align), merged so that no span of `keep` (target numbers) crosses a boundary (keep_whole) and no segment is
    very short (merge_short). tgt None: source sentences only (target spans (0, 0))."""
    if tgt is None: return [(a, b, 0, 0) for a, b, _, _ in merge_short([(a, b, 0, 0) for a, b in sentences(src)], src)]
    return merge_short(keep_whole(align(src, tgt), list(keep), 1), src, tgt)


def changed(old, new):
    """-> [(start, end)] spans of `new` that the German change inserted or rewrote (whitespace trimmed)."""
    from ..ui.build import diff          # the review page's diff (lazy: ui.build imports this package)
    pos, out = 0, []
    for s in diff(old, new):
        if s[0] == "d": continue
        a, b = pos, pos + len(s[1]); pos = b
        if s[0] != "i": continue
        t = new[a:b]; a += len(t) - len(t.lstrip()); b -= len(t) - len(t.rstrip())
        if a >= b: continue
        if out and out[-1][1] >= a - 1 and not new[out[-1][1]:a].strip(): out[-1] = (out[-1][0], b)
        else: out.append((a, b))
    assert pos == len(new), "diff does not rebuild the new German"
    return out


def number_spans(s):
    return [(m.start(), m.end()) for m in core.gl2.NUMRX.finditer(s)]
