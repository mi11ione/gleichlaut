"""Plain test runner (no pytest needed): imports every tests/test_*.py and calls each test_* function.
A test may raise SkipTest (unittest.SkipTest) when an optional input (research tree, lxml) is absent."""
import importlib.util, os, sys, time, traceback, unittest
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(H, "..", "src")); sys.path.insert(0, H)
only = sys.argv[1:]
ok = fail = skip = 0; t0 = time.time()
for f in sorted(os.listdir(H)):
    if not (f.startswith("test_") and f.endswith(".py")) or (only and not any(o in f for o in only)): continue
    spec = importlib.util.spec_from_file_location(f[:-3], os.path.join(H, f)); m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    for n in sorted(dir(m)):
        if not n.startswith("test_") or not callable(getattr(m, n)): continue
        try:
            getattr(m, n)(); ok += 1; print(f"ok    {f}::{n}")
        except unittest.SkipTest as e:
            skip += 1; print(f"skip  {f}::{n}  ({e})")
        except Exception:
            fail += 1; print(f"FAIL  {f}::{n}"); traceback.print_exc()
print(f"\n{ok} passed, {fail} failed, {skip} skipped in {time.time() - t0:.0f}s")
sys.exit(1 if fail else 0)
