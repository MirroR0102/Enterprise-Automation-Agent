# 企业业务流程自动化 Agent

面向运营人员的有状态 Agent：接收自然语言复杂任务，用 **LangGraph StateGraph** 拆解并调用工具（Tavily 搜索、计算器、时间、只读 MySQL、本地 Markdown 读写），最多 8 轮工具调用，经 FastAPI 提供登录、会话隔离与执行过程可视化，最终输出 Markdown 周报。

仓库：https://github.com/MirroR0102/Enterprise-Automation-Agent

智能体请读 [`AGENT.md`](AGENT.md)，不要把本文件当操作手册。

## 架构

```text
浏览器 (login / 左侧能力栏工作台 / 开发日志)
    → FastAPI (JWT)
        → 会话运行时 + 取消标志（终态后不可再标 cancelled）
        → LangGraph StateGraph + MemorySaver(thread_id=session_id)
            agent ⇄ tools → finalize
        → 工具：web_search / calculator / current_time / mysql_query /
                 write_markdown_report / read_markdown_report /
                 enterprise_knowledge_search（默认 Stub）
        → SQLite mock 或 MySQL（users / sales / agent_logs）
```

工作台为浅色双栏：左「运营周报 Agent / 知识库问答（第 3 部分占位）」+ 左下角昵称/登录名；右为主区。周报页底部输入；执行过程优先全宽，出 Markdown 后右侧分屏预览。顶栏有「过往周报」「新开对话」。同会话可追问（MemorySaver）；仅「新开对话」重置 session。成功周报写入每用户分库（MySQL `eoa_u_{id}` 或 mock `data/users/u_{id}.db`）。

## 环境要求

- Python 3.11+
- 默认不需要本机 MySQL（`USE_MOCK_DB=true`）
- 真实对话需要 `DEEPSEEK_API_KEY`；联网搜索需要 `TAVILY_API_KEY`

## 启动

本机推荐用 Anaconda 的 Python 3.13.9：`D:\anaconda\python.exe`。

```powershell
cd <本项目目录>
D:\anaconda\python.exe -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env
# 编辑 .env：填 DEEPSEEK_API_KEY；搜索再填 TAVILY_API_KEY
.\.venv\Scripts\python.exe scripts\init_db.py
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

打开 http://127.0.0.1:8000 （未登录跳转登录页）。API 文档：http://127.0.0.1:8000/docs

### 演示账号

| 用户名 | 密码 | 角色 |
| --- | --- | --- |
| `ops` | `ops123` | 运营：对话、看自己的执行过程 |
| `dev` | `dev123` | 开发：另外可看 `/logs.html` 与 `GET /api/logs` |

密码只作本地演示，库中存 PBKDF2 哈希。

### LLM 切换

| `LLM_PROVIDER` | 需要的变量 | 默认模型 |
| --- | --- | --- |
| `deepseek`（默认） | `DEEPSEEK_API_KEY`，`DEEPSEEK_BASE_URL` | `deepseek-chat` |
| `openai`（演示） | `OPENAI_API_KEY` | `gpt-4o-mini` |
| `qwen`（预留） | `QWEN_API_KEY`，`QWEN_BASE_URL` | `Qwen2-72B-Instruct` |

密钥只放 `.env`，不要提交。

### MySQL

- 无 MySQL：保持 `USE_MOCK_DB=true`，数据在 `data/mock.db`（已 gitignore）
- 有 MySQL：`USE_MOCK_DB=false`，设置 `MYSQL_DSN=mysql://user:pass@host:3306/enterprise_ops`，再运行 `scripts/init_db.py`。亦可手工执行 `app/db/schema.sql` 与 `app/db/seed.sql`（用户哈希仍建议用 init 脚本写入）

种子销售：2026-09 合计 100000，2025-09 合计 80000，同比 25%。

## 验收句

登录后发送：

`帮我搜索2026AI行业新闻，再查询本月销售总额，计算同比增长率，生成一份运营周报markdown`

期望自动调用搜索、数据库、计算器（建议再写入 `reports/`），并给出完整 Markdown。逐步时间线可见思考、工具名、入参、返回。详见 `scripts/acceptance_check.md`。

真实 LLM + 搜索可能超过默认 `TASK_TIMEOUT_S=30`，可按环境加大。

