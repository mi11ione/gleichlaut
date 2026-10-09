"""Gleichlaut S2 model runs on the Air (Apertus v1.5 8B text, MLX 4-bit DWQ, greedy, thinking off).
Model id / load / chat template from round8/spike8.py; generation call + output cleaning from gleichschritt/gleich.py.
Arm 2 (locked): code applies rule ops; for each merged lock window of the remaining DE ops the 8B writes ONLY that window's
       replacement (right-to-left), with every number shown as a slot code ⟨A⟩ and a logit mask that forbids every token
       containing a decimal digit and whole-word FR/IT number words. Code writes slot values back and stitches.
Arm 3 (free): translate DE_new from scratch, no lock, no mask.
usage (from ~/apertus-spikes): .venv/bin/python gleichlaut/s2.py gleichlaut/items.json [23|2|3]
Writes results/gleichlaut/{arm2,arm3}.jsonl incrementally (resumable); last line of stdout: GL2_DONE"""
import json, os, sys, time, re, unicodedata, inspect, atexit
atexit.register(lambda: print("GL2_DONE", flush=True))  # last line of gl2.log even if the run crashes (traceback comes first)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gl2, lock
import mlx.core as mx
from mlx_lm import load, generate

MODEL = "m1rkocasu/Apertus-v1.5-8B-text-MLX-4bit-DWQ"
OUT = "results/gleichlaut"; os.makedirs(OUT, exist_ok=True)
mx.set_cache_limit(512 * 1024 * 1024)
items = json.load(open(sys.argv[1]))
arms = sys.argv[2] if len(sys.argv) > 2 else "23"
model, tok = load(MODEL)
LNAME = {"fr": "French", "it": "Italian"}


def chat(user):
    return tok.apply_chat_template([{"role": "user", "content": user}], tokenize=False, add_generation_prompt=True, enable_thinking=False)


# ---------------------------------------------------------------- digit / number-word mask
def build_mask():
    V = model(mx.array([[1]])).shape[-1]
    n = len(tok.get_vocab()) if hasattr(tok, "get_vocab") else V
    bad = {"fr": [], "it": []}; nd = 0
    for i in range(min(n, V)):
        s = tok.decode([i])
        if any(unicodedata.category(c) == "Nd" for c in s):
            bad["fr"].append(i); bad["it"].append(i); nd += 1; continue
        raw = tok.convert_ids_to_tokens(i) if hasattr(tok, "convert_ids_to_tokens") else s
        initial = s[:1].isspace() or str(raw)[:1] in ("Ġ", "▁")
        w = s.strip().lower()
        for L in ("fr", "it"):
            if w in gl2.BANWORDS[L] and initial: bad[L].append(i)
    masks = {}
    for L in ("fr", "it"):
        m = [0.0] * V
        for i in bad[L]: m[i] = -1e9
        masks[L] = mx.array(m, dtype=mx.float32)
    print(f"mask: vocab {V}, digit tokens {nd}, fr banned {len(bad['fr'])}, it banned {len(bad['it'])}", flush=True)
    return masks


MASKS = build_mask()
HAS_LP = "logits_processors" in str(inspect.signature(__import__("mlx_lm.generate", fromlist=["generate_step"]).generate_step))
print("logits_processors supported:", HAS_LP, flush=True)
assert HAS_LP, "mlx_lm.generate_step has no logits_processors; the digit ban cannot be applied"


def gen(prompt, max_tokens, lang=None):
    t0 = time.time()
    kw = {}
    if lang:
        m = MASKS[lang]
        kw["logits_processors"] = [lambda toks, logits: logits + m]
    g = generate(model, tok, prompt=chat(prompt), max_tokens=max_tokens, verbose=False, **kw)
    if "</think>" in g: g = g.split("</think>", 1)[1]
    return g, time.time() - t0


def clean_first(g, lang):
    s = g.strip()
    s = re.sub(r"^```\w*\s*|\s*```$", "", s).strip()
    lines = [l.strip() for l in s.split("\n") if l.strip()]
    if not lines: return ""
    s = lines[0]
    s = re.sub(r"^(?:\*\*)?(?:" + LNAME[lang] + r"|Français|Italiano|Französisch|Italienisch)[^:]{0,30}:\s*(?:\*\*)?\s*", "", s, flags=re.I)
    if len(s) > 1 and s[0] in "«\"“" and s[-1] in "»\"”": s = s[1:-1].strip()
    return s


def clean_window(g, lang):
    s = clean_first(g, lang)
    s = s.replace("⟦", "").replace("⟧", "").strip()
    if len(s) > 1 and s[0] in "«\"“" and s[-1] in "»\"”": s = s[1:-1].strip()
    return s


