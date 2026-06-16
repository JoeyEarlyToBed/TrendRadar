# TrendRadar v6.9.1 — 技术架构与功能完全手册

> 编写日期：2026-06-16
> 编写背景：Joey 尤晓昳 — KUKA China 质量部门数字化推进工程师
> 项目定位：集团"030 AI造物者闯关记"参赛作品，24小时极限搭建的 AI 辅助精准舆情监控原型

---

## 一、总览

TrendRadar 是一个**AI 驱动的热点新闻智能监控与分析平台**，支持从国内主流热榜平台及 RSS 源抓取实时数据，通过关键词/正则过滤+AI 分析，生成结构化情报报告，并推送至企业微信、飞书、钉钉等即时通讯工具。

### 技术栈

| 层级 | 技术 |
|------|------|
| 运行时 | Python 3.10+ |
| 热榜数据源 | NewsNow API (`newsnow.busiyi.world`) |
| RSS 解析 | `feedparser` (RSS 2.0 / Atom / JSON Feed) |
| AI 分析 | OpenAI 兼容 API（DeepSeek / OpenAI / 通义千问等） |
| 存储 | SQLite (本地)、S3 (远程) |
| 通知 | Webhook (企业微信/飞书/钉钉/Slack/通用)、Telegram Bot、邮件、Bark、ntfy |
| Web 服务 | Uvicorn + FastAPI (MCP Server) |
| 部署 | Docker Compose 或本地 `.venv` |
| 前端配置 | HTML/Tailwind CSS 可视化编辑器 |

---

## 二、项目结构

```
TrendRadar-v6.9.1/
├── config/                          # 📁 配置文件目录（运行时只读）
│   ├── frequency_words.txt          #   关键词/正则匹配规则
│   ├── ai_interests.txt             #   AI兴趣描述（自然语言）
│   ├── ai_analysis_prompt.txt       #   AI分析提示词模板
│   ├── config.yaml                  #   主配置文件
│   └── timeline.yaml                # ⏰ 定时调度配置
├── output/                          # 📁 输出目录（运行时生成）
│   ├── data.sqlite                  #   SQLite 数据库
│   ├── report_latest.html           #   最新 HTML 报告
│   ├── cron.log                     #   定时执行日志
│   └── rss_report_latest.html       #   RSS 专用报告
├── trendradar/                      # 📁 核心源代码
│   ├── __main__.py                  #   程序入口 CLI
│   ├── context.py                   #   全局上下文（加载配置）
│   ├── core/                        #   核心模块
│   │   ├── config.py                #     多账号配置解析
│   │   ├── loader.py                #     配置文件加载
│   │   ├── frequency.py             #     关键词匹配引擎
│   │   ├── analyzer.py              #     词频/权重分析
│   │   ├── scheduler.py             #     定时调度器
│   │   └── data.py                  #     数据查询接口
│   ├── crawler/                     # 📁 爬虫模块
│   │   ├── fetcher.py               #     NewsNow API 数据获取
│   │   └── rss/
│   │       ├── fetcher.py           #     RSS 源抓取
│   │       └── parser.py            #     RSS 解析器
│   ├── ai/                          # 📁 AI 分析模块
│   │   ├── analyzer.py              #     AI分析执行器
│   │   ├── client.py                #     API 客户端
│   │   ├── filter.py                #     AI过滤
│   │   ├── formatter.py             #     格式化输出
│   │   ├── prompt_loader.py         #     提示词加载
│   │   └── translator.py            #     翻译
│   ├── notification/                # 📁 通知推送模块
│   │   ├── dispatcher.py            #     推送分发器
│   │   ├── senders.py               #     各渠道发送器
│   │   ├── formatters.py            #     消息格式
│   │   ├── renderer.py              #     渲染
│   │   ├── batch.py                 #     批量推送
│   │   └── splitter.py              #     消息分割
│   ├── report/                      # 📁 报告模块
│   │   ├── generator.py             #     报告生成
│   │   ├── formatter.py             #     格式处理
│   │   ├── helpers.py               #     辅助函数
│   │   ├── html.py                  #     HTML模板
│   │   └── rss_html.py              #     RSS HTML模板
│   ├── storage/                     # 📁 存储模块
│   │   ├── base.py                  #     存储接口
│   │   ├── local.py                 #     本地存储
│   │   ├── manager.py               #     存储管理器
│   │   ├── sqlite_mixin.py          #     SQLite 混入
│   │   └── remote.py                #     远程存储 (S3)
│   └── utils/                       # 📁 工具模块
│       ├── time.py                  #     时间工具
│       └── url.py                   #     URL工具
├── mcp_server/                      # 📁 MCP Server (Model Context Protocol)
│   ├── server.py                    #     FastAPI 服务入口
│   ├── services/                    #     服务层
│   │   ├── cache_service.py         #       缓存服务
│   │   ├── data_service.py          #       数据服务
│   │   └── parser_service.py        #       解析服务
│   └── tools/                       #     MCP 工具
│       ├── analytics.py             #       分析工具
│       ├── article_reader.py        #       文章读取
│       ├── config_mgmt.py           #       配置管理
│       ├── data_query.py            #       数据查询
│       ├── notification.py          #       通知管理
│       ├── search_tools.py          #       搜索工具
│       ├── storage_sync.py          #       存储同步
│       └── system.py                #       系统管理
├── docker/                          # Docker 部署
│   ├── docker-compose.yml
│   └── manage.py
├── docs/                            # 文档
│   ├── index.html                   # 可视化配置编辑器
│   └── assets/                      # 前端资源
├── run.sh                           # 本地运行脚本
└── requirements.txt                 # Python 依赖
```

