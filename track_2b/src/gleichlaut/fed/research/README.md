# Fedlex lane research code (Gleichschritt S1, do not edit)

Byte-identical copies of `~/Desktop/hackapertus/spikes/gleichschritt/` (8 Oct 2026). sha256 in `SHA256SUMS`
(`shasum -a 256 -c SHA256SUMS`); `gleichlaut.fed.lane` checks them at import and refuses to run on a mismatch.
None of these files is imported as a module except `units.py` and `common.py` (pure stdlib, no side effects).
The rest is parsed with `ast` and only the named definitions are executed, with model I/O, the network and file
writes injected, so the shipped lane runs this source rather than a re-implementation.

`lock.py` is **not** copied: `gleichschritt/lock.py` is byte-identical to `frozen/s2/lock.py`
(sha256 `1409b2ad5f5acc68bc9ace45620f86131681ec6e33d9d30d62b3ad0141f9c29f`), so the lane uses `core.lock`
and `lane.verify()` checks that hash too.

| File | Role in the research | What runs here |
|---|---|---|
| `gleich.py` | model loop on the Air (MLX 4-bit DWQ): arm A locked whole-paragraph rewrite + one retry, arm B free translation | `LNAME`, `PA`, `RETRY`, `PB`, `clean`, `changes_list`, `gen`, `done_ids`, `run_A`, `run_B` (`lane.py`), with `generate` -> `ask`, `chat` -> identity, `tok.encode` -> token count, `open` -> in-memory sink |
| `score.py` | scorer: exact / strict / edit-F1 / chrF / lock / flips / slot guard; corrected (apostrophe-normalised) lock replay; code lane | executed whole on staged copies of the recorded runs (`fed/score.py:research_scores`); `restore_apos`, `is_cluster`, `flip` extracted for the lane |
| `build_fed.py` | federal pool: SPARQL versions, filestore AKN, eId alignment, filters | `LM`, `QV`, `versions`, `roots_for` (`ingest.py`); the per-paragraph filters of `main()` are ported line for line in `mine.py` |
| `net.py` | cached, rate-limited HTTP (UA hackapertus-research/0.1, >= 1.1 s) | `UA`, `EP`, `_last`, `get`, `sparql` (`ingest.py`), offline by default, cache dirs injected |
| `units.py` | AKN XML -> leaf units (paragraph / item / listIntroduction with eId; footnotes stripped), alignment | imported as is (`ingest.py`) |
| `common.py` | tokeniser, change ratio, repeal pattern | imported as is (`mine.py`) |
| `make_items.py` | pools -> items (one per paragraph x language) + punctuation clean-up | `clean` (`mine.py`) |

Known inert lines: `gleich.py` imports `mlx` at top level and `net.py` names `fedlex.data.admin.ch/filestore`
(robots.txt disallows it; the research run fetched 443 filestore documents from that host). Neither line runs here:
`ingest.py` fetches filestore documents from `www.fedlex.admin.ch/filestore` and is offline unless asked.
