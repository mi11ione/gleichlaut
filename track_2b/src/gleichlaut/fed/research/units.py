"""Leggasi S1 pipeline helpers (NOT part of the frozen decoder): AKN XML -> aligned leaf units.
A leaf unit is a paragraph / item / listIntroduction element (with an eId) that contains no nested
paragraph/item/blockList element. Text excludes authorialNote (footnotes). stdlib only."""
import re
import xml.etree.ElementTree as ET

LEAF_TAGS = {"paragraph", "item", "listIntroduction"}
CONTAINER_TAGS = {"paragraph", "item", "blockList", "list"}


def strip_ns(root):
    for e in root.iter():
        if isinstance(e.tag, str) and "}" in e.tag:
            e.tag = e.tag.split("}", 1)[1]
    return root


def load_xml(path):
    return strip_ns(ET.parse(path).getroot())


def load_xml_bytes(b):
    return strip_ns(ET.fromstring(b))


def text_of(e):
    parts = []

    def rec(x):
        if x.tag == "authorialNote":
            if x.tail:
                parts.append(x.tail)
            return
        if x.text:
            parts.append(x.text)
        for c in x:
            rec(c)
        if x.tail and x is not e:
            parts.append(x.tail)

    rec(e)
    return re.sub(r"\s+", " ", " ".join(parts).replace("\u00ad", "")).strip()


def index(root):
    parent = {c: p for p in root.iter() for c in p}
    byid = {e.get("eId"): e for e in root.iter() if e.get("eId")}
    return parent, byid


def is_leaf(e):
    if e.tag not in LEAF_TAGS:
        return False
    for c in list(e.iter())[1:]:
        if c.tag in CONTAINER_TAGS and (c.get("eId") or c.tag in ("blockList", "list")):
            return False
    return True


def leaf_units(root):
    out = {}
    for e in root.iter():
        i = e.get("eId")
        if i and is_leaf(e):
            out[i] = text_of(e)
    return out


def aligned_leaves(roots):
    """roots: {lang: root}. Returns {eid: {lang: text}} for eids present as leaves in all languages."""
    leaves = {l: leaf_units(r) for l, r in roots.items()}
    ls = list(roots)
    common = set(leaves[ls[0]])
    for l in ls[1:]:
        common &= set(leaves[l])
    return {i: {l: leaves[l][i] for l in ls} for i in sorted(common)}


# ---- AS publications: amendment acts carry flat <p>/<blockList> content without eIds -------------------------
import difflib as _dl

_BLOCK = {"p", "listIntroduction", "item", "tr"}
_SKIP_INSIDE = {"authorialNote", "meta", "preface", "num"}


def as_blocks(root):
    """Document-order blocks of the body: <p>, <listIntroduction>, <item>, <tr>, not nested in another block or a note.
    Returns list of (key, tag, text). key = eId when the block (or its nearest ancestor) has one, else running index."""
    parent = {c: p for p in root.iter() for c in p}
    bodies = [e for e in root.iter() if e.tag in ("body", "mainBody")] or [root]
    out = []

    def anc(e):
        x = parent.get(e)
        while x is not None:
            yield x
            x = parent.get(x)

    seen = set()
    for e in (x for b in bodies for x in b.iter()):
        if id(e) in seen:
            continue
        seen.add(id(e))
        if e.tag not in _BLOCK:
            continue
        a = list(anc(e))
        if any(x.tag in _BLOCK for x in a) or any(x.tag in _SKIP_INSIDE for x in a):
            continue
        if e.tag == "p" and e.find(".//item") is not None:
            continue
        t = text_of(e)
        if not t:
            continue
        out.append((len(out), e.tag, t))
    return out


_SIG_NUM = re.compile(r"\d+")


_LABEL = re.compile(r"^\s*(\d+[a-z]*(?:\s?(?:bis|ter|quater))?|[a-z]{1,3})[.)]?\s")


def _sig(tag, t):
    m = _LABEL.match(t)
    return (m.group(1) if m else "", tuple(sorted(set(_SIG_NUM.findall(t))))[:4])


def aligned_blocks(roots):
    """{lang: root} -> {key: {lang: text}}. Index alignment when block counts match, else difflib on signatures
    (pairwise against DE)."""
    bl = {l: as_blocks(r) for l, r in roots.items()}
    ls = list(roots)
    if len({len(v) for v in bl.values()}) == 1:
        return {f"blk_{i}": {l: bl[l][i][2] for l in ls} for i in range(len(bl[ls[0]]))}
    base = ls[0]
    maps = {}
    for l in ls[1:]:
        a = [_sig(tg, t) for _, tg, t in bl[base]]
        b = [_sig(tg, t) for _, tg, t in bl[l]]
        sm = _dl.SequenceMatcher(None, a, b, autojunk=False)
        m = {}
        for op, i1, i2, j1, j2 in sm.get_opcodes():
            if op == "equal" or (op == "replace" and i2 - i1 == j2 - j1):
                for k in range(i2 - i1):
                    m[i1 + k] = j1 + k  # equal runs, and equal-length gaps between anchors, align by position
        maps[l] = m
    out = {}
    for i in range(len(bl[base])):
        if all(i in maps[l] for l in ls[1:]):
            out[f"blk_{i}"] = {base: bl[base][i][2], **{l: bl[l][maps[l][i]][2] for l in ls[1:]}}
    return out


def units_any(roots):
    """eId leaves if the document has a structured body (>= 3 aligned leaves), else aligned flat blocks."""
    al = aligned_leaves(roots)
    if len(al) >= 3:
        return al, "eid"
    return aligned_blocks(roots), "blocks"
