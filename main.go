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

	"gopkg.in/yaml.v3"
)

// ---------------- 结构体定义 ----------------

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
		Targets         []string `yaml:"targets"`
		Sources         []string `yaml:"sources"`
		AllowLists      []string `yaml:"allowlists"`
		LocalAllowLists []string `yaml:"local_allowlists"`
	} `yaml:"rule_sets"`
}

// ---------------- 主函数 ----------------

func main() {
	// 1. 加载配置
	fmt.Println("📖 [Init] 读取配置文件 config.yaml...")
	data, err := os.ReadFile("config.yaml")
	if err != nil {
		fmt.Printf("❌ 无法读取配置文件: %v\n", err)
		os.Exit(1)
	}
	var cfg Config
	if err := yaml.Unmarshal(data, &cfg); err != nil {
		fmt.Printf("❌ 配置文件解析失败: %v\n", err)
		os.Exit(1)
	}

	// 打印调试信息，确认配置生效
	fmt.Printf("⚙️  [Config] DNS检测: %v | DNS服务器: %s | 并发: %d\n", 
		cfg.Settings.DNSCheck, cfg.Settings.DNSServer, cfg.Settings.Concurrency)

	// 初始化目录
	dirs := []string{"mihomo", "adg", "mosdns"}
	for _, d := range dirs {
		os.MkdirAll(fmt.Sprintf("%s/%s", cfg.Settings.OutputDir, d), 0755)
	}

	// 2. 遍历处理规则集
	for _, ruleSet := range cfg.RuleSets {
		fmt.Printf("\n🚀 [Start] 正在处理: [%s] (类型: %s)\n", ruleSet.Name, ruleSet.Type)

		// A. 下载
		blockLines := parallelDownload(ruleSet.Sources)
		fmt.Printf("   ⬇️  [Download] 原始行数: %d\n", len(blockLines))

		// B. 处理白名单
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
			fmt.Printf("   🛡️  [Allow] 白名单域名: %d\n", len(allowMap))
		}

		// C. 基础清洗 (Set去重 + 排除白名单)
		uniqueDomains := make(map[string]bool)
		for _, line := range blockLines {
			// FakeIP 特殊处理
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

		// 转为切片
		domains := make([]string, 0, len(uniqueDomains))
		for d := range uniqueDomains {
			domains = append(domains, d)
		}
		fmt.Printf("   🧹 [Clean] 基础清洗后: %d\n", len(domains))

		// D. DNS 连通性检测 (核心修复点)
		// 只有全局开关打开 且 当前规则集类型为 reject 时才检测
		if cfg.Settings.DNSCheck && ruleSet.Type == "reject" {
			fmt.Printf("   🔍 [DNS] 开始执行死链检测 (服务器: %s, 并发: %d)...\n", cfg.Settings.DNSServer, cfg.Settings.Concurrency)
			beforeCount := len(domains)
			domains = filterDeadDomains(domains, cfg.Settings.DNSServer, cfg.Settings.Concurrency)
			fmt.Printf("   ✅ [DNS] 检测完成: %d -> %d (移除了 %d 个失效域名)\n", beforeCount, len(domains), beforeCount-len(domains))
		} else {
			fmt.Printf("   ⏭️  [DNS] 跳过检测 (GlobalCheck: %v, SetType: %s)\n", cfg.Settings.DNSCheck, ruleSet.Type)
		}

		// E. 智能层级去重 (算法升级)
		fmt.Println("   🧠 [Dedup] 执行智能层级去重 (倒序排序法)...")
		beforeCount := len(domains)
		finalDomains := smartDedup(domains)
		fmt.Printf("   📦 [Result] 最终数量: %d (优化掉 %d 个子域名)\n", len(finalDomains), beforeCount-len(finalDomains))

		// F. 输出
		for _, target := range ruleSet.Targets {
			switch target {
			case "mihomo":
				txtPath := fmt.Sprintf("%s/mihomo/%s.txt", cfg.Settings.OutputDir, ruleSet.Name)
				saveTextFile(txtPath, finalDomains, "")
				
				mrsPath := fmt.Sprintf("%s/mihomo/%s.mrs", cfg.Settings.OutputDir, ruleSet.Name)
				ruleType := "domain"
				cmd := exec.Command(cfg.Settings.MihomoBin, "convert-ruleset", ruleType, "text", txtPath, mrsPath)
				if err := cmd.Run(); err != nil {
					fmt.Printf("   ⚠️  Mihomo编译失败: %v\n", err)
				}

			case "adguard":
				path := fmt.Sprintf("%s/adg/%s_adg.txt", cfg.Settings.OutputDir, ruleSet.Name)
				saveTextFile(path, finalDomains, "adguard")

			case "mosdns":
				path := fmt.Sprintf("%s/mosdns/ad_domain_list.txt", cfg.Settings.OutputDir)
				saveTextFile(path, finalDomains, "")
			}
		}
	}
}

// ---------------- 核心算法函数 ----------------

