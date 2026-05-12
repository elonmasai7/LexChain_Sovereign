"""Session management service."""
from datetime import datetime, timezone, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models.user import UserSession, User
from app.core.security import hash_token, generate_session_id
from app.core.config import settings


class SessionService:
    """Session management with device fingerprinting."""

    @staticmethod
    async def create_session(db: AsyncSession, user_id: str, token: str, refresh_token: str = None, ip_address: str = None, user_agent: str = None, device_fingerprint: str = None) -> UserSession:
        """Create a new session."""
        session = UserSession(
            user_id=user_id,
            token_hash=hash_token(token),
            refresh_token_hash=hash_token(refresh_token) if refresh_token else None,
            ip_address=ip_address,
            user_agent=user_agent,
            device_fingerprint=device_fingerprint,
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        )
        db.add(session)
        await db.flush()
        return session

    @staticmethod
    async def validate_session(db: AsyncSession, token: str) -> Optional[UserSession]:
        """Validate session token."""
        token_hash = hash_token(token)
        result = await db.execute(
            select(UserSession).where(
                and_(
                    UserSession.token_hash == token_hash,
                    UserSession.is_active == True,
                    UserSession.expires_at > datetime.now(timezone.utc)
                )
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def invalidate_session(db: AsyncSession, session_id: str) -> bool:
        """Invalidate a session."""
        result = await db.execute(select(UserSession).where(UserSession.id == session_id))
        session = result.scalar_one_or_none()
        if session:
            session.is_active = False
            await db.flush()
            return True
        return False

    @staticmethod
    async def rotate_session(db: AsyncSession, session: UserSession, new_token: str, new_refresh_token: str = None) -> UserSession:
        """Rotate session tokens."""
        session.token_hash = hash_token(new_token)
        if new_refresh_token:
            session.refresh_token_hash = hash_token(new_refresh_token)
        session.rotated_at = datetime.now(timezone.utc)
        session.last_activity = datetime.now(timezone.utc)
        await db.flush()
        return session

    @staticmethod
    async def get_active_sessions(db: AsyncSession, user_id: str) -> list[UserSession]:
        """Get all active sessions for a user."""
        result = await db.execute(
            select(UserSession).where(
                and_(
                    UserSession.user_id == user_id,
                    UserSession.is_active == True,
                    UserSession.expires_at > datetime.now(timezone.utc)
                )
            ).order_by(UserSession.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def revoke_all_sessions(db: AsyncSession, user_id: str, except_session_id: str = None) -> int:
        """Revoke all sessions for a user."""
        query = select(UserSession).where(
            and_(
                UserSession.user_id == user_id,
                UserSession.is_active == True
            )
        )
        result = await db.execute(query)
        sessions = list(result.scalars().all())

        count = 0
        for session in sessions:
            if except_session_id is None or str(session.id) != except_session_id:
                session.is_active = False
                count += 1

        await db.flush()
        return count

    @staticmethod
    async def cleanup_expired_sessions(db: AsyncSession) -> int:
        """Clean up expired sessions."""
        result = await db.execute(
            select(UserSession).where(
                UserSession.expires_at < datetime.now(timezone.utc)
            )
        )
        sessions = list(result.scalars().all())

        for session in sessions:
            session.is_active = False

        await db.flush()
        return len(sessions)


session_service = SessionService()