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
		OutputPrefix    string   `yaml:"output_prefix"`
		Targets         []string `yaml:"targets"`
		Sources         []string `yaml:"sources"`
		AllowLists      []string `yaml:"allowlists"`
		LocalAllowLists []string `yaml:"local_allowlists"`
	} `yaml:"rule_sets"`
}

// 内部处理用的记录结构
type domainRecord struct {
	pureDomain string   // 清洗后的纯域名 (e.g. "baidu.com")
	isWildcard bool     // 是否为通配符 (true: "+.baidu.com", false: "baidu.com")
	parts      []string // 倒序切分用于排序 (e.g. ["com", "baidu"])
}

// ---------------- 主函数 ----------------

func main() {
	// 1. 初始化
	fmt.Println("📖 [Init] 读取配置文件 config.yaml...")
	data, err := os.ReadFile("config.yaml")
	if err != nil {
		panic(fmt.Sprintf("读取配置失败: %v", err))
	}
	var cfg Config
	if err := yaml.Unmarshal(data, &cfg); err != nil {
		panic(fmt.Sprintf("解析配置失败: %v", err))
	}

	rand.Seed(time.Now().UnixNano())

	// 创建输出目录结构
	dirs := []string{"mihomo", "adg", "mosdns-x"}
	for _, d := range dirs {
		os.MkdirAll(fmt.Sprintf("%s/%s", cfg.Settings.OutputDir, d), 0755)
	}

	// 2. 遍历处理规则集
	for _, ruleSet := range cfg.RuleSets {
		fmt.Printf("\n🚀 [Processing] %s (Type: %s)\n", ruleSet.Name, ruleSet.Type)

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
			// 预分配 Map 减少扩容开销
			allowMap = make(map[string]bool, len(rawAllows))
			for _, l := range rawAllows {
				// 白名单也走同样的清洗逻辑
				d, _ := normalizeDomain(l)
				if d != "" {
					allowMap[d] = true
					allowList = append(allowList, d)
				}
			}
			fmt.Printf("   🛡️  [Allow] 白名单: %d\n", len(allowMap))
		}

		// B. 下载黑名单
		blockLines := parallelDownload(ruleSet.Sources)
		fmt.Printf("   ⬇️  [Download] 原始行数: %d\n", len(blockLines))

		// C. 构建黑名单记录 (同时执行清洗、IP剔除、基础去重)
		// 预估容量，减少切片扩容
		records := make([]domainRecord, 0, len(blockLines))
		seen := make(map[string]bool, len(blockLines)) // "pure|isWildcard"

		for _, line := range blockLines {
			// 1. 特殊源清洗逻辑
			if ruleSet.Type == "fakeip" {
				if strings.Contains(line, "fake-ip-filter:") || strings.Contains(line, "dns:") {
					continue
				}
				line = strings.TrimLeft(line, "- ")
				line = strings.Trim(line, "\"' ")
			}
			// 2. 剔除 skk.moe 自身域名
			if strings.Contains(line, "skk.moe") {
				continue
			}

			// 3. 核心清洗
			pure, isWildcard := normalizeDomain(line)

			// 4. 有效性检查：非空、不在白名单中
			if pure == "" || allowMap[pure] {
				continue
			}

			// 5. 唯一性检查
			key := fmt.Sprintf("%s|%t", pure, isWildcard)
			if !seen[key] {
				seen[key] = true
				
				// 预处理倒序 parts (供后续 smartDedup 使用)
				parts := strings.Split(pure, ".")
				reverseSlice(parts)

				records = append(records, domainRecord{
					pureDomain: pure,
					isWildcard: isWildcard,
					parts:      parts,
				})
			}
		}

		// D. 双向白名单清洗 (父杀子 & 子杀父)
		records = resolveConflicts(records, allowMap, allowList)
		fmt.Printf("   🧹 [Clean] 清洗后剩余: %d\n", len(records))

		// E. 智能去重 (核心：倒序排序 + 通配符覆盖)
		fmt.Println("   🧠 [Dedup] 执行智能层级去重...")
		dedupBefore := len(records)
		finalDomains := smartDedup(records)
		fmt.Printf("   📦 [Result] 最终数量: %d (优化掉 %d)\n", len(finalDomains), dedupBefore-len(finalDomains))

		// F. DNS 检测 (仅对 reject 类型)
		if cfg.Settings.DNSCheck && ruleSet.Type == "reject" {
			fmt.Printf("   🔍 [DNS] 执行死链检测 (池: %d, 并发: %d)...\n", len(cfg.Settings.DNSServers), cfg.Settings.Concurrency)
			checkBefore := len(finalDomains)
			finalDomains = filterDeadDomainsSafe(finalDomains, cfg.Settings.DNSServers, cfg.Settings.Concurrency)
			fmt.Printf("   ✅ [DNS] 检测完成: %d -> %d (移除 %d 个)\n", checkBefore, len(finalDomains), checkBefore-len(finalDomains))
		}

		// G. 输出
		for _, target := range ruleSet.Targets {
			switch target {
			case "mihomo":
				txtPath := fmt.Sprintf("%s/mihomo/%s.txt", cfg.Settings.OutputDir, ruleSet.Name)
				// 使用配置中的 OutputPrefix (如 "+.")
				saveTextFile(txtPath, finalDomains, ruleSet.OutputPrefix, "")
				
				mrsPath := fmt.Sprintf("%s/mihomo/%s.mrs", cfg.Settings.OutputDir, ruleSet.Name)
				cmd := exec.Command(cfg.Settings.MihomoBin, "convert-ruleset", "domain", "text", txtPath, mrsPath)
				if err := cmd.Run(); err != nil {
					fmt.Printf("   ⚠️  Mihomo 编译失败: %v\n", err)
				}

			case "adguard":
				path := fmt.Sprintf("%s/adg/%s_adg.txt", cfg.Settings.OutputDir, ruleSet.Name)
				saveTextFile(path, finalDomains, "", "adguard")

			case "mosdns":
				path := fmt.Sprintf("%s/mosdns-x/ad_domain_list.txt", cfg.Settings.OutputDir)
				saveTextFile(path, finalDomains, "", "")
			}
		}
	}
}

