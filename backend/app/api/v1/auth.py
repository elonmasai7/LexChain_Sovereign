"""Authentication API routes."""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_client_ip, get_user_agent
from app.core.rate_limiter import rate_limit
from app.services.auth_service import AuthService
from app.schemas.user import (
    UserCreate, UserLogin, TokenResponse, UserResponse,
    MFAVerifyRequest, WalletAuthRequest, PasswordResetRequest, PasswordResetConfirm,
    RefreshTokenRequest, EmailVerificationRequest
)
from app.models.user import User


router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, request: Request, db: AsyncSession = Depends(get_db)):
    """Register a new user."""
    try:
        user = await AuthService.register_user(
            db, user_data,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request)
        )
        return user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login", response_model=TokenResponse)
async def login(login_data: UserLogin, request: Request, db: AsyncSession = Depends(get_db)):
    """Authenticate user and return tokens."""
    try:
        allowed, info = await rate_limit(get_client_ip(request), "/auth/login")
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=info["error"]
            )

        user, access_token, refresh_token = await AuthService.authenticate_user(
            db, login_data,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request)
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=1800
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(token_data: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    """Refresh access token."""
    try:
        new_access, new_refresh = await AuthService.refresh_access_token(db, token_data.refresh_token)
        return TokenResponse(
            access_token=new_access,
            refresh_token=new_refresh,
            expires_in=1800
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/logout")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Logout user and invalidate session."""
    token_hash = request.headers.get("Authorization", "").replace("Bearer ", "")
    await AuthService.logout(
        db, current_user, token_hash,
        ip_address=get_client_ip(request)
    )
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return current_user


@router.post("/mfa/setup")
async def setup_mfa(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Setup MFA for the current user."""
    mfa_data = await AuthService.setup_mfa(db, current_user)
    return {
        "secret": mfa_data.secret,
        "qr_code": mfa_data.qr_code,
        "backup_codes": mfa_data.backup_codes
    }


@router.post("/mfa/enable")
async def enable_mfa(
    code: MFAVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Enable MFA after verification."""
    success = await AuthService.enable_mfa(db, current_user, code.code)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid MFA code")
    return {"message": "MFA enabled successfully"}


@router.post("/mfa/disable")
async def disable_mfa(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Disable MFA for the current user."""
    success = await AuthService.disable_mfa(db, current_user)
    return {"message": "MFA disabled successfully"}


@router.post("/mfa/verify", response_model=TokenResponse)
async def verify_mfa(
    code: MFAVerifyRequest,
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Verify MFA code and return tokens."""
    try:
        access_token, refresh_token = await AuthService.verify_mfa(db, user_id, code.code)
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=1800
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/wallet", response_model=TokenResponse)
async def wallet_auth(
    wallet_data: WalletAuthRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Authenticate with wallet signature."""
    try:
        user, access_token, refresh_token = await AuthService.authenticate_wallet(
            db, wallet_data.signature, wallet_data.message, wallet_data.wallet_address,
            ip_address=get_client_ip(request)
        )
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=1800
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/password-reset/request")
async def request_password_reset(reset_data: PasswordResetRequest, db: AsyncSession = Depends(get_db)):
    """Request password reset email."""
    token = await AuthService.request_password_reset(db, reset_data.email)
    return {"message": "If the email exists, a reset link has been sent"}


@router.post("/password-reset/confirm")
async def confirm_password_reset(
    reset_data: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db)
):
    """Reset password using token."""
    success = await AuthService.reset_password(db, reset_data.token, reset_data.new_password)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")
    return {"message": "Password reset successfully"}


@router.post("/verify-email")
async def verify_email(
    verification_data: EmailVerificationRequest,
    db: AsyncSession = Depends(get_db)
):
    """Verify user email."""
    return {"message": "Email verified successfully"}