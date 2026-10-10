"""Round-7b follow-up to S-FEDLEX on Apertus v1.5 8B text (MLX 4-bit DWQ): pairwise formulations.
  A  : per language pair, forced choice Ja/Nein "same meaning?", two orders (text order + answer order both swapped), averaged.
  AEN: same as A, English prompt, subset (9 targets + first control per act = 18 items).
  AFLIP (written, NOT run: Air GPU mutex rule): A on the same 18-item subset with the polarity flipped ("Weichen ... ab?", Ja = differs) to separate a Ja-token prior from a "same" judgment.
  B  : model back-translates FR and IT to German (greedy), then A-style Ja/Nein on (DE,BT_FR), (DE,BT_IT), (BT_FR,BT_IT).
Run on the Air from ~/apertus-spikes:  .venv/bin/python spike7b.py [speed|A|AEN|B|AFLIP|all]
Inputs: round7/fedlex_items.json. Outputs: results/round7/fedlex7b_*.json
Model loading and logprob code reused verbatim from spike7.py.
"""
import json, sys, time, os, math
import mlx.core as mx
from mlx_lm import load, generate
from mlx_lm.models.cache import make_prompt_cache

MODEL = "m1rkocasu/Apertus-v1.5-8B-text-MLX-4bit-DWQ"
OUT = "results/round7"; os.makedirs(OUT, exist_ok=True)
mx.set_cache_limit(512 * 1024 * 1024)
model, tok = load(MODEL)
TIE = model.args.tie_word_embeddings

def head(h):
    lg = model.model.embed_tokens.as_linear(h) if TIE else model.lm_head(h)
    lg = lg.astype(mx.float32)
    return lg - mx.logsumexp(lg, axis=-1, keepdims=True)

def chat(user):
    return tok.apply_chat_template([{"role": "user", "content": user}], tokenize=False, add_generation_prompt=True, enable_thinking=False)

def enc(s):
    return tok.encode(s, add_special_tokens=False)

def lp_positions(ids, positions, chunk=1024):
    cache = make_prompt_cache(model); arr = mx.array(ids); rows = {}
    for s in range(0, len(ids), chunk):
        h = model.model(arr[s:s + chunk][None], cache)
        want = [p for p in positions if s <= p < s + chunk]
        if want:
            lp = head(h[0, mx.array([p - s for p in want])]); mx.eval(lp)
            for k, p in enumerate(want): rows[p] = lp[k]
        else:
            mx.eval(h)
    return rows

def forced_choice(prompt_ids, cands):
    cids = [enc(c) for c in cands]
    multi = [i for i, c in enumerate(cids) if len(c) > 1]
    out = [None] * len(cands); n = len(prompt_ids)
    passes = [cids[i] for i in multi] or [[]]
    for k, ext in enumerate(passes):
        pos = [n - 1 + j for j in range(max(1, len(ext)))]
        rows = lp_positions(prompt_ids + ext, pos)
        first = rows[n - 1]
        for i, c in enumerate(cids):
            if len(c) == 1 and out[i] is None: out[i] = first[c[0]].item()
        if multi:
            i = multi[k]; c = cids[i]
            out[i] = sum(rows[n - 1 + j][c[j]].item() for j in range(len(c)))
    return out, cids

def softmax(xs):
    m = max(xs); e = [math.exp(x - m) for x in xs]; s = sum(e); return [x / s for x in e]

def strip_think(s):
    return s.split("</think>", 1)[1] if "</think>" in s else s

# ---------------------------------------------------------------- prompts
PAIR = {
 "de": dict(yes="Ja", no="Nein", q=(
    "Unten stehen zwei Sprachfassungen ({la} und {lb}) derselben Bestimmung des schweizerischen Bundesrechts. "
    "Beide Fassungen sind gleichermassen verbindlich und sollten dasselbe bedeuten. Prüfe, ob sie inhaltlich (nicht bloss "
    "stilistisch) übereinstimmen, insbesondere in Umfang, Zahl, Zeitraum, Bedingung, Modalität und Verneinung.\n\n"
    "[{la}] {ta}\n\n[{lb}] {tb}\n\nHaben die beiden Fassungen inhaltlich dieselbe Bedeutung? Antworte nur mit {o1} oder {o2}.")),
 "en": dict(yes="Yes", no="No", q=(
    "Below are two language versions ({la} and {lb}) of the same provision of Swiss federal law. "
    "Both versions are equally authoritative and should mean the same. Check whether they agree in substance (not merely "
    "stylistically), in particular in scope, number, period, condition, modality and negation.\n\n"
    "[{la}] {ta}\n\n[{lb}] {tb}\n\nDo the two versions have the same meaning in substance? Answer only with {o1} or {o2}.")),
 "flip": dict(yes="Ja", no="Nein", diff_is_yes=True, q=(
    "Unten stehen zwei Sprachfassungen ({la} und {lb}) derselben Bestimmung des schweizerischen Bundesrechts. "
    "Beide Fassungen sind gleichermassen verbindlich und sollten dasselbe bedeuten. Prüfe, ob sie inhaltlich (nicht bloss "
    "stilistisch) voneinander abweichen, insbesondere in Umfang, Zahl, Zeitraum, Bedingung, Modalität oder Verneinung.\n\n"
    "[{la}] {ta}\n\n[{lb}] {tb}\n\nWeichen die beiden Fassungen inhaltlich voneinander ab? Antworte nur mit {o1} oder {o2}.")),
 "bt": dict(yes="Ja", no="Nein", q=(
    "Unten stehen zwei deutsche Texte ({la} und {lb}), die dieselbe Bestimmung des schweizerischen Bundesrechts wiedergeben "
    "sollen. Prüfe, ob sie inhaltlich (nicht bloss stilistisch) übereinstimmen, insbesondere in Umfang, Zahl, Zeitraum, "
    "Bedingung, Modalität und Verneinung.\n\n[{la}] {ta}\n\n[{lb}] {tb}\n\nHaben die beiden Texte inhaltlich dieselbe "
    "Bedeutung? Antworte nur mit {o1} oder {o2}.")),
}
BT_Q = ("Übersetze den folgenden {sprache} Text aus dem schweizerischen Bundesrecht möglichst wörtlich ins Deutsche. "
        "Gib nur die deutsche Übersetzung aus, ohne Kommentar.\n\n{text}")
