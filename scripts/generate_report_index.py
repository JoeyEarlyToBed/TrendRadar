#!/usr/bin/env python3
# coding=utf-8
"""
报告索引生成器

扫描 reports 目录，生成 index.json 文件，包含所有报告的元数据
用于前端矩阵/轮播/时间线展示
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


def extract_report_metadata(html_content: str) -> Dict:
    """
    从 HTML 报告中提取元数据
    
    Args:
        html_content: HTML 文件内容
    
    Returns:
        元数据字典
    """
    metadata = {
        "keywords": [],
        "preview": [],
        "title": "",
    }
    
    # 提取标题
    title_match = re.search(r'<title>(.*?)</title>', html_content, re.IGNORECASE)
    if title_match:
        metadata["title"] = title_match.group(1).strip()
    
    # 提取关键词（从 meta 标签或内容中）
    keywords_match = re.search(r'<meta[^>]*name=["\']keywords["\'][^>]*content=["\']([^"\']*)["\']', 
                                html_content, re.IGNORECASE)
    if keywords_match:
        metadata["keywords"] = [k.strip() for k in keywords_match.group(1).split(',') if k.strip()]
    
    # 提取预览内容（从热点条目中）
    # 匹配常见的标题模式
    title_patterns = [
        r'<div[^>]*class=["\'][^"\']*title[^"\']*["\'][^>]*>(.*?)</div>',
        r'<a[^>]*>(.*?)</a>',
        r'<span[^>]*class=["\'][^"\']*title[^"\']*["\'][^>]*>(.*?)</span>',
    ]
    
    for pattern in title_patterns:
        matches = re.findall(pattern, html_content, re.IGNORECASE | re.DOTALL)
        for match in matches[:5]:  # 只取前5条
            # 清理 HTML 标签
            clean_text = re.sub(r'<[^>]+>', '', match).strip()
            if clean_text and len(clean_text) > 5 and clean_text not in metadata["preview"]:
                metadata["preview"].append(clean_text)
        
        if len(metadata["preview"]) >= 5:
            break
    
    # 限制预览数量
    metadata["preview"] = metadata["preview"][:5]
    
    return metadata


def generate_reports_index(reports_dir: str, output_file: str) -> bool:
    """
    生成报告索引文件
    
    Args:
        reports_dir: 报告目录路径
        output_file: 输出索引文件路径
    
    Returns:
        是否成功
    """
    reports_path = Path(reports_dir)
    if not reports_path.exists():
        print(f"[索引生成] 报告目录不存在: {reports_dir}")
        return False
    
    reports = []
    
    # 扫描所有 HTML 文件
    for html_file in sorted(reports_path.glob("*.html"), reverse=True):
        filename = html_file.name
        
        # 解析文件名获取日期和时间
        # 支持格式: YYYYMMDD-HHMM.html 或 MM-DD-HHMM.html 等
        date_str = ""
        time_str = ""
        
        # 尝试匹配不同格式
        # 格式1: YYYYMMDD-HHMM.html (如 20250616-1530.html)
        match1 = re.match(r'(\d{4})(\d{2})(\d{2})-(\d{2})(\d{2})\.html$', filename)
        if match1:
            date_str = f"{match1.group(1)}-{match1.group(2)}-{match1.group(3)}"
            time_str = f"{match1.group(4)}:{match1.group(5)}"
        
        # 格式2: MM-DD-HHMM.html (如 06-16-1530.html)
        match2 = re.match(r'(\d{2})-(\d{2})-(\d{2})(\d{2})\.html$', filename)
        if match2:
            year = datetime.now().year
            date_str = f"{year}-{match2.group(1)}-{match2.group(2)}"
            time_str = f"{match2.group(3)}:{match2.group(4)}"
        
        # 格式3: HH-MM.html (如 15-30.html，使用文件修改时间获取日期)
        match3 = re.match(r'(\d{2})-(\d{2})\.html$', filename)
        if match3:
            mtime = datetime.fromtimestamp(html_file.stat().st_mtime)
            date_str = mtime.strftime("%Y-%m-%d")
            # 使用文件修改时间作为日期，而不是当前时间
            time_str = f"{match3.group(1)}:{match3.group(2)}"
        
        if not date_str:
            continue
        
        # 读取文件内容提取元数据
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            metadata = extract_report_metadata(content)
            
            report_info = {
                "id": f"{date_str}-{time_str.replace(':', '-')}",
                "filename": filename,
                "date": date_str,
                "time": time_str,
                "title": metadata.get("title", f"{date_str} {time_str} 报告"),
                "keywords": metadata.get("keywords", ["热点", "趋势"]),
                "preview": metadata.get("preview", []),
                "size": len(content),
                "modified": datetime.fromtimestamp(html_file.stat().st_mtime).isoformat(),
            }
            
            reports.append(report_info)
            
        except Exception as e:
            print(f"[索引生成] 处理文件失败 {filename}: {e}")
            continue
    
    # 按日期时间排序（最新的在前）
    reports.sort(key=lambda x: f"{x['date']} {x['time']}", reverse=True)
    
    # 标记最新的报告
    if reports:
        reports[0]["isNewest"] = True
    
    # 写入索引文件
    try:
        index_data = {
            "generated_at": datetime.now().isoformat(),
            "total": len(reports),
            "reports": reports,
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)
        
        print(f"[索引生成] 成功生成索引: {output_file} (共 {len(reports)} 条报告)")
        return True
        
    except Exception as e:
        print(f"[索引生成] 写入索引失败: {e}")
        return False


def main():
    """主函数"""
    import sys
    
    # 默认路径
    reports_dir = "docs/reports"
    output_file = "docs/reports/index.json"
    
    # 支持命令行参数
    if len(sys.argv) > 1:
        reports_dir = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    
    success = generate_reports_index(reports_dir, output_file)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
