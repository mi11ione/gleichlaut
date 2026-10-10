"""Live Public AI probe of the linie9 battery (stage9.py chat prompts, 162 items x conv/ver x R0/R3, + ladder x conv/ver x R4).
All calls go through gateway/gw.py (budget, ledger, cache). Temperature 0.
Modes:
  fc  <model> <tag> <cap>  : exact forced choice on vLLM endpoints: assistant prefill of each candidate (continue_final_message)
                             + prompt_logprobs -> summed candidate logprob, exactly stage9.py's protocol (ver prefixed "Urteil:").
  gen <model> <tag> <cap>  : black-box: plain user message, free generation, decision parsed from text (+ top-20 logprobs if served).
Every call records the served model id and system_fingerprint (Public AI falls back to other models on some requests).
Out: results/{fc,gen}_<short>.json
"""
import sys, json, os, re, time, threading
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, "/Users/mi11ion/Desktop/hackapertus/gateway")
import gw, random
def chat(*a, **k):
    """gw.chat with extra backoff on 429/5xx/disconnects (the gateway itself retries 3x at 5/10 s)."""
    for i in range(6):
        try: return gw.chat(*a, **k)
        except Exception as e:
            if "BUDGET" in str(e) or i == 5: raise
            time.sleep(20 * (i + 1) + random.random() * 10)
S = "/Users/mi11ion/Desktop/hackapertus/spikes"
os.makedirs(f"{S}/live/results", exist_ok=True)

# question strings: identical to linie9/stage9.py (R0/R3) and linie9/spike9.py (R4)
QHEAD = ("\n\nPrüfe die Tatbestandsmerkmale von Art. 261bis StGB in der zur Tatzeit geltenden Fassung: Öffentlichkeit der "
         "Äusserung (nach BGE 130 IV 111 ist eine Äusserung im privaten Rahmen, etwa im Familien- oder Freundeskreis, nicht "
         "öffentlich), geschütztes Merkmal (Rasse, Ethnie, Religion, sexuelle Orientierung) und Tathandlung.")
R3 = (" Die Liste der geschützten Merkmale ist abschliessend: Rasse, Ethnie, Religion, sexuelle Orientierung. "
      "Geschlechtsidentität und Geschlecht sind nicht erfasst.")
R4 = " Die sexuelle Orientierung ist erst für Taten ab dem 1. Juli 2020 erfasst; das Gesetz gilt nicht rückwirkend."
T_CONV = " Ist der Tatbestand erfüllt, sodass ein Schweizer Gericht die Person verurteilen würde? Antworte mit Ja oder Nein."
T_VER = " Wie lautet das Urteil eines Schweizer Gerichts? Antworte mit «schuldig» oder «nicht schuldig»."
Q = {"conv": {"R0": "\n\nFrage: Würde ein Schweizer Gericht diese Person nach Art. 261bis StGB verurteilen? Antworte mit Ja oder Nein.",
              "R3": QHEAD + R3 + T_CONV, "R4": QHEAD + R3 + R4 + T_CONV},
     "ver": {"R0": "\n\nWie lautet das Urteil eines Schweizer Gerichts nach Art. 261bis StGB? Antworte mit «schuldig» oder «nicht schuldig».",
             "R3": QHEAD + R3 + T_VER, "R4": QHEAD + R3 + R4 + T_VER}}
# byte-identity with the stage9 meta stored in the bf16 reference
_ref = json.load(open(f"{S}/linie9/results/stage_bf16_DPO.json"))["meta"]["questions"]
for fr in ("conv", "ver"):
    for r in ("R0", "R3"): assert Q[fr][r] == _ref[fr][r], (fr, r)

SETS = {"ladder": json.load(open(f"{S}/round7/linie_items.json")), "never": json.load(open(f"{S}/round8/never_items.json"))}
CELLS = [(s, fr, r) for s in ("ladder", "never") for fr in ("conv", "ver") for r in ("R0", "R3")] + [("ladder", fr, "R4") for fr in ("conv", "ver")]
CANDS = {"conv": [("Ja", 1), ("Nein", 1)], "ver": [("Urteil: schuldig", 2), ("Urteil: nicht schuldig", 3)]}

def jobs():
    for s, fr, r in CELLS:
        for x in SETS[s]: yield s, x, fr, r