---

## 三、模块功能详解

### 3.1 核心模块 (`trendradar/core/`)

#### `config.py` — 多账号配置解析
- `parse_multi_account_config()`: 从 `config.yaml` 解析多账号配置
- `validate_paired_configs()`: 校验多账号配置完整性
- `limit_accounts()`: 限制最大账号数
- `get_account_at_index()`: 按索引获取账号配置

#### `loader.py` — 配置加载
- `load_config()`: 加载 `config.yaml` 主配置，返回结构化的配置字典

#### `frequency.py` — 关键词匹配引擎（核心业务）
- `load_frequency_words(filepath)`: 加载 `frequency_words.txt`，解析为结构化词组
- `matches_word_groups(title, word_groups)`: 将标题与词组进行匹配
  - 支持语法：`+必须词`、`!排除词`、`/正则/`、`[组名]`、`关键词 => 别名`、`@限制条数`
- **匹配机制**：
  1. 先过 `[GLOBAL_FILTER]` 全局过滤（排除"震惊"等标题党）
  2. 逐组匹配标题
  3. 同一组内关键词为"或"关系
  4. `+` 开头的词为"必须包含"（与组内其他词为"与"关系）
  5. `!` 开头的词为"排除"（命中则整组跳过该标题）

#### `analyzer.py` — 数据分析
- `count_word_frequency()`: 对热榜标题进行词频统计
- `count_rss_frequency()`: 对 RSS 标题进行词频统计
- `calculate_news_weight()`: 计算新闻权重
- `format_time_display()`: 时间格式化

#### `scheduler.py` — 定时调度器
- `Scheduler`: 调度器主类
- `ResolvedSchedule`: 解析后的调度配置
- 支持 `config.yaml` 中的 `schedule` 配置段：`enabled`、`interval_minutes`、`cron_expression`

#### `data.py` — 数据查询
- `read_all_today_titles()`: 读取今日所有标题
- `detect_latest_new_titles()`: 检测新增标题（用于增量模式）

### 3.2 爬虫模块 (`trendradar/crawler/`)

#### `fetcher.py` — NewsNow 热榜抓取
- `DataFetcher`: 核心数据获取器
  - `DEFAULT_API_URL = "https://newsnow.busiyi.world/api/s"`
  - `fetch_data(id_info)`: 获取单个平台数据（支持重试）
  - `crawl_websites(ids_list)`: 批量爬取多个平台
- **调用格式**: `GET /api/s?id={platform_id}&latest`
- **平台映射**：配置文件 `config.yaml` 中定义 `sources.hotlist` 列表

#### 平台支持清单

当前版本通过 NewsNow API 支持以下热榜平台：

