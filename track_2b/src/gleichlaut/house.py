"""House sentences: BAG's dominant French and Italian wording of frequent fixed German sentences ("Folgender Indikationscode
ist an den Krankenversicherer zu übermitteln:"), mined from the register. Deterministic, stdlib, no model, no network.

Mined with the termbase's method (gleichlaut.termbase, docs/termbase.md) from the same snapshot (the 1,688 limitations of the
6 Oct 2026 feed, aligned DE/FR/IT by id as audit.load aligns them; a target field written in another language is skipped):

  S1 units: every limitation's German and target text cut into the aligned sentence beads of emit.segment.align (the XLIFF
     segmentation). A bead's German side is the German sentence.
  S2 normalisation (key()): NBSP and other spaces as one space, typographic apostrophes as ', every number or code
     (21150.07, 20481.XX's digits, 1.5) as '#', no space before : ; ! ? » ) ] , . and none after « ( [. The German key needs
     at least MIN_WORDS words of two letters or more (a lone code number is not a sentence).
  S3 support: a German key is recorded when it is in >= MIN_SUPPORT limitations. Its renderings are the normalised target
     sides of its beads, counted in limitations.
  S4 house rendering: the most frequent rendering when it is in >= MIN_SUPPORT limitations and in > MIN_SHARE of the
     limitations with the German key (the termbase's M6); otherwise the entry says 'no dominant rendering' and is not used.
  S5 variants: the other renderings in >= VAR_MIN limitations, most frequent first, at most MAX_VARIANTS, with counts.
No rendering is written by hand: every wording shown is one BAG published, with its count.

Output: data/termbase/house_sentences_<date>.json (not in the TBX: a sentence with a number slot is translation-memory
material, not a term of a concept entry).

Advisory (presentation only; emit/xliff.py and the review page): for a draft whose new German has a sentence with a house
rendering, aligned (emit.segment.align) to a draft sentence that is recognisably the same formula (character similarity
>= SIMILAR after normalisation) but not the house wording, one low-priority note in the reviewer's language naming the
house wording and its support: "Phrase maison pour « … » : « … » (n limitations) ; le brouillon écrit « … »". Only for a
sentence the draft inserted or rewrote: a sentence carried over unchanged from the old text is left alone (the German did
not change it, the checks keep edits inside the change, and BAG's own amendments leave such sentences as they are). A
sentence the draft does not translate at all is the checks' business (change applied), not this note's. It never changes
a verdict, a draft or a score; measured in eval/results/explain_v3.json (emit.explain.measure_v3())."""
import argparse, difflib, json, os, re, sys
from collections import Counter, defaultdict
from . import core

DATE = "20261006"
DEST = os.path.join(core.ROOT, "data", "termbase")
JSON = os.path.join(DEST, f"house_sentences_{DATE}.json")
LANGS = ("fr", "it")
MIN_SUPPORT, MIN_SHARE, MIN_WORDS, VAR_MIN, MAX_VARIANTS = 10, 0.5, 3, 2, 5
SIMILAR = 0.6          # a draft sentence at least this similar to the house wording is the same formula, written otherwise
NUM = re.compile(r"\d+(?:[.,'’]\d+)*")
WORD = re.compile(r"[^\W\d_]{2,}")


def _nrm(t):
    from .sl.ingest import nrm
    return nrm(t or "").replace("’", "'").replace("ʼ", "'")


def key(s):
    """S2: the normalised form of a sentence (numbers and codes as '#', spacing around punctuation dropped)."""
    s = NUM.sub("#", _nrm(s))
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"\s+([:;!?»)\],.])", r"\1", s)
    return re.sub(r"([«(\[])\s+", r"\1", s)


def display(s):
    """a published sentence as shown in a note: whitespace collapsed, numbers and codes as '…'."""
    return re.sub(r"\s+", " ", NUM.sub("…", _nrm(s))).strip()


