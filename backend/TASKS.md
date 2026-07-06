# 今日宜吃 · 后端开发任务清单

> 基于前端代码梳理，列出需要迁移到后端的逻辑：前端按钮触发事件、自动任务、AI 调用。
> 前端代码位于 `../frontend/`，核心逻辑集中在 `src/composables/useFortune.js`。

---

## 一、前端按钮触发事件（需迁移后端）

### 1. 「再开一签」按钮 — 食历页 (Home.vue)
- **触发位置**：`Home.vue` → `onRedraw()` → `redraw()` → `fetchDrawResult()`
- **当前实现**：本地伪随机抽菜品，`pickByTags`/`pickAny`，排除当前菜品兜底
- **后端任务**：实现 `POST /api/fortune/draw`
  - 入参：`{ excludeId?: string, preferences?: { mood, flavor, note } }`
  - 出参：一道菜品完整对象 `{ id, title, category, stars, reason, sign, signName, level, cookTime, difficulty, direction, ... }`
  - 要求：保证 `excludeId` 对应菜品不返回（前后两次不重复）
- **前端改造**：`fetchDrawResult()` 内替换为 `fetch('/api/fortune/draw', ...)`，删除本地 `pickByTags`/`pickAny` 兜底

### 2. 「选一餐 / 再选一餐」按钮 — 选一选页 (Detail.vue)
- **触发位置**：`Detail.vue` → `onPickMe()` → `redraw()` → 同上 `fetchDrawResult()`
- **当前实现**：复用首页 redraw 逻辑，传入 `state.preferences`
- **后端任务**：复用同一个 `POST /api/fortune/draw`，但必须处理 `note` 自由文本（见「AI 调用」第 1 条）
- **前端改造**：无额外改造，与按钮 1 共用接口

### 3. 「复制饭签」按钮 — 食历页 (Home.vue)
- **触发位置**：`Home.vue` → `onCopy()` → `buildShareText()`
- **当前实现**：纯前端拼接分享文案
- **后端任务**：**无需迁移**。保持前端纯文本拼接即可。
  - 若后续要做"分享图生成"或"服务端短链"，再新增 `POST /api/share/generate`

### 4. 心情/口味「换」按钮 — 选一选页 (Detail.vue)
- **触发位置**：`Detail.vue` → `refreshMood()` / `refreshFlavor()`
- **当前实现**：本地 16 项池随机抽 4 项
- **后端任务**：**暂不迁移**（选项池轻量、无个性化需求）。
  - 若后续要做"按用户历史推荐选项"，新增 `GET /api/preferences/options?type=mood|flavor`

### 5. chip 选择 / 偏好设置 — 选一选页 (Detail.vue)
- **触发位置**：`Detail.vue` → `onPick()`
- **当前实现**：纯前端状态 `state.preferences`
- **后端任务**：**无需迁移**。前端本地状态即可。
  - 若后续做用户画像，可新增 `POST /api/user/preferences` 持久化

---

## 二、自动任务（需迁移后端）

### A1. 每日食历生成（核心自动任务）
- **当前位置**：`useFortune.js` → `dailyExtras` computed，基于 `today.seed` 本地生成
- **当前实现**：用 LCG 伪随机从本地数据池抽取：
  - 黄历宜（`pickAlmanacYi`，3-4 条）
  - 黄历忌（`pickAlmanacJi`，2-3 条）
  - 干饭宜（`pickSuitable`，3 条）
  - 干饭忌（`pickAvoid`，3-5 条）
  - 幸运三件套（`pickLucky`：口味/颜色/方位）
  - 签号 + 签文（`pickSignNo` + `pickSignObj`）
- **后端任务**：实现 `GET /api/fortune/today`
  - 出参：上述完整"今日食历"包，按日期稳定（所有用户同一天看到相同内容）
  - 建议：后端按日期缓存（Redis 或内存），凌晨 0 点定时任务刷新
  - 价值：服务端可人工运营干预（替换敏感内容、节日特供）
- **前端改造**：`dailyExtras` 改为请求 `/api/fortune/today`，缓存到 state；本地种子逻辑全部删除

