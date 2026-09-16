"""知识库工具：Stub 不编造内容；HTTP 客户端解析 citations。"""

import httpx

from app.config import get_settings
from app.tools.kb import HttpKnowledgeBaseClient, StubKnowledgeBaseClient, query_enterprise_kb


def test_stub_does_not_invent_business_content():
    """Stub 应 hit=false 且固定「未接入」文案，无 citations。"""
    hit = StubKnowledgeBaseClient().query("公司差旅标准是什么")
    assert hit.hit is False
    assert hit.answer == "当前未接入企业内部知识库"
    assert hit.citations == []


def test_default_query_uses_stub():
    """KB_ENABLED=false 时 query_enterprise_kb 走 Stub。"""
    get_settings.cache_clear()
    hit = query_enterprise_kb("内部制度")
    assert hit.hit is False
    assert "未接入" in hit.answer


def test_http_client_parses_citations(monkeypatch):
    """KB_ENABLED=true 时 HTTP 客户端应解析 answer/hit/citations。"""
    monkeypatch.setenv("KB_ENABLED", "true")
    monkeypatch.setenv("KB_BASE_URL", "http://kb.example")
    get_settings.cache_clear()

    def fake_post(url, json, headers, timeout):
        request = httpx.Request("POST", url)
        return httpx.Response(
            200,
            json={
                "answer": "差旅上限 800 元",
                "hit": True,
                "citations": [
                    {"doc_name": "差旅制度.pdf", "page": 3, "snippet": "住宿上限 800"}
                ],
            },
            request=request,
        )

    monkeypatch.setattr("app.tools.kb.httpx.post", fake_post)
    hit = HttpKnowledgeBaseClient().query("差旅")
    assert hit.hit is True
    assert hit.citations[0].doc_name == "差旅制度.pdf"
    assert hit.citations[0].page == 3
    get_settings.cache_clear()
