from typing import List, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from backend.app.core.security import decode_token
from backend.app.db.session import get_db
from backend.app.models import User
from backend.app.core.errors import WaylineError

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

def get_current_user(
    db: Session = Depends(get_db),
    token: Optional[str] = Depends(oauth2_scheme),
) -> User:
    if not token:
        raise WaylineError(
            code="UNAUTHORIZED",
            message="Authentication credentials were not provided.",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise WaylineError(
            code="INVALID_TOKEN",
            message="Invalid or expired authentication token.",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise WaylineError(
            code="USER_INACTIVE",
            message="User account is inactive or not found.",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    return user

def require_role(allowed_roles: List[str]):
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles and current_user.role != "admin":
            raise WaylineError(
                code="FORBIDDEN",
                message=f"Access denied. Requires one of roles: {', '.join(allowed_roles)}.",
                status_code=status.HTTP_403_FORBIDDEN,
            )
        return current_user
    return role_checker

