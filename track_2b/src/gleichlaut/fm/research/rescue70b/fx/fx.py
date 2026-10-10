"""D. Fedlex 9+36 with the 70B: pairwise 'same meaning? Ja/Nein' (round7b PAIR['de'] prompt verbatim), DE-FR, DE-IT, FR-IT,
both orders (ab: first lang first, 'Ja oder Nein'; ba: second lang first, 'Nein oder Ja'). Generation, temperature 0.
P(differs) per pair = share of the two orders answering Nein. Localisation as in round7b: score(L) = mean of the two pairs with L
minus the third; flagged if max >= 0.5; hit = flagged and unique argmax = gold. usage: python3 -I fx.py [N]"""
import json, sys, os, re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import ask, pmap
H = os.path.dirname(os.path.abspath(__file__))
items = json.load(open("/Users/mi11ion/Desktop/hackapertus/spikes/round7/fedlex_items.json"))
if len(sys.argv) > 1: items = items[:int(sys.argv[1])]
Q = ("Unten stehen zwei Sprachfassungen ({la} und {lb}) derselben Bestimmung des schweizerischen Bundesrechts. "
     "Beide Fassungen sind gleichermassen verbindlich und sollten dasselbe bedeuten. Prüfe, ob sie inhaltlich (nicht bloss "
     "stilistisch) übereinstimmen, insbesondere in Umfang, Zahl, Zeitraum, Bedingung, Modalität und Verneinung.\n\n"
     "[{la}] {ta}\n\n[{lb}] {tb}\n\nHaben die beiden Fassungen inhaltlich dieselbe Bedeutung? Antworte nur mit {o1} oder {o2}.")
PAIRS = [("de", "fr"), ("de", "it"), ("fr", "it")]

def parse(t):
    m = re.search(r"\b(ja|nein)\b", t.lower())
    return m.group(1) if m else None

jobs = []
for x in items:
    for a, b in PAIRS:
        jobs.append((x["id"], f"{a}-{b}", "ab", Q.format(la=a.upper(), lb=b.upper(), ta=x[a], tb=x[b], o1="Ja", o2="Nein")))
        jobs.append((x["id"], f"{a}-{b}", "ba", Q.format(la=b.upper(), lb=a.upper(), ta=x[b], tb=x[a], o1="Nein", o2="Ja")))
def run(j):
    t, m = ask(j[3], "fx-70b", 0.3, 8)
    return dict(id=j[0], pair=j[1], order=j[2], raw=t, ans=parse(t), usd=m["usd"], cached=m.get("cached", False))
R = pmap(run, jobs, 2)
json.dump(R, open(f"{H}/fx_raw.json", "w"), ensure_ascii=False, indent=1)
by = {}
for r in R: by.setdefault(r["id"], {}).setdefault(r["pair"], {})[r["order"]] = r["ans"]
rows = []; hits = ff = tflag = 0; unparsed = sum(r["ans"] is None for r in R)
for x in items:
    P = {p: sum(v == "nein" for v in o.values()) / 2 for p, o in by[x["id"]].items()}
    sc = {L: sum(P[p] for p in P if L in p.split("-")) / 2 - P[[p for p in P if L not in p.split("-")][0]] for L in ("de", "fr", "it")}
    mx = max(sc.values()); arg = [L for L in sc if sc[L] == mx]
    flag = mx >= 0.5; loc = arg[0] if len(arg) == 1 else None
    agree = sum(o["ab"] == o["ba"] for o in by[x["id"]].values())
    r = dict(id=x["id"], kind=x["kind"], gold=x.get("gold"), P=P, score=sc, flagged=flag, loc=loc, order_agree=agree, answers=by[x["id"]])
    if x["kind"] == "target":
        hits += flag and loc == x["gold"]; tflag += flag
    else: ff += flag
    rows.append(r)
nt = sum(x["kind"] == "target" for x in items); nc = len(items) - nt
oa = sum(r["order_agree"] for r in rows) / (3 * len(rows))
S = dict(hits=hits, n_targets=nt, targets_flagged=tflag, false_flags=ff, n_controls=nc, unparsed=unparsed, order_agreement=oa,
         any_nein_answers=sum(r["ans"] == "nein" for r in R), n_calls=len(R), usd=sum(r["usd"] for r in R if not r["cached"]))
json.dump(dict(summary=S, rows=rows), open(f"{H}/fx_results.json", "w"), ensure_ascii=False, indent=1)
print(json.dumps(S, indent=1))
for r in rows:
    if r["kind"] == "target" or r["flagged"]: print(r["kind"][0], r["id"], r["gold"], r["P"], "flag" if r["flagged"] else "", r["loc"])