# ------------------------------------------------------------------------------------------------------- mining
def mine(J, date=DATE):
    """-> dict(meta, entries) from one aligned snapshot J (audit.load)."""
    from .emit.segment import align
    from .termbase import _lang_ok
    entries = []
    for L in LANGS:
        lims = [i for i in sorted(J["de"]["lim"]) if J[L]["lim"].get(i) and J["de"]["lim"][i] and _lang_ok(J[L]["lim"][i], L)]
        R = defaultdict(lambda: defaultdict(set)); surf = defaultdict(Counter); dsurf = defaultdict(Counter)
        for i in lims:
            de, tg = _nrm(J["de"]["lim"][i]), _nrm(J[L]["lim"][i])
            for a0, a1, b0, b1 in align(de, tg):
                g = key(de[a0:a1])
                if len(WORD.findall(g)) < MIN_WORDS: continue
                t = key(tg[b0:b1]); R[g][t].add(i)
                surf[(g, t)][display(tg[b0:b1])] += 1; dsurf[g][display(de[a0:a1])] += 1
        for g, T in R.items():
            n = len(set().union(*T.values()))
            if n < MIN_SUPPORT: continue
            ranked = sorted(T.items(), key=lambda kv: (-len(kv[1]), kv[0]))
            best, has = ranked[0]
            text = lambda t: sorted(surf[(g, t)].items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
            e = dict(lang=L, de=g, de_text=sorted(dsurf[g].items(), key=lambda kv: (-kv[1], kv[0]))[0][0], limitations=n,
                     rendering=best, text=text(best), support=len(has), share=round(len(has) / n, 3),
                     variants=[dict(key=t, text=text(t), limitations=len(s)) for t, s in ranked[1:] if len(s) >= VAR_MIN][:MAX_VARIANTS])
            e["house"] = e["support"] >= MIN_SUPPORT and e["share"] > MIN_SHARE
            if not e["house"]: e["note"] = f"no dominant rendering (share {e['share']:.2f} not above {MIN_SHARE})"
            entries.append(e)
    entries.sort(key=lambda e: (e["lang"], -e["limitations"], e["de"]))
    from .termbase import _d
    meta = dict(generated_by=f"gleichlaut termbase --date {date}", date=date, source=f"BAG Spezialitätenliste, public ePL FHIR feed {_d(date)}",
                limitations=len(J["de"]["lim"]), unit="aligned sentence bead (emit.segment.align); German side = the sentence",
                rules=dict(min_support=MIN_SUPPORT, min_share=MIN_SHARE, min_words=MIN_WORDS, variant_min=VAR_MIN,
                           max_variants=MAX_VARIANTS),
                normalisation="numbers and codes as '#', whitespace collapsed, typographic apostrophes as ', no space before "
                              ": ; ! ? » ) ] , . or after « ( [",
                note="Mined from the register itself (gleichlaut.house, docs/termbase.md). Counts are limitations; 'share' = "
                     "support / limitations whose German has the sentence. house=false: no dominant rendering, not used.")
    return dict(meta=meta, entries=entries)


def write_json(d, path=JSON):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh: json.dump(d, fh, ensure_ascii=False, indent=1); fh.write("\n")
    return path


# ------------------------------------------------------------------------------------------------------- advisory
_H = {}


def load(path=JSON):
    """-> {(lang, German key): entry} of the house sentences (house=true), {} when the file is absent."""
    if path not in _H:
        try:
            d = json.load(open(path, encoding="utf-8"))
            _H[path] = {(e["lang"], e["de"]): e for e in d["entries"] if e.get("house")}
        except (OSError, ValueError, KeyError):
            _H[path] = {}
    return _H[path]


def _sentence_keys(text):
    from .emit.segment import sentences
    t = _nrm(text)
    return {key(t[a:b]) for a, b in sentences(t)}


def advice(v, hs=None, carried=False):
    """-> [dict(de, house, support, wrote, kind, variant, sim, key, mine)] for one draft view (lang, de_new, tgt_old, draft):
    one item per draft sentence aligned to a German house sentence that departs from the house wording, in a sentence the
    draft inserted or rewrote (kind "departs"). A sentence the draft carries over unchanged from the old text (kind "kept")
    is left alone: the German did not change it, and the checks keep edits inside the change (carried=True lists them, for
    the measurement only). variant: how many limitations BAG wrote the draft's wording in, when it is one of the recorded
    variants (else None)."""
    L = v.get("lang"); draft = v.get("draft") or ""
    if L not in LANGS or not draft or v.get("status") == "human": return []
    H = load() if hs is None else hs
    if not H: return []
    from .emit.segment import align
    de, dr = _nrm(v.get("de_new")), _nrm(draft)
    old = _sentence_keys(v.get("tgt_old") or "")
    out = []
    for a0, a1, b0, b1 in align(de, dr):
        e = H.get((L, key(de[a0:a1])))
        if not e: continue
        k = key(dr[b0:b1])
        if k == e["rendering"]: continue
        sim = difflib.SequenceMatcher(None, k, e["rendering"], autojunk=False).ratio()
        if sim < SIMILAR: continue
        var = next((x["limitations"] for x in e["variants"] if x["key"] == k), None)
        kept = _sentence_keys(dr[b0:b1]) <= old
        if kept and not carried: continue
        out.append(dict(de=e["de_text"], house=e["text"], support=e["support"], wrote=display(dr[b0:b1]), mine=k,
                        kind="kept" if kept else "departs", variant=var,
                        sim=round(sim, 3), key=e["de"]))
    return out


NOTE = {"fr": dict(head="Phrase maison pour {de} : {house} ({n} limitations)", wrote="le brouillon écrit {x}",
                   var=" (variante publiée dans {k} limitations)", var_1=" (variante publiée dans 1 limitation)"),
        "it": dict(head="Frase in uso all'UFSP per {de}: {house} ({n} limitazioni)", wrote="la bozza scrive {x}",
                   var=" (variante pubblicata in {k} limitazioni)", var_1=" (variante pubblicata in 1 limitazione)")}
GIST = 140             # a sentence longer than this is shown as the part that differs, with two words around it


def _q(L, s): return f"« {s} »" if L == "fr" else f"«{s}»"


def gist(a, b, n=GIST):
    """(a shown, b shown): the whole sentences when both are short, else the span where they differ with two words of
    context on each side ('… transmis à l'assurance-maladie : …' / '… transmis à l'assureur-maladie : …')."""
    if len(a) <= n and len(b) <= n: return a, b
    sp = lambda t: re.sub(r"([«(\[])\s+", r"\1", re.sub(r"\s+([:;!?»)\]])", r"\1", t))     # spacing is not the difference
    A, B = sp(a).split(" "), sp(b).split(" ")
    ops = [o for o in difflib.SequenceMatcher(None, A, B, autojunk=False).get_opcodes() if o[0] != "equal"]
    if not ops: return a, b
    i1, j1 = max(0, ops[0][1] - 2), max(0, ops[0][3] - 2); i2, j2 = min(len(A), ops[-1][2] + 2), min(len(B), ops[-1][4] + 2)
    cut = lambda W, x, y: ("… " if x > 0 else "") + " ".join(W[x:y]) + (" …" if y < len(W) else "")
    return cut(A, i1, i2), cut(B, j1, j2)


def advisory_text(A, L):
    """one low-priority note in the reviewer's language, or None: per house sentence (at most two), the house wording with
    its support and what the draft writes there (the differing part with two words around it when the sentence is long)."""
    A = [a for a in A or [] if a["kind"] != "kept"]
    if not A or L not in NOTE: return None
    N = NOTE[L]; parts = []
    for a in A[:2]:
        w, h = gist(a["wrote"], a["house"])
        de = a["de"] if len(a["de"]) <= 100 else a["de"][:100].rsplit(" ", 1)[0] + " …"
        s = N["head"].format(de=_q(L, de), house=_q(L, h), n=a["support"]) + (" ; " if L == "fr" else "; ")
        s += N["wrote"].format(x=_q(L, w))
        if a.get("variant"): s += N["var_1" if a["variant"] == 1 else "var"].format(k=a["variant"])
        parts.append(s + ".")
    return " ".join(parts)


# ------------------------------------------------------------------------------------------------------- measurement
SHADOW = ("shadow/20260901-20261001", ("q4_k_m", "q8_0", "70b"))


def bag_sentence(x, gkey):
    """BAG's published sentence (tgt_new, evaluation data) aligned to the German house sentence gkey, as a key, or None."""
    from .emit.segment import align
    if not x.get("tgt_new"): return None
    de, tg = _nrm(x["de_new"]), _nrm(x["tgt_new"])
    return next((key(tg[b0:b1]) for a0, a1, b0, b1 in align(de, tg) if key(de[a0:a1]) == gkey), None)


def measure_views(views, items):
    """-> counts for one run: drafts, drafts with a house-sentence note (ready / flagged), notes, and, per note, BAG's
    published sentence of the same amendment at that German sentence (evaluation data, never shown): differs from the
    draft's, is the house wording, is the draft's wording, or unknown (no published text / not aligned). carried_*: the
    departing sentences the draft carries over unchanged (no note), and how often BAG's published text keeps them too."""
    row = dict(drafts=0, drafts_with_note=0, ready_with_note=0, flagged_with_note=0, notes=0, notes_variant=0,
               bag_differs_from_draft=0, bag_writes_house=0, bag_same_as_draft=0, bag_unknown=0,
               drafts_with_note_bag_differs=0, keys=[], by_sentence=Counter(),
               carried_not_noted=0, carried_bag_same_as_draft=0, carried_bag_writes_house=0)
    for v in views:
        if v["status"] == "human": continue
        row["drafts"] += 1
        for a in advice(v, carried=True):              # carried over unchanged: no note; what BAG published there
            if a["kind"] != "kept": continue
            row["carried_not_noted"] += 1; b = bag_sentence(items[v["key"]], a["key"])
            row["carried_bag_same_as_draft"] += b == a["mine"]; row["carried_bag_writes_house"] += b == load()[(v["lang"], a["key"])]["rendering"]
        A = v.get("house")
        if A is None: A = advice(v)
        if not A: continue
        row["drafts_with_note"] += 1; row["ready_with_note" if v["status"] == "ready" else "flagged_with_note"] += 1
        row["keys"].append(v["key"]); x = items[v["key"]]; differs = False
        for a in A:
            row["notes"] += 1; row["notes_variant"] += bool(a.get("variant"))
            row["by_sentence"][f"{v['lang']}: {a['de'][:60]}"] += 1
            b = bag_sentence(x, a["key"])
            if b is None: row["bag_unknown"] += 1; continue
            e = load()[(v["lang"], a["key"])]
            row["bag_writes_house"] += b == e["rendering"]; row["bag_same_as_draft"] += b == a["mine"]
            if b != a["mine"]: row["bag_differs_from_draft"] += 1; differs = True
        row["drafts_with_note_bag_differs"] += differs
    row["by_sentence"] = dict(sorted(row["by_sentence"].items()))
    return row


# ------------------------------------------------------------------------------------------------------- CLI
def table(d, out=sys.stdout):
    for e in d["entries"]:
        vs = "; ".join(f"{x['text'][:50]} {x['limitations']}" for x in e["variants"][:2])
        print(f"  {e['lang']} {'*' if e['house'] else ' '} {e['support']:3d}/{e['limitations']:3d} {e['de_text'][:60]:60s} -> "
              f"{e['text'][:70]}" + (f"  | {vs}" if vs else ""), file=out)


def main(argv=None):
    """python -m gleichlaut.house [--hist DIR] [--date YYYYMMDD] [--json OUT] [--quiet] (also run by `gleichlaut termbase`)"""
    ap = argparse.ArgumentParser(prog="gleichlaut.house", description="mine BAG's house FR/IT wording of frequent fixed German "
                                 "sentences from one SL snapshot (no model)")
    ap.add_argument("--hist"); ap.add_argument("--date", default=DATE); ap.add_argument("--json"); ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args(argv)
    from .sl import hist_dir
    from . import audit
    H = hist_dir(a.hist)
    if not os.path.exists(os.path.join(H, f"{a.date}-de.json")):
        print(f"house: no snapshot {a.date} in {H}", file=sys.stderr); return 2
    J, _ = audit.load(H, a.date); d = mine(J, a.date)
    p = write_json(d, a.json or os.path.join(DEST, f"house_sentences_{a.date}.json"))
    if not a.quiet:
        table(d); print(f"house sentences {a.date}: {sum(e['house'] for e in d['entries'])} with a house rendering "
                        f"({len(d['entries'])} German sentences in >= {MIN_SUPPORT} limitations) -> {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