// 1. 域名标准化 (去除非法字符，统一小写)
func normalizeDomain(line string) string {
	line = strings.Split(line, "#")[0] // 去行尾注释
	line = strings.TrimSpace(line)
	if line == "" { return "" }
	
	// 处理 hosts 格式 0.0.0.0
	if strings.HasPrefix(line, "0.0.0.0 ") || strings.HasPrefix(line, "127.0.0.1 ") {
		fields := strings.Fields(line)
		if len(fields) >= 2 { return strings.ToLower(fields[1]) }
	}

	// 移除常见修饰符
	line = strings.TrimPrefix(line, "||")
	line = strings.TrimPrefix(line, "+.")
	line = strings.TrimPrefix(line, ".")
	line = strings.TrimSuffix(line, "^")
	
	// 处理 DOMAIN-SUFFIX,example.com,REJECT 等格式
	if strings.Contains(line, ",") {
		parts := strings.Split(line, ",")
		if len(parts) > 1 {
			// 通常第二个是域名
			line = parts[1]
		} else {
			return ""
		}
	}

	// 简单合法性检查: 必须包含点，且不能包含 URL 路径符号
	if !strings.Contains(line, ".") || strings.Contains(line, "/") {
		return ""
	}

	return strings.ToLower(line)
}

// 2. 智能去重 - 倒序排序法 (彻底解决子域名覆盖问题)
// 输入: ["a.b.com", "b.com"]
// 逻辑: 倒序为 ["moc.b.a", "moc.b"] -> 排序 -> ["moc.b", "moc.b.a"]
// 遍历: "moc.b.a" 以 "moc.b" + "." 开头 -> 删除
func smartDedup(domains []string) []string {
	type item struct {
		original string
		reversed string
	}
	
	list := make([]item, len(domains))
	for i, d := range domains {
		list[i] = item{
			original: d,
			reversed: reverseString(d),
		}
	}

	// 排序
	sort.Slice(list, func(i, j int) bool {
		return list[i].reversed < list[j].reversed
	})

	var final []string
	if len(list) == 0 {
		return final
	}

	// 核心去重逻辑
	final = append(final, list[0].original)
	lastKept := list[0].reversed

	for i := 1; i < len(list); i++ {
		curr := list[i].reversed
		// 如果当前域名(倒序) 是以 上一个保留域名(倒序) + "." 开头
		// 说明当前域名是上一个域名的子域名。
		// 例如: lastKept="moc.udiab" (baidu.com), curr="moc.udiab.da" (ad.baidu.com)
		if strings.HasPrefix(curr, lastKept+".") {
			continue // 是子域名，丢弃
		}
		
		final = append(final, list[i].original)
		lastKept = curr
	}
	
	// 最后再按正序排一次，方便查看
	sort.Strings(final)
	return final
}

func reverseString(s string) string {
	r := []rune(s)
	for i, j := 0, len(r)-1; i < j; i, j = i+1, j-1 {
		r[i], r[j] = r[j], r[i]
	}
	return string(r)
}

// 3. DNS 存活检测 (并发版)
func filterDeadDomains(domains []string, server string, concurrency int) []string {
	var wg sync.WaitGroup
	aliveChan := make(chan string, len(domains))
	sem := make(chan struct{}, concurrency) // 限制并发数
	
	// 自定义 Resolver，强制使用指定 DNS 且超时短
	resolver := &net.Resolver{
		PreferGo: true,
		Dial: func(ctx context.Context, network, address string) (net.Conn, error) {
			d := net.Dialer{Timeout: 1500 * time.Millisecond} // 1.5秒建立连接超时
			return d.Dial("udp", server)
		},
	}

	for _, d := range domains {
		wg.Add(1)
		go func(domain string) {
			defer wg.Done()
			sem <- struct{}{} 
			defer func() { <-sem }()

			ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second) // 整体解析超时
			defer cancel()
			
			// 只要有任意记录 (A, AAAA, CNAME) 就算活
			_, err := resolver.LookupHost(ctx, domain)
			if err == nil {
				aliveChan <- domain
			} else {
				// 调试: 打印失败原因 (可选，日志量会很大)
				// fmt.Printf("Dead: %s (%v)\n", domain, err)
			}
		}(d)
	}

	wg.Wait()
	close(aliveChan)

	var alive []string
	for d := range aliveChan {
		alive = append(alive, d)
	}
	sort.Strings(alive)
	return alive
}

// 4. 并发下载
func parallelDownload(urls []string) []string {
	var wg sync.WaitGroup
	resultChan := make(chan []string, len(urls))
	limitChan := make(chan struct{}, 8) // 限制下载并发，防封IP

	for _, url := range urls {
		wg.Add(1)
		go func(u string) {
			defer wg.Done()
			limitChan <- struct{}{}
			defer func() { <-limitChan }()

			client := &http.Client{Timeout: 30 * time.Second}
			resp, err := client.Get(u)
			if err != nil {
				fmt.Printf("   ⚠️  下载失败: %s\n", u)
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

// 5. 保存文件
func saveTextFile(path string, lines []string, format string) {
	f, err := os.Create(path)
	if err != nil {
		fmt.Printf("❌ 创建文件失败: %v\n", err)
		return
	}
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
