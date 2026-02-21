"""Persist chat history for authenticated users."""
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.chat import ChatSession, ChatMessage


def get_or_create_session(
    db: Session,
    user_id: int,
    client_session_id: str,
    agent_type: str | None = None,
    first_user_message: str | None = None,
) -> ChatSession:
    session = (
        db.query(ChatSession)
        .filter(
            ChatSession.user_id == user_id,
            ChatSession.client_session_id == client_session_id,
        )
        .first()
    )
    if session:
        return session
    title = (first_user_message or "New chat")[:255] if first_user_message else "New chat"
    session = ChatSession(
        user_id=user_id,
        client_session_id=client_session_id,
        title=title,
        agent_type=agent_type,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def append_turn(
    db: Session,
    user_id: int,
    client_session_id: str,
    user_query: str,
    assistant_content: str,
    agent_name: str,
    agent_type: str | None = None,
) -> None:
    session = get_or_create_session(
        db, user_id, client_session_id,
        agent_type=agent_type,
        first_user_message=user_query,
    )
    # Update title only if still default
    if session.title == "New chat" and user_query:
        session.title = user_query[:255]
    session.updated_at = datetime.utcnow()
    for role, content, name in [
        ("user", user_query, None),
        ("assistant", assistant_content, agent_name),
    ]:
        msg = ChatMessage(
            session_id=session.id,
            role=role,
            content=content,
            agent_name=name,
        )
        db.add(msg)
    db.commit()
