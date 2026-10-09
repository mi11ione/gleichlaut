"""Gleichlaut S2b on the Air: Gleichschritt arm A (gleichschritt/gleich.py) on the 120 SL items, with the digit ban.
The 8B sees DE_old, DE_new, the code-derived list of German changes and the old FR/IT, and emits the FULL new FR/IT paragraph.
Every number (digits; DE/FR/IT number words 2-12) is shown as a slot code ⟨A⟩ in all three texts; a logit mask forbids every
digit token and whole-word FR/IT number words; code writes the values back. Lock check (lock.check, on apostrophe-normalised
text, as in the corrected Gleichschritt scorer) -> one retry with feedback -> flag.
Rule-only items (all DE ops are number/month/ALLCAPS swaps that code applies) skip the model (Gleichschritt "A+code").
usage (from ~/apertus-spikes): .venv/bin/python gleichlaut/s2b.py gleichlaut/items.json
Writes results/gleichlaut/arm2b.jsonl incrementally (resumable); last line of stdout: GL2B_DONE"""
import json, os, sys, time, re, unicodedata, inspect, atexit
atexit.register(lambda: print("GL2B_DONE", flush=True))  # last line of gl2b.log even if the run crashes
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gl2, lock
import mlx.core as mx
from mlx_lm import load, generate

MODEL = "m1rkocasu/Apertus-v1.5-8B-text-MLX-4bit-DWQ"
OUT = "results/gleichlaut"; os.makedirs(OUT, exist_ok=True)
mx.set_cache_limit(512 * 1024 * 1024)
items = json.load(open(sys.argv[1]))
model, tok = load(MODEL)
LNAME = {"fr": "French", "it": "Italian"}


def chat(user):
    return tok.apply_chat_template([{"role": "user", "content": user}], tokenize=False, add_generation_prompt=True, enable_thinking=False)


def build_mask():  # identical to s2.py
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
assert HAS_LP, "mlx_lm.generate_step has no logits_processors; the digit ban cannot be applied"


def gen(prompt, n_tgt_tokens, lang):  # gleich.py gen() + mask
    mt = int(n_tgt_tokens * 2.2) + 60
    m = MASKS[lang]; t0 = time.time()
    g = generate(model, tok, prompt=chat(prompt), max_tokens=mt, verbose=False, logits_processors=[lambda toks, logits: logits + m])
    if "</think>" in g: g = g.split("</think>", 1)[1]
    return g, time.time() - t0


def clean(g, lang):
    """gleich.py clean(), but SL paragraphs can be long: lines are joined (the old texts are single-line), labels stripped."""
    s = re.sub(r"^```\w*\s*|\s*```$", "", g.strip()).strip()
    s = re.sub(r"^(?:\*\*)?(?:" + LNAME[lang] + r"|Français|Italiano|Französisch|Italienisch)[^:\n]{0,30}:\s*(?:\*\*)?\s*", "", s, flags=re.I)
    s = re.sub(r"\s+", " ", s).strip()
    if len(s) > 1 and s[0] in "«\"“" and s[-1] in "»\"”": s = s[1:-1].strip()
    return s


PA = """A Swiss reimbursement limitation (Spezialitätenliste, BAG) was amended in German. Apply exactly the same amendment to the {L} version.
Change only the words that correspond to the German change. Copy every other word and punctuation mark of the old {L} text unchanged. Use the established {L} terminology of the Spezialitätenliste. Numbers are written as slot codes such as ⟨A⟩: copy the slot codes, never write digits or numbers in words.

German (old): {de_old}
German (new): {de_new}
Changes in German:
{changes}

{L} (old): {tgt_old}

Output only the amended {L} text, nothing else."""
RETRY = """

Your previous answer was: {prev}
It changed {L} text outside the amended part: {bad}. Keep all of that exactly as in the old {L} text and change only what corresponds to the German change."""


def chk(x, out):
    return lock.check(x["de_old"], x["de_new"], lock.norm(x["tgt_old"]), lock.norm(out))


def done_ids(path):
    if not os.path.exists(path): return set()
    return {json.loads(l)["key"] for l in open(path)}


def run():
    path = f"{OUT}/arm2b.jsonl"; done = done_ids(path)
    for x in items:
        if x["key"] in done: continue
        L, lang = LNAME[x["lang"]], x["lang"]
        p = gl2.plan(x["de_old"], x["de_new"], x["tgt_old"], lang)
        if p["rule_only"]:
            rec = dict(key=x["key"], out=p["base"], rule_only=True, retried=False, lock_ok=chk(x, p["base"])["ok"], flagged_lock=False, secs=0.0)
            open(path, "a").write(json.dumps(rec, ensure_ascii=False) + "\n"); print("2b", x["key"], "rules", flush=True); continue
        a, b, ops = lock.de_ops(x["de_old"], x["de_new"])
        S = gl2.Slots(x["tgt_old"])
        dom, dnm, tom = S.mask(x["de_old"], "de"), S.mask(x["de_new"], "de"), S.mask(x["tgt_old"], lang)
        ch = S.mask(gl2.changes_list(a, b, ops), "de")
        n = len(tok.encode(x["tgt_old"]))
        prompt = PA.format(L=L, de_old=dom, de_new=dnm, changes=ch, tgt_old=tom)
        g1, s1 = gen(prompt, n, lang); m1 = clean(g1, lang); o1 = S.unmask(m1, lang); c1 = chk(x, o1)
        rec = dict(key=x["key"], rule_only=False, raw1=g1, out1_masked=m1, out1=o1, check1=c1, secs1=s1, retried=False)
        out, c = o1, c1
        if not c1["ok"]:
            bad = "; ".join(f"«{S.mask(u, lang)}» -> «{S.mask(v, lang)}»" for u, v in c1["outside"][:4])
            g2, s2 = gen(prompt + RETRY.format(prev=m1, L=L, bad=bad), n, lang); m2 = clean(g2, lang); o2 = S.unmask(m2, lang); c2 = chk(x, o2)
            rec.update(retried=True, raw2=g2, out2_masked=m2, out2=o2, check2=c2, secs2=s2); out, c = o2, c2
        rec.update(out=out, lock_ok=c["ok"], flagged_lock=not c["ok"], unknown_slots=re.findall(r"⟨[^⟩]{0,3}⟩?", out).__len__() if "⟨" in out else 0,
                   slots=S.surf, secs=rec["secs1"] + rec.get("secs2", 0))
        open(path, "a").write(json.dumps(rec, ensure_ascii=False) + "\n")
        print("2b", x["key"], "ok" if c1["ok"] else ("retry-ok" if c["ok"] else "FLAG"), f"{rec['secs']:.1f}s", flush=True)


t0 = time.time()
run()
print("DONE", f"{time.time() - t0:.0f}s", flush=True)
