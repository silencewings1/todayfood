# 今日宜吃

> 基于黄历的 AI 开运菜单生成器 —— 每日食历 + 抽签推荐 + 自由文本解析

每天给你一签、一菜、一份干饭宜忌，搭配幸运三件套（口味 / 颜色 / 方位）。小程序竖屏布局，所有内容当日固定，凌晨 0 点按北京时间切换。

## 项目组成

本仓库是 monorepo，包含三个工程：

| 目录 | 技术栈 | 说明 | 详细文档 |
|------|--------|------|----------|
| `frontend/` | Vue 3 + Vite | 用户侧 H5 应用（食历 / 择食 / 关于） | [frontend/README.md](frontend/README.md) |
| `backend/` | FastAPI + openai-agents | 业务 API + AI 接入 + 后台管理（内嵌） | [backend/README.md](backend/README.md) |
| `admin/` | FastAPI + 单文件 HTML | 后台管理界面（可独立部署） | 见下文 |
| `deploy/` | systemd + shell | 部署模板与日志备份脚本 | 见下文 |

## 整体架构

```
┌─────────────┐   /api/*   ┌─────────────┐
│  frontend   │ ─────────▶ │  backend    │
│  (Vite SSR) │            │  (FastAPI)  │
└─────────────┘            └──────┬──────┘
       │                          │ 内嵌
       │                          ▼
       │                  ┌─────────────┐
       │                  │ admin 模块  │
       │                  │ (router/db) │
       │                  └──────┬──────┘
       │                         │ 写入
       │                         ▼
       │                  ┌─────────────┐
       │                  │ SQLite 日志  │
       │                  │ backend/data│
       │                  └─────────────┘
       │                         
       │   /admin    ┌─────────────┐
       └───────────▶ │ admin/main  │ (可选独立进程)
                    │ (FastAPI)   │
                    └─────────────┘
```

- 开发期：前端 5173 + 后端 8000，vite 代理 `/api`
- 生产期：可单端口（后端托管前端 dist）或 nginx 反代双端口
- admin 可内嵌在主后端（`/admin`），也可作为独立进程运行（`admin/main.py`）

## 快速开始（本地）

需要：Python 3.12+、Node 18+、一个终端窗口跑后端、一个跑前端。

```bash
# 1. 克隆
git clone <repo-url> todayfood && cd todayfood

# 2. 启动后端（终端 A）
cd backend
source ~/.py_food/bin/activate        # 或你的虚拟环境
pip install -r requirements.txt
cp .env.example .env                   # 按需填 OPENAI_API_KEY，不填也能跑
uvicorn app.main:app --reload --port 8000

# 3. 启动前端（终端 B）
cd frontend
npm install
cp .env.example .env
npm run dev
# 打开 http://localhost:5173

# 4. 后台管理
#    内嵌：http://localhost:8000/admin（账号密码通过 ADMIN_USERNAME/ADMIN_PASSWORD 环境变量配置）
#    独立：python -m admin.main → http://localhost:9082
```

详细说明见各子目录 README。

## 配置体系总览

整个项目遵循"敏感信息走环境变量、结构化默认值走 toml、运行时兜底走代码默认值"的分层配置原则。

### 后端配置

| 文件 | 用途 | 入 git |
|------|------|--------|
| `backend/config/app.toml` | 服务端口、CORS、时区、缓存、调度、admin 参数 | 是 |
| `backend/config/ai.toml` | AI 协议、模型、超时、各 agent 开关 | 是 |
| `backend/.env.example` | 环境变量模板 | 是 |
| `backend/.env` | 敏感信息（API Key / admin 密码）+ 部署期覆盖 | 否 |

优先级：**环境变量 > .env > app.toml / ai.toml > 代码默认值**

### 前端配置

| 文件 | 用途 | 入 git |
|------|------|--------|
| `frontend/.env.example` | 模板（端口 / 代理目标 / API 前缀） | 是 |
| `frontend/.env` | 本地配置 | 否 |

仅 `VITE_` 前缀变量会暴露到运行时。API 路径集中在 `frontend/src/config.js`。

### admin 配置

admin 复用后端的 `config/app.toml [admin]` 段，可被环境变量覆盖。独立部署时通过 `admin/.env`（若需要）或 systemd `Environment=` 注入。

