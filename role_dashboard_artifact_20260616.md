# TrendRadar 角色化仪表盘改造 — 完成

## 目标
"同一个底座，不同仪表盘"：基于现有关键词匹配数据底座，为不同角色（CEO/CTO/CDO/质量总监）提供各自关注的仪表盘视图。

## 修改内容

### 1. `config/frequency_words.txt` — 关键词角色标记（35 组）
- 将原有 17 个关键词组扩展为 35 个带 `[角色:子主题]` 标签的组
- CEO（7 组）：品牌声誉、ESG、地缘政治、资本市场
- CTO（10 组）：协作机器人、具身智能、竞品、专利、人才
- CDO（6 组）：数字工厂、智能制造、AI 质检、数据合规
- QM（7 组）：产品质量、客户反馈、供应链风险、标准认证
- 通用（5 组）：人形机器人、智能制造、机器人行业、美的、库卡
- 全局过滤词：震惊、惊爆、刚发生

### 2. `trendradar/core/role_filter.py` — 角色过滤模块（新增 261 行）
- `_parse_role_from_alias()` — 解析 `[CEO:子主题]` 标签语法
- `get_role_group_map()` — 将关键词组按角色归类（含通用组自动加入所有角色）
- `classify_stats_by_role()` — 将匹配统计结果按角色分类
- `get_role_summary()` — 生成供 HTML 使用的角色摘要数据
- `get_matched_titles_by_role()` — 按角色获取详细标题列表

### 3. `trendradar/report/html.py` — HTML 报告角色标签页（CSS + JS + HTML）
- **角色 Tab 栏**：位于关键词 Tab 栏上方，左侧彩色边框区分四种角色
- **角色徽章**：每个关键词组旁显示角色彩色徽章（CEO=红/CTO=蓝/CDO=绿/QM=黄）
- **角色过滤 JS**：点击角色 Tab 自动过滤只显示该角色的关键词组
- **角色 CSS**：支持亮色/暗色模式，自适应布局
- **`data-role` 属性**：每个 word-group div 携带角色标识

### 4. `trendradar/context.py` — 上下文注入
- 在 `render_html()` 中自动计算 `role_summary` 和 `word_role_map`
- 数据通过 `report_data["_word_role_map"]` 和 `role_summary` 参数传入 HTML

### 5. `config/ai_interests.txt` — 兴趣描述更新（KUKA 质量场景）
- 聚焦库卡、美的、工业机器人、数字化质量管理、供应链安全
- 涵盖 10 个核心关注方向

## 核心设计

- **Word first**：关键词匹配完全基于 frequency_words.txt 实现，不改动匹配逻辑
- **纯前端筛选**：角色标签页通过 JavaScript 控制 CSS `display`，不改变后端数据流
- **角色与关键词自动对应**：通过 `[CEO:子主题]` 标签语法自动解析归属
- **通用组自动继承**：标记为 `[通用:X]` 或无名组的自动加入所有角色

## 验证结果
- 模块语法检查通过 ✅
- 角色分类逻辑正确 ✅（35 组 → CEO 13 组 / CTO 16 组 / CDO 12 组 / QM 13 组）
- HTML 生成 9 项检查全部通过 ✅
- 全部集成测试通过 ✅

## 文件状态
- `role_filter.py`: 261 行 (新)
- `html.py`: 3374 行 (+157)
- `context.py`: 1166 行 (+23)
- `frequency_words.txt`: 234 行 (重构)
- `ai_interests.txt`: 25 行 (重写)
