from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    organization_name: str = Field(min_length=2, max_length=120)
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)
    organization_slug: str | None = Field(default=None, max_length=80)


class UserProfile(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    organization_id: str
    organization_name: str
    organization_slug: str
    role: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserProfile


class RoleUpdateRequest(BaseModel):
    role: str = Field(pattern="^(owner|admin|on_call|viewer)$")


class MemberRead(BaseModel):
    user_id: str
    email: EmailStr
    full_name: str
    role: str