// ---------------- 核心算法 ----------------

// 1. 域名标准化 (严格复刻 Shell 脚本逻辑)
func normalizeDomain(line string) (string, bool) {
	// bash: tr -d '\r' | sed ...
	line = strings.TrimSpace(line)
	if line == "" { return "", false }
	
	// 去除注释
	if idx := strings.IndexAny(line, "#$"); idx != -1 {
		line = line[:idx]
	}
	
	// AdBlock 修饰符剔除
	if strings.HasPrefix(line, "!") || strings.HasPrefix(line, "@@") {
		return "", false
	}

	// hosts 格式处理 (0.0.0.0 domain)
	if strings.HasPrefix(line, "0.0.0.0") || strings.HasPrefix(line, "127.0.0.1") {
		fields := strings.Fields(line)
		if len(fields) >= 2 {
			line = fields[1]
		} else {
			return "", false
		}
	}

	// 识别通配符意图
	isWildcard := false

	// AdGuard: ||domain^ -> wildcard
	if strings.HasPrefix(line, "||") {
		isWildcard = true
		line = strings.TrimPrefix(line, "||")
		line = strings.TrimSuffix(line, "^")
	}
	
	// Clash/Mihomo 格式处理
	lower := strings.ToLower(line)
	if strings.HasPrefix(lower, "domain-suffix,") {
		isWildcard = true
		line = line[14:] 
	} else if strings.HasPrefix(lower, "domain,") {
		isWildcard = false // 精确匹配
		line = line[7:]    
	} else if strings.HasPrefix(lower, "domain-keyword,") {
		isWildcard = true 
		line = line[15:]
	}

	// 清理残留符号
	line = strings.ReplaceAll(line, "|", "")
	line = strings.ReplaceAll(line, "^", "")

	// 取逗号前的内容
	if idx := strings.Index(line, ","); idx != -1 {
		line = line[:idx]
	}

	// 再次检查前缀 (脚本逻辑: s/^\+\.//; s/^\.//)
	if strings.HasPrefix(line, "+.") {
		isWildcard = true
		line = line[2:]
	} else if strings.HasPrefix(line, ".") {
		isWildcard = true
		line = line[1:]
	}
	line = strings.TrimSuffix(line, ".")

	line = strings.TrimSpace(line)
	
	// 【关键】IP 地址检查：如果是 IP，直接丢弃
	if net.ParseIP(line) != nil {
		return "", false
	}
	
	// 合法性检查
	if line == "" || !strings.Contains(line, ".") || strings.Contains(line, "/") {
		return "", false
	}

	return strings.ToLower(line), isWildcard
}

