"""Pydantic schemas for auth and user."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class SignUpRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    full_name: Optional[str] = None


# Chat history (for /users/me/chats)
class ChatMessageOut(BaseModel):
    role: str
    content: str
    agent_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ChatSessionListItem(BaseModel):
    id: int
    client_session_id: str
    title: Optional[str] = None
    agent_type: Optional[str] = None
    updated_at: datetime

    class Config:
        from_attributes = True


class ChatSessionDetail(BaseModel):
    id: int
    client_session_id: str
    title: Optional[str] = None
    agent_type: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    messages: list[ChatMessageOut] = []

    class Config:
        from_attributes = True
