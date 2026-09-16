"""Generate Part-4 presentation PPTX and speech-script PDF (local only, not for git)."""

from __future__ import annotations

from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_AUTO_SHAPE_TYPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "presentation"
OUT.mkdir(parents=True, exist_ok=True)

PPTX_PATH = OUT / "第4部分-企业业务流程自动化Agent-汇报.pptx"
PDF_PATH = OUT / "第4部分-企业业务流程自动化Agent-演讲稿.pdf"

NAVY = RGBColor(0x1B, 0x2A, 0x4A)
ACCENT = RGBColor(0xC4, 0x8A, 0x1A)
INK = RGBColor(0x1E, 0x24, 0x30)
MUTED = RGBColor(0x4A, 0x55, 0x68)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT = RGBColor(0xF4, 0xF6, 0xFA)


def _set_run(run, size=18, bold=False, color=INK):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    run.font.name = "Microsoft YaHei"


def add_title_bar(slide, title: str):
    bar = slide.shapes.add_shape(
        MSO_AUTO_SHAPE_TYPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(0.9)
    )
    bar.fill.solid()
    bar.fill.fore_color.rgb = NAVY
    bar.line.fill.background()
    tf = bar.text_frame
    tf.clear()
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    run = p.add_run()
    run.text = "  " + title
    _set_run(run, size=24, bold=True, color=WHITE)


def add_bullets(slide, lines: list[str], top=1.2, left=0.7, width=12, size=18):
    box = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(5.8))
    tf = box.text_frame
    tf.word_wrap = True
    first = True
    for line in lines:
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.level = 0
        p.space_after = Pt(10)
        run = p.add_run()
        run.text = line
        _set_run(run, size=size, color=INK)


def blank_slide(prs):
    return prs.slides.add_slide(prs.slide_layouts[6])


