# TrendRadar 问题修复日志

## 2026-06-16

### 1. RSS 关键词匹配零命中
**症状**：新增 IT之家 RSS 源后，AI 分析报告显示 RSS 采集数正常但匹配结果为 0。
**根因**：`__pycache__` 目录下的 `.pyc` 字节码缓存了旧版本的 `trendradar/crawler/rss/` 模块，导致新添加的 RSS 源实际未被加载。即使修改了 Python 源文件，`__pycache__` 中的缓存也可能在特定情况下（如文件名 hash 碰撞）不被刷新。
**修复**：
1. 删除全项目 `__pycache__` 目录：`find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null`
2. 重新运行后 RSS 关键词匹配恢复正常（36kr 3/53 命中）
**预防**：在 `run.sh` 执行脚本中增加自动清空 `__pycache__` 的命令

### 2. RSS 新源 ID 与热榜平台冲突
**症状**：新增 `ithome` RSS 源后，发现其 `feed_id`（`ithome`）与已存在的热榜平台 `ithome`（IT之家热榜）冲突，导致 RSS 源被视为已存在而未被注册。
**根因**：TrendRadar 使用 `feed_id` 区分不同数据源，RSS 源和热榜源在同一命名空间下。
**修复**：将 RSS 源的 feed_id 改为 `ithome-rss`（少数派相应改为 `sspai-rss`），避免与同站点的热榜平台冲突。
**预防**：新增 RSS 源时应检查是否与已有热榜平台同名，如有冲突则追加 `-rss` 后缀。

### 3. role_filter.py: get_matched_titles_by_role 标题格式兼容
**症状**：`get_matched_titles_by_role` 函数中 `stat.get("titles", {}).items()` 仅处理 dict 格式（高版本），但 `count_word_frequency` 实际返回 list 格式（`[{title, source_name, ...}]`），导致 AttributeError。
**根因**：统计函数在不同版本/分支中可能返回 dict 或 list 两种格式的 titles。test 模块使用了另一种格式。
**修复**：增加 `isinstance` 判断，同时支持 dict 和 list 两种格式的 titles。
**预防**：统一 titles 格式为 list。

### 4. get_role_group_map 解析段落标记
**症状**：`get_role_group_map` 解析 `[WORD_GROUPS]`、`[GLOBAL_FILTERS]` 等段落标记时，将空 display_name 的条目也加入角色分组。
**根因**：`_parse_role_from_alias` 对无内容的段落标记返回空字符串，但调用方未过滤。
**修复**：在 `get_role_group_map` 中增加 `if not clean_display: continue` 跳过空名字的条目。

### 5. html.py 角色变量未定义
**症状**：`render_html_content` 中 `f"""<div class="word-group" ... {role_attr}> {role_badge}"""` 中的 `role_attr` 和 `role_badge` 是 f-string 占位符，但作为 Python 变量在循环前未定义。
**根因**：最初的 `.replace()` 逻辑（将模板文本替换）被错误地当成了 f-string 变量引用。f-string 解析时发现变量未定义。
**修复**：在循环中（`for i, stat in enumerate(stats, 1)`）的 f-string 前添加：
```python
role_attr = ""
role_badge = ""
stat_role = word_role_map.get(stat.get("word", ""), "")
if stat_role:
    role_attr = f' data-role="{html_escape(stat_role)}"'
    role_badge = f'<span class="role-badge role-{html_escape(stat_role)}">{html_escape(stat_role[:3])}</span>'
```
