# 后端服务说明

面向「今日食堂 · 菜单与食谱」的 Python 后端。**零第三方依赖**，只用标准库，方便直接部署。

## 启动

```bash
# 在仓库根目录
python menu-recipe-site/server/run.py

# 常用参数
python menu-recipe-site/server/run.py --port 5190        # 换端口
python menu-recipe-site/server/run.py --host 0.0.0.0     # 允许局域网访问
python menu-recipe-site/server/run.py --reset            # 清空订单与收藏
python menu-recipe-site/server/run.py --quiet            # 不打印请求日志
```

启动后同一端口同时提供：

| 地址 | 用途 |
| --- | --- |
| `http://127.0.0.1:5188/` | 前端页面（静态文件） |
| `http://127.0.0.1:5188/api/health` | 健康检查 |

## 目录结构

```
server/
├── run.py                      # 启动入口（参数解析、启动横幅）
├── app/
│   ├── __init__.py             # 装配：bootstrap / build_context / serve
│   ├── seed.py                 # 菜品库种子数据（39 道，由前端 data.js 迁移）
│   ├── storage/
│   │   ├── json_store.py       # JSON 存储引擎（原子写、并发锁、损坏自愈）
│   │   └── repository.py       # 领域仓库（菜品/订单/收藏/配置）
│   ├── services/
│   │   ├── menu_service.py     # 菜品列表、筛选、食谱详情
│   │   ├── order_service.py    # 点餐、一周菜单、一键生成、营养统计
│   │   └── favorite_service.py # 收藏
│   └── api/
│       └── router.py           # 路由、JSON 响应、错误处理、静态文件
├── data/                       # 运行时数据（自动创建）
└── tests/test_api.py           # 自测脚本（47 项）
```

## 存储策略

数据库层当前使用**文件存储**，每个领域一个 JSON 文件：

| 文件 | 内容 | 说明 |
| --- | --- | --- |
| `recipes.json` | 菜品库 | 首次启动由 `seed.py` 初始化，之后以文件为准 |
| `users.json` | 用户账号 | 含 PBKDF2 密码哈希与随机盐，**绝不存明文** |
| `families.json` | 家庭 | 用户与家庭的归属关系，为多账号绑定预留 |
| `sessions.json` | 登录会话 | token → userId，带过期时间 |
| `orders.json` | 点餐订单 | **按家庭隔离**，同家庭成员共享同一份 |
| `favorites.json` | 收藏 | **按用户隔离**，每个账号各自独立 |
| `config.json` | 系统配置 | 周信息、营养目标、饮水量 |

**隔离规则**

| 数据 | 隔离维度 | 原因 |
| --- | --- | --- |
| 一周菜单 / 点餐 / 营养 | `familyId` | 同家庭共享一份菜单 |
| 我的收藏 | `userId` | 每个人的口味不同 |
| 登录会话 | `token` | 每个设备独立登录 |

用户注册时会自动创建一个"xxx 的家庭"，并成为 owner。这样"菜单挂家庭"的模型从第一天就成立，后续加入家庭机制时只需把成员迁入同一家庭，菜单自然共享。

**前端展示 → 后端字段映射**

| 前端展示元素 | 后端字段 |
| --- | --- |
| 菜品缩略图 / 名称 / 标签 | `recipes.id` / `name` / `tags` |
| 时长 / 难度 / 份量 | `time` / `difficulty` / `serving` |
| 营养拆解（5 项） | `nutrition.{calorie,protein,fat,carb,fiber}` |
| 食材清单（主料标记） | `ingredients[{name, amount, main}]` |
| 烹饪步骤 + 每步耗时 | `steps[{title, desc, minutes}]` |
| 小贴士 | `tips` |
| 一周菜单 / 点餐篮 | `orders.weeks[key][day][meal] = [{id, qty}]` |
| 我的收藏 | `favorites` 数组 |
| 营养概览每日数据 | **不落盘**，由订单实时计算，避免两份数据不一致 |

### 存储引擎的可靠性设计

- **原子写入**：先写临时文件再 `os.replace`，中途崩溃不会留下半截文件
- **并发保护**：进程内 `RLock` + 跨进程 `fcntl` 文件锁，多线程写不丢数据（测试覆盖 5 线程 × 20 次写入）
- **损坏自愈**：JSON 解析失败时自动备份到 `data/backups/` 再回落为空，不会让服务起不来

## 接口

统一响应格式：

```json
// 成功
{ "ok": true, "data": { ... } }
// 失败
{ "ok": false, "error": "错误说明" }
```