| 配置ID | 名称 | 类型 |
|--------|------|------|
| `toutiao` | 今日头条 | 资讯/社会 |
| `baidu` | 百度热搜 | 综合/搜索 |
| `wallstreetcn-hot` | 华尔街见闻 | 财经 |
| `thepaper` | 澎湃新闻 | 新闻 |
| `bilibili-hot-search` | B站热搜 | 年轻/视频 |
| `cls-hot` | 财联社 | 财经/B端 |
| `ifeng` | 凤凰网 | 资讯 |
| `tieba` | 百度贴吧 | 社区 |
| `weibo` | 微博 | 社交/舆论 |
| `douyin` | 抖音 | 短视频 |
| `zhihu` | 知乎 | 深度/问答 |

**⚠️ 当前版本未覆盖的常见平台**：小红书、快手、雪球、虎嗅、IT之家等

#### RSS 模块 (`trendradar/crawler/rss/`)
- `RSSFetcher`: RSS 源抓取
  - `fetch_feed(feed_config)`: 获取单个 RSS 源
  - `fetch_all_feeds(feeds)`: 批量获取所有 RSS 源
- `RSSParser`: RSS 解析器（支持 RSS 2.0 / Atom / JSON Feed 1.1）
- **支持的网络协议**：HTTP/HTTPS，不支持通过中国大陆防火墙的 Google News RSS
- **常见可用 RSS 源**：
  - 36氪 `https://36kr.com/feed`
  - 虎嗅 `https://www.huxiu.com/rss/0.xml`
  - 开源中国 `https://www.oschina.net/news/rss`
  - 极客公园 `https://www.geekpark.net/rss`
  - 阮一峰周刊 `https://feeds.feedburner.com/ruanyifeng`
  - Hacker News `https://hnrss.org/frontpage`
  - Solidot `https://solidot.org/feeds`

### 3.3 AI 分析模块 (`trendradar/ai/`)

#### `client.py` — AI API 客户端
- 支持 OpenAI 兼容 API（DeepSeek、OpenAI、通义千问等）
- 配置项：`api_key`、`model`（如 `deepseek/deepseek-chat`）、`api_base`、`temperature`

#### `analyzer.py` — AI 分析执行
- 接收匹配到的热榜+RSS数据
- 加载 `ai_interests.txt` 和 `ai_analysis_prompt.txt`
- 调用 AI API 生成结构化分析报告（JSON 格式）

#### 分析报告 JSON 格式

```json
{
  "core_trends": "核心热点态势（200字以内，包含宏观主线+微观领域）",
  "sentiment_controversy": "舆论风向争议（100字以内，情绪光谱+核心矛盾）",
  "signals": "异动与弱信号（150字以内，跨平台共振/温差/轨迹突变）",
  "rss_insights": "RSS深度洞察（100字以内，认知纠偏/硬核增量）",
  "outlook_strategy": "研判策略建议（角色分群建议）",
  "standalone_summaries": {
    "知乎": "100字以内概括",
    "Hacker News": "100字以内概括"
  }
}
```

#### `prompt_loader.py` — 提示词加载
- 从 `ai_analysis_prompt.txt` 和 `ai_interests.txt` 加载提示词

#### `filter.py` — AI 过滤
- 使用 AI 额外过滤低质量内容

#### `formatter.py` — AI 输出格式化
- 将 AI 返回的 JSON 格式化为可读文本

#### `translator.py` — 翻译（可选）
- 翻译非中文内容至中文

### 3.4 通知模块 (`trendradar/notification/`)

#### 支持的通知渠道

| 渠道 | 配置环境变量 | 说明 |
|------|-------------|------|
| **企业微信** | `WEWORK_WEBHOOK_URL` | 支持 markdown 和 text 两种格式 |
| **飞书** | `FEISHU_WEBHOOK_URL` | Webhook 推送 |
| **钉钉** | `DINGTALK_WEBHOOK_URL` | Webhook 推送 |
| **Telegram** | `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` | Bot 推送 |
| **邮件** | `EMAIL_*` 系列配置 | SMTP 邮件发送 |
| **Slack** | `SLACK_WEBHOOK_URL` | Webhook 推送 |
| **ntfy** | `NTFY_*` 系列配置 | 开源推送服务 |
| **Bark** | `BARK_URL` | iOS 推送 |
| **通用 Webhook** | `GENERIC_WEBHOOK_URL` | 自定义 Webhook |

