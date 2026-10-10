"""DEV ONLY (PREREG R16). Memorisation probe: could Apertus have seen BAG's published FR/IT texts that are the answers of
the fresh 166 (items_fresh.json `tgt_new`)? Three sets of limitation texts, each cut in half at a word boundary; the model
is asked to continue the first half word for word; the continuation is scored against the true second half
(score.memorisation, wired into replay as res["memorisation"]).

  build     write data/memo/r16_items.json from the fresh 166, the two live months (data/shadow/) and the snapshots
            (--hist: the 2026 snapshot JSONs, --wb2025: the 2025 XML captures). Deterministic; no model, no network.
  --check   rebuild and compare with the committed file (exit 1 on any difference).
  run       Apertus 70B through the development gateway (backends.Gateway: plain user message, no system message, no
            prefill, temperature 0, served model checked on every call), sequential, one call per text, every response
            recorded in data/memo/r16_70b/responses/ (never data/cache/responses), call log calls.jsonl. Resumable.
  run8b     the same prompts with the Apertus 8B GGUF Q8_0 through llama-cpp-python (GitHub Actions CPU runners, workflow
            r16-8b): create_chat_completion with the one user message (the GGUF's chat template), temperature 0, NO logit
            mask, every response recorded in data/memo/r16_8b_q8_0/responses/ (key: payload_key('gguf:q8_0.gguf', ...)).
usage: PYTHONPATH=src python3 tools/r16_memo.py build|--check [--hist DIR] [--wb2025 DIR]
       PYTHONPATH=src python3 tools/r16_memo.py run
       PYTHONPATH=src python3 tools/r16_memo.py run8b --gguf models/q8_0.gguf [--shard K --of N]"""
import datetime, json, os, random, re, sys, time
import xml.etree.ElementTree as ET
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from gleichlaut import core, backends
from gleichlaut.sl.ingest import nrm

OUT = os.path.join(core.ROOT, "data", "memo", "r16_items.json")
RUN = os.path.join(core.ROOT, "data", "memo", "r16_70b")
HIST = os.path.expanduser("~/Desktop/hackapertus/spikes/gleichlaut/data/hist")
WB = os.path.expanduser("~/Desktop/hackapertus/spikes/gleichlaut/data/wb2025")
MONTHS = ("20260801-20260901", "20260901-20261001")
SNAPS = ["20260219", "20260304", "20260401", "20260601", "20260701", "20260801", "20260901", "20261001", "20261006"]
MINLEN, P_PER_LANG, SEED, P_BEFORE = 200, 60, 20261016, "2023-01-01"
LANGS = ("fr", "it")
INSTR = ("Continue this Swiss drug-reimbursement limitation text word for word, exactly as published by the BAG. "
         "Output only the continuation.\n\n")
MAX_TOKENS = 300
TAG = "gleichlaut-r16-70b"


def split(text):
    """first half of the words (cut at a word boundary) and the rest; texts are nrm()'d, so single spaces."""
    w = text.split(" "); k = len(w) // 2
    return " ".join(w[:k]), " ".join(w[k:])


def prompt(prefix): return INSTR + prefix


def load_xml(path):
    """every <Limitation> of a Preparations.xml -> [(valid_from ISO date, lang, text)] (texts as sl.ingest.load_xml)."""
    ns = core._extract(os.path.join(core.FROZEN, "build_fresh.py"), ("TAGS", "INLINE", "untag"), {"re": re, "nrm": nrm})
    untag = ns["untag"]; out = []
    for _, el in ET.iterparse(path, events=("end",)):
        if el.tag != "Limitation": continue
        d = (el.findtext("ValidFromDate") or "").strip()
        iso = datetime.datetime.strptime(d, "%d.%m.%Y").date().isoformat() if d else ""
        for l in LANGS: out.append((iso, l, nrm(untag(el.findtext(f"Description{l.capitalize()}") or ""))))
    return out


def snap_texts(hist, s, lang):
    return {nrm(t) for t in json.load(open(os.path.join(hist, f"{s}-{lang}.json"), encoding="utf-8"))["lim"].values()}


def rec(set_, key, lang, text, old=None, **src):
    pre, truth = split(text)
    r = dict(set=set_, key=key, lang=lang, text=text, prefix=pre, truth=truth, src=src)
    if old is not None:
        r["old_cont"] = old[len(pre):].strip() if old.startswith(pre + " ") else None     # BAG's earlier text after the same prefix
    return r