## 测试

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

单测用 mock DB，不打真实 DeepSeek / Tavily / MySQL。

## 主要 API

均需登录（`Authorization: Bearer <token>`），除登录本身。

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/api/auth/login` | `{username,password}` → `{access_token,token_type,role,username}` |
| GET | `/api/auth/me` | 当前用户 |
| POST | `/api/sessions` | 创建会话 → `{session_id}` |
| POST | `/api/sessions/{id}/messages` | `{content}` 后台启动 Agent |
| GET | `/api/sessions/{id}/events` | 事件列表（前端时间线轮询） |
| GET | `/api/sessions/{id}/stream` | SSE |
| POST | `/api/sessions/{id}/cancel` | 合作式取消（仅 running；已完成/已有 final 时保持原终态，`ok:false`） |
| GET | `/api/reports` | 当前用户过往周报列表（每用户分库） |
| GET | `/api/reports/{id}` | 单份周报 Markdown |
| GET | `/api/logs?session_id=&limit=` | **仅 dev** |
| GET | `/api/health` | 存活 |

事件 JSON：

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

硬限制：最多 **8** 轮工具；工具失败 **重试 1 次** 仍失败则停止；任务 **30 秒**超时（可配）；SQL 只允许单条 SELECT，拦截 drop/alter/delete/truncate/insert/update/create/grant/revoke。

## 日志保留

`agent_logs` 带 `created_at`，默认保留 60 天。可定期执行：

```powershell
.\.venv\Scripts\python.exe scripts\purge_logs.py
```

## 第 3 部分知识库对接（预留）

默认 `KB_ENABLED=false`，工具 `enterprise_knowledge_search` 走 Stub：`hit=false`，文案「当前未接入企业内部知识库」，**不编造**业务内容。验收句不依赖知识库。

启用时：

- `KB_ENABLED=true`
- `KB_BASE_URL`（客户端 POST `{KB_BASE_URL}/api/v1/qa`）
- 可选 `KB_API_KEY`（Bearer）
- `KB_TIMEOUT_S=3`

请求：

```json
{ "question": "差旅标准", "top_k": 5, "session_id": "可选" }
```

响应建议：

```json
{
  "answer": "...",
  "hit": true,
  "citations": [{ "doc_name": "制度.pdf", "page": 3, "snippet": "..." }]
}
```

失败按普通工具失败处理（再试 1 次），不要在 3 号服务里实现文档上传/向量库（那是 3 号的范围）。3 号侧请提供稳定 HTTP QA 与明确 `hit=false`。

## 目录

```text
app/           FastAPI + LangGraph + 工具 + DB
web/           登录 / 能力壳工作台（周报+知识库占位）/ 开发日志
reports/       Agent 可写的 Markdown
tests/         pytest
scripts/       init_db / purge_logs / 验收说明 / build_presentation.py
docs/superpowers/plans/  实现规划（与根目录同名稿一致）
docs/presentation/       30 分钟汇报 PPTX + 演讲稿 PDF（本地，不 push）
2026-09-15-enterprise-ops-agent.md  根目录规划稿
2026-09-15-part4-30min-presentation-outline.md  汇报大纲规格
```

产品 brief 的 `.docx` 仅本地参考，已在 `.gitignore`，不会上传。

## 汇报材料（本地，不推送）

| 文件 | 路径 |
| --- | --- |
| PPT（22 页，少字多图，v2） | `docs/presentation/第4部分-企业业务流程自动化Agent-汇报.pptx` |
| 演讲稿 PDF（≈30′） | `docs/presentation/第4部分-企业业务流程自动化Agent-演讲稿.pdf` |
| 报告执行说明 PDF | `docs/presentation/第4部分-企业业务流程自动化Agent-报告执行说明.pdf` |
| 报告执行说明（md 源） | `docs/presentation/第4部分-企业业务流程自动化Agent-报告执行说明.md` |
| 大纲 | `2026-09-15-part4-30min-presentation-outline.md` |
| 清单（含 P0–P4） | `2026-09-16-ui-interaction-revision.md` |
| 生成脚本 | `scripts/build_presentation.py` |

重新生成三件套：

```powershell
.\.venv\Scripts\python.exe scripts\build_presentation.py
```

**维护约定：** 项目仍在迭代。每当架构、验收口径、安全止损、演示账号/验收句、第 3 部分接口、联调问题结论等有重要改动，请同步更新上述 PPTX 与 PDF（或改脚本后重跑），并视需要改大纲。每次修改须先在 `AGENT.md`「已完成」区留痕（日期 · 改了什么 · 涉及文件），更新 PPT / 讲稿时直接对照该记录逐条同步。`.pptx`/`.pdf` 已 gitignore，**不要 push**。范本目录 `reference-contract-ai/` 仅本地参考，亦不推送。

## 联调问题记录（项目报告素材）

> 记录真实验收中踩过的坑，便于写报告「问题与解决」。

### 2026-09-16：成功出周报后状态误显示 cancelled

| 项 | 内容 |
| --- | --- |
| 现象 | 右侧已有完整周报，顶部状态仍为 `cancelled` |
| 根因 | 任务已完成后仍可点取消；`cancel_session` 无条件把 status 写成 cancelled；与 final 事件并存 |
| 修复 | 终态（completed/failed/timeout/max_rounds）或已有 `final` 事件时拒绝覆盖；前端中文状态芯片 + 终态禁用取消 |
| 结论 | 取消只作用于真正进行中的任务；已有报告视为成功 |

| 项 | 内容 |
| --- | --- |
| 场景 | 登录后发送验收句：搜索 2026 AI 新闻 → 查本月销售 → 算同比 → 生成 Markdown 周报 |
| 现象 | 时间线出现 `mysql_query` 后立刻 `error`：`工具连续失败两次，已停止：查询执行失败: no such column: order_date` |
| Agent 实际 SQL | `SELECT SUM(amount) AS total_sales FROM sales WHERE order_date >= DATE_FORMAT(CURDATE(), '%Y-%m-01')` |
| 正确表结构 | `sales(sale_date, amount, region)`（种子数据本月合计 100000，去年同月 80000） |
| 根因 1 | LLM 臆造列名 `order_date`，系统提示/工具说明未写明真实 schema |
| 根因 2 | `run_mysql_query` 对执行失败 `raise RuntimeError`，经 ToolNode 变成工具异常；图侧「失败重试 1 次仍失败则 `status=failed` 并停止」把**可纠正的 SQL 错误**当成致命失败，Agent 无法改 SQL 再查 |
| 次要风险 | mock 为 SQLite 时，`CURDATE()` / `DATE_FORMAT` 本身也不兼容，即便列名对了也可能再失败 |
| 修复 | （1）`SYSTEM_PROMPT` 与 `mysql_query` docstring 写明 `sale_date` 及字面量日期示例；（2）SQL 执行失败改为**返回错误字符串**（不抛异常），提示核对表结构后重试；（3）README/AGENT 同步口径 |
| 涉及文件 | `app/agent/prompts.py`、`app/tools/mysql_query.py`、`tests/test_mysql_query.py` |
| 结论（可写进报告） | 有状态 Agent 的「工具失败即停」适合真正的不可恢复故障；对 LLM 易写错的 SQL，应把校验/执行错误回传给模型做自纠，并用 schema 约束降低胡编列名概率 |

## 常见问题

- **侧栏一直「加载中」、点不开设置**：曾因 head 里同步拉 `marked` CDN 卡住导致整页脚本不跑；现改为 `defer`，整块用户区可点，本地缓存先显示昵称/登录名。硬刷新（Ctrl+F5）后再试。
- **Tavily 未配置**：工具返回明确错误，周报应写明未检索到公开新闻，而不是编造。
- **DeepSeek 401/超时**：检查 `DEEPSEEK_API_KEY`；任务超时固定 `TASK_TIMEOUT_S=30`（规划要求，勿擅自放宽）。
- **SQL 写错列名**：见上文「联调问题记录」；业务表是 `sales(sale_date, amount, region)`，不是 `order_date`。
- **MemorySaver 进程内记忆**：多副本/重启丢会话图状态；日志仍在 DB。后续可换 Postgres checkpointer。
- 远程仓库：https://github.com/MirroR0102/Enterprise-Automation-Agent

## 明确不做

OAuth/SSO、细粒度 RBAC、K8s、真实数仓、第 3 部分 RAG 本体、移动端 App。
