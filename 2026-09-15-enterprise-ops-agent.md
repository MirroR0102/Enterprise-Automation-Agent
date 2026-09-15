# 企业业务流程自动化 Agent 实现规划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Target repo: `https://github.com/MirroR0102/Enterprise-Automation-Agent`. Do not invent requirements beyond this document and the attached product brief.
> **PUSH GATE (user instruction):** Implement and test the FULL project end-to-end. Do **NOT** `git push` until the user confirms VPN is on and push is allowed. When code + tests are done, stop and report completion first.


**Goal:** 基于 LangGraph 构建面向运营人员的有状态 Agent：接收自然语言复杂任务，自动拆解并调用工具（Tavily 搜索、计算器、时间、MySQL 查询、本地 Markdown 文件读写），最多 8 轮工具调用，经 FastAPI 对外提供会话隔离与执行过程可视化，最终输出 Markdown 周报/分析报告。

**Architecture:** FastAPI 提供会话与流式/分步事件 API；核心为 LangGraph `StateGraph` + `MemorySaver`（按 `thread_id`/`session_id` 隔离）。Agent 节点调用 LLM（**默认 DeepSeek**，演示可切 GPT-4o-mini，亦可切 Qwen2-72B-Instruct）做工具选择；工具结果写回 state；达到完成条件或最大轮次后结束。每次思考与工具调用写入 MySQL 日志表，并推送给前端展示「思考 → 工具 → 入参 → 返回」。

**Tech Stack:** Python 3.11+ · LangGraph · LangChain tools (`@tool`, `TavilySearchResults`) · FastAPI · Uvicorn · MySQL（业务查询 + Agent 日志 + 用户账号）· MemorySaver · DeepSeek API（OpenAI 兼容）· 前端：单页 HTML/JS 或轻量 Vite+React（二选一，优先可最快验收的方案）· pytest

**Remote:** 目标 GitHub 仓库为 `https://github.com/MirroR0102/Enterprise-Automation-Agent`（`MirroR0102/Enterprise-Automation-Agent`）。本地可正常 `git commit`；**在用户明确说可以推送之前，禁止 `git push`**（用户需要先开 VPN）。全部代码写完并测试通过后，先向用户汇报「已完成、可推送」，等待确认后再 push。

## Global Constraints

- 编排框架必须是 **LangGraph StateGraph**（不是纯 LangChain AgentExecutor 作为最终方案）。
- LLM：**默认使用 DeepSeek**（OpenAI 兼容接口，环境变量 `LLM_PROVIDER=deepseek`，`DEEPSEEK_API_KEY`，`DEEPSEEK_BASE_URL` 默认 `https://api.deepseek.com`，`LLM_MODEL` 默认如 `deepseek-chat`）。**GPT-4o-mini 仅用于演示/对比**（`LLM_PROVIDER=openai`）。仍保留切换 **Qwen2-72B-Instruct** 的配置位。密钥只放 `.env`，禁止提交密钥。
- 记忆：**MemorySaver**，会话键为 `thread_id`（与 API 的 `session_id` 一一对应）。
- 最大工具调用轮次：**8**；超过立即终止并返回明确提示。
- 单次完整任务超时：**30 秒**强制终止。
- 工具失败：**自动重试 1 次**；仍失败则返回错误说明并停止后续工具链（不无限循环）。
- SQL 工具：只允许只读查询语义；**黑名单拦截**含 `drop`/`alter`/`delete`/`truncate`/`insert`/`update`/`create`/`grant`/`revoke` 等写/高危语句（大小写不敏感）；参数化或严格校验后执行。
- 日志：记录用户输入、思考过程、全部工具调用参数与返回、时间戳；保留策略按 **60 天**（实现清理任务或文档化 cron；至少实现按时间字段可筛）。
- 支持**人工终止**正在运行的任务。
- 最终对用户可见结果为 **Markdown**。
- 验收用例必须能跑通（可用 mock/种子数据）：「帮我搜索2026AI行业新闻，再查询本月销售总额，计算同比增长率，生成一份运营周报 markdown」。
- **需要登录**：简单账号密码登录（会话 Token / JWT 或 signed cookie 均可）；区分角色 `ops`（运营）与 `dev`（开发维护）。运营可对话与看自己的执行过程；开发可看日志。不做 OAuth、不做多租户计费、不做复杂细粒度 RBAC。
- 远程仓库：`https://github.com/MirroR0102/Enterprise-Automation-Agent`。Task 结束只做本地 commit；**不要 push**，除非用户已确认 VPN 已开并允许推送。
- 预留第 3 部分知识库 HTTP 工具接口，默认 `KB_ENABLED=false` 走 Stub；不阻塞独立验收。
- 提交前确保 `pytest` 通过；每完成一个 Task 做一次 git commit。

