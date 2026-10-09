"""Every number in README.md, technical_report.md and docs/notes-field.md is a registered claim whose value still equals
its source (tools/claims.py)."""
import os, subprocess, sys
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")


def test_claims_resolve_and_documents_contain_only_registered_numbers():
    r = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "claims.py"), "--scan",
                        *(os.path.join(ROOT, f) for f in ("README.md", "technical_report.md", "docs/notes-field.md"))],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout[-2000:]
