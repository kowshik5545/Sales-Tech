from __future__ import annotations

from fastapi import APIRouter, Depends

from api.routes.auth import get_current_user, optional_user
from db.supabase_client import list_sessions
from models.schemas import SessionSummary

router = APIRouter(prefix="/api", tags=["sessions"])


@router.get("/sessions", response_model=list[SessionSummary])
async def get_sessions(current_user: dict | None = Depends(optional_user)) -> list[SessionSummary]:
    role = current_user.get("role") if current_user else None
    uid = current_user.get("sub") if current_user else None
    return await list_sessions(user_role=role, user_id=uid)