---

## 产品背景（给执行者的上下文）

运营人员需要查指标、搜行业新闻、做计算、生成周报。固定脚本无法覆盖多变自然语言需求。本系统让 Agent 自主规划步骤并调用工具完成最多 8 步链式任务，并可视化全过程便于排错。

**角色：**

| 角色 | 能力 |
| :--- | :--- |
| 运营业务用户（`ops`） | 登录后输入自然语言任务，查看执行过程与最终结果 |
| 开发维护人员（`dev`） | 登录后查看工具调用日志，调试异常流程（工具配置可用 `.env` + 简单配置页或文档） |

---

## 目标目录结构

```text
.
├── README.md
├── .env.example
├── .gitignore
├── requirements.txt
├── pyproject.toml          # 可选；若只用 requirements.txt 也可
├── app/
│   ├── __init__.py
│   ├── main.py             # FastAPI 入口
│   ├── config.py           # 环境变量与常量（MAX_TOOL_ROUNDS=8, TASK_TIMEOUT_S=30）
│   ├── api/
│   │   ├── __init__.py
│   │   ├── auth.py         # 注册/登录/当前用户（简单账号密码）
│   │   ├── chat.py         # 创建会话、发送任务、取消任务、获取事件（需登录）
│   │   └── logs.py         # 日志查询（需 dev 角色）
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── security.py     # 密码哈希、JWT/session、依赖 get_current_user
│   │   └── models.py       # User 模型或 SQL 访问
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── state.py        # AgentState TypedDict
│   │   ├── graph.py        # StateGraph 定义与编译
│   │   ├── nodes.py        # 思考/工具/结束节点
│   │   └── prompts.py      # 系统提示词
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── registry.py     # 导出全部工具列表
│   │   ├── search.py       # Tavily
│   │   ├── calculator.py
│   │   ├── time_tool.py
│   │   ├── mysql_query.py  # 含 SQL 防护
│   │   └── file_io.py      # 读写 reports/*.md
│   ├── db/
│   │   ├── __init__.py
│   │   ├── mysql.py        # 业务库与日志库连接
│   │   ├── schema.sql      # 业务种子表 + agent_logs 表
│   │   └── seed.sql        # 本月/去年同月销售等验收数据
│   └── logging_service.py  # 写日志、按 session 查询
├── web/                    # 最小可视化前端
│   ├── login.html          # 登录页
│   ├── index.html          # 运营对话 + 过程时间线（未登录跳转登录）
│   └── logs.html           # 开发日志查看（需 dev；可合并为单页多 Tab）
├── reports/                # Agent 文件工具读写目录（gitkeep）
├── tests/
│   ├── test_sql_guard.py
│   ├── test_calculator.py
│   ├── test_graph_limits.py
│   └── test_api_cancel.py
└── docs/
    └── superpowers/
        └── plans/
            └── 2026-09-15-enterprise-ops-agent.md  # 本文件
```

---

## Task 1: 项目脚手架与配置

