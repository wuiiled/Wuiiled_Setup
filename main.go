package main

import (
	"bufio"
	"context"
	"fmt"
	"net"
	"net/http"
	"os"
	"os/exec"
	"sort"
	"strings"
	"sync"
	"time"

	"golang.org/x/net/publicsuffix"
	"gopkg.in/yaml.v3"
)

// Config 结构
type Config struct {
	Settings struct {
		OutputDir   string `yaml:"output_dir"`
		MihomoBin   string `yaml:"mihomo_bin"`
		DNSCheck    bool   `yaml:"dns_check"`
		DNSServer   string `yaml:"dns_server"`
		Concurrency int    `yaml:"concurrency"`
	} `yaml:"settings"`
	RuleSets []struct {
		Name            string   `yaml:"name"`
		Type            string   `yaml:"type"`
		Targets         []string `yaml:"targets"` // mihomo, adguard, mosdns
		Sources         []string `yaml:"sources"`
		AllowLists      []string `yaml:"allowlists"`
		LocalAllowLists []string `yaml:"local_allowlists"`
	} `yaml:"rule_sets"`
}

func main() {
	// 1. 加载配置
	fmt.Println("📖 读取配置文件 config.yaml...")
	data, err := os.ReadFile("config.yaml")
	if err != nil {
		panic(err)
	}
	var cfg Config
	if err := yaml.Unmarshal(data, &cfg); err != nil {
		panic(err)
	}

	// 初始化目录结构
	dirs := []string{"mihomo", "adg", "mosdns"}
	for _, d := range dirs {
		os.MkdirAll(fmt.Sprintf("%s/%s", cfg.Settings.OutputDir, d), 0755)
	}

	// 2. 处理规则集
	for _, ruleSet := range cfg.RuleSets {
		fmt.Printf("\n🚀 处理: [%s]\n", ruleSet.Name)

		// 下载
		blockLines := parallelDownload(ruleSet.Sources)
		fmt.Printf("   ⬇️  原始规则: %d 行\n", len(blockLines))

		// 处理白名单
		allowMap := make(map[string]bool)
		if len(ruleSet.AllowLists) > 0 || len(ruleSet.LocalAllowLists) > 0 {
			allowLines := parallelDownload(ruleSet.AllowLists)
			for _, f := range ruleSet.LocalAllowLists {
				if c, err := os.ReadFile(f); err == nil {
					allowLines = append(allowLines, strings.Split(string(c), "\n")...)
				}
			}
			for _, l := range allowLines {
				if d := normalizeDomain(l); d != "" {
					allowMap[d] = true
				}
			}
			fmt.Printf("   🛡️  白名单: %d 个\n", len(allowMap))
		}

		// 清洗
		uniqueDomains := make(map[string]bool)
		for _, line := range blockLines {
			if ruleSet.Type == "fakeip" {
				if strings.Contains(line, "fake-ip-filter:") || strings.Contains(line, "dns:") {
					continue
				}
				line = strings.TrimLeft(line, "- ")
				line = strings.Trim(line, "\"' ")
			}
			domain := normalizeDomain(line)
			if domain != "" && !allowMap[domain] {
				uniqueDomains[domain] = true
			}
		}

		domains := make([]string, 0, len(uniqueDomains))
		for d := range uniqueDomains {
			domains = append(domains, d)
		}
		fmt.Printf("   🧹 清洗后: %d 个\n", len(domains))

		// DNS 检测
		if cfg.Settings.DNSCheck && ruleSet.Type == "reject" {
			fmt.Println("   🔍 正在进行 DNS 存活检测...")
			domains = filterDeadDomains(domains, cfg.Settings.DNSServer, cfg.Settings.Concurrency)
			fmt.Printf("   ✅ 存活域名: %d 个\n", len(domains))
		}

		// 智能去重
		fmt.Println("   🧠 智能层级合并...")
		finalDomains := smartDedup(domains)
		fmt.Printf("   📦 最终数量: %d 个\n", len(finalDomains))

		// 分发输出
		for _, target := range ruleSet.Targets {
			switch target {
			case "mihomo":
				// 生成 .txt
				txtPath := fmt.Sprintf("%s/mihomo/%s.txt", cfg.Settings.OutputDir, ruleSet.Name)
				saveTextFile(txtPath, finalDomains, "")
				
				// 编译 .mrs
				mrsPath := fmt.Sprintf("%s/mihomo/%s.mrs", cfg.Settings.OutputDir, ruleSet.Name)
				ruleType := "domain" // 默认为 domain，如果是 ip 列表可扩展判断逻辑
				cmd := exec.Command(cfg.Settings.MihomoBin, "convert-ruleset", ruleType, "text", txtPath, mrsPath)
				if err := cmd.Run(); err != nil {
					fmt.Printf("   ⚠️  Mihomo 编译失败: %v\n", err)
				}

			case "adguard":
				path := fmt.Sprintf("%s/adg/%s_adg.txt", cfg.Settings.OutputDir, ruleSet.Name)
				saveTextFile(path, finalDomains, "adguard")

			case "mosdns":
				// MosDNS 通常和 Mihomo 格式兼容 (纯域名列表)
				// 如果需要 domain: 前缀，可在此扩展
				path := fmt.Sprintf("%s/mosdns/ad_domain_list.txt", cfg.Settings.OutputDir) // 保持 convert.sh 的命名习惯
				saveTextFile(path, finalDomains, "")
			}
		}
	}
}