// 2. 智能去重 (严格复刻 Python optimize_smart_self)
// 逻辑：排序后，仅当父域名 isWildcard=true 时才覆盖子域名
func smartDedup(records []domainRecord) []string {
	// 排序逻辑复刻 Python: (parts, not is_wildcard)
	sort.Slice(records, func(i, j int) bool {
		// 1. 比较 parts (字典序)
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
		// 2. parts 相同，Wildcard 优先 (True < False)
		// Python: not True(0) < not False(1)
		if records[i].isWildcard != records[j].isWildcard {
			return records[i].isWildcard && !records[j].isWildcard
		}
		return false
	})

	var final []string
	if len(records) == 0 { return final }

	var lastRoot []string
	
	for _, item := range records {
		curr := item.parts
		isCovered := false

		if lastRoot != nil {
			// 检查前缀匹配 (即子域名关系)
			if len(curr) >= len(lastRoot) {
				match := true
				for k := 0; k < len(lastRoot); k++ {
					if curr[k] != lastRoot[k] {
						match = false
						break
					}
				}
				if match {
					isCovered = true
				}
			}
		}

		if !isCovered {
			final = append(final, item.pureDomain)
			
			// 【核心逻辑】
			// 只有当父域名是 Wildcard (如 +.net.cn) 时，才设置为 root，覆盖后续子域名
			// 普通域名 (如 net.cn) 不会覆盖子域名 (如 cdn.net.cn)
			if item.isWildcard {
				lastRoot = curr
			} else {
				lastRoot = nil
			}
		}
	}
	
	sort.Strings(final)
	return final
}

// 3. 双向冲突解决
func resolveConflicts(records []domainRecord, allowMap map[string]bool, allowList []string) []domainRecord {
	// 优化：预先构建需要删除的父域名集合
	toRemove := make(map[string]bool)

	// 子杀父逻辑: 遍历白名单，找出所有需要在黑名单中删除的父级
	for _, allowed := range allowList {
		parts := strings.Split(allowed, ".")
		for i := 0; i < len(parts); i++ {
			parent := strings.Join(parts[i:], ".")
			toRemove[parent] = true
		}
	}

	var cleaned []domainRecord
	for _, rec := range records {
		domain := rec.pureDomain
		
		// 检查1: 是否命中 "子杀父"
		if toRemove[domain] {
			continue
		}

		// 检查2: 父杀子
		// 检查当前域名的所有父级是否在白名单中
		parts := strings.Split(domain, ".")
		isAllowed := false
		for i := 0; i < len(parts); i++ {
			parent := strings.Join(parts[i:], ".")
			if allowMap[parent] {
				isAllowed = true
				break
			}
		}
		if isAllowed {
			continue
		}

		cleaned = append(cleaned, rec)
	}
	return cleaned
}

// 4. DNS 检测 (带重试机制的负载均衡)
func filterDeadDomainsSafe(domains []string, servers []string, concurrency int) []string {
	if len(servers) == 0 { servers = []string{"8.8.8.8:53"} }
	var wg sync.WaitGroup
	aliveChan := make(chan string, len(domains))
	sem := make(chan struct{}, concurrency)

	// 单次检测工具函数
	check := func(domain, server string) bool {
		resolver := &net.Resolver{
			PreferGo: true,
			Dial: func(ctx context.Context, network, address string) (net.Conn, error) {
				d := net.Dialer{Timeout: 2 * time.Second} // 连接超时
				return d.Dial("udp", server)
			},
		}
		ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second) // 查询超时
		defer cancel()
		_, err := resolver.LookupHost(ctx, domain)
		return err == nil
	}

	for _, d := range domains {
		wg.Add(1)
		go func(domain string) {
			defer wg.Done()
			sem <- struct{}{}
			defer func() { <-sem }()
			
			// 策略：随机选两个不同的 DNS 尝试，只要有一个成功即保留
			// 这能极大减少因单一 DNS 抖动导致的误杀
			for i := 0; i < 2; i++ {
				srv := servers[rand.Intn(len(servers))]
				if check(domain, srv) {
					aliveChan <- domain
					return
				}
			}
		}(d)
	}
	wg.Wait()
	close(aliveChan)
	
	var alive []string
	for d := range aliveChan { alive = append(alive, d) }
	sort.Strings(alive)
	return alive
}

// 辅助: 并发下载 (增加 User-Agent 防止被拒)
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

			req, _ := http.NewRequest("GET", u, nil)
			req.Header.Set("User-Agent", "Mozilla/5.0 (compatible; RuleBuilder/1.0)")
			
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

// 辅助: 切片反转
func reverseSlice(s []string) {
	for i, j := 0, len(s)-1; i < j; i, j = i+1, j-1 {
		s[i], s[j] = s[j], s[i]
	}
}

// 辅助: 保存文件
func saveTextFile(path string, lines []string, prefix string, format string) {
	f, _ := os.Create(path)
	defer f.Close()
	w := bufio.NewWriter(f)
	w.WriteString(fmt.Sprintf("# Updated: %s\n", time.Now().Format("2006-01-02 15:04:05")))
	w.WriteString(fmt.Sprintf("# Count: %d\n", len(lines)))
	for _, l := range lines {
		if format == "adguard" {
			w.WriteString(fmt.Sprintf("||%s^\n", l))
		} else {
			w.WriteString(prefix + l + "\n")
		}
	}
	w.Flush()
}
