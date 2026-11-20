from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.schemas import UserCreate, UserResponse, LoginRequest, RefreshTokenRequest, Token, ChangePasswordRequest, ForgotPasswordRequest, ResetPasswordRequest, PasswordResetMessage
from app.services.auth_service import AuthService
from app.dependencies.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_student(user_in: UserCreate, db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    return auth_service.register_student(user_in)


@router.post("/login", response_model=Token)
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    return auth_service.authenticate_user(login_data)


@router.post("/refresh", response_model=Token)
def refresh_token(refresh_data: RefreshTokenRequest, db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    return auth_service.refresh_access_token(refresh_data.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    refresh_data: RefreshTokenRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    AuthService(db).revoke_refresh_token(refresh_data.refresh_token, current_user)
    return None


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        AuthService(db).change_password(current_user, password_data)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error
    return None


@router.post("/forgot-password", response_model=PasswordResetMessage, status_code=status.HTTP_202_ACCEPTED)
def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    AuthService(db).request_password_reset(str(request.email))
    return PasswordResetMessage(message="If that account exists, password reset instructions will be sent to its email address.")


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    AuthService(db).reset_password(request)
    return None
