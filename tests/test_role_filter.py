#!/usr/bin/env python3
"""
测试 role_filter.py 模块
- 角色标签解析 (_parse_role_from_alias)
- 角色-关键词组映射 (get_role_group_map)
- 统计结果按角色分类 (classify_stats_by_role)
- 角色摘要生成 (get_role_summary)
- 角色标题列表获取 (get_matched_titles_by_role)
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from trendradar.core.role_filter import (
    ROLE_DEFINITIONS,
    _parse_role_from_alias,
    get_role_group_map,
    classify_stats_by_role,
    get_role_summary,
    get_matched_titles_by_role,
)
from trendradar.core.frequency import load_frequency_words


class TestRoleParse:
    def test_parse_ceo_label(self):
        """解析 [CEO:品牌声誉_美的集团] → role=CEO, display=品牌声誉 · 美的集团"""
        role, display = _parse_role_from_alias("CEO:品牌声誉_美的集团")
        assert role == "CEO", f"Expected CEO, got {role}"
        assert "品牌声誉" in display
        assert "美的集团" in display

    def test_parse_cto_label(self):
        """解析 [CTO:技术_协作机器人] → role=CTO, display=技术 · 协作机器人"""
        role, display = _parse_role_from_alias("CTO:技术_协作机器人")
        assert role == "CTO", f"Expected CTO, got {role}"

    def test_parse_cdo_label(self):
        """解析 [CDO:数字化_数字工厂] → role=CDO"""
        role, display = _parse_role_from_alias("CDO:数字化_数字工厂")
        assert role == "CDO", f"Expected CDO, got {role}"

    def test_parse_qm_label(self):
        """解析 [QM:口碑_产品质量] → role=QM"""
        role, display = _parse_role_from_alias("QM:口碑_产品质量")
        assert role == "QM", f"Expected QM, got {role}"

    def test_parse_general_label(self):
        """解析 [通用:XXX] → role=None（通用组归入全部角色）"""
        role, display = _parse_role_from_alias("通用:人形机器人")
        assert role is None, f"Expected None for 通用, got {role}"

    def test_parse_no_label(self):
        """无角色标记 → display=原字符串, role=None"""
        role, display = _parse_role_from_alias("美的集团 Midea")
        assert role is None
        assert display == "美的集团 Midea"

    def test_parse_empty_label(self):
        """空字符串 → role=None, display=''"""
        role, display = _parse_role_from_alias("")
        assert role is None
        assert display == ""


class TestRoleGroupMap:
    @classmethod
    def setup_class(cls):
        cls.role_groups, cls.group_displays = get_role_group_map()

    def test_four_roles_present(self):
        """应包含所有 4 个角色"""
        assert set(self.role_groups.keys()) == {"CEO", "CTO", "CDO", "QM"}, \
            f"Roles: {set(self.role_groups.keys())}"

    def test_ceo_has_groups(self):
        """CEO 至少应有 7 个专用组"""
        assert len(self.role_groups["CEO"]) >= 7, \
            f"CEO has {len(self.role_groups['CEO'])} groups (expected >= 7)"

    def test_cto_has_groups(self):
        """CTO 至少应有 8 个专用组"""
        assert len(self.role_groups["CTO"]) >= 8, \
            f"CTO has {len(self.role_groups['CTO'])} groups (expected >= 8)"

    def test_cdo_has_groups(self):
        """CDO 至少应有 5 个专用组"""
        assert len(self.role_groups["CDO"]) >= 5, \
            f"CDO has {len(self.role_groups['CDO'])} groups (expected >= 5)"

    def test_qm_has_groups(self):
        """质量总监至少应有 6 个专用组"""
        assert len(self.role_groups["QM"]) >= 6, \
            f"QM has {len(self.role_groups['QM'])} groups (expected >= 6)"

    def test_common_groups_in_all(self):
        """通用组（display_name 含'通用'）应出现在所有角色中"""
        # 查找 display_name 含'通用'的组
        common_groups = []
        for g in self.role_groups["CEO"]:
            dn = g.get("display_name", "")
            if "通用" in dn:
                common_groups.append(g["group_key"])
        assert len(common_groups) > 0, f"Expected some common groups in CEO, got {len(common_groups)}"
        # 验证出现在所有角色
        for role in ["CEO", "CTO", "CDO", "QM"]:
            role_keys = {g["group_key"] for g in self.role_groups[role]}
            for cg in common_groups:
                assert cg in role_keys, f"Common group '{cg}' missing from {role}"

    def test_word_groups_count(self):
        """总共应有 35 个关键词组"""
        word_groups, _, _ = load_frequency_words()
        assert len(word_groups) == 35, f"Expected 35 groups, got {len(word_groups)}"


class TestClassifyStats:
    @classmethod
    def setup_class(cls):
        cls.role_groups, _ = get_role_group_map()
        # 从每个角色取第一个实际关键词组构建 mock stats
        cls.mock_stats = []
        for role in ["CEO", "CTO", "CDO", "QM"]:
            groups = cls.role_groups.get(role, [])
            if groups:
                cls.mock_stats.append({
                    "word": groups[0]["group_key"],
                    "display_name": groups[0].get("display_name", ""),
                    "count": 3,
                    "titles": [
                        {"title": f"Test {role}", "source_name": "Test", "platform": "Test"}
                    ],
                })

    def test_classify_returns_all_roles(self):
        """分类结果应包含所有 4 个角色"""
        result = classify_stats_by_role(self.mock_stats)
        assert set(result.keys()) == {"CEO", "CTO", "CDO", "QM"}

    def test_classify_correct_role(self):
        """每个 stat 应正确归类到其角色（通过 display_name 中的角色关键词反查）"""
        result = classify_stats_by_role(self.mock_stats)
        # 检查每个角色下至少有一个 stat
        for role in ["CEO", "CTO", "CDO", "QM"]:
            assert len(result[role]) >= 1, f"No stats classified as {role}"
        # 验证 CTO 组的 display_name 含'技术'等关键词
        cto_display_names = [s.get("display_name", "") for s in result["CTO"]]
        cto_combined = " ".join(cto_display_names)
        assert any(kw in cto_combined for kw in ["技术", "协作", "具身"]), \
            f"CTO display_names don't look technical: {cto_display_names}"
        # 验证 QM 组的 display_name 含'口碑'/'质量'/'供应链'等
        qm_display_names = [s.get("display_name", "") for s in result["QM"]]
        qm_combined = " ".join(qm_display_names)
        assert any(kw in qm_combined for kw in ["口碑", "质量", "供应链", "客户", "标准"]), \
            f"QM display_names don't look quality-related: {qm_display_names}"

    def test_empty_stats(self):
        """空 stats 列表应返回空结果"""
        result = classify_stats_by_role([])
        for role in result.values():
            assert role == []


class TestGetRoleSummary:
    @classmethod
    def setup_class(cls):
        cls.role_groups, _ = get_role_group_map()
        cls.mock_stats = []
        for role in ["CEO", "CTO", "CDO", "QM"]:
            groups = cls.role_groups.get(role, [])
            if groups:
                cls.mock_stats.append({
                    "word": groups[0]["group_key"],
                    "display_name": groups[0].get("display_name", ""),
                    "count": 2,
                    "titles": [
                        {"title": f"Title1 {role}", "source_name": "Test", "platform": "Test"},
                        {"title": f"Title2 {role}", "source_name": "Test", "platform": "Test"},
                    ],
                })
        cls.summary = get_role_summary(cls.mock_stats)

    def test_summary_four_roles(self):
        """摘要应包含 4 个角色"""
        assert len(self.summary) == 4, f"Expected 4 roles, got {len(self.summary)}"

    def test_summary_has_required_fields(self):
        """每个角色条目应包含必要字段"""
        for entry in self.summary:
            assert "role" in entry
            assert "name" in entry
            assert "label" in entry
            assert "color" in entry
            assert "title_count" in entry
            assert "has_items" in entry

    def test_summary_title_count(self):
        """至少应有 4 条标题（每角色 2 条）"""
        total = sum(e["title_count"] for e in self.summary)
        assert total >= 4, f"Expected >= 4 titles, got {total}"

    def test_summary_colors(self):
        """角色颜色应各不相同"""
        colors = {e["role"]: e["color"] for e in self.summary}
        assert len(set(colors.values())) == 4, "Colors should be unique per role"

    def test_empty_summary(self):
        """空 stats → 所有角色 has_items=False"""
        summary = get_role_summary([])
        for entry in summary:
            assert entry["has_items"] == False
            assert entry["title_count"] == 0