def build(hist=HIST, wbd=WB):
    hist = os.path.expanduser(hist); wbd = os.path.expanduser(wbd)
    ok = lambda t: len(t) >= MINLEN and len(split(t)[1].split(" ")) >= 10
    # T: the answers of the fresh 166
    T, seen = [], set()
    for x in json.load(open(os.path.join(core.ROOT, "data", "items", "items_fresh.json"), encoding="utf-8")):
        t = nrm(x["tgt_new"])
        if ok(t) and t not in seen:
            seen.add(t); T.append(rec("T", x["key"], x["lang"], t, nrm(x["tgt_old"]), item="items_fresh.json"))
    # earlier texts per language: both 2025 XML captures and every 2026 snapshot up to a given date
    xml = {sub: load_xml(os.path.join(wbd, sub, "Preparations.xml")) for sub in ("20250611", "20250731")}
    xml_texts = {l: {t for sub in xml for _, ll, t in xml[sub] if ll == l} for l in LANGS}
    # N: BAG's new FR/IT texts of the two live months (Aug, Sep 2026), not seen in any earlier capture
    N, nseen = [], set()
    for m in MONTHS:
        old_snap = m[:8]
        earlier = {l: set().union(xml_texts[l], *(snap_texts(hist, s, l) for s in SNAPS if s <= old_snap)) for l in LANGS}
        for x in json.load(open(os.path.join(core.ROOT, "data", "shadow", m, "items.json"), encoding="utf-8")):
            if not x.get("tgt_new"): continue
            t, o = nrm(x["tgt_new"]), nrm(x["tgt_old"])
            if t == o or not ok(t) or t in nseen or t in seen or t in earlier[x["lang"]]: continue
            nseen.add(t); N.append(rec("N", x["key"], x["lang"], t, o, month=m))
    # P: limitations valid since before 2023 in the June 2025 XML whose FR/IT text is unchanged in every 2026 snapshot
    P = []
    for l in LANGS:
        stable = set.intersection(*(snap_texts(hist, s, l) for s in SNAPS if s >= "20260601"))   # Feb-May files drop '<...>' spans
        cand = sorted({t for d, ll, t in xml["20250611"] if ll == l and d and d < P_BEFORE and ok(t) and t in stable
                       and t not in seen and t not in nseen})
        vf = {}
        for d, ll, t in xml["20250611"]:
            if ll == l and t in cand: vf[t] = min(vf.get(t, d), d)
        pick = random.Random(f"{SEED}-{l}").sample(cand, min(P_PER_LANG, len(cand)))
        P += [rec("P", f"P-{l}-{i:03d}", l, t, valid_from=vf[t]) for i, t in enumerate(sorted(pick))]
        print(f"P {l}: {len(cand)} candidates, {len(pick)} sampled", file=sys.stderr)
    items = T + N + P
    for r in items: r["payload_key"] = backends.payload_key(core.M70, prompt(r["prefix"]), MAX_TOKENS)   # the recorded response's file name
    return dict(rule="PREREG R16", instruction=INSTR, max_tokens=MAX_TOKENS, model=core.M70, min_len=MINLEN,
                p_valid_before=P_BEFORE, p_seed=SEED, sizes={s: sum(r["set"] == s for r in items) for s in "TPN"},
                langs={s: dict(sorted({l: sum(r["set"] == s and r["lang"] == l for r in items) for l in LANGS}.items())) for s in "TPN"},
                generated_by="PYTHONPATH=src python3 tools/r16_memo.py build", items=items)


def run():
    D = json.load(open(OUT, encoding="utf-8"))
    os.makedirs(RUN, exist_ok=True)
    resp = os.path.join(RUN, "responses")
    ask = backends.Gateway(os.path.expanduser("~/Desktop/hackapertus/gateway"), TAG, 2.0, model=D["model"],
                           log=os.path.join(RUN, "calls.jsonl"), record_to=resp)
    done = 0
    for i, r in enumerate(D["items"]):
        p = prompt(r["prefix"]); k = backends.payload_key(D["model"], p, D["max_tokens"])
        if os.path.exists(os.path.join(resp, k[:2], k + ".json")): continue
        text, meta = ask(p, "r16", 2.0, D["max_tokens"])
        done += 1
        print(f"{i + 1:3d}/{len(D['items'])} {r['set']} {r['lang']} served={meta['model_served']} {text[:60]!r}", flush=True)
        time.sleep(1.0)
    print("calls made:", done)


M8 = "gguf:q8_0.gguf"
RUN8 = os.path.join(core.ROOT, "data", "memo", "r16_8b_q8_0")


def run8b(gguf, k=0, n=1):
    from llama_cpp import Llama
    D = json.load(open(OUT, encoding="utf-8"))
    resp = os.path.join(RUN8, "responses"); os.makedirs(resp, exist_ok=True)
    th = backends.cpu_count()
    llm = Llama(model_path=gguf, n_ctx=8192, n_threads=th, n_threads_batch=th, logits_all=False, verbose=False)
    log = os.path.join(RUN8, f"calls-{k}of{n}.jsonl"); done = 0
    for i, r in enumerate(D["items"]):
        if i % n != k: continue
        p = prompt(r["prefix"]); key = backends.payload_key(M8, p, D["max_tokens"])
        if os.path.exists(os.path.join(resp, key[:2], key + ".json")): continue
        t0 = time.time()
        out = llm.create_chat_completion(messages=[{"role": "user", "content": p}], max_tokens=D["max_tokens"], temperature=0.0)
        text = out["choices"][0]["message"]["content"]; u = out.get("usage", {})
        meta = dict(prompt_tokens=u.get("prompt_tokens"), completion_tokens=u.get("completion_tokens"), secs=round(time.time() - t0, 2),
                    model_served=M8, backend=f"llama-cpp-python {backends.llama_version()}")
        backends.write_cache(resp, key, text, meta)
        backends._log(log, dict(meta, key=key, set=r["set"], item=r["key"], ts=backends._now()))
        done += 1
        print(f"{i + 1:3d}/{len(D['items'])} {r['set']} {r['lang']} {meta['secs']}s {text[:60]!r}", flush=True)
    print("calls made:", done)


if __name__ == "__main__":
    a = sys.argv[1:]
    opt = lambda f: a[a.index(f) + 1] if f in a else None
    if not a: sys.exit(__doc__)
    if a[0] == "run": run()
    elif a[0] == "run8b": run8b(opt("--gguf"), int(opt("--shard") or 0), int(opt("--of") or 1))
    else:
        d = build(opt("--hist") or HIST, opt("--wb2025") or WB)
        s = json.dumps(d, ensure_ascii=False, indent=1) + "\n"
        if a[0] == "--check":
            same = open(OUT, encoding="utf-8").read() == s
            print("r16 items", "identical" if same else "DIFFER"); sys.exit(0 if same else 1)
        os.makedirs(os.path.dirname(OUT), exist_ok=True); open(OUT, "w", encoding="utf-8").write(s)
        print("wrote", os.path.relpath(OUT, core.ROOT), d["sizes"], d["langs"])
