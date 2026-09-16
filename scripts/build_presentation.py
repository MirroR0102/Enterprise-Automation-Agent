# -*- coding: utf-8 -*-
r"""第 4 部分汇报三件套生成器（本地材料，不进 git 远端的二进制默认为 gitignore）。

生成：
1) docs/presentation/第4部分-企业业务流程自动化Agent-汇报.pptx   —— 22 页，少字多图
2) docs/presentation/第4部分-企业业务流程自动化Agent-演讲稿.pdf —— ≈30 分钟完整口语稿
3) docs/presentation/第4部分-企业业务流程自动化Agent-报告执行说明.md / .pdf

运行：.\.venv\Scripts\python.exe scripts\build_presentation.py
"""

from __future__ import annotations

from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "presentation"
OUT.mkdir(parents=True, exist_ok=True)

PPTX_PATH = OUT / "第4部分-企业业务流程自动化Agent-汇报.pptx"
SPEECH_PDF = OUT / "第4部分-企业业务流程自动化Agent-演讲稿.pdf"
RUNBOOK_MD = OUT / "第4部分-企业业务流程自动化Agent-报告执行说明.md"
RUNBOOK_PDF = OUT / "第4部分-企业业务流程自动化Agent-报告执行说明.pdf"

# ---------------------------------------------------------------- 调色板
INK = RGBColor(0x16, 0x22, 0x3A)
NAVY = RGBColor(0x1B, 0x2A, 0x4A)
BLUE = RGBColor(0x2E, 0x6B, 0xD6)
GOLD = RGBColor(0xB8, 0x82, 0x0E)
TEAL = RGBColor(0x0F, 0x76, 0x6E)
RED = RGBColor(0xB2, 0x3A, 0x48)
MUTED = RGBColor(0x5B, 0x68, 0x7D)
LIGHT = RGBColor(0xF2, 0xF5, 0xFA)
SOFT = RGBColor(0xE3, 0xEB, 0xF6)
WARM = RGBColor(0xFB, 0xF3, 0xE2)
GREEN = RGBColor(0xE8, 0xF5, 0xEF)
PINK = RGBColor(0xFB, 0xEB, 0xED)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
GREY_LINE = RGBColor(0xD8, 0xDF, 0xEA)
FONT = "Microsoft YaHei"
TOTAL = 22


# ---------------------------------------------------------------- 基础工具
def _style_run(run, size=12, bold=False, color=INK, italic=False, font=FONT):
    f = run.font
    f.size = Pt(size)
    f.bold = bold
    f.italic = italic
    f.color.rgb = color
    f.name = font
    rPr = run._r.get_or_add_rPr()
    latin = rPr.find(qn("a:latin"))
    ea = rPr.find(qn("a:ea"))
    if ea is None:
        ea = rPr.makeelement(qn("a:ea"), {})
        if latin is not None:
            latin.addnext(ea)
        else:
            rPr.append(ea)
    ea.set("typeface", font)


def P(*runs, align=PP_ALIGN.LEFT, sa=4, ls=1.0):
    return {"runs": list(runs), "align": align, "sa": sa, "ls": ls}


def T(text, size=12, bold=False, color=INK, italic=False):
    return (text, {"size": size, "bold": bold, "color": color, "italic": italic})


def _fill_paras(tf, paras):
    for i, pr in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = pr.get("align", PP_ALIGN.LEFT)
        p.space_after = Pt(pr.get("sa", 4))
        p.space_before = Pt(pr.get("sb", 0))
        p.line_spacing = pr.get("ls", 1.0)
        for text, opts in pr["runs"]:
            r = p.add_run()
            r.text = text
            _style_run(r, **opts)


def txt(s, x, y, w, h, paras, anchor=MSO_ANCHOR.TOP, wrap=True):
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = wrap
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Inches(0.02)
    tf.margin_top = tf.margin_bottom = Inches(0.01)
    _fill_paras(tf, paras)
    return tb


def card(s, x, y, w, h, paras, fill=LIGHT, line=None, radius=0.10,
         anchor=MSO_ANCHOR.MIDDLE, line_w=1.0):
    shp = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y),
                             Inches(w), Inches(h))
    try:
        shp.adjustments[0] = radius
    except Exception:
        pass
    try:
        shp.shadow.inherit = False
    except Exception:
        pass
    if fill is None:
        shp.fill.background()
    else:
        shp.fill.solid()
        shp.fill.fore_color.rgb = fill
    if line is None:
        shp.line.fill.background()
    else:
        shp.line.color.rgb = line
        shp.line.width = Pt(line_w)
    tf = shp.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Inches(0.09)
    tf.margin_top = tf.margin_bottom = Inches(0.045)
    _fill_paras(tf, paras)
    return shp


def rect(s, x, y, w, h, fill=LIGHT, line=None):
    shp = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y),
                             Inches(w), Inches(h))
    try:
        shp.shadow.inherit = False
    except Exception:
        pass
    if fill is None:
        shp.fill.background()
    else:
        shp.fill.solid()
        shp.fill.fore_color.rgb = fill
    if line is None:
        shp.line.fill.background()
    else:
        shp.line.color.rgb = line
        shp.line.width = Pt(0.75)
    return shp


def arrow_r(s, x, y, w=0.30, h=0.22, color=GOLD):
    shp = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(x), Inches(y),
                             Inches(w), Inches(h))
    shp.fill.solid()
    shp.fill.fore_color.rgb = color
    shp.line.fill.background()
    try:
        shp.shadow.inherit = False
    except Exception:
        pass
    return shp


def dot(s, x, y, d=0.12, color=BLUE):
    shp = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x), Inches(y),
                             Inches(d), Inches(d))
    shp.fill.solid()
    shp.fill.fore_color.rgb = color
    shp.line.fill.background()
    try:
        shp.shadow.inherit = False
    except Exception:
        pass
    return shp


def chip(s, x, y, w, h, text, fill=SOFT, line=None, color=INK, size=10.5,
         bold=True, radius=0.5):
    return card(s, x, y, w, h, [P(T(text, size=size, bold=bold, color=color),
                                   align=PP_ALIGN.CENTER, sa=0)],
                fill=fill, line=line, radius=radius)


def chevrons(s, x, y, total_w, h, steps, fill=SOFT, line=BLUE, size=11.5,
             first_fill=None, text_color=INK):
    n = len(steps)
    overlap = 0.16
    w = (total_w + overlap * (n - 1)) / n
    cx = x
    for i, step in enumerate(steps):
        shp_type = MSO_SHAPE.PENTAGON if i == 0 else MSO_SHAPE.CHEVRON
        shp = s.shapes.add_shape(shp_type, Inches(cx), Inches(y), Inches(w), Inches(h))
        try:
            shp.adjustments[0] = 0.30
        except Exception:
            pass
        try:
            shp.shadow.inherit = False
        except Exception:
            pass
        shp.fill.solid()
        shp.fill.fore_color.rgb = (first_fill or fill) if i == 0 else fill
        if line is None:
            shp.line.fill.background()
        else:
            shp.line.color.rgb = line
            shp.line.width = Pt(1.0)
        tf = shp.text_frame
        tf.word_wrap = True
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf.margin_left = Inches(0.24)
        tf.margin_right = Inches(0.06)
        tf.margin_top = tf.margin_bottom = Inches(0.02)
        _fill_paras(tf, [P(T(step, size=size, bold=True, color=text_color),
                           align=PP_ALIGN.CENTER, sa=0, ls=0.98)])
        cx += w - overlap


def _table(s, x, y, col_ws, rows, row_h=0.45, size=11.5, header_size=12.5):
    w = sum(col_ws)
    gf = s.shapes.add_table(len(rows), len(col_ws), Inches(x), Inches(y),
                            Inches(w), Inches(row_h * len(rows)))
    t = gf.table
    try:
        t.first_row = False
        t.horz_banding = False
    except Exception:
        pass
    try:
        tbl = t._tbl
        tblPr = tbl.tblPr
        sid = tblPr.find(qn("a:tableStyleId"))
        if sid is None:
            sid = tblPr.makeelement(qn("a:tableStyleId"), {})
            tblPr.append(sid)
        sid.text = "{2D5ABB26-0587-4C30-8999-92F81FD0307C}"
    except Exception:
        pass
    for i, cw in enumerate(col_ws):
        t.columns[i].width = Inches(cw)
    for ri, row in enumerate(rows):
        t.rows[ri].height = Inches(row_h)
        for ci, val in enumerate(row):
            cell = t.cell(ri, ci)
            cell.margin_left = Inches(0.08)
            cell.margin_right = Inches(0.06)
            cell.margin_top = cell.margin_bottom = Inches(0.02)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.fill.solid()
            if ri == 0:
                cell.fill.fore_color.rgb = NAVY
                runs = [T(val, size=header_size, bold=True, color=WHITE)]
            else:
                cell.fill.fore_color.rgb = WHITE if ri % 2 else LIGHT
                runs = [T(val, size=size, bold=False, color=INK)]
            _fill_paras(cell.text_frame, [P(*runs, sa=0, ls=0.98)])
    return t


def header(s, page, kicker, title):
    rect(s, 0, 0, 13.333, 0.07, fill=NAVY)
    rect(s, 0.55, 0.40, 0.085, 0.66, fill=GOLD)
    txt(s, 0.78, 0.30, 11.9, 0.30,
        [P(T(kicker, size=11.5, bold=True, color=GOLD), sa=0)])
    txt(s, 0.78, 0.55, 12.0, 0.62,
        [P(T(title, size=22, bold=True, color=INK), sa=0)])
    footer(s, page)


def footer(s, page):
    rect(s, 0.55, 7.04, 12.23, 0.012, fill=GREY_LINE)
    txt(s, 0.55, 7.09, 9.0, 0.3,
        [P(T("第 4 部分 · 企业业务流程自动化 Agent · 本地汇报材料（不推送）",
             size=9, color=MUTED), sa=0)])
    txt(s, 11.3, 7.06, 1.48, 0.3,
        [P(T(f"{page:02d} / {TOTAL}", size=10.5, bold=True, color=MUTED),
           align=PP_ALIGN.RIGHT, sa=0)])


def bullets_card(s, x, y, w, h, title, items, fill=LIGHT, line=None,
                 title_color=NAVY, size=13, title_size=15, gap=7):
    paras = [P(T(title, size=title_size, bold=True, color=title_color),
               align=PP_ALIGN.LEFT, sa=8)]
    for it in items:
        paras.append(P(T("· ", size=size, bold=True, color=GOLD),
                       T(it, size=size, color=INK), align=PP_ALIGN.LEFT, sa=gap))
    return card(s, x, y, w, h, paras, fill=fill, line=line,
                anchor=MSO_ANCHOR.MIDDLE)


