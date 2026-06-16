# TrendRadar 变更日志

## [v6.10.0] — 2026-06-16 — 角色化仪表盘 + 数据源扩展

### ✨ 新增功能

#### 角色化仪表盘（"同一个底座，不同仪表盘"）
- **关键词角色标签系统**：`frequency_words.txt` 全部 35 个关键词组带 `[角色:子主题]` 标记
  - CEO（品牌声誉/ESG/地缘政治/资本市场 — 7 组 + 5 通用）
  - CTO（协作机器人/具身智能/竞品/专利/人才 — 10 组 + 5 通用）
  - CDO（数字工厂/智能制造/AI 质检/数据合规 — 6 组 + 5 通用）
  - 质量总监（产品质量/客户反馈/供应链风险/标准认证 — 7 组 + 5 通用）
- **新的 `role_filter.py` 模块**（trendradar/core/role_filter.py）：
  - `_parse_role_from_alias()` — 解析 `[CEO:子主题]` 标签
  - `get_role_group_map()` — 关键词组按角色归类
  - `classify_stats_by_role()` — 匹配统计结果按角色分类
  - `get_role_summary()` — 生成 HTML 角色摘要数据
- **HTML 报告角色仪表盘**（trendradar/report/html.py）：
  - 角色 Tab 栏（位于关键词 Tab 栏上方，彩色边框）
  - 角色过滤 JavaScript（点击 Tab 只显示对应角色数据）
  - 彩色角色徽章（CEO=红方/CTO=蓝方/CDO=绿方/QM=黄方）
  - 暗色模式兼容
- **context.py 数据注入**：自动计算 `role_summary` 和 `word_role_map`

#### 数据源扩展
- **热榜平台增加到 23 个**：新增雪球、格隆汇、金十数据、IT之家、掘金、Hacker News、少数派、Solidot、V2EX、虎扑、参考消息、联合早报
- **RSS 源新增 IT之家和少数派**：已验证运行及关键词匹配
- **`ai_interests.txt` 重写**：聚焦 KUKA 质量工程场景（10 个维度）

### 🐛 问题修复
- 修复 RSS 新源 ID 与热榜平台冲突（`ithome`→`ithome-rss` / `sspai`→`sspai-rss`）
- 修复 `__pycache__` 缓存导致 RSS 关键词匹配零命中（清空缓存后恢复）
- 修复 `role_filter.py` 中 `get_matched_titles_by_role` 的标题统计兼容 list/dict 两种格式
- 修复 `get_role_group_map` 跳过空 `display_name` 的段落标记
- 修复 `html.py` 中 `role_attr` 和 `role_badge` 变量未在循环前定义

### 🔧 配置变更
- `config/frequency_words.txt`: 从 17 组扩展到 35 组，全部带角色标签
- `config/config.yaml`: 新增 12 个热榜平台 + 2 个 RSS 源配置、增量模式
- `config/ai_interests.txt`: 重写为 KUKA/质量场景
- `docker/.env`: 更新为增量模式 + WeChat Work 推送配置

### 📝 文档
- 新增 `docs/TrendRadar技术架构与功能完全手册.md`（约 21KB，10 章）
- 新增 `docs/project_page.html`（深色工业风 + KUKA 橙色系技术展示页）
- 新增 `CHANGELOG.md`（本文档）
