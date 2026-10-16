# 🔥 抖音自动续火花

[![GitHub stars](https://img.shields.io/github/stars/hxcong666/douyin-auto-fire_new?style=flat-square)](https://github.com/hxcong666/douyin-auto-fire_new/stargazers)
[![License](https://img.shields.io/badge/license-PolyForm%20Noncommercial-blue?style=flat-square)](LICENSE)

> 部署在云服务器上，每天定时自动向抖音好友发送消息，保持火花不断。服务器上通过虚拟桌面直接扫码登录，任务结果推送到飞书机器人。

## 项目介绍

`douyin-auto-fire_new` 是一个基于 Python + Playwright 的抖音私信自动发送工具，通过模拟真实浏览器操作，按配置自动向指定好友发送文字、图片或抖音原生表情。

本项目的核心特点：

- 🖥️ **服务器扫码登录**：服务器上用 Xvfb + x11vnc + noVNC 起虚拟桌面，通过浏览器远程打开服务器上的 Chromium 扫码登录，不需要在本地电脑导出 Cookie
- 🔏 **飞书机器人加签**：支持飞书机器人「签名校验」安全设置，任务结果安全推送到飞书群
- ⏰ **cron 每日定时**：每天 9:00 自动运行，日志按天归档，适合长期挂在云服务器上运行
- 🖱️ **网页管理后台**：在网页上增删好友、编辑消息、启用停用、查看执行结果和日志，详见 [管理后台](docs/admin.md)

> ⚠️ 项目使用 Storage State / Cookie 作为登录凭证。请只保存在服务器安全位置，不要提交到公开仓库，也不要分享给他人。

## ✨ 功能

- 🖥️ **服务器虚拟桌面扫码登录**：通过 SSH 隧道 + noVNC 远程操作服务器浏览器，登录状态保存为 `storage-state.json`
- 🔏 **飞书签名校验**：配置 `FEISHU_SECRET` 后自动为飞书 Webhook 请求加签
- ⏰ **定时自动发送**：支持 cron、systemd Timer、Docker、GitHub Actions 等方式定时运行
- 💬 **多种消息类型**：支持文字、图片（PNG/JPG/GIF/WebP）和抖音原生表情
- 🎲 **随机消息**：支持从多条候选消息中随机选择
- 👥 **多好友 / 多账号**：可以同时为多个好友、多个账号配置发送任务
- 🧪 **Dry Run 模式**：只验证登录状态和好友定位，不真实发送消息
- 🔒 **防重复发送**：记录发送历史，减少重复触发导致的重复发送
- 🔔 **多渠道通知**：飞书、钉钉、企业微信、Slack、Discord、Telegram 等任意 Webhook
- 🛡️ **失败诊断**：失败时保存日志、页面截图和 Playwright Trace
- ⏱️ **模拟真人操作**：随机发送间隔和输入节奏

## 🚀 服务器部署（推荐）

以下为本项目实际使用的部署方式：项目目录 `/opt/douyin-auto-sender`，运行用户 `douyin-sender`，Ubuntu 云服务器。

### 1. 安装项目

```bash
sudo useradd --system --home /opt/douyin-auto-sender --shell /usr/sbin/nologin douyin-sender
sudo git clone https://github.com/hxcong666/douyin-auto-fire_new.git /opt/douyin-auto-sender
sudo chown -R douyin-sender:douyin-sender /opt/douyin-auto-sender

cd /opt/douyin-auto-sender
sudo -u douyin-sender -H python3 -m venv .venv
sudo -u douyin-sender -H .venv/bin/pip install -r requirements.txt
sudo .venv/bin/playwright install-deps chromium
sudo -u douyin-sender -H .venv/bin/playwright install chromium
```

### 2. 启动虚拟桌面

```bash
sudo apt install -y xvfb x11vnc novnc websockify

Xvfb :99 -screen 0 1440x1000x24 &
x11vnc -storepasswd                      # 设置 VNC 密码，保存到 ~/.vnc/passwd
x11vnc -display :99 -rfbauth ~/.vnc/passwd -localhost -rfbport 5900 -forever -shared -bg
websockify --web /usr/share/novnc 127.0.0.1:6080 127.0.0.1:5900 &
```

VNC 和 noVNC 只监听 `127.0.0.1`，不对公网开放，通过 SSH 隧道访问。

### 3. 扫码登录

在本地电脑建立 SSH 隧道，然后用浏览器打开 noVNC：

```bash
ssh -L 6080:127.0.0.1:6080 ubuntu@你的服务器IP
# 浏览器访问 http://127.0.0.1:6080/vnc.html
```

在服务器上运行扫码登录脚本，浏览器会出现在 VNC 画面里，用抖音 App 扫码：

```bash
cd /opt/douyin-auto-sender
sudo -u douyin-sender -H env DISPLAY=:99 .venv/bin/python scripts/login.py
```

登录成功后回到终端按 Enter，登录状态保存到 `storage-state.json`，程序运行时会自动读取。

### 4. 配置任务和通知

```bash
sudo -u douyin-sender cp config.example.json config.json   # 好友和消息配置
sudo -u douyin-sender cp .env.example .env                 # 环境变量
sudo chmod 600 config.json .env
```

`.env` 关键配置：

```env
TASK_CONFIG=/opt/douyin-auto-sender/config.json
ARTIFACTS_DIR=/opt/douyin-auto-sender/artifacts
HEADLESS=true

# 飞书机器人通知
WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/你的机器人ID
FEISHU_SECRET=飞书机器人安全设置里的签名密钥
```

使用 Storage State 登录时，注释掉 `.env` 里的 `DOUYIN_COOKIE`。

先执行一次 Dry Run，确认登录和好友定位正常（不会真实发送消息）：

```bash
sudo -u douyin-sender -H .venv/bin/python run.py --dry-run
```

### 5. 配置每日定时

```bash
sudo install -m 755 deploy/cron/douyin-daily-run.sh /usr/local/bin/douyin-daily-run.sh
sudo crontab -e
# 添加一行：
0 9 * * * /usr/local/bin/douyin-daily-run.sh
```

每天的运行日志写入 `artifacts/daily_YYYYMMDD.log`，运行结果在 `artifacts/result.json`。

### 登录失效

`scripts/login.py` 只在扫码时导出一次登录状态，之后每次运行都使用这份快照，运行中刷新的 Cookie 不会写回文件。登录状态能保持多久取决于抖音，收到失败通知或日志提示未登录时，重新执行第 3 步扫码即可。

## 🖱️ 管理后台

在网页上管理续火花好友，不用再手动编辑 `config.json`：

- 添加、编辑、删除好友，为每个好友配置文字、表情、图片或随机消息
- 一键启用 / 停用某个好友，配置保留
- 保存后下次定时任务自动生效；任务运行中保存也不会冲突
- 查看最近执行时间、每个好友的发送结果和失败原因、每天的运行日志
- 账号密码登录，浏览器拿不到抖音 Cookie 等登录凭证

```bash
scripts/admin/build-web.sh                               # 构建前端
sudo -u douyin-sender -H scripts/admin/install.sh        # 安装依赖
sudo -u douyin-sender -H scripts/admin/set-password.sh   # 设置账号密码
sudo cp deploy/systemd/douyin-admin.service /etc/systemd/system/
sudo systemctl enable --now douyin-admin                 # 启动，默认端口 8090
```

部署、访问方式和安全说明见 [docs/admin.md](docs/admin.md)。

## 🔏 飞书机器人加签

飞书机器人开启「签名校验」后，不带签名的消息会被拒收。本项目在 `app/notifier.py` 中实现了飞书签名：

- 当 `WEBHOOK_URL` 指向 `open.feishu.cn` 且配置了 `FEISHU_SECRET` 时，自动在请求体中加入 `timestamp` 和 `sign`
- 签名算法与飞书官方一致：以 `timestamp + "\n" + secret` 为密钥做 HMAC-SHA256，再 base64 编码
- 未配置 `FEISHU_SECRET` 时不加签，不影响钉钉、企业微信等其他通知

飞书机器人设置：群设置 → 群机器人 → 添加自定义机器人 → 安全设置勾选「签名校验」，把 Webhook 地址填入 `WEBHOOK_URL`、签名密钥填入 `FEISHU_SECRET`。

## 📚 其他部署方式

- [云服务器 systemd 部署](docs/server.md)：使用 Cookie + systemd Timer
- [Docker 部署](docs/docker.md)：适合 NAS、1Panel、宝塔环境
- [GitHub Actions 部署](docs/github-actions.md)：无需服务器
- [Windows 电脑部署](docs/windows.md)：Windows 任务计划程序定时运行

> 第一次使用建议先配置 **1 个账号 + 1 个好友 + 1 条文字消息**，先执行 Dry Run，确认正常后再真实发送和增加其他配置。

## 🧰 技术栈

| 类别 | 内容 |
| --- | --- |
| 语言 | Python 3.11+ |
| 浏览器自动化 | [Playwright](https://playwright.dev/python/) + Chromium |
| 远程登录 | Xvfb + x11vnc + noVNC |
| 管理后台 | FastAPI + Next.js 15 + React 19 + Tailwind CSS 4 |
| 定时调度 | cron / systemd Timer / Docker Cron / GitHub Actions |
| 通知 | 飞书机器人（加签）/ 钉钉机器人 / 通用 Webhook |
| 运行环境 | Ubuntu 云服务器 |

主要依赖：

```text
playwright>=1.54,<2
python-dotenv>=1.1,<2
tzdata>=2025.2
```

## ⚠️ 注意事项

- `storage-state.json`、`config.json`、`.env` 不要提交到仓库，已在 `.gitignore` 中排除。
- 修改好友、消息或表情配置后，建议先运行一次 Dry Run。
- 同一个抖音账号不要同时运行多个自动发送任务，避免重复发送。
- 云服务器网络环境可能触发抖音安全验证，需要本人通过 VNC 重新完成验证。
- 抖音网页结构发生变化时，自动化功能可能需要同步适配。

## License

本项目采用 [PolyForm Noncommercial License 1.0.0](LICENSE)，仅限个人学习、研究和非商业用途使用。
