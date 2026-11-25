# -*- coding: utf-8 -*-
"""
MosDNS-X Rule Exporter (domain: / full: syntax).
"""

from typing import Dict, Optional

import utils
from core.models import RuleSet


def build_mosdns_rules(rules: Dict[str, RuleSet], output_dir: str = "output/mosdns-x") -> None:
    utils.export_oxidns_rules(
        rules, output_dir, domain_prefix="domain:", flatten_host_cidr=False, label="MosDNS"
    )


def run_all(rules: Optional[Dict[str, RuleSet]] = None) -> None:
    if rules is None:
        from core.manager import load_all_rules
        rules = load_all_rules()
    build_mosdns_rules(rules)


if __name__ == "__main__":
    run_all()
