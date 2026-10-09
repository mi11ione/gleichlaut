"""Shared helpers for the 70B rescue spikes. Every model call goes through the budget gateway (gw.chat)."""
import sys, re
sys.path.insert(0, "/Users/mi11ion/Desktop/hackapertus/gateway")
from gw import chat as _chat
M70 = "swiss-ai/apertus-v1.5-70b"

def ask(prompt, tag, cap, max_tokens):
    import time, urllib.error
    for k in range(8):
        try:
            text, meta = _chat([{"role": "user", "content": prompt}], model=M70, max_tokens=max_tokens, temperature=0.0, tag=tag, tag_cap_usd=cap)
            break
        except urllib.error.HTTPError as e:
            if e.code != 429 or k == 7: raise
            time.sleep(20 * (k + 1))
    if False: text, meta = _chat([{"role": "user", "content": prompt}], model=M70, max_tokens=max_tokens, temperature=0.0, tag=tag, tag_cap_usd=cap)
    if "</think>" in text: text = text.split("</think>", 1)[1]
    return text, meta

def pmap(f, xs, workers=4):
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(workers) as ex: return list(ex.map(f, xs))