def build_pptx() -> Path:
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    # A1 cover
    s = blank_slide(prs)
    bg = s.shapes.add_shape(
        MSO_AUTO_SHAPE_TYPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(7.5)
    )
    bg.fill.solid()
    bg.fill.fore_color.rgb = NAVY
    bg.line.fill.background()
    t = s.shapes.add_textbox(Inches(1), Inches(2.2), Inches(11), Inches(1.2))
    p = t.text_frame.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = "企业业务流程自动化 Agent"
    _set_run(r, size=36, bold=True, color=WHITE)
    st = s.shapes.add_textbox(Inches(1), Inches(3.5), Inches(11), Inches(1))
    p = st.text_frame.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = "第 4 部分 · 项目汇报（约 30 分钟）"
    _set_run(r, size=22, color=ACCENT)
    meta = s.shapes.add_textbox(Inches(1), Inches(5.2), Inches(11), Inches(1))
    p = meta.text_frame.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = "汇报人：________　　日期：________　　仓库：MirroR0102/Enterprise-Automation-Agent"
    _set_run(r, size=14, color=WHITE)

    # A2 agenda
    s = blank_slide(prs)
    add_title_bar(s, "A2 · 今天要讲什么（30 分钟）")
    add_bullets(
        s,
        [
            "A 开场与问题（3'）→ B 目标与范围（3'）→ C 总体架构（4'）",
            "D 核心机制：LangGraph / 工具 / 安全（5'）",
            "E 登录、可视化与可观测（3'）",
            "F 现场演示：验收原句（6'）——演示超时可压缩 D，不砍 F",
            "G 第 3 部分接口预留、测试与交付（3'）",
            "H 总结、风险、Q&A（3'）",
        ],
    )

    # A3 pain
    s = blank_slide(prs)
    add_title_bar(s, "A3 · 运营同学的真实痛点")
    add_bullets(
        s,
        [
            "查指标、搜行业动态、算同比、写周报——步骤碎、脚本不灵活",
            "自然语言需求多变，固定脚本覆盖不了",
            "期望：说一句话 → Agent 规划并调用工具 → Markdown 周报",
            "过程可看、可停；数字来自工具，不靠模型瞎编",
        ],
    )

    # B1 goals
    s = blank_slide(prs)
    add_title_bar(s, "B1 · 业务目标")
    add_bullets(
        s,
        [
            "周报类工作量目标：减少约 50%（需求目标，非已测 KPI）",
            "Agent 自主完成最多 8 步链式工具调用",
            "展示思考与工具调用全过程，便于排错",
            "输出完整 Markdown 运营周报",
            "前端：浅色能力壳（周报主区 + 知识库占位）；状态中文芯片；完成后不可误标取消",
        ],
    )

    # B2 position
    s = blank_slide(prs)
    add_title_bar(s, "B2 · 我们在大项目中的位置")
    add_bullets(
        s,
        [
            "本交付 = 第 4 部分：企业业务流程自动化 Agent",
            "第 3 部分 = 企业内部知识库问答（RAG）——本部分不实现向量库",
            "仅预留可选调用：enterprise_knowledge_search（默认 Stub）",
            "本部分独立可验收，不硬依赖第 3 部分上线",
        ],
    )

    # B3 scope
    s = blank_slide(prs)
    add_title_bar(s, "B3 · 范围边界（做 / 不做）")
    add_bullets(
        s,
        [
            "做：LangGraph StateGraph、工具集、FastAPI、JWT（ops/dev）、过程可视化、日志、KB Stub",
            "不做：OAuth/复杂 RBAC、生产 K8s、真实数仓对接、第 3 部分 RAG 本体",
            "当前：默认 USE_MOCK_DB（无 MySQL 也能演示）；TASK_TIMEOUT_S=30（规划固定）",
        ],
        size=17,
    )

    # C1 architecture
    s = blank_slide(prs)
    add_title_bar(s, "C1 · 架构总览")
    boxes = [
        (0.5, 1.3, 12.3, 0.9, "浏览器：login / 运营工作台 / 开发日志"),
        (0.5, 2.5, 12.3, 0.9, "FastAPI（JWT）→ 会话运行时 + 取消标志"),
        (0.5, 3.7, 12.3, 0.9, "LangGraph StateGraph + MemorySaver（thread_id = session_id）"),
        (0.5, 4.9, 12.3, 0.9, "agent ⇄ tools → finalize　｜　搜索 / 计算 / 时间 / SQL / 文件 / KB Stub"),
    ]
    for x, y, w, h, text in boxes:
        shp = s.shapes.add_shape(
            MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h)
        )
        shp.fill.solid()
        shp.fill.fore_color.rgb = LIGHT
        shp.line.color.rgb = NAVY
        tf = shp.text_frame
        tf.clear()
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        r = p.add_run()
        r.text = text
        _set_run(r, size=16, bold=True, color=NAVY)

    # C2 request path
    s = blank_slide(prs)
    add_title_bar(s, "C2 · 一次请求怎么走")
    add_bullets(
        s,
        [
            "登录拿 Token → 创建 session → 发送自然语言任务",
            "Agent 思考 → 选工具 → 结果写回 state → 未完成则继续",
            "达到完成条件 / 最大轮次 / 超时 / 取消 → 结束",
            "事件推到前端时间线；同时写入 agent_logs",
            "最终对用户可见：Markdown 周报",
        ],
    )

    # C3 stack
    s = blank_slide(prs)
    add_title_bar(s, "C3 · 技术选型一览")
    add_bullets(
        s,
        [
            "编排：LangGraph StateGraph（不是纯 AgentExecutor）",
            "后端：FastAPI + Uvicorn",
            "LLM：默认 DeepSeek；演示可切 GPT-4o-mini；预留 Qwen",
            "记忆：MemorySaver（thread_id = session_id）",
            "数据：MySQL 或本地 mock SQLite（USE_MOCK_DB=true）",
            "前端：静态页（登录 / 对话 / 日志）",
        ],
    )

    # D1 graph
    s = blank_slide(prs)
    add_title_bar(s, "D1 · LangGraph 状态图")
    add_bullets(
        s,
        [
            "节点：agent ⇄ tools → finalize / 结束",
            "状态关键字段：messages、tool_round、status、events、session_id",
            "为何用图：多步工具、会话隔离、轮次/取消/超时可控",
            "status 示例：running / completed / failed / cancelled / timeout / max_rounds",
        ],
    )

    # D2 tools
    s = blank_slide(prs)
    add_title_bar(s, "D2 · 内置工具箱")
    add_bullets(
        s,
        [
            "Tavily 搜索 —— 行业新闻 / 公开信息",
            "计算器 —— 同比等数学表达式（ast 白名单）",
            "时间 —— 当前日期时间",
            "MySQL/只读查询 —— 业务指标；列名 sale_date/amount/region",
            "文件读写 —— reports/ 下 Markdown（防路径穿越）",
            "enterprise_knowledge_search —— 接第 3 部分，默认 Stub",
        ],
        size=17,
    )

    # D3 safety
    s = blank_slide(prs)
    add_title_bar(s, "D3 · 安全与止损（评委爱问）")
    add_bullets(
        s,
        [
            "怕死循环 → 最大工具轮次 8",
            "怕挂太久 → 任务超时默认 30s（规划固定；演示长链路可临时调配置）",
            "怕外部抖动 → 工具失败重试 1 次，仍失败则停止并说明",
            "怕 SQL 误伤 → 仅 SELECT；黑名单 drop/alter/delete/…；禁多语句",
            "怕跑飞 → 人工取消；前端时间线可审计",
            "实践：SQL 错误回传自纠；任务已 completed / 已有 final 后忽略迟到取消",
        ],
        size=16,
    )

    # E1 roles
    s = blank_slide(prs)
    add_title_bar(s, "E1 · 角色与权限")
    add_bullets(
        s,
        [
            "ops：对话、查看自己的执行过程",
            "dev：额外可看全局日志页 / GET /api/logs",
            "JWT 登录；密码 PBKDF2 哈希存储",
            "演示账号：ops/ops123　｜　dev/dev123（仅演示环境）",
        ],
    )

    # E2 visualization
    s = blank_slide(prs)
    add_title_bar(s, "E2 · 过程可视化")
    add_bullets(
        s,
        [
            "时间线：思考 → 工具名 → 入参 → 返回 → 最终 Markdown",
            "对应需求：「方便排查错误」",
            "支持轮询事件列表 / SSE 流式",
        ],
    )

    # F1 demo script
    s = blank_slide(prs)
    add_title_bar(s, "F1 · 演示脚本（提词）")
    add_bullets(
        s,
        [
            "1. 打开 http://127.0.0.1:8000 ，用 ops 登录",
            "2. 粘贴验收句并发送",
            "3. 指时间线：搜索 → 查销售 → 计算器 →（可选）写 reports/",
            "4. 展示最终 Markdown（种子：本月 100000 / 去年同月 80000 → 同比 25%）",
            "5. 可选：dev 看日志；或取消按钮；或 KB Stub「未接入知识库」",
        ],
        size=17,
    )

    # F2 acceptance
    s = blank_slide(prs)
    add_title_bar(s, "F2 · 验收对照")
    add_bullets(
        s,
        [
            "验收句：帮我搜索2026AI行业新闻，再查询本月销售总额，计算同比增长率，生成一份运营周报markdown",
            "□ 自动调用搜索 / 数据库 / 计算器",
            "□ 输出完整 Markdown 周报，过程可见",
            "□ 异常不无限循环（轮次 / 超时 / 失败停止）",
            "□ pytest 单测覆盖 SQL 防护、鉴权、取消、轮次等",
        ],
        size=16,
    )

    # G1 KB
    s = blank_slide(prs)
    add_title_bar(s, "G1 · 与第 3 部分的衔接")
    add_bullets(
        s,
        [
            "工具名：enterprise_knowledge_search",
            "KB_ENABLED=false → Stub，hit=false，不编造业务内容",
            "日后 KB_ENABLED=true + KB_BASE_URL → HTTP 调第 3 部分 QA API",
            "4 号主验收路径默认不依赖 3 号",
        ],
    )

    # G2 quality + deliverables combined to keep page count
    s = blank_slide(prs)
    add_title_bar(s, "G2 · 质量保障与交付")
    add_bullets(
        s,
        [
            "pytest：SQL 防护、计算器、鉴权、取消、图轮次、KB Stub…",
            "文档：README（人）/ AGENT.md（智能体）/ acceptance_check.md",
            "交付：可运行代码、测试、演示账号、规划文档、本汇报材料（本地）",
            "仓库：https://github.com/MirroR0102/Enterprise-Automation-Agent",
        ],
    )

    # H1 summary
    s = blank_slide(prs)
    add_title_bar(s, "H1 · 一句话总结")
    add_bullets(
        s,
        [
            "交付了一个可登录、可观测、带止损的 LangGraph 运营 Agent：",
            "自然语言完成「搜新闻 + 查数 + 计算 + 出周报」链式任务；",
            "并为第 3 部分知识库留了可开关接口（默认 Stub，独立验收）。",
        ],
        top=2.2,
        size=20,
    )

    # H2 risks
    s = blank_slide(prs)
    add_title_bar(s, "H2 · 风险与对策")
    add_bullets(
        s,
        [
            "工具循环 → 最大轮次 + 超时 + 取消",
            "SQL 注入/误删改 → 只读 + 黑名单；错误可回传自纠",
            "外部 API 不稳 → 重试 1 次；演示备用录屏",
            "长任务超 30s → 规划固定超时；优化提示减少空转（演示可临时调配置）",
            "第 3 部分联调延迟 → 默认 Stub，独立验收",
            "LLM 写错列名（联调实录）→ schema 写入提示词；见 README「联调问题记录」",
        ],
        size=16,
    )

    # H3 outlook + thanks
    s = blank_slide(prs)
    add_title_bar(s, "H3 · 展望")
    add_bullets(
        s,
        [
            "正式对接第 3 部分 KB HTTP",
            "Checkpointer 外置，支持多进程",
            "更细的周报模板与指标看板",
            "（项目仍在迭代：重要改动后同步更新本 PPT / 演讲稿）",
        ],
    )

    s = blank_slide(prs)
    bg = s.shapes.add_shape(
        MSO_AUTO_SHAPE_TYPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(7.5)
    )
    bg.fill.solid()
    bg.fill.fore_color.rgb = NAVY
    bg.line.fill.background()
    t = s.shapes.add_textbox(Inches(1), Inches(2.8), Inches(11), Inches(1.5))
    p = t.text_frame.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = "感谢聆听 · Q&A"
    _set_run(r, size=40, bold=True, color=WHITE)
    st = s.shapes.add_textbox(Inches(1), Inches(4.5), Inches(11), Inches(1))
    p = st.text_frame.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = "MirroR0102 / Enterprise-Automation-Agent"
    _set_run(r, size=16, color=ACCENT)

    prs.save(PPTX_PATH)
    return PPTX_PATH


