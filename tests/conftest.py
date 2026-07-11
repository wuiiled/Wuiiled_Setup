#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pytest configuration: add scripts/ to sys.path for imports."""
import sys
import os

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'scripts')
sys.path.insert(0, os.path.abspath(SCRIPTS_DIR))