def clean_full(g, lang):
    """arm 3: the whole translation (SL texts are one paragraph; join lines, drop a leading label)."""
    s = re.sub(r"^```\w*\s*|\s*```$", "", g.strip()).strip()
    s = re.sub(r"^(?:\*\*)?(?:" + LNAME[lang] + r"|Français|Italiano|Traduction|Traduzione)[^:\n]{0,30}:\s*(?:\*\*)?\s*", "", s, flags=re.I)
    return re.sub(r"\s+", " ", s).strip()


PW = """The German text of a Swiss reimbursement limitation (Spezialitätenliste, BAG) was amended. The {L} version must receive exactly the same amendment.

German (old): {de_old}
German (new): {de_new}
German change for this part:
{changes}

{L} (old), the part to rewrite is marked ⟦ ⟧:
{tgt_marked}

Rewrite only the marked part so that the {L} text says what the new German says. Keep the wording of the marked part wherever the German did not change. Use the established {L} terminology of the Spezialitätenliste. Numbers are written as slot codes such as ⟨A⟩: copy the slot codes, never write digits or numbers in words.

Output only the new {L} text for the marked part, without ⟦ ⟧, nothing else."""

PF = """Translate this Swiss reimbursement limitation (Spezialitätenliste, BAG) from German into {L}. Use the established {L} terminology of the Spezialitätenliste. Output only the translation, nothing else.

{de_new}"""


def done_ids(path):
    if not os.path.exists(path): return set()
    return {json.loads(l)["key"] for l in open(path)}


def run_2():
    path = f"{OUT}/arm2.jsonl"; done = done_ids(path)
    for x in items:
        if x["key"] in done: continue
        L, lang = LNAME[x["lang"]], x["lang"]
        p = gl2.plan(x["de_old"], x["de_new"], x["tgt_old"], lang)
        a, b, ops = lock.de_ops(x["de_old"], x["de_new"])
        S = gl2.Slots(x["tgt_old"])
        de_old_m, de_new_m = S.mask(x["de_old"], "de"), S.mask(x["de_new"], "de")
        text = p["base"]; wins = []; t0 = time.time()
        for (lo, hi), wops in reversed(list(zip(p["windows"], p["ops_per_window"]))):
            s, e = gl2.char_span(text, lo, hi)
            marked = S.mask(text[:s], lang) + "⟦" + S.mask(text[s:e], lang) + "⟧" + S.mask(text[e:], lang)
            ch = S.mask(gl2.changes_list(a, b, wops), "de")
            prompt = PW.format(L=L, de_old=de_old_m, de_new=de_new_m, changes=ch, tgt_marked=marked)
            nt = len(tok.encode(text[s:e])); nn = sum(len(tok.encode(" ".join(b[o[3]:o[4]]))) for o in wops)
            g, secs = gen(prompt, int(max(nt, 1.5 * nn) * 2) + 40, lang)
            r_masked = clean_window(g, lang); r = S.unmask(r_masked, lang)
            leftover = re.findall(r"⟨[A-Z]{1,2}⟩", r)
            text = gl2.stitch(text, lo, hi, r)
            wins.append(dict(lo=lo, hi=hi, old=p["base"][s:e] if True else None, raw=g, out_masked=r_masked, out=r, secs=secs, unknown_slots=leftover))
        rec = dict(key=x["key"], out=text, rule_only=p["rule_only"], n_windows=len(p["windows"]), windows=wins[::-1],
                   slots=S.surf, secs=time.time() - t0)
        open(path, "a").write(json.dumps(rec, ensure_ascii=False) + "\n")
        print("2", x["key"], "rules" if p["rule_only"] else f"{len(wins)}w", f"{rec['secs']:.1f}s", flush=True)


def run_3():
    path = f"{OUT}/arm3.jsonl"; done = done_ids(path)
    for x in items:
        if x["key"] in done: continue
        L = LNAME[x["lang"]]; n = max(len(tok.encode(x["tgt_old"])), int(1.3 * len(tok.encode(x["de_new"]))))
        g, s = gen(PF.format(L=L, de_new=x["de_new"]), int(n * 1.4) + 60)
        open(path, "a").write(json.dumps(dict(key=x["key"], raw=g, out=clean_full(g, x["lang"]), secs=s), ensure_ascii=False) + "\n")
        print("3", x["key"], f"{s:.1f}s", flush=True)


t0 = time.time()
if "2" in arms: run_2()
if "3" in arms: run_3()
print("DONE", f"{time.time() - t0:.0f}s", flush=True)
