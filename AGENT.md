# AGENT.md — 后续智能体唯一入口

新对话请**只读本文件**即可接着干活。人类文档是 `README.md`。

- 仓库：https://github.com/MirroR0102/Enterprise-Automation-Agent
- 规划：`docs/superpowers/plans/2026-09-15-enterprise-ops-agent.md`（根目录也有一份同名稿，勿另发明需求）
- 本机：`127.0.0.1:8000`，前端静态页挂在 `/`，OpenAPI `/docs`
- 工作区就是本文件夹（`企业业务流程自动化Agent`），不要改并列的 COC / langchain 笔记仓
- **未获用户明确许可前禁止 `git push`**（用户需要先开 VPN）

---

## 强制：用户任务完成后必须同步两份文档

每完成一项用户明确要求的工作，必须同时修改 `AGENT.md` 与 `README.md`。口径一致。未同步视为任务未完成。

**修改留痕（用户要求）：** 以后每一次修改都要在本文件留下痕迹（在下方「已完成」区追加一条：日期 · 改了什么 · 涉及文件），以便更新 PPT / 讲稿 / 执行说明时可直接查本 `.md` 文件的记录对照同步。

---

## 硬约束（违反即视为回归）

1. 编排必须是 **LangGraph `StateGraph`**，不要改回纯 LangChain `AgentExecutor` 作为主路径。
2. LLM 默认 **DeepSeek**（`LLM_PROVIDER=deepseek`）。GPT-4o-mini 只是演示切换；保留 Qwen 配置位。密钥只在 `.env`。
3. 记忆用 **MemorySaver**，`thread_id` 与 API `session_id` 一一对应。
4. 最大工具轮次 **8**（先 +1 再判断 `> MAX_TOOL_ROUNDS`）；超时 **`TASK_TIMEOUT_S`（默认 30s）**。
5. 工具失败 **自动重试 1 次**，仍失败则 `status=failed` 并停止后续工具链。
6. SQL 工具只读：必须以 `select` 开头、禁止分号多语句、黑名单 `drop/alter/delete/truncate/insert/update/create/grant/revoke`。
7. 最终对用户可见结果为 **Markdown**；不要捏造销售数字。
8. 需要登录；角色只有 `ops` / `dev`。`GET /api/logs` 仅 `dev`。
9. `KB_ENABLED` 默认 false，走 Stub，文案固定「当前未接入企业内部知识库」，不编造业务内容。不要实现 3 号的向量库/解析/上传。
10. 勿提交 `.env`、`.venv`、`data/`、`reports/*.md`（保留 `reports/.gitkeep`）。
11. 用户未明确要求时：**不要 `git push`**、不要改 git config、不要 `--force`。
12. 用户说「提交」通常指本地 commit；「上传 / 推送」才 push。
13. 完成本次用户要求后，同步更新 `AGENT.md` 与 `README.md`。
14. 用户说停止就立刻停，不要继续加功能。
15. **汇报材料同步**：对架构 / 验收口径 / 安全止损 / 演示账号与验收句 / 第 3 部分接口 / 联调问题结论等**重要改动**完成后，必须同步更新本地 `docs/presentation/` 下的 PPTX 与演讲稿 PDF（可重跑 `scripts/build_presentation.py`），并核对大纲 `2026-09-15-part4-30min-presentation-outline.md`。这两份成品**禁止 push**（已 gitignore）。

---

## 改哪里

| 目标 | 优先打开 |
| --- | --- |
| 图结构 / 轮次 / 重试 / 结束路由 | `app/agent/graph.py`、`nodes.py`、`state.py` |
| 系统提示 | `app/agent/prompts.py` |
| 工具注册 | `app/tools/registry.py` |
| SQL 防护 | `app/tools/mysql_query.py` |
| 计算器 / 时间 / 搜索 / 文件 | `app/tools/{calculator,time_tool,search,file_io}.py` |
| 知识库 Stub/HTTP | `app/tools/kb.py` |
| 登录 JWT | `app/auth/security.py`、`app/api/auth.py`、`app/auth/deps.py` |
| 会话 / 事件 / 取消 | `app/api/chat.py`、`app/runtime.py` |
| 日志与 60 天清理 | `app/logging_service.py`、`scripts/purge_logs.py` |
| MySQL / mock SQLite | `app/db/mysql.py`、`schema.sql`、`seed.sql` |
| 前端 | `web/login.html`、`index.html`（侧栏能力壳）、`logs.html`、`app.css` |
| 配置常量 | `app/config.py`、`.env.example` |
| 单测 | `tests/test_*.py` |
| 30 分钟汇报 PPT/PDF（本地，不 push） | `docs/presentation/`、`scripts/build_presentation.py`、根目录 `2026-09-15-part4-30min-presentation-outline.md` |

---

## 建议工作流

1. 改工具或 SQL 防护 → `pytest tests/test_sql_guard.py tests/test_calculator.py tests/test_kb.py`
2. 改图 → `pytest tests/test_graph_limits.py`
3. 改 API/鉴权/取消 → `pytest tests/test_auth.py tests/test_api_cancel.py`
4. 改前端 → 启动 uvicorn，用浏览器走登录 → 发送 → 时间线 → 取消 → dev 日志
5. 提交前同步 `AGENT.md` + `README.md`；全量 `pytest -q`
6. **若本次是重要改动**：同步更新 `docs/presentation/` 的 PPTX/PDF（或重跑 `scripts/build_presentation.py`），再决定是否本地 commit（演示成品默认不进 git）
7. 推 GitHub 仅当用户确认 VPN 已开；**勿 push** `docs/presentation/*.pptx|*.pdf`