## 本地测试

### 后端测试

```bash
cd backend
source ~/.py_food/bin/activate
pytest -v                      # 单元测试：seed/picker/api
uvicorn app.main:app --reload  # 手动验证接口
```

### 前端测试

```bash
cd frontend
npm run dev      # dev server
npm run build    # 验证构建
npm run preview  # 预览构建产物
```

### 端到端验证

1. 启动后端 + 前端
2. 打开 `http://localhost:5173`，确认首页能加载今日食历 + 今日菜品
3. 进入「择食」，选偏好后点「再开一签」，确认抽到新菜
4. 访问 `http://localhost:8000/health`，确认 AI 配置正确
5. 访问 `http://localhost:8000/admin`，登录后查看 API 日志 / AI 调用记录

## 远程部署

### 部署清单

| 项 | 说明 |
|----|------|
| 服务器 | Linux（systemd --user 支持） |
| Python | 3.12+ |
| Node | 18+（仅构建前端时需要） |
| 端口 | 后端 9081、admin 9082（可改） |
| 数据 | `backend/data/log.db`（SQLite，自动创建） |

### 部署步骤

```bash
# 1. 拉代码
cd ~/project
git clone <repo-url> todayfood && cd todayfood

# 2. 配置后端 .env（必改 OPENAI_API_KEY / ADMIN_PASSWORD）
cd backend
cp .env.example .env && vim .env

# 3. 安装后端依赖
python -m venv ~/.py_food
source ~/.py_food/bin/activate
pip install -r requirements.txt

# 4. 构建前端（后端托管模式）
cd ../frontend
npm install && npm run build

# 5. 准备目录与 systemd unit
cd ..
mkdir -p logs
cp deploy/todayfood.service ~/.config/systemd/user/
cp deploy/todayfood-admin.service ~/.config/systemd/user/   # 可选：admin 独立部署
cp deploy/todayfood-backup.service ~/.config/systemd/user/  # 可选：日志备份
cp deploy/todayfood-backup.timer ~/.config/systemd/user/

# 6. 按服务器路径修改 unit 文件中的 WorkingDirectory / ExecStart 路径
vim ~/.config/systemd/user/todayfood.service

# 7. 启动
systemctl --user daemon-reload
systemctl --user enable --now todayfood
systemctl --user status todayfood
journalctl --user -u todayfood -f
```

### nginx 反代示例（生产推荐）

```nginx
server {
    listen 80;
    server_name todayfood.example.com;

    root /home/<user>/project/todayfood/frontend/dist;
    index index.html;
    location / { try_files $uri $uri/ /index.html; }

    location /api/ { proxy_pass http://127.0.0.1:9081; }
    location /admin/ { proxy_pass http://127.0.0.1:9081; }
}
```

### 日志备份

`deploy/backup_logs.sh` 会把 `logs/` 与 `backend/data/log.db` 打包到 `backups/YYYY-MM-DD/`，保留 14 天。配合 `todayfood-backup.timer` 每天 03:20 自动执行：

```bash
systemctl --user enable --now todayfood-backup.timer
```

### 升级流程

```bash
cd ~/project/todayfood
git pull
cd backend && pip install -r requirements.txt
cd ../frontend && npm install && npm run build
systemctl --user restart todayfood
```

## 目录速览

```
todayfood/
├── frontend/          前端 Vue 3 应用
├── backend/           后端 FastAPI 应用（含 AI 接入）
├── admin/             后台管理（可内嵌可独立）
│   ├── backend/       admin 的路由 / 鉴权 / SQLite 访问层
│   ├── frontend/      单文件 HTML 管理界面
│   └── main.py        独立部署入口
├── deploy/            systemd unit + 备份脚本
├── .gitignore
└── README.md          本文件
```

## 技术栈

- **前端**：Vue 3 + Vue Router + Vite，原创 SVG 图标，暖橙米主题
- **后端**：FastAPI + uvicorn + pydantic，SQLite (WAL) 存日志
- **AI**：openai-agents SDK，支持 `chat_completions` 与 `responses` 双协议，超时/异常自动回退本地数据池
- **配置**：TOML（结构化默认值）+ .env（敏感/覆盖）+ 环境变量（运维期）
- **部署**：systemd --user + nginx 反代（可选）
