"""A. Gleichlaut S2 with the 70B on the same 120 items. Prompts, cleaners, planning, slots, stitching and lock check are the
8B ones (gleichlaut/s2/s2.py PW + clean_*, s2b.py PA/RETRY/clean, gl2.py, lock.py), taken verbatim (ast for the scripts that
import mlx). Differences forced by the API: no logit mask (the 70B is only *told* not to write digits; every generated digit is
counted, and an output with a model-written digit is flagged), token budgets from characters (chars/3 ~ tokens).
arm 2  (window-only locked) -> gl/arm2.jsonl   (same record format as the 8B, so score2.py scores it unchanged)
arm 2b (whole-paragraph locked rewrite + lock check + one retry, Gleichschritt-style) -> gl/arm2b.jsonl
usage: python3 -I gl70.py 2|2b [N]"""
import json, sys, os, re, ast, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import ask, pmap
S2 = "/Users/mi11ion/Desktop/hackapertus/spikes/gleichlaut/s2"; sys.path.insert(0, S2)
import gl2, lock
H = os.path.dirname(os.path.abspath(__file__))
ns = {"re": re, "LNAME": {"fr": "French", "it": "Italian"}, "lock": lock}
for f, names in ((f"{S2}/s2.py", ("PW", "clean_first", "clean_window")), (f"{S2}/s2b.py", ("PA", "RETRY", "clean", "chk"))):
    for node in ast.parse(open(f).read()).body:
        n = getattr(node, "name", None) or getattr(node.targets[0], "id", None) if isinstance(node, (ast.Assign, ast.FunctionDef)) else None
        if n in names: exec(compile(ast.Module([node], []), f, "exec"), ns)
PW, PA, RETRY, LNAME = ns["PW"], ns["PA"], ns["RETRY"], ns["LNAME"]
clean_window, clean_full, chk = ns["clean_window"], ns["clean"], ns["chk"]
items = json.load(open(f"{S2}/items.json"))
arm = sys.argv[1]; N = int(sys.argv[2]) if len(sys.argv) > 2 else None
TAG, CAP = "gl-70b", 1.2
def ntok(s): return max(1, len(s) // 3)
def digits(s): return len(re.findall(r"\d", s))

def run_2(x):
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
        nt = ntok(text[s:e]); nn = sum(ntok(" ".join(b[o[3]:o[4]])) for o in wops)
        g, meta = ask(prompt, TAG, CAP, int(max(nt, 1.5 * nn) * 2) + 40)
        r_masked = clean_window(g, lang); r = S.unmask(r_masked, lang)
        leftover = re.findall(r"⟨[A-Z]{1,2}⟩", r)
        old = text[s:e]
        text = gl2.stitch(text, lo, hi, r)
        wins.append(dict(lo=lo, hi=hi, old=old, raw=g, out_masked=r_masked, out=r, secs=meta.get("secs", 0), unknown_slots=leftover,
                         digits_raw=digits(g), ins_de=" ".join(" ".join(b[o[3]:o[4]]) for o in wops), usd=0 if meta.get("cached") else meta["usd"]))
    return dict(key=x["key"], out=text, rule_only=p["rule_only"], n_windows=len(p["windows"]), windows=wins[::-1], slots=S.surf, secs=time.time() - t0)

def run_2b(x):
    L, lang = LNAME[x["lang"]], x["lang"]
    p = gl2.plan(x["de_old"], x["de_new"], x["tgt_old"], lang)
    if p["rule_only"]:
        return dict(key=x["key"], out=p["base"], rule_only=True, retried=False, lock_ok=chk(x, p["base"])["ok"], flagged_lock=False, secs=0.0, digits_raw=0)
    a, b, ops = lock.de_ops(x["de_old"], x["de_new"])
    S = gl2.Slots(x["tgt_old"])
    dom, dnm, tom = S.mask(x["de_old"], "de"), S.mask(x["de_new"], "de"), S.mask(x["tgt_old"], lang)
    ch = S.mask(gl2.changes_list(a, b, ops), "de")
    mt = int(ntok(x["tgt_old"]) * 2.2) + 60
    prompt = PA.format(L=L, de_old=dom, de_new=dnm, changes=ch, tgt_old=tom)
    g1, m1_ = ask(prompt, TAG, CAP, mt); m1 = clean_full(g1, lang); o1 = S.unmask(m1, lang); c1 = chk(x, o1)
    rec = dict(key=x["key"], rule_only=False, raw1=g1, out1_masked=m1, out1=o1, check1=c1, secs1=m1_.get("secs", 0), retried=False, digits_raw=digits(g1))
    out, c = o1, c1
    if not c1["ok"]:
        bad = "; ".join(f"«{S.mask(u, lang)}» -> «{S.mask(v, lang)}»" for u, v in c1["outside"][:4])
        g2, m2_ = ask(prompt + RETRY.format(prev=m1, L=L, bad=bad), TAG, CAP, mt); m2 = clean_full(g2, lang); o2 = S.unmask(m2, lang); c2 = chk(x, o2)
        rec.update(retried=True, raw2=g2, out2_masked=m2, out2=o2, check2=c2, secs2=m2_.get("secs", 0), digits_raw2=digits(g2)); out, c = o2, c2
    rec.update(out=out, lock_ok=c["ok"], flagged_lock=not c["ok"], unknown_slots=re.findall(r"⟨[^⟩]{0,3}⟩?", out).__len__() if "⟨" in out else 0,
               slots=S.surf, secs=rec["secs1"] + rec.get("secs2", 0))
    return rec

todo = items[:N] if N else items
R = pmap(run_2 if arm == "2" else run_2b, todo, 2)
with open(f"{H}/arm{arm}.jsonl", "w") as f:
    for r in R: f.write(json.dumps(r, ensure_ascii=False) + "\n")
print("arm", arm, "items", len(R), "done")
