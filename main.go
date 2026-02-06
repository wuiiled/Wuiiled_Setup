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
	dirs := []string{"mihomo", "adg", "mosdns-x"} // mosdns-x 对应分支名
	for _, d := range dirs {
		os.MkdirAll(fmt.Sprintf("%s/%s", cfg.Settings.OutputDir, d), 0755)
	}

	// 2. 遍历处理规则集
	for _, ruleSet := range cfg.RuleSets {
		fmt.Printf("\n🚀 [Processing] %s (Type: %s)\n", ruleSet.Name, ruleSet.Type)

		// A. 下载并准备白名单
		allowMap := make(map[string]bool)
		allowDomainsList := []string{}
		if len(ruleSet.AllowLists) > 0 || len(ruleSet.LocalAllowLists) > 0 {
			rawAllows := parallelDownload(ruleSet.AllowLists)
			// 读取本地白名单
			for _, f := range ruleSet.LocalAllowLists {
				if c, err := os.ReadFile(f); err == nil {
					rawAllows = append(rawAllows, strings.Split(string(c), "\n")...)
				}
			}
			for _, l := range rawAllows {
				if d := normalizeDomain(l); d != "" {
					allowMap[d] = true
					allowDomainsList = append(allowDomainsList, d)
				}
			}
			fmt.Printf("   🛡️  [Allow] 白名单: %d\n", len(allowMap))
		}

		// B. 下载黑名单
		blockLines := parallelDownload(ruleSet.Sources)
		fmt.Printf("   ⬇️  [Download] 原始行数: %d\n", len(blockLines))

		// C. 构建黑名单 Map
		blockMap := make(map[string]bool)
		for _, line := range blockLines {
			// FakeIP 特殊清洗逻辑
			if ruleSet.Type == "fakeip" {
				if strings.Contains(line, "fake-ip-filter:") || strings.Contains(line, "dns:") {
					continue
				}
				line = strings.TrimLeft(line, "- ")
				line = strings.Trim(line, "\"' ")
			}
			// 剔除 skk.moe 自身域名 (保留原有逻辑)
			if strings.Contains(line, "skk.moe") {
				continue
			}

			domain := normalizeDomain(line)
			// 确保域名非空、不是IP、且不在白名单中
			if domain != "" && !allowMap[domain] {
				blockMap[domain] = true
			}
		}

		// D. 双向冲突清洗 (父杀子 & 子杀父)
		resolveConflicts(blockMap, allowMap, allowDomainsList)
		
		domains := make([]string, 0, len(blockMap))
		for d := range blockMap {
			domains = append(domains, d)
		}
		fmt.Printf("   🧹 [Clean] 清洗后剩余: %d\n", len(domains))

		// E. DNS 连通性检测 (仅对 reject 类型)
		if cfg.Settings.DNSCheck && ruleSet.Type == "reject" {
			fmt.Printf("   🔍 [DNS] 执行死链检测 (服务器池: %d个, 并发: %d)...\n", len(cfg.Settings.DNSServers), cfg.Settings.Concurrency)
			beforeCount := len(domains)
			domains = filterDeadDomainsSafe(domains, cfg.Settings.DNSServers, cfg.Settings.Concurrency)
			fmt.Printf("   ✅ [DNS] 检测完成: %d -> %d (移除 %d 个失效域名)\n", beforeCount, len(domains), beforeCount-len(domains))
		}

		// F. 智能层级去重 (倒序排序法)
		fmt.Println("   🧠 [Dedup] 执行智能层级去重...")
		beforeCount := len(domains)
		finalDomains := smartDedup(domains)
		fmt.Printf("   📦 [Result] 最终数量: %d (减少 %d)\n", len(finalDomains), beforeCount-len(finalDomains))

		// G. 输出文件
		for _, target := range ruleSet.Targets {
			switch target {
			case "mihomo":
				txtPath := fmt.Sprintf("%s/mihomo/%s.txt", cfg.Settings.OutputDir, ruleSet.Name)
				saveTextFile(txtPath, finalDomains, ruleSet.OutputPrefix, "")
				
				mrsPath := fmt.Sprintf("%s/mihomo/%s.mrs", cfg.Settings.OutputDir, ruleSet.Name)
				// 编译 .mrs
				cmd := exec.Command(cfg.Settings.MihomoBin, "convert-ruleset", "domain", "text", txtPath, mrsPath)
				if err := cmd.Run(); err != nil {
					fmt.Printf("   ⚠️  Mihomo 编译失败: %v\n", err)
				}

			case "adguard":
				path := fmt.Sprintf("%s/adg/%s_adg.txt", cfg.Settings.OutputDir, ruleSet.Name)
				saveTextFile(path, finalDomains, "", "adguard")

			case "mosdns":
				// 输出到 mosdns-x 目录，保持和分支名一致
				path := fmt.Sprintf("%s/mosdns-x/ad_domain_list.txt", cfg.Settings.OutputDir)
				saveTextFile(path, finalDomains, "", "")
			}
		}
	}
}

