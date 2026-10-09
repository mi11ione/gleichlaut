"""SL lane input: BAG ePL FHIR snapshots -> compact per-snapshot JSON (ingest) -> real DE limitation changes and FR/IT items (mine).

Paths: snapshots are read from --hist, else $GLEICHLAUT_HIST, else track_2b/out/hist (gitignored; `ingest` writes there).
Raw feeds (~90 MB per language) are never written inside the repo's data/."""
import os

TRACK = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))   # track_2b/
OUT = os.path.join(TRACK, "out")


def hist_dir(arg=None):
    return arg or os.environ.get("GLEICHLAUT_HIST") or os.path.join(OUT, "hist")
