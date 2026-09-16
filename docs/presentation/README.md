# 本地汇报材料（不推送 GitHub）

本目录存放第 4 部分 30 分钟汇报交付物：

| 文件 | 说明 |
| --- | --- |
| `第4部分-企业业务流程自动化Agent-汇报.pptx` | 演示用幻灯片 |
| `第4部分-企业业务流程自动化Agent-演讲稿.pdf` | 口语完整演讲稿 |

生成脚本：`scripts/build_presentation.py`  
大纲规格：`2026-09-15-part4-30min-presentation-outline.md`

## 维护约定（重要）

项目**尚未完全定稿**。每当出现重要改动（架构、验收口径、安全止损、演示账号/验收句、第 3 部分接口、联调问题结论等），必须同步更新：

1. 本目录下的 **PPTX** 与 **PDF**（可改脚本后重跑 `python scripts/build_presentation.py`，或直接改成品）
2. 若结构变了：根目录大纲 md
3. `README.md` 与 `AGENT.md` 中的演示材料说明

`.pptx` / `.pdf` 已在 `.gitignore` 中，**默认不 push**。
