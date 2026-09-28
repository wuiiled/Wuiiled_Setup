#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pytest configuration: add scripts/ to sys.path for imports."""
import os
import sys

# 测试环境无 mihomo/sing-box 编译器: 允许 check_tool 返回 False 而非 sys.exit
os.environ.setdefault("WUIILED_ALLOW_MISSING_COMPILERS", "1")

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'scripts')
sys.path.insert(0, os.path.abspath(SCRIPTS_DIR))
