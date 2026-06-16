#!/bin/bash
# TrendRadar 本地运行脚本
# 用法: ./run.sh [once|server|test]

set -e

cd "$(dirname "$0")"
source .venv/bin/activate

# 加载环境变量
export AI_API_KEY="${AI_API_KEY:-sk-d733112384e7491983c4f3f2d3b7d19d}"
export AI_MODEL="${AI_MODEL:-deepseek/deepseek-chat}"
export WEWORK_WEBHOOK_URL="${WEWORK_WEBHOOK_URL:-https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=309f1285-a644-47e0-a9ea-820c6c85c02f}"
export WEWORK_MSG_TYPE="${WEWORK_MSG_TYPE:-markdown}"

case "${1:-server}" in
  once|run)
    echo "▶️ 单次执行爬虫..."
    python -m trendradar
    ;;
  server)
    echo "🌐 启动 Web 服务器 (端口 8080)..."
    python -m uvicorn trendradar.web:app --host 127.0.0.1 --port 8080 &
    echo "⏰ 启动定时执行 (每30分钟)..."
    echo "▶️ 立即执行一次..."
    python -m trendradar
    # 使用 macOS launchd 实现定时
    echo "设置 crontab 中..."
    (
      crontab -l 2>/dev/null | grep -v trendradar
      echo "*/30 * * * * cd $(pwd) && .venv/bin/python -m trendradar >> output/cron.log 2>&1"
    ) | crontab -
    echo "✅ TrendRadar 已启动！"
    echo "   Web 界面: http://127.0.0.1:8080"
    echo "   推送测试: ./run.sh test"
    echo "   单次运行: ./run.sh once"
    echo "   日志: tail -f output/cron.log"
    ;;
  test)
    echo "📨 发送测试通知..."
    python -m trendradar --test-notification
    ;;
  doctor)
    python -m trendradar --doctor
    ;;
  *)
    echo "用法: ./run.sh [once|server|test|doctor]"
    exit 1
    ;;
esac
