#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pytest configuration: isolate source cache and allow compiler-free unit tests."""
import os
import sys

import pytest

os.environ.setdefault("WUIILED_ALLOW_MISSING_COMPILERS", "1")

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "scripts")
if os.path.abspath(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, os.path.abspath(SCRIPTS_DIR))


@pytest.fixture(autouse=True)
def _isolated_source_cache(tmp_path, monkeypatch):
    """Redirect per-source fallback cache to an isolated tmp directory."""
    import core.fetcher as fetcher
    monkeypatch.setattr(fetcher, "SOURCE_CACHE_DIR", str(tmp_path / "source_cache"))
