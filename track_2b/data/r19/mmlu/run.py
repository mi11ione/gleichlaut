import sys, json, re
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, "/Users/mi11ion/Desktop/hackapertus/gateway")
from gw import chat
D = "/private/tmp/claude-502/-Users-mi11ion/f0ec4b30-3fdf-4a1e-aa2c-660b75f86ff4/scratchpad/mmlu"
items = json.load(open(f"{D}/items.json"))
model = sys.argv[1]
def prompt(it):
    ch = "\n".join(f"{'ABCD'[i]}. {c}" for i, c in enumerate(it["ch"]))
    return f"{it['q']}\n\n{ch}\n\nAnswer with only the letter (A, B, C or D)."
def one(it):
    try:
        c, meta = chat([{"role": "user", "content": prompt(it)}], model=model, max_tokens=3, tag="sizecheck", tag_cap_usd=1.0, full=True)
        txt = c["message"]["content"] if isinstance(c, dict) else c
        served = meta.get("resp", {}).get("model") if isinstance(meta.get("resp"), dict) else meta.get("model")
        m = re.search(r"[ABCD]", txt or "")
        return dict(pred=m.group(0) if m else None, gold="ABCD"[it["a"]], served=served)
    except Exception as e:
        return dict(pred=None, gold="ABCD"[it["a"]], err=str(e)[:100])
with ThreadPoolExecutor(4) as ex: res = list(ex.map(one, items))
ok = sum(r["pred"] == r["gold"] for r in res); n = len(res)
served = sorted({str(r.get("served")) for r in res}); errs = sum("err" in r for r in res)
by = {}
for it, r in zip(items, res): by.setdefault(it["subject"], [0, 0]); by[it["subject"]][0] += r["pred"] == r["gold"]; by[it["subject"]][1] += 1
json.dump(res, open(f"{D}/res_{model.replace('/','_')}.json", "w"))
print(model, f"{ok}/{n} = {ok/n:.1%}", "errs", errs, "served", served, by)
