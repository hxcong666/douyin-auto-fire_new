# 管理后台

在网页上管理续火花好友和消息，查看每天的执行结果和日志。后台只读写 `config.json`，原有的定时任务、发送逻辑、登录方式都不变：每天 9:00 照常运行，读取最新保存的配置。

## 功能

| 功能 | 说明 |
| --- | --- |
| 好友管理 | 添加、编辑、删除续火花好友 |
| 消息管理 | 为每个好友配置文字、抖音表情、图片、随机一条（从候选中随机选） |
| 启用 / 停用 | 关闭开关即暂停续火花，配置保留，随时可以重新打开 |
| 表情库 | 维护可用的抖音表情名称 |
| 自动生效 | 保存到服务器的 `config.json`，下次定时任务自动读取 |
| 状态与日志 | 最近执行时间、每个好友的发送结果和失败原因、每天的运行日志 |
| 登录保护 | 账号密码登录，失败 5 次锁定 15 分钟 |

## 架构

```text
浏览器 ──HTTP──▶ 管理后台（admin/，FastAPI + Next.js 静态页面，端口 8090）
                    │  读写（原子替换 + 校验）        │ 只读
                    ▼                                  ▼
               config.json                 artifacts/（result.json、日志）
                    ▲                                  │ 写入
                    │ 启动时读取一次                   │
               续火花程序（run.py，root crontab 每天 9:00）
```

- 后台是独立的 uv 项目，依赖装在 `admin/.venv`，不改动续火花程序的 `.venv`。
- 续火花程序只增加了一处改动：好友支持 `"enabled": false`，停用的好友会被跳过；没有这个字段时默认启用，旧配置无需修改。

## 并发与数据安全

| 场景 | 处理方式 |
| --- | --- |
| 定时任务运行中保存配置 | 续火花程序只在启动时读一次配置，运行中改动不影响本次执行。后台检测到 `artifacts/run.lock` 时照常保存，并提示「下次执行生效」 |
| 写到一半被读取 | 先写临时文件并 fsync，再用 `os.replace` 原子替换，任何时刻读到的都是完整文件 |
| 保存了错误配置 | 替换前用续火花程序自己的解析逻辑校验临时文件（表情是否存在、至少一个启用好友等），不通过则原文件不动 |
| 两个窗口同时编辑 | 读取时返回文件指纹 `version`，保存时比对，不一致返回 409，提示刷新 |
| 其他字段 | `task_id`、发送间隔、重试次数等后台不编辑的字段原样保留 |
| 文件权限 | 保存后保持原文件权限（服务器上为 600） |

## 安全设计

- 浏览器拿不到任何登录凭证：后台只读写 `config.json` 和 `artifacts/` 下已脱敏的结果文件，不读取 `.env`、`storage-state.json`、`login_state.json`、Cookie 文件。
- 日志接口只允许 `YYYYMMDD` 格式的日期，不能读取其他文件；返回前再兜底打码一次链接和 `token=`、`secret=` 一类内容。
- 会话令牌放在 `HttpOnly` + `SameSite=Strict` 的 Cookie 中，前端 JS 读不到；修改配置还需要 CSRF 令牌。
- 密码只保存 scrypt 哈希（`.env.admin`，权限 600），不保存明文。
- 关闭接口文档页面，设置 CSP、`X-Frame-Options` 等安全响应头。
- systemd 以 `douyin-sender` 用户运行，开启 `ProtectSystem=strict`、`ProtectHome` 等加固选项。
- 后台日志（`logs/admin.log`）记录登录和保存操作，只记录数量，不记录好友昵称和消息内容。

> ⚠️ 通过公网 IP + HTTP 访问时，登录密码和会话 Cookie 是明文传输的，同一网络中的人有可能截获。正式使用建议改为下面「访问方式」中的 SSH 隧道或 HTTPS。

## 部署

以下命令在服务器 `/opt/douyin-auto-sender` 下执行。

### 1. 构建前端

前端构建需要 Node.js，可以在本地电脑构建后上传 `admin/web/out/`，也可以在服务器上构建：

```bash
scripts/admin/build-web.sh
```

### 2. 安装后台依赖

```bash
sudo -u douyin-sender -H scripts/admin/install.sh
```

### 3. 设置后台账号密码

```bash
sudo -u douyin-sender -H scripts/admin/set-password.sh
```

按提示输入用户名和密码（至少 10 位），会写入项目根目录的 `.env.admin`。忘记密码时重新执行即可。

### 4. 配置监听地址

编辑 `.env.admin`：

```env
ADMIN_HOST=0.0.0.0   # 公网访问；只用 SSH 隧道时保持 127.0.0.1
ADMIN_PORT=8090
```

公网访问还需要在腾讯云控制台的安全组中放行 TCP 8090，建议只放行自己的 IP。

### 5. 用 systemd 常驻运行

```bash
sudo cp deploy/systemd/douyin-admin.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now douyin-admin
sudo systemctl status douyin-admin
```

浏览器打开 `http://服务器IP:8090`。

## 访问方式

| 方式 | 配置 | 安全性 |
| --- | --- | --- |
| 公网 IP + HTTP | `ADMIN_HOST=0.0.0.0`，安全组放行 8090 | 密码明文传输，仅建议临时使用并限制来源 IP |
| SSH 隧道 | `ADMIN_HOST=127.0.0.1`，本地执行 `ssh -L 8090:127.0.0.1:8090 ubuntu@服务器IP` 后打开 `http://127.0.0.1:8090` | 不暴露端口，推荐 |
| 域名 + HTTPS | 用 Caddy / Nginx 反向代理到 `127.0.0.1:8090`，`.env.admin` 中设置 `ADMIN_COOKIE_SECURE=true` | 加密传输，推荐长期使用 |

## 日常维护

| 操作 | 命令 |
| --- | --- |
| 查看后台状态 | `sudo systemctl status douyin-admin` |
| 重启后台 | `sudo systemctl restart douyin-admin` |
| 查看后台日志 | `tail -f logs/admin.log` |
| 本机调试运行 | `scripts/admin/serve.sh`（前台）或 `scripts/admin/start.sh` / `stop.sh`（后台） |
| 运行后台测试 | `scripts/admin/test.sh` |
| 运行续火花程序测试 | `scripts/test-runner.sh` |

## 日志中的好友编号

续火花程序的日志和结果不显示真实昵称，而是按**启用好友的顺序**编号为「好友01、好友02…」。管理后台的每张好友卡片上会显示对应的日志编号；停用、调整顺序后编号会变化。
