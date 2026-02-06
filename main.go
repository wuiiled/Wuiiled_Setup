package main

import (
	"bufio"
	"context"
	"fmt"
	"math/rand"
	"net"
	"net/http"
	"os"
	"os/exec"
	"regexp"
	"sort"
	"strings"
	"sync"
	"time"

	"gopkg.in/yaml.v3"
)

// ---------------- 结构体定义 ----------------

type Config struct {
	Settings struct {
		OutputDir   string   `yaml:"output_dir"`
		MihomoBin   string   `yaml:"mihomo_bin"`
		DNSCheck    bool     `yaml:"dns_check"`
		DNSServers  []string `yaml:"dns_servers"`
		Concurrency int      `yaml:"concurrency"`
	} `yaml:"settings"`
	RuleSets []struct {
		Name            string   `yaml:"name"`
		Type            string   `yaml:"type"`
		OutputPolicy    string   `yaml:"output_policy"` // force_wildcard | respect_wildcard
		Targets         []string `yaml:"targets"`
		Sources         []string `yaml:"sources"`
		AllowLists      []string `yaml:"allowlists"`
		LocalAllowLists []string `yaml:"local_allowlists"`
	} `yaml:"rule_sets"`
}

type domainRecord struct {
	pureDomain string
	isWildcard bool
	parts      []string
}

// ---------------- 主函数 ----------------

func main() {
	fmt.Println("📖 [Init] 读取配置文件 config.yaml...")
	data, err := os.ReadFile("config.yaml")
	if err != nil { panic(err) }
	var cfg Config
	if err := yaml.Unmarshal(data, &cfg); err != nil { panic(err) }
	rand.Seed(time.Now().UnixNano())

	dirs := []string{"mihomo", "adg", "mosdns-x"}
	for _, d := range dirs { os.MkdirAll(fmt.Sprintf("%s/%s", cfg.Settings.OutputDir, d), 0755) }

	for _, ruleSet := range cfg.RuleSets {
		fmt.Printf("\n🚀 [Processing] %s (Type: %s, Policy: %s)\n", ruleSet.Name, ruleSet.Type, ruleSet.OutputPolicy)

		// A. 准备白名单
		allowMap := make(map[string]bool)
		var allowList []string
		if len(ruleSet.AllowLists) > 0 || len(ruleSet.LocalAllowLists) > 0 {
			rawAllows := parallelDownload(ruleSet.AllowLists)
			for _, f := range ruleSet.LocalAllowLists {
				if c, err := os.ReadFile(f); err == nil {
					rawAllows = append(rawAllows, strings.Split(string(c), "\n")...)
				}
			}
			for _, l := range rawAllows {
				d, _ := normalizeGeneric(l)
				// 白名单必须是合法域名
				if d != "" && isValidDomain(d) {
					allowMap[d] = true
					allowList = append(allowList, d)
				}
			}
			fmt.Printf("   🛡️  [Allow] 白名单: %d\n", len(allowMap))
		}

		// B. 下载
		blockLines := parallelDownload(ruleSet.Sources)
		fmt.Printf("   ⬇️  [Download] 原始行数: %d\n", len(blockLines))

		// C. 构建记录
		records := make([]domainRecord, 0, len(blockLines))
		seen := make(map[string]bool, len(blockLines))

		for _, line := range blockLines {
			var pure string
			var isWildcard bool

			// 1. 分流清洗
			switch ruleSet.Name {
			case "Fake_IP_Filter_merged":
				pure, isWildcard = normalizeFakeIP(line)
			case "CN_merged":
				pure, isWildcard = normalizeCN(line)
			case "Reject_Drop_merged":
				pure, isWildcard = normalizeRejectDrop(line)
			default:
				pure, isWildcard = normalizeGeneric(line)
			}

			// 2. 强校验
			if pure == "" || !isValidDomain(pure) { continue }
			
			// 3. 白名单过滤
			if allowMap[pure] { continue }

			// 【关键修复】如果策略是强制通配，则忽略源文件属性，强制设为 True
			// 这样在去重时，baidu.com (isWildcard=true) 就能覆盖 ad.baidu.com
			if ruleSet.OutputPolicy == "force_wildcard" {
				isWildcard = true
			}

			// 4. 去重
			key := fmt.Sprintf("%s|%t", pure, isWildcard)
			if !seen[key] {
				seen[key] = true
				parts := strings.Split(pure, ".")
				reverseSlice(parts)
				records = append(records, domainRecord{pure, isWildcard, parts})
			}
		}

		// D. 双向清洗
		records = resolveConflicts(records, allowMap, allowList)
		fmt.Printf("   🧹 [Clean] 清洗后剩余: %d\n", len(records))

		// E. 智能去重
		fmt.Println("   🧠 [Dedup] 执行智能层级去重...")
		dedupBefore := len(records)
		finalRecords := smartDedup(records)
		fmt.Printf("   📦 [Result] 最终数量: %d (减少 %d)\n", len(finalRecords), dedupBefore-len(finalRecords))

		// F. DNS 检测 (仅对 reject 类型)
		if cfg.Settings.DNSCheck && ruleSet.Type == "reject" {
			fmt.Printf("   🔍 [DNS] 执行死链检测 (池: %d, 并发: %d)...\n", len(cfg.Settings.DNSServers), cfg.Settings.Concurrency)
			checkBefore := len(finalRecords)
			finalRecords = filterDeadDomainsSafe(finalRecords, cfg.Settings.DNSServers, cfg.Settings.Concurrency)
			fmt.Printf("   ✅ [DNS] 检测完成: %d -> %d\n", checkBefore, len(finalRecords))
		}

		// G. 输出
		for _, target := range ruleSet.Targets {
			switch target {
			case "mihomo":
				txtPath := fmt.Sprintf("%s/mihomo/%s.txt", cfg.Settings.OutputDir, ruleSet.Name)
				// 传递 OutputPolicy 给保存函数
				saveTextFile(txtPath, finalRecords, ruleSet.OutputPolicy, "")
				
				mrsPath := fmt.Sprintf("%s/mihomo/%s.mrs", cfg.Settings.OutputDir, ruleSet.Name)
				cmd := exec.Command(cfg.Settings.MihomoBin, "convert-ruleset", "domain", "text", txtPath, mrsPath)
				cmd.Run()
			case "adguard":
				path := fmt.Sprintf("%s/adg/%s_adg.txt", cfg.Settings.OutputDir, ruleSet.Name)
				saveTextFile(path, finalRecords, "", "adguard")
			case "mosdns":
				path := fmt.Sprintf("%s/mosdns-x/ad_domain_list.txt", cfg.Settings.OutputDir)
				saveTextFile(path, finalRecords, "", "")
			}
		}
	}
}

