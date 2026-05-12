"""User-related Pydantic schemas."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator
from app.core.validation import InputValidator


class UserCreate(BaseModel):
    """Schema for user registration."""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = Field(None, max_length=255)
    company: Optional[str] = Field(None, max_length=255)
    jurisdiction: Optional[str] = Field(None, max_length=100)
    wallet_address: Optional[str] = None

    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        is_valid, message = InputValidator.validate_username(v)
        if not is_valid:
            raise ValueError(message)
        return v

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        is_valid, message = InputValidator.validate_password(v)
        if not is_valid:
            raise ValueError(message)
        return v

    @field_validator('wallet_address')
    @classmethod
    def validate_wallet(cls, v):
        if v:
            if not InputValidator.validate_wallet_address(v):
                raise ValueError("Invalid wallet address format")
        return v


class UserUpdate(BaseModel):
    """Schema for updating user profile."""
    full_name: Optional[str] = Field(None, max_length=255)
    company: Optional[str] = Field(None, max_length=255)
    jurisdiction: Optional[str] = Field(None, max_length=100)
    wallet_address: Optional[str] = None

    @field_validator('wallet_address')
    @classmethod
    def validate_wallet(cls, v):
        if v and not InputValidator.validate_wallet_address(v):
            raise ValueError("Invalid wallet address format")
        return v


class UserResponse(BaseModel):
    """User response schema."""
    id: str
    email: str
    username: str
    role: str
    is_active: bool
    is_verified: bool
    full_name: Optional[str] = None
    company: Optional[str] = None
    jurisdiction: Optional[str] = None
    wallet_address: Optional[str] = None
    did: Optional[str] = None
    mfa_enabled: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class UserLogin(BaseModel):
    """Login request schema."""
    email: EmailStr
    password: str
    remember_me: bool = False


class TokenResponse(BaseModel):
    """JWT token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class MFASetupResponse(BaseModel):
    """MFA setup response."""
    secret: str
    qr_code: str
    backup_codes: list[str]


class MFAVerifyRequest(BaseModel):
    """MFA verification request."""
    code: str = Field(..., min_length=6, max_length=6)


class WalletAuthRequest(BaseModel):
    """Wallet authentication request."""
    signature: str
    message: str
    wallet_address: str

    @field_validator('wallet_address')
    @classmethod
    def validate_wallet(cls, v):
        if not InputValidator.validate_wallet_address(v):
            raise ValueError("Invalid wallet address format")
        return v


class PasswordResetRequest(BaseModel):
    """Password reset request."""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation."""
    token: str
    new_password: str

    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v):
        is_valid, message = InputValidator.validate_password(v)
        if not is_valid:
            raise ValueError(message)
        return v


class EmailVerificationRequest(BaseModel):
    """Email verification request."""
    token: str


class RefreshTokenRequest(BaseModel):
    """Token refresh request."""
    refresh_token: str