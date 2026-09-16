"""企业内部知识库客户端：未配置时返回 stub，已配置则走 HTTP QA 接口。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

import httpx

from app.config import get_settings


@dataclass
class Citation:
    """知识库引用片段。"""

    doc_name: str
    page: int | str | None = None
    snippet: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {"doc_name": self.doc_name, "page": self.page, "snippet": self.snippet}


@dataclass
class KnowledgeHit:
    """知识库查询结果。"""

    answer: str
    citations: list[Citation] = field(default_factory=list)
    hit: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "answer": self.answer,
            "citations": [c.as_dict() for c in self.citations],
            "hit": self.hit,
            "stub": not get_settings().kb_enabled,
        }


class KnowledgeBaseClient(Protocol):
    """知识库客户端协议。"""

    def query(
        self,
        question: str,
        top_k: int = 5,
        session_id: str | None = None,
    ) -> KnowledgeHit: ...


class StubKnowledgeBaseClient:
    """未接入知识库时的占位实现，固定返回未接入提示。"""

    def query(
        self,
        question: str,
        top_k: int = 5,
        session_id: str | None = None,
    ) -> KnowledgeHit:
        return KnowledgeHit(
            answer="当前未接入企业内部知识库",
            citations=[],
            hit=False,
        )


class HttpKnowledgeBaseClient:
    """通过 HTTP 调用外部知识库 QA 服务。"""

    def query(
        self,
        question: str,
        top_k: int = 5,
        session_id: str | None = None,
    ) -> KnowledgeHit:
        settings = get_settings()
        if not settings.kb_base_url:
            raise RuntimeError("KB_ENABLED=true 但未配置 KB_BASE_URL")
        url = settings.kb_base_url.rstrip("/") + "/api/v1/qa"
        headers = {"Content-Type": "application/json"}
        if settings.kb_api_key:
            headers["Authorization"] = f"Bearer {settings.kb_api_key}"
        payload = {"question": question, "top_k": top_k}
        if session_id:
            payload["session_id"] = session_id
        try:
            response = httpx.post(
                url,
                json=payload,
                headers=headers,
                timeout=settings.kb_timeout_s,
            )
            response.raise_for_status()
            data = response.json()
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"知识库请求失败: {exc}") from exc
        citations = []
        for item in data.get("citations") or []:
            citations.append(
                Citation(
                    doc_name=item.get("doc_name") or item.get("source") or "",
                    page=item.get("page"),
                    snippet=item.get("snippet") or "",
                )
            )
        hit = bool(data.get("hit", bool(data.get("answer"))))
        return KnowledgeHit(
            answer=str(data.get("answer") or ""),
            citations=citations,
            hit=hit,
        )


def get_kb_client() -> KnowledgeBaseClient:
    """按 KB_ENABLED 选择 HTTP 客户端或 stub。"""
    if get_settings().kb_enabled:
        return HttpKnowledgeBaseClient()
    return StubKnowledgeBaseClient()


def query_enterprise_kb(question: str, top_k: int = 5, session_id: str | None = None) -> KnowledgeHit:
    """查询企业知识库的统一入口。"""
    return get_kb_client().query(question=question, top_k=top_k, session_id=session_id)