def _register_font() -> str:
    candidates = [
        Path(r"C:\Windows\Fonts\msyh.ttc"),
        Path(r"C:\Windows\Fonts\msyh.ttf"),
        Path(r"C:\Windows\Fonts\simhei.ttf"),
        Path(r"C:\Windows\Fonts\simsun.ttc"),
    ]
    for path in candidates:
        if path.exists():
            name = "CNFont"
            try:
                pdfmetrics.registerFont(TTFont(name, str(path), subfontIndex=0))
            except Exception:
                pdfmetrics.registerFont(TTFont(name, str(path)))
            return name
    return "Helvetica"


def build_pdf() -> Path:
    font = _register_font()
    styles = getSampleStyleSheet()
    title = ParagraphStyle(
        "CNTitle",
        parent=styles["Title"],
        fontName=font,
        fontSize=18,
        leading=24,
        spaceAfter=12,
    )
    h1 = ParagraphStyle(
        "CNH1",
        parent=styles["Heading1"],
        fontName=font,
        fontSize=14,
        leading=20,
        spaceBefore=14,
        spaceAfter=8,
    )
    h2 = ParagraphStyle(
        "CNH2",
        parent=styles["Heading2"],
        fontName=font,
        fontSize=12,
        leading=16,
        spaceBefore=10,
        spaceAfter=6,
    )
    body = ParagraphStyle(
        "CNBody",
        parent=styles["Normal"],
        fontName=font,
        fontSize=10.5,
        leading=16,
        spaceAfter=6,
    )
    cue = ParagraphStyle(
        "CNCue",
        parent=body,
        fontName=font,
        fontSize=10.5,
        leading=16,
        spaceBefore=4,
        spaceAfter=8,
        textColor=HexColor("#8B1E1E"),
    )

    doc = SimpleDocTemplate(
        str(PDF_PATH),
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=1.8 * cm,
        bottomMargin=1.8 * cm,
    )
    story: list = []

    def P(text: str, style=body):
        story.append(Paragraph(text.replace("\n", "<br/>"), style))

    def B(text: str):
        P(f"<b>{text}</b>", cue)

    P("第 4 部分 · 企业业务流程自动化 Agent · 演讲稿（口语完整稿）", title)
    P("总时长约 30 分钟（含演示与简短问答）。依据 README / AGENT / 规划文档；不编造未实现能力。", body)
    P("汇报人：________　　日期：________　　仓库：MirroR0102/Enterprise-Automation-Agent", body)
    P("说明：项目仍在迭代。重要功能/验收口径变更后，请同步更新本 PDF 与同目录 PPT（本地文件，不推送 GitHub）。", body)

    P("段 A · 开场与问题（建议 3 分钟）", h1)
    P(
        "各位老师、同学好。今天汇报的是大项目里的第 4 部分——企业业务流程自动化 Agent。"
        "先讲一个运营同学每天都会遇到的场景：要交周报，得去搜行业新闻、查本月销售额、算同比增长率，再拼成 Markdown。"
        "步骤碎、脚本一变需求就废。我们希望他只说一句话，系统自己规划步骤、调用工具，把周报写出来，"
        "而且每一步思考和工具入参都能看见、任务还能人工停掉。这就是有状态 Agent 加工具编排要解决的问题。",
        body,
    )

    P("段 B · 目标与范围（建议 3 分钟）", h1)
    P(
        "业务目标来自需求：周报类工作量希望减少大约一半——这是目标表述，不是我们已经测出来的 KPI。"
        "技术上，Agent 最多自主走 8 轮工具调用，并把全过程展示出来便于排错。"
        "在大项目里，第 3 部分是企业内部知识库 RAG；我们第 4 部分不实现向量库，只预留 enterprise_knowledge_search。"
        "默认 KB_ENABLED 关掉，走 Stub，所以第 4 部分可以独立验收，不会被第 3 部分拖住。"
        "范围上：做 LangGraph、工具集、FastAPI、登录角色、可视化、日志；不做 OAuth、复杂 RBAC、K8s、真实数仓和 RAG 本体。"
        "当前演示环境可以不接 MySQL，用 mock SQLite；任务超时按规划默认 30 秒。",
        body,
    )

    P("段 C · 总体架构（建议 4 分钟）", h1)
    P(
        "请看架构图：最上面是浏览器三个页面——登录、运营工作台、开发日志。"
        "请求进 FastAPI，先过 JWT。再进会话运行时，带取消标志。"
        "核心是 LangGraph 的 StateGraph，记忆用 MemorySaver，thread_id 就等于 session_id，保证会话隔离。"
        "图里 agent 节点负责想和选工具，tools 节点执行，最后 finalize 收束成 Markdown。"
        "底下挂搜索、计算器、时间、只读库查询、文件读写，以及知识库 Stub。"
        "一次请求就是：登录拿 Token，建 session，发自然语言；事件一边推时间线一边落日志。"
        "技术选型一句话：编排 LangGraph，后端 FastAPI，默认 LLM 是 DeepSeek，演示可切 GPT-4o-mini，还预留了 Qwen。",
        body,
    )

    P("段 D · 核心机制（建议 5 分钟）", h1)
    P(
        "为什么用图而不是一次 Prompt？因为要多步工具、要分支结束、要控轮次和取消。"
        "工具箱里：Tavily 搜公开新闻；计算器算同比；时间打时间戳；SQL 查销售但只读；"
        "文件工具只允许写在 reports 目录；知识库工具默认 Stub。"
        "安全用「怕什么就挡什么」来说：怕死循环就卡 8 轮；怕挂太久就 30 秒超时；"
        "怕外网抖就失败重试一次，还失败就停并说明；怕 SQL 误伤就只允许 SELECT 加黑名单；"
        "怕跑飞就给人取消按钮。补充一句联调经验：模型曾经把 sale_date 写成 order_date，"
        "如果把执行失败直接当致命错误，整条任务会当场终止；我们改成把错误文案返回给 Agent，"
        "并在提示词里写清表结构，方便它改 SQL 再查——细节写在 README 的联调问题记录里，写报告可以直接引用。",
        body,
    )

    P("段 E · 登录、可视化与可观测（建议 3 分钟）", h1)
    P(
        "角色很简单：ops 负责对话和看自己的过程；dev 还能看全局日志。"
        "密码哈希存储，登录发 JWT。前端时间线按思考、工具名、入参、返回、最终 Markdown 排列，"
        "正好对应需求里的「方便排查错误」。日志带时间戳，保留策略按 60 天，仓库里有清理脚本说明。"
        "时间紧的话，日志这一页可以口头带过，把细节留到演示里看。",
        body,
    )

    P("段 F · 现场演示（建议 6 分钟）", h1)
    P("下面进入演示。若现场卡顿，按备用计划切录屏或已有 reports 文件，不要空等。", body)
    B("演示口令：「下面用验收原句跑一遍，请看右侧或下方时间线。」")
    P(
        "操作顺序：打开本机 8000 端口页面，用 ops 加密码 ops123 登录；"
        "粘贴验收句——帮我搜索2026AI行业新闻，再查询本月销售总额，计算同比增长率，生成一份运营周报markdown——发送。",
        body,
    )
    B("演示口令：「这里调用了数据库而不是编造销售额。」")
    B("演示口令：「同比用计算器得出 25%，与种子数据一致——本月 100000，去年同月 80000。」")
    P(
        "可选 30 秒：用 dev 看日志页，或点一次取消，或提一句 KB Stub 返回「当前未接入企业内部知识库」。"
        "对照验收：多工具自动调用、完整周报、过程可见、异常不无限循环。",
        body,
    )
    P(
        "备用计划：外网或 Tavily 失败时，说明可用事先录屏，并展示已生成的 reports 与 pytest 结果；"
        "若 LLM 超时，说明演示环境可临时调大 TASK_TIMEOUT_S，或直接切录屏——正式口径仍以规划 30 秒为准。",
        body,
    )

    P("段 G · 接口预留、测试与交付（建议 3 分钟）", h1)
    P(
        "和第 3 部分的衔接：工具 enterprise_knowledge_search；关开关走 Stub 不编造；"
        "开开关加 KB_BASE_URL 就 HTTP 调对方问答接口。主验收不依赖 3 号上线。"
        "质量上我们有 pytest 覆盖 SQL 防护、计算器、鉴权、取消、轮次上限、KB Stub 等；"
        "人读 README，智能体读 AGENT.md。交付物包括可运行代码、测试、演示账号、规划文档，"
        "以及本汇报 PPT 与演讲稿——后两份只在本地 docs/presentation，不进 GitHub 推送。",
        body,
    )

    P("段 H · 总结、风险、Q&A（建议 3 分钟）", h1)
    P(
        "一句话总结：我们交付了一个可登录、可观测、带止损的 LangGraph 运营 Agent，"
        "能用自然语言完成搜新闻、查数、计算、出周报的链式任务，并为第 3 部分知识库留了可开关接口。"
        "风险上：循环靠轮次超时取消；SQL 靠只读黑名单；外网靠有限重试和录屏备份；"
        "第 3 部分联调晚也不堵交付。展望三件：正式接 KB HTTP、Checkpointer 外置、周报模板更细。"
        "我的汇报到这里，谢谢大家，欢迎提问。",
        body,
    )

    P("附录 · 评委可能提问（预备答，不必上 PPT）", h1)
    P(
        "1. 为什么用 LangGraph 而不是纯 Prompt？——多步工具、状态、分支结束、会话记忆与轮次控制更清晰。<br/>"
        "2. 如何防止胡编销售额？——强制工具查库；提示词禁止捏造；过程可视化可审计。<br/>"
        "3. 和 ChatGPT 插件有何不同？——私有链路、业务库只读防护、会话与日志、角色权限、与第 3 部分预留集成。<br/>"
        "4. 30 秒不够用怎么办？——超时配置；演示可录屏；工具失败有限重试。<br/>"
        "5. 第 3 部分没好能不能交？——能；KB 默认 Stub，主验收不依赖。<br/>"
        "6. 联调时 SQL 写错列名怎么办？——提示词写清 schema；执行错误返回给模型自纠；见 README 联调问题记录。",
        body,
    )

    P("维护约定", h2)
    P(
        "每当项目出现重要改动（架构、验收口径、安全止损、演示账号、与第 3 部分接口、已知问题结论等），"
        "应同步修订：① 本 PDF；② 同目录 PPT；③ 大纲 "
        "2026-09-15-part4-30min-presentation-outline.md（如结构变化）；④ README / AGENT 中的演示材料说明。"
        "PPT/PDF 已 gitignore，默认不 push。",
        body,
    )

    doc.build(story)
    return PDF_PATH


if __name__ == "__main__":
    pptx = build_pptx()
    pdf = build_pdf()
    print(f"PPTX: {pptx}")
    print(f"PDF:  {pdf}")
    print(f"slides: check manually")
