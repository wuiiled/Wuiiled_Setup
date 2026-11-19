# -*- coding: utf-8 -*-
"""clean_domain_entry 统一入口语义边界 + patcher 行解析加固 + AI 源格式绊线。
(2026-11-20 裁剪: 移除重构期"新旧逻辑对拍"迁移测试, CI 语义由既有单测与
lint_artifacts/构建守卫覆盖。)"""
import os
import unittest

from core.cleaner import clean_domain_entry
from core.patcher import _parse_patch_line

_SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class CleanDomainEntryTest(unittest.TestCase):
    def test_prefix_and_typed_semantics(self):
        self.assertEqual(clean_domain_entry("+.example.com"), ("domain_suffix", "example.com"))
        self.assertEqual(clean_domain_entry(".example.com"), ("domain_suffix", "example.com"))
        self.assertEqual(clean_domain_entry("example.com"), ("domain", "example.com"))
        self.assertEqual(clean_domain_entry("DOMAIN-SUFFIX,Example.COM"),
                         ("domain_suffix", "example.com"))
        self.assertEqual(clean_domain_entry("domain,foo.com"), ("domain", "foo.com"))
        self.assertEqual(clean_domain_entry("host-suffix,foo.com"), ("domain_suffix", "foo.com"))
        self.assertEqual(clean_domain_entry("host,foo.com"), ("domain", "foo.com"))

    def test_rejections(self):
        # 非域名桶(调用方特判) / 垃圾 / IPv4 / 通配 / 裸 TLD 不作精确域
        for line in ("", "# c", "! foo", "@@||foo.com^",
                     "DOMAIN-KEYWORD,ads", "DOMAIN-REGEX,x", "IP-CIDR,1.2.3.0/24",
                     "PROCESS-NAME,foo", "user-agent,foo",
                     "1.2.3.4", "10.0.0.0/8", "*.wild.com", "foo.com/path",
                     "foo.com:8080", "foo bar", "foo.com/x", "foo.com:80", "cn"):
            self.assertIsNone(clean_domain_entry(line), line)

    def test_normalization(self):
        self.assertEqual(clean_domain_entry("中文.com"), ("domain", "xn--fiq228c.com"))
        self.assertEqual(clean_domain_entry("example.com # 注释"),
                         ("domain", "example.com"))
        self.assertEqual(clean_domain_entry("example.com."), ("domain", "example.com"))
        self.assertEqual(clean_domain_entry("+.cn"), ("domain_suffix", "cn"))


class PatchLineTest(unittest.TestCase):
    def test_hardened_parsing(self):
        # 11-17 加固: `+.` 前缀与行内注释此前分别带着字面 `+`/注释入库
        self.assertEqual(_parse_patch_line("+.example.com"),
                         ("rule", "domain_suffix", "example.com"))
        self.assertEqual(_parse_patch_line("example.com # 说明"),
                         ("rule", "domain_suffix", "example.com"))
        self.assertEqual(_parse_patch_line("example.com#nospace"),
                         ("rule", "domain_suffix", "example.com"))
        self.assertEqual(_parse_patch_line(".example.com"),
                         ("rule", "domain_suffix", "example.com"))

    def test_include_and_typed_rules_untouched(self):
        self.assertEqual(_parse_patch_line("include:dat:category-ai-!cn"),
                         ("include", "dat", "category-ai-!cn"))
        self.assertEqual(_parse_patch_line("exclude:dat:cn"),
                         ("exclude", "dat", "cn"))
        self.assertEqual(_parse_patch_line("full:www.example.com"),
                         ("rule", "domain", "www.example.com"))
        self.assertEqual(_parse_patch_line("regexp:ad#slot"),
                         ("rule", "domain_regex", "ad#slot"))  # regexp 值合法含 #


class AISourceTripwireTest(unittest.TestCase):
    """AI 上游格式绊线: 零 `domain:`/`full:` 等冒号前缀行 — 若上游引入,
    本测试红, 强制先裁决 mosdns(suffix)/sing-box(exact) 语义再改
    parse_ai_rule_line(当前四源实测零命中, 该分支为死路径)。"""

    @staticmethod
    def _cached_or_fetch(name, url):
        cache_dir = os.path.join(_SCRIPTS, "..", ".tmp-equiv")
        os.makedirs(cache_dir, exist_ok=True)
        cache = os.path.join(cache_dir, name + ".txt")
        if os.path.exists(cache):
            with open(cache, encoding="utf-8", errors="replace") as f:
                return f.read().splitlines()
        try:
            import urllib.request
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            lines = urllib.request.urlopen(req, timeout=30).read().decode(
                "utf-8", errors="replace").splitlines()
            with open(cache, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            return lines
        except Exception as e:
            print(f"  [equiv] {name} 拉取失败跳过: {e}")
            return None

    def test_ai_sources_no_domain_prefix(self):
        cache_dir = os.path.join(_SCRIPTS, "..", ".tmp-equiv")
        os.makedirs(cache_dir, exist_ok=True)
        ai_urls = [
            ("ai_meta", "https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/meta/geo/geosite/category-ai-!cn.list"),
            ("ai_dustin", "https://raw.githubusercontent.com/DustinWin/ruleset_geodata/mihomo-ruleset/ai.list"),
            ("ai_magic", "https://magicrule.pages.dev/data/_shared/artifacts/GlobalAI_rules_7591fffa97b1e679.list"),
        ]
        compared = 0
        for name, url in ai_urls:
            lines = self._cached_or_fetch(name, url)
            if lines is None:
                continue
            colon = [l for l in lines
                     if l.strip().lower().startswith(("domain:", "full:", "keyword:", "regexp:"))]
            self.assertFalse(colon, f"{name} 出现冒号前缀行(上游格式变更, 先裁决语义): {colon[:3]}")
            compared += 1
        self.assertTrue(compared >= 2, f"AI 源参与不足: {compared}")


if __name__ == "__main__":
    unittest.main()
