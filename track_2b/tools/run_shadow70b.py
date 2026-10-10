"""DEV ONLY (PREREG R7, R10). A shadow month (the items the shadow workflow mined from the public feed,
data/shadow/<from>-<to>/items.json) drafted by the shipped SL pipeline with Apertus 70B through the development gateway:
plain user messages, temperature 0, served model checked on every call (backends.Gateway). Same routing, records and
summary as `gleichlaut month` (cli.draft_items / cli.summarise). Responses are recorded only in the run's own
70b/responses/ (never data/cache/responses). Resumable.
usage: PYTHONPATH=src python3 tools/run_shadow70b.py [FROM-TO]     (default 20260901-20261001, R7; R10: 20260801-20260901)"""
import json, os, re, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from gleichlaut import core, backends, cli

month = sys.argv[1] if len(sys.argv) > 1 else "20260901-20261001"
assert re.fullmatch(r"\d{8}-\d{8}", month), month
RUN = os.path.join(core.ROOT, "data", "shadow", month)
OUT = os.path.join(RUN, "70b")
items = json.load(open(os.path.join(RUN, "items.json"), encoding="utf-8"))
os.makedirs(OUT, exist_ok=True)
tag = "gleichlaut-shadow70b" if month == "20260901-20261001" else f"gleichlaut-shadow70b-{month}"
ask = backends.Gateway(os.path.expanduser("~/Desktop/hackapertus/gateway"), tag, 0.6,
                       log=os.path.join(OUT, "calls.jsonl"), record_to=os.path.join(OUT, "responses"))      # its own folder: prompts recur from earlier runs with other answers
cli.draft_items(items, ask, OUT, label="gateway apertus-v1.5-70b (dev)")
cli.summarise(items, OUT, "shadow (public feed), Apertus 70B through the development gateway (dev)")
