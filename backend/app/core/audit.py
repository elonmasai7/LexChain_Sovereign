"""Audit logging service for security and compliance."""
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from app.models.audit_log import AuditLog
from app.core.logging import get_logger


logger = get_logger(__name__)


class AuditLoggerService:
    """Service for recording and querying audit logs."""

    async def log_action(
        self,
        db: AsyncSession,
        user_id: Optional[str] = None,
        action: str = "",
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        status: str = "success"
    ) -> AuditLog:
        """Record an audit log entry."""
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent,
            status=status
        )

        db.add(audit_log)
        await db.flush()

        logger.info(
            f"Audit log: {action} on {resource_type}/{resource_id} by {user_id}",
            extra={"extra_data": {
                "user_id": user_id,
                "action": action,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "ip_address": ip_address,
                "status": status
            }}
        )

        return audit_log

    async def query_logs(
        self,
        db: AsyncSession,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> tuple[list[AuditLog], int]:
        """Query audit logs with filters."""
        conditions = []

        if user_id:
            conditions.append(AuditLog.user_id == user_id)
        if action:
            conditions.append(AuditLog.action == action)
        if resource_type:
            conditions.append(AuditLog.resource_type == resource_type)
        if resource_id:
            conditions.append(AuditLog.resource_id == resource_id)
        if status:
            conditions.append(AuditLog.status == status)
        if start_date:
            conditions.append(AuditLog.created_at >= start_date)
        if end_date:
            conditions.append(AuditLog.created_at <= end_date)

        where_clause = and_(*conditions) if conditions else True

        count_query = select(AuditLog).where(where_clause)
        count_result = await db.execute(count_query)
        total = len(count_result.scalars().all())

        query = (
            select(AuditLog)
            .where(where_clause)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await db.execute(query)
        logs = list(result.scalars().all())

        return logs, total

    async def get_user_activity(
        self,
        db: AsyncSession,
        user_id: str,
        limit: int = 50
    ) -> list[AuditLog]:
        """Get recent activity for a specific user."""
        query = (
            select(AuditLog)
            .where(AuditLog.user_id == user_id)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
        )

        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_resource_history(
        self,
        db: AsyncSession,
        resource_type: str,
        resource_id: str
    ) -> list[AuditLog]:
        """Get the complete history of changes to a resource."""
        query = (
            select(AuditLog)
            .where(
                and_(
                    AuditLog.resource_type == resource_type,
                    AuditLog.resource_id == resource_id
                )
            )
            .order_by(AuditLog.created_at.desc())
        )

        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_failed_logins(
        self,
        db: AsyncSession,
        hours: int = 24,
        limit: int = 100
    ) -> list[AuditLog]:
        """Get failed login attempts in the last N hours."""
        since = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        from datetime import timedelta
        since = datetime.now(timezone.utc) - timedelta(hours=hours)

        query = (
            select(AuditLog)
            .where(
                and_(
                    AuditLog.action == "login",
                    AuditLog.status == "failure",
                    AuditLog.created_at >= since
                )
            )
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
        )

        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_security_events(
        self,
        db: AsyncSession,
        limit: int = 100
    ) -> list[AuditLog]:
        """Get security-related audit events."""
        security_actions = [
            "login", "logout", "register", "password_change",
            "mfa_enable", "mfa_disable", "api_key_create", "api_key_revoke",
            "role_change", "permission_denied"
        ]

        query = (
            select(AuditLog)
            .where(AuditLog.action.in_(security_actions))
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
        )

        result = await db.execute(query)
        return list(result.scalars().all())


audit_logger_service = AuditLoggerService()