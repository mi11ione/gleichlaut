"""Dreiklang S1 on the Air: closed-list forced-choice typing of every candidate number span, per candidate separately.
Apertus v1.5 8B text, MLX 4-bit DWQ, chat template with thinking off, assistant prefix "Antwort:".
Options = 8 subjects x 5 operators + "keine" (41), scored as summed token logprobs of the continuation.
Efficiency: the instruction is a shared KV prefix (prefilled once, trimmed back after each candidate); the 41 options
are scored through a token trie on the same cache (one single-token forward per internal trie node).
Model id, head(), chat(), enc(), lp_positions() follow round8/spike8.py.
Run on the Air from ~/apertus-spikes:  .venv/bin/python dreiklang/s1.py   (inputs dreiklang/s1_items.json,
output dreiklang/raw/s1_scores.jsonl (resumable) + dreiklang/raw/s1_meta.json). Last line always DK1_DONE.
"""
import json, os, sys, time, hashlib, glob, collections, traceback

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "raw"); os.makedirs(OUT, exist_ok=True)
MODEL = "m1rkocasu/Apertus-v1.5-8B-text-MLX-4bit-DWQ"

SUBJ = ["Alter", "Gewicht", "Dosis", "Intervall", "Zeit", "Anzahl", "Messwert", "Preis"]
OPS = ["≥", ">", "≤", "<", "="]
NONE = "keine"
OPTIONS = [f" {s} {o}" for s in SUBJ for o in OPS] + [" " + NONE]

INSTR = (
    "Du bekommst einen Ausschnitt aus einer Limitierung der Schweizer Spezialitätenliste (auf Deutsch, Französisch "
    "oder Italienisch). Eine Zahl ist mit ⟦ ⟧ markiert. Bestimme die Rolle genau dieser Zahl.\n\n"
    "Ist die Zahl eine Bedingung für die Vergütung (wer, wie viel, wie oft, wie lange, zu welchem Preis), nenne die "
    "Grösse und den Vergleichsoperator, die im Text für diese Zahl gelten.\n"
    "Grössen:\n"
    "Alter – Alter der Patienten\n"
    "Gewicht – Körpergewicht\n"
    "Dosis – Dosis oder Wirkstoffmenge einer Gabe\n"
    "Intervall – Abstand zwischen zwei Gaben (alle N Wochen)\n"
    "Zeit – Dauer, Zeitpunkt oder Zeitfenster (Behandlungsdauer, nach N Wochen, in den letzten N Monaten)\n"
    "Anzahl – Anzahl von Ereignissen, Vortherapien, Therapielinien, Gaben, Packungen oder Zyklen\n"
    "Messwert – Laborwert, Score, Stadium oder prozentuale Veränderung\n"
    "Preis – Preis, Zuschlag oder Rückerstattung\n"
    "Operatoren: ≥ (mindestens, ab), > (mehr als, über), ≤ (höchstens, bis), < (weniger als, unter), "
    "= (genau dieser Wert, ohne Vergleich).\n"
    "Ist die Zahl keine Bedingung (Code, Datum, Gesetzesartikel, Studien-, Gen- oder Krankheitsname, Skalenangabe, "
    "Packungsgrösse, Artikel wie «eine Dosis»), antworte «keine».\n"
    "Antworte nur mit «Grösse Operator» oder «keine».\n\n"
    "<ausschnitt>\n")
TAIL = "\n</ausschnitt>\n\nMarkierte Zahl: ⟦{surface}⟧"
PREFIX = "Antwort:"


