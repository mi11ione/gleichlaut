"""Pilot Phase 1: ein GEVER-taugliches Markdown-Fallblatt pro Sachverhalt (issue) des Registerprüfungs-Laufs vom
6. Oktober 2026, dazu die 6 bestätigten experimentellen Befunde (Runde 5, standardmässig aus) und eine Übersicht.
Dasselbe für jeden eigenen Lauf (`gleichlaut audit`, z. B. monatlich in out/audit/): Befunde ohne blinde Einstufung
sind «noch nicht beurteilt». Deterministisch, nur Standardbibliothek und der Code dieses Repositoriums, keine
Modellaufrufe, kein Netz.

  python3 tools/pilot_sheets.py                 schreibt docs/pilot/fallblaetter/ (Lauf vom 6. Oktober 2026, Pilotpaket)
  python3 tools/pilot_sheets.py --out DIR       schreibt nach DIR
  python3 tools/pilot_sheets.py --check         prüft, dass docs/pilot/fallblaetter/ dem Generator entspricht (exit 1 sonst)
  python3 tools/pilot_sheets.py --run DIR [--date YYYYMMDD] [--out DIR] [--check]
                                                ein eigener Lauf: DIR/audit_<date>.json (ohne --date der neueste in DIR);
                                                schreibt nach DIR/fallblaetter-<date>/ (oder --out)

Quellen (nichts wird erfunden):
  data/audit/audit_20261006.json                Befunde, Kontexte, first_seen / seen_in, findings_r5
  data/audit/audit_texts_20261006.json          DE/FR/IT-Volltexte der betroffenen Limitierungen (Auszüge der 3. Sprache)
  src/gleichlaut/ui/audit_view.py               Gruppierung zu Sachverhalten (issues(), wie im Register) und Auszüge
  eval/labels/audit_relabel.tsv (+ Satzdateien) blinde Einstufung (Mehrheit von Claude-Annotatoren, PREREG R14)
  eval/labels/audit_r15_20261006.tsv            blinde Einstufung der Runde-5-Befunde (PREREG R15)
  eval/results/audit_relabel.json, audit_r15.json, audit_grouping.json   Kontrollsummen: der Generator bricht ab, wenn
                                                seine Zählung von den Ergebnisdateien abweicht."""
import json, os, re, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))
from gleichlaut.ui import audit_view as av      # noqa: E402

OUT = os.path.join(ROOT, "docs", "pilot", "fallblaetter")
LABELS = os.path.join(ROOT, "eval", "labels")
RESULTS = os.path.join(ROOT, "eval", "results")
DATE = "20261006"
LANG = {"de": "DE", "fr": "FR", "it": "IT"}
KIND = {"number": "Zahl (Wert mit Einheit)", "unit": "Einheit", "language": "Sprache des Feldes",
        "editorial": "redaktionell (Tippfehler)", "terminology": "Terminologie (von BAG anderswo korrigierter Begriff)",
        "operator": "Vergleichsoperator", "negation": "Verneinung", "number_word": "Zahlwort"}
OPEN = "noch nicht beurteilt"
SHORT = {"real": "real", "minor": "geringfügig", "not": "nicht bestätigt", "open": OPEN}
LABEL = {"real": "real: Bedeutung weicht ab", "minor": "geringfügig: Form fehlerhaft, Bedeutung erhalten",
         "not": "nicht bestätigt: gleiche Bedeutung", "open": OPEN + ": keine blinde Einstufung zu diesem Lauf"}
EXP = "experimentelle Prüfung, standardmässig aus"
# die Antworten des Registers, Wort für Wort (src/gleichlaut/ui/page.py, TX8.de: aWrongQ, aRemQ, rem; Test prüft die Gleichheit)
WRONG_Q, REM_Q = "Welcher Text ist falsch?", "Was ist zu tun?"
REM = ("Von Amtes wegen berichtigen", "Mit der Zulassungsinhaberin in der dreijährlichen Überprüfung aufnehmen", "An den Sprachdienst",
       "Keine Massnahme (gleichwertige Formulierung)", "Noch unklar – Entscheiddossier prüfen")
FEED = "https://epl.bag.admin.ch/static/sl/publication/fhir/foph-sl-publication-20261006-{}.ndjson"


def d(s):
    return f"{s[6:8]}.{s[4:6]}.{s[:4]}" if s and len(s) == 8 else (s or "")


