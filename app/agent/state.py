from typing import Annotated, Any, Literal, TypedDict

from langgraph.graph.message import add_messages

Status = Literal["running", "completed", "failed", "cancelled", "timeout", "max_rounds"]


class AgentState(TypedDict, total=False):
    messages: Annotated[list, add_messages]
    session_id: str
    user_id: int
    tool_round: int
    status: Status
    events: list[dict[str, Any]]
    last_error: str
