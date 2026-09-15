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
| 前端 | `web/login.html`、`index.html`、`logs.html` |
| 配置常量 | `app/config.py`、`.env.example` |
| 单测 | `tests/test_*.py` |

---

## 建议工作流

1. 改工具或 SQL 防护 → `pytest tests/test_sql_guard.py tests/test_calculator.py tests/test_kb.py`
2. 改图 → `pytest tests/test_graph_limits.py`
3. 改 API/鉴权/取消 → `pytest tests/test_auth.py tests/test_api_cancel.py`
4. 改前端 → 启动 uvicorn，用浏览器走登录 → 发送 → 时间线 → 取消 → dev 日志
5. 提交前同步 `AGENT.md` + `README.md`；全量 `pytest -q`
6. 推 GitHub 仅当用户确认 VPN 已开

Windows / PowerShell：用 `D:\anaconda\python.exe -m venv .venv` 建环境；日常跑命令用 `.\.venv\Scripts\python.exe`。

---

## 当前待办

- [ ] 用户确认 VPN 已开后，再 `git push` 到 `origin`（`https://github.com/MirroR0102/Enterprise-Automation-Agent.git`）
- [ ] 若有真实 DeepSeek + Tavily，按 `scripts/acceptance_check.md` 跑一遍联网验收句
- [ ] 生产若要多副本：把 MemorySaver 换成 Postgres checkpointer（README 已记为后续）

## 已完成（摘要，避免重复劳动）

- Task 1–10：脚手架、JWT 登录（ops/dev）、SQL 防护、计算器/时间、MySQL schema+seed（含 `USE_MOCK_DB`）、Tavily/文件/KB Stub、LangGraph 8 轮与失败重试、日志、FastAPI 会话/事件/SSE/取消、静态前端、pytest
- 本机 venv：`D:\anaconda\python.exe -m venv .venv`（Python 3.13.9）；`pytest -q` → **23 passed**
- 默认账号 `ops/ops123`、`dev/dev123`
- 远程 `origin` 已指向目标仓库；**尚未 push**（等用户确认 VPN）

---

## 主要 API

见 README「主要 API」。会话键：`configurable.thread_id = session_id`。

取消：`POST /api/sessions/{id}/cancel` 设 `runtime` 取消标志，图节点每步检查；同时 `task.cancel()`。

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