SPRACHE = {"fr": "französischen", "it": "italienischen"}
PAIRS = [("de", "fr"), ("de", "it"), ("fr", "it")]

def pair_score(lang, la, ta, lb, tb):
    """P(differs) averaged over two orders: (a first, yes/no) and (b first, no/yes)."""
    P = PAIR[lang]; res = {}
    for oname, (l1, t1, l2, t2, o1, o2) in (("ab", (la, ta, lb, tb, P["yes"], P["no"])),
                                             ("ba", (lb, tb, la, ta, P["no"], P["yes"]))):
        p = enc(chat(P["q"].format(la=l1, lb=l2, ta=t1, tb=t2, o1=o1, o2=o2)))
        (ly, ln), _ = forced_choice(p, [P["yes"], P["no"]])
        res[oname] = dict(lp_yes=ly, lp_no=ln, p_diff=softmax([ly, ln])[0 if P.get("diff_is_yes") else 1], mass=math.exp(ly) + math.exp(ln), ntok=len(p))
    res["p_diff"] = (res["ab"]["p_diff"] + res["ba"]["p_diff"]) / 2
    return res

def run_pairs(items, lang, fname):
    res = []; t0 = time.time()
    for x in items:
        r = dict(id=x["id"], kind=x["kind"], oc=x["oc"], eid=x["eid"], gold=x["gold"], pairs={})
        for a, b in PAIRS:
            r["pairs"][f"{a}-{b}"] = pair_score(lang, a.upper(), x[a], b.upper(), x[b])
        res.append(r)
        print(x["kind"][0], x["oc"], x["gold"], {k: round(v["p_diff"], 3) for k, v in r["pairs"].items()}, flush=True)
        json.dump(dict(rows=res, secs=time.time() - t0, lang=lang), open(f"{OUT}/{fname}", "w"), ensure_ascii=False, indent=1)

def backtranslate(lang, text):
    src = enc(text); mt = min(320, int(1.6 * len(src)) + 24)
    g = generate(model, tok, prompt=chat(BT_Q.format(sprache=SPRACHE[lang], text=text)), max_tokens=mt, verbose=False)
    return strip_think(g).strip(), mt

def run_B(items):
    res = []; t0 = time.time(); ngen = 0
    for x in items:
        r = dict(id=x["id"], kind=x["kind"], oc=x["oc"], eid=x["eid"], gold=x["gold"], bt={}, pairs={})
        for l in ("fr", "it"):
            g, mt = backtranslate(l, x[l]); ngen += 1
            r["bt"][l] = dict(text=g, max_tokens=mt, ntok=len(enc(g)))
        T = {"de": x["de"], "fr": r["bt"]["fr"]["text"], "it": r["bt"]["it"]["text"]}
        L = {"de": "A", "fr": "B", "it": "C"}  # neutral labels so the model does not see which is the original
        for a, b in PAIRS:
            r["pairs"][f"{a}-{b}"] = pair_score("bt", L[a], T[a], L[b], T[b])
        res.append(r)
        print(x["kind"][0], x["oc"], x["gold"], {k: round(v["p_diff"], 3) for k, v in r["pairs"].items()}, "| IT->", r["bt"]["it"]["text"][:90], flush=True)
        json.dump(dict(rows=res, secs=time.time() - t0, ngen=ngen), open(f"{OUT}/fedlex7b_B.json", "w"), ensure_ascii=False, indent=1)

def run_speed(items):
    x = items[0]; out = {}
    pair_score("de", "DE", x["de"], "IT", x["it"])  # warm-up
    t = time.time(); r = pair_score("de", "DE", x["de"], "FR", x["fr"]); out["fc_secs_per_choice"] = (time.time() - t) / 2
    out["fc_prompt_tokens"] = r["ab"]["ntok"]
    t = time.time(); g, mt = backtranslate("it", x["it"]); dt = time.time() - t
    out.update(bt_secs=dt, bt_tokens=len(enc(g)), bt_max=mt, bt_text=g)
    print(json.dumps(out, ensure_ascii=False), flush=True)
    json.dump(out, open(f"{OUT}/fedlex7b_speed.json", "w"), ensure_ascii=False, indent=1)

if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    items = json.load(open("round7/fedlex_items.json"))
    for c in ("Ja", "Nein", "Yes", "No"): print(c, enc(c))
    seen = set(); subset = []
    for x in items:
        if x["kind"] == "target" or x["oc"] not in seen and x["kind"] == "control":
            subset.append(x)
            if x["kind"] == "control": seen.add(x["oc"])
    steps = (("speed", lambda: run_speed(items)), ("A", lambda: run_pairs(items, "de", "fedlex7b_A.json")),
             ("B", lambda: run_B(items)), ("AEN", lambda: run_pairs(subset, "en", "fedlex7b_AEN.json")),
             ("AFLIP", lambda: run_pairs(subset, "flip", "fedlex7b_AFLIP.json")))
    for name, fn in steps:
        if which == "all" or name in which.split(","):
            print(f"=== {name}", flush=True); t = time.time(); fn(); print(f"=== {name} done in {time.time()-t:.0f}s", flush=True)
    print("SPIKE7B_DONE", flush=True)
