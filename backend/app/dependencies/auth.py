from typing import Optional, List
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.security import decode_token
from app.core.exceptions import UnauthorizedAccessException, ForbiddenOperationException
from app.models.user import User, UserRole
from app.repositories.user_repo import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise UnauthorizedAccessException("Invalid or expired access token")

    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedAccessException("Token contains no user identifier")

    user_repo = UserRepository(db)
    user = user_repo.get_by_id(int(user_id))
    if not user or not user.is_active:
        raise UnauthorizedAccessException("User not found or deactivated")
    if payload.get("token_version") != user.token_version:
        raise UnauthorizedAccessException("Session expired. Sign in again.")

    return user


def require_role(allowed_roles: List[UserRole]):
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise ForbiddenOperationException(
                f"Operation not permitted. Requires role: {[r.value for r in allowed_roles]}"
            )
        return current_user
    return role_checker


# Role helper dependencies
require_admin = require_role([UserRole.ADMIN])
require_staff = require_role([UserRole.STAFF, UserRole.ADMIN])
require_student = require_role([UserRole.STUDENT, UserRole.ADMIN])
