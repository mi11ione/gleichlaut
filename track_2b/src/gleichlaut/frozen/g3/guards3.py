"""guards3 = the coordinator's 'guard v2': the frozen gl/guards.py stack (V2 = True: G1 German function words/umlaut/-ung,
G2 proportional stale, G3a outside-window survival, G3c unjustified removal, G4 duplication) PLUS three untranslated detectors:
 G5 copied-from-DE: a token the output adds (vs the old FR/IT, case-insensitive) that also occurs in the new DE text, is not on the
    target-language product/substance/ATC whitelist, and occurs in fewer than VMIN target-language limitation texts (vocab).
 G6 terminology: the output adds a DE abbreviation A for which the mined DE->FR/IT map gives B != A ("A -> B").
 G7 out-of-vocabulary: the output adds a word of >= 4 letters that occurs in no target-language limitation text (vocab), is not
    whitelisted and is not in the old FR/IT text (catches Germanised hybrids and imported fragments).
Resources (build_resources.py): whitelist_{fr,it}.json, vocab_{fr,it}.json, terms_{fr,it}.json. G5-G7 findings are also appended
to 'g1' so that reask.py's complaint text names them ("German words that must be in <L>")."""
import json, os, re, sys
from collections import Counter
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(os.path.dirname(H), "gl"))
import guards
guards.V2 = True
from lock import tok, norm
VMIN = 5
WL = {L: set(json.load(open(f"{H}/whitelist_{L}.json"))) for L in ("fr", "it")}
VOC = {L: json.load(open(f"{H}/vocab_{L}.json")) for L in ("fr", "it")}
TERMS = {L: json.load(open(f"{H}/terms_{L}.json")) for L in ("fr", "it")}
WORD = re.compile(r"^[^\W\d_]+$")


def added(old, out):
    o = Counter(t.lower() for t in tok(norm(old))); n = Counter(t.lower() for t in tok(norm(out)))
    return set(n - o)


def added_cs(old, out):
    return set(Counter(tok(norm(out))) - Counter(tok(norm(old))))


def extra(x, out):
    L = x["lang"]; A = added(x["tgt_old"], out); de = {t.lower() for t in tok(x["de_new"])}
    oldw = {t.lower() for t in tok(x["tgt_old"])}
    g5 = sorted(t for t in A if WORD.match(t) and len(t) >= 2 and t in de and t not in WL[L] and VOC[L].get(t, 0) < VMIN)
    g6 = sorted(f"{a} -> {TERMS[L][a]}" for a in added_cs(x["tgt_old"], out) if a in TERMS[L])
    g7 = sorted(t for t in A if WORD.match(t) and len(t) >= 4 and VOC[L].get(t, 0) == 0 and t not in WL[L] and t not in oldw)
    return g5, g6, g7


def run(x, out):
    r = guards.run(x, out); g5, g6, g7 = extra(x, out)
    r.update(g5=g5, g6=g6, g7=g7)
    r["g1"] = list(r["g1"]) + [t for t in g5 + g7 if t not in r["g1"]] + g6
    r["flag"] = bool(r["flag"] or g5 or g6 or g7)
    return r
