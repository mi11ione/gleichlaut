"""Guard re-ask for arm 2b: every model item still flagged after the full guard stack (lock.check, slot guard, unknown slots,
guards v2) gets ONE 70B re-ask: the arm-2b prompt + its previous answer + the guards' complaints. Policy (fixed before the
run): the re-ask output replaces the original only if it passes every guard; otherwise the original stays (flagged).
Gateway tag gl-70b-guard, cap $0.5. Writes reask/arm2b.jsonl (+ a copy of arm2.jsonl so score2.main works there).
usage: python3 -I reask.py"""
import json, sys, os, re, shutil
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H); sys.path.insert(0, os.path.dirname(H))
from common import ask, pmap
import guards
guards.V2 = True
exec(open(f"{H}/gl70.py").read().split("items = json.load")[0].split('"""', 2)[2])   # PA, clean_full, chk, gl2, lock, LNAME
def ntok(s): return max(1, len(s) // 3)
items = {x["key"]: x for x in json.load(open(f"{S2}/items.json"))}
R = [json.loads(l) for l in open(f"{H}/arm2b.jsonl")]
OUT = f"{H}/reask"; os.makedirs(OUT, exist_ok=True)

FIX = """

Your previous answer was: {prev}
An automatic checker found these problems in it:
{probs}
Correct exactly these problems. Apart from that, keep the old {L} text unchanged outside the amended part. Output only the amended {L} text, nothing else."""


def full_check(x, out, rec_unknown=0):
    c = chk(x, out); sg = lock.guard(x["de_old"], x["de_new"], lock.norm(x["tgt_old"]), lock.norm(out), x["lang"])
    g = guards.run(x, out); unk = len(re.findall(r"⟨[^⟩]{0,3}⟩?", out)) if "⟨" in out else 0
    return dict(lock=c, slot=sg, g=g, unknown=unk, flag=(not c["ok"]) or bool(sg) or unk > 0 or g["flag"])


def complaints(x, S, fc, L):
    lang = x["lang"]; P = []
    if not fc["lock"]["ok"]:
        P.append("- It changed text outside the amended part: " + "; ".join(f"«{S.mask(u, lang)}» -> «{S.mask(v, lang)}»" for u, v in fc["lock"]["outside"][:4]))
    if fc["slot"]: P.append(f"- The German change alters {', '.join(fc['slot'])} (numbers / negation / modal verbs); the {L} text must mirror exactly that change.")
    if fc["unknown"]: P.append("- It contains unknown slot codes; copy only the slot codes that appear in the texts.")
    g = fc["g"]
    if g["g1"]: P.append(f"- It contains German words that must be in {L}: " + ", ".join(sorted(set(g["g1"]))[:8]))
    for kind, de in g["g2"]: P.append(f"- The German change {S.mask(de, 'de')} is not (fully) carried over into the {L} text.")
    for d in g["g3"]:
        if d[0] == "outside-lost": P.append(f"- It lost words that the German change does not touch: {d[2]}")
        else: P.append(f"- Near the German change {S.mask(d[1], 'de')} it removed more than the German removes: {d[2]}")
    for n in g["g4"]: P.append(f"- It repeats text that occurs only once in the old {L} text: «{n}»")
    return "\n".join(P[:10])


def run(r):
    x = items[r["key"]]
    if r["rule_only"]: return dict(r, reasked=False, guard_flag=full_check(x, r["out"])["flag"])
    fc = full_check(x, r["out"])
    if not fc["flag"]: return dict(r, reasked=False, guard_flag=False)
    L, lang = LNAME[x["lang"]], x["lang"]
    a, b, ops = lock.de_ops(x["de_old"], x["de_new"]); S = gl2.Slots(x["tgt_old"])
    dom, dnm, tom = S.mask(x["de_old"], "de"), S.mask(x["de_new"], "de"), S.mask(x["tgt_old"], lang)
    ch = S.mask(gl2.changes_list(a, b, ops), "de")
    prompt = PA.format(L=L, de_old=dom, de_new=dnm, changes=ch, tgt_old=tom) + FIX.format(prev=S.mask(r["out"], lang), probs=complaints(x, S, fc, L), L=L)
    g, m = ask(prompt, "gl-70b-guard", 0.5, int(ntok(x["tgt_old"]) * 2.2) + 60)
    o = S.unmask(clean_full(g, lang), lang); fc2 = full_check(x, o)
    rec = dict(r, reasked=True, reask_raw=g, reask_out=o, reask_check=dict(lock_ok=fc2["lock"]["ok"], slot=fc2["slot"], g=fc2["g"], unknown=fc2["unknown"]),
               complaints=complaints(x, S, fc, L), reask_digits=len(re.findall(r"\d", g)), orig_out=r["out"])
    if not fc2["flag"]:
        rec.update(out=o, lock_ok=True, flagged_lock=False, unknown_slots=0, guard_flag=False, replaced=True)
    else:
        rec.update(guard_flag=True, replaced=False)
    return rec


if "--dry" in sys.argv:
    n = sum(1 for r in R if not r["rule_only"] and full_check(items[r["key"]], r["out"])["flag"])
    print("would re-ask", n, "est chars", sum(len(items[r["key"]]["tgt_old"]) * 3 + 1500 for r in R if not r["rule_only"])); sys.exit()
R2 = pmap(run, R, 2)
with open(f"{OUT}/arm2b.jsonl", "w") as f:
    for r in R2: f.write(json.dumps(r, ensure_ascii=False) + "\n")
shutil.copy(f"{H}/arm2.jsonl", f"{OUT}/arm2.jsonl")
print("reasked", sum(r.get("reasked", False) for r in R2), "replaced", sum(r.get("replaced", False) for r in R2),
      "still flagged", sum(r.get("guard_flag", False) for r in R2), "digits in reasks", sum(r.get("reask_digits", 0) > 0 for r in R2))
