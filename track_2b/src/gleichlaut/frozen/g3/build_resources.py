"""Resources for guards3 (the coordinator's 'guard v2'). Mechanical, no hand-picked entries.
whitelist_{fr,it}: lowercased word tokens (>= 3 letters) of (a) the target-language productName entries, (b) Ingredient substance
   names (Latin INNs), (c) the target-language ATC display names - all from the current BAG ePL FHIR feed (data/sl-*.ndjson).
vocab_{fr,it}: token -> number of distinct limitation texts containing it, over the FR/IT limitation texts of the 1 Jun 2025
   XMLPublications capture. (Chosen because it predates every new text of the dev set (2026) and of the fresh test set
   (Jul 2025 / Feb 2026): no gold text can leak into the guard.)
terms_{fr,it}: DE->FR/IT abbreviation map mined from the aligned DE/FR/IT limitation triples of the same 1 Jun 2025 capture:
   per triple, abbreviations (A-Z start, 2-6 upper-case letters/digits, optional -suffix) present in DE but not in the target
   text (D) and present in the target but not in DE (T); if |D| == |T| >= 1 they are paired in order of first appearance.
   Kept: pairs seen >= 2 times that account for >= 60% of the DE abbreviation's pairings, with A != B, and A itself used in
   fewer than 5 target-language texts (an abbreviation that is normal in the target language is not a translation error).
usage: python3 -I build_resources.py"""
import json, os, re, sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
H = os.path.dirname(os.path.abspath(__file__)); G = "/Users/mi11ion/Desktop/hackapertus/spikes/gleichlaut"
sys.path.insert(0, f"{G}/s2"); sys.path.insert(0, os.path.join(os.path.dirname(H), "fresh"))
from mine import nrm
WORD = re.compile(r"[^\W\d_]+")
ABBR = re.compile(r"\b[A-Z][A-Z0-9]{1,5}(?:-[A-Z0-9]{1,4})?\b")
LCODE = {"fr": "fr-CH", "it": "it-CH"}
TAGS = re.compile(r"</?(?:br|p|ul|ol|li|div)\b[^<>]*>", re.I); INLINE = re.compile(r"</?(?:b|i|u|strong|em|sup|sub|span|font)\b[^<>]*>", re.I)
untag = lambda s: TAGS.sub(" ", INLINE.sub("", nrm(s)))

# whitelists from the FHIR feed
for L in ("fr", "it"):
    W = set()
    with open(f"{G}/data/sl-{L}.ndjson") as f:
        for line in f:
            if not line.strip(): continue
            for e in json.loads(line).get("entry", []):
                r = e["resource"]; rt = r["resourceType"]
                if rt == "MedicinalProductDefinition":
                    for n in r.get("name", []):
                        langs = [c.get("code") for u in n.get("usage", []) for c in (u.get("language") or {}).get("coding", [])]
                        if LCODE[L] in langs: W.update(w.lower() for w in WORD.findall(n.get("productName") or "") if len(w) >= 3)
                    for c in r.get("classification", []):
                        for cd in c.get("coding", []):
                            if "atc" in cd.get("system", ""): W.update(w.lower() for w in WORD.findall(cd.get("display") or "") if len(w) >= 3)
                elif rt == "Ingredient":
                    t = ((r.get("substance") or {}).get("code") or {}).get("concept", {}).get("text") or ""
                    W.update(w.lower() for w in WORD.findall(t) if len(w) >= 3)
    json.dump(sorted(W), open(f"{H}/whitelist_{L}.json", "w"), ensure_ascii=False)
    print("whitelist", L, len(W))

# vocab + abbreviation map from the aligned 1 Jun 2025 XML
triples = set()
for _, el in ET.iterparse(f"{G}/data/wb2025/20250611/Preparations.xml", events=("end",)):
    if el.tag == "Limitation":
        triples.add(tuple(untag(el.findtext(f"Description{x}") or "") for x in ("De", "Fr", "It")))
    if el.tag == "Preparation": el.clear()
print("distinct limitation triples", len(triples))
for li, L in ((1, "fr"), (2, "it")):
    V = Counter(); P = defaultdict(Counter); AT = Counter()
    for t in triples:
        V.update({w.lower() for w in WORD.findall(t[li])}); AT.update(set(ABBR.findall(t[li])))
        de, tg = t[0], t[li]
        if not de or not tg: continue
        ad, at = ABBR.findall(de), ABBR.findall(tg)
        D = [a for a in dict.fromkeys(ad) if a not in set(at)]; T = [a for a in dict.fromkeys(at) if a not in set(ad)]
        if D and len(D) == len(T):
            for a, b in zip(D, T): P[a][b] += 1
    terms = {a: c.most_common(1)[0][0] for a, c in P.items()
             if c.most_common(1)[0][1] >= 2 and c.most_common(1)[0][1] / sum(c.values()) >= 0.6 and c.most_common(1)[0][0] != a and AT[a] < 5}
    json.dump(dict(V), open(f"{H}/vocab_{L}.json", "w"), ensure_ascii=False)
    json.dump(dict(sorted(terms.items())), open(f"{H}/terms_{L}.json", "w"), ensure_ascii=False, indent=0)
    print("vocab", L, len(V), "terms", L, len(terms), {k: terms[k] for k in list(sorted(terms))[:40]})
