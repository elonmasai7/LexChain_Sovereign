"""Audit log API routes."""
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_super_admin
from app.core.audit import audit_logger_service
from app.schemas.common import PaginatedResponse
from app.models.user import User


router = APIRouter()


@router.get("/logs", response_model=PaginatedResponse)
async def get_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get audit logs with filters (admin only)."""
    logs, total = await audit_logger_service.query_logs(
        db, user_id, action, resource_type, None, start_date, end_date, status, page_size, (page - 1) * page_size
    )

    return PaginatedResponse(
        items=[{
            "id": str(log.id),
            "user_id": str(log.user_id) if log.user_id else None,
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "details": log.details,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "status": log.status,
            "created_at": log.created_at.isoformat() if log.created_at else None
        } for log in logs],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.get("/user/{user_id}")
async def get_user_audit_trail(
    user_id: str,
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get audit trail for a specific user."""
    if current_user.role.value != "super_admin" and str(current_user.id) != user_id:
        return {"error": "Access denied"}

    logs = await audit_logger_service.get_user_activity(db, user_id, limit)
    return {"user_id": user_id, "logs": [log.to_dict() for log in logs], "count": len(logs)}


@router.get("/resource/{resource_type}/{resource_id}")
async def get_resource_history(
    resource_type: str,
    resource_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get history of changes to a specific resource."""
    logs = await audit_logger_service.get_resource_history(db, resource_type, resource_id)
    return {"resource_type": resource_type, "resource_id": resource_id, "history": [log.to_dict() for log in logs]}


@router.get("/security-events")
async def get_security_events(
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get security-related audit events."""
    events = await audit_logger_service.get_security_events(db, limit)
    return {"events": [e.to_dict() for e in events], "count": len(events)}


@router.get("/failed-logins")
async def get_failed_logins(
    hours: int = Query(24, ge=1, le=168),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get failed login attempts."""
    events = await audit_logger_service.get_failed_logins(db, hours, limit)
    return {"events": [e.to_dict() for e in events], "count": len(events)}