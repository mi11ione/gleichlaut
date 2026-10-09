"""Fresh 2025 test of the frozen pipeline with guards3 (the coordinator's guard v2): 70B whole-paragraph locked rewrite + one re-ask
on the 166 FR/IT items mined from the 2025 XMLPublications captures (fresh/items_fresh.json). Nothing in gl70.py / reask.py / guards.py is edited: their code is executed
with only paths, gateway tag (gl-70b-oos) and cap ($1.0) substituted (each substitution asserted).
usage: python3 -I oos.py items | 2b | reask"""
import json, sys, os
H = os.path.dirname(os.path.abspath(__file__)); GL = os.path.join(os.path.dirname(H), "gl")
S2 = "/Users/mi11ion/Desktop/hackapertus/spikes/gleichlaut/s2"
ITEMS = f"{H}/items_fresh.json"; TAG, CAP = "gl-70b-v2", 1.0
G3 = os.path.join(os.path.dirname(H), "g3")
phase = sys.argv[1]

if phase == "items_unused":
    sys.exit("items are built by fresh/build_fresh.py")
    A = json.load(open(f"{S2}/items_all.json")); U = json.load(open(f"{S2}/items.json"))
    sig = lambda x: (x["lang"], x["de_old"], x["de_new"], x["tgt_old"])
    used = {sig(x) for x in U}; seen = {x["cluster"] for x in U}
    rest = [dict(x, pair=x["key"].rsplit("-", 1)[0], seen_family=x["cluster"] in seen) for x in A if sig(x) not in used]
    json.dump(rest, open(ITEMS, "w"), ensure_ascii=False, indent=1)
    print("items", len(rest), "seen-family items", sum(x["seen_family"] for x in rest), "unseen", sum(not x["seen_family"] for x in rest),
          "unseen families", len({x["cluster"] for x in rest if not x["seen_family"]}), "seen families", len({x["cluster"] for x in rest if x["seen_family"]}))

elif phase == "2b":
    src = open(f"{GL}/gl70.py").read().split('"""', 2)[2].split("todo = ")[0]
    sys.argv = ["gl70.py", "2b"]
    ns = {"__file__": f"{GL}/gl70.py", "__name__": "gl70"}
    exec(compile(src, f"{GL}/gl70.py", "exec"), ns)
    ns["TAG"], ns["CAP"] = TAG, CAP
    items = json.load(open(ITEMS))
    R = ns["pmap"](ns["run_2b"], items, 2)
    with open(f"{H}/arm2b.jsonl", "w") as f:
        for r in R: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("2b done", len(R))

elif phase == "reask":
    src = open(f"{GL}/reask.py").read()
    subs = [('json.load(open(f"{S2}/items.json"))', f'json.load(open("{ITEMS}"))'),
            ('open(f"{H}/arm2b.jsonl")', f'open("{H}/arm2b.jsonl")'),
            ('OUT = f"{H}/reask"', f'OUT = "{H}/final"'),
            ('"gl-70b-guard", 0.5', f'"{TAG}", {CAP}'),
            ('shutil.copy(f"{H}/arm2.jsonl", f"{OUT}/arm2.jsonl")', 'pass'),
            # a gateway BUDGET refusal during the re-ask = item not re-asked (empty answer fails every guard -> original kept, flagged)
            ("from common import ask, pmap", "from common import ask as _ask, pmap\nSKIPPED = []\n"
             "def ask(p, t, c, m):\n    try: return _ask(p, t, c, m)\n    except RuntimeError as e:\n"
             "        if 'BUDGET' not in str(e): raise\n        SKIPPED.append(1); return '', dict(usd=0.0, cached=False)\n"),
            ('print("reasked"', 'print("budget-skipped re-asks", len(SKIPPED)); print("reasked"'),
            ("import guards\nguards.V2 = True", f"sys.path.insert(0, '{G3}')\nimport guards3 as guards")]
    for a, b in subs:
        assert src.count(a) == 1, a
        src = src.replace(a, b)
    sys.argv = ["reask.py"] + sys.argv[2:]
    exec(compile(src, f"{GL}/reask.py", "exec"), {"__file__": f"{GL}/reask.py", "__name__": "__main__"})
