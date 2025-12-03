import os
import sys

# Add repo root to sys.path so `import analytics` resolves to local package
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
