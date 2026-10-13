#!/bin/bash
# 每天早上9点定时运行的抖音私信发送脚本
# 由 root crontab 调用，切到 douyin-sender 执行
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
cd /opt/douyin-auto-sender
# 日志追加到当天文件
LOGFILE=/opt/douyin-auto-sender/artifacts/daily_$(date +\%Y\%m\%d).log
echo "===== $(date '+%Y-%m-%d %H:%M:%S') 定时任务启动 =====" >> "$LOGFILE"
sudo -u douyin-sender -H .venv/bin/python run.py >> "$LOGFILE" 2>&1
echo "===== $(date '+%Y-%m-%d %H:%M:%S') 定时任务结束 =====" >> "$LOGFILE"
