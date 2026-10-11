"""gleichlaut xliff-import FILE [FILE ...] [--run RUN | --records R.jsonl --items I.json] [--lang fr|it] [--reviewer NAME]
                       [--out decisions.json]

Reads XLIFF 1.2 or 2.1 files returned from a CAT tool (exported by `gleichlaut emit`, edited by a translator) back into
the register: the decisions JSON of the review page (`Export decisions`), which the page imports and `gleichlaut emit
--decisions` turns into reviewed XLIFF. Standard library only (ElementTree); no model, no network.

Per unit, the target text is the concatenation of every target in the unit (2.1: all <segment>/<ignorable> in order;
1.2: the whole <target>, any <mrk mtype="seg"> inside), so segments the translator joined, split or flattened read the
same as the exported ones. The text is compared with the register's draft (whitespace runs folded; a non-breaking space
counts as an edit):
  signed off (1.2: approved="yes" or target state signed-off / final; 2.1: every segment reviewed / final), text present
      -> accept (text = the draft) or accept-edited (text = the returned text)
  no target text (target removed or emptied, any state), the register had a draft -> send-back
  no target text, no draft (routed to a translator)                                -> untranslated, no decision
  text present, not signed off: edited -> the returned text goes to "edits" (shown on the page, no decision);
      unchanged -> no decision
Units are matched by id (the item key); a unit whose id is not in the register (a gettext round trip through
xliff2po / po2xliff renumbers the units) is matched by its German source text within the file's target language (exactly
one register item must have that text). The reviewer is --reviewer, else the 1.2 <phase> contact-name the unit's target
names (phase-name), else the last <phase> of the file with a contact-name, else a 2.1 <mda:meta type="reviewer">; the
decision time is that phase's date, else the file's modification time.
Exit 0; 2 when a file is not XLIFF 1.2 / 2.x, names another run, or no unit matches the register."""
import argparse, datetime, json, os, re, sys
import xml.etree.ElementTree as ET
from .. import core

NS11, NS12 = "urn:oasis:names:tc:xliff:document:1.1", "urn:oasis:names:tc:xliff:document:1.2"
NS2, MDA = "urn:oasis:names:tc:xliff:document:2.0", "urn:oasis:names:tc:xliff:metadata:2.0"
SIGNED12, SIGNED2 = {"signed-off", "final"}, {"reviewed", "final"}
LANGS = ("fr", "it", "rm")


class XliffImportError(ValueError):
    """bad input: one-line message, exit 2."""


def norm(t):
    """Whitespace runs (space, tab, newline) -> one space, stripped. A non-breaking space stays significant."""
    return re.sub(r"[ \t\r\n]+", " ", t or "").strip()


def _text(el):
    return "".join(el.itertext()) if el is not None else ""


def _join(parts):
    """Segment targets -> one text; a space where two non-empty parts meet without any whitespace (CAT tools that trim
    segments)."""
    out = ""
    for p in parts:
        if out and p and not out[-1].isspace() and not p[0].isspace(): out += " "
        out += p
    return out


def _lang(code):
    L = (code or "").split("-")[0].lower()
    return L if L in LANGS else None


def parse(path):
    """-> dict(version, run, lang, units=[dict(id, source, text, signed, states, phase; 2.x: raw)],
    phases={name: (contact, date)}, reviewer) for one XLIFF 1.2 (or 1.1, which po2xliff writes) or 2.x file. text None = no target at all."""
    try: root = ET.parse(path).getroot()
    except (ET.ParseError, OSError) as e: raise XliffImportError(f"{path}: not readable XML ({e})")
    ns = root.tag[1:].split("}")[0] if root.tag.startswith("{") else ""
    if ns in (NS12, NS11): return _parse12(root, ns)
    if ns == NS2: return _parse2(root)
    raise XliffImportError(f"{path}: not XLIFF 1.2 or 2.x (root {root.tag})")


def _run_of(original):
    return original.split(":", 1)[1] if (original or "").startswith("gleichlaut:") else None