// ---------------- 强校验 ----------------
// 允许数字开头的域名(如163.com)，但不允许纯IP
var validDomainRegex = regexp.MustCompile(`^([a-zA-Z0-9_]([a-zA-Z0-9-_]{0,61}[a-zA-Z0-9_])?\.)+[a-zA-Z]{2,63}$`)

func isValidDomain(domain string) bool {
	if strings.Contains(domain, "*") { return false } // Mihomo不支持*
	// 简单的长度和字符检查
	if len(domain) > 253 { return false }
	if net.ParseIP(domain) != nil { return false } // 剔除IP
	if strings.ContainsAny(domain, "/%:\\") { return false }
	return true
}

// ---------------- 定制清洗 ----------------

// 1. Generic (ADS/AI)
func normalizeGeneric(line string) (string, bool) {
	line = strings.TrimSpace(line)
	if strings.HasPrefix(line, "#") || line == "" { return "", false }
	if idx := strings.IndexAny(line, "#$"); idx != -1 { line = line[:idx] }
	
	if strings.HasPrefix(line, "0.0.0.0") || strings.HasPrefix(line, "127.0.0.1") {
		f := strings.Fields(line)
		if len(f) >= 2 { line = f[1] } else { return "", false }
	}

	isWildcard := false
	if strings.HasPrefix(line, "||") {
		isWildcard = true; line = strings.TrimPrefix(line, "||"); line = strings.TrimSuffix(line, "^")
	} else if strings.HasPrefix(strings.ToLower(line), "domain-suffix,") {
		isWildcard = true; line = line[14:]
	} else if strings.HasPrefix(line, "+.") {
		isWildcard = true; line = line[2:]
	} else if strings.HasPrefix(line, ".") {
		isWildcard = true; line = line[1:]
	}

	if idx := strings.Index(line, ","); idx != -1 { line = line[:idx] }
	line = strings.TrimSpace(line)
	return strings.ToLower(line), isWildcard
}

