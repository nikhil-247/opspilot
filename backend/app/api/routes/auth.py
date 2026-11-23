import re
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import UserContext, get_current_context, require_roles
from app.core.config import settings
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models import Membership, Organization, User
from app.schemas.auth import (
    LoginRequest,
    MemberRead,
    RegisterRequest,
    RoleUpdateRequest,
    TokenResponse,
    UserProfile,
)

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])


def _profile(db: Session, user: User, membership: Membership) -> UserProfile:
    organization = db.get(Organization, membership.organization_id)
    if organization is None:
        raise HTTPException(status_code=500, detail="Organization record is missing")
    return UserProfile(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        organization_id=organization.id,
        organization_name=organization.name,
        organization_slug=organization.slug,
        role=membership.role,
    )


def _token_response(db: Session, user: User, membership: Membership) -> TokenResponse:
    return TokenResponse(
        access_token=create_access_token(
            user_id=user.id,
            organization_id=membership.organization_id,
            role=membership.role,
        ),
        expires_in=settings.access_token_expire_minutes * 60,
        user=_profile(db, user, membership),
    )


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    email = str(payload.email).lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="An account with this email already exists")

    slug_base = re.sub(r"[^a-z0-9]+", "-", payload.organization_name.lower()).strip("-")[:60]
    slug = f"{slug_base or 'workspace'}-{uuid4().hex[:6]}"
    now = datetime.now(timezone.utc)
    organization = Organization(name=payload.organization_name.strip(), slug=slug, created_at=now)
    user = User(
        email=email,
        full_name=payload.full_name.strip(),
        password_hash=hash_password(payload.password),
        is_active=True,
        created_at=now,
    )
    db.add_all([organization, user])
    db.flush()
    membership = Membership(
        user_id=user.id,
        organization_id=organization.id,
        role="owner",
        created_at=now,
    )
    db.add(membership)
    db.commit()
    db.refresh(user)
    db.refresh(membership)
    return _token_response(db, user, membership)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    email = str(payload.email).lower()
    user = db.scalar(select(User).where(User.email == email))
    if user is None or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Email or password is incorrect")

    memberships = list(
        db.scalars(
            select(Membership).where(Membership.user_id == user.id).order_by(Membership.created_at)
        ).all()
    )
    if payload.organization_slug:
        matches = []
        for membership in memberships:
            organization = db.get(Organization, membership.organization_id)
            if organization is not None and organization.slug == payload.organization_slug:
                matches.append(membership)
        memberships = matches
    if not memberships:
        raise HTTPException(status_code=403, detail="No membership found for this workspace")
    return _token_response(db, user, memberships[0])


@router.get("/me", response_model=UserProfile)
def me(
    context: UserContext = Depends(get_current_context),
    db: Session = Depends(get_db),
) -> UserProfile:
    user = db.get(User, context.user_id)
    membership = db.scalar(
        select(Membership).where(
            Membership.user_id == context.user_id,
            Membership.organization_id == context.organization_id,
        )
    )
    if user is None or membership is None:
        raise HTTPException(status_code=401, detail="Account is no longer active")
    return _profile(db, user, membership)


@router.get("/members", response_model=list[MemberRead])
def list_members(
    context: UserContext = Depends(get_current_context),
    db: Session = Depends(get_db),
) -> list[MemberRead]:
    rows = db.execute(
        select(User, Membership)
        .join(Membership, Membership.user_id == User.id)
        .where(Membership.organization_id == context.organization_id)
        .order_by(User.full_name)
    ).all()
    return [
        MemberRead(user_id=user.id, email=user.email, full_name=user.full_name, role=membership.role)
        for user, membership in rows
    ]


@router.patch("/members/{user_id}/role", response_model=MemberRead)
def update_member_role(
    user_id: str,
    payload: RoleUpdateRequest,
    context: UserContext = Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> MemberRead:
    if user_id == context.user_id:
        raise HTTPException(status_code=400, detail="You cannot change your own role")
    membership = db.scalar(
        select(Membership).where(
            Membership.user_id == user_id,
            Membership.organization_id == context.organization_id,
        )
    )
    if membership is None:
        raise HTTPException(status_code=404, detail="Organization member not found")
    if membership.role == "owner" and context.role != "owner":
        raise HTTPException(status_code=403, detail="Only an owner can change another owner's role")
    if payload.role == "owner" and context.role != "owner":
        raise HTTPException(status_code=403, detail="Only an owner can grant the owner role")
    membership.role = payload.role
    db.commit()
    user = db.get(User, user_id)
    return MemberRead(
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=membership.role,
    )
