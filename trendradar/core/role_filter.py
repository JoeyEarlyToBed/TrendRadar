# coding=utf-8
"""
角色过滤模块 — "同一底座，不同仪表盘"

实现多角色关键词分组功能。在 frequency_words.txt 中使用 [角色:分组名] 语法
标记每个词组属于哪个角色，支持以下角色：
  - CEO  : 品牌声誉 / ESG / 地缘政治 / 资本市场
  - CTO  : 技术路线 / 竞争格局 / 人才信号
  - CDO  : 数字化叙事 / AI应用 / 数据合规
  - QM   : 质量总监 — 客户口碑 / 供应链风险

用法:
  >>> from trendradar.core.role_filter import RoleFilter
  >>> rf = RoleFilter("config/frequency_words.txt")
  >>> cto_groups = rf.get_role_groups("CTO")      # 仅 CTO 的词组
  >>> matched = rf.classify_matched_titles(stats)  # 为每条匹配新闻标记角色
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from trendradar.core.frequency import load_frequency_words, matches_word_groups


# 角色定义
ROLE_DEFINITIONS = {
    "CEO": {
        "name": "CEO视角",
        "label": "品牌声誉 · 资本市场 · 地缘政治",
        "description": "企业声誉、ESG合规、地缘风险、市值与资本市场信号",
        "color": "#e74c3c",       # 红色 — 战略/风险
    },
    "CTO": {
        "name": "CTO视角",
        "label": "技术路线 · 竞争格局 · 人才信号",
        "description": "技术发展、竞品动态、专利标准、技术人才流动",
        "color": "#2980b9",       # 蓝色 — 技术/理性
    },
    "CDO": {
        "name": "CDO视角",
        "label": "数字化叙事 · AI应用 · 数据合规",
        "description": "数字化转型、工业AI、数字工厂、数据治理",
        "color": "#27ae60",       # 绿色 — 创新/增长
    },
    "QM": {
        "name": "质量总监视角",
        "label": "客户口碑 · 供应链风险",
        "description": "质量缺陷、客户投诉、供应链中断、标准认证",
        "color": "#f39c12",       # 橙色 — 预警/警示
    },
}

ROLE_ALIASES = {
    "CEO": ["CEO", "ceo", "Ceo"],
    "CTO": ["CTO", "cto", "Cto"],
    "CDO": ["CDO", "cdo", "Cdo"],
    "QM":  ["QM", "qm", "Qm", "质量", "Quality"],
}


def _parse_role_from_alias(group_alias: str) -> Tuple[Optional[str], str]:
    """
    从组别名中解析角色前缀和显示名
    [CEO:品牌声誉_美的集团] → ("CEO", "品牌声誉 · 美的集团")

    Args:
        group_alias: 组别名 (如 "CEO:品牌声誉_美的集团")

    Returns:
        (角色名或None, 纯显示名)
    """
    if not group_alias or ":" not in group_alias:
        return None, group_alias or ""

    role_part, display_part = group_alias.split(":", 1)

    # 规范化角色名
    for canonical, aliases in ROLE_ALIASES.items():
        if role_part.strip() in aliases:
            # 将下划线替换为更美观的分隔符
            clean_display = display_part.strip().replace("_", " · ")
            return canonical, clean_display

    return None, group_alias


def get_role_group_map(
    frequency_file: str = "config/frequency_words.txt",
) -> Tuple[Dict[str, List[Dict]], Dict[str, str]]:
    """
    加载并解析频率词文件，按角色分组

    Returns:
        (role_group_map, group_display_map):
        - role_group_map: {角色名: [词组配置列表]}
        - group_display_map: {角色名: {group_key: display_name}}
    """
    word_groups, _, _ = load_frequency_words(frequency_file)

    role_groups: Dict[str, List[Dict]] = {}
    group_displays: Dict[str, Dict[str, str]] = {}

    for group in word_groups:
        group_key = group["group_key"]
        # 从 display_name 中解析角色
        display_name = group.get("display_name", group_key)

        if not display_name:
            # 跳过无别名的段落标记（如 [WORD_GROUPS] 的遗留空组）
            continue

        role, clean_display = _parse_role_from_alias(display_name or group_key)

        if role:
            # 有角色标记：加入对应角色的组
            if role not in role_groups:
                role_groups[role] = []
                group_displays[role] = {}

            # 修正 display_name
            group["display_name"] = clean_display
            role_groups[role].append(group)
            group_displays[role][group_key] = clean_display
        else:
            # 无角色标记（如 [通用:...]）：加入所有角色
            for r in ROLE_DEFINITIONS:
                if r not in role_groups:
                    role_groups[r] = []
                    group_displays[r] = {}
                role_groups[r].append(group)
                if clean_display not in group_displays[r] and group_key not in group_displays[r]:
                    group_displays[r][group_key] = clean_display

    return role_groups, group_displays


def classify_stats_by_role(
    stats: List[Dict],
    frequency_file: str = "config/frequency_words.txt",
) -> Dict[str, List[Dict]]:
    """
    将关键词匹配统计结果按角色分类

    从每个 stat 的 word 字段反查其归属 role
    如果某 stat 匹配了多个角色的关键词，按顺序取第一个匹配的角色
    通用组会出现在所有角色中

    Args:
        stats: count_word_frequency 返回的统计结果
        frequency_file: 频率词文件路径

    Returns:
        {角色名: [属于该角色的 stats]}
    """
    role_groups, _ = get_role_group_map(frequency_file)

    # 建立 group_key → role 的映射
    group_to_role: Dict[str, str] = {}
    for role, groups in role_groups.items():
        for group in groups:
            group_key = group["group_key"]
            if group_key not in group_to_role:
                group_to_role[group_key] = role

    # 分类 stats
    role_stats: Dict[str, List[Dict]] = {r: [] for r in ROLE_DEFINITIONS}
    for stat in stats:
        stat_word = stat.get("word", "")
        if stat_word in group_to_role:
            role = group_to_role[stat_word]
            role_stats[role].append(stat)
        else:
            # 无法确定的 stat 放到 CEO 下（兜底）
            role_stats["CEO"].append(stat)

    return role_stats


def get_matched_titles_by_role(
    stats: List[Dict],
    frequency_file: str = "config/frequency_words.txt",
) -> Dict[str, List[Dict]]:
    """
    获取每个角色匹配到的具体标题列表

    Returns:
        {角色名: [{title, platform, url, ...}, ...]}
    """
    role_stats = classify_stats_by_role(stats, frequency_file)
    result = {}
    for role, role_stat_list in role_stats.items():
        titles = []
        for stat in role_stat_list:
            raw_titles = stat.get("titles", [])
            if isinstance(raw_titles, dict):
                # dict 格式: {title: title_data}
                for title, title_data in raw_titles.items():
                    titles.append({
                        "title": title,
                        "platform": title_data.get("platform", ""),
                        "url": title_data.get("url", ""),
                        "count": title_data.get("count", 1),
                        "rank": title_data.get("rank", 0),
                        "keyword": stat.get("word", ""),
                        "keyword_display": stat.get("display_name", stat.get("word", "")),
                    })
            else:
                # list 格式: [{title, source_name, platform, ...}]
                for td in raw_titles:
                    titles.append({
                        "title": td.get("title", ""),
                        "platform": td.get("platform", td.get("source_name", "")),
                        "url": td.get("url", ""),
                        "count": td.get("count", 1),
                        "rank": td.get("rank", 0),
                        "keyword": stat.get("word", ""),
                        "keyword_display": stat.get("display_name", stat.get("word", "")),
                    })
        result[role] = titles
    return result


def get_role_summary(
    stats: List[Dict],
    frequency_file: str = "config/frequency_words.txt",
) -> List[Dict]:
    """
    生成多角色摘要数据（供 HTML 模板使用）

    Returns:
        [{role, name, label, color, title_count, titles, has_items}, ...]
    """
    role_stats = classify_stats_by_role(stats, frequency_file)
    matched_titles = get_matched_titles_by_role(stats, frequency_file)

    summary = []
    for role_key, role_def in ROLE_DEFINITIONS.items():
        role_stat_list = role_stats.get(role_key, [])
        role_title_list = matched_titles.get(role_key, [])

        # 去重标题（同一条新闻可能匹配多个关键词）
        seen_titles = {}
        for t in role_title_list:
            key = f"{t['platform']}:{t['title']}"
            if key not in seen_titles:
                seen_titles[key] = t

        summary.append({
            "role": role_key,
            "name": role_def["name"],
            "label": role_def["label"],
            "description": role_def["description"],
            "color": role_def["color"],
            "keyword_count": len(role_stat_list),
            "title_count": len(seen_titles),
            "has_items": len(seen_titles) > 0,
            "titles": list(seen_titles.values()),
        })

    return summary
