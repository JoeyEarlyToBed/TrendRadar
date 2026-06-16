#!/usr/bin/env python3
"""
测试 HTML 报告的角色仪表盘 Tab 渲染
- 角色 Tab 栏 HTML 结构
- 角色过滤 JavaScript
- 角色徽章 (role-badge) CSS
- 角色 data-attribute 注入
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from trendradar.report.html import render_html_content
from trendradar.core.role_filter import get_role_summary, classify_stats_by_role, get_role_group_map
from trendradar.core.frequency import load_frequency_words


def _build_html_with_roles():
    """构建带角色数据的测试 HTML"""
    word_groups, _, _ = load_frequency_words()
    role_groups_map, _ = get_role_group_map()

    mock_stats = []
    for role, groups in role_groups_map.items():
        for g in groups[:2]:
            mock_stats.append({
                "word": g["group_key"],
                "display_name": g.get("display_name", ""),
                "count": 2,
                "titles": [
                    {"title": f"[{role}] {g['group_key'][:30]}", "source_name": "Test",
                     "platform": "Test", "rank": 1, "count": 2}
                ],
            })

    word_role_map = {}
    role_stats_map = classify_stats_by_role(mock_stats)
    for role, stats in role_stats_map.items():
        for s in stats:
            w = s.get("word", "")
            if w:
                word_role_map[w] = role

    role_summary = get_role_summary(mock_stats)
    report_data = {
        "stats": mock_stats,
        "new_titles": [],
        "failed_ids": [],
        "total_new_count": 0,
        "_word_role_map": word_role_map,
    }
    html = render_html_content(
        report_data=report_data,
        total_titles=len(mock_stats),
        mode="incremental",
        role_summary=role_summary,
    )
    return html, role_summary


class TestRoleTabBar:
    def setup_method(self):
        self.html, self.role_summary = _build_html_with_roles()

    def test_role_tab_bar_exists(self):
        assert 'class="role-tab-bar"' in self.html, "role-tab-bar missing in HTML"
        assert 'role-tab-btn' in self.html, "role-tab-btn missing"

    def test_all_role_button(self):
        assert "全部角色" in self.html, "全部角色 button missing"

    def test_ceo_tab(self):
        assert 'data-role="CEO"' in self.html, "CEO tab missing"

    def test_cto_tab(self):
        assert 'data-role="CTO"' in self.html, "CTO tab missing"

    def test_cdo_tab(self):
        assert 'data-role="CDO"' in self.html, "CDO tab missing"

    def test_qm_tab(self):
        assert 'data-role="QM"' in self.html, "QM tab missing"

    def test_tab_count_badge(self):
        for entry in self.role_summary:
            count = entry.get("title_count", 0)
            if count > 0:
                assert str(count) in self.html, f"Count {count} not found"

    def test_role_badge_spans(self):
        assert 'class="role-badge' in self.html, "role-badge span missing"

    def test_role_data_attributes(self):
        assert 'data-role=' in self.html, "data-role missing on word groups"

    def test_role_filter_javascript(self):
        assert "filterByRole" in self.html, "filterByRole JS function missing"

    def test_role_css_classes(self):
        for check in ["role-tab-btn", "role-badge"]:
            assert check in self.html, f"CSS class '{check}' missing"

    def test_html_length(self):
        assert len(self.html) > 1000, "HTML output too short"

    def test_proper_html(self):
        assert "<html" in self.html, "Not a valid HTML document"


class TestBackwardCompat:
    def test_render_without_role(self):
        """在没有 role_summary 参数时不应崩溃"""
        html = render_html_content(
            report_data={"stats": [], "new_titles": [], "failed_ids": [],
                        "total_new_count": 0, "_word_role_map": {}},
            total_titles=0,
        )
        assert len(html) > 500

    def test_equal_role_rendering(self):
        """两次渲染同数据应输出相同"""
        data = {"stats": [], "new_titles": [], "failed_ids": [],
                "total_new_count": 0, "_word_role_map": {}}
        h1 = render_html_content(report_data=data, total_titles=0)
        h2 = render_html_content(report_data=data, total_titles=0)
        assert h1 == h2