def main():
    import mlx.core as mx
    from mlx_lm import load
    from mlx_lm.models.cache import make_prompt_cache, can_trim_prompt_cache, trim_prompt_cache
    mx.set_cache_limit(512 * 1024 * 1024)
    items = json.load(open(os.path.join(BASE, "s1_items.json")))
    t_load = time.time()
    model, tok = load(MODEL)
    TIE = model.args.tie_word_embeddings

    def head(h):
        lg = model.model.embed_tokens.as_linear(h) if TIE else model.lm_head(h)
        lg = lg.astype(mx.float32)
        return lg - mx.logsumexp(lg, axis=-1, keepdims=True)

    def chat(user):
        return tok.apply_chat_template([{"role": "user", "content": user}], tokenize=False, add_generation_prompt=True,
                                       enable_thinking=False)

    def enc(s):
        return tok.encode(s, add_special_tokens=False)

    def prompt_text(x):
        return chat(INSTR + x["ctx"] + TAIL.replace("{surface}", x["surface"])) + PREFIX

    # option token sequences, checked to be a clean extension of the prompt tokenisation
    def option_ids(ptxt, pre):
        seqs = []
        for o in OPTIONS:
            full = enc(ptxt + o)
            assert full[:len(pre)] == pre, ("boundary", o)
            seqs.append(full[len(pre):])
        return seqs

    # shared static prefix = longest common prefix of two different prompts, minus 2 tokens of safety
    a, b = enc(prompt_text(items[0])), enc(prompt_text(items[-1]))
    lcp = 0
    while lcp < min(len(a), len(b)) and a[lcp] == b[lcp]:
        lcp += 1
    static = a[:max(1, lcp - 2)]
    cache = make_prompt_cache(model); assert can_trim_prompt_cache(cache)
    h = model.model(mx.array(static)[None], cache); mx.eval(h)
    print(f"model loaded {time.time() - t_load:.0f}s; static prefix {len(static)} tokens; template tail {chat('X')[-80:]!r}", flush=True)

    def score_trie(first, seqs):
        out = [0.0] * len(seqs); calls = [0]

        def rec(lp, depth, idxs):
            groups = collections.defaultdict(list)
            for i in idxs:
                groups[seqs[i][depth]].append(i)
            for tid, mem in groups.items():
                s = lp[tid].item()
                for i in mem:
                    out[i] += s
                cont = [i for i in mem if len(seqs[i]) > depth + 1]
                if cont:
                    hh = model.model(mx.array([[tid]]), cache); nlp = head(hh[0, -1:])[0]; mx.eval(nlp); calls[0] += 1
                    rec(nlp, depth + 1, cont)
                    trim_prompt_cache(cache, 1)
        rec(first, 0, list(range(len(seqs))))
        return out, calls[0]

    def score_item(x):
        ptxt = prompt_text(x); pre = enc(ptxt)
        seqs = option_ids(ptxt, pre)
        if pre[:len(static)] != static:  # should not happen; fall back to a fresh cache
            raise RuntimeError("static prefix mismatch")
        ext = pre[len(static):]
        hh = model.model(mx.array(ext)[None], cache); first = head(hh[0, -1:])[0]; mx.eval(first)
        sc, calls = score_trie(first, seqs)
        trim_prompt_cache(cache, len(ext))
        return sc, len(pre), calls, seqs

    def naive(x, which):
        """reference: fresh full prefill per option (no shared cache), for the self-check"""
        ptxt = prompt_text(x); pre = enc(ptxt); seqs = option_ids(ptxt, pre); res = []
        for i in which:
            ids = pre + seqs[i]; c2 = make_prompt_cache(model)
            hh = model.model(mx.array(ids[:-1])[None], c2); lp = head(hh[0, len(pre) - 1:]); mx.eval(lp)
            res.append(sum(lp[j][seqs[i][j]].item() for j in range(len(seqs[i]))))
        return res

    outp = os.path.join(OUT, "s1_scores.jsonl")
    done = set()
    if os.path.exists(outp):
        for ln in open(outp):
            done.add(json.loads(ln)["pkey"])
    # self-check on the first item
    x0 = items[0]
    sc0, _, _, seqs0 = score_item(x0)
    which = [0, 7, 22, 33, len(OPTIONS) - 1]
    ref = naive(x0, which)
    diff = max(abs(sc0[i] - r) for i, r in zip(which, ref))
    print("self-check trie vs naive max|diff| =", round(diff, 4), "option token lengths", sorted(set(len(s) for s in seqs0)), flush=True)
    meta = dict(model=MODEL, options=OPTIONS, instr=INSTR, tail=TAIL, prefix=PREFIX, static_tokens=len(static),
                selfcheck_maxdiff=diff, option_ids=seqs0,
                instr_sha256=hashlib.sha256((INSTR + TAIL + PREFIX).encode()).hexdigest(),
                template_sha256=hashlib.sha256(chat("X").encode()).hexdigest())
    snap = glob.glob(os.path.expanduser(f"~/.cache/huggingface/hub/models--{MODEL.replace('/', '--')}/snapshots/*/"))
    if snap:
        hs = {}
        for f in sorted(glob.glob(snap[0] + "*.safetensors")):
            hsh = hashlib.sha256()
            with open(f, "rb") as fh:
                for chunk in iter(lambda: fh.read(1 << 24), b""):
                    hsh.update(chunk)
            hs[os.path.basename(f)] = hsh.hexdigest()
        meta["weights_sha256"] = hs
    json.dump(meta, open(os.path.join(OUT, "s1_meta.json"), "w"), ensure_ascii=False, indent=1)

    t0 = time.time(); n = 0
    with open(outp, "a") as f:
        for x in items:
            if x["pkey"] in done:
                continue
            t1 = time.time()
            sc, ntok, calls = score_item(x)[:3]
            done.add(x["pkey"]); n += 1
            f.write(json.dumps(dict(pkey=x["pkey"], lp=dict(zip(OPTIONS, sc)), ntok=ntok, calls=calls,
                                    secs=round(time.time() - t1, 3)), ensure_ascii=False) + "\n"); f.flush()
            if n % 25 == 0:
                print(f"{n}/{len(items)} scored, {(time.time() - t0) / n:.2f} s/cand", flush=True)
    print(f"scored {n} new prompts in {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        print("DK1_FAILED", flush=True)
    finally:
        print("DK1_DONE", flush=True)
