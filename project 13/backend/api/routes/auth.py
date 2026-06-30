from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from db.supabase_client import get_user_by_email, get_user_by_id, list_users, LOCAL_USERS

router = APIRouter(prefix="/api/auth", tags=["auth"])
security = HTTPBearer(auto_error=False)


class LoginRequest(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str


class LoginResponse(BaseModel):
    token: str
    user: UserResponse


class CreateUserRequest(BaseModel):
    email: str
    password: str
    name: str
    role: str


class UpdateUserRequest(BaseModel):
    name: str | None = None
    role: str | None = None


class AuthPayload(BaseModel):
    sub: str
    role: str
    name: str
    exp: float


def _get_jwt_secret() -> str:
    return os.getenv("JWT_SECRET", "dev-jwt-secret-change-me")


def _create_token(user_id: str, role: str, name: str) -> str:
    secret = _get_jwt_secret()
    payload = {
        "sub": user_id,
        "role": role,
        "name": name,
        "exp": datetime.now(timezone.utc) + timedelta(days=7),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    secret = _get_jwt_secret()
    try:
        payload = jwt.decode(credentials.credentials, secret, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict | None:
    if credentials is None:
        return None
    secret = _get_jwt_secret()
    try:
        return jwt.decode(credentials.credentials, secret, algorithms=["HS256"])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


def require_role(allowed_roles: list[str]):
    async def role_checker(current_user: dict = Depends(get_current_user)) -> dict:
        if current_user.get("role") not in allowed_roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return role_checker


@router.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest) -> LoginResponse:
    user = await get_user_by_email(req.email)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    stored_hash = user.get("password_hash", "")
    if isinstance(stored_hash, str):
        stored_hash = stored_hash.encode("utf-8")

    if not bcrypt.checkpw(req.password.encode("utf-8"), stored_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = _create_token(user["id"], user["role"], user["name"])
    return LoginResponse(
        token=token,
        user=UserResponse(
            id=user["id"],
            email=user["email"],
            name=user["name"],
            role=user["role"],
        ),
    )


@router.get("/me", response_model=UserResponse)
async def me(current_user: dict = Depends(get_current_user)) -> UserResponse:
    user = await get_user_by_id(current_user["sub"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(
        id=user["id"],
        email=user["email"],
        name=user["name"],
        role=user["role"],
    )


@router.get("/users", response_model=list[UserResponse])
async def get_users(current_user: dict = Depends(require_role(["admin", "manager"]))) -> list[UserResponse]:
    users = await list_users()
    return [
        UserResponse(id=u["id"], email=u["email"], name=u["name"], role=u["role"])
        for u in users
    ]


@router.post("/users", response_model=UserResponse, status_code=201)
async def create_user(
    req: CreateUserRequest,
    current_user: dict = Depends(require_role(["admin"])),
) -> UserResponse:
    existing = await get_user_by_email(req.email)
    if existing:
        raise HTTPException(status_code=409, detail="A user with this email already exists")

    if req.role not in ("admin", "manager", "rep"):
        raise HTTPException(status_code=400, detail="Role must be admin, manager, or rep")

    hashed = bcrypt.hashpw(req.password.encode("utf-8"), bcrypt.gensalt())
    if isinstance(hashed, bytes):
        hashed = hashed.decode("utf-8")

    user_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    from db.supabase_client import LOCAL_USERS

    LOCAL_USERS[req.email] = {
        "id": user_id,
        "email": req.email,
        "password_hash": hashed,
        "name": req.name,
        "role": req.role,
        "created_at": now,
    }

    sb = None
    try:
        from supabase import create_client
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_ANON_KEY")
        if url and key and "your-project" not in url:
            sb = create_client(url, key)
    except Exception:
        sb = None

    if sb:
        from db.supabase_client import _safe_execute
        _safe_execute(
            lambda: sb.table("users").insert({
                "id": user_id,
                "email": req.email,
                "password_hash": hashed,
                "name": req.name,
                "role": req.role,
            }).execute(),
            label="create_user",
        )

    return UserResponse(id=user_id, email=req.email, name=req.name, role=req.role)


@router.patch("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    req: UpdateUserRequest,
    current_user: dict = Depends(require_role(["admin"])),
) -> UserResponse:
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if req.role is not None and req.role not in ("admin", "manager", "rep"):
        raise HTTPException(status_code=400, detail="Role must be admin, manager, or rep")

    from db.supabase_client import LOCAL_USERS

    for email, u in LOCAL_USERS.items():
        if u["id"] == user_id:
            if req.name is not None:
                LOCAL_USERS[email]["name"] = req.name
            if req.role is not None:
                LOCAL_USERS[email]["role"] = req.role
            break

    if current_user.get("sub") == user_id:
        raise HTTPException(status_code=400, detail="Cannot update your own role via this endpoint")

    sb = None
    try:
        from supabase import create_client
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_ANON_KEY")
        if url and key and "your-project" not in url:
            sb = create_client(url, key)
    except Exception:
        sb = None

    if sb:
        from db.supabase_client import _safe_execute
        payload: dict = {}
        if req.name is not None:
            payload["name"] = req.name
        if req.role is not None:
            payload["role"] = req.role
        if payload:
            _safe_execute(
                lambda: sb.table("users").update(payload).eq("id", user_id).execute(),
                label="update_user",
            )

    updated = await get_user_by_id(user_id)
    return UserResponse(
        id=updated["id"],
        email=updated["email"],
        name=updated["name"],
        role=updated["role"],
    )


@router.delete("/users/{user_id}", status_code=204)
async def delete_user(
    user_id: str,
    current_user: dict = Depends(require_role(["admin"])),
) -> Response:
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if current_user.get("sub") == user_id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")

    from db.supabase_client import LOCAL_USERS

    emails_to_remove = [email for email, u in LOCAL_USERS.items() if u["id"] == user_id]
    for email in emails_to_remove:
        del LOCAL_USERS[email]

    sb = None
    try:
        from supabase import create_client
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_ANON_KEY")
        if url and key and "your-project" not in url:
            sb = create_client(url, key)
    except Exception:
        sb = None

    if sb:
        from db.supabase_client import _safe_execute
        _safe_execute(
            lambda: sb.table("users").delete().eq("id", user_id).execute(),
            label="delete_user",
        )

    return Response(status_code=204)
