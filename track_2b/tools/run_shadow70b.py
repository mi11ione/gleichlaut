"""DEV ONLY (PREREG R7). The shadow month 01.09.2026 -> 01.10.2026 (the items the shadow workflow mined from the public
feed, data/shadow/20260901-20261001/items.json) drafted by the shipped SL pipeline with Apertus 70B through the development
gateway: plain user messages, temperature 0, served model checked on every call (backends.Gateway). Same routing,
records and summary as `gleichlaut month` (cli.draft_items / cli.summarise). Resumable.
usage: PYTHONPATH=src python3 tools/run_shadow70b.py"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from gleichlaut import core, backends, cli

RUN = os.path.join(core.ROOT, "data", "shadow", "20260901-20261001")
OUT = os.path.join(RUN, "70b")
items = json.load(open(os.path.join(RUN, "items.json"), encoding="utf-8"))
os.makedirs(OUT, exist_ok=True)
ask = backends.Gateway(os.path.expanduser("~/Desktop/hackapertus/gateway"), "gleichlaut-shadow70b", 0.6,
                       log=os.path.join(OUT, "calls.jsonl"), record_to=os.path.join(OUT, "responses"))      # its own folder: 14 prompts recur from earlier runs with other answers
cli.draft_items(items, ask, OUT, label="gateway apertus-v1.5-70b (dev)")
cli.summarise(items, OUT, "shadow (public feed), Apertus 70B through the development gateway (dev)")