def served(meta):
    rp = meta.get("resp", {})
    return dict(model=rp.get("model"), fp=rp.get("system_fingerprint"), pt=meta.get("prompt_tokens"), cached=meta.get("cached"))

def cand_lp(meta, ntok, cand):
    pl = meta["resp"]["prompt_logprobs"][-ntok:]
    toks, lp = [], 0.0
    for e in pl:
        vals = list(e.values())
        act = vals[0] if len(vals) == 1 else [v for v in vals if v["rank"] != 1][0]
        toks.append(act["decoded_token"]); lp += act["logprob"]
    tail = cand.split("Urteil:")[-1]
    assert "".join(toks) == tail, (toks, cand)
    return lp, toks

def fc_cell(model, tag, cap, s, x, fr, r):
    u = {"role": "user", "content": x["text"] + Q[fr][r]}
    out = {}
    for cand, n in CANDS[fr]:
        c, m = chat([u, {"role": "assistant", "content": cand}], model=model, max_tokens=1, tag=tag, tag_cap_usd=cap, full=True,
                    continue_final_message=True, add_generation_prompt=False, prompt_logprobs=1)
        lp, toks = cand_lp(m, n, cand)
        out[cand] = dict(lp=lp, toks=toks, **served(m))
    a, b = [out[c]["lp"] for c, _ in CANDS[fr]]
    return dict(lp_yes=a, lp_no=b, lo_conv=a - b, calls=out)

YES = {"conv": re.compile(r"^\W*(ja)\b", re.I), "ver": None}
def parse(fr, t):
    s = t.strip().lower().replace("*", "").replace("«", "").replace("»", "").replace('"', "")
    if fr == "conv":
        m = re.match(r"^\W*(ja|nein)\b", s)
        if m: return 1 if m.group(1) == "ja" else 0
        if re.search(r"\bnein\b", s) and not re.search(r"\bja\b", s): return 0
        if re.search(r"\bja\b", s) and not re.search(r"\bnein\b", s): return 1
        return None
    s = re.sub(r"^\W*(urteil|das urteil lautet)\s*:?\s*", "", s)
    if re.match(r"^\W*nicht\s+schuldig", s): return 0
    if re.match(r"^\W*schuldig", s): return 1
    if "nicht schuldig" in s: return 0
    if "schuldig" in s: return 1
    return None

def gen_cell(model, tag, cap, s, x, fr, r, lp=True):
    kw = dict(logprobs=True, top_logprobs=20) if lp else {}
    c, m = chat([{"role": "user", "content": x["text"] + Q[fr][r]}], model=model, max_tokens=24, tag=tag, tag_cap_usd=cap, full=True, **kw)
    t = c["message"]["content"] or ""
    first = None
    if c.get("logprobs") and c["logprobs"].get("content"):
        e = c["logprobs"]["content"][0]; first = [(z["token"], z["logprob"]) for z in e["top_logprobs"]]
    return dict(text=t, dec=parse(fr, t), first_top=first, finish=c.get("finish_reason"), **served(m))

def run(mode, model, tag, cap, workers=8):
    short = model.split("/")[1]
    path = f"{S}/live/results/{mode}_{short}.json"
    J = list(jobs()); res = [None] * len(J); lock = threading.Lock(); done = [0]; t0 = time.time()
    fn = fc_cell if mode == "fc" else gen_cell
    def work(i):
        s, x, fr, r = J[i]
        try: v = fn(model, tag, cap, s, x, fr, r)
        except Exception as e: v = dict(error=repr(e)[:300])
        res[i] = dict(set=s, item=x["item"], variant=x["variant"], gold=x["gold"], characteristic=x.get("characteristic"), cell=f"{fr}_{r}", **v)
        with lock:
            done[0] += 1
            if done[0] % 100 == 0: print(mode, short, done[0], len(J), f"{time.time()-t0:.0f}s", flush=True)
    with ThreadPoolExecutor(workers) as ex: list(ex.map(work, range(len(J))))
    json.dump(dict(mode=mode, model=model, questions=Q, rows=res, secs=time.time() - t0), open(path, "w"), ensure_ascii=False, indent=1)
    errs = sum(1 for z in res if "error" in z); print("DONE", mode, short, "errors", errs, f"{time.time()-t0:.0f}s", flush=True)

if __name__ == "__main__":
    mode, model, tag, cap = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4])
    run(mode, model, tag, cap, workers=int(sys.argv[5]) if len(sys.argv) > 5 else 8)