def tsv(name):
    L = open(os.path.join(LABELS, name), encoding="utf-8").read().splitlines()
    h = L[0].split("\t")
    return [dict(zip(h, x.split("\t"))) for x in L[1:] if x.strip()]


def esc(s):
    """Markdown-sicher: Steuerzeichen der Auszeichnung maskieren."""
    return re.sub(r"([\\`*_<>|])", r"\\\1", s)


def render(segs):
    """[[text, 0|1|2]] -> Markdown; die abweichenden Werte (2) fett."""
    return "".join(f"**{esc(t)}**" if k == 2 else esc(t) for t, k in segs).strip()


def mark(snip, what):
    """Die Werte einer Zahlenabweichung (beide Seiten, aus der Register-Zeile) in jedem Auszug fett, auch dort, wo der
    Auszug sie nur als gewöhnliche Zahl führt (z. B. IT «quattro settimane» gegenüber DE «acht Wochen»)."""
    hot = {L: set() for L in av.LANGS}
    for w in what:
        if w[0] != "number": continue
        hot["de"] |= {x for x in w[2].split() if x != "—"}; hot[w[1]] |= {x for x in w[3].split() if x != "—"}
    out = {}
    for L, segs in snip.items():
        out[L] = [[t, 2 if k == 1 and any(v in hot[L] for _, v in av._values_in(t, L)) else k] for t, k in segs]
    return out


def votes_line(final, votes):
    """Die Einstufung in einem deutschen Satz (statt der englischen Begründung der Annotatoren)."""
    v = [x for x in votes if x]; k = sum(x == final for x in v)
    who = "von beiden blinden Claude-Annotatoren" if len(v) == 2 and k == 2 else f"von {k} der {len(v)} blinden Claude-Annotatoren (Mehrheit)"
    return f"{who} {VERDICT[final]}"


VERDICT = {"real": "als real bestätigt: die Bedeutung weicht ab", "minor": "als geringfügig bestätigt: die Form ist fehlerhaft, die Bedeutung erhalten",
           "not": "nicht bestätigt: gleiche Bedeutung"}


def labels(F, date=DATE, complete=True):
    """{fid: (final, Satz)} für die 38 Registerbefunde: Mehrheit aus audit_relabel.tsv, über die Satzdateien (Kennung,
    Sprache, Rang bzw. Art) dem Befund zugeordnet (audit_view.blind_labels, dieselbe Zuordnung wie im Register). Für einen
    eigenen Lauf (complete=False) ist die Einstufung optional: ein Befund ohne Einstufung bekommt («open», «noch nicht
    beurteilt»)."""
    BL = av.blind_labels(F, date)
    if complete: assert len(BL) == len(F), (len(BL), len(F))
    out = {fid: (b["final"], votes_line(b["final"], b["votes"])) for fid, b in BL.items()}
    for f in F:
        if f.get("fid") not in out: out[f.get("fid")] = ("open", OPEN)
    return out


def check_counts(lab, X, issues):
    """Die eigene Zählung muss den Ergebnisdateien entsprechen."""
    R = json.load(open(os.path.join(RESULTS, "audit_relabel.json"), encoding="utf-8"))["sets"]
    want = {k: R["register"]["answers"].get(k, 0) + R["terminology"]["answers"].get(k, 0) for k in ("real", "minor", "not")}
    got = {k: sum(v[0] == k for v in lab.values()) for k in want}
    assert got == want, (got, want)
    P = json.load(open(os.path.join(RESULTS, "audit_r15.json"), encoding="utf-8"))["precision"]
    assert X["n"] == sum(v["findings"] for v in P.values()), X["n"]
    assert X["confirmed"] == sum(v["real_or_minor"] for v in P.values()), X["confirmed"]
    assert sum(r["label"] == "real" for r in X["rows"]) == sum(v["real"] for v in P.values())
    G = json.load(open(os.path.join(RESULTS, "audit_grouping.json"), encoding="utf-8"))
    assert len(issues) == G["issues"], (len(issues), G["issues"])
    return got


def ODD(o):
    return LANG.get(o, "unklar (die dritte Sprache entscheidet es nicht)") if o != "unclear" else "unklar (die dritte Sprache entscheidet es nicht)"