**Files:**
- Create: `README.md`, `.gitignore`, `.env.example`, `requirements.txt`, `app/__init__.py`, `app/config.py`, `reports/.gitkeep`
- Remote: 初始化 git（若尚无）并设置 `origin` 为 `https://github.com/MirroR0102/Enterprise-Automation-Agent.git`

**Produces:**
- `Settings`（pydantic-settings 或简单 os.getenv）：`LLM_PROVIDER`（默认 `deepseek`）, `DEEPSEEK_API_KEY`, `DEEPSEEK_BASE_URL`（默认 `https://api.deepseek.com`）, `LLM_MODEL`（DeepSeek 默认 `deepseek-chat`；演示 OpenAI 时用 `gpt-4o-mini`）, `OPENAI_API_KEY`/`OPENAI_BASE_URL`（演示用）, `TAVILY_API_KEY`, `MYSQL_DSN`, `JWT_SECRET`（或 session secret）, `MAX_TOOL_ROUNDS=8`, `TASK_TIMEOUT_S=30`, `REPORTS_DIR=reports`

- [ ] **Step 1:** 创建上述文件；`.gitignore` 含 `.env`, `__pycache__/`, `.venv/`, `reports/*.md`（保留 `.gitkeep`）。
- [ ] **Step 2:** `requirements.txt` 至少包含：`langgraph`, `langchain`, `langchain-openai`, `langchain-community`, `tavily-python`, `fastapi`, `uvicorn[standard]`, `mysql-connector-python` 或 `pymysql`+`sqlalchemy`, `pydantic-settings`, `python-dotenv`, `httpx`, `passlib[bcrypt]`, `PyJWT`（或 `python-jose`）, `pytest`, `pytest-asyncio`.
- [ ] **Step 3:** `README.md` 写明：如何复制 `.env.example`、配置 DeepSeek（默认）与演示用 GPT-4o-mini、安装依赖、初始化 MySQL schema/seed、默认账号、启动 API 与打开前端、跑验收句与 pytest；写明仓库地址 `https://github.com/MirroR0102/Enterprise-Automation-Agent`。
- [ ] **Step 4:** 配置 `git remote origin` 为上述仓库（可先 `git fetch`/`pull` 对齐远程，勿在未获推送许可时 push）；Commit: `chore: scaffold enterprise ops agent project`（仅本地 commit）。

---


## Task 2: 登录与鉴权

**Files:**
- Create: `app/auth/security.py`, `app/auth/models.py`, `app/api/auth.py`, `tests/test_auth.py`
- Modify: `app/db/schema.sql`, `app/main.py`（挂载路由与鉴权依赖）

**Interfaces:**
- `POST /api/auth/login` body: `{ "username", "password" }` → `{ "access_token", "token_type": "bearer", "role" }`
- `GET /api/auth/me` → 当前用户
- 可选：`POST /api/auth/register`（若只做 seed 账号可不开放注册；开放则仅允许创建 `ops`，或仅开发环境启用）
- FastAPI 依赖：`get_current_user`、`require_role("dev")`
- 密码：`bcrypt` 或 `pbkdf2`；禁止明文存储

- [ ] **Step 1:** 写 `tests/test_auth.py`：错误密码 401；正确密码返回 token；无 token 访问受保护路由 401；`ops` 访问 `/api/logs` 403，`dev` 可访问。
- [ ] **Step 2:** 实现 users 表、seed 账号、login/me、密码哈希与 JWT（或等价 signed session）。
- [ ] **Step 3:** 后续 chat/logs 路由加上登录与角色校验（可先留 TODO 依赖，在 Task 8 API 任务中强制挂上——本 Task 至少完成 auth 模块与测试）。
- [ ] **Step 4:** Commit（不 push）: `feat: add login and role-based access`

---
## Task 3: SQL 防护与计算器、时间工具（无 LLM）

