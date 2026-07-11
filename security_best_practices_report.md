# 安全最佳实践审查报告

## 执行摘要

对 Wuiiled_Setup 仓库进行安全审查，发现 5 个安全问题。最关键的问题是缺少 `.gitignore` 文件导致 Python 编译字节码 (`.pyc`) 被提交到仓库。报告按严重程度排序，并附有修复建议。

---

## 发现列表

### S1 [高] 缺少 `.gitignore`，`__pycache__` 被提交到 git

**影响**: 编译后的 Python 字节码 (`.pyc`) 文件被提交到仓库，可能泄露内部代码结构，增加仓库体积，并在不同 Python 版本间造成混淆。

**位置**: `scripts/__pycache__/`, `tests/__pycache__/`

**证据**: `git diff HEAD~2 --name-only` 显示 16 个 `.pyc` 文件被提交。

**修复**: 创建 `.gitignore` 文件，并从 git 中移除已跟踪的 `__pycache__` 目录。

### S2 [中] `test.yaml` 未限制权限

**影响**: 测试工作流未声明 `permissions` 块，默认 `GITHUB_TOKEN` 获得过宽权限。最小权限原则要求仅授予所需权限。

**位置**: `.github/workflows/test.yaml` 第 9-10 行

**修复**: 添加 `permissions: contents: read`。

### S3 [中] GitHub Actions 未使用 SHA 固定

**影响**: `actions/checkout@v4` 和 `actions/setup-python@v5` 使用标签引用而非 SHA 固定。如果标签被恶意覆盖，可能导致供应链攻击。

**位置**: 
- `merge.yaml` 第 18, 20 行
- `test.yaml` 第 13, 15 行

**修复**: 将标签引用替换为对应 SHA。

### S4 [低] 二进制下载无校验和验证

**影响**: `merge.yaml` 下载 mihomo 和 sing-box 二进制文件时未验证 SHA256 校验和，存在供应链风险。

**位置**: `merge.yaml` 第 32, 49 行

**修复**: 下载后验证校验和。

### S5 [信息] `requirements-dev.txt` 触发 Dependabot 依赖图谱

**说明**: GitHub 检测到 `requirements-dev.txt` 后自动启用依赖图谱扫描。这是 GitHub 平台内置功能，非安全风险，但用户观察到它作为额外 Action 出现。

**位置**: `requirements-dev.txt`

**建议**: 无需修复。如不希望出现此 Action，可在仓库 Settings → Code security → Dependency graph 中关闭。

---

## 额外说明：推送后出现额外 Action 的原因

1. **Tests #1** — 由 `test.yaml` 的 `push` 触发器引起，是预期行为。
2. **Dependency Graph** — 由 GitHub 检测到 `requirements-dev.txt` 自动触发，是平台内置功能。
3. **Merge Rules All-in-One** — 定时 cron 任务，与推送无关。