def what_line(w):
    """Kurzangabe der Abweichung aus der Register-Zeile [kind, lang, DE-Seite, Zielseite(, xkind)]."""
    k, L, a, b = w[:4]; T = LANG.get(L, L)
    if k == "number": return f"Zahl, {T}: DE {a} · {T} {b}"
    if k == "editorial": return f"Tippfehler, {T}: «{a}», gemeint «{b}»"
    if k == "terminology": return f"Terminologie, {T}: steht «{a}», von BAG anderswo ersetzt durch «{b}»"
    if k == "language": return f"Sprache, {T}: das {T}-Feld ist in {LANG.get(a, a)} verfasst"
    if k == "experimental":
        x = w[4] if len(w) > 4 else ""
        if x == "operator": return f"Vergleichsoperator, {T}: DE «{a}» · {T} «{b}»"
        if x == "negation":
            return f"Verneinung, {T}: DE verneint («{a}»), {T} nicht" if b == "—" else f"Verneinung, {T}: {T} verneint («{b}»), DE nicht"
        return f"Zahlwort, {T}: DE {a} · {T} {b}"
    return f"{k}, {T}: {a} {b}".strip()


def dating_line(dt, exp=True):
    if not dt: return "nicht datiert (die experimentelle Prüfung wird nicht über frühere Stände datiert)" if exp else \
        "nicht datiert (der Lauf hatte keine früheren Stände des Jahres zum Vergleich)"
    n, m = dt.get("n"), dt.get("m")
    pres = f"; vorhanden in {n} von {m} geprüften Ständen ab diesem Datum" if n and m else ""
    if dt.get("earliest"):
        return f"bereits im frühesten geprüften Stand 2026 vorhanden ({d(dt['first'])}){pres}"
    return f"erstmals am {d(dt['first'])}, nicht vorhanden am {d(dt['prev'])}{pres}"


def third_language(lim, ctx_de, have, date=DATE):
    """Auszug einer im Befund nicht zitierten Sprache aus den gebündelten Volltexten (wie im Register)."""
    full = av._hist_texts(None, date, lim); out = {}
    if not full or "de" not in full or not ctx_de: return out
    for L in av.LANGS:
        if L in have or L not in full: continue
        out[L] = av.highlight(av._window(full["de"], ctx_de, "de", full[L], L), L, set())
    return out


def sheet(no, title, meta, excerpts, fids, exp=False, date=DATE, src=None, pilot=True):
    """Ein Fallblatt als Markdown."""
    o = [f"# Fallblatt {no}: {title}", "",
         f"Spezialitätenliste (SL), Prüfung der Sprachfassungen DE/FR/IT, Lauf vom {d(date)} ({'Phase 1, Pilot' if pilot else 'eigener Lauf'}).", ""]
    if exp: o += [f"> **{EXP[0].upper() + EXP[1:]}.** Dieser Befund stammt aus einer Prüfart, die ihr vorab festgelegtes "
                  "Präzisionsziel nicht erreicht hat; sie ist im Standardlauf ausgeschaltet. Der Befund wurde von beiden "
                  "blinden Annotatoren bestätigt und wird deshalb zur Prüfung vorgelegt.", ""]
    o += ["| Feld | Inhalt |", "|---|---|"]
    o += [f"| {k} | {v} |" for k, v in meta]
    o += ["", "## Auszüge", "",
          f"Wörtlich aus der Publikation vom {d(date)}; die abweichenden Werte sind **fett**. «…» kürzt den Text.", ""]
    for fid, ex, note in excerpts:
        o += [f"### Befund {fid}", ""]
        for L in av.LANGS:
            if L in ex: o += [f"- **{LANG[L]}:** {render(ex[L])}"]
        if note: o += ["", f"Einstufung: {esc(note)}."]
        o += [""]
    o += ["## Bearbeitung (durch BAG auszufüllen)", "",
          "| Feld | Eintrag |", "|---|---|",
          "| Geschäftsnummer (GEVER) | durch BAG zu ergänzen |",
          "| Sprache der Verfügung | aus dem Dossier: ______ |",
          f"| {WRONG_Q} | ☐ DE ☐ FR ☐ IT (mehrere möglich; gemessen am Entscheid des BAG) |",
          f"| {REM_Q} | " + " ".join("☐ " + x for x in REM) + " |",
          "| Bemerkung | |",
          "| Visum (Name, Datum) | |", "",
          f"Quelle: `{src or f'data/audit/audit_{DATE}.json'}`, Befund{'e' if len(fids) > 1 else ''} {', '.join(fids)}; "
          "erzeugt mit `python3 tools/pilot_sheets.py` (ohne Modellaufruf).", ""]
    return "\n".join(o)


