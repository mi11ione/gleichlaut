"""DEV ONLY (PREREG R5). The shipped Fedlex lane (fed.lane.fed_draft) with Apertus 70B through the development gateway on
the 120 FR/IT Fedlex items. Plain user messages, temperature 0, served model checked on every call (backends.Gateway).
Writes data/runs/70b_fedlex_shipped.jsonl (resumable) and the blind-annotation worklist of its unflagged non-exact drafts.
usage: PYTHONPATH=src python3 tools/run_fedlex70b.py [--n N]"""
import json, os, random, sys
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from gleichlaut import core, backends
from gleichlaut.fed import lane

OUT = os.path.join(core.ROOT, "data", "runs", "70b_fedlex_shipped.jsonl")
LOG = os.path.join(core.ROOT, "eval", "certificates", "fedlex70b.calls.jsonl")
n = int(sys.argv[sys.argv.index("--n") + 1]) if "--n" in sys.argv else None
items = [x for x in lane.load(lane.ITEMS) if x["src"] == "fed" and x["lang"] in lane.SCOPE][:n]
done = {json.loads(l)["key"] for l in open(OUT, encoding="utf-8")} if os.path.exists(OUT) else set()
ask = backends.Gateway(os.path.expanduser("~/Desktop/hackapertus/gateway"), "gleichlaut-fed70b", 0.6, log=LOG,
                       record_to=os.path.join(core.ROOT, "data", "cache", "responses"))


def one(x):
    r = lane.fed_draft(x, ask); r["model"] = core.M70
    with backends._LOCK, open(OUT, "a", encoding="utf-8") as f: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(x["key"], r["status"], "exact" if r.get("exact") else "", flush=True)
    return r


with ThreadPoolExecutor(2) as ex: list(ex.map(one, [x for x in items if x["key"] not in done]))
R = {json.loads(l)["key"]: json.loads(l) for l in open(OUT, encoding="utf-8")}
I = {x["key"]: x for x in items}
todo = [k for k, r in R.items() if r["status"] == "ready" and not r.get("exact")]
print(f"items {len(R)}  exact {sum(bool(r.get('exact')) for r in R.values())}  flagged {sum(r['flagged'] for r in R.values())}  "
      f"ready non-exact {len(todo)}")
random.Random(7).shuffle(todo)
SP = os.environ.get("ANNOT_DIR")
if SP and len(R) == len(items):
    os.makedirs(SP, exist_ok=True)
    rows = [dict(id=f"H{i:02d}", lang=I[k]["lang"], de_old=I[k]["de_old"], de_new=I[k]["de_new"], tgt_old=I[k]["tgt_old"],
                 draft=R[k]["out"], official_new=I[k]["tgt_new"]) for i, k in enumerate(todo)]
    json.dump(rows, open(os.path.join(SP, "worklist.json"), "w"), ensure_ascii=False, indent=1)
    json.dump({r["id"]: k for r, k in zip(rows, todo)}, open(os.path.join(SP, "key_map_DO_NOT_SHOW.json"), "w"))
    print("worklist", len(rows), "->", SP)
