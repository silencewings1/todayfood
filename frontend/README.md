# 今日宜吃 · 前端

基于 Vue 3 + Vite 的「今日宜吃」小程序风格 H5 应用。竖屏布局、底部 TabBar 切换食历 / 择食 / 关于三个页面，所有数据由后端 API 提供。

## 工程结构

```
frontend/
├── public/
│   └── favicon.svg
├── src/
│   ├── main.js                  # 应用入口，挂载 Vue + Router
│   ├── App.vue                  # 根组件（顶部栏 + <router-view> + TabBar）
│   ├── config.js                # 集中导出 API 路径（前缀来自 .env）
│   ├── router/index.js          # 路由表：/index /pick /about
│   ├── views/                   # 页面
│   │   ├── Home.vue             #   今日宜吃（食历 + 今日菜品 + 开签）
│   │   ├── Detail.vue           #   选一选（偏好选择 + 抽签）
│   │   └── Mine.vue             #   关于
│   ├── components/              # 通用组件
│   │   ├── AppHeader.vue        #   顶部栏（sticky + 毛玻璃）
│   │   ├── AppLogo.vue          #   品牌 logo
│   │   ├── AppTabBar.vue        #   底部 TabBar（食历/择食/关于）
│   │   └── DrawOverlay.vue      #   抽签动画遮罩
│   ├── composables/
│   │   └── useFortune.js        # 核心状态管理 + API 调用（不再持有数据池）
│   ├── data/
│   │   └── icons.js             # 菜品原创 SVG 图标（按 food.id 匹配）
│   └── assets/
│       └── styles/
│           ├── variables.css    # 主题变量（暖橙米渐变 / 主橙 / 卡片米白）
│           └── main.css         # 全局样式
├── index.html
├── vite.config.js               # 端口/代理目标从 .env 读取
├── package.json
├── .env.example                 # 环境变量模板
└── .env                         # 本地配置（gitignore）
```

## 配置体系

前端配置通过 Vite 内置的 `.env` 机制管理，仅 `VITE_` 前缀的变量会暴露到运行时代码（`import.meta.env.VITE_XXX`）。

| 文件 | 用途 | 是否入 git |
|------|------|------------|
| `.env.example` | 模板，列出所有可配置项 | 是 |
| `.env` | 本地默认值 | 否（gitignore） |
| `.env.local` | 本地覆盖（可选） | 否 |

可用变量（详见 `.env.example`）：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `VITE_DEV_PORT` | `5173` | dev server 端口 |
| `VITE_DEV_PROXY_TARGET` | `http://127.0.0.1:8000` | dev 阶段 `/api` 代理目标，指向后端 `config/app.toml` 的 `[server].host:port` |
| `VITE_API_BASE` | `/api` | API 前缀，开发由 vite 代理、生产由 nginx 反代 |

API 路径集中在 `src/config.js` 导出，业务代码统一从 `@/config` 引入：

```js
import { API } from '@/config'
fetch(API.TODAY)   // -> /api/fortune/today
fetch(API.DRAW, ...) // -> /api/fortune/draw
```

修改 `.env` 后需重启 `npm run dev` 生效。

## 本地测试

### 1. 环境准备

```bash
cd frontend
npm install          # 首次或依赖变化时
```

### 2. 配置 .env

```bash
cp .env.example .env
# 默认值已可用：5173 端口、代理到 127.0.0.1:8000
# 若后端跑在别的端口，改 VITE_DEV_PROXY_TARGET 即可
```

### 3. 启动 dev server

```bash
npm run dev
# 打开 http://localhost:5173
```

开发期所有 `/api/*` 请求会被 vite 代理到 `VITE_DEV_PROXY_TARGET`，无需在前端处理跨域。请确保后端已启动（见 `backend/README.md`）。

### 4. 生产构建

```bash
npm run build        # 产物输出到 dist/
npm run preview      # 本地预览构建产物（4173 端口）
```

构建产物可由后端直接托管（`frontend/dist` 存在时后端会自动挂载），也可交给 nginx 单独托管。

## 远程部署

### 方式一：后端托管（最简）

前端构建产物交由后端 FastAPI 直接服务，单端口上线：

```bash
# 服务器上
cd ~/project/todayfood/frontend
npm install && npm run build
# 生成 frontend/dist/，后端启动后自动挂载到 /
# 直接访问 http://server:9081 即可
```

### 方式二：nginx 独立托管（推荐生产）

前端独立部署，nginx 反代 `/api` 到后端：

```bash
cd ~/project/todayfood/frontend
npm install && npm run build
```

nginx 配置示例：

```nginx
server {
    listen 80;
    server_name todayfood.example.com;

    root /home/<user>/project/todayfood/frontend/dist;
    index index.html;

    # 前端 SPA 路由回退
    location / {
        try_files $uri $uri/ /index.html;
    }

    # 后端 API（与 .env 中 VITE_API_BASE 保持一致）
    location /api/ {
        proxy_pass http://127.0.0.1:9081;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # 后台管理（可选，也可独立域名）
    location /admin/ {
        proxy_pass http://127.0.0.1:9081;
    }
}
```

### 升级流程

```bash
cd ~/project/todayfood
git pull
cd frontend && npm install && npm run build
# nginx 静态托管：无需重启；后端托管：systemctl --user restart todayfood
```

## 页面与路由

| 路径 | 组件 | Tab | 说明 |
|------|------|-----|------|
| `/` | 重定向 → `/index` | — | — |
| `/index` | `Home.vue` | 食历 | 今日食历卡 + 今日菜品 + 再开一签 |
| `/pick` | `Detail.vue` | 择食 | 心情/口味/想吃点啥偏好选择 → 抽新菜 |
| `/about` | `Mine.vue` | 关于 | 项目介绍与免责声明 |

## 关键设计

- **竖屏小程序布局**：固定底部 TabBar，所有信息在当前页面内呈现，不使用滚动加载
- **每日食历固定**：「今日食历」卡内容每日固定不变，仅依赖后端 `today.seed`，与「再开一签」切换的菜品相互独立
- **原创 SVG 图标**：菜品图标通过 `getFoodSvg(food.id)` 从 `data/icons.js` 获取，禁止使用 emoji
- **暖橙米主题**：背景渐变 `#f7ead6 → #f3e2c7`，卡片 `#fdf7ec`，主橙 `#c4622d`
- **桌面/移动自适应**：桌面端显示 420px 宽居中圆角卡片，移动端全屏
