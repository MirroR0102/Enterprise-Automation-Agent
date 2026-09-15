# 验收记录

目标句：

`帮我搜索2026AI行业新闻，再查询本月销售总额，计算同比增长率，生成一份运营周报markdown`

在已配置 `DEEPSEEK_API_KEY`（及可选 `TAVILY_API_KEY`）时：

1. `python scripts/init_db.py`
2. `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000`
3. 浏览器打开 http://127.0.0.1:8000/login.html ，用 `ops` / `ops123` 登录
4. 发送验收句
5. 时间线应出现搜索 / mysql_query / calculator（写入 reports/*.md 可选）
6. 最终面板渲染完整 Markdown 周报
7. 点取消可终止进行中的任务
8. 用 `dev` / `dev123` 打开 `/logs.html` 能看到工具入参与返回
9. `pytest -q` 全绿（不依赖真实 DeepSeek/Tavily/MySQL）

无 Tavily 时，搜索工具会返回配置错误文案，Agent 应说明原因而不是编造新闻。
无 DeepSeek 时，页面任务会失败；单测仍可全部通过。
