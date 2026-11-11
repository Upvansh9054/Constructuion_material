from typing import AsyncGenerator, Callable, List, Optional
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.constants import AuditAction, UserRole
from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.audit_log import AuditLog
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme),
) -> User:
    """Validate bearer token and retrieve authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account",
        )
    return user


def require_roles(allowed_roles: List[UserRole]) -> Callable:
    """Dependency factory checking if the authenticated user has one of the allowed roles."""
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        # Superuser always bypasses role restrictions
        if current_user.is_superuser or current_user.role == UserRole.ADMIN:
            return current_user

        # Match contractor aliases
        effective_role = current_user.role
        if effective_role == UserRole.DEMOLITION_CONTRACTOR:
            effective_role = UserRole.CONTRACTOR
        if effective_role == UserRole.MATERIAL_BUYER:
            effective_role = UserRole.BUYER

        allowed_effective = []
        for r in allowed_roles:
            if r == UserRole.DEMOLITION_CONTRACTOR:
                allowed_effective.append(UserRole.CONTRACTOR)
            elif r == UserRole.MATERIAL_BUYER:
                allowed_effective.append(UserRole.BUYER)
            else:
                allowed_effective.append(r)

        if effective_role not in allowed_effective:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires one of the following roles: {[r.value for r in allowed_roles]}",
            )
        return current_user

    return role_checker


# Role-specific shorthand dependencies
require_admin = require_roles([UserRole.ADMIN])
require_contractor = require_roles([UserRole.ADMIN, UserRole.CONTRACTOR, UserRole.DEMOLITION_CONTRACTOR, UserRole.SURVEYOR])
require_buyer = require_roles([UserRole.ADMIN, UserRole.BUYER, UserRole.MATERIAL_BUYER, UserRole.RECYCLER])


async def record_audit_log(
    db: AsyncSession,
    user_id: Optional[str],
    action: AuditAction,
    resource_type: str,
    resource_id: Optional[str],
    change_details: Optional[dict] = None,
    request: Optional[Request] = None,
) -> AuditLog:
    """Persist an immutable audit log record for security, compliance, and provenance."""
    ip_address = None
    user_agent = None
    if request:
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

    log_entry = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        change_details=change_details or {},
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(log_entry)
    await db.commit()
    return log_entry
