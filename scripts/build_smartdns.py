# -*- coding: utf-8 -*-
"""
SmartDNS Branch Rule Exporter (OxiDNS consumer syntax).
"""

from typing import Dict, Optional

import utils
from core.models import RuleSet


def build_smartdns_rules(rules: Dict[str, RuleSet], output_dir: str = "output/smartdns") -> None:
    utils.export_oxidns_rules(
        rules, output_dir, domain_prefix="", flatten_host_cidr=True, label="SmartDNS"
    )


def run_all(rules: Optional[Dict[str, RuleSet]] = None) -> None:
    if rules is None:
        from core.manager import load_all_rules
        rules = load_all_rules()
    build_smartdns_rules(rules)


if __name__ == "__main__":
    run_all()
