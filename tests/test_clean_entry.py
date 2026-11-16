# -*- coding: utf-8 -*-
"""11-17 全量审计收口测试: clean_domain_entry 统一入口 + patcher 行解析加固。"""
import os
import unittest

from core.cleaner import clean_domain_entry, clean_mihomo_domain_line
from core.patcher import _parse_patch_line

_SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class CleanDomainEntryTest(unittest.TestCase):
    def test_prefix_semantics(self):
        self.assertEqual(clean_domain_entry("+.example.com"), ("domain_suffix", "example.com"))
        self.assertEqual(clean_domain_entry(".example.com"), ("domain_suffix", "example.com"))
        self.assertEqual(clean_domain_entry("example.com"), ("domain", "example.com"))
        self.assertEqual(clean_domain_entry("example.com."), ("domain", "example.com"))

    def test_typed_prefixes(self):
        self.assertEqual(clean_domain_entry("DOMAIN-SUFFIX,Example.COM"),
                         ("domain_suffix", "example.com"))
        self.assertEqual(clean_domain_entry("domain,foo.com"), ("domain", "foo.com"))
        self.assertEqual(clean_domain_entry("host-suffix,foo.com"), ("domain_suffix", "foo.com"))
        self.assertEqual(clean_domain_entry("host,foo.com"), ("domain", "foo.com"))

    def test_non_domain_buckets_rejected(self):
        for line in ("DOMAIN-KEYWORD,ads", "DOMAIN-REGEX,x", "IP-CIDR,1.2.3.0/24",
                     "PROCESS-NAME,foo", "user-agent,foo"):
            self.assertIsNone(clean_domain_entry(line), line)

    def test_junk_rejected(self):
        for line in ("", "# comment", "! foo", "@@||foo.com^", "1.2.3.4",
                     "10.0.0.0/8", "*.wild.com", "foo.com/path", "foo.com:8080",
                     "foo bar"):
            self.assertIsNone(clean_domain_entry(line), line)
        # 行内注释是设计内剥离(与旧 loader 的 clean_mihomo 行为一致), 见下一条

    def test_single_label_tld_allowed_as_suffix_only(self):
        self.assertEqual(clean_domain_entry("+.cn"), ("domain_suffix", "cn"))
        self.assertIsNone(clean_domain_entry("cn"))  # 裸 TLD 不作精确域

    def test_idna_normalized(self):
        self.assertEqual(clean_domain_entry("中文.com"), ("domain", "xn--fiq228c.com"))

    def test_inline_comment_stripped(self):
        self.assertEqual(clean_domain_entry("example.com # 说明"),
                         ("domain", "example.com"))


class PatchLineTest(unittest.TestCase):
    def test_plus_prefix_now_accepted(self):
        # 11-17 加固: `+.` 前缀此前带着字面 `+` 入库
        self.assertEqual(_parse_patch_line("+.example.com"),
                         ("rule", "domain_suffix", "example.com"))

    def test_inline_comment_now_stripped(self):
        self.assertEqual(_parse_patch_line("example.com # 说明"),
                         ("rule", "domain_suffix", "example.com"))
        self.assertEqual(_parse_patch_line("example.com#nospace"),
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

    def test_leading_dot_still_normalized(self):
        self.assertEqual(_parse_patch_line(".example.com"),
                         ("rule", "domain_suffix", "example.com"))


class LoaderEquivalenceTest(unittest.TestCase):
    """新旧逻辑对拍: 统一入口 vs 真实旧逻辑(clean_mihomo + 各 loader 的
    手写前缀拆分)在真实源上对拍。不变量: new ⊆ old.lower() — 统一入口
    只允许"lower 归一 + 拒掉旧逻辑收进的垃圾", 不允许发明新产出。"""

    def _old_loader_line(self, line: str):
        """被替换前的真实旧逻辑: clean_mihomo_domain_line + 手写前缀拆分
        (load_pcdn/iptv/skk/custom 的原样拷贝)。"""
        cleaned = clean_mihomo_domain_line(line)
        if not cleaned or cleaned == "+.":
            return None
        if cleaned.startswith("+."):
            v = cleaned[2:].lstrip(".")
            return ("domain_suffix", v) if v else None
        if cleaned.startswith("."):
            v = cleaned[1:].lstrip(".")
            return ("domain_suffix", v) if v else None
        return ("domain", cleaned)

    def test_real_sources_equivalence(self):
        import urllib.request
        sources = {
            "pcdn": "https://raw.githubusercontent.com/wuiiled/PCDN-mihomo-list/main/pcdn.list",
            "rejectdrop": "https://ruleset.skk.moe/Clash/non_ip/reject-drop.txt",
            "skk_ali": "https://ruleset.skk.moe/Internal/mihomo_nameserver_policy/alibaba.txt",
        }
        cache_dir = os.path.join(_SCRIPTS, "..", ".tmp-equiv")
        os.makedirs(cache_dir, exist_ok=True)
        compared = 0
        for name, url in sources.items():
            cache = os.path.join(cache_dir, name + ".txt")
            if os.path.exists(cache):
                with open(cache, encoding="utf-8", errors="replace") as f:
                    lines = f.read().splitlines()
            else:
                try:
                    lines = urllib.request.urlopen(url, timeout=30).read().decode(
                        "utf-8", errors="replace").splitlines()
                    with open(cache, "w", encoding="utf-8") as f:
                        f.write("\n".join(lines))
                except Exception as e:
                    print(f"  [equiv] {name} 拉取失败跳过: {e}")
                    continue
            compared += 1
            old = set()
            for l in lines:
                if name == "rejectdrop" and "skk.moe" in l.lower():
                    continue
                m = self._old_loader_line(l)
                if m:
                    old.add(m[1])
            new = set()
            for l in lines:
                if name == "rejectdrop" and "skk.moe" in l.lower():
                    continue  # 真实管线 stage1 (rd_lines) 先过滤水印行
                p = clean_domain_entry(l)
                if p:
                    new.add(p[1])
            old_low = {x.lower() for x in old}
            invented = sorted(new - old_low)
            # 唯一允许的差异方向: new ⊆ old.lower() (lower 归一 + 拒垃圾);
            # old − new = 旧逻辑收进、新逻辑拒掉的垃圾(带空格/冒号/大小写残片)
            self.assertFalse(
                invented,
                f"{name}: 统一入口发明了旧逻辑没有的产出: {invented[:5]}")
            dropped = sorted(x for x in old_low - new)
            print(f"  [equiv] {name}: old={len(old_low)} new={len(new)} "
                  f"旧收新拒(垃圾)={len(dropped)} {dropped[:5]}")
        self.assertTrue(compared > 0, "没有任何真实源参与对拍")


if __name__ == "__main__":
    unittest.main()


if __name__ == "__main__":
    unittest.main()
