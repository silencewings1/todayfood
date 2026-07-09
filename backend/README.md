# 今日宜吃 · 后端

基于 FastAPI 实现的「今日宜吃」小程序后端，提供每日食历、抽签推荐、AI 自由文本解析等接口。零配置即可启动（走本地兜底数据池），配置 `OPENAI_API_KEY` 后自动启用 AI 增强。

## 工程结构

```
backend/
├── app/
│   ├── __init__.py              # 版本号
│   ├── config.py                # 配置加载（app.toml + ai.toml + .env + 环境变量）
│   ├── main.py                  # FastAPI 入口，中间件 + 路由注册 + 生命周期
│   ├── api/                     # HTTP 路由层
│   │   ├── meta.py              #   GET /meta  GET /health
│   │   └── fortune.py           #   GET /api/fortune/today  POST /api/fortune/draw
│   ├── schemas/fortune.py       # Pydantic 请求/响应模型（字段与前端对齐）
│   ├── services/                # 业务编排层
│   │   ├── fortune_service.py   #   今日食历构造 + 抽签流程（含 AI 接入点）
│   │   ├── cache.py             #   按日期的内存缓存
│   │   └── scheduler.py         #   后台线程：每日凌晨刷新缓存
│   ├── core/                    # 纯算法（无 IO）
│   │   ├── seed.py              #   日期种子 + 今日信息
│   │   └── picker.py            #   菜品/签文/宜忌选择算法
│   ├── data/                    # 静态数据池（兜底用）
│   │   ├── foods.py  signs.py  almanac.py  suitable.py  avoids.py
│   └── ai/                      # AI Provider
│       ├── base.py              #   AIProvider 抽象 + NoteParseResult
│       ├── dummy.py             #   占位实现（零配置可用）
│       ├── factory.py           #   根据 settings.ai 决定实例化哪个 Provider
│       └── openai_agents_provider.py  # 基于 openai-agents SDK 的实现
├── config/
│   ├── app.toml                 # 系统/服务/调度/admin 配置（可提交）
│   └── ai.toml                  # AI 协议/模型/超时/各 agent 开关（可提交）
├── tests/                       # pytest 测试
│   ├── conftest.py
│   ├── test_api.py
│   └── test_seed_and_picker.py
├── data/                        # 运行时生成（已 gitignore）：admin 日志 SQLite
├── requirements.txt
├── .env.example                 # 环境变量模板（复制为 .env）
└── TASKS.md                     # 开发任务清单
```

## 配置体系

配置分三层，优先级 **高 → 低**：

| 层级 | 文件 | 用途 | 是否入 git |
|------|------|------|------------|
| 环境变量 | shell / systemd `Environment=` | 敏感信息、运维期覆盖 | — |
| .env | `backend/.env` | 本地开发常用覆盖项 | 否（gitignore） |
| TOML | `config/app.toml` `config/ai.toml` | 结构化非敏感默认值 | 是 |
| 代码默认值 | `app/config.py` | 兜底，保证零配置可用 | 是 |

- `config/app.toml`：服务端口、CORS 白名单、时区、缓存、调度间隔、admin 后台参数
- `config/ai.toml`：AI 协议（`chat_completions` / `responses`）、模型、超时、三个 agent 独立开关
- `.env`：仅放敏感信息（`OPENAI_API_KEY`、`ADMIN_PASSWORD`）和需要快速覆盖的项；模板见 `.env.example`

修改 toml / .env 后，`--reload` 模式会自动重启生效。

## 本地测试

### 1. 环境准备

```bash
# 进入 backend 目录
cd backend

# 激活 Python 虚拟环境（按你本机实际路径）
source ~/.py_food/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置 .env

```bash
cp .env.example .env
# 按需填写 OPENAI_API_KEY / OPENAI_BASE_URL / OPENAI_MODEL
# 不填也能跑，AI 会自动回退 DummyProvider
```

### 3. 启动服务

```bash
# 方式一：uvicorn 热重载（开发推荐）
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# 方式二：python 模块入口（读 config 中的 host/port）
python -m app.main
```

启动后：

- 接口文档：<http://localhost:8000/docs>
- 健康检查：<http://localhost:8000/health>（含 AI 配置摘要）
- 后台管理：<http://localhost:8000/admin>（账号密码通过 `ADMIN_USERNAME`/`ADMIN_PASSWORD` 环境变量配置）

### 4. 验证接口

```bash
# 今日食历 + 今日菜品
curl http://localhost:8000/api/fortune/today | jq

