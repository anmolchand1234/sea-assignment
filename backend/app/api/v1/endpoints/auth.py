from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.models import User
from backend.app.schemas.auth import LoginRequest, TokenResponse, UserResponse
from backend.app.core.security import verify_password, create_access_token, create_refresh_token, decode_token
from backend.app.core.deps import get_current_user
from backend.app.core.errors import WaylineError

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise WaylineError(
            code="INVALID_CREDENTIALS",
            message="Incorrect email or password.",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    if not user.is_active:
        raise WaylineError(
            code="USER_INACTIVE",
            message="User account is deactivated.",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        role=user.role,
        name=user.name,
    )

@router.post("/refresh", response_model=TokenResponse)
def refresh_token_endpoint(refresh_token: str, db: Session = Depends(get_db)):
    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise WaylineError(
            code="INVALID_REFRESH_TOKEN",
            message="Invalid or expired refresh token.",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise WaylineError(
            code="USER_INACTIVE",
            message="User not found or inactive.",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    new_access = create_access_token(user.id)
    new_refresh = create_refresh_token(user.id)
    return TokenResponse(
        access_token=new_access,
        refresh_token=new_refresh,
        role=user.role,
        name=user.name,
    )

@router.get("/me", response_model=UserResponse)
def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user

