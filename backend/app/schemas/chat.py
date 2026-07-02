from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field

from app.schemas.company import CompanyProfile
from app.schemas.synthesis import SynthesisResult


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class SessionEvent(BaseModel):
    type: Literal["session"] = "session"
    session_id: str


class StepEvent(BaseModel):
    type: Literal["step"] = "step"
    node: str
    status: Literal["started", "completed"]
    used_demo: bool = False
    summary: str = ""


class ResultEvent(BaseModel):
    type: Literal["result"] = "result"
    intent: str
    payload: SynthesisResult | CompanyProfile | dict
    demo_flags: dict[str, bool]


class ErrorEvent(BaseModel):
    type: Literal["error"] = "error"
    node: str
    message: str


class DoneEvent(BaseModel):
    type: Literal["done"] = "done"


ChatStreamEvent = Annotated[
    Union[SessionEvent, StepEvent, ResultEvent, ErrorEvent, DoneEvent],
    Field(discriminator="type"),
]


class ChatMessageOut(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    intent: str | None = None
    used_demo_data: bool = False
    created_at: str


class ChatHistoryResponse(BaseModel):
    session_id: str
    messages: list[ChatMessageOut]
