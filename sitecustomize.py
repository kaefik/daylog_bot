"""Test environment path adjustments.

Ensures project root is on sys.path so legacy imports like `from csvdb import CSVDB`
work with compatibility shims.
"""
from __future__ import annotations
import sys
import os

ROOT = os.path.abspath(os.path.dirname(__file__))
if ROOT not in sys.path:  # idempotent
    sys.path.insert(0, ROOT)