def build(path=None):
    """-> {Dateiname: Inhalt}. path: ein audit_<date>.json (Standard: der Lauf vom 6. Oktober 2026 des Pilotpakets, mit
    vollständiger Einstufung und Kontrollsummen); für jeden anderen Lauf ist die Einstufung optional."""
    pilot = path is None or os.path.realpath(path) == os.path.realpath(av.AUDIT)
    path = av.AUDIT if path is None else path
    A = json.load(open(path, encoding="utf-8"))
    F = A["findings"]; byfid = {f["fid"]: f for f in F}
    date = (A.get("summary") or {}).get("date") or re.sub(r"\D", "", os.path.basename(path))[:8]
    src = None if pilot else (os.path.relpath(path, ROOT) if os.path.realpath(path).startswith(ROOT + os.sep) else os.path.basename(path))
    D = av.data(path, hist=None)
    R, I, X = D["rows"], D["issues"], D["exp"]
    lab = labels(F, date, complete=pilot)
    tot = check_counts(lab, X, I) if pilot else {k: sum(v[0] == k for v in lab.values()) for k in ("real", "minor", "not", "open")}
    r15p = os.path.join(LABELS, f"audit_r15_{date}.tsv")
    r15 = {r["fid"]: r for r in tsv(f"audit_r15_{date}.tsv")} if os.path.exists(r15p) else {}
    files, idx = {}, []
    for i in I:
        M = [R[ix] for ix in i["rows"]]
        prods = ", ".join(i["products"]); fids = [r["fid"] for r in M]
        L = sorted({lab[f][0] for f in fids}, key=["real", "minor", "not", "open"].index)
        if "open" in L: L = ["open"]                  # an issue with an unlabelled finding: not yet assessed as a whole
        lines = "; ".join(f"{f}: {lab[f][0] if lab[f][0] != 'open' else OPEN}" for f in fids)
        flags = []
        if i["known"]: flags.append("Fall war vor Entwicklung der Prüfregel bekannt (kein unabhängiger Treffer)")
        if i["eq"]: flags.append("Prüfung selbst markiert «vermutlich gleichwertige Formulierung» (nur Triage)")
        meta = [("Präparat(e)", esc(prods)), ("Limitierung(en), Kennung in der Publikation", ", ".join(f"`{x}`" for x in i["lims"])),
                ("Art der Prüfung", ", ".join(KIND.get(k, k) for k in i["kinds"])),
                ("Betroffene Sprachfassung(en)", ", ".join(LANG[x] for x in i["langs"])),
                ("Abweichung", "<br>".join(esc(what_line(w)) for w in i["what"])),
                ("Weicht von den beiden anderen ab", ODD(i["odd"])),
                ("Erstmals festgestellt", dating_line(i["dating"], exp=False)),
                ("Blinde Einstufung", f"{LABEL[L[0]]} ({lines})"),
                ("Herkunft der Einstufung", "zwei blinde Claude-Annotatoren, ein dritter bei Uneinigkeit (Mehrheit); keine Einstufung durch das BAG"
                 if L[0] != "open" else "keine: Befunde dieses Laufs ohne blinde Einstufung; die Beurteilung erfolgt durch die Fachperson (Bearbeitung unten)"),
                ("Hinweis", "; ".join(flags) if flags else "–"),
                ("Nachschlagen", f"https://sl.bag.admin.ch/sl, Präparat «{esc(i['products'][0] if i['products'] else '')}» suchen, Limitierung in DE, FR und IT vergleichen; "
                                 f"Rohdaten: {feed(date, 'de')} (ebenso `-fr`, `-it`)")]
        ex = []
        for r in M:
            snip = dict(r["snip"])
            if len(snip) < 3:
                ctx = next((c for L2, c in av._ctxs(byfid[r["fid"]], r["kind"], r["lang"]) if L2 == "de"), None)
                snip.update(third_language(r["lim"], ctx, snip, date))
            ex.append((r["fid"], mark(snip, i["what"]), lab[r["fid"]][1]))
        no = i["iid"]; name = f"FB-{no}_{re.sub(r'[^A-Za-z0-9]+', '-', i['products'][0] if i['products'] else i['lims'][0]).strip('-')}.md"
        files[name] = sheet(no, f"{prods} ({', '.join(KIND.get(k, k).split(' (')[0] for k in i['kinds'])})", meta, ex, fids,
                            date=date, src=src, pilot=pilot)
        idx.append((no, name, prods, i["lims"], i["kinds"], i["langs"], i["what"], L[0], i["dating"], False))
    for n, r in enumerate((X or {}).get("rows", [])):
        f = next(g for g in A["findings_r5"] if g["fid"] == r["fid"])
        ctx = (f.get("context") or [None])[0]
        snip = dict(r["snip"]); snip.update(third_language(r["lim"], ctx, snip, date))
        w = X["issues"][n]["what"][0]
        meta = [("Präparat(e)", esc(r["product"])), ("Limitierung(en), Kennung in der Publikation", f"`{r['lim']}`"),
                ("Art der Prüfung", f"{KIND[r['xkind']]}: {EXP}"),
                ("Betroffene Sprachfassung(en)", LANG[r["lang"]]),
                ("Abweichung", esc(what_line(w))),
                ("Weicht von den beiden anderen ab", ODD(r["odd"])),
                ("Erstmals festgestellt", dating_line(None)),
                ("Blinde Einstufung", f"{LABEL[r['label']]} ({r['fid']}: {r['label']})"),
                ("Herkunft der Einstufung", "zwei blinde Claude-Annotatoren, übereinstimmend; keine Einstufung durch das BAG"),
                ("Hinweis", "experimentelle Prüfart; 31 Befunde im Register, davon 6 bestätigt (eval/results/audit_r15.json)"),
                ("Nachschlagen", f"https://sl.bag.admin.ch/sl, Präparat «{esc(r['product'])}» suchen, Limitierung in DE, FR und IT vergleichen; "
                                 f"Rohdaten: {feed(date, 'de')} (ebenso `-fr`, `-it`)")]
        no = X["issues"][n]["iid"]
        name = f"FB-{no}_{re.sub(r'[^A-Za-z0-9]+', '-', r['product']).strip('-')}.md"
        files[name] = sheet(no, f"{r['product']} ({KIND[r['xkind']]}, experimentell)", meta,
                            [(r["fid"], snip, votes_line(r["label"], ((r15.get(r["fid"]) or {}).get(c, "") for c in ("A", "B", "T"))))], [r["fid"]], exp=True,
                            date=date, src=src, pilot=pilot)
        idx.append((no, name, r["product"], [r["lim"]], [r["xkind"]], [r["lang"]], [w], r["label"], None, True))
    files["00_Uebersicht.md"] = overview(idx, tot, X, len(I)) if pilot else overview_run(idx, tot, X, len(I), date, src)
    return files


