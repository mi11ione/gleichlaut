"""rules+ : the strongest no-model baseline we could write in an afternoon, to measure what Apertus adds beyond copying.

Written once, before it was scored (prompted by a juror who built a similar ~30-line baseline):
  1. the frozen rules lane (core.gl2.rules): number, month and all-caps-name substitutions;
  2. copy: every German replace whose old span occurs verbatim exactly once in the old target (drug names, codes,
     abbreviations) is replaced by the new German span, as-is;
  3. delete: a German deletion that removes a whole sentence deletes the target sentence at the same position, when
     German and target have the same number of sentences;
  4. insert: a German insertion made only of copyable tokens (capitalised names, codes, numbers, all-caps) is inserted
     after the target occurrence of the German anchor token, when that anchor occurs exactly once in the target.
Everything else stays as in the old target. No model, no glossary."""
import re
from . import core

lock, gl2 = core.lock, core.gl2
SENT = re.compile(r"(?<=[.;:])\s+(?=[A-ZÄÖÜÀ-Ý«\"(])")


def sentences(s): return [p for p in SENT.split(s) if p.strip()]


def copyable(tokens):
    return bool(tokens) and all(re.match(r"^(\d[\d.,']*|[A-ZÄÖÜ][\w\-]*|[A-Z0-9\-]{2,}|[().,;:/%-])$", t) for t in tokens)


def rules_plus(x):
    de_old, de_new, tgt, lang = x["de_old"], x["de_new"], x["tgt_old"], x["lang"]
    out, _ = gl2.rules(de_old, de_new, tgt, lang)
    a, b, ops = lock.de_ops(de_old, de_new)
    for op, i1, i2, j1, j2 in ops:
        old, new = " ".join(a[i1:i2]), " ".join(b[j1:j2])
        if op == "replace" and old and re.search(r"\w", old):
            pat = re.compile(r"(?<!\w)" + r"\s*".join(map(re.escape, a[i1:i2])) + r"(?!\w)")
            if len(pat.findall(out)) == 1: out = pat.sub(lambda m: new, out, count=1)
        elif op == "delete":
            ds, ts = sentences(de_old), sentences(out)
            if len(ds) == len(ts):
                for k, sent in enumerate(ds):
                    if lock.tok(sent) == a[i1:i2]: out = " ".join(t for n, t in enumerate(ts) if n != k); break
        elif op == "insert" and copyable(b[j1:j2]) and i1 > 0:
            anchor = a[i1 - 1]
            pat = re.compile(r"(?<!\w)" + re.escape(anchor) + r"(?!\w)")
            if len(pat.findall(out)) == 1: out = pat.sub(lambda m: m.group(0) + " " + new, out, count=1)
    return re.sub(r"\s+([.,;:)])", r"\1", re.sub(r"\s{2,}", " ", out)).strip()
