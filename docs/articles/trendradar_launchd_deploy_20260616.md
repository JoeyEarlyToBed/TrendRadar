# TrendRadar launchd 部署完成

## 19:39 → 19:57 部署验证

### 部署架构
- **方案**: launchd（macOS 原生定时任务）
- **Plists**: `com.trendradar.crawler.plist`（已推 GitHub）
  - 位置: `~/Library/LaunchAgents/com.trendradar.crawler.plist`
- **调度**: 每 30 分钟（StartInterval=1800），7:00-22:00 运行
- **加载/卸载命令**:
  ```bash
  # 加载
  launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.trendradar.crawler.plist
  # 手动触发
  launchctl kickstart gui/$(id -u)/com.trendradar.crawler
  # 卸载
  launchctl bootout gui/$(id -u)/com.trendradar.crawler
  ```

### 首次运行
- 热榜 21/23 成功，522 条当前
- RSS 5/9 成功
- AI 分析完成 → 企业微信 2 批次推送成功
- HTML 报告生成

### 关键修复
- `output/cron.log` 是目录 → 清除了，改用 `daemon.log`
- plist 加 `PYTHONUNBUFFERED=1` 确保日志实时