# ================================================================ PPT
def build_pptx() -> Path:
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[6]

    def new():
        return prs.slides.add_slide(blank)

    # ---------------------------------------------------------- 01 封面
    s = new()
    rect(s, 0, 0, 13.333, 7.5, fill=NAVY)
    rect(s, 0.9, 1.72, 1.15, 0.06, fill=GOLD)
    txt(s, 0.9, 1.95, 11.5, 1.1,
        [P(T("企业业务流程自动化 Agent", size=40, bold=True, color=WHITE), sa=0)])
    txt(s, 0.9, 3.05, 11.5, 0.6,
        [P(T("第 4 部分 · 项目报告（约 30 分钟 · 含现场演示）",
             size=20, color=RGBColor(0xE8, 0xD9, 0xAD)), sa=0)])
    txt(s, 0.9, 3.72, 11.6, 0.5,
        [P(T("面向运营人员的有状态 Agent：一句自然语言 → 工具链自动编排 → 可审计的 Markdown 周报",
             size=14.5, color=RGBColor(0xC9, 0xD4, 0xE8)), sa=0)])
    strip = card(s, 0.9, 4.42, 11.55, 0.62,
                 [P(T("LangGraph StateGraph · 最多 8 轮工具 · DeepSeek（可切 GPT-4o-mini / Qwen） · FastAPI + JWT · MySQL / SQLite · 全链路可观测",
                      size=13, bold=False, color=RGBColor(0xE6, 0xEC, 0xF7)),
                    align=PP_ALIGN.CENTER, sa=0)],
                 fill=RGBColor(0x25, 0x3A, 0x66), line=RGBColor(0x3D, 0x55, 0x8C))
    txt(s, 0.9, 5.42, 11.5, 0.4,
        [P(T("汇报人：李刘钰祚　　（日期：____ 年 __ 月 __ 日）",
             size=14, color=WHITE), sa=0)])
    txt(s, 0.9, 5.95, 11.5, 0.4,
        [P(T("仓库：github.com/MirroR0102/Enterprise-Automation-Agent　·　本套材料：PPT / 演讲稿 / 执行说明（本地，不推送）",
             size=11.5, color=RGBColor(0xA9, 0xB6, 0xD0)), sa=0)])

    # ---------------------------------------------------------- 02 目录
    s = new()
    header(s, 2, "AGENDA · 30′ 时间轴", "今天讲什么：一圈走完“做、跑、改、守”")
    rows = [
        ("0–3′", "开场 · 运营痛点与目标", "为什么做：步骤碎、脚本僵、数字必须可信"),
        ("3–6′", "范围 · 第 3 ↔ 4 部分边界", "预留 enterprise_knowledge_search，独立验收"),
        ("6–11′", "架构 · 五层结构与任务全流程", "浏览器 → FastAPI → LangGraph → 工具 → 数据"),
        ("11–14′", "机制 · 工具箱与安全止损", "7 个工具 + 6 条防线 + 两个真实事故"),
        ("14–16′", "平台 · 登录、界面与可观测", "JWT / 时间线 / 日志 / 每用户分库"),
        ("16–23′", "演示 · 验收句全链路（7′）", "现场跑通：搜索 → 查库 → 计算 → 周报"),
        ("23–28′", "代码 · 关键模块地图（5′）", "评委问「在哪改」的参考答案"),
        ("28–30′", "收尾 · 测试、风险、总结、Q&A", "28 项测试 + 三条诚实边界"),
    ]
    y = 1.30
    for i, (tm, title, desc) in enumerate(rows):
        card(s, 0.55, y, 1.10, 0.56, [P(T(tm, size=13, bold=True, color=NAVY),
                                        align=PP_ALIGN.CENTER, sa=0)],
             fill=SOFT if i % 2 == 0 else LIGHT, anchor=MSO_ANCHOR.MIDDLE)
        card(s, 1.78, y, 4.30, 0.56, [P(T(title, size=13.5, bold=True, color=INK),
                                        align=PP_ALIGN.LEFT, sa=0)], fill=WHITE)
        card(s, 6.20, y, 6.58, 0.56, [P(T(desc, size=12.5, color=MUTED),
                                        align=PP_ALIGN.LEFT, sa=0)], fill=WHITE)
        y += 0.62
    txt(s, 0.55, 6.42, 12.2, 0.4,
        [P(T("控场原则：超时先砍「展望 / 代码细节」，绝不砍演示；演示含备用录屏与已生成样例。",
             size=11.5, color=MUTED), sa=0)])

    # ---------------------------------------------------------- 03 痛点与目标
    s = new()
    header(s, 3, "A · 开场", "痛点 → 第 4 部分目标")
    bullets_card(s, 0.55, 1.25, 5.95, 4.35, "运营同学的痛点（真实场景）", [
        "搜行业动态、查销售、算同比、写周报：四件事、四个工具、反复复制粘贴",
        "自然语言需求天天变（同比 / 环比 / 按区域）：固定脚本永远追不上",
        "数字必须“查出来”：不能约等于，更不能是模型编的",
        "出问题要能查：过程不可见，就只能“重跑一遍碰运气”",
    ], size=14, gap=11, fill=RGBColor(0xFD, 0xF2, 0xF4), line=RGBColor(0xE7, 0xC4, 0xC9))
    bullets_card(s, 6.83, 1.25, 5.95, 4.35, "第 4 部分目标（需求口径）", [
        "说一句话 → Agent 自主规划 → 最多 8 轮工具调用 → 完整 Markdown 周报",
        "周报类工作量目标降低约 50%（需求目标，非已测 KPI）",
        "全过程时间线可视化：可看、可停（取消）、可审计",
        "为第 3 部分知识库预留可开关接口，独立验收不受阻",
    ], size=14, gap=11, fill=GREEN, line=RGBColor(0xBF, 0xDD, 0xCD))
    card(s, 0.55, 5.80, 12.23, 1.05,
         [P(T("一句话版本：", size=13, bold=True, color=NAVY),
            T("把“碎、慢、怕出错”的重复工作，交给一个有状态、有止损、有审计的 Agent。",
              size=13, color=INK), sa=0, ls=1.05)],
         fill=WARM, line=RGBColor(0xE6, 0xD3, 0xA6))

    # ---------------------------------------------------------- 04 第 3↔4 边界
    s = new()
    header(s, 4, "B · 范围", "大项目边界：第 3 部分 ↔ 第 4 部分")
    bullets_card(s, 0.55, 1.30, 5.15, 2.55, "第 3 部分 · 企业内部知识库问答（另一交付）", [
        "文档上传 / 解析 / 向量库 / 检索问答（RAG 本体）",
        "本仓库不实现，也不依赖它上线",
        "提供稳定 HTTP 问答接口（hit=false 语义明确）",
    ], fill=LIGHT, title_size=13.5, size=12)
    arrow_r(s, 5.85, 2.35, 0.72, 0.45, color=BLUE)
    txt(s, 5.78, 2.85, 0.9, 0.3, [P(T("预留接口", size=10.5, bold=True, color=BLUE),
                                     align=PP_ALIGN.CENTER, sa=0)])
    bullets_card(s, 6.78, 1.30, 6.0, 2.55, "第 4 部分 · 本交付（运营 Agent）", [
        "LangGraph 业务 Agent + 工具链 + 周报工作台",
        "工具 enterprise_knowledge_search：默认 Stub",
        "KB_ENABLED=false → 固定文案「当前未接入企业内部知识库」，不编造",
        "启用后：POST {KB_BASE_URL}/api/v1/qa（question / top_k / session_id）",
    ], fill=SOFT, title_size=13.5, size=12, line=RGBColor(0xB9, 0xCB, 0xE8))
    chip(s, 0.55, 4.15, 3.93, 1.25, "工具名\nenterprise_knowledge_search",
         fill=WHITE, line=GREY_LINE, color=INK, size=11.5)
    chip(s, 4.70, 4.15, 3.93, 1.25, "默认行为\nKB_ENABLED=false → Stub\n失败按普通工具失败处理（重试 1 次）",
         fill=WHITE, line=GREY_LINE, color=INK, size=11.5)
    chip(s, 8.85, 4.15, 3.93, 1.25, "开启后\nHTTP 调用第 3 部分问答 API\n响应：answer / hit / citations",
         fill=WHITE, line=GREY_LINE, color=INK, size=11.5)
    card(s, 0.55, 5.70, 12.23, 1.10,
         [P(T("原则：", size=13, bold=True, color=NAVY),
            T("第 4 部分独立可验收；接口先行（契约已定，联调只差开关）；Stub 期间绝不把占位文案当内部制度写入周报。",
              size=13, color=INK), sa=0, ls=1.05)],
         fill=WARM, line=RGBColor(0xE6, 0xD3, 0xA6))

    # ---------------------------------------------------------- 05 架构
    s = new()
    header(s, 5, "C · 架构", "总体架构：五层，一眼看清")
    layers = [
        ("L1", "接入层", "浏览器：登录页 / 运营工作台（时间线 + 分屏预览）/ 开发日志页"),
        ("L2", "服务层", "FastAPI + JWT · 会话运行时 + 取消标志 · /api/sessions · events · stream(SSE) · reports"),
        ("L3", "编排层", "LangGraph StateGraph + MemorySaver（thread_id = session_id，一个会话一条记忆）"),
        ("L4", "工具层", "web_search · mysql_query(只读) · calculator · current_time · 文件读写 · KB Stub（7 个）"),
        ("L5", "数据层", "业务库 sales/users/agent_logs（只读查询）· 每用户分库 eoa_u_{id}（会话 / 事件 / 周报）"),
    ]
    y = 1.22
    for i, (tag, name, desc) in enumerate(layers):
        card(s, 0.55, y, 0.72, 0.86, [P(T(tag, size=15, bold=True, color=WHITE),
                                        align=PP_ALIGN.CENTER, sa=0)],
             fill=NAVY if i % 2 == 0 else RGBColor(0x2A, 0x3E, 0x6B),
             anchor=MSO_ANCHOR.MIDDLE)
        card(s, 1.42, y, 11.36, 0.86,
             [P(T(name + "　", size=14.5, bold=True, color=NAVY),
                T(desc, size=12.5, color=INK), align=PP_ALIGN.LEFT, sa=0, ls=1.0)],
             fill=LIGHT if i % 2 == 0 else SOFT, anchor=MSO_ANCHOR.MIDDLE)
        y += 1.02
    txt(s, 0.55, 6.40, 12.2, 0.5,
        [P(T("选型说明：默认 DeepSeek（openai 兼容，演示可切 GPT-4o-mini，预留 Qwen）；前端零框架静态页；事件“轮询 + SSE”双通道。",
             size=11.5, color=MUTED), sa=0)])

    # ---------------------------------------------------------- 06 一次任务全流程
    s = new()
    header(s, 6, "C · 全流程", "一次验收任务怎么走（时序）")
    chevrons(s, 0.55, 1.30, 12.23, 0.92, [
        "① 登录\nJWT · 角色 ops/dev",
        "② 发送任务\n自然语言一句话",
        "③ Agent 思考\n拆解并规划步骤",
        "④ 工具链多轮\n搜索 / 查库 / 计算",
        "⑤ finalize\nMarkdown 周报",
        "⑥ 时间线 + 落库\n预览 / 过往周报",
    ], fill=SOFT, line=RGBColor(0xB9, 0xCB, 0xE8))
    card(s, 0.55, 2.48, 6.0, 1.55,
         [P(T("验收句（原句，逐字使用）", size=12.5, bold=True, color=NAVY),
            sa=6, align=PP_ALIGN.LEFT),
          P(T("帮我搜索2026AI行业新闻，再查询本月销售总额，计算同比增长率，生成一份运营周报markdown",
              size=13.5, bold=True, color=RGBColor(0x8A, 0x5B, 0x00)), sa=0, ls=1.15)],
         fill=WARM, line=RGBColor(0xE6, 0xD3, 0xA6), anchor=MSO_ANCHOR.MIDDLE)
    card(s, 6.75, 2.48, 6.03, 1.55,
         [P(T("预期工具链与口径", size=12.5, bold=True, color=NAVY), sa=6, align=PP_ALIGN.LEFT),
          P(T("web_search → mysql_query（本月 + 去年同月）→ calculator → final（写文件可选）",
              size=12, color=INK), sa=4, align=PP_ALIGN.LEFT),
          P(T("种子数据：本月 100,000 / 去年同月 80,000 → 同比 +25.0%",
              size=12, bold=True, color=TEAL), sa=0, align=PP_ALIGN.LEFT)],
         fill=LIGHT, anchor=MSO_ANCHOR.MIDDLE)
    card(s, 0.55, 4.28, 3.93, 1.45,
         [P(T("可纠正的错误", size=12.5, bold=True, color=NAVY), sa=4, align=PP_ALIGN.LEFT),
          P(T("SQL 写错列名等\n→ 错误回传，模型自纠重查", size=12, color=INK), sa=0, align=PP_ALIGN.LEFT)],
         fill=WHITE, line=GREY_LINE)
    card(s, 4.70, 4.28, 3.93, 1.45,
         [P(T("不可恢复的失败", size=12.5, bold=True, color=NAVY), sa=4, align=PP_ALIGN.LEFT),
          P(T("重试 1 次仍失败\n→ 停止并明说原因，不编造", size=12, color=INK), sa=0, align=PP_ALIGN.LEFT)],
         fill=WHITE, line=GREY_LINE)
    card(s, 8.85, 4.28, 3.93, 1.45,
         [P(T("硬止损", size=12.5, bold=True, color=NAVY), sa=4, align=PP_ALIGN.LEFT),
          P(T("超 8 轮 / 超 30s / 人工取消\n→ 明确终态 max_rounds·timeout·cancelled",
              size=12, color=INK), sa=0, align=PP_ALIGN.LEFT)],
         fill=WHITE, line=GREY_LINE)
    txt(s, 0.55, 5.90, 12.2, 0.65,
        [P(T("真实事件流（节选）：user_input → thought → tool_call(web_search·含入参) → tool_result → tool_call(mysql_query·含 SQL) → … → final",
             size=11.5, color=MUTED), sa=0, ls=1.1),
         P(T("每一步都落日志与用户分库，可在「开发日志」与时间线里逐条回放。",
             size=11.5, color=MUTED), sa=0, ls=1.1)])

    # ---------------------------------------------------------- 07 LangGraph 运行逻辑
    s = new()
    header(s, 7, "D · 运行逻辑", "LangGraph 状态图：agent ⇄ tools → finalize")
    nodes = [
        ("START", 2.12, 0.95, SOFT, NAVY),
        ("agent\n思考 / 选工具", 3.21, 1.70, LIGHT, BLUE),
        ("tools\n执行 · 重试 1 次", 5.60, 1.60, LIGHT, BLUE),
        ("finalize\n产出终稿", 7.77, 1.50, GREEN, TEAL),
        ("END", 9.81, 0.95, SOFT, NAVY),
    ]
    for name, x, w, fill, line in nodes:
        card(s, x, 1.28, w, 0.88, [P(T(name, size=12.5, bold=True, color=NAVY),
                                     align=PP_ALIGN.CENTER, sa=0, ls=0.95)],
             fill=fill, line=line)
    # agent <-> tools 双向箭头
    dbl = s.shapes.add_shape(MSO_SHAPE.LEFT_RIGHT_ARROW, Inches(4.99), Inches(1.52),
                             Inches(0.53), Inches(0.36))
    dbl.fill.solid(); dbl.fill.fore_color.rgb = GOLD; dbl.line.fill.background()
    try:
        dbl.shadow.inherit = False
    except Exception:
        pass
    arrow_r(s, 7.28, 1.52, 0.41, 0.36, color=BLUE)
    arrow_r(s, 9.30, 1.52, 0.43, 0.36, color=TEAL)
    arrow_r(s, 3.075, 1.57, 0.12, 0.30, color=BLUE)
    txt(s, 4.62, 2.22, 1.30, 0.3,
        [P(T("tool_calls ⇄ 返回", size=9.5, color=GOLD, bold=True),
           align=PP_ALIGN.CENTER, sa=0)])
    txt(s, 7.22, 2.22, 0.72, 0.3,
        [P(T("无调用", size=9.5, color=BLUE, bold=True), align=PP_ALIGN.CENTER, sa=0)])
    # 三张卡
    card(s, 0.55, 2.62, 3.93, 2.18,
         [P(T("状态字段（AgentState）", size=12.5, bold=True, color=NAVY), sa=5, align=PP_ALIGN.LEFT),
          P(T("messages　消息轨迹（含工具调用）", size=11.5, color=INK), sa=3, align=PP_ALIGN.LEFT),
          P(T("tool_round　工具轮次计数器", size=11.5, color=INK), sa=3, align=PP_ALIGN.LEFT),
          P(T("status　运行状态机", size=11.5, color=INK), sa=3, align=PP_ALIGN.LEFT),
          P(T("events　事件列表（推给前端）", size=11.5, color=INK), sa=3, align=PP_ALIGN.LEFT),
          P(T("session_id / user_id　归属", size=11.5, color=INK), sa=0, align=PP_ALIGN.LEFT)],
         fill=LIGHT, anchor=MSO_ANCHOR.TOP)
    card(s, 4.70, 2.62, 3.93, 2.18,
         [P(T("状态机（status）", size=12.5, bold=True, color=NAVY), sa=5, align=PP_ALIGN.LEFT),
          P(T("running → completed", size=11.5, color=TEAL, bold=True), sa=3, align=PP_ALIGN.LEFT),
          P(T("running → failed（连续失败）", size=11.5, color=RED), sa=3, align=PP_ALIGN.LEFT),
          P(T("running → timeout（30s）", size=11.5, color=RED), sa=3, align=PP_ALIGN.LEFT),
          P(T("running → max_rounds（>8 轮）", size=11.5, color=RED), sa=3, align=PP_ALIGN.LEFT),
          P(T("running → cancelled（人工）", size=11.5, color=MUTED), sa=0, align=PP_ALIGN.LEFT)],
         fill=LIGHT, anchor=MSO_ANCHOR.TOP)
    card(s, 8.85, 2.62, 3.93, 2.18,
         [P(T("止损与“取消互斥”", size=12.5, bold=True, color=NAVY), sa=5, align=PP_ALIGN.LEFT),
          P(T("轮次 > 8：先 +1 再判断，立即终止", size=11.5, color=INK), sa=3, align=PP_ALIGN.LEFT),
          P(T("超时 30s：asyncio 强制终止", size=11.5, color=INK), sa=3, align=PP_ALIGN.LEFT),
          P(T("失败：重试 1 次，仍失败即停", size=11.5, color=INK), sa=3, align=PP_ALIGN.LEFT),
          P(T("取消：仅 running 生效；已有 final / 终态 → 拒绝改写（保持原状态）",
              size=11.5, color=GOLD, bold=True), sa=0, align=PP_ALIGN.LEFT, ls=1.05)],
         fill=WARM, line=RGBColor(0xE6, 0xD3, 0xA6), anchor=MSO_ANCHOR.TOP)
    card(s, 0.55, 5.00, 12.23, 1.72,
         [P(T("为什么用状态图（而不是一次性 Prompt / 纯 AgentExecutor）", size=12.5,
              bold=True, color=NAVY), sa=6, align=PP_ALIGN.LEFT),
          P(T("· 多步工具链：循环“思考 → 调用 → 回填”用条件边表达最自然；　· 可控终止：轮次 / 超时 / 取消 / 失败都挂在图上，一处收紧；",
              size=12, color=INK), sa=3, align=PP_ALIGN.LEFT),
          P(T("· 可恢复会话：MemorySaver 按 thread_id 存图状态，同会话追问自动带上下文；　· 可审计：状态与事件同源，前端显示的就是图里发生的。",
              size=12, color=INK), sa=0, align=PP_ALIGN.LEFT)],
         fill=LIGHT, anchor=MSO_ANCHOR.MIDDLE)

    # ---------------------------------------------------------- 08 工具箱
    s = new()
    header(s, 8, "D · 工具箱", "7 个工具：每个都有“护栏”")
    tools_top = [
        ("web_search", "Tavily 联网搜索", "行业新闻 / 公开信息", "未配置 → 明确报错，不编新闻"),
        ("mysql_query", "只读 SQL 查询", "sales(sale_date, amount, region)", "仅 SELECT + 黑名单 + 禁多语句"),
        ("calculator", "安全计算器", "ast 白名单数学表达式", "禁 exec / 求值任意代码"),
        ("current_time", "当前时间", "让“本月 / 去年同月”对齐真实日期", "相对时间的锚点"),
    ]
    tools_bottom = [
        ("read / write_markdown_report", "Markdown 文件读写", "锁死在 reports/，仅 .md，防路径穿越与绝对路径", "样例产出 weekly-ops.md"),
        ("enterprise_knowledge_search", "知识库预留（第 3 部分）", "默认 Stub：「当前未接入企业内部知识库」", "KB_ENABLED=true 后走 HTTP"),
        ("用户分库（写侧能力）", "会话 / 事件 / 周报落库", "MySQL eoa_u_{id}；mock 则 data/users/u_{id}.db", "「过往周报」数据源"),
    ]
    x = 0.55
    for name, title, desc, tag in tools_top:
        card(s, x, 1.28, 2.93, 2.05,
             [P(T(title, size=13.5, bold=True, color=NAVY), sa=2, align=PP_ALIGN.LEFT),
              P(T(name, size=10, color=BLUE), sa=4, align=PP_ALIGN.LEFT),
              P(T(desc, size=11, color=INK), sa=4, align=PP_ALIGN.LEFT),
              P(T(tag, size=10.5, color=GOLD), sa=0, align=PP_ALIGN.LEFT)],
             fill=LIGHT, anchor=MSO_ANCHOR.TOP)
        x += 3.09
    x = 0.57
    for name, title, desc, tag in tools_bottom:
        card(s, x, 3.48, 3.93, 2.05,
             [P(T(title, size=13.5, bold=True, color=NAVY), sa=2, align=PP_ALIGN.LEFT),
              P(T(name, size=10, color=BLUE), sa=4, align=PP_ALIGN.LEFT),
              P(T(desc, size=11.5, color=INK), sa=4, align=PP_ALIGN.LEFT),
              P(T(tag, size=11, color=TEAL), sa=0, align=PP_ALIGN.LEFT)],
             fill=SOFT if x > 5 else LIGHT, anchor=MSO_ANCHOR.TOP)
        x += 4.13
    card(s, 0.55, 5.68, 12.23, 1.10,
         [P(T("防“臆造”三道保险：", size=12.5, bold=True, color=NAVY),
            T("① 系统提示写明表结构与字面量日期示例；② 工具 docstring 再写一遍 schema 与示例 SQL；③ 执行失败回传可读错误，让模型自纠而不是当机。",
              size=12.5, color=INK), sa=0, ls=1.1)],
         fill=WARM, line=RGBColor(0xE6, 0xD3, 0xA6))

    # ---------------------------------------------------------- 09 安全与止损
    s = new()
    header(s, 9, "D · 安全止损", "“怕什么 → 挡什么”六条防线")
    fears = [
        ("怕死循环", "最多 8 轮工具；超限即终止，终态 max_rounds", RED),
        ("怕挂太久", "单任务 30s 硬超时；asyncio 层强制终止", RED),
        ("怕外网抖动", "工具失败自动重试 1 次；仍失败则停止并说明", GOLD),
        ("怕 SQL 误伤", "仅 SELECT + 9 个写/高危关键词黑名单 + 禁多语句", RED),
        ("怕路径穿越", "文件工具锁死 reports/，仅 .md，禁绝对路径", GOLD),
        ("怕“误取消”", "终态互斥：已有 final / 状态终态 → 拒绝改写 cancelled", TEAL),
    ]
    x, y = 0.57, 1.30
    for i, (fear, block, color) in enumerate(fears):
        cx = 0.57 + (i % 3) * 4.13
        cy = 1.30 + (i // 3) * 1.86
        card(s, cx, cy, 3.93, 1.68,
             [P(T(fear, size=13.5, bold=True, color=color), sa=5, align=PP_ALIGN.LEFT),
              P(T(block, size=11.5, color=INK), sa=0, align=PP_ALIGN.LEFT, ls=1.1)],
             fill=WHITE, line=GREY_LINE, anchor=MSO_ANCHOR.MIDDLE)
    card(s, 0.55, 5.06, 12.23, 1.66,
         [P(T("★ 联调复盘（真实事故 → 修复，报告直接可引用）", size=13, bold=True,
              color=RGBColor(0x8A, 0x5B, 0x00)), sa=6, align=PP_ALIGN.LEFT),
          P(T("① 模型臆造列名 order_date → 原实现把 SQL 错误当致命失败直接停链；修复：错误回传自纠 + 提示词写清 schema；",
              size=12, color=INK), sa=3, align=PP_ALIGN.LEFT),
          P(T("② 周报已完成却显示 cancelled → 修复：取消与终态互斥 + 前端终态禁用取消 + 中文状态芯片。",
              size=12, color=INK), sa=0, align=PP_ALIGN.LEFT)],
         fill=WARM, line=RGBColor(0xE6, 0xD3, 0xA6), anchor=MSO_ANCHOR.MIDDLE)

    # ---------------------------------------------------------- 10 登录·会话·权限
    s = new()
    header(s, 10, "E · 平台", "登录、角色与会话隔离")
    card(s, 0.55, 1.25, 5.95, 2.10,
         [P(T("角色与账号（本地演示）", size=13.5, bold=True, color=NAVY), sa=5, align=PP_ALIGN.LEFT),
          P(T("ops / ops123：对话、看自己的执行过程与周报；", size=12.5, color=INK), sa=3, align=PP_ALIGN.LEFT),
          P(T("dev / dev123：额外可看全局日志页与 GET /api/logs；", size=12.5, color=INK), sa=3, align=PP_ALIGN.LEFT),
          P(T("密码 PBKDF2 加盐哈希入库；登录签发 JWT（Bearer）。", size=12.5, color=INK), sa=0, align=PP_ALIGN.LEFT)],
         fill=LIGHT)
    card(s, 6.83, 1.25, 5.95, 2.10,
         [P(T("会话模型：session_id ↔ thread_id", size=13.5, bold=True, color=NAVY), sa=5, align=PP_ALIGN.LEFT),
          P(T("同会话可连续追问（MemorySaver 记忆）；", size=12.5, color=INK), sa=3, align=PP_ALIGN.LEFT),
          P(T("「新开对话」= 新线程，清空上下文；", size=12.5, color=INK), sa=3, align=PP_ALIGN.LEFT),
          P(T("会话归属校验：非本人访问 403/404；dev 可查全局日志。", size=12.5, color=INK), sa=0, align=PP_ALIGN.LEFT)],
         fill=LIGHT)
    card(s, 0.55, 3.55, 5.95, 2.10,
         [P(T("取消的语义（答辩高频）", size=13.5, bold=True, color=NAVY), sa=5, align=PP_ALIGN.LEFT),
          P(T("仅 running 状态可取消；", size=12.5, color=INK), sa=3, align=PP_ALIGN.LEFT),
          P(T("completed / failed / timeout / max_rounds 或已有 final：拒绝并保持原状态；",
              size=12.5, color=INK), sa=3, align=PP_ALIGN.LEFT),
          P(T("图节点逐处检查取消标志，实现“合作式取消”。", size=12.5, color=INK), sa=0, align=PP_ALIGN.LEFT)],
         fill=GREEN)
    card(s, 6.83, 3.55, 5.95, 2.10,
         [P(T("隔离与隐私", size=13.5, bold=True, color=NAVY), sa=5, align=PP_ALIGN.LEFT),
          P(T("销售业务查询与用户数据分离：查销售走只读业务库；", size=12.5, color=INK), sa=3, align=PP_ALIGN.LEFT),
          P(T("会话消息 / 事件 / 周报落在每用户分库；", size=12.5, color=INK), sa=3, align=PP_ALIGN.LEFT),
          P(T("「过往周报」只列当前登录用户自己的数据。", size=12.5, color=INK), sa=0, align=PP_ALIGN.LEFT)],
         fill=SOFT)
    card(s, 0.55, 5.85, 12.23, 0.95,
         [P(T("演示前状态：", size=12.5, bold=True, color=NAVY),
            T("本机 .env 已配置 DeepSeek 与 Tavily，USE_MOCK_DB=false 连真实 MySQL；演示账号均为本地演示用途。",
              size=12.5, color=INK), sa=0, ls=1.05)],
         fill=WARM, line=RGBColor(0xE6, 0xD3, 0xA6))

    # ---------------------------------------------------------- 11 界面信息架构
    s = new()
    header(s, 11, "E · 界面", "工作台信息架构（示意）")
    rect(s, 0.55, 1.22, 12.23, 5.05, fill=WHITE, line=GREY_LINE)
    rect(s, 0.55, 1.22, 12.23, 0.34, fill=RGBColor(0xED, 0xF1, 0xF7))
    txt(s, 0.72, 1.25, 6.5, 0.28,
        [P(T("127.0.0.1:8000 · 运营工作台", size=10.5, color=MUTED), sa=0)])
    dot(s, 12.30, 1.33, 0.10, RGBColor(0xE6, 0x7A, 0x7A))
    dot(s, 12.44, 1.33, 0.10, RGBColor(0xE8, 0xB7, 0x4B))
    dot(s, 12.58, 1.33, 0.10, RGBColor(0x7A, 0xC4, 0x8E))
    # 侧栏
    rect(s, 0.62, 1.62, 2.50, 4.55, fill=LIGHT)
    chip(s, 0.72, 1.72, 2.30, 0.42, "运营助手 · 第 4 部分", fill=SOFT, color=NAVY, size=10.5, radius=0.25)
    chip(s, 0.72, 2.26, 2.30, 0.46, "运营周报 Agent（当前）", fill=WHITE, line=BLUE, color=NAVY, size=10.5, radius=0.25)
    chip(s, 0.72, 2.82, 2.30, 0.46, "知识库问答（第 3 部分占位）", fill=SOFT, color=MUTED, size=10.5, radius=0.25)
    chip(s, 0.72, 5.62, 2.30, 0.50, "头像 · 昵称（下行登录名）→ 设置", fill=WHITE, line=GREY_LINE, color=INK, size=9.5, radius=0.25)
    # 主区顶栏
    rect(s, 3.25, 1.62, 9.42, 0.44, fill=WHITE)
    txt(s, 3.38, 1.68, 5.0, 0.3,
        [P(T("运营周报 Agent · 会话 3f9c…", size=10.5, bold=True, color=INK), sa=0)])
    chip(s, 9.62, 1.66, 1.28, 0.34, "过往周报", fill=SOFT, color=NAVY, size=10, radius=0.3)
    chip(s, 10.98, 1.66, 1.20, 0.34, "新开对话", fill=SOFT, color=NAVY, size=10, radius=0.3)
    chip(s, 12.26, 1.66, 0.36, 0.34, "⋯", fill=SOFT, color=NAVY, size=10, radius=0.3)
    # 时间线
    rect(s, 3.25, 2.12, 4.55, 2.62, fill=LIGHT)
    txt(s, 3.38, 2.20, 4.0, 0.3, [P(T("执行过程（时间线）", size=11, bold=True, color=NAVY), sa=0)])
    chip(s, 3.38, 2.56, 1.30, 0.36, "思考", fill=WHITE, line=GREY_LINE, color=INK, size=9.5, radius=0.3)
    chip(s, 3.38, 3.00, 4.16, 0.42, "工具调用 · web_search（入参展开）", fill=WHITE, line=GREY_LINE, color=INK, size=9.5, radius=0.25)
    chip(s, 3.38, 3.50, 4.16, 0.36, "工具返回（摘要）", fill=WHITE, line=GREY_LINE, color=INK, size=9.5, radius=0.25)
    chip(s, 3.38, 3.94, 4.16, 0.36, "工具调用 · mysql_query（SQL 入参）", fill=WHITE, line=GREY_LINE, color=INK, size=9.5, radius=0.25)
    chip(s, 3.38, 4.38, 1.30, 0.32, "…final", fill=GREEN, color=TEAL, size=9.5, radius=0.3)
    # 预览
    rect(s, 7.95, 2.12, 4.72, 2.62, fill=SOFT)
    txt(s, 8.08, 2.20, 4.4, 0.3, [P(T("周报预览（出 final 后右侧分屏，可收起 / 复制）", size=11, bold=True, color=NAVY), sa=0)])
    for i in range(3):
        rect(s, 8.08, 2.58 + i * 0.30, 4.46, 0.16, fill=WHITE)
    rect(s, 8.08, 3.56, 3.10, 0.16, fill=WHITE)
    chip(s, 8.08, 4.30, 2.0, 0.34, "查看 / 复制 / 收起", fill=WHITE, line=GREY_LINE, color=MUTED, size=9.5, radius=0.3)
    # composer
    rect(s, 3.25, 4.86, 9.42, 0.82, fill=WHITE)
    rect(s, 3.37, 4.94, 6.40, 0.66, fill=LIGHT)
    txt(s, 3.50, 5.10, 6.0, 0.35, [P(T("输入自然语言任务…（发送成功后输入框清空）", size=10, color=MUTED), sa=0)])
    chip(s, 9.90, 4.96, 0.95, 0.32, "已完成", fill=GREEN, color=TEAL, size=9.5, radius=0.4)
    chip(s, 10.95, 4.96, 0.75, 0.32, "取消", fill=LIGHT, color=MUTED, size=9.5, radius=0.25)
    chip(s, 11.80, 4.96, 0.75, 0.32, "发送", fill=NAVY, color=WHITE, size=9.5, radius=0.25)
    txt(s, 3.30, 5.72, 9.3, 0.35,
        [P(T("补充：设置弹窗（改昵称 / 周报目录偏好 / 退出）；「过往周报」右侧抽屉；dev 登录后顶部出现「开发日志」。",
             size=10, color=MUTED), sa=0)])
    txt(s, 0.55, 6.38, 12.2, 0.6,
        [P(T("① 能力壳 + 用户卡　② 顶栏：过往周报 / 新开对话（dev 另有日志入口）　③ 时间线：入参 / 返回默认展开　④ 分屏预览：可收起 / 复制　⑤ composer：取消仅任务进行中可点",
             size=10.5, color=MUTED), sa=0, ls=1.1)])

    # ---------------------------------------------------------- 12 可观测
    s = new()
    header(s, 12, "E · 可观测", "过程可视化与日志：每一步都可回放")
    card(s, 0.55, 1.28, 4.55, 4.55,
         [P(T("事件模型（统一 JSON）", size=13.5, bold=True, color=NAVY), sa=8, align=PP_ALIGN.LEFT),
          P(T("type 九类：", size=11.5, bold=True, color=INK), sa=4, align=PP_ALIGN.LEFT),
          P(T("thought　思考", size=11.5, color=INK), sa=2, align=PP_ALIGN.LEFT),
          P(T("tool_call　工具调用（含入参）", size=11.5, color=INK), sa=2, align=PP_ALIGN.LEFT),
          P(T("tool_result　工具返回", size=11.5, color=INK), sa=2, align=PP_ALIGN.LEFT),
          P(T("final　终稿 Markdown", size=11.5, color=TEAL), sa=2, align=PP_ALIGN.LEFT),
          P(T("error / cancelled / max_rounds / timeout", size=11.5, color=RED), sa=2, align=PP_ALIGN.LEFT),
          P(T("（另有 user_input 用户输入）", size=10.5, color=MUTED), sa=0, align=PP_ALIGN.LEFT)],
         fill=LIGHT, anchor=MSO_ANCHOR.TOP)
    card(s, 5.30, 1.28, 7.48, 2.15,
         [P(T("两条通路：前端实时 + 后端持久化", size=13.5, bold=True, color=NAVY), sa=6, align=PP_ALIGN.LEFT),
          P(T("· 前端：轮询 GET events + SSE 流式，按序渲染时间线；", size=12.5, color=INK), sa=3, align=PP_ALIGN.LEFT),
          P(T("· 后端：每个事件同步写 agent_logs 与用户分库 tool_events，带时间戳；", size=12.5, color=INK), sa=3, align=PP_ALIGN.LEFT),
          P(T("· 事件与状态双轨：终态由事件驱动（final → completed）。", size=12.5, color=INK), sa=0, align=PP_ALIGN.LEFT)],
         fill=WHITE, line=GREY_LINE)
    card(s, 5.30, 3.58, 7.48, 2.25,
         [P(T("日志与保留", size=13.5, bold=True, color=NAVY), sa=6, align=PP_ALIGN.LEFT),
          P(T("· dev 角色专属「开发日志」页 + GET /api/logs（按会话筛选）；", size=12.5, color=INK), sa=3, align=PP_ALIGN.LEFT),
          P(T("· 记录：用户输入、思考、全部工具入参与返回、时间戳；", size=12.5, color=INK), sa=3, align=PP_ALIGN.LEFT),
          P(T("· 默认保留 60 天，scripts/purge_logs.py 定期清理；", size=12.5, color=INK), sa=3, align=PP_ALIGN.LEFT),
          P(T("· 用途：排障、审计、报告素材（联调记录就是从这里来的）。", size=12.5, color=INK), sa=0, align=PP_ALIGN.LEFT)],
         fill=WHITE, line=GREY_LINE)
    card(s, 0.55, 6.00, 12.23, 0.80,
         [P(T("可观测性 = 可审计：数字从哪来、每一步调用了什么，全部可以逐条回放。",
              size=13, bold=True, color=NAVY), sa=0)],
         fill=WARM, line=RGBColor(0xE6, 0xD3, 0xA6))

    # ---------------------------------------------------------- 13 多轮记忆
    s = new()
    header(s, 13, "F · 演示预告", "多轮记忆：同一会话“上周格式 → 本周”")
    card(s, 0.55, 1.35, 5.42, 2.75,
         [P(T("第 1 轮（生成上周周报）", size=14, bold=True, color=NAVY), sa=8),
          P(T("“生成一份上周运营周报 markdown”", size=13, color=INK), sa=6, ls=1.1),
          P(T("→ 完整周报：标题层级 / 章节结构 / 写法被记入本次会话", size=12, color=MUTED), sa=0, ls=1.15)],
         fill=LIGHT, anchor=MSO_ANCHOR.MIDDLE)
    arrow_r(s, 6.12, 2.42, 1.05, 0.42, color=GOLD)
    txt(s, 5.90, 2.92, 1.55, 0.3,
        [P(T("同一会话", size=10.5, bold=True, color=GOLD), align=PP_ALIGN.CENTER, sa=0)])
    card(s, 7.35, 1.35, 5.43, 2.75,
         [P(T("第 2 轮（沿用格式生成本周）", size=14, bold=True, color=NAVY), sa=8),
          P(T("“请沿用刚才周报的标题层级和章节结构，补充一句本周风险提示”",
              size=13, color=INK), sa=6, ls=1.1),
          P(T("→ 不重新规划，按上一份结构续写；MemorySaver 按 thread_id 记忆", size=12, color=MUTED), sa=0, ls=1.15)],
         fill=SOFT, anchor=MSO_ANCHOR.MIDDLE)
    card(s, 0.55, 4.35, 12.23, 1.05,
         [P(T("机制：", size=12.5, bold=True, color=NAVY),
            T("MemorySaver 以 thread_id（= session_id）保存图状态；「新开对话」才会换线程、清空上下文；服务重启会丢图状态（日志与周报不受影响，后续可换 Postgres checkpointer）。",
              size=12.5, color=INK), sa=0, ls=1.12)],
         fill=LIGHT, anchor=MSO_ANCHOR.MIDDLE)
    card(s, 0.55, 5.60, 12.23, 1.05,
         [P(T("演示口令：", size=12.5, bold=True, color=RGBColor(0x8A, 0x5B, 0x00)),
            T("“同一会话可以追问；只有点『新开对话』才会清空记忆。”",
              size=13, bold=True, color=RGBColor(0x8A, 0x5B, 0x00)), sa=0)],
         fill=WARM, line=RGBColor(0xE6, 0xD3, 0xA6))

    # ---------------------------------------------------------- 14 演示提词
    s = new()
    header(s, 14, "F · 现场演示（7′）", "演示脚本：照这 6 步走")
    steps = [
        ("1", "启动与登录", "uvicorn app.main:app（127.0.0.1:8000）→ 浏览器登录 ops/ops123"),
        ("2", "指界面 30 秒", "侧栏能力壳 / 时间线 / composer / 顶栏按钮 / 用户卡设置"),
        ("3", "跑验收句", "粘贴原句发送 → 指时间线：搜索 → 查库 → 计算（入参都展开）"),
        ("4", "讲终稿与预览", "右侧分屏周报：本月/去年同月 + 同比 +25%，强调“数字来自数据库”"),
        ("5", "加餐：记忆追问", "同会话发“沿用刚才的格式……”→ 展示结构被记住"),
        ("6", "加餐：过往周报 / dev 日志", "抽屉里刚生成的周报；dev 登录看事件日志（时间紧可跳）"),
    ]
    y = 1.28
    for num, title, desc in steps:
        dot(s, 0.60, y + 0.13, 0.34, BLUE)
        txt(s, 0.60, y + 0.13, 0.34, 0.34, [P(T(num, size=13, bold=True, color=WHITE),
                                               align=PP_ALIGN.CENTER, sa=0)])
        card(s, 1.08, y, 6.72, 0.78,
             [P(T(title + "　", size=13, bold=True, color=NAVY),
                T(desc, size=11.5, color=INK), align=PP_ALIGN.LEFT, sa=0, ls=1.02)],
             fill=LIGHT if int(num) % 2 else WHITE, line=GREY_LINE, anchor=MSO_ANCHOR.MIDDLE)
        y += 0.88
    card(s, 8.05, 1.28, 4.73, 1.85,
         [P(T("演示口令（照念）", size=13, bold=True, color=RGBColor(0x8A, 0x5B, 0x00)), sa=6, align=PP_ALIGN.LEFT),
          P(T("“这里调用了数据库而不是编造销售额。”", size=12, bold=True, color=RGBColor(0x8A, 0x5B, 0x00)), sa=3, align=PP_ALIGN.LEFT),
          P(T("“同一会话可以追问；只有新开对话才清空记忆。”", size=12, bold=True, color=RGBColor(0x8A, 0x5B, 0x00)), sa=0, align=PP_ALIGN.LEFT)],
         fill=WARM, line=RGBColor(0xE6, 0xD3, 0xA6), anchor=MSO_ANCHOR.TOP)
    card(s, 8.05, 3.28, 4.73, 2.10,
         [P(T("备用计划（写死进流程）", size=13, bold=True, color=NAVY), sa=6, align=PP_ALIGN.LEFT),
          P(T("· 搜索/模型失败：立刻切 reports/weekly-ops.md 或录屏，说明工具链已跑通；", size=11.5, color=INK), sa=3, align=PP_ALIGN.LEFT),
          P(T("· 30s 超时：说明“兜底会明说超时、不编造”，转讲安全设计；", size=11.5, color=INK), sa=3, align=PP_ALIGN.LEFT),
          P(T("· 页面异常：Ctrl+F5；端口被占改 8001。", size=11.5, color=INK), sa=0, align=PP_ALIGN.LEFT)],
         fill=LIGHT, anchor=MSO_ANCHOR.TOP)
    card(s, 8.05, 5.53, 4.73, 1.27,
         [P(T("时间盒", size=13, bold=True, color=NAVY), sa=5, align=PP_ALIGN.LEFT),
          P(T("总 7′：步骤 1–4 占 5′，加餐各 1′；超时优先砍第 6 步，绝不砍验收句。",
              size=11.5, color=INK), sa=0, align=PP_ALIGN.LEFT, ls=1.12)],
         fill=WHITE, line=GREY_LINE, anchor=MSO_ANCHOR.MIDDLE)

    # ---------------------------------------------------------- 15 每用户分库
    s = new()
    header(s, 15, "G · 数据", "每用户分库 + 过往周报：数据归谁，自己说了算")
    card(s, 0.55, 1.28, 5.95, 3.05,
         [P(T("业务库（共享，只读查询）", size=13.5, bold=True, color=NAVY), sa=6, align=PP_ALIGN.LEFT),
          P(T("· users：演示账号（PBKDF2 哈希、JWT 登录）", size=12.5, color=INK), sa=4, align=PP_ALIGN.LEFT),
          P(T("· sales：销售种子数据（本月 10 万 / 去年同月 8 万）", size=12.5, color=INK), sa=4, align=PP_ALIGN.LEFT),
          P(T("· agent_logs：全局事件日志（60 天保留）", size=12.5, color=INK), sa=4, align=PP_ALIGN.LEFT),
          P(T("· SQL 工具唯一去处：在只读防线下执行", size=12.5, color=TEAL), sa=0, align=PP_ALIGN.LEFT)],
         fill=LIGHT, anchor=MSO_ANCHOR.TOP)
    card(s, 6.83, 1.28, 5.95, 3.05,
         [P(T("用户分库（每用户一套）", size=13.5, bold=True, color=NAVY), sa=6, align=PP_ALIGN.LEFT),
          P(T("· MySQL：eoa_u_{id}；mock：data/users/u_{id}.db", size=12.5, color=INK), sa=4, align=PP_ALIGN.LEFT),
          P(T("· conversations：会话（「新开对话」= 新行）", size=12.5, color=INK), sa=4, align=PP_ALIGN.LEFT),
          P(T("· messages / tool_events：消息与事件回放", size=12.5, color=INK), sa=4, align=PP_ALIGN.LEFT),
          P(T("· weekly_reports：成功 final 的周报正文", size=12.5, color=INK), sa=4, align=PP_ALIGN.LEFT),
          P(T("· API：GET /api/reports、/api/reports/{id}（仅本人）", size=12.5, color=TEAL), sa=0, align=PP_ALIGN.LEFT)],
         fill=SOFT, anchor=MSO_ANCHOR.TOP)
    card(s, 0.55, 4.52, 12.23, 1.05,
         [P(T("为什么要分：", size=12.5, bold=True, color=NAVY),
            T("隔离与审计（谁的会话、谁的周报一目了然）；「过往周报」不依赖扫磁盘目录；与销售业务查询天然分离——查数不会碰到用户数据。",
              size=12.5, color=INK), sa=0, ls=1.1)],
         fill=WARM, line=RGBColor(0xE6, 0xD3, 0xA6))
    card(s, 0.55, 5.72, 12.23, 1.08,
         [P(T("演示口令：", size=12.5, bold=True, color=RGBColor(0x8A, 0x5B, 0x00)),
            T("“这些周报存在我自己的用户分库里——换个账号登录，就看不到。”",
              size=13, bold=True, color=RGBColor(0x8A, 0x5B, 0x00)), sa=2),
          P(T("排障提示：抽屉为空 = 本账号没有成功生成过 final（不是坏了）。",
              size=10.5, color=MUTED), sa=0)],
         fill=WHITE, line=GREY_LINE, anchor=MSO_ANCHOR.MIDDLE)

    # ---------------------------------------------------------- 16 代码地图
    s = new()
    header(s, 16, "G · 代码实现", "代码地图：评委问“在哪改”，照这张表答")
    rows = [
        ("目标", "优先打开的文件"),
        ("图结构 / 条件边 / 编译", "app/agent/graph.py"),
        ("三个节点：思考 / 工具重试 / finalize", "app/agent/nodes.py"),
        ("状态字段定义（AgentState）", "app/agent/state.py"),
        ("系统提示词（schema / 禁编造 / 停止条件）", "app/agent/prompts.py"),
        ("工具注册表（7 个工具）", "app/tools/registry.py"),
        ("SQL 防护 + 错误回传自纠", "app/tools/mysql_query.py"),
        ("会话 / 取消 / 事件 API", "app/api/chat.py · app/runtime.py"),
        ("每用户分库与周报读写", "app/db/user_store.py · app/api/reports.py"),
        ("日志落库与 60 天清理", "app/logging_service.py · scripts/purge_logs.py"),
        ("前端：登录 / 工作台 / 日志（零框架）", "web/login.html · index.html · logs.html · app.css · common.js"),
    ]
    _table(s, 0.55, 1.28, [4.55, 7.68], rows, row_h=0.465, size=11.5)
    txt(s, 0.55, 6.52, 12.2, 0.4,
        [P(T("讲法：不念代码、不报模块堆砌——按“这功能在哪改、为什么这么拆”回答；时间紧只讲 graph.py 与 user_store.py。",
             size=11.5, color=MUTED), sa=0)])

    # ---------------------------------------------------------- 16 测试与验收
    s = new()
    header(s, 17, "H · 质量", "测试与验收：28 项全绿 + 验收清单")
    card(s, 0.55, 1.28, 6.0, 4.62,
         [P(T("端到端验收对照（acceptance_check.md）", size=13.5, bold=True, color=NAVY), sa=8, align=PP_ALIGN.LEFT),
          P(T("✓ 登录 ops / dev，角色入口互不越权", size=12.5, color=INK), sa=5, align=PP_ALIGN.LEFT),
          P(T("✓ 发送后输入框清空；时间线出现搜索 / SQL / 计算器", size=12.5, color=INK), sa=5, align=PP_ALIGN.LEFT),
          P(T("✓ 工具入参 / 返回默认展开可见", size=12.5, color=INK), sa=5, align=PP_ALIGN.LEFT),
          P(T("✓ 终稿 Markdown + 右侧分屏预览；状态「已完成」", size=12.5, color=INK), sa=5, align=PP_ALIGN.LEFT),
          P(T("✓ 过往周报可见（每用户分库）", size=12.5, color=INK), sa=5, align=PP_ALIGN.LEFT),
          P(T("✓ 取消仅 running 可点；终态禁用", size=12.5, color=INK), sa=5, align=PP_ALIGN.LEFT),
          P(T("✓ 同会话记忆两轮（上周格式 → 本周）", size=12.5, color=INK), sa=5, align=PP_ALIGN.LEFT),
          P(T("✓ dev 日志页按会话可查全部事件", size=12.5, color=INK), sa=10, align=PP_ALIGN.LEFT),
          P(T("现场演示覆盖前 6 项；完整十条见 scripts/acceptance_check.md。", size=11, color=MUTED), sa=0, align=PP_ALIGN.LEFT)],
         fill=GREEN, anchor=MSO_ANCHOR.TOP)
    card(s, 6.75, 1.28, 6.03, 4.62,
         [P(T("pytest：28 个用例全部通过（4.5s）", size=13.5, bold=True, color=NAVY), sa=8, align=PP_ALIGN.LEFT),
          P(T("覆盖：鉴权与角色越权 / 取消互斥 / SQL 防护与错误回传 / 计算器安全 / 图轮次上限 / KB Stub / 文件工具防穿越 / 周报归属隔离 / API 取消", size=12, color=INK), sa=7, align=PP_ALIGN.LEFT, ls=1.15),
          P(T("用例文件：test_auth · test_api_cancel · test_sql_guard · test_calculator · test_graph_limits · test_kb · test_file_io · test_mysql_query · test_reports", size=11, color=MUTED), sa=7, align=PP_ALIGN.LEFT, ls=1.1),
          P(T(r".\.venv\Scripts\python.exe -m pytest -q", size=11.5, bold=True, color=TEAL), sa=7, align=PP_ALIGN.LEFT),
          P(T("单测全程 mock：不出网、不打真实 DeepSeek / Tavily / MySQL；联网验收按脚本清单人工执行。",
              size=12, color=INK), sa=0, align=PP_ALIGN.LEFT, ls=1.15)],
         fill=LIGHT, anchor=MSO_ANCHOR.TOP)
    card(s, 0.55, 6.05, 12.23, 0.75,
         [P(T("真实联调已完成：验收句在真实 DeepSeek + Tavily + MySQL 下跑通，产出 reports/weekly-ops.md（含 +25% 同比与新闻摘要）；两次事故与修复见下页。",
              size=12, color=INK), sa=0, ls=1.05)],
         fill=WARM, line=RGBColor(0xE6, 0xD3, 0xA6))

    # ---------------------------------------------------------- 17 联调复盘
    s = new()
    header(s, 18, "H · 联调复盘", "两次真实事故：问题 → 根因 → 修复")
    card(s, 0.55, 1.28, 6.0, 4.66,
         [P(T("事故一：SQL 臆造列名 → 任务直接终止", size=13.5, bold=True, color=RED), sa=8, align=PP_ALIGN.LEFT),
          P(T("现象：", size=12, bold=True, color=NAVY), T("时间线在 mysql_query 后立刻 error：「no such column: order_date」。", size=12, color=INK), sa=5, align=PP_ALIGN.LEFT, ls=1.12),
          P(T("根因：", size=12, bold=True, color=NAVY), T("模型臆造列名；执行失败被 raise 成工具异常，被“失败即停”当成致命错误。", size=12, color=INK), sa=5, align=PP_ALIGN.LEFT, ls=1.12),
          P(T("修复：", size=12, bold=True, color=NAVY), T("① 失败改为返回可读错误字符串，提示核对表结构后重试；② 系统提示与工具 docstring 写明 sales(sale_date, amount, region) 与字面量日期示例。", size=12, color=INK), sa=5, align=PP_ALIGN.LEFT, ls=1.12),
          P(T("结论：", size=12, bold=True, color=TEAL), T("可纠正的错误应回传模型自纠；“工具失败即停”只留给不可恢复故障。", size=12, color=INK), sa=0, align=PP_ALIGN.LEFT, ls=1.12)],
         fill=PINK, line=RGBColor(0xE7, 0xC4, 0xC9), anchor=MSO_ANCHOR.TOP)
    card(s, 6.75, 1.28, 6.03, 4.66,
         [P(T("事故二：周报已完成，状态却显示 cancelled", size=13.5, bold=True, color=RED), sa=8, align=PP_ALIGN.LEFT),
          P(T("现象：", size=12, bold=True, color=NAVY), T("右侧已有完整周报，顶部状态仍为「已取消」。", size=12, color=INK), sa=5, align=PP_ALIGN.LEFT, ls=1.12),
          P(T("根因：", size=12, bold=True, color=NAVY), T("任务完成后仍可点取消；cancel 接口无条件把状态改写为 cancelled，与 final 事件并存。", size=12, color=INK), sa=5, align=PP_ALIGN.LEFT, ls=1.12),
          P(T("修复：", size=12, bold=True, color=NAVY), T("① 终态（completed/failed/timeout/max_rounds）或已有 final 时拒绝覆盖；② 前端终态禁用取消；③ 状态芯片中文化。", size=12, color=INK), sa=5, align=PP_ALIGN.LEFT, ls=1.12),
          P(T("结论：", size=12, bold=True, color=TEAL), T("取消只作用于真正进行中的任务；已有报告即视为成功完成。", size=12, color=INK), sa=0, align=PP_ALIGN.LEFT, ls=1.12)],
         fill=WARM, line=RGBColor(0xE6, 0xD3, 0xA6), anchor=MSO_ANCHOR.TOP)
    card(s, 0.55, 6.10, 12.23, 0.72,
         [P(T("来源：README「联调问题记录」（附完整时间线）；已同步进测试用例，回归有保障。",
              size=12, color=INK), sa=0)],
         fill=LIGHT)

    # ---------------------------------------------------------- 18 风险与边界
    s = new()
    header(s, 19, "H · 风险诚实边界", "风险与对策（不遮不掩）")
    rows = [
        ("风险", "对策 / 诚实口径"),
        ("MemorySaver 为进程内记忆：重启 / 多副本会丢图状态",
         "日志与周报在库不受影响；生产升级为 Postgres checkpointer（已列入展望）"),
        ("30s 超时对长链路偏紧（规划硬约束，未擅自放宽）",
         "配置项可调；演示用短任务；备用录屏与已生成样例"),
        ("外部 API 波动：DeepSeek / Tavily 不可用",
         "重试 1 次后停止并明说原因；绝不用编造数据兜底"),
        ("单进程会话内存态：横向扩容需外部会话存储",
         "当前定位是单机演示 / 内部试用；扩容路径已在文档写明"),
    ]
    _table(s, 0.55, 1.28, [6.0, 6.23], rows, row_h=0.62, size=11.5)
    card(s, 0.55, 4.85, 12.23, 1.15,
         [P(T("明确不做（写进 README，避免误解为“未完成”）：", size=12.5, bold=True, color=NAVY), sa=5, align=PP_ALIGN.LEFT),
          P(T("OAuth / SSO · 细粒度 RBAC · K8s · 真实数仓对接 · 第 3 部分 RAG 本体 · 移动端 App",
              size=12, color=INK), sa=0, align=PP_ALIGN.LEFT)],
         fill=LIGHT, anchor=MSO_ANCHOR.MIDDLE)
    card(s, 0.55, 6.05, 12.23, 0.75,
         [P(T("展示原则：宁可少讲一页，不把“没做 / 没测”说成“已交付”；所有数字都能在仓库里找到出处。",
              size=12, color=INK), sa=0)],
         fill=WARM, line=RGBColor(0xE6, 0xD3, 0xA6))

    # ---------------------------------------------------------- 19 总结
    s = new()
    header(s, 20, "H · 总结", "交付了什么：三条价值")
    cards = [
        ("01", "可运行的有状态 Agent", "LangGraph StateGraph + MemorySaver；最多 8 轮工具链；同会话追问，新开对话即重置；一句验收句端到端跑通。"),
        ("02", "安全与可观测是设计出来的", "SQL 只读三重防护；轮次 / 超时 / 重试 / 取消四类止损；时间线 + 日志 + 分库三重留痕；两个真实事故闭环成测试。"),
        ("03", "具备真实系统形态", "JWT 登录 + ops/dev 角色；每用户分库与过往周报；零框架前端工作台；28 项测试与完整文档（README / AGENT / 验收清单）。"),
    ]
    x = 0.57
    for num, title, desc in cards:
        card(s, x, 1.45, 3.93, 3.00,
             [P(T(num, size=30, bold=True, color=GOLD), sa=4),
              P(T(title, size=15, bold=True, color=NAVY), sa=8, ls=1.05),
              P(T(desc, size=12, color=INK), sa=0, ls=1.22)],
             fill=LIGHT if num == "02" else WHITE, line=GREY_LINE, anchor=MSO_ANCHOR.TOP)
        x += 4.13
    card(s, 0.55, 4.80, 12.23, 1.50,
         [P(T("一句话收束：说一句话，它自己完成“搜新闻 + 查数 + 计算 + 出周报”——过程可看、可停、可审计；",
              size=14.5, bold=True, color=NAVY), sa=4),
          P(T("并为第 3 部分知识库留好了随开随用的接口。", size=12.5, color=MUTED), sa=0)],
         fill=WARM, line=RGBColor(0xE6, 0xD3, 0xA6))

    # ---------------------------------------------------------- 20 展望
    s = new()
    header(s, 21, "H · 展望", "下一步：把演示形态推向可用形态")
    items = [
        ("1", "对接真实第 3 部分 KB", "KB_ENABLED=true + KB_BASE_URL，替换 Stub；错误按工具失败重试语义处理。"),
        ("2", "持久化会话（Postgres checkpointer）", "替换 MemorySaver：会话跨重启、支持多副本部署。"),
        ("3", "会话列表与周报模板管理", "分库已有 conversations 表基础；前端加会话抽屉与模板选择。"),
        ("4", "运维化落地", "密钥管理、超时与保留策略、演示环境一键启动脚本。"),
    ]
    y = 1.30
    for num, title, desc in items:
        card(s, 0.55, y, 0.62, 0.92, [P(T(num, size=17, bold=True, color=WHITE),
                                         align=PP_ALIGN.CENTER, sa=0)], fill=NAVY)
        card(s, 1.32, y, 11.46, 0.92,
             [P(T(title + "　", size=13.5, bold=True, color=NAVY),
                T(desc, size=12, color=INK), align=PP_ALIGN.LEFT, sa=0, ls=1.05)],
             fill=LIGHT if int(num) % 2 else SOFT, anchor=MSO_ANCHOR.MIDDLE)
        y += 1.05
    txt(s, 0.55, 5.72, 12.2, 0.4,
        [P(T("以上为规划方向，不在本次交付范围；当前交付以第 15–19 页为准。",
             size=11.5, color=MUTED), sa=0)])

    # ---------------------------------------------------------- 21 谢谢
    s = new()
    rect(s, 0, 0, 13.333, 7.5, fill=NAVY)
    txt(s, 0.9, 2.55, 11.5, 1.2,
        [P(T("谢谢聆听 · 欢迎提问", size=38, bold=True, color=WHITE), sa=0)])
    txt(s, 0.9, 3.95, 11.5, 0.5,
        [P(T("欢迎上手体验：http://127.0.0.1:8000（ops/ops123）",
             size=16, color=RGBColor(0xE8, 0xD9, 0xAD)), sa=0)])
    txt(s, 0.9, 4.60, 11.5, 0.5,
        [P(T("仓库：github.com/MirroR0102/Enterprise-Automation-Agent（备用展示）",
             size=13, color=RGBColor(0xC9, 0xD4, 0xE8)), sa=0)])
    txt(s, 0.9, 5.35, 11.5, 0.5,
        [P(T("备用材料：reports/weekly-ops.md · 演讲稿 / 执行说明（本地）",
             size=12, color=RGBColor(0xA9, 0xB6, 0xD0)), sa=0)])

    prs.save(str(PPTX_PATH))
    return PPTX_PATH


# ================================================================ PDF 工具
def _register_font() -> str:
    candidates = [
        Path(r"C:\Windows\Fonts\msyh.ttc"),
        Path(r"C:\Windows\Fonts\msyh.ttf"),
        Path(r"C:\Windows\Fonts\simhei.ttf"),
    ]
    for path in candidates:
        if path.exists():
            try:
                pdfmetrics.registerFont(TTFont("CN", str(path)))
                return "CN"
            except Exception:
                continue
    return "Helvetica"


def _pdf_styles(font: str):
    s = {}
    s["title"] = ParagraphStyle("t", fontName=font, fontSize=17, leading=24,
                                textColor=HexColor("#1B2A4A"), spaceAfter=8)
    s["meta"] = ParagraphStyle("m", fontName=font, fontSize=9.5, leading=14,
                               textColor=HexColor("#5B687D"), spaceAfter=4,
                               wordWrap="CJK")
    s["h1"] = ParagraphStyle("h", fontName=font, fontSize=13.5, leading=19,
                             textColor=HexColor("#FFFFFF"), spaceBefore=14,
                             spaceAfter=8, backColor=HexColor("#1B2A4A"),
                             borderPadding=(4, 6, 4, 6), wordWrap="CJK")
    s["h2"] = ParagraphStyle("h2", fontName=font, fontSize=11.5, leading=16,
                             textColor=HexColor("#8A5B00"), spaceBefore=10,
                             spaceAfter=4, wordWrap="CJK")
    s["body"] = ParagraphStyle("b", fontName=font, fontSize=10.5, leading=16,
                               textColor=HexColor("#16223A"), spaceAfter=6,
                               wordWrap="CJK", alignment=4)
    s["cue"] = ParagraphStyle("c", fontName=font, fontSize=10.5, leading=16,
                              textColor=HexColor("#B23A48"), spaceBefore=4,
                              spaceAfter=6, wordWrap="CJK",
                              backColor=HexColor("#FDF2F4"), borderPadding=(3, 5, 3, 5))
    s["q"] = ParagraphStyle("q", fontName=font, fontSize=10.5, leading=16,
                            textColor=HexColor("#8A5B00"), spaceBefore=4,
                            spaceAfter=6, wordWrap="CJK", backColor=HexColor("#FBF3E2"),
                            borderPadding=(3, 5, 3, 5))
    s["note"] = ParagraphStyle("n", fontName=font, fontSize=9.5, leading=14,
                               textColor=HexColor("#5B687D"), spaceBefore=2,
                               spaceAfter=6, wordWrap="CJK")
    s["small"] = ParagraphStyle("s", fontName=font, fontSize=9, leading=13,
                                textColor=HexColor("#0F766E"), spaceAfter=3,
                                wordWrap="CJK")
    return s


# ================================================================ 演讲稿
def build_speech_pdf() -> Path:
    font = _register_font()
    st = _pdf_styles(font)
    doc = SimpleDocTemplate(str(SPEECH_PDF), pagesize=A4, leftMargin=2 * cm,
                            rightMargin=2 * cm, topMargin=1.8 * cm, bottomMargin=1.9 * cm)
    story = []

    def P(text, style=None):
        story.append(Paragraph(text, style or st["body"]))

    def H(text):
        story.append(Paragraph(text, st["h1"]))

    def H2(text):
        story.append(Paragraph(text, st["h2"]))

    def CUE(text):
        story.append(Paragraph("【动作】" + text, st["cue"]))

    def Q(text):
        story.append(Paragraph("【口令】" + text, st["q"]))

    def NOTE(text):
        story.append(Paragraph("【时间提示】" + text, st["note"]))

    def SMALL(text):
        story.append(Paragraph(text, st["small"]))

    P("《企业业务流程自动化 Agent》第 4 部分 · 项目报告讲稿", st["title"])
    P("配套 PPT：同目录《第4部分…汇报.pptx》（22 页）｜总时长约 30 分钟｜建议语速 240–260 字/分钟"
      "｜灰色【】为动作 / 演示提示，不要念出声。", st["meta"])
    P("汇报人：李刘钰祚　　日期：____ 年 __ 月 __ 日（留空手填）　　仓库：MirroR0102/Enterprise-Automation-Agent", st["meta"])
    SMALL("代码地图（供查阅，不念）：① 图结构 graph.py ② 节点 nodes.py ③ 状态 state.py ④ 提示词 prompts.py "
          "⑤ 工具 registry.py / mysql_query.py ⑥ 会话与取消 api/chat.py + runtime.py ⑦ 用户分库 db/user_store.py + api/reports.py "
          "⑧ 日志 logging_service.py + scripts/purge_logs.py ⑨ 前端 web/ ⑩ 生成脚本 scripts/build_presentation.py")

    H("一、开场 · 痛点与目标（0:00–3:00）｜ PPT 1–3")
    P("各位老师、同学，大家好。今天我的汇报是大项目第 4 部分——企业业务流程自动化 Agent。")
    P("开场先讲一个很具体的场景。假设你是公司运营，周一早上要交出上一周的运营周报：先去网上搜一圈行业动态，"
      "再登录业务系统查本月销售总额，然后翻出去年同期的数字算一个同比，最后把内容拼成一份格式规整的周报。"
      "四件事、四个工具、无数次复制粘贴——真正麻烦的不是“不会做”，而是它太碎、太重复。还有一个更关键的点："
      "周报里的数字必须是真实查出来的，不能约等于，更不能是编的。")
    P("那能不能让系统听懂人话？“帮我查本月销售，算个同比，再结合行业新闻生成周报”——问题立刻来了：自然语言需求天天在变。"
      "今天要同比，明天要环比，后天要按区域拆分。固定脚本永远追不上业务变化。")
    P("所以第 4 部分的目标一句话：做一个有状态的运营 Agent——用户说一句自然语言，系统自己拆解步骤、调用工具、"
      "最多 8 轮，最后产出一份完整的 Markdown 周报；整个过程要看得见、能取消、可审计，数字全部来自工具。"
      "需求文档里的业务目标是“周报类工作量减少约 50%”——我说明一下口径：这是需求提出的目标值，不是我们已测过的 KPI。")
    P("用一句话先立三个目标，待会儿逐条证明：第一，模型不“瞎编数字”——所有数字都能追溯到工具；"
      "第二，系统不“失控乱跑”——该停的时候一定停；第三，过程不是黑盒——每一步都有记录可查。")
    CUE("翻到痛点页（PPT 第 3 页），指左右两栏；语气放慢，把节奏带起来。")
    P("左边是痛点，右边是我们的目标。等一会儿现场演示的时候，大家在右边看到的每一条目标，都会当场兑现。")

    H("二、范围界定 · 与第 3 部分的关系（3:00–6:00）｜ PPT 4")
    P("讲技术之前，先交代边界：这是大项目里的第 4 部分。大项目里还有第 3 部分——企业内部知识库问答，也就是 RAG。"
      "文档上传、向量库、检索问答，这些是第 3 部分的范围，我们这个仓库不实现。")
    P("那两部分怎么衔接？我们预留了一个工具，叫 enterprise_knowledge_search。默认开关 KB_ENABLED=false，"
      "走的是一根“桩”（Stub）：你问它，它固定回答“当前未接入企业内部知识库”——它绝不编造任何业务内容。"
      "等第 3 部分交付之后，只要把开关打开、配上它的问答接口地址，这个工具就会自动改为通过 HTTP 去调用第 3 部分的服务。"
      "接口契约已经定死了：请求带 question、top_k、session_id；响应里 answer、hit、citations 三个字段。")
    P("这样设计有两个好处：第一，第 4 部分今天就可以独立验收，不会被第 3 部分的进度拖住；"
      "第二，联调只差一个开关，不需要改代码。范围边界也说清楚：做——LangGraph Agent、工具链、登录角色、过程可视化、"
      "日志、每用户分库、第 3 部分接口预留；不做——单点登录、细粒度权限、K8s、真实数仓，以及第 3 部分的 RAG 本体。")
    P("再补一句为什么“接口先行”很重要：如果两部分都等对方先做，就成了互相拖进度；我们把契约定死、"
      "把开关留给部署，等于把“联调”压缩成了“开开关”。这也是两部分都能按时独立交付的原因。")
    CUE("指 PPT 第 4 页中间箭头与下方三格接口示意，强调“接口先行、独立验收”。")

    H("三、总体架构 · 一次任务的全流程（6:00–11:00）｜ PPT 5–7")
    P("先看总体架构，从上到下五层。")
    P("最上面是接入层：浏览器三个页面——登录页、运营工作台、开发日志页。工作台是浅色双栏：左边能力栏和用户卡，"
      "中间执行过程时间线，底部输入框，周报出来后在右侧分屏预览。")
    P("第二层服务层：FastAPI 提供 HTTP 接口——登录用 JWT；每个会话有独立运行时和取消标志；"
      "接口包括建会话、发消息、拉事件、SSE 流、取消、过往周报。")
    P("第三层编排层，是核心：LangGraph 的 StateGraph。会话记忆用 MemorySaver，会话键 thread_id 就等于 session_id——"
      "一个会话一条记忆，互不串台。")
    P("第四层工具层：七个工具——联网搜索、只读 SQL、计算器、当前时间、Markdown 文件读写，以及第 3 部分预留工具。")
    P("第五层数据层：业务库存销售和账号；每个用户还有一个自己的分库，存他的会话消息、事件和过往周报。")
    P("从这张图还能看出一个重要的取舍：编排层不直接碰数据库、也不直接读写文件——一切都要经过工具，"
      "而工具自带护栏。这样一来，“模型能做什么”就被约束在“工具允许做什么”的范围内，边界是清晰的。"
      "这也是我们敢在答辩现场放开手跑的原因：哪怕模型理解偏了，工具的护栏会把损失限制在小范围里。")
    CUE("指 PPT 第 5 页分层图，从上往下依次指；不要念模块名，讲“每层负责什么”。")
    P("再看“一次任务怎么走”。用户登录拿到 Token，创建一个会话，粘贴一句任务；后台把这句话交给图：agent 节点先思考，"
      "需要数据就发起工具调用；tools 节点执行工具，结果写回状态；agent 再决策——还需要信息就继续调工具；"
      "信息够了就走到 finalize，把完整 Markdown 作为最终事件推给前端。前端一边轮询、一边用 SSE 接收事件，"
      "把“思考 → 工具名 → 入参 → 返回 → 终稿”实时画成时间线；同时所有事件落日志库，成功周报再落用户分库。")
    P("为什么用图、而不是一次性 Prompt？三个原因：第一，多步工具链的循环——“思考、调用、回填”用条件边表达最自然；"
      "第二，终止条件可以精确控制——轮次、超时、取消、失败，全部挂在图上；第三，状态和事件都在图里流转，天然可审计。")
    P("再说两个实现细节。第一，前端是怎么做到“实时”的？其实两条通路并存：一条是定时轮询事件列表——"
      "服务端每 0.25 秒检查一次有没有新事件；另一条是 SSE 流式通道，任务结束时会推送一个 done 信号。"
      "这样即使某一条通路抖动，时间线也不会丢内容。第二，事件是“只增不改”的：思考、调用、返回、终稿，"
      "按时间戳追加；终态由事件驱动——“final 到达”这件事本身就是“任务完成”的判定依据。"
      "这也保证了回放的一致性：开发日志里看到的事件序列，就是当时前端时间线上出现的序列。")
    CUE("翻到 PPT 第 7 页运行逻辑图：先指 agent 与 tools 的循环，再指下面三张卡（状态字段 / 状态机 / 止损）。")

    H("四、核心机制 · 工具箱与安全止损（11:00–14:00）｜ PPT 8–9")
    P("具体讲两个关键机制：工具箱和安全止损。")
    P("工具箱七个，各有护栏。搜索工具接的是 Tavily，拿公开的行业新闻；SQL 工具只允许查——业务表 sales 就三列，"
      "sale_date、amount、region，工具说明里写得清清楚楚，就是为了不让模型发挥出不存在的列名；"
      "计算器用 Python 的 ast 白名单实现，只算数学表达式，不能执行任意代码；时间工具提供“今天”，"
      "因为“本月”“去年同月”这种相对时间要锚定到真实日期；文件工具锁死在 reports 目录里，只许 .md，"
      "禁止绝对路径和路径穿越；最后一个是知识库预留工具，前面讲过了。")
    P("举个例子。验收句跑起来之后，大家会在入参里看到模型自己写出的 SQL——select sum(amount) from sales，"
      "条件是 sale_date 在 2026 年 9 月 1 日到 10 月 1 日之间。注意，它用的是字面量日期，而不是 CURDATE() 这类函数。"
      "为什么？因为提示词里明确写了：mock 模式不兼容日期函数，用字面量最稳。"
      "这一条小小的约束，是被联调事故“教”出来的。")
    P("然后是这一部分我认为最值得讲的：安全与止损——用一个句式，“怕什么，挡什么”。"
      "怕死循环 → 最多 8 轮工具，超限立刻终止；怕挂太久 → 单任务 30 秒硬超时；怕外部接口抖动 → 失败自动重试 1 次，"
      "再失败就停，并把失败原因明说，不允许编数据；怕 SQL 误伤 → 只读 + 九个写操作关键字黑名单 + 禁多语句；"
      "怕路径穿越 → 文件锁死在 reports/；怕“误取消” → 终态互斥，这个有故事，马上讲。")
    CUE("翻到 PPT 第 9 页，六格快速过，在金色高亮条停住。")
    P("讲两个真实踩过的坑，都在仓库 README 里有完整记录，也是我们报告里“问题与解决”的素材。")
    P("第一个坑：模型把销量表的列名臆造成了 order_date。最早实现里，SQL 执行失败会抛异常，被当成“工具连续失败”，"
      "整条任务直接终止——一个本可以改好再查的 SQL 错误，把整条链掐死了。修复其实是个观念转变：把“可纠正的错误”"
      "回传给模型自纠。现在 SQL 跑错会返回一条明确的错误说明，提示核对表结构重试；同时我们在系统提示和工具说明里"
      "把真实 schema 写死。改完之后，模型自己就能把列名改对、重查、继续完成任务。")
    P("第二个坑：有一次任务已经出了完整周报，状态栏却显示“已取消”。根因是任务完成后取消按钮还能点，"
      "取消接口无条件把状态改成 cancelled。修复是“终态互斥”：已完成、或者事件里已经有 final 的，取消请求一律拒绝；"
      "前端在终态把取消按钮置灰；状态芯片全部中文化。")
    P("这两个故事说明的事情一样：Agent 系统里，“什么时候停下来”和“什么时候继续”同样重要。")
    P("修复之后我们都补了回归测试：SQL 错误回传有测试、取消互斥有测试。这样下次再改代码，这两条底线先被守住。")

    H("五、登录、界面与可观测（14:00–16:00）｜ PPT 10–12")
    P("快速看一下用户体系和可观测性。角色只有两个：ops 是运营，能对话、看自己的执行过程和周报；"
      "dev 是开发维护，额外能看全局日志页和日志 API。密码在库里是 PBKDF2 哈希加盐，不落明文；登录签发 JWT。"
      "演示账号 ops 和 dev，密码在仓库 README 里，仅本地演示用。")
    P("会话机制三个点：同一个会话可以连续追问，记忆在 MemorySaver 里；点“新开对话”才会换线程、清空上下文；"
      "会话有归属校验，别人的会话打不开。")
    P("取消这个动作我再展开一句：它不是“杀掉进程”那种蛮力，而是合作式取消——取消接口先置标志、"
      "把状态记为 cancelled；图里的每个节点在关键位置检查这个标志，看到就优雅退出。"
      "而如果任务其实已经完成、final 已经产生，取消请求会被直接拒绝——保证“已经交付的结果”不会被误标。")
    P("可观测性上，每个事件都是结构化 JSON：思考、工具调用（带入参）、工具返回、终稿、错误、取消、超轮次、超时——"
      "统统一条记录。前端按序渲染成时间线，入参和返回默认展开；dev 的日志页按会话筛选；日志默认保留 60 天，"
      "配了清理脚本。还有个工程细节：周报不但写 reports 文件夹，还同时存进每个用户自己的分库——"
      "MySQL 模式建 eoa_u_{id} 库，本机 mock 模式就是一个用户一个 SQLite 文件。前端“过往周报”抽屉就是从分库读的。")
    CUE("翻到 PPT 第 14 页分库图，指业务库与用户库的分界；这里只要 20 秒，演示时还会看到。")

    H("六、现场演示 · 验收句全链路（16:00–23:00）｜ PPT 13–14")
    CUE("切浏览器：打开 http://127.0.0.1:8000，用 ops / ops123 登录。先确认左下角是 ops。")
    P("界面先花 30 秒：左边能力栏——“运营周报 Agent”，下面“知识库问答”是第 3 部分的占位；左下角是昵称和登录名，"
      "点头像可以改昵称；中间是执行过程区；底部输入框；右上角“过往周报”和“新开对话”。")
    Q("“下面我用需求里的原句跑一遍，请看时间线。”")
    CUE("粘贴验收句，发送。原句：帮我搜索2026AI行业新闻，再查询本月销售总额，计算同比增长率，生成一份运营周报markdown")
    P("发送之后，大家看时间线：先出现“思考”，模型在规划；接着是搜索工具的调用，入参里能看到查询词；"
      "工具返回后继续思考、继续调用——数据库查询，查本月和去年同月的销售额，SQL 语句作为入参直接展示；"
      "然后用计算器算同比；最后 finalize，输出整份 Markdown 周报。发送成功后输入框会自动清空，"
      "这是交互细节，但保证连续演示不手忙脚乱。")
    Q("“这里我要强调：销售额是数据库里查出来的，不是模型编的。”")
    CUE("指右侧预览：本月数据、同比分析、新闻摘要、风险提示、行动建议。同比 +25%——种子数据本月十万、去年同月八万。")
    P("这里给大家看一眼周报结构：标题、本期数据、同比分析、行业新闻摘要、风险提示、行动建议——"
      "一个可以直接交出去的运营周报。")
    P("另外注意状态芯片——这里显示的是中文“已完成”；如果中途点过取消，它会显示“已取消”，"
      "而且只可能在任务真正进行中发生。这个细节就是前面说过的“终态互斥”在界面上的样子。")
    CUE("加餐一（记忆）：同一会话继续发送——“请沿用刚才周报的标题层级和章节结构，补充一句本周风险提示”。")
    P("看它没有重新规划，而是顺着上一份周报的结构续写——记忆就演示在这里。")
    Q("“同一会话可以追问；只有点『新开对话』才会清空记忆。”")
    CUE("加餐二（过往周报）：点右上角“过往周报”，刚生成的这份在列表里，点开重新预览。")
    P("这些数据存在我自己的用户分库里——换一个账号登录，就看不到我的周报。")
    CUE("加餐三（可选）：dev / dev123 登录，打开“开发日志”，按会话查到刚才全部事件——思考、工具、入参、返回、时间戳，一条不少。")
    NOTE("现场慢 / 失败怎么办：立刻切备用——打开仓库里已生成好的 reports/weekly-ops.md 或录屏，说明工具链此前已完整跑通；"
         "超时就口头说明“兜底会明说失败、不编造”，转讲安全设计。原则：绝不砍演示。")

    H("七、代码实现 · 关键模块地图（23:00–28:00）｜ PPT 15–16")
    P("演示看的是效果，这一段讲“它是怎么实现的”，大约 5 分钟。我按“评委问『这功能在哪改』怎么答”的方式过一遍。")
    P("编排核心在 app/agent 下四个文件。graph.py 定义图：START 进 agent；条件边——有 tool_calls 去 tools，没有去 finalize；"
      "tools 执行完回到 agent，形成循环。nodes.py 是三个节点的实现：agent 节点负责思考并广播思考事件；"
      "tools 节点负责执行、记录入参和返回、失败重试一次、超轮次终止；finalize 节点产出最终事件并把状态置为 completed。"
      "state.py 定义状态字段；prompts.py 是系统提示词，写清了工具使用顺序、表结构、禁止编造，以及“拿到足够信息就停”。")
    P("再讲一个高频问题：事件是怎么记的？每个节点在做事的同时，往 state 的 events 里追加一条结构化事件，"
      "并同步写日志与用户分库；API 层把这些事件合成一条流，前端按序渲染。"
      "也就是说，时间线不是页面自己“拼”出来的——它就是图运行时留下的轨迹。")
    P("安全在 app/tools/mysql_query.py：is_safe_select_sql 做三道校验——开头必须是 select、黑名单九个关键字、"
      "禁止分号多语句；run_mysql_query 执行查询，并把失败变成“可自纠的错误信息”，这就是刚才那个事故的修复。")
    P("会话与取消在 app/api/chat.py 和 app/runtime.py：runtime 存会话记录和取消标志；chat 负责建会话、投消息、"
      "拉事件、SSE、取消——“终态互斥”逻辑就在 cancel 接口里。")
    P("取消的完整链路值得再过一遍：前端点取消，请求到 cancel 接口；接口先查状态——允许取消才置标志、"
      "改写状态，并取消后台 asyncio 任务；图节点下一次检查时看到标志，走 cancelled 终态。"
      "这一整套设计里，任何一步都不允许把已完成的任务“改判”。")
    P("用户分库在 app/db/user_store.py：ensure_user_store 自动建库建表，save_weekly_report 落周报；"
      "对应 API 在 app/api/reports.py。日志在 app/logging_service.py，清理脚本 scripts/purge_logs.py。"
      "前端就是三个静态页面加 CSS 和公共 JS，没有引入重框架——一个考虑是课堂演示环境要简单可靠。")
    P("还有同学可能会问：以后想加一个新工具，要动几处？答案是两处——在 app/tools 下写一个带 @tool 装饰器的函数，"
      "把 docstring 写清楚（它其实是给模型看的说明书）；然后把它加进 registry 的工具列表。系统提示词里视情况补一句使用时机。"
      "就这样，Agent 下一次运行就能“看到”这个新工具。这是我认为这套架构最值得保留的扩展点。")
    NOTE("时间紧时：这一节只讲 graph.py 和 user_store.py，压缩到 3 分钟。")
    CUE("可切 IDE 打开 graph.py 指一下条件边；不要念代码。")

    H("八、测试、风险与总结（28:00–30:00）｜ PPT 17–22")
    P("最后讲质量保障、风险，然后总结。")
    P("测试方面：28 个 pytest 用例全部通过，覆盖鉴权、取消互斥、SQL 防护、计算器、图轮次上限、KB Stub、"
      "文件工具防穿越、周报归属隔离这些关键路径；单测全程不出网——mock 数据库，不打真实模型和搜索。"
      "联网验收按仓库 scripts/acceptance_check.md 的十个检查点人工执行。还有一个可以直接展示的证据："
      "仓库里 reports/weekly-ops.md 就是真实联调跑出来的周报，含 25% 同比和当天的行业新闻。")
    P("风险我选择诚实地说三条：第一，MemorySaver 是进程内记忆，服务重启会丢图状态——但日志和周报都在库里，"
      "不受影响；生产上换成 Postgres checkpointer 就能多副本。第二，30 秒超时对长链路偏紧，这是规划里的硬约束，"
      "我们没有擅自放宽；演示用短任务，备用录屏兜底。第三，外部 API 波动时，系统会明示失败，绝不编造——这是底线。")
    P("交付物也一并列一下：可运行的代码仓库、28 项测试、演示账号、验收清单、README 与 AGENT 两套文档，"
      "以及本地这套汇报材料。想复现的话，四步：装依赖、配 .env、跑 init_db、启动服务——五分钟。")
    P("总结成一句话：我们交付了一个可登录、过程可观测、带完整止损的 LangGraph 运营 Agent；说一句话，"
      "它自己完成搜新闻、查数、计算、出周报；并且为第 3 部分知识库留好了随开随用的接口。")
    P("最后留一个小尾巴：如果今天时间还充裕，我最想多聊的是“提示词工程与安全边界的平衡”——"
      "哪些约束应该写进提示词，哪些应该做成硬代码。这是我们做这个项目踩坑最多、也收获最多的地方，欢迎会后交流。")
    CUE("翻到第 19 页三条价值，语速放慢；再翻到“谢谢聆听”页收尾。")
    P("我的汇报到这里，谢谢大家，欢迎提问。")

    H2("附录 A · 评委可能提问 · 预备答（被问到再翻）")
    qa = [
        ("为什么用 LangGraph，而不是一次性 Prompt 或纯 AgentExecutor？",
         "多步工具需要显式的循环与条件边；轮次 / 超时 / 取消 / 失败都需要挂在图上统一收紧；状态与事件同源，可审计。"),
        ("怎么保证数字是真的？",
         "强制工具查库 + 提示词禁止编造 + 时间线展示 SQL 入参与返回，三重可核查；工具失败明说，不用假数据兜底。"),
        ("为什么定 8 轮、30 秒？",
         "防死循环、防挂死的硬止损；都是配置项可调，但规划要求默认不放宽，演示用短任务适配。"),
        ("SQL 很危险，怎么防？",
         "只读三件套：select 开头 + 九个写 / 高危词黑名单 + 禁多语句；执行层只连只读语义查询；失败回传模型自纠。"),
        ("任务做完了还能取消吗？",
         "不能。终态互斥：completed / failed / timeout / max_rounds 或已有 final 事件时，取消请求被拒绝并保持原状态。"),
        ("为什么每个用户单独建库？",
         "隔离与审计：会话、事件、周报天然按用户分域；与销售业务库分离，查销售不会碰到用户数据。"),
        ("第 3 部分还没好，你们怎么算集成完成？",
         "接口先行：工具名、开关、Stub 文案、HTTP 契约、失败语义都已定义；第 3 部分上线只需打开开关。第 4 部分独立验收。"),
        ("MemorySaver 重启丢状态怎么办？",
         "如实说明：进程内记忆，重启丢图状态；日志与周报落库不受影响；后续升级 Postgres checkpointer 即可。"),
        ("和直接用 ChatGPT / 平台插件有什么区别？",
         "私有链路：自有业务库只读防护、JWT 角色、会话与日志、每用户分库、与企业内部第 3 部分的预留集成。"),
        ("现场跑不出来怎么办？",
         "备用录屏与已生成周报；说明“失败会明说、不编造”本身就是设计目标之一。"),
    ]
    for q, a in qa:
        H2("Q：" + q)
        P("A：" + a)

    H2("附录 B · 事实速查卡（数字口径背这几个）")
    P("· 验收句原文：帮我搜索2026AI行业新闻，再查询本月销售总额，计算同比增长率，生成一份运营周报markdown")
    P("· 种子数据：本月 100,000；去年同月 80,000；同比 +25.0%（计算器结果 (10-8)/8）")
    P("· 账号：ops / ops123（运营）；dev / dev123（开发，另有日志页）")
    P("· 硬限制：工具轮次 ≤ 8；任务超时 30s；失败重试 1 次；SQL 黑名单 9 个关键字；日志保留 60 天")
    P("· 测试：28 个 pytest 用例全部通过（mock 环境，约 4.5s）")
    P("· 地址：http://127.0.0.1:8000（登录页 /login.html；API 文档 /docs）；仓库 MirroR0102/Enterprise-Automation-Agent")

    def foot(canvas, d):
        fname = "CN" if "CN" in _registered_fonts() else "Helvetica"
        canvas.saveState()
        canvas.setFont(fname, 8)
        canvas.setFillColor(HexColor("#8A94A6"))
        canvas.drawString(2 * cm, 1.0 * cm, "第 4 部分 · 演讲稿 · 仅供汇报人使用")
        canvas.drawRightString(A4[0] - 2 * cm, 1.0 * cm, f"第 {d.page} 页")
        canvas.restoreState()

    doc.build(story, onFirstPage=foot, onLaterPages=foot)
    return SPEECH_PDF


_registered_cache: list[str] = []


def _registered_fonts() -> list[str]:
    return _registered_cache


# ================================================================ 执行说明
RUNBOOK = [
    ("h1", "〇、这份文件怎么用"),
    ("p", "本文件给汇报人控场用，不要对听众朗读。配套三件套："),
    ("bullets", [
        "《第4部分-企业业务流程自动化Agent-汇报.pptx》——22 页少字多图版；",
        "《第4部分-企业业务流程自动化Agent-演讲稿.pdf》——约 30 分钟口语完整稿（含【动作】与附录备答）；",
        "本《报告执行说明》——会前清单 / 时间轴 / 逐段动作 / 应急与交流预案。",
    ]),
    ("p", "总原则：宁可少讲一页，不可错过演示；所有数字都能在仓库中找到出处。"),
    ("h1", "一、会前清单"),
    ("h2", "T-1 天（提前一天）"),
    ("bullets", [
        r"确认虚拟环境可用：.\.venv\Scripts\python.exe -m pytest -q → 应显示 28 passed；",
        ".env 已配好 DeepSeek 与 Tavily（本机已配，勿外传、勿提交）；USE_MOCK_DB=false 时确认本机 MySQL 已启动；",
        "完整干跑一遍验收句，确认时间线与周报正常；留意单次耗时（真实模型 + 搜索通常 20–60 秒）；",
        "登录一次 ops，触发一次任务“预热”模型与连接；准备 dev 账号用于日志演示；",
        "把 PPT / 讲稿过一遍，标好自己口播的断句；确认 reports/weekly-ops.md 存在（备用素材）。",
    ]),
    ("h2", "T-30 分钟（当天）"),
    ("bullets", [
        r"启动服务：cd 项目根目录 → .\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000（演示时建议不要 --reload）；",
        "浏览器打开 http://127.0.0.1:8000 登录 ops，硬刷新一次（Ctrl+F5）；",
        "复制到剪贴板：验收句原文；记忆加餐句（见下“演示原句”）；",
        "打开 PPT 停在封面；准备投屏测试与翻页；关闭聊天软件与系统通知；",
        "备用检查：录屏文件可播放 / reports/weekly-ops.md 可打开；手机存一份讲稿 PDF。",
    ]),
    ("h1", "二、30 分钟时间轴总表（对齐 PPT 页码）"),
    ("table", [
        ["时间", "环节", "PPT", "核心一句话"],
        ["0:00–3:00", "开场：痛点与目标", "1–3", "“说一句话 → 自己查数 → 出周报”"],
        ["3:00–6:00", "范围：第 3、4 部分边界", "4", "接口预留，独立验收"],
        ["6:00–11:00", "架构与全流程", "5–7", "五层 + 图循环 + 止损"],
        ["11:00–14:00", "工具箱与安全", "8–9", "“怕什么挡什么”；两个真实事故"],
        ["14:00–16:00", "登录 / 界面 / 观测", "10–12", "可看、可查、可审计"],
        ["16:00–23:00", "现场演示", "13–14", "验收句 + 记忆 + 过往周报"],
        ["23:00–28:00", "代码地图", "15–16", "评委问“在哪改”"],
        ["28:00–30:00", "测试 / 风险 / 总结 / Q&A", "17–22", "28 项测试 + 诚实边界"],
    ]),
    ("h1", "三、逐段执行细则"),
    ("h2", "① 开场（0–3′）｜ PPT 1–3"),
    ("bullets", [
        "站定、环视再开口；前 30 秒讲“周一早上写周报”的场景故事，再落到目标；",
        "讲“数字必须可信”时放慢，这是全场最重要的价值主张；",
        "翻到第 3 页指左右两栏；翻到第 4 页讲边界时强调“接口先行、独立验收”。",
    ]),
    ("h2", "② 架构与全流程（6–11′）｜ PPT 5–7"),
    ("bullets", [
        "指第 5 页五层图：从上往下，指到哪讲到哪，别跳层；",
        "第 6 页时序：按“登录 → 发句 → 思考 → 工具 → 终稿 → 落库”讲一遍；",
        "第 7 页是评委重点：先指循环，再指三张卡；把“取消互斥”提前埋伏笔（演示时兑现）。",
    ]),
    ("h2", "③ 工具箱与安全（11–14′）｜ PPT 8–9"),
    ("bullets", [
        "工具不用逐个念参数，每个一句话：它是什么、为什么要有护栏；",
        "第 9 页六格用“怕什么挡什么”的句式；最后在金色高亮条讲两个事故——这是报告“问题与解决”的素材；",
        "事故讲法：现象 → 根因 → 修复 → 结论，每则 40 秒以内。",
    ]),
    ("h2", "④ 登录 / 界面 / 观测（14–16′）｜ PPT 10–12"),
    ("bullets", [
        "角色、密码哈希、JWT 快速带过；重点在“会话 = 记忆”“分库 = 隔离”两个概念；",
        "第 12 页强调：事件九类 + 日志 60 天 + 可回放，“可观测 = 可审计”。",
    ]),
    ("h2", "⑤ 现场演示（16–23′）｜ PPT 13–14，浏览器"),
    ("bullets", [
        "切浏览器：登录 ops → 指界面 30 秒 → 粘贴验收句发送；",
        "指着时间线讲：搜索（入参是查询词）→ SQL（入参是语句）→ 计算器 → final；重点句：“销售额来自数据库”；",
        "指右侧预览讲周报结构；同比 +25% 与口径（10 万 / 8 万）念准；",
        "加餐 A（记忆追问，必做）：同会话发送“请沿用刚才周报的标题层级和章节结构，补充一句本周风险提示”；",
        "加餐 B（过往周报，必做）：打开抽屉 → 说明数据在自己的用户分库；",
        "加餐 C（dev 日志，可选）：dev 登录取日志页，按会话指事件与时间戳；",
        "任何一步失败 → 立即切备用（已生成周报 / 录屏），不要现场和故障搏斗超过 20 秒。",
    ]),
    ("h2", "⑥ 代码实现（23–28′）｜ PPT 15–16"),
    ("bullets", [
        "先翻第 15 页讲分库，再按第 16 页表格讲“在哪改”：graph.py → nodes.py → prompts.py → mysql_query.py → chat/runtime → user_store；",
        "不念代码；可切 IDE 指 graph.py 的条件边与 cancel 的终态互斥；",
        "超时可只讲 graph.py 与 user_store.py 两个文件（压到 3 分钟）。",
    ]),
    ("h2", "⑦ 收尾（28–30′）｜ PPT 17–22"),
    ("bullets", [
        "第 17–18 页：28 项测试、验收十项、两次联调复盘——这段是“质量与工程素养”的展示窗口，别跳过；",
        "第 18 页风险诚实说；第 19 页三条价值放慢；第 20 页展望点到为止；第 21 页收尾致谢；",
        "留 2–3 分钟给提问；被问到不会的：翻讲稿附录 A 或如实说“文档里有，会后再确认”。",
    ]),
    ("h1", "四、演示原句与加餐"),
    ("p", "主句（逐字）：帮我搜索2026AI行业新闻，再查询本月销售总额，计算同比增长率，生成一份运营周报markdown"),
    ("p", "记忆加餐（同一会话，逐字）：请沿用刚才周报的标题层级和章节结构，补充一句本周风险提示"),
    ("p", "账号：ops / ops123（主演示）；dev / dev123（日志页）。地址：http://127.0.0.1:8000"),
    ("h1", "五、减配与加餐"),
    ("bullets", [
        "减配（按顺序砍）：演示第 6 步 dev 日志 → 代码段只讲两个文件 → 展望页一句话带过 → 取消演示改口述；",
        "加餐（富余时）：改昵称展示设置；现场跑一句“查询 8 月各区域销售”（演示 SQL 入参变化）；谈一谈 prompt 里“拿到足够信息就停”的调优。",
    ]),
    ("h1", "六、应急预案"),
    ("table", [
        ["故障", "对策"],
        ["模型 / 搜索导致 30s 超时", "说明“超时会明说、不编造”，立即切备用：reports/weekly-ops.md 或录屏"],
        ["Tavily 未配置 / 失败", "工具返回明确错误；周报写明“未检索到公开新闻”，顺着讲“不编造”设计"],
        ["MySQL 掉线", "临时 USE_MOCK_DB=true 重启（数据在本地 mock），或口述 mock 机制展示周报结构"],
        ["端口被占", "换 8001 启动并同步改浏览器地址；或用已打开的旧标签页"],
        ["页面样式 / 身份异常", "Ctrl+F5 硬刷新；确认未启用代理插件拦截本地请求"],
        ["取消按钮演示失败", "不现场反复点；改为口述“终态互斥”→ 指第 7 页卡片"],
    ]),
    ("h1", "七、交流预案（高频提问速查）"),
    ("table", [
        ["问题", "回答要点"],
        ["为什么用 LangGraph", "多步循环 + 条件结束 + 轮次 / 取消控制 + 状态可审计"],
        ["怎么防胡编数字", "强制查库 + 提示词禁编造 + 时间线公开 SQL 入参 / 返回"],
        ["8 轮 / 30s 依据", "硬止损配置；防死循环与挂死；演示用短任务适配"],
        ["SQL 安全", "select 白名单 + 9 词黑名单 + 禁多语句 + 失败自纠回传"],
        ["完成后的取消", "终态互斥：拒绝改写，保持原状态"],
        ["为什么分库", "隔离 / 审计；销售业务库与用户数据分离"],
        ["KB 没上线的集成", "接口先行（工具名 / 开关 / Stub / HTTP 契约），独立验收"],
        ["MemorySaver 局限", "进程内；重启丢图状态；日志周报在库；升级 Postgres 即可"],
    ]),
    ("h1", "八、事实速查（数字口径）"),
    ("table", [
        ["要点", "数值 / 口径"],
        ["种子数据", "本月 100,000；去年同月 80,000；同比 +25.0%"],
        ["硬限制", "≤8 轮工具；30s 超时；失败重试 1 次；SQL 黑名单 9 词；日志 60 天"],
        ["测试", "28 个 pytest 用例全部通过（mock，约 4.5s）"],
        ["事件类型", "thought / tool_call / tool_result / final / error / cancelled / max_rounds / timeout"],
        ["备用素材", "reports/weekly-ops.md（真实联调产物）"],
    ]),
    ("p", "—— 执行说明结束。演示成功的关键：提前干跑一遍、备用素材随手可切、数字口径背熟。"),
]


def _render_runbook(font: str):
    st = _pdf_styles(font)
    doc = SimpleDocTemplate(str(RUNBOOK_PDF), pagesize=A4, leftMargin=1.8 * cm,
                            rightMargin=1.8 * cm, topMargin=1.7 * cm, bottomMargin=1.8 * cm)
    story = []
    story.append(Paragraph("第 4 部分 · 报告执行说明（自用，不要念）", st["title"]))
    story.append(Paragraph("配套：汇报.pptx（22 页）· 演讲稿.pdf（≈30′）｜本文件给汇报人控场使用", st["meta"]))
    tw = A4[0] - 3.6 * cm
    for kind, payload in RUNBOOK:
        if kind == "h1":
            story.append(Paragraph(payload, st["h1"]))
        elif kind == "h2":
            story.append(Paragraph(payload, st["h2"]))
        elif kind == "p":
            story.append(Paragraph(payload, st["body"]))
        elif kind == "bullets":
            for item in payload:
                story.append(Paragraph("·　" + item, st["body"]))
        elif kind == "table":
            rows = payload
            n = len(rows[0])
            w0 = 4.2 * cm if n == 4 else 5.2 * cm
            rest = (tw - w0) / (n - 1)
            data = []
            for ri, row in enumerate(rows):
                line = []
                for cell in row:
                    style = st["body"] if ri else ParagraphStyle(
                        "th", parent=st["body"], textColor=HexColor("#FFFFFF"),
                        fontSize=9.5)
                    line.append(Paragraph(cell, ParagraphStyle(
                        "cell", parent=style, fontSize=9.5, leading=13, spaceAfter=0)))
                data.append(line)
            tbl = Table(data, colWidths=[w0] + [rest] * (n - 1))
            tbl.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), HexColor("#1B2A4A")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#FFFFFF"), HexColor("#F2F5FA")]),
                ("GRID", (0, 0), (-1, -1), 0.4, HexColor("#D8DFEA")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]))
            story.append(tbl)
            story.append(Spacer(1, 6))

    def foot(canvas, d):
        fname = "CN" if "CN" in _registered_fonts() else "Helvetica"
        canvas.saveState()
        canvas.setFont(fname, 8)
        canvas.setFillColor(HexColor("#8A94A6"))
        canvas.drawString(1.8 * cm, 1.0 * cm, "第 4 部分 · 报告执行说明 · 自用")
        canvas.drawRightString(A4[0] - 1.8 * cm, 1.0 * cm, f"第 {d.page} 页")
        canvas.restoreState()

    doc.build(story, onFirstPage=foot, onLaterPages=foot)
    return RUNBOOK_PDF