# 抽一道新菜
curl -X POST http://localhost:8000/api/fortune/draw \
  -H 'Content-Type: application/json' \
  -d '{"excludeId":null,"preferences":{"mood":"tired","flavor":"spicy"}}' | jq
```

### 5. 运行测试

```bash
cd backend
source ~/.py_food/bin/activate
pytest -v
```

### 6. 查看后端日志

- 前台启动：日志直接输出到终端，可实时观察请求方法/路径/IP/状态码/耗时，POST 还会打印请求体
- 写文件：`uvicorn app.main:app >> logs/uvicorn.log 2>&1`
- admin 后台：访问 `/admin` → 「API 日志」/「AI 调用」分页查看，数据持久化在 `backend/data/log.db`

## 远程部署

### 1. 同步代码到服务器

```bash
# 服务器上
cd ~/project
git clone <repo-url> todayfood
cd todayfood
```

### 2. 配置 .env

```bash
cd backend
cp .env.example .env
vim .env
# 必改项：
#   OPENAI_API_KEY=sk-xxx
#   ADMIN_PASSWORD=<强密码>
# 按需改：
#   OPENAI_BASE_URL / OPENAI_MODEL / FRONTEND_ORIGIN
```

如需覆盖 `config/app.toml` 的默认端口/时区等，可在 `.env` 或 systemd `Environment=` 中设置对应环境变量（优先级更高）。

### 3. 安装依赖

```bash
cd backend
python -m venv ~/./.py_food       # 或用现有虚拟环境
source ~/./.py_food/bin/activate
pip install -r requirements.txt
```

### 4. systemd 常驻

仓库 `deploy/todayfood.service` 已提供模板，按服务器路径调整后软链到 `~/.config/systemd/user/`：

```ini
[Service]
WorkingDirectory=/home/<user>/project/todayfood/backend
Environment=USE_AI=1
Environment=HOST=0.0.0.0
Environment=PORT=9081
ExecStart=/home/<user>/.py_food/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 9081
Restart=always
StandardOutput=append:/home/<user>/project/todayfood/logs/uvicorn.log
```

```bash
mkdir -p ~/.config/systemd/user logs
cp deploy/todayfood.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now todayfood
systemctl --user status todayfood
journalctl --user -u todayfood -f   # 查看日志
```

### 5. 反向代理（推荐）

生产环境建议用 nginx 反代前端 + 后端，示例：

```nginx
server {
    listen 80;
    server_name todayfood.example.com;

    # 前端静态资源（vite build 产物）
    root /home/<user>/project/todayfood/frontend/dist;
    index index.html;
    location / { try_files $uri $uri/ /index.html; }

    # 后端 API
    location /api/ {
        proxy_pass http://127.0.0.1:9081;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # 后台管理（内嵌在主后端）
    location /admin/ {
        proxy_pass http://127.0.0.1:9081;
        proxy_set_header Host $host;
    }
}
```

后端也可直接托管前端构建产物：`frontend/dist` 存在时，`/{full_path}` 会回退到 `index.html`，单端口即可上线。

### 6. 升级流程

```bash
cd ~/project/todayfood
git pull
cd backend && pip install -r requirements.txt   # 依赖有变化时
systemctl --user restart todayfood
```

## API 一览

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查 + AI 配置摘要 |
| GET | `/meta` | 服务元信息 |
| GET | `/api/fortune/today` | 今日食历 + 今日菜品（每日固定，按 date 缓存） |
| POST | `/api/fortune/draw` | 抽一道新菜（支持偏好，note 走 AI 解析） |
| GET | `/admin` | 后台管理界面（需登录） |
| * | `/admin/api/*` | 后台管理 API |

请求/响应字段详见 `app/schemas/fortune.py` 或 <http://localhost:8000/docs>。

## 关键设计

- **每日食历固定**：「今日食历」卡内容（黄历宜忌 + 干饭宜忌 + 幸运三件套 + 签文）仅依赖当日种子 `YYYYMMDD`，对所有用户一致，凌晨 0 点按 `app.timezone` 切换
- **AI 兜底**：所有 AI 调用用 `asyncio.wait_for(timeout=ai_timeout)` 包装，超时/异常自动回退本地数据池，不影响主流程
- **双协议支持**：`api_protocol = chat_completions | responses`，兼容 OpenAI 官方与第三方兼容服务（DeepSeek / Moonshot / 通义千问 / 智谱等）
- **零配置可用**：未配置 `OPENAI_API_KEY` 时自动回退 `DummyProvider`，服务可正常启动
