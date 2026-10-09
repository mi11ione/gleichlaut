"""Write or check eval/prereg/freeze.json: the sha256 of every frozen file and of the test items.
usage: python3 tools/freeze.py [--write]
The 'research_freeze' column repeats the hashes of the freeze record written on 9 Oct 2026 before any fresh-set output
existed (spikes/rescue70b/results.md); a file listed there must still match it."""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from gleichlaut.core import ROOT, FREEZE, sha256

RESEARCH = {  # 9 Oct 2026 freeze record (before the fresh 2025 run)
    "src/gleichlaut/frozen/g3/guards3.py": "113aa7a12d6c9406bbac193d7b5946dd6d7ae56e805a5fbc03f3fbd467f6fdfd",
    "src/gleichlaut/frozen/g3/whitelist_fr.json": "ea60777e147b2cc847d7ffe058496685e9474a292a8fa99a170e89386f7bc425",
    "src/gleichlaut/frozen/g3/whitelist_it.json": "8160299dedf70fdcdffa336329568298edcd362cfcb62cabf962ac69b6167e5f",
    "src/gleichlaut/frozen/g3/vocab_fr.json": "869f28c6caaf5d7cbb70f07ea601f4c0df0a697d76c4001aed29b7e6d1da5e72",
    "src/gleichlaut/frozen/g3/vocab_it.json": "8286a7ef52d379a868a2ea3d869d5e89e2b6275ed274c43181e88d559cec1c2d",
    "src/gleichlaut/frozen/g3/terms_fr.json": "4ee58c230d0c03f5d8753f33e9aabacb96dbf74b37ac2291a3e79b602c3ec993",
    "src/gleichlaut/frozen/g3/terms_it.json": "cad76b00259a70cbf8469a8ee0a1b43e1d4799d29db954fccafa5e7002a38a57",
    "src/gleichlaut/frozen/gl/guards.py": "d0d1e0d47e3828bf127e05572e055391a6eba9f9e89108b4c09e67a7fd1524f0",
    "src/gleichlaut/frozen/gl/gl70.py": "f2a207787b2ee024f67959ba5ba3001c7da44907effc50ec3e1d5fa8940ad3b8",
    "src/gleichlaut/frozen/gl/reask.py": "5b30a30a170117a9cc27baaeb6cf04395bf097c3475cb00d1db4e68286f84920",
    "src/gleichlaut/frozen/run_v2.py": "d5460bba8d10ed5d47c78941b7035631e4f8e0572845a6d984d698afb22139ab",
    "data/items/items_fresh.json": "157ca97a6ccf207e3f570e66a79b4da543cab69f3bb88b01da5bc741a5df9b02",
    "src/gleichlaut/frozen/common.py": "0ae44b4e6ba6e7fecc2d36d671a4afd5c7c6e5a60a062521339c63bdeac7c753",
    "src/gleichlaut/frozen/s2/lock.py": "1409b2ad5f5acc68bc9ace45620f86131681ec6e33d9d30d62b3ad0141f9c29f",
    "src/gleichlaut/frozen/s2/gl2.py": "08aefe04a102e13fe7d37fad2b05a47b23a96b8952a35b7e0341bba47d2f297c",
}
EXTRA = ["src/gleichlaut/frozen/s2/s2b.py", "src/gleichlaut/frozen/s2/s2.py", "src/gleichlaut/frozen/s2/score2.py",
         "src/gleichlaut/frozen/g3/build_resources.py", "src/gleichlaut/frozen/score_fresh.py", "src/gleichlaut/frozen/build_fresh.py",
         "data/items/items_oos.json", "data/items/items_dev.json"]


def build():
    files = []
    for p in list(RESEARCH) + EXTRA:
        h = sha256(os.path.join(ROOT, p))
        if p in RESEARCH and h != RESEARCH[p]: raise SystemExit(f"{p} no longer matches the 9 Oct research freeze")
        files.append(dict(path=p, sha256=h, research_freeze=RESEARCH.get(p)))
    return dict(note="sha256 of the frozen code, guard resources and test items. research_freeze = the hash in the 9 Oct 2026 "
                     "freeze record written before any fresh-set output existed (null: vendored later for provenance, unchanged since).",
                files=files)


if __name__ == "__main__":
    rec = build()
    if "--write" in sys.argv:
        os.makedirs(os.path.dirname(FREEZE), exist_ok=True)
        json.dump(rec, open(FREEZE, "w"), indent=1); print("wrote", FREEZE, len(rec["files"]), "files")
    else:
        old = json.load(open(FREEZE))
        print("OK" if old["files"] == rec["files"] else "DIFFERS")