// --- 工具函数 ---

func parallelDownload(urls []string) []string {
	var wg sync.WaitGroup
	resultChan := make(chan []string, len(urls))
	limitChan := make(chan struct{}, 10)

	for _, url := range urls {
		wg.Add(1)
		go func(u string) {
			defer wg.Done()
			limitChan <- struct{}{}
			defer func() { <-limitChan }()

			client := &http.Client{Timeout: 20 * time.Second}
			resp, err := client.Get(u)
			if err != nil {
				return
			}
			defer resp.Body.Close()

			var lines []string
			scanner := bufio.NewScanner(resp.Body)
			for scanner.Scan() {
				lines = append(lines, scanner.Text())
			}
			resultChan <- lines
		}(url)
	}
	wg.Wait()
	close(resultChan)

	var all []string
	for slice := range resultChan {
		all = append(all, slice...)
	}
	return all
}

func normalizeDomain(line string) string {
	line = strings.Split(line, "#")[0]
	line = strings.TrimSpace(line)
	if line == "" { return "" }
	
	if strings.HasPrefix(line, "0.0.0.0 ") || strings.HasPrefix(line, "127.0.0.1 ") {
		fields := strings.Fields(line)
		if len(fields) >= 2 { return fields[1] }
	}

	line = strings.TrimPrefix(line, "||")
	line = strings.TrimPrefix(line, "+.")
	line = strings.TrimPrefix(line, ".")
	line = strings.TrimSuffix(line, "^")
	
	if strings.Contains(line, ",") {
		parts := strings.Split(line, ",")
		if len(parts) > 1 { return parts[1] }
	}

	if !strings.Contains(line, ".") && line != "localhost" { return "" }
	return strings.ToLower(line)
}

func filterDeadDomains(domains []string, server string, concurrency int) []string {
	var wg sync.WaitGroup
	aliveChan := make(chan string, len(domains))
	sem := make(chan struct{}, concurrency)
	resolver := &net.Resolver{
		PreferGo: true,
		Dial: func(ctx context.Context, network, address string) (net.Conn, error) {
			d := net.Dialer{Timeout: 2 * time.Second}
			return d.Dial("udp", server)
		},
	}

	for _, d := range domains {
		wg.Add(1)
		go func(domain string) {
			defer wg.Done()
			sem <- struct{}{}
			defer func() { <-sem }()
			ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
			defer cancel()
			if _, err := resolver.LookupHost(ctx, domain); err == nil {
				aliveChan <- domain
			}
		}(d)
	}
	wg.Wait()
	close(aliveChan)
	var alive []string
	for d := range aliveChan { alive = append(alive, d) }
	return alive
}

func smartDedup(domains []string) []string {
	tree := make(map[string]map[string]bool)
	others := []string{}
	for _, d := range domains {
		eTLD, err := publicsuffix.EffectiveTLDPlusOne(d)
		if err != nil {
			others = append(others, d)
			continue
		}
		if _, ok := tree[eTLD]; !ok { tree[eTLD] = make(map[string]bool) }
		tree[eTLD][d] = true
	}
	final := append([]string{}, others...)
	for root, subMap := range tree {
		if subMap[root] {
			final = append(final, root)
		} else {
			for sub := range subMap { final = append(final, sub) }
		}
	}
	sort.Strings(final)
	return final
}

func saveTextFile(path string, lines []string, format string) {
	f, _ := os.Create(path)
	defer f.Close()
	w := bufio.NewWriter(f)
	w.WriteString(fmt.Sprintf("# Updated: %s\n", time.Now().Format("2006-01-02 15:04:05")))
	w.WriteString(fmt.Sprintf("# Count: %d\n", len(lines)))
	for _, l := range lines {
		if format == "adguard" {
			w.WriteString(fmt.Sprintf("||%s^\n", l))
		} else {
			w.WriteString(l + "\n")
		}
	}
	w.Flush()
}