// 2. FakeIP: 增强解析
func normalizeFakeIP(line string) (string, bool) {
	line = strings.TrimSpace(line)
	if line == "" || strings.HasPrefix(line, "#") { return "", false }
	if strings.HasPrefix(line, "dns:") || strings.HasPrefix(line, "fake-ip-filter:") { return "", false }
	
	// 处理yaml列表符: "- +.lan"
	line = strings.TrimPrefix(line, "-")
	line = strings.TrimSpace(line)
	// 去除引号
	line = strings.ReplaceAll(line, "'", "")
	line = strings.ReplaceAll(line, "\"", "")
	
	isWildcard := false
	if strings.HasPrefix(line, "+.") {
		isWildcard = true; line = line[2:]
	} else if strings.HasPrefix(line, ".") {
		isWildcard = true; line = line[1:]
	}
	
	return strings.ToLower(line), isWildcard
}

// 3. CN: 智能判断
func normalizeCN(line string) (string, bool) {
	line = strings.TrimSpace(line)
	if line == "" || strings.HasPrefix(line, "#") { return "", false }
	if strings.Contains(line, "skk.moe") { return "", false }

	isWildcard := false
	if strings.Contains(line, ",") {
		// Clash规则
		lower := strings.ToLower(line)
		if strings.HasPrefix(lower, "domain-suffix,") {
			isWildcard = true; line = line[14:]
		} else if strings.HasPrefix(lower, "domain,") {
			line = line[7:]
		}
		if idx := strings.Index(line, ","); idx != -1 { line = line[:idx] }
	} else {
		// 纯域名列表 -> 默认为通配符 (如Shell逻辑 s/^/+./)
		isWildcard = true
		if strings.HasPrefix(line, "+.") { line = line[2:] }
	}
	return strings.ToLower(strings.TrimSpace(line)), isWildcard
}

// 4. RejectDrop
func normalizeRejectDrop(line string) (string, bool) {
	return normalizeCN(line)
}

// ---------------- 辅助函数 ----------------

func smartDedup(records []domainRecord) []domainRecord {
	// 排序：先按 parts 字典序，parts 相同则 Wildcard 在前
	sort.Slice(records, func(i, j int) bool {
		minLen := len(records[i].parts)
		if len(records[j].parts) < minLen { minLen = len(records[j].parts) }
		for k := 0; k < minLen; k++ {
			if records[i].parts[k] != records[j].parts[k] {
				return records[i].parts[k] < records[j].parts[k]
			}
		}
		if len(records[i].parts) != len(records[j].parts) {
			return len(records[i].parts) < len(records[j].parts)
		}
		// True < False? No. We want True first. 
		// Go sort expects "Less". 
		// If i=True, j=False. Is True < False? 
		// Let's definte True < False for this sort.
		if records[i].isWildcard != records[j].isWildcard {
			return records[i].isWildcard // True(Wildcard) comes first
		}
		return false
	})

	var final []domainRecord
	if len(records) == 0 { return final }
	var lastRoot []string
	
	for _, item := range records {
		curr := item.parts
		isCovered := false
		if lastRoot != nil {
			if len(curr) >= len(lastRoot) {
				match := true
				for k := 0; k < len(lastRoot); k++ {
					if curr[k] != lastRoot[k] { match = false; break }
				}
				if match { isCovered = true }
			}
		}
		if !isCovered {
			final = append(final, item)
			// 只有 Wildcard 才能成为根，覆盖后面的子域名
			if item.isWildcard { lastRoot = curr } else { lastRoot = nil }
		}
	}
	sort.Slice(final, func(i, j int) bool { return final[i].pureDomain < final[j].pureDomain })
	return final
}