**Files:**
- Create: `app/tools/calculator.py`, `app/tools/time_tool.py`, `app/tools/mysql_query.py`, `tests/test_sql_guard.py`, `tests/test_calculator.py`

**Interfaces:**
- `safe_eval_math(expr: str) -> float`（仅数学表达式，禁任意 exec）
- `get_current_time() -> str`（ISO 或可读本地时间）
- `is_safe_select_sql(sql: str) -> bool`
- `run_mysql_query(sql: str) -> str`（不安全则抛错/返回错误信息，不执行）

- [ ] **Step 1:** 写 `tests/test_sql_guard.py`：断言含 `DROP TABLE`、`delete from`、`ALTER`、多语句注入等返回 False；合法 `SELECT SUM(amount) FROM sales WHERE ...` 返回 True。
- [ ] **Step 2:** 跑测确认失败后实现黑名单 + 仅允许以 `select` 开头（trim 后）+ 禁止分号多语句。
- [ ] **Step 3:** 计算器用 `ast` 白名单节点实现；测试 `"(100-80)/80"` → `0.25`。
- [ ] **Step 4:** 时间工具返回当前时间字符串；用 `@tool` 包装三个工具。
- [ ] **Step 5:** Commit: `feat: add calculator, time, and SQL guard tools`

---

## Task 4: MySQL schema、种子数据与查询工具接线

**Files:**
- Create: `app/db/mysql.py`, `app/db/schema.sql`, `app/db/seed.sql`
- Modify: `app/tools/mysql_query.py`

**Produces:**
- 业务表示例：`sales(id, sale_date, amount, region)`；至少含「本月」与「去年同月」汇总可算同比。
- 用户表：`users(id, username, password_hash, role, created_at)`，`role` 为 `ops` 或 `dev`；seed 至少各一个演示账号（密码仅存哈希，明文写在 README/`.env.example` 说明里）。
- 日志表：`agent_logs(id, session_id, user_id, event_type, content_json, created_at)`（`event_type` 含 `user_input`/`thought`/`tool_call`/`tool_result`/`final`/`error`/`cancelled`）。

- [ ] **Step 1:** 编写 schema + seed；README 给出导入命令。
- [ ] **Step 2:** `run_mysql_query` 在防护通过后执行并返回 JSON/表格字符串；失败信息可读。
- [ ] **Step 3:** 若环境无 MySQL，允许 `USE_MOCK_DB=true` 时用内存假数据响应验收 SQL（须在 README 写明）；但代码路径仍保留真实 MySQL。
- [ ] **Step 4:** Commit: `feat: add MySQL schema, seed, and query tool`

---

## Task 5: Tavily 搜索与文件读写工具

**Files:**
- Create: `app/tools/search.py`, `app/tools/file_io.py`, `app/tools/registry.py`

**Interfaces:**
- `tavily_search(query: str) -> str`
- `write_report(filename: str, content: str) -> str`（仅允许 `reports/` 下、禁止路径穿越）
- `read_report(filename: str) -> str`
- `get_all_tools() -> list`

- [ ] **Step 1:** Tavily 用官方/LangChain `TavilySearchResults`；无 key 时工具返回明确配置错误（测试可 mock）。
- [ ] **Step 2:** 文件工具规范化路径，拒绝 `..` 与绝对路径。
- [ ] **Step 3:** `registry.py` 汇总全部 `@tool`；并加入 `enterprise_knowledge_search`（见「与第 3 部分接口预留」：默认 Stub，`KB_ENABLED` 可切 HTTP client）。
- [ ] **Step 4:** 单测 Stub/HTTP mock。
- [ ] **Step 5:** Commit: `feat: add search, file IO, KB stub tools and registry`

---

## Task 6: LangGraph 状态图（核心）

**Files:**
- Create: `app/agent/state.py`, `app/agent/prompts.py`, `app/agent/nodes.py`, `app/agent/graph.py`, `tests/test_graph_limits.py`