#### 推送模式
- **每日推送** (`daily`)：每天汇总推送一次
- **增量推送** (`incremental`)：每次执行时推送新增的匹配内容
- **实时推送** (`realtime`)：发现即推送

---

## 四、运行模式

### 4.1 本地运行

```bash
cd TrendRadar-v6.9.1
source .venv/bin/activate

# 单次执行
python -m trendradar

# 或使用 run.sh
./run.sh once     # 单次爬取+分析+推送
./run.sh server   # 启动 Web 服务 + 定时执行（每30分钟）
./run.sh test     # 发送测试通知
./run.sh doctor   # 健康检查
```

### 4.2 Docker 部署

```bash
cd docker
docker-compose up -d
```

### 4.3 MCP Server 模式

通过 MCP Server 提供 API 接口，支持外部调用和集成：
- 端口：3333（默认）
- 功能：数据分析查询、配置管理、文章读取、通知管理等

---

## 五、配置详解

### 5.1 `config.yaml` — 主配置

```yaml
# 🔧 关键配置段

filter:
  method: keyword        # 过滤方式: keyword | ai | off
  match_all: false       # 是否全部匹配才推送

source:
  hotlist:               # 热榜平台列表
    - toutiao
    - baidu
    - ...
  rss:                   # RSS 源配置
    - url: https://36kr.com/feed
    - url: https://hnrss.org/frontpage
    - ...

schedule:
  enabled: false         # 是否开启定时
  interval_minutes: 30   # 间隔（分钟）
  cron_expression: "*/30 * * * *"

report:
  mode: incremental      # 报告模式: daily | incremental
  output:
    html: true          # 生成 HTML 报告

ai_analysis:
  enabled: true          # 是否开启 AI 分析
  include_rss: true     # 分析中是否包含 RSS 数据
  include_standalone: true  # 是否包含独立展示区
  api_key: ${AI_API_KEY}
  model: deepseek/deepseek-chat
  temperature: 0.3

notification:
  wework:
    webhook_url: ${WEWORK_WEBHOOK_URL}
    msg_type: markdown   # text | markdown
```

### 5.2 `frequency_words.txt` — 关键词文件

包含两个区段：

1. **`[GLOBAL_FILTER]`** — 全局过滤关键词
2. **`[WORD_GROUPS]`** — 词组定义区

语法示例：
```
# 简单匹配
华为

# 正则匹配（| 分隔多个词，=> 后为别名）
/华为|鸿蒙|任正非/ => 华为

# 分组名
[AI 相关]
/(?<![a-zA-Z])ai(?![a-zA-Z])/
人工智能

# 必须词
+苹果
+发布会

# 排除词
[苹果公司]
苹果
!水果
!果园

# 数量限制
[科技新闻]
科技
@5
```

### 5.3 `timeline.yaml` — 定时调度

```yaml
schedules:
  - id: default
    run_at:
      cron_expression: "*/30 * * * *"
    frequency_file: config/frequency_words.txt  # 可选：指定关键词文件
    test_notification: false
```

### 5.4 `ai_interests.txt` — AI 兴趣描述

自然语言描述关注方向，按优先级排列。当前已配置 15 个方向：

1. 中国科技与互联网公司（DeepSeek、华为、腾讯、字节、京东）
2. 大模型与 AI 产品（OpenAI、Claude、ChatGPT 等）
3. AI 基础设施与云算力（英伟达、AMD、CUDA 等）
4. 芯片与半导体制造
5. 智能汽车与自动驾驶
6. 机器人与具身智能
7. 全球科技巨头
8. 地缘政治与国际关系
9. 金融市场与宏观政策
10. 能源与电力系统
11. 航天与深空探索
12. 前沿科学技术
13. 文化 IP 与内容产业
14. 零售与消费品牌
15. 国家与区域观察

---

## 六、数据流

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│ NewsNow API │────▶│  DataFetcher  │────▶│  SQLite DB   │
│ (11 platforms)│     │ (crawl_websites)│     │ (storage)     │
└─────────────┘     └──────────────┘     └──────────────┘
                                                        │