def feed(date, lang):
    return FEED.replace("20261006", date).format(lang)


def overview_run(idx, tot, X, n_issues, date, src):
    """Die Übersicht eines eigenen Laufs (ohne die Kontrollsummen des Pilotpakets)."""
    o = [f"# Fallblätter: Übersicht des Laufs vom {d(date)}", "",
         f"Lauf der Registerprüfung auf der SL-Publikation vom {d(date)}, ohne Modellaufruf (`{src}`). "
         f"{sum(tot.values())} Befunde in {n_issues} Sachverhalten (ein Fallblatt je Sachverhalt, Gruppierung wie im Register); "
         f"blinde Einstufung: {tot['real']} real, {tot['minor']} geringfügig, {tot['not']} nicht bestätigt, {tot['open']} {OPEN}.", ""]
    if X and X.get("rows"):
        o += [f"Dazu {X['confirmed']} bestätigte Befunde der experimentellen Prüfung (von {X['n']}), {EXP}.", ""]
    o += ["Befunde «noch nicht beurteilt» sind von niemandem eingestuft; die Fachperson beurteilt sie im Fallblatt. Eine "
          "vorhandene Einstufung stammt von blinden Claude-Annotatoren, nicht vom BAG; sie ordnet die Reihenfolge der "
          "Prüfung, sie ersetzt den Entscheid nicht.", "",
          "| Nr. | Präparat(e) | Limitierung(en) | Art | Abweichung | Einstufung | Erstmals festgestellt |", "|---|---|---|---|---|---|---|"]
    o += [_idx_row(*x) for x in idx]
    o += ["", "«≤ Datum»: bereits im frühesten geprüften Stand des Jahres vorhanden. «Datum – Datum»: zwischen diesen beiden "
          "publizierten Ständen aufgetreten. «nicht datiert»: der Lauf hatte keine früheren Stände.", ""]
    return "\n".join(o)


