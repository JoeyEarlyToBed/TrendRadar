# macOS 部署 TrendRadar 全攻略：AI 角色化仪表盘，工业质量人的私有情报局

> 矩阵精选 · 首发

大家好，我是尤晓昳，库卡中国（KUKA China）质量部门的数字化推进工程师。

在工业制造领域，信息差就是成本。机器人行业的供应链波动、竞品技术路线转向、地缘政策变化、质量事故回溯——这些信息散落在几十个平台里。每天刷一遍头条、知乎、微博、36氪、华尔街见闻、海外科技博客……一天下来，大部分时间花在了"看"而不是"判断"上。

更要命的是，同一组信息，CEO 想看品牌声誉和资本市场信号，CTO 关心技术路线和竞品动态，CDO 关注数字化叙事和 AI 应用，质量总监紧盯客户口碑和供应链风险。**四双眼睛看同一份报告，能抓到的要点完全不同。**

[GitHub 上 4.3 万 Star 的 TrendRadar](https://github.com/sansan0/TrendRadar) 提供了一个完美的底座：多平台热点聚合 + 关键词过滤 + AI 分析 + 多端推送。但它缺了一样东西——**角色视角**。

所以我对它做了一次深度二次开发：**"同一个底座，不同仪表盘"**。

![展示页面截图 - 替换为实际截图]

这篇文章，我就从头到尾复盘一遍：从 macOS 原生部署（不用 Docker），到角色化仪表盘的改造思路和代码实现，再到 launchd 定时调度上去。全流程可复现，附完整配置和避坑指南。

---

## 一、为什么用 macOS 原生部署？

网上大多数 TrendRadar 教程走的是 **Docker + NAS** 路线。但我的场景有几个特殊需求：

| 场景 | Docker/NAS | macOS 原生 |
|------|-----------|-------------|
| 网络环境 | 容器内需配代理（国内 Docker Hub 超时） | 直接用 Clash 代理，零配置 |
| 定时调度 | 依赖容器内 supercronic | 用 launchd，macOS 原生自带 |
| 二次开发 | 每次改代码要重建镜像 | 直接改 `.py` 文件，即刻生效 |
| 配置文件 | 挂载卷，路径容易搞混 | 本地目录，所见即所得 |
| 本地浏览 HTML | 需要端口映射 | 浏览器直开 `file://` 或 `python3 -m http.server` |

**结论**：如果你是在 macOS 上做二次开发、频繁改配置、需要快速迭代，原生部署远比 Docker 高效。

---

## 二、环境准备

```bash
# 1. 克隆项目（或从我的 fork 下载）
git clone https://github.com/JoeyEarlyToBed/TrendRadar.git
cd TrendRadar

# 2. 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 验证安装
python -m trendradar --help
```

依赖很简单：Python 3.10+、requests、beautifulsoup4、litellm（AI 调度）、pyyaml。不需要 JDK、不需要编译，一分钟装完。

---

## 三、核心配置：config.yaml

TrendRadar 的所有行为都由 `config/config.yaml` 控制。585 行的配置文件看起来吓人，但日常只需要关注四个模块。

### 3.1 监控平台（23 个数据源）

我配置了 23 个热榜平台，覆盖四大类：

```yaml
platforms:
  enabled: true
  sources:
    # ─── 新闻资讯 ───
    - id: "toutiao"        # 今日头条
    - id: "baidu"          # 百度热搜
    - id: "thepaper"       # 澎湃新闻
    - id: "ifeng"          # 凤凰网
    - id: "weibo"          # 微博热搜

    # ─── 财经投资 ───
    - id: "wallstreetcn-hot"  # 华尔街见闻
    - id: "cls-hot"           # 财联社
    - id: "xueqiu"            # 雪球
    - id: "gelonghui"         # 格隆汇
    - id: "jin10"             # 金十数据

    # ─── 科技行业 ───
    - id: "ithome"         # IT之家
    - id: "juejin"         # 掘金
    - id: "hackernews"     # Hacker News
    - id: "sspai"          # 少数派
    - id: "solidot"        # Solidot
    - id: "v2ex"           # V2EX
```

RSS 订阅源另外配置，我加了 IT之家 RSS、少数派 RSS、36氪、Hacker News 等：

```yaml
rss:
  enabled: true
  freshness_filter:
    enabled: true
    max_age_days: 1
  feeds:
    - id: "36kr"           # 36氪
    - id: "ithome-rss"     # IT之家 RSS
    - id: "sspai-rss"      # 少数派 RSS
    - id: "hacker-news"    # Hacker News
    - id: "ruanyifeng"     # 阮一峰的网络日志
```

> **🛑 踩坑 #1：国内网络限制**
> Google News RSS 和部分海外 RSS 源（虎嗅、品玩）在中国大陆网络下不可达（超时/403）。配置文件里我已经注释掉了不可达的源，后面会专门讲如何判断一个源是否可达。

### 3.2 报告与推送模式

```yaml
report:
  mode: "incremental"        # 增量模式：只推送新增内容，零重复
  display_mode: "keyword"    # 按关键词分组显示

notification:
  enabled: true
  channels:
    wework:
      webhook_url: "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_KEY"
      msg_type: "markdown"   # 群机器人 markdown 格式
```

增量模式是我最推荐的方式——每次只推送新出现的匹配新闻，不会重复轰炸。

### 3.3 调度系统

TrendRadar v5.0 开始支持内置调度（`schedule.preset`），配合 `timeline.yaml` 按时间段自动调整行为：

```yaml
schedule:
  enabled: true
  preset: "morning_evening"  # 全天推送 + 晚间每日汇总
```

`morning_evening` 预设的行为：
- **07:00-20:00**：正常运行，采集+AI分析+实时推送
- **20:00-22:00**：触发日汇总（daily summary），生成一份完整当日报告

---

## 四、关键词配置：从"词表"到"角色仪表盘"

这是我投入最多的改造部分。TrendRadar 原生支持 `frequency_words.txt` 做关键词过滤，但只是一个扁平词表。我把它重构为 **35 组角色标记词表**。

### 4.1 角色语法

在 `frequency_words.txt` 中使用 `[角色:分组名]` 语法：

```ini
[CEO:品牌声誉_美的集团]
美的集团
Midea
@30

[CEO:地缘政治]
地缘政治|出口管制
技术外流|技术脱钩
中美贸易|制裁
@25

[CTO:技术_协作机器人]
协作机器人|Cobot
柔性制造|人机协作|安全协作
@25

[CTO:竞争_国际竞品]
ABB|发那科|Fanuc
安川|Yaskawa
川崎|Kawasaki
@30

[CDO:数字化_数字工厂]
数字工厂|智能工厂
工业4.0|Industrie 4.0
灯塔工厂|黑灯工厂
数字孪生|Digital Twin
@25

[QM:口碑_产品质量]
质量缺陷|批次不合格
退货|投诉|索赔
质量事故|质量门
@30

[通用:人形机器人]
人形机器人
具身智能
机械臂
工业机器人
@30
```

语法说明：
- `|` 表示"或"（任一命中即可）
- `&` 表示"与"（必须同时命中）
- `@数字` 表示权重（越高越优先展示）
- `[通用:xxx]` 标记为所有四个角色共用
- 不加角色前缀（传统格式）的组也会被所有角色继承

### 4.2 角色分组逻辑

四个角色视角的热力图分布：

| 角色 | 关键词组数 | 关注重点 |
|------|-----------|---------|
| **CEO** | 13 组 | 品牌声誉、ESG合规、地缘政治、资本市场 |
| **CTO** | 17 组 | 技术路线、协作/人形机器人、竞品动态、专利标准 |
| **CDO** | 12 组 | 数字工厂、智能制造、AI质检、数据合规 |
| **QM（质量总监）** | 16 组 | 产品质量、客户投诉、供应链、认证标准 |

---

## 五、核心改造：role_filter.py

这是二次开发的核心模块。完整源码约 260 行，分四个关键函数。

### 5.1 角色解析器

```python
ROLE_ALIASES = {
    "CEO": ["CEO", "ceo", "Ceo"],
    "CTO": ["CTO", "cto", "Cto"],
    "CDO": ["CDO", "cdo", "Cdo"],
    "QM":  ["QM", "qm", "Qm", "质量", "Quality"],
}

def _parse_role_from_alias(group_alias: str):
    """[CEO:品牌声誉_美的集团] → ("CEO", "品牌声誉 · 美的集团")"""
    if not group_alias or ":" not in group_alias:
        return None, group_alias or ""

    role_part, display_part = group_alias.split(":", 1)
    for canonical, aliases in ROLE_ALIASES.items():
        if role_part.strip() in aliases:
            clean_display = display_part.strip().replace("_", " · ")
            return canonical, clean_display
    return None, group_alias
```

### 5.2 角色组映射

```python
def get_role_group_map(frequency_file: str = "config/frequency_words.txt"):
    """
    加载 frequency_words.txt，按角色重组词组
    返回:
      - role_group_map: {角色名: [词组配置]}
      - group_display_map: {角色名: {group_key: display_name}}
    """
    word_groups, _, _ = load_frequency_words(frequency_file)
    role_groups = {}
    group_displays = {}

    for group in word_groups:
        display_name = group.get("display_name", "")
        if not display_name:
            continue

        role, clean_display = _parse_role_from_alias(display_name)

        if role:
            # 有角色标记 → 加入对应角色
            group["display_name"] = clean_display
            role_groups.setdefault(role, []).append(group)
            group_displays.setdefault(role, {})[group["group_key"]] = clean_display
        else:
            # [通用:xxx] 或传统格式 → 加入所有角色
            for r in ROLE_DEFINITIONS:
                role_groups.setdefault(r, []).append(group)

    return role_groups, group_displays
```

### 5.3 新闻按角色分类

```python
def get_role_summary(stats, frequency_file="config/frequency_words.txt"):
    """
    生成多角色摘要数据（供 HTML 模板使用）
    返回: [{role, name, label, color, title_count, titles, has_items}, ...]
    """
    role_stats = classify_stats_by_role(stats, frequency_file)
    matched_titles = get_matched_titles_by_role(stats, frequency_file)

    summary = []
    for role_key, role_def in ROLE_DEFINITIONS.items():
        role_title_list = matched_titles.get(role_key, [])
        # 去重：同一条新闻可能匹配多个关键词
        seen = {}
        for t in role_title_list:
            key = f"{t['platform']}:{t['title']}"
            if key not in seen:
                seen[key] = t

        summary.append({
            "role": role_key,
            "name": role_def["name"],
            "label": role_def["label"],
            "color": role_def["color"],
            "keyword_count": len(role_stats.get(role_key, [])),
            "title_count": len(seen),
            "has_items": len(seen) > 0,
            "titles": list(seen.values()),
        })
    return summary
```

### 5.4 注入主流程

在 `trendradar/core/context.py` 中注入角色数据：

```python
from trendradar.core.role_filter import get_role_summary

# 在 build_report_context 中添加：
role_summary = get_role_summary(stats)
word_role_map = get_word_role_map(stats)
context["role_summary"] = role_summary
context["word_role_map"] = word_role_map
```

HTML 模板中增加角色 Tab 栏：

```html
<!-- 角色 Tab 栏 -->
<div class="role-tab-bar">
  {% for role_info in role_summary %}
  <button class="role-tab {% if loop.first %}active{% endif %}"
          data-role="{{ role_info.role }}"
          style="--role-color: {{ role_info.color }}">
    <span class="role-badge">{{ role_info.title_count }}</span>
    {{ role_info.name }}
  </button>
  {% endfor %}
</div>
```

配合 CSS 暗色/亮色双模式和 JS 切换逻辑，实现了点击 Tab 只看对应角色的新闻：

```javascript
// 角色过滤 JS
document.querySelectorAll('.role-tab').forEach(tab => {
  tab.addEventListener('click', () => {
    const role = tab.dataset.role;
    // 激活当前 tab
    document.querySelectorAll('.role-tab').forEach(t => t.classList.remove('active'));
    tab.classList.add('active');
    // 过滤新闻卡片
    document.querySelectorAll('.keyword-group').forEach(group => {
      group.style.display = group.dataset.role === role ? '' : 'none';
    });
  });
});
```

---

## 六、AI 分析配置

TrendRadar 通过 LiteLLM 对接几乎所有主流 AI 模型。我用的是 DeepSeek，性价比极高：

```yaml
ai:
  model: "deepseek/deepseek-chat"
  api_key: "sk-your-api-key"
  timeout: 120
  max_tokens: 5000

ai_analysis:
  enabled: true
  language: "Chinese"
  max_news_for_analysis: 150
  include_rss: false
  include_rank_timeline: true
```

> **🛑 踩坑 #2：LiteLLM 模型价格超时**
> 首次运行时会从 `raw.githubusercontent.com` 拉取模型价格表。国内网络超时没关系，LiteLLM 会自动回退到本地备份，不影响使用。

`config/ai_analysis_prompt.txt` 是发给 AI 的提示词。我把它定制为 KUKA/质量行业场景：

```
你是一位资深工业机器人行业分析师。
请从以下新闻中提炼关键信号，按角色视角组织分析：

- CEO 视角：品牌声誉信号、地缘政治风险、资本市场动向
- CTO 视角：技术路线演进、竞品产品发布、人才团队动态
- CDO 视角：数字化案例、AI+制造落地、数据合规风险
- 质量总监视角：质量事故预警、供应链中断信号、标准法规更新

输出格式：
1. 【CEO 视角】战略风险与市场信号
2. 【CTO 视角】技术路线与竞品动态
3. 【CDO 视角】数字化演进与应用落地
4. 【QM 视角】质量风险与供应链预警
5. 【交叉信号】跨视角关联
```

---

## 七、推送配置：企业微信

我选择企业微信作为通知渠道（群机器人 webhook，markdown 格式），配置在 `config.yaml`：

```yaml
notification:
  enabled: true
  channels:
    wework:
      webhook_url: "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_KEY"
      msg_type: "markdown"
```

推送效果：

```
# 【CEO视角】3 条
> 美的集团卷入反倾销调查...  [微博]
> 库卡收购后整合三年效果评估...  [华尔街见闻]
> 工业机器人板块全线飘红...  [雪球]

# 【CTO视角】7 条
> ABB发布新一代协作机器人...  [IT之家]
> 宇树科技人形机器人完成B轮融资...  [36氪]
> ...
```

> **🛑 踩坑 #3：企业微信推送分批次**
> 企业微信单条消息上限 4096 字节。匹配新闻较多时，TrendRadar 会自动分批次发送（2-3 条消息）。日志里看到 `企业微信消息分为 2 批次发送` 是正常的。

---

## 八、定时调度：macOS launchd

Docker 方案的定时任务用 `supercronic`，但你也可以直接在 **macOS 上用 launchd**——系统自带，零依赖，不需要 crontab。

### 8.1 创建 plist

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
 "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.trendradar.crawler</string>
    <key>ProgramArguments</key>
    <array>
        <string>/path/to/.venv/bin/python</string>
        <string>-m</string>
        <string>trendradar</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/path/to/TrendRadar</string>
    <key>StartInterval</key>
    <integer>1800</integer>
    <key>RunAtLoad</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/path/to/TrendRadar/output/daemon.log</string>
    <key>StandardErrorPath</key>
    <string>/path/to/TrendRadar/output/daemon.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PYTHONUNBUFFERED</key>
        <string>1</string>
        <key>PATH</key>
        <string>/usr/bin:/bin:/usr/sbin:/sbin:/usr/local/bin</string>
    </dict>
</dict>
</plist>
```

### 8.2 加载与日常管理

```bash
# 安装（首次）
cp com.trendradar.crawler.plist ~/Library/LaunchAgents/
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.trendradar.crawler.plist

# 手动触发一次
launchctl kickstart gui/$(id -u)/com.trendradar.crawler

# 查看状态
launchctl print gui/$(id -u)/com.trendradar.crawler | grep -E 'state|interval'

# 卸载
launchctl bootout gui/$(id -u)/com.trendradar.crawler
```

`StartInterval=1800` 表示每 30 分钟执行一次。配合 `schedule.preset: morning_evening`，程序内部会根据当前时间自动决定行为（白天实时推送，晚间日汇总）。

> **🛑 踩坑 #4：crontab 写入被 macOS 安全策略拦截**
> `crontab -` 管道写入会触发 macOS 的 Full Disk Access 限制，进程直接被 SIGTERM。换成 launchd plist 彻底解决问题——它是系统级调度框架，权限和生命周期都更靠谱。

> **🛑 踩坑 #5：`output/cron.log` 是目录**
> 之前创建了一个 `output/cron.log/` 目录占位，导致 launchd 的 stdout 写不进去，退出码 78（配置错误）。改成 `daemon.log` 文件名并加 `PYTHONUNBUFFERED=1` 环境变量解决。

---

## 九、踩坑经验总结

这一路踩了不少坑，记录在此供参考：

| 坑 | 现象 | 根因 | 解法 |
|----|------|------|------|
| **RSS 匹配零命中** | 关键词明明在标题里，但没有命中 | `__pycache__` 缓存了旧版模块 | 删除 `__pycache__/` 和 `.pyc` 文件 |
| **Google News RSS 超时** | 3 个 Google News 源全部超时不可达 | 中国大陆网络限制（google.com 被墙） | 已注释；可配代理或换国内 RSS 源 |
| **参考消息/联合早报安全警告** | "安全警告：域名校验失败" | NewsNow API 返回的链接域名与预期不符 | 上游问题，数据已自动丢弃不处理 |
| **GitHub Push Protection** | push 被拦截，提示"secret detected" | README 中示例 Webhook URL 看起来像真实密钥 | 替换为 `XXXX...XXXX` 模糊占位 |
| **crontab 无法写入** | `crontab -` 被 SIGTERM 杀死 | macOS Full Disk Access 限制 | 改用 launchd plist |
| **LiteLLM 模型价格表超时** | 启动时显示 `Failed to fetch remote model cost map` | `raw.githubusercontent.com` 国内不可达 | 不影响使用，自动回退本地备份 |

---

## 十、二次开发指南

如果你也想做类似改造，以下几点可能对你有帮助：

### 10.1 架构概览

```
TrendRadar/
├── config/
│   ├── config.yaml            # 主配置（平台、AI、通知、调度）
│   ├── frequency_words.txt    # 关键词（我的版本有角色标记）
│   ├── timeline.yaml          # 调度时间线
│   └── ai_analysis_prompt.txt # AI 分析提示词
├── trendradar/
│   ├── core/
│   │   ├── context.py         # 报告数据构建（注入 role_summary）
│   │   ├── role_filter.py     # ★ 我的二次开发模块
│   │   ├── frequency.py       # 关键词匹配引擎
│   │   └── html.py            # HTML 报告渲染（角色 Tab）
│   ├── crawlers/              # 爬虫模块
│   ├── notification/          # 推送通知模块
│   └── web/                   # Web 服务器
└── output/                    # 输出目录（数据 + 报告 + 日志）
```

### 10.2 数据流

```
热榜API (newsnow) + RSS源
  ↓ 采集并存入 SQLite
关键词匹配 (frequency.py)
  ↓ 匹配到的标题 + stats
角色过滤 (role_filter.py)        ← 我的改造
  ↓ 按4个角色分类 + 摘要数据
上下文注入 (context.py)
  ↓ 注入 role_summary, word_role_map
AI分析 + HTML报告 + 企业微信推送
```

### 10.3 自建 MCP 服务

TrendRadar 还提供了 MCP Server（`trendradar-mcp` 镜像），可以接入 Claude Desktop、Cursor 等 AI 工具进行对话式数据查询。Docker 部署的话直接 `docker-compose.yml` 里加 `trendradar-mcp` 服务即可。

### 10.4 完整代码

我的 fork 仓库（含角色化仪表盘全部改造）：

**GitHub**: [https://github.com/JoeyEarlyToBed/TrendRadar](https://github.com/JoeyEarlyToBed/TrendRadar)

关键文件列表：
- `config/frequency_words.txt` — 35 组角色标记关键词
- `trendradar/core/role_filter.py` — 角色过滤模块（260 行）
- `trendradar/core/html.py` — HTML 报告的角色 Tab 注入（+157 行）
- `trendradar/core/context.py` — 报告上下文的角色数据注入
- `com.trendradar.crawler.plist` — macOS launchd 调度配置
- `tests/test_role_filter.py` — 角色过滤测试（34 个测试用例）

---

## 十一、效果验证

部署完成后的首次全流程运行日志：

```
获取 toutiao 成功（缓存数据）
获取 baidu 成功（缓存数据）
...
成功: ['toutiao', 'baidu', ...21个平台]
[RSS] 抓取完成: 5 个源成功, 共 113 条
[本地存储] 热榜处理完成：新增 0 条，更新 522 条
[RSS] 检测到 63 条新增
[RSS] 关键词分组统计：0/63 条匹配
[调度] 时间段: morning_evening · 行为: 采集+分析+推送
当前榜单模式: 522 条中有 19 条频率词匹配
[AI] 正在进行 AI 分析... (deepseek/deepseek-chat)
[AI] 分析完成
HTML报告已生成: output/html/2026-06-16/19-57.html
[推送] 热榜 19 条
企业微信消息分为 2 批次发送 [当前榜单]
企业微信第 1/2 批次发送成功
企业微信第 2/2 批次发送成功
企业微信所有 2 批次发送完成 [当前榜单]
```

一次运行，3 分钟完成全流程：23 个平台热榜采集 → 522 条当前榜单 → 19 条精准命中 → AI 分析 → 企业微信 2 批次推送。

---

## 结语

以前我们是算法的猎物，被头条、微博、抖音的推荐算法牵着鼻子走。

现在借助 TrendRadar + AI 分析，我们终于可以翻身成为信息的主人——不仅可以主动定义"什么值得关注"，还能让同一个信息底座为不同角色（CEO / CTO / CDO / 质量总监）提供定制化视角。

如果你也是制造业从业者、投资研究、自媒体运营，或者只是想从信息洪流中圈出一块清醒的自留地——不妨试试这套方案。

> 如有问题，欢迎到 [GitHub Issues](https://github.com/JoeyEarlyToBed/TrendRadar/issues) 讨论。
>
> 我的 fork 仓库：[https://github.com/JoeyEarlyToBed/TrendRadar](https://github.com/JoeyEarlyToBed/TrendRadar)
>
> 原项目：[https://github.com/sansan0/TrendRadar](https://github.com/sansan0/TrendRadar)
