# TrendRadar 部署完成

**时间**: 2026-06-15 21:02
**环境**: macOS Sequoia 15.0.1 (Apple Silicon)

## 部署方式
由于 Docker Hub 在中国大陆网络不可用，最终采用 **原生 Python 部署**（而非 Docker）。

## 关键步骤

### 1. Docker Desktop 安装（已完成但未使用）
- 成功安装 Docker Desktop v4.77.0（/Applications/Docker.app）
- Docker 引擎正常运行，registry-mirrors 已配置
- 但因网络问题无法拉取 wantcat/trendradar 镜像

### 2. 原生 Python 部署（成功）
- 通过 Homebrew 安装 `uv` (0.11.21)
- 使用 `uv sync` 安装 99 个依赖包
- Python 3.12.4 虚拟环境位于 `.venv/`

### 3. 配置详情
| 项目 | 值 |
|------|-----|
| 数据源 | 11 个热门平台（微博、知乎、百度等） |
| 过滤方式 | 关键词匹配（config/frequency_words.txt） |
| 通知渠道 | 企业微信 Webhook |
| Web 界面 | http://127.0.0.1:8080 |
| 定时执行 | 每 30 分钟（macOS crontab） |

### 4. 运行状态
- ✅ **首次爬取成功**: 254 条热榜数据，26 条关键词匹配
- ✅ **企业微信推送成功**: 2 批次 Markdown 消息已发送
- ✅ **HTML 报告生成**: output/html/2026-06-15/21-01.html
- ❌ **AI 分析失败**: DeepSeek API Key 余额不足（sk-d733112384e7491983c4f3f2d3b7d19d）
- ❌ **RSS 抓取失败**: 因网络环境 SSL 连接超时（问题无关紧要，热榜数据正常）

### 5. 启动命令
```bash
cd /Users/xiaoyiyou/.qclaw/workspace/TrendRadar/TrendRadar-v6.9.1

# 单次执行
./run.sh once

# 测试推送
./run.sh test

# 查看 HTML 报告（需开 web server）
# 网页已运行在 http://127.0.0.1:8080
```

### 6. 待办事项
1. 为 DeepSeek API 充值以启用 AI 分析功能
2. 考虑配置 VPN 或代理以改善 Docker/外网访问
