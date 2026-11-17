from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.models import User
from backend.app.schemas.auth import (
    LoginRequest,
    SignUpRequest,
    ChangePasswordRequest,
    TokenResponse,
    UserResponse,
)
from backend.app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from backend.app.core.deps import get_current_user
from backend.app.core.errors import WaylineError

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/signup", response_model=TokenResponse)
def signup(payload: SignUpRequest, db: Session = Depends(get_db)):
    """User and Passenger sign up with assigned role."""
    existing_user = db.query(User).filter(User.email == payload.email).first()
    if existing_user:
        raise WaylineError(
            code="USER_ALREADY_EXISTS",
            message=f"An account with email {payload.email} already exists.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    # Normalize role: passenger or operator/user
    assigned_role = "passenger" if payload.role.lower() == "passenger" else "dispatcher"

    new_user = User(
        name=payload.name.strip(),
        email=payload.email.lower().strip(),
        password_hash=get_password_hash(payload.password),
        role=assigned_role,
        is_active=True,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    access_token = create_access_token(new_user.id)
    refresh_token = create_refresh_token(new_user.id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        role=new_user.role,
        name=new_user.name,
        email=new_user.email,
    )

@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """User and Passenger sign in with valid credentials."""
    user = db.query(User).filter(User.email == payload.email.lower().strip()).first()
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
        email=user.email,
    )

@router.post("/change-password")
def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Change user password after verifying old password."""
    if not verify_password(payload.old_password, current_user.password_hash):
        raise WaylineError(
            code="INVALID_PASSWORD",
            message="Current password does not match.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    current_user.password_hash = get_password_hash(payload.new_password)
    db.commit()
    return {"status": "success", "message": "Password changed successfully."}

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
        email=user.email,
    )

@router.get("/me", response_model=UserResponse)
def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user