**Interfaces:**
- `AgentState` 至少含：`messages`, `session_id`, `tool_round: int`, `status: str`（`running|completed|failed|cancelled|timeout|max_rounds`）, `events: list[dict]`（供 API/前端）
- `build_graph() -> compiled graph`（checkpointer=`MemorySaver()`）
- 运行时 config：`{"configurable": {"thread_id": session_id}}`
- 每轮工具调用前：`tool_round += 1`；若 `> MAX_TOOL_ROUNDS` → 结束并提示
- 工具调用包装：失败重试 1 次；仍失败则 `status=failed` 并停止
- 整体 `asyncio.wait_for(..., timeout=TASK_TIMEOUT_S)` 或等价超时

- [ ] **Step 1:** 实现 StateGraph：`agent`（LLM+tool decision）⇄ `tools` → 条件边判断继续/结束。
- [ ] **Step 2:** 封装 `get_llm()`：按 `LLM_PROVIDER` 构造 Chat 模型（DeepSeek 走 OpenAI 兼容 base_url；openai 演示走 GPT-4o-mini；qwen 走对应配置）。系统提示要求：多步骤任务规划；最终产出完整 Markdown 周报；需要数据时调用工具；不要捏造销售数字。
- [ ] **Step 3:** 测试：人为把 `MAX_TOOL_ROUNDS` 设为 0 或 mock 工具循环时，图会停并带 `max_rounds` 状态。
- [ ] **Step 4:** 测试：工具连续失败两次后停止。
- [ ] **Step 5:** Commit: `feat: implement LangGraph agent with round limit and retries`

---

## Task 7: 日志服务

**Files:**
- Create: `app/logging_service.py`
- Modify: graph/nodes 在关键事件点写日志

**Produces:**
- `log_event(session_id, event_type, payload: dict) -> None`
- `list_events(session_id) -> list`
- `list_recent(limit=100) -> list`（开发页）

- [ ] **Step 1:** 持久化到 `agent_logs`；无 DB 时降级为进程内列表（开发模式）但仍实现同一接口。
- [ ] **Step 2:** 在用户输入、每次思考摘要、工具名/入参、工具返回、最终结果、错误、取消时写日志。
- [ ] **Step 3:** Commit: `feat: persist agent execution logs`

---

## Task 8: FastAPI —— 对话、事件流、取消

**Files:**
- Create: `app/main.py`, `app/api/chat.py`, `app/api/logs.py`, `tests/test_api_cancel.py`

**API（必须实现）：**
- `POST /api/sessions` → `{ "session_id": "..." }`
- `POST /api/sessions/{session_id}/messages` body: `{ "content": "..." }` → 启动 Agent（后台任务）
- `GET /api/sessions/{session_id}/events` → 返回已产生事件列表；或 `SSE /api/sessions/{session_id}/stream` 推送（二选一，优先 SSE 或轮询，须能支撑前端时间线）
- `POST /api/sessions/{session_id}/cancel` → 合作式取消（设置 cancel flag，图侧检查后 `status=cancelled`）
- `GET /api/logs?session_id=&limit=` → 开发维护日志

**事件 JSON 形状（固定，前后端约定）：**
```json
{
  "type": "thought|tool_call|tool_result|final|error|cancelled|max_rounds|timeout",
  "timestamp": "ISO-8601",
  "content": "文本或摘要",
  "tool": "可选工具名",
  "input": "可选入参",
  "output": "可选返回"
}
```

- [ ] **Step 1:** 实现路由与进程内 `session -> cancel_flag/task` 注册表；chat 相关接口必须登录；logs 接口必须 `dev` 角色；会话关联 `user_id`。
- [ ] **Step 2:** 超时与 max rounds 映射到对应事件类型。
- [ ] **Step 3:** API 取消测试：启动后立刻 cancel，最终状态为 cancelled。
- [ ] **Step 4:** Commit: `feat: add FastAPI session, events, cancel, logs APIs`