def _idx_row(no, name, prods, lims, kinds, langs, what, L, dt, exp):
    art = ", ".join(KIND.get(k, k).split(" (")[0] for k in kinds) + (" (experimentell)" if exp else "")
    first = "nicht datiert" if not dt else (f"≤ {d(dt['first'])}" if dt.get("earliest") else f"{d(dt['prev'])} – {d(dt['first'])}")
    return (f"| [{no}]({name}) | {esc(prods)} | {'<br>'.join('`' + x + '`' for x in lims)} | {art} | "
            f"{'<br>'.join(esc(what_line(w)) for w in what)} | {SHORT[L]} | {first} |")


def overview(idx, tot, X, n_issues):
    real_x = sum(r["label"] == "real" for r in X["rows"])
    o = ["# Fallblätter Phase 1: Übersicht", "",
         "Lauf der Registerprüfung auf der SL-Publikation vom 06.10.2026, ohne Modellaufruf. "
         f"{sum(tot.values())} Befunde in {n_issues} Sachverhalten (ein Fallblatt je Sachverhalt, Gruppierung wie im Register); "
         f"blinde Einstufung: {tot['real']} real, {tot['minor']} geringfügig, {tot['not']} nicht bestätigt "
         "(`eval/results/audit_relabel.json`). Dazu die "
         f"{X['confirmed']} bestätigten Befunde der experimentellen Prüfung ({real_x} real, {X['confirmed'] - real_x} geringfügig, "
         f"von {X['n']}; `eval/results/audit_r15.json`), {EXP}.", "",
         "Die Einstufung stammt von blinden Claude-Annotatoren, nicht vom BAG. Sie ordnet die Reihenfolge der Prüfung, "
         "sie ersetzt den Entscheid nicht.", "",
         "| Nr. | Präparat(e) | Limitierung(en) | Art | Abweichung | Einstufung | Erstmals festgestellt |", "|---|---|---|---|---|---|---|"]
    o += [_idx_row(*x) for x in idx]
    o += ["", "«≤ Datum»: bereits im frühesten geprüften Stand 2026 vorhanden. «Datum – Datum»: zwischen diesen beiden "
          "publizierten Ständen aufgetreten. Der Stand vom 04.05.2026 enthält nur Deutsch und ist nicht "
          "in die Datierung einbezogen.", ""]
    return "\n".join(o)


def run_file(run, date=None):
    """audit_<date>.json in a run directory (or the file itself); without date the newest."""
    if os.path.isfile(run): return run
    fs = sorted(f for f in (os.listdir(run) if os.path.isdir(run) else []) if re.fullmatch(r"audit_\d{8}\.json", f))
    if date: fs = [f for f in fs if f == f"audit_{date}.json"]
    if not fs: raise SystemExit(f"pilot_sheets: no audit_{date or '<date>'}.json in {run} (gleichlaut audit writes it)")
    return os.path.join(run, fs[-1])


def main(argv=None):
    a = sys.argv[1:] if argv is None else argv
    path = None
    if "--run" in a:
        path = run_file(a[a.index("--run") + 1], a[a.index("--date") + 1] if "--date" in a else None)
        date = re.sub(r"\D", "", os.path.basename(path))[:8]
        out = a[a.index("--out") + 1] if "--out" in a else os.path.join(os.path.dirname(os.path.abspath(path)), f"fallblaetter-{date}")
    else:
        out = a[a.index("--out") + 1] if "--out" in a else OUT
    files = build(path)
    if "--check" in a:
        have = {f for f in os.listdir(out) if f.endswith(".md")} if os.path.isdir(out) else set()
        bad = sorted(set(files) ^ have) + sorted(f for f in files if f in have and open(os.path.join(out, f), encoding="utf-8").read() != files[f])
        if bad: print("differs:", ", ".join(bad)); return 1
        print(f"ok: {len(files)} files"); return 0
    os.makedirs(out, exist_ok=True)
    for f in os.listdir(out):
        if f.endswith(".md") and f not in files: os.remove(os.path.join(out, f))
    for f, s in files.items():
        open(os.path.join(out, f), "w", encoding="utf-8").write(s)
    print(f"{len(files)} files -> {os.path.relpath(out, ROOT) if os.path.realpath(out).startswith(ROOT + os.sep) else out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
