"""DEV ONLY (PREREG R7, R10, R12). A shadow month (the items the shadow workflow mined from the public feed,
data/shadow/<from>-<to>/items.json) drafted by the shipped SL pipeline with Apertus 70B through the development gateway:
plain user messages, temperature 0, served model checked on every call (backends.Gateway). Same routing, records and
summary as `gleichlaut month` (cli.draft_items / cli.summarise). Responses are recorded only in the run's own
responses/ folder (never data/cache/responses). Resumable.
--variant v3-terms (R12): the experimental prompt variant (gleichlaut.v3terms) with BAG's house wording mined from the
<from> snapshot -> data/shadow/<from>-<to>/v3_terms_70b/ (status: guard_status; every item reviewed, as the CLI does).
usage: PYTHONPATH=src python3 tools/run_shadow70b.py [FROM-TO] [--variant v3-terms]
       (default 20260901-20261001, R7; R10: 20260801-20260901)"""
import json, os, re, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from gleichlaut import core, backends, cli

args = [a for a in sys.argv[1:] if not a.startswith("--")]
variant = sys.argv[sys.argv.index("--variant") + 1] if "--variant" in sys.argv else "frozen"
if variant != "frozen": args = [a for a in args if a != variant]
month = args[0] if args else "20260901-20261001"
assert re.fullmatch(r"\d{8}-\d{8}", month), month
assert variant in ("frozen", "v3-terms"), variant
RUN = os.path.join(core.ROOT, "data", "shadow", month)
OUT = os.path.join(RUN, "70b" if variant == "frozen" else "v3_terms_70b")
items = json.load(open(os.path.join(RUN, "items.json"), encoding="utf-8"))
os.makedirs(OUT, exist_ok=True)
tag = "gleichlaut-shadow70b" if month == "20260901-20261001" else f"gleichlaut-shadow70b-{month}"
if variant != "frozen": tag = f"gleichlaut-r12-70b-{month}"
ask = backends.Gateway(os.path.expanduser("~/Desktop/hackapertus/gateway"), tag, 0.6,
                       log=os.path.join(OUT, "calls.jsonl"), record_to=os.path.join(OUT, "responses"))      # its own folder: prompts recur from earlier runs with other answers
if variant == "frozen":
    cli.draft_items(items, ask, OUT, label="gateway apertus-v1.5-70b (dev)")
    cli.summarise(items, OUT, "shadow (public feed), Apertus 70B through the development gateway (dev)")
else:
    td = month[:8]                                   # house wording mined from the month's OLD snapshot only
    review = f"experimental prompt variant {variant} (PREREG R12), not the certified pipeline: every item is reviewed; guard_status keeps the frozen guards' verdict"
    cli.draft_items(items, ask, OUT, review=review, label=f"gateway apertus-v1.5-70b (dev) (variant {variant}, house wording mined from the {td} snapshot)",
                    variant=variant, terms_date=td)
    cli.summarise(items, OUT, f"shadow (public feed), Apertus 70B through the development gateway (dev), variant {variant} (experimental)",
                  dict(variant=dict(name=variant, terms_date=td)))