---

## Task 9: 前端过程可视化（含登录页）

**Files:**
- Create: `web/index.html`（可含内联 CSS/JS）；可选 `web/logs.html`
- Modify: `README.md` 启动说明；可用 FastAPI `StaticFiles` 挂载 `/`

**UI 要求：**
- 登录页：用户名密码登录，保存 token
- 输入框发送自然语言任务（请求带 Authorization）
- 时间线展示：思考 → 调用哪个工具 → 入参 → 工具返回 → 最终 Markdown（可渲染）
- 取消按钮
- 简单日志页或 Tab（仅 dev 可见或进入时报错提示）

- [ ] **Step 1:** 实现登录页 + 对话页，对接上述 API。
- [ ] **Step 2:** 用浏览器或手动说明验证事件顺序可见。
- [ ] **Step 3:** Commit: `feat: add web UI for agent trace visualization`

---

## Task 10: 端到端验收与文档收尾

**Files:**
- Modify: `README.md`
- Create: `scripts/acceptance_check.md` 或 README 中的验收章节

**验收步骤（执行者必须实际跑或给出可复现记录）：**

1. 启动服务。
2. 输入：`帮我搜索2026AI行业新闻，再查询本月销售总额，计算同比增长率，生成一份运营周报markdown`
3. 确认自动调用：搜索、数据库、计算器（文件写入可选但建议写入 `reports/`）。
4. 输出完整 Markdown 周报。
5. 模拟工具异常：确认错误信息返回且不无限循环。
6. 页面可见每一步思考与工具参数。
7. `pytest` 全绿。

- [ ] **Step 1:** 跑通验收；修复缺口。
- [ ] **Step 2:** README 补充架构简图、环境变量、常见问题（Tavily/MySQL/LLM）。
- [ ] **Step 3:** Commit: `docs: acceptance notes and finalize README`

---

## 实现顺序与依赖

```text
Task1 脚手架（含 GitHub remote）
  → Task2 登录与鉴权
  → Task3 本地工具+SQL防护
  → Task4 MySQL（含 users/sales/logs）
  → Task5 搜索+文件+registry
  → Task6 LangGraph 核心（默认 DeepSeek）
  → Task7 日志
  → Task8 FastAPI（挂鉴权）
  → Task9 前端（含登录页）
  → Task10 验收；汇报完成；等待用户开 VPN 后再 push
```

不可并行打乱：Task6 依赖 Task3–5；Task8 依赖 Task2、Task6–7；Task9 依赖 Task8。Task4 与 Task2 都动 schema 时，合并迁移并保证 users 表存在。

---


## 与第 3 部分（RAG 知识库）的接口预留

> 约束：第 4 部分**独立可验收**，不硬依赖第 3 部分线上服务。仅预留稳定接口与占位实现，便于日后对接。

**假设的协作方向（当前可见的 3 号能力）：**
- 3 号对外提供「自然语言提问 → 带引用答案」能力。
- 4 号 Agent 在写周报/查内部规范时，可选调用该能力，而不是用 Tavily 搜公网。

**4 号侧预留（必须实现）：**

1. 工具接口（Python Protocol / ABC），例如：
   - `query_enterprise_kb(question: str, top_k: int = 5) -> KnowledgeHit`
   - `KnowledgeHit` 字段至少：`answer: str`, `citations: list[{doc_name, page, snippet}]`, `hit: bool`
2. 配置：`KB_ENABLED=false`（默认）、`KB_BASE_URL=`、`KB_API_KEY=`（可选）、`KB_TIMEOUT_S=3`
3. 两种实现，由配置切换：
   - `StubKnowledgeBaseClient`：`hit=False`，返回固定文案「当前未接入企业内部知识库」，**不编造**业务内容
   - `HttpKnowledgeBaseClient`：对 `KB_BASE_URL` 发 HTTP（建议约定 `POST /api/v1/qa`，body `{"question","session_id?"}`，响应含 answer/citations）；3 号路径名若不同，只改 client 映射
