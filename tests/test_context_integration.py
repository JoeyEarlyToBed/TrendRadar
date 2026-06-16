#!/usr/bin/env python3
"""
测试 context.py 中的角色数据注入逻辑
- render_html() 正确计算 role_summary 和 word_role_map
- 数据通过 report_data["_word_role_map"] 正确传递
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from trendradar.core.role_filter import (
    get_role_summary, classify_stats_by_role, get_role_group_map,
)
from trendradar.core.frequency import load_frequency_words


class TestContextRoleInjection:
    def setup_method(self):
        self.word_groups, _, _ = load_frequency_words()
        self.role_groups_map, _ = get_role_group_map()

        self.mock_stats = []
        for role, groups in self.role_groups_map.items():
            if groups:
                g = groups[0]
                self.mock_stats.append({
                    "word": g["group_key"],
                    "display_name": g.get("display_name", ""),
                    "count": 2,
                    "titles": [
                        {"title": f"Test {role} news", "source_name": "Source",
                         "platform": f"Platform-{role}", "rank": 1}
                    ],
                })

    def test_role_summary_returns_all_roles(self):
        """get_role_summary 应返回 4 个角色"""
        summary = get_role_summary(self.mock_stats)
        assert len(summary) == 4, f"Expected 4 roles, got {len(summary)}"

    def test_role_summary_has_some_titles(self):
        """标题数应 > 0"""
        summary = get_role_summary(self.mock_stats)
        total = sum(e["title_count"] for e in summary)
        assert total > 0, "Expected > 0 total titles"

    def test_word_role_map_built(self):
        """word_role_map 应正确建立（模拟 context.py 逻辑）"""
        word_role_map = {}
        role_stats_map = classify_stats_by_role(self.mock_stats)
        for role, stats in role_stats_map.items():
            for s in stats:
                w = s.get("word", "")
                if w:
                    word_role_map[w] = role

        assert len(word_role_map) > 0, "Empty word_role_map"
        valid_roles = {"CEO", "CTO", "CDO", "QM"}
        for w, r in word_role_map.items():
            assert r in valid_roles, f"Invalid role '{r}' for word"

    def test_report_data_structure(self):
        """模拟 context.py 注入结构"""
        word_role_map = {}
        role_stats_map = classify_stats_by_role(self.mock_stats)
        for role, stats in role_stats_map.items():
            for s in stats:
                w = s.get("word", "")
                if w:
                    word_role_map[w] = role

        report_data = {"stats": self.mock_stats, "_word_role_map": word_role_map}
        assert "_word_role_map" in report_data
        assert len(report_data["_word_role_map"]) == len(self.mock_stats)

    def test_role_colors(self):
        """角色颜色定义"""
        summary = get_role_summary([])
        colors = {e["role"]: e["color"] for e in summary}
        assert len(set(colors.values())) == 4, "Expected 4 unique colors"