| 方法 | 路径 | 需登录 | 说明 |
| --- | --- | --- | --- |
| GET | `/api/health` | 否 | 健康检查，返回菜品数量 |
| POST | `/api/auth/register` | 否 | 注册 `{username, password, displayName?}` |
| POST | `/api/auth/login` | 否 | 登录 `{username, password}` |
| GET | `/api/auth/me` | 是 | 当前用户信息 |
| POST | `/api/auth/logout` | 是 | 退出登录，使 token 失效 |
| GET | `/api/family` | 是 | 家庭信息与成员列表（为家庭机制预留） |
| GET | `/api/meta` | 是 | 标签字典、周信息、营养目标 |
| GET | `/api/dishes?tag=&q=` | 是 | 菜品橱窗，支持分类筛选与关键词搜索 |
| GET | `/api/dishes/{id}` | 是 | 食谱详情（含标签中文、步骤总时长） |
| GET | `/api/menu` | 是 | 一周菜单完整视图（按天/餐次展开 + 合计） |
| POST | `/api/menu/items` | 是 | 加入菜品 `{dishId, day, meal, qty}` |
| PATCH | `/api/menu/items` | 是 | 修改数量 `{dishId, day, meal, qty}`，`qty=0` 即移除 |
| DELETE | `/api/menu/items?dishId=&day=&meal=` | 是 | 移除单条 |
| POST | `/api/menu/generate` | 是 | 一键生成整周菜单 |
| POST | `/api/menu/clear` | 是 | 清空整周 |
| GET | `/api/nutrition` | 是 | 营养概览（每日趋势 + 日均完成度 + 饮水） |
| GET | `/api/favorites` | 是 | 收藏列表 |
| POST | `/api/favorites` | 是 | 添加收藏 `{dishId}` |
| DELETE | `/api/favorites/{id}` | 是 | 移除收藏 |
| POST | `/api/favorites/{id}/toggle` | 是 | 切换收藏 |

### 鉴权

登录后在请求头带上 token（二选一）：

```
Authorization: Bearer <token>
X-Auth-Token: <token>
```

未登录访问受保护接口返回 `401`，前端会自动跳回登录页。

错误码：`400` 参数非法 / `401` 未登录或会话失效 / `404` 资源不存在 / `405` 方法不允许 / `500` 服务端错误。

### 安全说明

- 密码使用 **PBKDF2-HMAC-SHA256**，每用户独立随机盐，迭代 20 万次
- 校验使用常量时间比较（`hmac.compare_digest`），避免时序攻击
- 登录失败统一提示"用户名或密码错误"，不暴露账号是否存在
- 用户名大小写不敏感，避免 `Tom` 与 `tom` 注册成两个账号
- 会话 token 由 `secrets.token_urlsafe(32)` 生成，默认 30 天过期，过期自动清理
- 返回体不含 `passwordHash` 与 `salt`，有测试断言兜底

## 营养口径说明

营养目标的量纲是**每日建议摄入量**，所以完成度按**日均值**比较：

```
日均值 = 已排菜品总量 ÷ 已排天数
完成度 = 日均值 ÷ 每日目标
```

未排菜的日子不计入分母，避免被稀释。接口同时返回 `total`、`dailyAvg`、`target`、`percent`，前端可自行选择展示口径。

## 自测

```bash
cd menu-recipe-site/server
python -m tests.test_api     # 存储 / 点餐 / 营养 / 接口（48 项）
python -m tests.test_auth    # 注册登录 / 密码安全 / 隔离性（54 项）
```

## 前端对接

前端通过 `js/api.js` 调用上述接口，token 存于 `localStorage`。

- 启动时若已有 token，会先调 `/api/auth/me` 恢复会话
- 任何接口返回 `401`，自动清除 token 并跳回登录页
- 未登录时只显示登录页，主应用不渲染

## 后续扩展

### 家庭机制（数据模型已就绪）

当前每个用户注册时自动拿到一个专属家庭。要支持"多账号绑定一个家庭"，只需新增：

1. `POST /api/family/invite` —— owner 生成邀请码
2. `POST /api/family/join` —— 成员凭邀请码加入，更新其 `familyId`
3. `POST /api/family/leave` —— 成员退出

`Repository` 已提供 `add_family_member()`，家庭成员列表也已通过 `/api/family` 暴露。

### AI 模块

新增 `app/services/ai_service.py`，复用 `Repository` 读取菜品与订单作为上下文；在 `router.py` 的 `ROUTES` 表加 `/api/ai/*` 前缀路由即可，不需要改动现有接口。前端在 `js/api.js` 增加对应方法。
