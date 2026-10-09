"""Kept for the tests' imports: the fake endpoint now lives in the package (python -m gleichlaut.fake_endpoint)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from gleichlaut.fake_endpoint import FakeOpenAI, RX, CACHE  # noqa: E402,F401
