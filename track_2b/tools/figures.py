"""Report figures as static SVG, generated from eval/results (never hand-edited).
  docs/fig_arms.svg      exact match vs the rules-only baseline, per arm, with 95% CIs (paired cluster bootstrap)
  docs/fig_outcomes.svg  what happens to the drafts of each run: ready vs flagged, with the hand-check composition
  docs/pipeline.svg      the pipeline diagram
usage: python3 tools/figures.py"""
import json, os
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
R = lambda n: json.load(open(os.path.join(ROOT, "eval", "results", n + ".json"), encoding="utf-8"))
INK, INK2, MUTED, GRID, SURF = "#0b0b0b", "#52514e", "#8a8984", "#e4e3df", "#fcfcfb"
BLUE, ORANGE, AQUA, GRAY = "#2a78d6", "#eb6834", "#1baf7a", "#b9b8b2"
FONT = 'font-family="Helvetica Neue, Helvetica, Arial, sans-serif"'


def svg(w, h, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" {FONT}>'
            f'<rect width="{w}" height="{h}" fill="{SURF}"/>{body}</svg>')


def t(x, y, s, size=11, fill=INK, anchor="start", weight="normal"):
    s = s.replace("&", "&amp;").replace("<", "&lt;")
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" font-weight="{weight}">{s}</text>'


def arms():
    f, o, d, e = (R(n)["summary"]["all"] for n in ("fresh166", "oos242", "dev120", "dev120_8b"))
    rows = [("Apertus 70B + guards3, FRESH held-out (n=166)", f, True), ("Apertus 70B + guards v2, out-of-sample (n=242)", o, False),
            ("Apertus 70B + guards v2, dev (n=120)", d, False), ("Apertus 8B (MLX DWQ) + guards3, dev (n=120)", e, False)]
    W, H, L, X0, X1 = 800, 250, 300, 300, 690
    sx = lambda v: X0 + (v + 5) / 30 * (X1 - X0)            # axis -5 .. +25 points
    b = [t(20, 24, "Exact-match gain over the rules-only baseline (percentage points, 95% CI)", 13, INK, weight="bold")]
    for v in range(-5, 26, 5):
        b.append(f'<line x1="{sx(v)}" y1="44" x2="{sx(v)}" y2="{H - 34}" stroke="{GRID}" stroke-width="1"/>')
        b.append(t(sx(v), H - 18, f"{v:+d}" if v else "0", 10, MUTED, "middle"))
    b.append(f'<line x1="{sx(5)}" y1="40" x2="{sx(5)}" y2="{H - 34}" stroke="{INK2}" stroke-width="1" stroke-dasharray="3 3"/>')
    b.append(t(sx(5) + 4, 52, "pass-rule bar +5", 10, INK2))
    for i, (lab, s, head) in enumerate(rows):
        y = 78 + i * 40; ex = s["exact"]; lo, hi = ex["ci95"]
        b.append(t(L - 12, y + 4, lab, 11, INK if head else INK2, "end", "bold" if head else "normal"))
        b.append(f'<line x1="{sx(lo)}" y1="{y}" x2="{sx(hi)}" y2="{y}" stroke="{BLUE}" stroke-width="2" stroke-linecap="round"/>')
        b.append(f'<circle cx="{sx(ex["delta"])}" cy="{y}" r="5" fill="{BLUE}" stroke="{SURF}" stroke-width="2"/>')
        b.append(t(sx(hi) + 8, y + 4, f'{ex["delta"]:+.1f} ({ex["model"]:.1f} vs {ex["rules"]:.1f}%)', 10, INK2))
    return svg(W, H, "".join(b))