┌─────────────┐     ┌──────────────┐                    │
│  RSS Feeds  │────▶│  RSSFetcher   │───────────────────▶│
│ (N sources)  │     │ (fetch_all)  │                    │
└─────────────┘     └──────────────┘                    │
                                                        ▼
                                              ┌──────────────────┐
                                              │   frequency.py   │
                                              │ 关键词/正则匹配   │
                                              │ (匹配 → 分组结果) │
                                              └──────────────────┘
                                                        │
                                              ┌─────────▼─────────┐
                                              │   AI Analyzer     │
                                              │ (结构化分析报告)   │
                                              └───────────────────┘
                                                        │
                                              ┌─────────▼─────────┐
                                              │   Dispatcher      │
                                              │ (推送通知/HTML报告)│
                                              └───────────────────┘
```

---

## 七、性能与限制

### 性能指标

| 环节 | 耗时 | 说明 |
|------|------|------|
| 热榜抓取（11平台） | ~15秒 | 受网络、API 响应影响 |
| RSS 抓取（4-6源） | ~30秒 | Google News RSS 在中国大陆不可达 |
| 关键词匹配 | <1秒 | Python 纯内存匹配 |
| AI 分析 | ~5-10秒 | 取决于 API 响应速度 |
| 推送通知 | <1秒 | Webhook 直推 |
| **单次全流程** | **~50-60秒** | |

### 已知限制

1. **网络限制**：Google News RSS（KUKA、机器人行业、质量认证）从中国大陆无法访问（超时）
2. **API 限制**：NewsNow API 受 Cloudflare 保护，频繁请求可能被限
3. **平台覆盖**：暂无小红书、快手、雪球等平台数据
4. **存储容量**：SQLite 本地存储，理论无上限，长期运行可清理旧数据
5. **中文编码**：已采用 UTF-8 编码，Windows 部署需注意

---

## 八、部署运维

### 初次安装

```bash
# 1. 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 2. 安装依赖
pip install -r requirements.txt
# 需额外安装的常见依赖：
# pip install pyyaml requests feedparser Jinja2

# 3. 配置环境变量
export AI_API_KEY="sk-xxx"
export AI_MODEL="deepseek/deepseek-chat"
export WEWORK_WEBHOOK_URL="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx"

# 4. 运行
./run.sh once
```

### 检查清单（出现异常时）

1. **匹配不生效**：清除 `__pycache__` 缓存 → `find . -type d -name __pycache__ -exec rm -rf {} +`
2. **RSS 零匹配**：检查 RSS 源是否可达 → `curl -I {rss_url}`，检查时区与当前时间差异
3. **AI 分析失败**：检查 API Key 是否有效、模型名称是否正确、API Base 是否可达
4. **推送失败**：检查 Webhook URL 是否有效
5. **定时不生效**：检查 `schedule.enabled: true`、crontab 是否设置正确

---

## 九、扩展指南

### 添加新的热榜平台

如果 NewsNow API 支持新 ID，在 `config.yaml` 的 `sources.hotlist` 中加入即可：
```yaml
hotlist:
  - xiaohongshu        # 如果 API 支持
  - kuaishou           # 如果 API 支持
```

### 添加新的 RSS 源

在 `config.yaml` 的 `sources.rss` 中加入：
```yaml
rss:
  - url: https://www.huxiu.com/rss/0.xml      # 虎嗅
  - url: https://www.oschina.net/news/rss     # 开源中国
```

### 自定义 AI 分析

编辑 `config/ai_analysis_prompt.txt` 修改分析策略和输出格式。
编辑 `config/ai_interests.txt` 修改关注方向。

---

## 十、相关资源

- **GitHub 仓库**：https://github.com/sansan0/TrendRadar
- **NewsNow 数据源**：https://github.com/ourongxing/newsnow
- **可视化配置编辑器**：`docs/index.html`（纯静态页面，可在浏览器打开）
- **配置文件示例**：`config/config.yaml`、`config/frequency_words.txt`

---

> 📝 *本文档为 TrendRadar v6.9.1 的完整技术参考，涵盖架构、模块、配置、部署与运维全链路。*
> *项目状态：正常运行中（热榜匹配✅ / RSS 匹配✅ / AI 分析✅ / 企业微信推送✅ / 定时尚未开启）*
