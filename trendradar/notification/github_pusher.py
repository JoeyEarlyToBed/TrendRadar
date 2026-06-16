# coding=utf-8
"""
GitHub 推送模块

将生成的 HTML 报告自动推送到 GitHub 仓库，用于 GitHub Pages 展示
支持配置自动推送开关、仓库地址、分支、目标目录等
"""

import os
import re
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional


class GitHubPusher:
    """
    GitHub 推送器
    
    功能：
    - 将 HTML 报告复制到 GitHub 仓库指定目录
    - 自动提交并推送
    - 支持配置化开关
    """
    
    def __init__(
        self,
        repo_path: str,
        target_dir: str = "docs/reports",
        branch: str = "main",
        enabled: bool = True,
        commit_message_template: str = "auto: update report {timestamp}",
        pat: Optional[str] = None,
    ):
        """
        初始化 GitHub 推送器
        
        Args:
            repo_path: 本地 GitHub 仓库路径
            target_dir: 报告存放的目标目录（相对于仓库根目录）
            branch: 目标分支
            enabled: 是否启用推送
            commit_message_template: 提交消息模板，可用变量 {timestamp}, {date}, {time}
            pat: GitHub Personal Access Token（可选，用于 HTTPS 推送）
        """
        self.repo_path = Path(repo_path).expanduser().resolve()
        self.target_dir = target_dir
        self.branch = branch
        self.enabled = enabled
        self.commit_message_template = commit_message_template
        self.pat = pat
        
        # 验证仓库路径
        if not self.repo_path.exists():
            raise ValueError(f"仓库路径不存在: {repo_path}")
        
        git_dir = self.repo_path / ".git"
        if not git_dir.exists():
            raise ValueError(f"路径不是 Git 仓库: {repo_path}")
    
    def push_report(self, html_content: str, filename: str) -> Dict:
        """
        推送 HTML 报告到 GitHub
        
        Args:
            html_content: HTML 报告内容
            filename: 文件名（如 "2025-12-28-15-30.html"）
        
        Returns:
            推送结果字典 {success: bool, message: str, commit_hash: str}
        """
        if not self.enabled:
            return {"success": False, "message": "GitHub 推送已禁用"}
        
        try:
            # 1. 确保目标目录存在
            target_path = self.repo_path / self.target_dir
            target_path.mkdir(parents=True, exist_ok=True)
            
            # 2. 写入 HTML 文件
            file_path = target_path / filename
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            
            # 3. 检查是否有变更
            status_result = self._run_git_command(["status", "--short", str(file_path)])
            if not status_result["stdout"].strip():
                return {
                    "success": True, 
                    "message": f"文件无变更，跳过推送: {filename}",
                    "commit_hash": ""
                }
            
            # 4. git add
            add_result = self._run_git_command(["add", str(file_path)])
            if add_result["returncode"] != 0:
                return {
                    "success": False, 
                    "message": f"git add 失败: {add_result['stderr']}"
                }
            
            # 5. git commit
            now = datetime.now()
            commit_message = self.commit_message_template.format(
                timestamp=now.strftime("%Y-%m-%d %H:%M:%S"),
                date=now.strftime("%Y-%m-%d"),
                time=now.strftime("%H:%M:%S"),
                filename=filename
            )
            
            commit_result = self._run_git_command([
                "commit", "-m", commit_message
            ])
            if commit_result["returncode"] != 0:
                # 可能是没有变更，检查 stderr
                if "nothing to commit" in commit_result["stderr"]:
                    return {
                        "success": True,
                        "message": "没有需要提交的变更",
                        "commit_hash": ""
                    }
                return {
                    "success": False,
                    "message": f"git commit 失败: {commit_result['stderr']}"
                }
            
            # 6. 获取 commit hash
            log_result = self._run_git_command(["log", "-1", "--format=%H"])
            commit_hash = log_result["stdout"].strip() if log_result["returncode"] == 0 else ""
            
            # 7. git push
            push_result = self._run_git_command([
                "push", "origin", self.branch
            ])
            if push_result["returncode"] != 0:
                # 检查是否是 Push Protection 或其他错误
                stderr = push_result["stderr"]
                if "Push Protection" in stderr or "secret" in stderr.lower():
                    return {
                        "success": False,
                        "message": f"GitHub Push Protection 阻止推送，请检查仓库设置或移除敏感信息: {stderr[:200]}"
                    }
                return {
                    "success": False,
                    "message": f"git push 失败: {stderr[:200]}"
                }
            
            return {
                "success": True,
                "message": f"成功推送报告: {filename}",
                "commit_hash": commit_hash,
                "file_path": str(file_path.relative_to(self.repo_path))
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"推送异常: {str(e)}"
            }
    
    def _run_git_command(self, args: list) -> Dict:
        """
        在仓库目录下运行 Git 命令
        
        Args:
            args: Git 命令参数列表
        
        Returns:
            {returncode: int, stdout: str, stderr: str}
        """
        cmd = ["git", "-C", str(self.repo_path)] + args
        
        # 设置环境变量，避免 locale 问题
        env = os.environ.copy()
        env["LC_ALL"] = "C.UTF-8"
        env["LANG"] = "C.UTF-8"
        
        # 如果有 PAT，设置到 remote URL
        if self.pat and "push" in args:
            # 临时修改 remote URL 包含 PAT
            self._setup_pat_remote()
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env,
            cwd=str(self.repo_path)
        )
        
        return {
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    
    def _setup_pat_remote(self):
        """配置 PAT 用于推送（临时修改 remote URL）"""
        if not self.pat:
            return
        
        # 获取当前 remote URL
        result = self._run_git_command(["remote", "get-url", "origin"])
        if result["returncode"] != 0:
            return
        
        current_url = result["stdout"].strip()
        
        # 如果已经是 HTTPS 格式，插入 PAT
        if current_url.startswith("https://"):
            # 解析 URL
            parsed = re.match(r"https://([^/]+)/(.+)", current_url)
            if parsed:
                domain = parsed.group(1)
                path = parsed.group(2)
                new_url = f"https://{self.pat}@{domain}/{path}"
                
                # 临时设置新 URL
                self._run_git_command(["remote", "set-url", "origin", new_url])
                
                # 记录原始 URL，稍后恢复
                self._original_remote_url = current_url
    
    def _restore_remote_url(self):
        """恢复原始 remote URL"""
        if hasattr(self, "_original_remote_url"):
            self._run_git_command([
                "remote", "set-url", "origin", 
                self._original_remote_url
            ])
            delattr(self, "_original_remote_url")
    
    def get_report_url(self, filename: str) -> str:
        """
        获取报告在 GitHub Pages 上的 URL
        
        Args:
            filename: 报告文件名
        
        Returns:
            GitHub Pages URL
        """
        # 获取仓库信息
        remote_result = self._run_git_command(["remote", "get-url", "origin"])
        if remote_result["returncode"] != 0:
            return ""
        
        remote_url = remote_result["stdout"].strip()
        
        # 解析 GitHub 用户名和仓库名
        # 支持 HTTPS: https://github.com/username/repo.git
        # 支持 SSH: git@github.com:username/repo.git
        https_match = re.match(r"https://github\.com/([^/]+)/(.+?)(?:\.git)?$", remote_url)
        ssh_match = re.match(r"git@github\.com:([^/]+)/(.+?)(?:\.git)?$", remote_url)
        
        if https_match:
            username = https_match.group(1)
            repo = https_match.group(2)
        elif ssh_match:
            username = ssh_match.group(1)
            repo = ssh_match.group(2)
        else:
            return ""
        
        # 构建 GitHub Pages URL
        # 用户页面: https://username.github.io/repo/path
        # 组织页面: https://org.github.io/repo/path
        pages_url = f"https://{username}.github.io/{repo}/{self.target_dir}/{filename}"
        
        return pages_url


def create_github_pusher_from_config(config: Dict) -> Optional[GitHubPusher]:
    """
    从配置字典创建 GitHub 推送器
    
    Args:
        config: 配置字典，包含 github 推送配置
    
    Returns:
        GitHubPusher 实例，如果未启用则返回 None
    """
    github_config = config.get("github", {})
    
    if not github_config.get("enabled", False):
        return None
    
    repo_path = github_config.get("repo_path", "")
    if not repo_path:
        print("[GitHub 推送] 未配置 repo_path，跳过")
        return None
    
    # 展开 ~ 为 home 目录
    repo_path = os.path.expanduser(repo_path)
    
    return GitHubPusher(
        repo_path=repo_path,
        target_dir=github_config.get("target_dir", "docs/reports"),
        branch=github_config.get("branch", "main"),
        enabled=True,
        commit_message_template=github_config.get(
            "commit_message", 
            "auto: update report {timestamp}"
        ),
        pat=github_config.get("pat") or os.environ.get("GITHUB_PAT"),
    )
