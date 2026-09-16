"""智能体 LangGraph 状态定义：消息、会话、工具轮次与事件流。"""

from typing import Annotated, Any, Literal, TypedDict

from langgraph.graph.message import add_messages

# 任务生命周期状态枚举
Status = Literal["running", "completed", "failed", "cancelled", "timeout", "max_rounds"]


class AgentState(TypedDict, total=False):
    """图节点间共享的状态；messages 使用 add_messages  reducer 追加。"""

    messages: Annotated[list, add_messages]
    session_id: str
    user_id: int
    tool_round: int
    status: Status
    events: list[dict[str, Any]]
    last_error: str
