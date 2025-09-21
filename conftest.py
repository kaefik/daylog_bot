# Ensure project root on sys.path for legacy imports (csvdb, csvdbutils)
import sys, os
ROOT = os.path.abspath(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