// ---------------- 核心算法 ----------------

// 1. 域名标准化 (剔除IP、修饰符)
func normalizeDomain(line string) string {
	line = strings.Split(line, "#")[0] // 去注释
	line = strings.TrimSpace(line)
	if line == "" { return "" }

	// hosts 格式处理
	if strings.HasPrefix(line, "0.0.0.0 ") || strings.HasPrefix(line, "127.0.0.1 ") {
		fields := strings.Fields(line)
		if len(fields) >= 2 { line = fields[1] }
	}

	// 移除修饰符
	line = strings.TrimPrefix(line, "||")
	line = strings.TrimPrefix(line, "+.")
	line = strings.TrimPrefix(line, ".")
	line = strings.TrimSuffix(line, "^")

	// Clash/Surge 格式处理
	if strings.Contains(line, ",") {
		parts := strings.Split(line, ",")
		if len(parts) > 1 { line = parts[1] } else { return "" }
	}

	// 【核心】剔除纯 IP 地址
	if ip := net.ParseIP(line); ip != nil {
		return ""
	}

	// 简单合法性检查
	if !strings.Contains(line, ".") || strings.Contains(line, "/") {
		return ""
	}

	return strings.ToLower(line)
}

// 2. 双向冲突解决
func resolveConflicts(blockMap map[string]bool, allowMap map[string]bool, allowList []string) {
	// 子杀父: Allow "wgo.mmstat.com" -> Block "mmstat.com" must go
	for _, allowed := range allowList {
		parts := strings.Split(allowed, ".")
		for i := 0; i < len(parts); i++ {
			parent := strings.Join(parts[i:], ".")
			if blockMap[parent] { delete(blockMap, parent) }
		}
	}
	// 父杀子: Allow "mmstat.com" -> Block "cnzz.mmstat.com" must go
	for blocked := range blockMap {
		if allowMap[blocked] { delete(blockMap, blocked); continue }
		parts := strings.Split(blocked, ".")
		for i := 1; i < len(parts); i++ {
			parent := strings.Join(parts[i:], ".")
			if allowMap[parent] { delete(blockMap, blocked); break }
		}
	}
}

// 3. 智能去重 (倒序排序法)
// 解决 net.cn 无法覆盖 *.net.cn 的问题
func smartDedup(domains []string) []string {
	type item struct { original, reversed string }
	list := make([]item, len(domains))
	for i, d := range domains {
		list[i] = item{original: d, reversed: reverseString(d)}
	}

	// 排序: cn.net, cn.net.cdn
	sort.Slice(list, func(i, j int) bool {
		return list[i].reversed < list[j].reversed
	})

	var final []string
	if len(list) == 0 { return final }

	final = append(final, list[0].original)
	lastKept := list[0].reversed

	for i := 1; i < len(list); i++ {
		curr := list[i].reversed
		// 如果 curr (cn.net.cdn) 以 lastKept (cn.net) + "." 开头
		// 则是子域名，剔除
		if strings.HasPrefix(curr, lastKept+".") {
			continue
		}
		final = append(final, list[i].original)
		lastKept = curr
	}
	
	// 最后正序排列
	sort.Strings(final)
	return final
}

func reverseString(s string) string {
	r := []rune(s)
	for i, j := 0, len(r)-1; i < j; i, j = i+1, j-1 { r[i], r[j] = r[j], r[i] }
	return string(r)
}

// 4. DNS 存活检测 (随机池 + 重试机制)
func filterDeadDomainsSafe(domains []string, servers []string, concurrency int) []string {
	if len(servers) == 0 { servers = []string{"8.8.8.8:53"} }
	var wg sync.WaitGroup
	aliveChan := make(chan string, len(domains))
	sem := make(chan struct{}, concurrency)

	// 单次检测函数
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

	for _, d := range domains {
		wg.Add(1)
		go func(domain string) {
			defer wg.Done()
			sem <- struct{}{}
			defer func() { <-sem }()

			// 随机选一个主DNS尝试
			s1 := servers[rand.Intn(len(servers))]
			if check(domain, s1) {
				aliveChan <- domain
				return
			}
			// 失败重试：随机选另一个DNS
			s2 := servers[rand.Intn(len(servers))]
			if check(domain, s2) {
				aliveChan <- domain
				return
			}
			// 两次都挂，判定为死链
		}(d)
	}

	wg.Wait()
	close(aliveChan)
	var alive []string
	for d := range aliveChan { alive = append(alive, d) }
	sort.Strings(alive)
	return alive
}

// 5. 并发下载
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
			client := &http.Client{Timeout: 30 * time.Second}
			resp, err := client.Get(u)
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
