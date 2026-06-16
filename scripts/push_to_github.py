#!/usr/bin/env python3
# coding=utf-8
"""
GitHub 推送集成脚本

将 TrendRadar 生成的报告自动推送到 GitHub 仓库
支持：
1. 推送 HTML 报告到 docs/reports/
2. 生成并推送索引文件
3. 提交并推送

使用方法:
    python scripts/push_to_github.py [report_file] [repo_path]

环境变量:
    GITHUB_PAT: GitHub Personal Access Token（可选）
"""

import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path


def run_git_command(repo_path, args):
    """在仓库目录下运行 git 命令"""
    cmd = ["git", "-C", str(repo_path)] + args
    env = os.environ.copy()
    env["LC_ALL"] = "C.UTF-8"
    env["LANG"] = "C.UTF-8"
    
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    return result.returncode == 0, result.stdout, result.stderr


def push_report_to_github(
    report_file: str,
    repo_path: str = "~/workspace/TrendRadar/TrendRadar-v6.9.1",
    target_dir: str = "docs/reports",
    branch: str = "main",
    generate_index: bool = True,
) -> bool:
    """
    推送报告到 GitHub
    
    Args:
        report_file: HTML 报告文件路径
        repo_path: 本地仓库路径
        target_dir: 报告存放目录
        branch: 目标分支
        generate_index: 是否生成索引文件
    
    Returns:
        是否成功
    """
    # 展开路径
    repo_path = Path(repo_path).expanduser().resolve()
    report_path = Path(report_file).expanduser().resolve()
    
    if not repo_path.exists():
        print(f"[GitHub 推送] 错误: 仓库路径不存在: {repo_path}")
        return False
    
    if not report_path.exists():
        print(f"[GitHub 推送] 错误: 报告文件不存在: {report_path}")
        return False
    
    # 检查是否是 git 仓库
    git_dir = repo_path / ".git"
    if not git_dir.exists():
        print(f"[GitHub 推送] 错误: 路径不是 Git 仓库: {repo_path}")
        return False
    
    print(f"[GitHub 推送] 开始推送报告: {report_path.name}")
    print(f"[GitHub 推送] 目标仓库: {repo_path}")
    
    # 1. 复制报告到目标目录
    target_path = repo_path / target_dir
    target_path.mkdir(parents=True, exist_ok=True)
    
    dest_file = target_path / report_path.name
    
    # 读取并写入内容（确保编码正确）
    try:
        with open(report_path, 'r', encoding='utf-8') as f:
            content = f.read()
        with open(dest_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"[GitHub 推送] 已复制报告到: {dest_file}")
    except Exception as e:
        print(f"[GitHub 推送] 复制文件失败: {e}")
        return False
    
    # 2. 生成索引文件（如果需要）
    if generate_index:
        index_script = repo_path / "scripts" / "generate_report_index.py"
        if index_script.exists():
            print(f"[GitHub 推送] 生成报告索引...")
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location("index_gen", index_script)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                index_file = repo_path / target_dir / "index.json"
                module.generate_reports_index(str(target_path), str(index_file))
                print(f"[GitHub 推送] 索引已生成: {index_file}")
            except Exception as e:
                print(f"[GitHub 推送] 生成索引失败: {e}")
        else:
            print(f"[GitHub 推送] 索引生成脚本不存在，跳过")
    
    # 3. Git 操作
    # git add
    success, stdout, stderr = run_git_command(repo_path, ["add", str(target_dir)])
    if not success:
        print(f"[GitHub 推送] git add 失败: {stderr}")
        return False
    
    # 检查是否有变更
    success, stdout, stderr = run_git_command(repo_path, ["status", "--short"])
    if not stdout.strip():
        print(f"[GitHub 推送] 没有需要提交的变更")
        return True
    
    # git commit
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    commit_msg = f"auto: update report {now} - {report_path.name}"
    
    success, stdout, stderr = run_git_command(repo_path, ["commit", "-m", commit_msg])
    if not success:
        if "nothing to commit" in stderr:
            print(f"[GitHub 推送] 没有需要提交的变更")
            return True
        print(f"[GitHub 推送] git commit 失败: {stderr}")
        return False
    
    print(f"[GitHub 推送] 已提交: {commit_msg}")
    
    # 4. git push
    # 检查是否有 PAT
    pat = os.environ.get("GITHUB_PAT", "")
    if pat:
        # 获取当前 remote URL
        success, remote_url, stderr = run_git_command(repo_path, ["remote", "get-url", "origin"])
        if success and remote_url.strip():
            original_url = remote_url.strip()
            # 插入 PAT
            if original_url.startswith("https://"):
                new_url = original_url.replace("https://", f"https://{pat}@")
                run_git_command(repo_path, ["remote", "set-url", "origin", new_url])
                print(f"[GitHub 推送] 已配置 PAT 推送")
    
    success, stdout, stderr = run_git_command(repo_path, ["push", "origin", branch])
    
    # 恢复原始 URL
    if pat and 'original_url' in locals():
        run_git_command(repo_path, ["remote", "set-url", "origin", original_url])
    
    if not success:
        if "Push Protection" in stderr or "secret" in stderr.lower():
            print(f"[GitHub 推送] 失败: GitHub Push Protection 阻止推送")
            print(f"[GitHub 推送] 请检查仓库设置或移除敏感信息")
        else:
            print(f"[GitHub 推送] git push 失败: {stderr}")
        return False
    
    print(f"[GitHub 推送] 成功推送报告到 GitHub!")
    
    # 构建 GitHub Pages URL
    success, remote_url, _ = run_git_command(repo_path, ["remote", "get-url", "origin"])
    if success:
        remote_url = remote_url.strip()
        # 解析 URL 获取用户名和仓库名
        import re
        match = re.match(r"https://github\.com/([^/]+)/(.+?)\.git$", remote_url)
        if match:
            username = match.group(1)
            repo = match.group(2)
            pages_url = f"https://{username}.github.io/{repo}/{target_dir}/{report_path.name}"
            print(f"[GitHub 推送] 报告访问地址: {pages_url}")
    
    return True


def main():
    """主函数"""
    # 默认参数
    report_file = None
    repo_path = os.environ.get("TRENDRADAR_REPO", "~/workspace/TrendRadar/TrendRadar-v6.9.1")
    
    # 解析命令行参数
    if len(sys.argv) > 1:
        report_file = sys.argv[1]
    if len(sys.argv) > 2:
        repo_path = sys.argv[2]
    
    if not report_file:
        print("用法: python push_to_github.py <report_file> [repo_path]")
        print("环境变量: GITHUB_PAT (可选)")
        sys.exit(1)
    
    success = push_report_to_github(report_file, repo_path)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
