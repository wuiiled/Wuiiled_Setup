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

    @staticmethod
    def _new_buckets(lines, skip_skk_watermark=False):
        new_sfx, new_dom = set(), set()
        for l in lines:
            if skip_skk_watermark and "skk.moe" in l.lower():
                continue  # 真实管线 stage1 (rd_lines) 先过滤水印行
            p = clean_domain_entry(l)
            if p:
                (new_sfx if p[0] == "domain_suffix" else new_dom).add(p[1])
        return new_sfx, new_dom

    def _assert_equiv(self, name, lines, old, new_sfx, new_dom):
        # 允许 IDNA: 统一入口在装载期 punycode 化, 旧管线在 main.py 阶段 2c
        # 全局转换 — 终点一致, 只是时机提前
        from core.cleaner import idna_domain
        old_low = {x.lower() for x in old} | {idna_domain(x).lower() for x in old}
        invented = sorted((new_sfx | new_dom) - old_low)
        dropped = sorted(x for x in old_low - (new_sfx | new_dom))
        self.assertFalse(
            invented,
            f"{name}: 统一入口发明了旧逻辑没有的产出: {invented[:5]}")
        print(f"  [equiv] {name}: old={len(old_low)} "
              f"new={len(new_sfx) + len(new_dom)} 旧收新拒(垃圾)={len(dropped)} "
              f"{dropped[:5]}")

    def _cached_or_fetch(self, name, url):
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

    def test_real_sources_equivalence(self):
        cache_dir = os.path.join(_SCRIPTS, "..", ".tmp-equiv")
        compared = 0

        # pcdn / skk (远程缓存)
        for name, url in (
                ("pcdn", "https://raw.githubusercontent.com/wuiiled/PCDN-mihomo-list/main/pcdn.list"),
                ("skk_ali", "https://ruleset.skk.moe/Internal/mihomo_nameserver_policy/alibaba.txt")):
            lines = self._cached_or_fetch(name, url)
            if lines is None:
                continue
            old = set()
            for l in lines:
                m = self._old_loader_line(l)
                if m:
                    old.add(m[1])
            new_sfx, new_dom = self._new_buckets(lines)
            self._assert_equiv(name, lines, old, new_sfx, new_dom)
            compared += 1

        # rejectdrop (远程缓存 + stage1 skk.moe 水印过滤)
        lines = self._cached_or_fetch(
            "rejectdrop", "https://ruleset.skk.moe/Clash/non_ip/reject-drop.txt")
        if lines is not None:
            old, old_lines = set(), []
            for l in lines:
                if "skk.moe" in l.lower():
                    continue
                m = self._old_loader_line(l)
                if m:
                    old.add(m[1])
                old_lines.append(l)
            new_sfx, new_dom = self._new_buckets(old_lines, skip_skk_watermark=True)
            self._assert_equiv("rejectdrop", old_lines, old, new_sfx, new_dom)
            compared += 1

        # iptv (Gary/Cathy 真源: IP 分流在前, 域名走新旧两版逻辑)
        iptv_lines = []
        for n in ("gary", "cathy"):
            p = os.path.join(os.path.dirname(_SCRIPTS), ".tmp-awavenue", n + ".txt")
            alt = os.path.join(cache_dir, "iptv_" + n + ".txt")
            if os.path.exists(p):
                iptv_lines += open(p, encoding="utf-8", errors="replace").read().splitlines()
            elif os.path.exists(alt):
                iptv_lines += open(alt, encoding="utf-8", errors="replace").read().splitlines()
            else:
                got = self._cached_or_fetch(
                    "iptv_" + n,
                    f"https://raw.githubusercontent.com/marcuccilli/{n.capitalize() if n == 'cathy' else 'gary'}/main/{'cathy_surge' if n == 'cathy' else 'iptv_surge'}.list")
                if got is not None:
                    iptv_lines += got
        if iptv_lines:
            old, dom_lines = set(), []
            for l in iptv_lines:
                l = l.strip()
                if not l or l.startswith("#"):
                    continue
                if l.startswith(("IP-CIDR,", "IP-CIDR6,", "IP6-CIDR,")):
                    continue  # IP 分支在 clean_domain_entry 之前, 本次未改动
                dom_lines.append(l)
                m = self._old_loader_line(l)
                if m:
                    old.add(m[1])
            new_sfx, new_dom = self._new_buckets(dom_lines)
            self._assert_equiv("iptv", dom_lines, old, new_sfx, new_dom)
            compared += 1

        # custom (本地 rules/Custom_*.txt; _SCRIPTS 在本测试 = 仓库根)
        import providers
        custom_lines = []
        for name, rel in providers.CUSTOM_RULES.items():
            if name.startswith("geoip-"):
                continue  # IP 分支未改动
            p = os.path.join(_SCRIPTS, rel)
            if os.path.exists(p):
                for l in open(p, encoding="utf-8", errors="replace").read().splitlines():
                    custom_lines.append((name, l))
        if custom_lines:
            old_by, new_by = {}, {}
            for name, l in custom_lines:
                m = self._old_loader_line(l)
                if m:
                    old_by.setdefault(name, set()).add(m[1])
                p = clean_domain_entry(l)
                if p:
                    new_by.setdefault(name, set()).add(p[1])
            for name in sorted(new_by):
                self._assert_equiv(f"custom/{name}", custom_lines,
                                   old_by.get(name, set()), new_by[name], set())
                compared += 1

        self.assertTrue(compared >= 3, f"参与对拍的源不足: {compared}")

    def test_ai_sources_no_domain_prefix_and_parse_stable(self):
        """AI 四源: ①零 `domain:` 冒号前缀行(若上游引入 → 本测试红,
        强制先裁决 mosdns(suffix)/sing-box(exact) 语义再改 parse_ai);
        ②parse_ai_rule_line 对真实源的产出与 254171d 版本逐桶一致。"""
        cache_dir = os.path.join(_SCRIPTS, "..", ".tmp-equiv")
        os.makedirs(cache_dir, exist_ok=True)
        from core.cleaner import parse_ai_rule_line
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


if __name__ == "__main__":
    unittest.main()