def outcomes():
    f, o, e = (R(n)["summary"]["all"] for n in ("fresh166", "oos242", "dev120_8b"))
    def comp(s):
        c = s["unflagged_classes"]; n = s["n"]
        good = c.get("exact", 0) + c.get("equivalent", 0) + c.get("preexisting", 0) + c.get("cosmetic", 0) + c.get("minor", 0)
        bad = n - s["flagged"] - good
        return [(good, BLUE, "ready, correct"), (bad, ORANGE, "ready, defective"), (s["flagged"], GRAY, "flagged for review")]
    rows = [("70B, fresh held-out (n=166)", comp(f), f), ("70B, out-of-sample (n=242)", comp(o), o), ("8B DWQ, dev (n=120)", comp(e), e)]
    W, H, L, X0, X1 = 760, 210, 230, 230, 720
    b = [t(20, 24, "What happens to each draft (share of items; ready = passes every guard)", 13, INK, weight="bold")]
    lx = 230
    for _, col, name in rows[0][1]:
        b.append(f'<rect x="{lx}" y="38" width="10" height="10" rx="2" fill="{col}"/>'); b.append(t(lx + 15, 47, name, 10, INK2)); lx += 150
    for i, (lab, parts, s) in enumerate(rows):
        y = 70 + i * 44; x = X0; n = s["n"]
        b.append(t(L - 12, y + 15, lab, 11, INK if i == 0 else INK2, "end", "bold" if i == 0 else "normal"))
        for k, (v, col, name) in enumerate(parts):
            w = (X1 - X0) * v / n
            if w <= 0: continue
            b.append(f'<rect x="{x + (1 if k else 0)}" y="{y}" width="{max(w - (1 if k else 0) - 1, 1)}" height="22" rx="3" fill="{col}"/>')
            if w > 34: b.append(t(x + w / 2, y + 15, f"{100 * v / n:.0f}%", 10, "#ffffff" if col != GRAY else INK, "middle"))
            x += w
        bad = parts[1][0]
        b.append(t(X1, y + 36, f"{bad} defective ready draft{'s' if bad != 1 else ''} in {n}", 10, ORANGE if bad else INK2, "end"))
    return svg(W, H, "".join(b))


def pipeline():
    boxes = [("Mine", "German change from the\nmonthly feed / Fedlex", None), ("Lock + slots", "windows from the DE diff;\nnumbers -> slot codes", None),
             ("Draft", "Apertus rewrites the\nparagraph (8B / 70B)", BLUE), ("Guards", "lock, numbers, German,\nstale, dropped, terms", None),
             ("Re-ask x1", "with the complaints;\nkept only if all pass", BLUE), ("Emit", "XLIFF 2.1, FHIR,\nreview page", None)]
    W, H, bw, gap = 800, 120, 116, 16
    b = []
    for i, (title, sub, col) in enumerate(boxes):
        x = 12 + i * (bw + gap)
        b.append(f'<rect x="{x}" y="22" width="{bw}" height="76" rx="0" fill="{SURF}" stroke="{col or INK2}" stroke-width="{2 if col else 1}"/>')
        b.append(t(x + bw / 2, 44, title, 12, col or INK, "middle", "bold"))
        for j, line in enumerate(sub.split("\n")): b.append(t(x + bw / 2, 64 + j * 14, line, 9, INK2, "middle"))
        if i < len(boxes) - 1:
            ax = x + bw + 2
            b.append(f'<path d="M{ax} 60 L{ax + gap - 5} 60" stroke="{MUTED}" stroke-width="1.5"/><path d="M{ax + gap - 6} 56 L{ax + gap - 2} 60 L{ax + gap - 6} 64" fill="none" stroke="{MUTED}" stroke-width="1.5"/>')
    b.append(t(12, 14, "Model steps in blue; everything else is deterministic code, frozen by sha256", 10, INK2))
    b.append(t(12, 114, "Routing: SL and Fedlex -> 8B on CPU, air-gapped (default; certified build)  |  SL, fewer edits -> 70B on a certified endpoint (option)  |  DE change > 60% -> human", 9.5, INK2))
    return svg(W, H, "".join(b))


if __name__ == "__main__":
    for name, fn in (("fig_arms", arms), ("fig_outcomes", outcomes), ("pipeline", pipeline)):
        p = os.path.join(ROOT, "docs", name + ".svg"); open(p, "w", encoding="utf-8").write(fn()); print("wrote", p)