Windows / PowerShell：用 `D:\anaconda\python.exe -m venv .venv` 建环境；日常跑命令用 `.\.venv\Scripts\python.exe`。

---

## 当前待办

- [ ] 若有真实 DeepSeek + Tavily，按 `scripts/acceptance_check.md` 跑一遍联网验收句
- [ ] 生产若要多副本：把 MemorySaver 换成 Postgres checkpointer（README 已记为后续）

## 已完成（摘要，避免重复劳动）

- Task 1–10：脚手架、JWT 登录（ops/dev）、SQL 防护、计算器/时间、MySQL schema+seed（含 `USE_MOCK_DB`）、Tavily/文件/KB Stub、LangGraph 8 轮与失败重试、日志、FastAPI 会话/事件/SSE/取消、静态前端、pytest
- 本机 venv：`D:\anaconda\python.exe -m venv .venv`（Python 3.13.9）；`pytest -q` → **23 passed**
- 默认账号 `ops/ops123`、`dev/dev123`
- 根目录规划稿 `2026-09-15-enterprise-ops-agent.md` 已纳入仓库；`*.docx` 已 gitignore，不上传
- `TASK_TIMEOUT_S=30` 按规划固定，不放宽
- 已推送 `main` → `origin`（`https://github.com/MirroR0102/Enterprise-Automation-Agent`）；直连失败时用本机代理 `127.0.0.1:7892`
- SQL 工具：错误列名等执行失败改为返回可读错误（不抛异常），系统提示与工具说明写明 `sales(sale_date, amount, region)`，避免整条任务因一次写错列名而终止
- 联调问题（`order_date` / 工具失败即停）已写入 `README.md`「联调问题记录」，供项目报告引用；勿删该节
- 30 分钟汇报材料已生成到 `docs/presentation/`（PPTX + 演讲稿 PDF，gitignore，不 push）；重要改动后须同步更新（见硬约束第 15 条）
- 2026-09-16：取消与终态互斥（完成后点取消仍保持 completed）；工作台浅色壳 + 左侧「运营周报 / 知识库占位」能力栏；状态中文芯片
- 2026-09-16 交互改版：底部 composer、侧栏左下头像、过程全宽、final 后右侧分屏预览（可收起）、取消仅 running 可点
- 2026-09-16：M1/U1–U6/DB1 — 同会话记忆、发送清空、昵称设置、入参默认展开、每用户分库 `eoa_u_{id}` + 过往周报
- 2026-09-16：侧栏身份「加载中」/设置点不开 — `marked` CDN 改 defer；整块用户区可点；本地缓存先渲染；`/login` 回传 `username`；MySQL `connect_timeout`
- 2026-09-16：汇报材料 P0–P4 完成 — 20 页少字多图 PPT + ≈30′ 讲稿 + 报告执行说明；脚本 `scripts/build_presentation.py`；成品本地不 push
- 2026-09-16（v2）：用户认为首版质量不足，整体重做三件套 — 22 页新版 PPT（新增分库页、联调复盘页；经 PowerPoint 导出 PNG 逐页抽查）+ 7 页讲稿（正文 ≈5200 字，含减配/附录）+ 4 页执行说明（md+pdf）；生成脚本重写；旧版产物已被覆盖（不 push）
- 2026-09-16：新增「修改留痕」强制规则（本文件「强制」区 + README「维护约定」同步）——每次修改在「已完成」区留一条记录，供 PPT/讲稿同步时对照；本条即第一条留痕。
- 2026-09-16：全仓源码补充中文注释（仅注释/docstring、不改行为）——`app/**`、`web/**`、`scripts/init_db.py`/`purge_logs.py`、`tests/*.py`。
- 2026-09-17：两项收尾改动——① 真流式：agent/tools 异步节点 + `final_delta` 逐字推送，前端改 SSE（失败回退轮询）；② `web_search` 固定近一周（Tavily `time_range=week`/`days=7`/`topic=news`），提示词与工具说明禁止编造新闻。涉及：`app/agent/nodes.py`、`prompts.py`、`app/tools/search.py`、`app/api/chat.py`、`web/index.html`、`tests/test_graph_limits.py`、`AGENT.md`/`README.md`。

---

## 主要 API

见 README「主要 API」。会话键：`configurable.thread_id = session_id`。

取消：`POST /api/sessions/{id}/cancel`。仅 `running` 时可取消；若已是 `completed`/`failed`/`timeout`/`max_rounds`，或事件中已有 `final`，**不得**改写成 `cancelled`（返回 `ok:false` 并保持原终态）。图节点仍检查取消标志；迟到的取消在已有报告时视为成功完成。

过往周报：`GET /api/reports` / `GET /api/reports/{id}`，数据在每用户分库（`app/db/user_store.py`），与销售业务库分离。

---

## 技术栈与目录

| 层 | 技术 |
| --- | --- |
| 编排 | FastAPI + LangGraph StateGraph + MemorySaver |
| LLM | OpenAI 兼容（默认 DeepSeek） |
| 存储 | MySQL 或 SQLite mock |
| 前端 | 静态 HTML/JS（`web/`） |

```
./
├── AGENT.md
├── README.md
├── app/agent|api|auth|db|tools
├── web/
├── reports/
├── tests/
└── scripts/
```

---

## Git / 代理

- `origin` → `https://github.com/MirroR0102/Enterprise-Automation-Agent.git`
- 直连 443 失败时（不要改全局 git config），用户常见本地代理 `127.0.0.1:7892`

---

## 设计原则

- 小改动、贴现有风格；不要无关重构。
- 验收用例必须能在 mock 下单测通过；联网能力在 README 标明必填项。
- 做完用户要求 → 改 `AGENT.md` + `README.md` →（若用户要求）再 commit。