4. 在 `app/tools/registry.py` 注册 `@tool`：`enterprise_knowledge_search`；当 `KB_ENABLED=false` 时工具仍可调用但走 Stub，并在 tool 返回里标明 stub，避免 Agent 当成真实资料写入周报
5. OpenAPI / README「集成说明」一小节：列出请求/响应 JSON 示例、超时与失败语义（失败不重试进死循环；计为普通工具失败，适用「重试 1 次」规则）
6. **不要**实现 3 号的文档上传、向量库、Reranker；那些属于 3 号

**3 号侧建议（只写在 README，不替对方实现）：**
- 提供稳定 HTTP QA 接口与鉴权方式
- 无命中时返回明确 `hit=false`（或与 3 号兜底话术一致），便于 4 号原样转述

**验收影响：**
- 默认 `KB_ENABLED=false` 时，原有验收用例（Tavily + MySQL + 计算器 + 周报）必须仍通过
- 另加单测：Stub 不编造；`KB_ENABLED=true` 时用 `httpx` mock 验证 client 解析 citations


## 明确不做（本阶段）

- OAuth / SSO / 复杂细粒度 RBAC（仅 `ops` / `dev` 两角色）
- 生产级 K8s 部署与多副本 MemorySaver 外置（可在 README 记为后续：Postgres checkpointer）
- 真实企业数据仓库对接（用 seed/mock 即可交验收）
- 实现第 3 部分 RAG 本体（向量库/解析/前端）；仅保留上述 KB 客户端接口与 Stub
- 移动端原生 App

---

## Spec 覆盖自检

| 需求 | 对应 Task |
| :--- | :--- |
| 登录与 ops/dev 角色 | Task2, Task8, Task9 |
| 默认 DeepSeek；GPT-4o-mini 演示 | Task1 config, Task6 `get_llm()` |
| 自然语言任务拆解与工具调用 | Task6 |
| session 隔离 MemorySaver | Task6, Task8 |
| 过程可视化 | Task8 事件 + Task9 |
| 最大 8 轮 | Task6 + config |
| Tavily/计算器/时间/MySQL/文件 | Task3–5 |
| Markdown 输出 | Task6 prompts + Task9 渲染 |
| 工具失败重试 1 次 | Task6 |
| 人工终止 | Task8 |
| 日志与 60 天策略 | Task7（保留字段；清理策略写 README 或简单脚本） |
| 30s 超时 | Task6/Task8 |
| SQL 高危拦截 | Task3 |
| 推送到指定 GitHub 仓库 | Task1 配置 remote + 本地 commits；**仅在用户确认后**由执行者或用户 push |
| 验收用例 | Task10 |
| 第 3 部分 KB 接口预留（默认 Stub） | Task4/5 registry + 单测；README 集成说明 |

---

## 给 Cursor Agent 的执行指令（摘要）

1. 严格按 Task 1→10 顺序把**整体代码写完**；每 Task 结束跑相关测试并做本地 git commit。**全程不要 `git push`**，直到用户明确说 VPN 已开、可以推送。
2. 不要跳过登录鉴权、SQL 防护与 max-round 测试；Task10 尽量跑通验收路径（外部 API 可用 mock）。
3. 默认 LLM 为 DeepSeek；GPT-4o-mini 仅作演示切换。密钥仅 `.env`；提交 `.env.example` 占位符。
4. 若缺外部服务：MySQL 可用 mock 开关；Tavily/DeepSeek 必须在 README 标明必填项，测试用 mock。
5. **全部完成后先向用户汇报「代码与测试已结束，尚未推送」**，列出：如何启动、默认账号、验收/测试结果摘要、剩余风险、待 push 的分支与 commit 概况。等用户确认后再执行 `git push` 到 `https://github.com/MirroR0102/Enterprise-Automation-Agent`。
