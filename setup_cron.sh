#!/bin/bash
# TrendRadar 定时执行设置脚本
# 博客推荐每 30 分钟运行一次（07:00-22:00），配合 morning_evening 调度预设
# 运行方式: bash setup_cron.sh

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
CRON_LINE="*/30 7-22 * * * cd ${PROJECT_DIR} && .venv/bin/python -m trendradar >> output/cron.log 2>&1"

# 检查是否已在 crontab 中
if crontab -l 2>/dev/null | grep -Fq "$PROJECT_DIR"; then
    echo "✅ TrendRadar 已在 crontab 中，如需更新请手动编辑 'crontab -e'"
    echo "当前:"
    crontab -l | grep "$PROJECT_DIR"
else
    (crontab -l 2>/dev/null; echo "$CRON_LINE") | crontab -
    echo "✅ 已添加 cron 任务: ${CRON_LINE}"
fi
