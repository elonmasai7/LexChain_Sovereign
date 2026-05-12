"""User management API routes."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_super_admin, get_client_ip, get_user_agent
from app.core.audit import audit_logger_service
from app.services.auth_service import AuthService
from app.schemas.user import UserResponse, UserUpdate
from app.schemas.common import PaginatedResponse, MessageResponse
from app.models.user import User, UserRole


router = APIRouter()


@router.get("/", response_model=PaginatedResponse)
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    role: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all users (admin only)."""
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    role_enum = UserRole(role) if role else None
    users, total = await AuthService.list_users(db, page, page_size, role_enum)

    return PaginatedResponse(
        items=[UserResponse.model_validate(u) for u in users],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user by ID."""
    if current_user.role != UserRole.SUPER_ADMIN and str(current_user.id) != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    user = await AuthService.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    update_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update user profile."""
    if str(current_user.id) != user_id and current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    user = await AuthService.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    updated_user = await AuthService.update_user(db, user, update_data.model_dump(exclude_unset=True))
    return updated_user


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    current_user: User = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
    request = None
):
    """Delete user (soft delete, admin only)."""
    user = await AuthService.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    await AuthService.delete_user(db, user)

    await audit_logger_service.log_action(
        db, user_id=str(current_user.id), action="user_delete",
        resource_type="user", resource_id=user_id,
        ip_address=get_client_ip(request) if request else None,
        user_agent=get_user_agent(request) if request else None
    )

    return MessageResponse(message="User deleted successfully")


@router.put("/{user_id}/role")
async def update_user_role(
    user_id: str,
    role: str,
    current_user: User = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update user role (admin only)."""
    user = await AuthService.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    try:
        role_enum = UserRole(role)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role")

    user.role = role_enum
    await db.flush()

    await audit_logger_service.log_action(
        db, user_id=str(current_user.id), action="role_change",
        resource_type="user", resource_id=user_id,
        details={"new_role": role}
    )

    return {"message": f"Role updated to {role}"}