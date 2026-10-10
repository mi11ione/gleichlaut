"""PREREG R8: the failure-mode tests of docs/failure-modes.md re-run on the shipped Apertus 8B GGUF (Q8_0).

run.py      runners for GitHub Actions CPU runners (sharded, resumable, raw responses kept)
measure.py  deterministic scoring of the recorded outputs, Q8_0 beside the recorded MLX 4-bit runs
research/   byte-identical copies of the research files these tests come from (sha256 in research/SHA256SUMS)"""
import os
from ..core import sha256

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "research")


def verify(strict=True):
    """sha256 of the vendored research files -> list of mismatches (raise if strict)."""
    bad = []
    with open(os.path.join(RES, "SHA256SUMS")) as fh: sums = [l.split() for l in fh if l.strip()]
    for h, f in sums:
        p = os.path.join(RES, f)
        got = sha256(p) if os.path.exists(p) else "MISSING"
        if got != h: bad.append((f, h, got))
    if bad and strict: raise SystemExit("FM RESEARCH MISMATCH: " + ", ".join(f for f, _, _ in bad))
    return bad


verify()
