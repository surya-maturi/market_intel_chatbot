from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import ChatMessage, ChatSession


def create_session(db: Session) -> ChatSession:
    session = ChatSession()
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_or_create_session(db: Session, session_id: str | None) -> ChatSession:
    if session_id:
        existing = db.get(ChatSession, session_id)
        if existing:
            return existing
    return create_session(db)


def save_message(
    db: Session,
    session_id: str,
    role: str,
    content: str,
    intent: str | None = None,
    used_demo_data: bool = False,
) -> ChatMessage:
    message = ChatMessage(
        session_id=session_id,
        role=role,
        content=content,
        intent=intent,
        used_demo_data=used_demo_data,
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def get_history(db: Session, session_id: str, limit: int = 100) -> list[ChatMessage]:
    result = db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .limit(limit)
    )
    return list(result.scalars().all())