### A2. 每日菜品初始化
- **当前位置**：`useFortune.js` → `pickTodayFood()`（页面首次加载时调用）
- **后端任务**：合并到 A1 接口 `GET /api/fortune/today`，返回 `todayFood` 字段
- **前端改造**：初始化时请求 A1 接口，取 `todayFood` 作为 `state.current`

### A3. 每日凌晨刷新（后端定时任务）
- **任务**：每天 00:00（北京时间）重新生成当日食历数据
- **实现**：Cron / 定时器，写入缓存层
- **前端无改造**

---

## 三、AI 调用（需迁移后端）

### AI1. 「想吃点啥」自由文本解析（核心 AI 调用）
- **当前位置**：`Detail.vue` 的 `noteText` 存入 `state.preferences.note`，但本地 `pickByTags` **完全未使用** note 字段（代码注释："note 留给后端"）
- **后端任务**：在 `POST /api/fortune/draw` 中，当 `preferences.note` 非空时：
  - 调用 LLM 把自由文本解析为结构化标签（如"热乎的汤面" → `{ flavor: 'light', temp: 'hot', type: 'noodle' }`）
  - 或直接让 LLM 基于用户描述 + 菜品池生成推荐
- **Prompt 设计要点**：限定菜品池范围，返回 JSON，避免幻觉出菜品池外的菜
- **前端改造**：无需改造，前端已正确地把 note 传给后端

### AI2. 推荐理由个性化生成
- **当前位置**：`food.reason` 是 `foods.js` 数据池里的**静态文案**
- **后端任务**：`POST /api/fortune/draw` 返回菜品时，可选用 LLM 生成结合用户 mood/note 的个性化 reason
- **可选**：也可保持静态 reason，AI 只参与选菜。优先级低。
- **前端改造**：无（字段名不变）

### AI3. 签文动态生成（可选）
- **当前位置**：`signPool` 静态 12 条签文
- **后端任务**：可选用 LLM 生成当日限定签文，增强仪式感
- **可选**：优先级最低，静态池已足够
- **前端改造**：无

---

## 四、数据迁移清单

以下数据池当前在前端 `src/data/`，应迁移到后端（DB 或配置文件），前端通过接口获取：

| 文件 | 内容 | 迁移目标 | 前端是否保留 |
|---|---|---|---|
| `foods.js` | 12 道菜品完整数据 | 后端 DB / seed | 删除（仅接口返回） |
| `signs.js` | 12 条签文 | 后端 DB | 删除 |
| `almanac.js` | 黄历宜忌池 | 后端 DB | 删除 |
| `avoids.js` | 干饭忌吃池 | 后端 DB | 删除 |
| `suitable.js` | 干饭宜吃池 | 后端 DB | 删除 |
| `icons.js` | 菜品 SVG 图标 | **保留前端**（纯展示资源） | 保留 |

> `icons.js` 是纯展示资源，无业务逻辑，保留在前端最合适。

---

## 五、接口总览

| 方法 | 路径 | 触发方 | 说明 |
|---|---|---|---|
| GET | `/api/fortune/today` | 自动（页面加载） | 今日食历包 + 今日菜品 |
| POST | `/api/fortune/draw` | 按钮（再开一签/选一餐） | 抽一道新菜，支持 excludeId + preferences |
| POST | `/api/share/generate` | 按钮（可选，未来） | 生成分享图/短链 |
| GET | `/api/preferences/options` | 按钮（可选，未来） | 个性化选项池 |

---

## 六、建议实施顺序

1. **P0**：搭建后端框架（选型：Node/Express 或 Python/FastAPI）+ 数据池迁移
2. **P0**：实现 `GET /api/fortune/today`（对应自动任务 A1+A2）
3. **P0**：实现 `POST /api/fortune/draw` 基础版（不含 AI，先迁移本地抽签逻辑）
4. **P1**：接入 AI1（note 自由文本解析）
5. **P2**：AI2 / AI3（个性化理由、动态签文）
6. **P2**：前端 `useFortune.js` 改造，删除本地兜底逻辑