func resolveConflicts(records []domainRecord, allowMap map[string]bool, allowList []string) []domainRecord {
	toRemove := make(map[string]bool)
	for _, allowed := range allowList {
		parts := strings.Split(allowed, ".")
		for i := 0; i < len(parts); i++ {
			parent := strings.Join(parts[i:], ".")
			toRemove[parent] = true
		}
	}
	var cleaned []domainRecord
	for _, rec := range records {
		if toRemove[rec.pureDomain] { continue }
		parts := strings.Split(rec.pureDomain, ".")
		isAllowed := false
		for i := 0; i < len(parts); i++ {
			parent := strings.Join(parts[i:], ".")
			if allowMap[parent] { isAllowed = true; break }
		}
		if isAllowed { continue }
		cleaned = append(cleaned, rec)
	}
	return cleaned
}

func filterDeadDomainsSafe(records []domainRecord, servers []string, concurrency int) []domainRecord {
	if len(servers) == 0 { servers = []string{"8.8.8.8:53"} }
	var wg sync.WaitGroup
	aliveChan := make(chan domainRecord, len(records))
	sem := make(chan struct{}, concurrency)
	check := func(domain, server string) bool {
		resolver := &net.Resolver{
			PreferGo: true,
			Dial: func(ctx context.Context, network, address string) (net.Conn, error) {
				d := net.Dialer{Timeout: 2 * time.Second}
				return d.Dial("udp", server)
			},
		}
		ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
		defer cancel()
		_, err := resolver.LookupHost(ctx, domain)
		return err == nil
	}
	for _, rec := range records {
		wg.Add(1)
		go func(r domainRecord) {
			defer wg.Done()
			sem <- struct{}{}
			defer func() { <-sem }()
			for i := 0; i < 2; i++ {
				srv := servers[rand.Intn(len(servers))]
				if check(r.pureDomain, srv) { aliveChan <- r; return }
			}
		}(rec)
	}
	wg.Wait()
	close(aliveChan)
	var alive []domainRecord
	for r := range aliveChan { alive = append(alive, r) }
	sort.Slice(alive, func(i, j int) bool { return alive[i].pureDomain < alive[j].pureDomain })
	return alive
}

func parallelDownload(urls []string) []string {
	var wg sync.WaitGroup
	resultChan := make(chan []string, len(urls))
	limitChan := make(chan struct{}, 8)
	for _, url := range urls {
		wg.Add(1)
		go func(u string) {
			defer wg.Done()
			limitChan <- struct{}{}
			defer func() { <-limitChan }()
			req, _ := http.NewRequest("GET", url, nil)
			req.Header.Set("User-Agent", "Mozilla/5.0")
			client := &http.Client{Timeout: 30 * time.Second}
			resp, err := client.Do(req)
			if err != nil { return }
			defer resp.Body.Close()
			var lines []string
			scanner := bufio.NewScanner(resp.Body)
			for scanner.Scan() { lines = append(lines, scanner.Text()) }
			resultChan <- lines
		}(url)
	}
	wg.Wait()
	close(resultChan)
	var all []string
	for slice := range resultChan { all = append(all, slice...) }
	return all
}

func reverseSlice(s []string) {
	for i, j := 0, len(s)-1; i < j; i, j = i+1, j-1 { s[i], s[j] = s[j], s[i] }
}

func saveTextFile(path string, records []domainRecord, policy string, format string) {
	f, _ := os.Create(path)
	defer f.Close()
	w := bufio.NewWriter(f)
	w.WriteString(fmt.Sprintf("# Updated: %s\n", time.Now().Format("2006-01-02 15:04:05")))
	w.WriteString(fmt.Sprintf("# Count: %d\n", len(records)))
	
	for _, rec := range records {
		if format == "adguard" {
			w.WriteString(fmt.Sprintf("||%s^\n", rec.pureDomain))
		} else {
			if policy == "force_wildcard" {
				w.WriteString("+." + rec.pureDomain + "\n")
			} else if policy == "respect_wildcard" {
				if rec.isWildcard {
					w.WriteString("+." + rec.pureDomain + "\n")
				} else {
					w.WriteString(rec.pureDomain + "\n")
				}
			} else {
				w.WriteString(rec.pureDomain + "\n")
			}
		}
	}
	w.Flush()
}