def _write_runbook_md() -> Path:
    lines = ["# 第 4 部分 · 报告执行说明（自用，不要念）", "",
             "> 配套：`汇报.pptx`（22 页）· `演讲稿.pdf`（≈30′）。本文件给汇报人控场，不对听众朗读。", ""]
    for kind, payload in RUNBOOK:
        if kind == "h1":
            lines += [f"## {payload}", ""]
        elif kind == "h2":
            lines += [f"### {payload}", ""]
        elif kind == "p":
            lines += [payload, ""]
        elif kind == "bullets":
            lines += [f"- {item}" for item in payload] + [""]
        elif kind == "table":
            rows = payload
            lines.append("| " + " | ".join(rows[0]) + " |")
            lines.append("| " + " | ".join(["---"] * len(rows[0])) + " |")
            for row in rows[1:]:
                lines.append("| " + " | ".join(row) + " |")
            lines.append("")
    RUNBOOK_MD.write_text("\n".join(lines), encoding="utf-8")
    return RUNBOOK_MD


def main():
    font = _register_font()
    if font == "CN":
        _registered_cache.append("CN")
    pptx_path = build_pptx()
    speech = build_speech_pdf()
    runbook = _render_runbook(font)
    runbook_md = _write_runbook_md()
    print("OK")
    print("PPT   :", pptx_path)
    print("Speech:", speech)
    print("Runbook:", runbook)
    print("Runbook md:", runbook_md)


if __name__ == "__main__":
    main()