def _parse12(root, ns):
    q = lambda t: f"{{{ns}}}{t}"
    units, phases, run, lang = [], {}, None, None
    for f in root.iter(q("file")):
        run = run or _run_of(f.get("original")); lang = lang or _lang(f.get("target-language"))
        for ph in f.iter(q("phase")):
            phases[ph.get("phase-name")] = (ph.get("contact-name") or ph.get("contact-email"), ph.get("date"))
        for tu in f.iter(q("trans-unit")):
            if tu.get("restype") == "x-gettext-domain-header": continue        # po2xliff's copy of the PO header
            t = tu.find(q("target")); st = t.get("state") if t is not None else None
            txt = _text(t) if t is not None else None
            units.append(dict(id=tu.get("id"), source=_text(tu.find(q("source"))), text=txt, states=[st],
                              signed=tu.get("approved") == "yes" or st in SIGNED12,
                              phase=t.get("phase-name") if t is not None else None))
    last = [v for v in phases.values() if v[0]]
    return dict(version=root.get("version") or "1.2", run=run, lang=lang, units=units, phases=phases, reviewer=last[-1][0] if last else None,
                reviewed_at=last[-1][1] if last else None)


def _parse2(root):
    q = lambda t: f"{{{NS2}}}{t}"
    units, run, lang, rev = [], None, _lang(root.get("trgLang")), None
    for m in root.iter(f"{{{MDA}}}meta"):
        if (m.get("type") or "").lower() in ("reviewer", "reviewed-by", "contact-name") and (m.text or "").strip(): rev = m.text.strip()
    for f in root.iter(q("file")):
        run = run or _run_of(f.get("original"))
        for u in f.iter(q("unit")):
            src, tgt, states, has_t = [], [], [], False
            for part in u:
                if part.tag not in (q("segment"), q("ignorable")): continue
                src.append(_text(part.find(q("source"))))
                t = part.find(q("target"))
                if t is not None: has_t = True; tgt.append(_text(t))
                if part.tag == q("segment"): states.append(part.get("state") or "initial")
            units.append(dict(id=u.get("id"), source="".join(src), text=_join(tgt) if has_t else None, raw="".join(tgt),
                              states=states, signed=bool(states) and all(s in SIGNED2 for s in states), phase=None))
    return dict(version=root.get("version") or "2", run=run, lang=lang, units=units, phases={}, reviewer=rev, reviewed_at=None)


def register(run=None, records=None, items=None):
    """-> (meta, {key: dict(lang, de_new, draft or None)}) of a recorded run or a records + items pair (read straight from
    the records: no re-guarding, the draft text is all the importer needs)."""
    from . import MODEL, _read_items
    from .. import score
    if records or items:
        if not (records and items): raise XliffImportError("--records and --items go together")
        I, F = _read_items(items), {r["key"]: r for r in _read_items(records)}
        stem = os.path.splitext(os.path.basename(records))[0]
        meta = dict(run=stem, model=None, run_sha256=core.sha256(records), items_sha256=core.sha256(items))
    else:
        if run not in score.RUNS or run not in MODEL: raise XliffImportError(f"unknown run {run!r} (known: {', '.join(MODEL)}; or --records/--items)")
        R = score.RUNS[run]; I = score.load_items(R["items"]); F = score.load_jsonl(R["final"])
        meta = dict(run=run, model=MODEL[run], run_sha256=core.sha256(os.path.join(score.DATA, R["final"])),
                    items_sha256=core.sha256(os.path.join(score.DATA, R["items"])))
    reg = {}
    for x in I:
        f = F.get(x["key"]) or {}
        draft = None if f.get("status") == "human" else f.get("out")
        reg[x["key"]] = dict(lang=x["lang"], de_new=x["de_new"], draft=draft)
    return meta, reg


def match(u, lang, reg, by_src):
    """-> the register key of a returned unit: its id, else its German source text (unique within the language)."""
    if u["id"] in reg: return u["id"], "id"
    c = by_src.get((lang, norm(u["source"])), [])
    return (c[0], "source") if len(c) == 1 else (None, "ambiguous" if c else "unmatched")


def decide(u, draft):
    """-> (outcome, decision or None, text): outcome in accept | accept-edited | send-back | untranslated | edited |
    unchanged."""
    txt = u["text"]
    if txt is None or not txt.strip():
        return ("send-back", "send-back", draft) if draft else ("untranslated", None, None)
    same = draft is not None and norm(draft) in (norm(txt), norm(u.get("raw") or txt))
    if u["signed"]: return ("accept", "accept", draft) if same else ("accept-edited", "accept-edited", txt)
    return ("unchanged", None, None) if same else ("edited", None, txt)


def _mtime(path):
    return datetime.datetime.fromtimestamp(os.path.getmtime(path), datetime.timezone.utc).isoformat(timespec="seconds")


