from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User, UserRole
from app.models.reminder import ReminderPreference
from app.core.security import hash_password, verify_password, create_access_token
from app.core.dependencies import get_current_user
from app.core.rate_limiter import auth_rate_limiter
from app.schemas.user import UserRegister, UserLogin, UserResponse, Token, UserUpdateProfile

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user_in: UserRegister, db: Session = Depends(get_db)):
    """Register a new student or admin account."""
    existing_user = db.query(User).filter(User.email == user_in.email.lower()).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists."
        )

    role_val = user_in.role.lower() if user_in.role else UserRole.STUDENT.value
    if role_val not in [UserRole.STUDENT.value, UserRole.ADMIN.value]:
        role_val = UserRole.STUDENT.value

    new_user = User(
        email=user_in.email.lower(),
        hashed_password=hash_password(user_in.password),
        full_name=user_in.full_name,
        role=role_val,
        college=user_in.college,
        roll_number=user_in.roll_number,
        streak_days=0,
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Initialize default reminder preference for the user
    default_pref = ReminderPreference(
        user_id=new_user.id,
        reminder_time="09:00",
        timezone="Asia/Kolkata",
        is_enabled=True,
        notification_channel="in_app"
    )
    db.add(default_pref)
    db.commit()

    return new_user

@router.post("/login", response_model=Token)
def login_user(
    login_in: UserLogin,
    request: Request,
    db: Session = Depends(get_db)
):
    """Authenticate user with email and password and return a JWT access token."""
    # Enforce rate limiting
    auth_rate_limiter.check(request, key_prefix="login")

    user = db.query(User).filter(User.email == login_in.email.lower()).first()
    if not user or not verify_password(login_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated."
        )

    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role}
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )

@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Retrieve the currently authenticated user's profile."""
    return current_user

@router.put("/me", response_model=UserResponse)
def update_current_user_profile(
    profile_in: UserUpdateProfile,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update profile information for the authenticated user."""
    if profile_in.full_name is not None:
        current_user.full_name = profile_in.full_name
    if profile_in.college is not None:
        current_user.college = profile_in.college
    if profile_in.roll_number is not None:
        current_user.roll_number = profile_in.roll_number

    db.commit()
    db.refresh(current_user)
    return current_user
