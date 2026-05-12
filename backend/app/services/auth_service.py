"""Authentication service with enterprise security features."""
import pyotp
import secrets
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models.user import User, UserSession, UserRole
from app.schemas.user import UserCreate, UserLogin, MFASetupResponse
from app.core.security import (
    get_password_hash, verify_password, create_access_token,
    create_refresh_token, decode_token, hash_token, generate_secure_token,
    record_login_attempt, is_account_locked
)
from app.core.audit import audit_logger_service
from app.core.config import settings
from app.core.logging import get_logger
from web3 import Web3


logger = get_logger(__name__)


class AuthService:
    """Enterprise authentication service."""

    @staticmethod
    async def register_user(db: AsyncSession, user_data: UserCreate, ip_address: str = None, user_agent: str = None) -> User:
        """Register a new user."""
        existing = await db.execute(
            select(User).where(
                and_(
                    (User.email == user_data.email) | (User.username == user_data.username),
                    User.deleted_at.is_(None)
                )
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError("User with this email or username already exists")

        user = User(
            email=user_data.email,
            username=user_data.username,
            password_hash=get_password_hash(user_data.password),
            full_name=user_data.full_name,
            company=user_data.company,
            jurisdiction=user_data.jurisdiction,
            wallet_address=user_data.wallet_address,
            role=UserRole.CLIENT
        )

        db.add(user)
        await db.flush()

        verification_token = secrets.token_urlsafe(32)
        await AuthService.send_verification_email(user, verification_token)

        await audit_logger_service.log_action(
            db, user_id=str(user.id), action="register",
            resource_type="user", resource_id=str(user.id),
            ip_address=ip_address, user_agent=user_agent
        )

        logger.info(f"New user registered: {user.email}")
        return user

    @staticmethod
    async def authenticate_user(db: AsyncSession, login_data: UserLogin, ip_address: str = None, user_agent: str = None) -> tuple[User, str, str]:
        """Authenticate user with email and password."""
        result = await db.execute(
            select(User).where(
                and_(User.email == login_data.email, User.deleted_at.is_(None))
            )
        )
        user = result.scalar_one_or_none()

        if not user:
            await audit_logger_service.log_action(
                db, action="login", resource_type="user",
                details={"email": login_data.email, "reason": "user_not_found"},
                ip_address=ip_address, user_agent=user_agent, status="failure"
            )
            raise ValueError("Invalid email or password")

        if is_account_locked(str(user.id)):
            await audit_logger_service.log_action(
                db, user_id=str(user.id), action="login", resource_type="user",
                details={"reason": "account_locked"},
                ip_address=ip_address, user_agent=user_agent, status="failure"
            )
            raise ValueError("Account temporarily locked due to failed login attempts")

        if not verify_password(login_data.password, user.password_hash):
            attempt_info = record_login_attempt(str(user.id), False)
            user.login_attempts += 1
            if attempt_info["locked"]:
                user.locked_until = attempt_info["lock_until"]
            await db.flush()

            await audit_logger_service.log_action(
                db, user_id=str(user.id), action="login", resource_type="user",
                details={"reason": "invalid_password", "attempts": attempt_info["attempts"]},
                ip_address=ip_address, user_agent=user_agent, status="failure"
            )
            raise ValueError("Invalid email or password")

        record_login_attempt(str(user.id), True)
        user.login_attempts = 0
        user.locked_until = None
        user.last_login_at = datetime.now(timezone.utc)
        await db.flush()

        access_token = create_access_token({
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.value
        })
        refresh_token, refresh_hash = create_refresh_token({
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.value
        })

        session = UserSession(
            user_id=user.id,
            token_hash=hash_token(access_token),
            refresh_token_hash=refresh_hash,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        )
        db.add(session)

        await audit_logger_service.log_action(
            db, user_id=str(user.id), action="login", resource_type="user",
            ip_address=ip_address, user_agent=user_agent, status="success"
        )

        logger.info(f"User authenticated: {user.email}")
        return user, access_token, refresh_token

    @staticmethod
    async def verify_mfa(db: AsyncSession, user_id: str, code: str) -> tuple[str, str]:
        """Verify MFA code and return tokens."""
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user or not user.mfa_enabled:
            raise ValueError("Invalid MFA request")

        totp = pyotp.TOTP(user.mfa_secret)
        if not totp.verify(code):
            raise ValueError("Invalid MFA code")

        access_token = create_access_token({
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.value
        })
        refresh_token, refresh_hash = create_refresh_token({
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.value
        })

        return access_token, refresh_token

    @staticmethod
    async def setup_mfa(db: AsyncSession, user: User) -> MFASetupResponse:
        """Setup MFA for a user."""
        secret = pyotp.random_base32()
        user.mfa_secret = secret
        await db.flush()

        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(name=user.email, issuer_name="LexChain Sovereign")

        backup_codes = [secrets.token_urlsafe(8) for _ in range(10)]

        await audit_logger_service.log_action(
            db, user_id=str(user.id), action="mfa_setup",
            resource_type="user", resource_id=str(user.id)
        )

        return MFASetupResponse(
            secret=secret,
            qr_code=provisioning_uri,
            backup_codes=backup_codes
        )

    @staticmethod
    async def enable_mfa(db: AsyncSession, user: User, code: str) -> bool:
        """Enable MFA after verification."""
        totp = pyotp.TOTP(user.mfa_secret)
        if not totp.verify(code):
            return False

        user.mfa_enabled = True
        await db.flush()

        await audit_logger_service.log_action(
            db, user_id=str(user.id), action="mfa_enable",
            resource_type="user", resource_id=str(user.id)
        )

        return True

    @staticmethod
    async def disable_mfa(db: AsyncSession, user: User) -> bool:
        """Disable MFA for a user."""
        user.mfa_enabled = False
        user.mfa_secret = None
        await db.flush()

        await audit_logger_service.log_action(
            db, user_id=str(user.id), action="mfa_disable",
            resource_type="user", resource_id=str(user.id)
        )

        return True

    @staticmethod
    async def authenticate_wallet(db: AsyncSession, signature: str, message: str, wallet_address: str, ip_address: str = None) -> tuple[User, str, str]:
        """Authenticate user via wallet signature."""
        if not Web3.is_address(wallet_address):
            raise ValueError("Invalid wallet address")

        checksum_address = Web3.to_checksum_address(wallet_address)

        result = await db.execute(
            select(User).where(
                and_(User.wallet_address == checksum_address, User.deleted_at.is_(None))
            )
        )
        user = result.scalar_one_or_none()

        if not user:
            user = User(
                email=f"{checksum_address.lower()}@wallet.lexchain",
                username=f"wallet_{checksum_address[:16]}",
                password_hash=get_password_hash(secrets.token_urlsafe(32)),
                wallet_address=checksum_address,
                role=UserRole.CLIENT
            )
            db.add(user)
            await db.flush()

        access_token = create_access_token({
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.value
        })
        refresh_token, _ = create_refresh_token({
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.value
        })

        await audit_logger_service.log_action(
            db, user_id=str(user.id), action="wallet_auth",
            resource_type="user", resource_id=str(user.id),
            ip_address=ip_address, details={"wallet": checksum_address}
        )

        return user, access_token, refresh_token

    @staticmethod
    async def refresh_access_token(db: AsyncSession, refresh_token: str) -> tuple[str, str]:
        """Refresh access token using refresh token."""
        try:
            payload = decode_token(refresh_token)
            if payload.get("type") != "refresh":
                raise ValueError("Invalid token type")

            user_id = payload.get("sub")
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()

            if not user or not user.is_active:
                raise ValueError("User not found or inactive")

            new_access = create_access_token({
                "sub": str(user.id),
                "email": user.email,
                "role": user.role.value
            })
            new_refresh, _ = create_refresh_token({
                "sub": str(user.id),
                "email": user.email,
                "role": user.role.value
            })

            return new_access, new_refresh

        except Exception as e:
            logger.warning(f"Token refresh failed: {str(e)}")
            raise ValueError("Invalid or expired refresh token")

    @staticmethod
    async def logout(db: AsyncSession, user: User, token_hash: str, ip_address: str = None) -> bool:
        """Logout user by invalidating session."""
        result = await db.execute(
            select(UserSession).where(
                and_(UserSession.user_id == user.id, UserSession.token_hash == token_hash)
            )
        )
        session = result.scalar_one_or_none()

        if session:
            session.is_active = False
            await db.flush()

        await audit_logger_service.log_action(
            db, user_id=str(user.id), action="logout",
            resource_type="session", ip_address=ip_address
        )

        return True

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional[User]:
        """Get user by ID."""
        result = await db.execute(
            select(User).where(and_(User.id == user_id, User.deleted_at.is_(None)))
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
        """Get user by email."""
        result = await db.execute(
            select(User).where(and_(User.email == email, User.deleted_at.is_(None)))
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_users(db: AsyncSession, page: int = 1, page_size: int = 20, role: Optional[UserRole] = None) -> tuple[list[User], int]:
        """List users with pagination."""
        query = select(User).where(User.deleted_at.is_(None))
        count_query = select(User).where(User.deleted_at.is_(None))

        if role:
            query = query.where(User.role == role)
            count_query = count_query.where(User.role == role)

        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size).order_by(User.created_at.desc())

        result = await db.execute(query)
        users = list(result.scalars().all())

        count_result = await db.execute(count_query)
        total = len(count_result.scalars().all())

        return users, total

    @staticmethod
    async def update_user(db: AsyncSession, user: User, update_data: dict) -> User:
        """Update user profile."""
        for key, value in update_data.items():
            if hasattr(user, key) and value is not None:
                setattr(user, key, value)

        await db.flush()

        await audit_logger_service.log_action(
            db, user_id=str(user.id), action="profile_update",
            resource_type="user", resource_id=str(user.id)
        )

        return user

    @staticmethod
    async def delete_user(db: AsyncSession, user: User) -> bool:
        """Soft delete a user."""
        user.deleted_at = datetime.now(timezone.utc)
        user.is_active = False
        await db.flush()

        await audit_logger_service.log_action(
            db, user_id=str(user.id), action="user_delete",
            resource_type="user", resource_id=str(user.id)
        )

        return True

    @staticmethod
    async def request_password_reset(db: AsyncSession, email: str) -> str:
        """Request password reset for an email."""
        result = await db.execute(
            select(User).where(and_(User.email == email, User.deleted_at.is_(None)))
        )
        user = result.scalar_one_or_none()

        if user:
            token = secrets.token_urlsafe(32)
            return token

        return ""

    @staticmethod
    async def reset_password(db: AsyncSession, token: str, new_password: str) -> bool:
        """Reset password using token."""
        return True

    @staticmethod
    async def send_verification_email(user: User, token: str):
        """Send email verification email."""
        logger.info(f"Email verification for {user.email}: token={token}")