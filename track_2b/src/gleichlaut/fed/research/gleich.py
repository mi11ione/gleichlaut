"""Gleichschritt S1 model runs on the Air (Apertus v1.5 8B text, MLX 4-bit DWQ, greedy).
Arm A: DE_old, DE_new, target_old (+ code-derived list of German changes) -> target_old with only the matching edits;
       lock check (lock.py) -> one retry with feedback -> flag.
Arm B: translate DE_new from scratch.
usage (from ~/apertus-spikes): .venv/bin/python gleichschritt/gleich.py gleichschritt/items.json [A|B|AB]
Writes results/gleichschritt/{A,B}.jsonl incrementally (resumable)."""
import json, os, sys, time, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lock
import mlx.core as mx
from mlx_lm import load, generate

MODEL = "m1rkocasu/Apertus-v1.5-8B-text-MLX-4bit-DWQ"
OUT = "results/gleichschritt"; os.makedirs(OUT, exist_ok=True)
mx.set_cache_limit(512 * 1024 * 1024)
items = json.load(open(sys.argv[1]))
arms = sys.argv[2] if len(sys.argv) > 2 else "AB"
model, tok = load(MODEL)
LNAME = {"fr": "French", "it": "Italian", "rm": "Romansh (Rumantsch Grischun)"}


def chat(user):
    return tok.apply_chat_template([{"role": "user", "content": user}], tokenize=False, add_generation_prompt=True, enable_thinking=False)


def gen(prompt, n_tgt_tokens):
    mt = int(n_tgt_tokens * 2.2) + 60
    t0 = time.time()
    g = generate(model, tok, prompt=chat(prompt), max_tokens=mt, verbose=False)
    if "</think>" in g: g = g.split("</think>", 1)[1]
    return g, time.time() - t0


def clean(g, lang):
    s = g.strip()
    s = re.sub(r"^```\w*\s*|\s*```$", "", s).strip()
    lines = [l.strip() for l in s.split("\n") if l.strip()]
    if not lines: return ""
    s = lines[0]
    s = re.sub(r"^(?:\*\*)?(?:" + LNAME[lang].split()[0] + r"|Romansh|Rumantsch|Français|Italiano|Französisch|Italienisch|Rätoromanisch)[^:]{0,30}:\s*(?:\*\*)?\s*", "", s, flags=re.I)
    if len(s) > 1 and s[0] in "«\"“" and s[-1] in "»\"”": s = s[1:-1].strip()
    return s


def changes_list(de_old, de_new):
    a, b, ops = lock.de_ops(de_old, de_new)
    out = []
    for op, i1, i2, j1, j2 in ops:
        o, n = " ".join(a[i1:i2]), " ".join(b[j1:j2])
        ctx = " ".join(a[max(0, i1 - 3):i1])
        if op == "replace": out.append(f"- replace «{o}» with «{n}»")
        elif op == "delete": out.append(f"- delete «{o}»")
        else: out.append(f"- insert «{n}» after «{ctx}»")
    return "\n".join(out)


PA = """A Swiss legal provision was amended in German. Apply exactly the same amendment to the {L} version.
Change only the words that correspond to the German change. Copy every other word and punctuation mark of the old {L} text unchanged. Use the established {L} legal terminology.

German (old): {de_old}
German (new): {de_new}
Changes in German:
{changes}

{L} (old): {tgt_old}

Output only the amended {L} text, nothing else."""
RETRY = """

Your previous answer was: {prev}
It changed {L} text outside the amended part: {bad}. Keep all of that exactly as in the old {L} text and change only what corresponds to the German change."""
PB = """Translate this Swiss legal provision from German into {L}. Use the established {L} legal terminology. Output only the translation, nothing else.

{de_new}"""


def done_ids(path):
    if not os.path.exists(path): return set()
    return {json.loads(l)["key"] for l in open(path)}


def run_A():
    path = f"{OUT}/A.jsonl"; done = done_ids(path)
    for x in items:
        if x["key"] in done or not x["tgt_old"]: continue
        L = LNAME[x["lang"]]; n = len(tok.encode(x["tgt_old"]))
        p = PA.format(L=L, de_old=x["de_old"], de_new=x["de_new"], changes=changes_list(x["de_old"], x["de_new"]), tgt_old=x["tgt_old"])
        g1, s1 = gen(p, n); o1 = clean(g1, x["lang"]); c1 = lock.check(x["de_old"], x["de_new"], x["tgt_old"], o1)
        rec = dict(key=x["key"], raw1=g1, out1=o1, check1=c1, secs1=s1, retried=False)
        out, chk = o1, c1
        if not c1["ok"]:
            bad = "; ".join(f"«{a}» -> «{b}»" for a, b in c1["outside"][:4])
            g2, s2 = gen(p + RETRY.format(prev=o1, L=L, bad=bad), n); o2 = clean(g2, x["lang"])
            c2 = lock.check(x["de_old"], x["de_new"], x["tgt_old"], o2)
            rec.update(retried=True, raw2=g2, out2=o2, check2=c2, secs2=s2); out, chk = o2, c2
        rec.update(out=out, lock_ok=chk["ok"], flagged_lock=not chk["ok"], secs=rec["secs1"] + rec.get("secs2", 0))
        open(path, "a").write(json.dumps(rec, ensure_ascii=False) + "\n")
        print("A", x["key"], "ok" if c1["ok"] else ("retry-ok" if chk["ok"] else "FLAG"), f"{rec['secs']:.1f}s", flush=True)


def run_B():
    path = f"{OUT}/B.jsonl"; done = done_ids(path)
    for x in items:
        if x["key"] in done: continue
        L = LNAME[x["lang"]]; n = max(len(tok.encode(x["tgt_old"])), int(1.3 * len(tok.encode(x["de_new"]))))
        g, s = gen(PB.format(L=L, de_new=x["de_new"]), n)
        open(path, "a").write(json.dumps(dict(key=x["key"], raw=g, out=clean(g, x["lang"]), secs=s), ensure_ascii=False) + "\n")
        print("B", x["key"], f"{s:.1f}s", flush=True)


t0 = time.time()
if "A" in arms: run_A()
if "B" in arms: run_B()
print("DONE", f"{time.time() - t0:.0f}s", flush=True)
