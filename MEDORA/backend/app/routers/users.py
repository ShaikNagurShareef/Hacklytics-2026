"""User routes: profile (me), profile update, chat history."""
from fastapi import APIRouter, Depends, HTTPException

from app.db.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.chat import ChatSession
from app.schemas.auth import (
    UserResponse,
    UserUpdate,
    ChatSessionListItem,
    ChatSessionDetail,
    ChatMessageOut,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
def get_me(user: User = Depends(get_current_user)):
    return user


@router.patch("/me", response_model=UserResponse)
def update_me(update: UserUpdate, user: User = Depends(get_current_user), db=Depends(get_db)):
    if update.full_name is not None:
        user.full_name = update.full_name.strip() or None
    db.commit()
    db.refresh(user)
    return user


@router.get("/me/chats", response_model=list[ChatSessionListItem])
def list_my_chats(user: User = Depends(get_current_user), db=Depends(get_db)):
    sessions = (
        db.query(ChatSession)
        .filter(ChatSession.user_id == user.id)
        .order_by(ChatSession.updated_at.desc())
        .all()
    )
    return sessions


@router.get("/me/chats/{client_session_id}", response_model=ChatSessionDetail)
def get_my_chat(client_session_id: str, user: User = Depends(get_current_user), db=Depends(get_db)):
    session = (
        db.query(ChatSession)
        .filter(
            ChatSession.user_id == user.id,
            ChatSession.client_session_id == client_session_id,
        )
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Chat not found")
    messages = [
        ChatMessageOut(role=m.role, content=m.content, agent_name=m.agent_name, created_at=m.created_at)
        for m in session.messages
    ]
    return ChatSessionDetail(
        id=session.id,
        client_session_id=session.client_session_id,
        title=session.title,
        agent_type=session.agent_type,
        created_at=session.created_at,
        updated_at=session.updated_at,
        messages=messages,
    )