def import_files(paths, run=None, records=None, items=None, lang=None, reviewer=None):
    """-> the decisions JSON (dict) for returned XLIFF files; report rows under "units"."""
    P = [parse(p) for p in paths]
    runs = {x["run"] for x in P if x["run"]}
    if not (run or records):
        if len(runs) != 1: raise XliffImportError("cannot tell the run from the files (<file original=\"gleichlaut:RUN\">): give --run or --records/--items")
        run = runs.pop()
    elif run and runs - {run}:
        raise XliffImportError(f"the files name run(s) {', '.join(sorted(runs))}, not {run}")
    meta, reg = register(run, records, items)
    by_src = {}
    for k, r in reg.items(): by_src.setdefault((r["lang"], norm(r["de_new"])), []).append(k)
    dec, edits, rows, who_all = {}, {}, [], set()
    for path, x in zip(paths, P):
        L = x["lang"] or lang
        if not L: raise XliffImportError(f"{path}: no target language in the file: give --lang fr|it")
        for u in x["units"]:
            key, how = match(u, L, reg, by_src)
            row = dict(file=os.path.basename(path), xliff=x["version"], id=u["id"], key=key, matched_by=how, states=u["states"])
            if key is None: rows.append(dict(row, outcome=how)); continue
            r = reg[key]; outcome, d, text = decide(u, r["draft"]); row["outcome"] = outcome; rows.append(row)
            ph = x["phases"].get(u["phase"]) if u["phase"] else None
            by = reviewer or (ph[0] if ph and ph[0] else None) or x["reviewer"]
            if by: who_all.add(by)
            if d:
                at = (ph[1] if ph and ph[1] else None) or x["reviewed_at"] or _mtime(path)
                dec[key] = dict(decision=d, lang=r["lang"], edited=d == "accept-edited", text=text, reason="", at=at, by=by,
                                note=f"XLIFF {x['version']} {os.path.basename(path)}: state {'/'.join(s or '-' for s in u['states'])}")
                if r["draft"] is None: dec[key]["status"] = "human"
                if d == "accept-edited": edits[key] = text
            elif outcome == "edited": edits[key] = text
    if not any(r["key"] for r in rows): raise XliffImportError("no unit of the file(s) matches the register of run " + meta["run"])
    return dict(run=meta["run"], model=meta["model"], run_sha256=meta["run_sha256"], items_sha256=meta["items_sha256"],
                exported_at=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
                reviewer=reviewer or (sorted(who_all)[0] if len(who_all) == 1 else None), source="xliff-import",
                files=[dict(file=os.path.basename(p), xliff=x["version"], sha256=core.sha256(p)) for p, x in zip(paths, P)],
                decisions=dec, edits=edits, units=rows)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="gleichlaut xliff-import", description=__doc__.split("\n\n")[1].split("\n")[0])
    ap.add_argument("files", nargs="+", metavar="FILE")
    ap.add_argument("--run", help="recorded run (default: the run the file names in <file original=\"gleichlaut:RUN\">)")
    ap.add_argument("--records", help="records JSONL (gleichlaut month / draft) instead of a recorded run; needs --items")
    ap.add_argument("--items", help="items file for --records")
    ap.add_argument("--lang", choices=LANGS, help="target language when the file does not name one")
    ap.add_argument("--reviewer", help="reviewer name (overrides the file's)")
    ap.add_argument("--out", help="decisions JSON (default: stdout)")
    a = ap.parse_args(argv)
    try:
        res = import_files(a.files, a.run, a.records, a.items, a.lang, a.reviewer)
    except XliffImportError as e:
        print(f"error: {e}", file=sys.stderr); return 2
    js = json.dumps(res, ensure_ascii=False, indent=1) + "\n"
    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        with open(a.out, "w", encoding="utf-8") as fh: fh.write(js)
    else: sys.stdout.write(js)
    from collections import Counter
    c = Counter(r["outcome"] for r in res["units"])
    print(f"xliff-import {res['run']}: {len(res['units'])} units; " + ", ".join(f"{k} {c[k]}" for k in
          ("accept", "accept-edited", "send-back", "edited", "unchanged", "untranslated", "unmatched", "ambiguous") if c[k])
          + f"; {len(res['decisions'])} decisions, {len(res['edits'])} edited texts" + (f" -> {a.out}" if a.out else ""), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
