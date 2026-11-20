from datetime import datetime, timezone, timedelta
from email.message import EmailMessage
from hashlib import sha256
import secrets
import smtplib
from sqlalchemy.orm import Session
from app.core.security import get_password_hash, verify_password, create_access_token, create_refresh_token, decode_token
from app.core.exceptions import UnauthorizedAccessException, DuplicateResourceException
from app.models.user import User, UserRole
from app.schemas.schemas import UserCreate, LoginRequest, Token, ChangePasswordRequest, ResetPasswordRequest
from app.repositories.user_repo import UserRepository
from app.models.auth_session import RefreshSession
from app.models.password_reset import PasswordResetToken
from app.core.config import settings
from app.core.logging import logger


class AuthService:
    def __init__(self, db: Session):
        self.user_repo = UserRepository(db)

    def register_student(self, user_in: UserCreate) -> User:
        existing = self.user_repo.get_by_email(user_in.email)
        if existing:
            raise DuplicateResourceException("User", "email", user_in.email)

        # Enforce student role for public registration
        new_user = User(
            email=user_in.email.lower().strip(),
            hashed_password=get_password_hash(user_in.password),
            full_name=user_in.full_name.strip(),
            role=UserRole.STUDENT,
            phone_number=user_in.phone_number,
        )
        return self.user_repo.create(new_user)

    def authenticate_user(self, login_data: LoginRequest) -> Token:
        user = self.user_repo.get_by_email(login_data.email.lower().strip())
        if not user or not verify_password(login_data.password, user.hashed_password):
            raise UnauthorizedAccessException("Incorrect email or password")

        if not user.is_active:
            raise UnauthorizedAccessException("User account is disabled")

        token_payload = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.value,
            "token_version": user.token_version,
        }
        access_token = create_access_token(token_payload)
        refresh_token = create_refresh_token(token_payload)
        refresh_payload = decode_token(refresh_token)
        self.user_repo.db.add(RefreshSession(
            user_id=user.id,
            token_jti=refresh_payload["jti"],
            expires_at=datetime.fromtimestamp(refresh_payload["exp"], tz=timezone.utc),
        ))
        self.user_repo.db.commit()

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
        )

    def refresh_access_token(self, refresh_token: str) -> Token:
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh" or not payload.get("jti"):
            raise UnauthorizedAccessException("Invalid or expired refresh token")

        user_id = payload.get("sub")
        if not user_id or not str(user_id).isdigit():
            raise UnauthorizedAccessException("Invalid refresh token subject")
        user = self.user_repo.get_by_id(int(user_id))
        if not user or not user.is_active:
            raise UnauthorizedAccessException("User does not exist or is inactive")
        existing = self.user_repo.db.query(RefreshSession).filter(
            RefreshSession.token_jti == payload["jti"],
            RefreshSession.user_id == user.id,
            RefreshSession.revoked_at.is_(None),
        ).first()
        if not existing:
            raise UnauthorizedAccessException("Refresh token has already been used or revoked")
        if existing.expires_at.replace(tzinfo=timezone.utc) <= datetime.now(timezone.utc):
            existing.revoked_at = datetime.now(timezone.utc)
            self.user_repo.db.commit()
            raise UnauthorizedAccessException("Refresh token has expired")

        token_payload = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.value,
            "token_version": user.token_version,
        }
        new_access_token = create_access_token(token_payload)
        new_refresh_token = create_refresh_token(token_payload)
        new_payload = decode_token(new_refresh_token)
        existing.revoked_at = datetime.now(timezone.utc)
        self.user_repo.db.add(RefreshSession(
            user_id=user.id,
            token_jti=new_payload["jti"],
            expires_at=datetime.fromtimestamp(new_payload["exp"], tz=timezone.utc),
        ))
        self.user_repo.db.commit()

        return Token(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
        )

    def revoke_refresh_token(self, refresh_token: str, user: User) -> None:
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh" or not payload.get("jti"):
            return
        session = self.user_repo.db.query(RefreshSession).filter(
            RefreshSession.token_jti == payload["jti"],
            RefreshSession.user_id == user.id,
            RefreshSession.revoked_at.is_(None),
        ).first()
        if session:
            session.revoked_at = datetime.now(timezone.utc)
            self.user_repo.db.commit()

    def change_password(self, user: User, request: ChangePasswordRequest) -> None:
        if not verify_password(request.current_password, user.hashed_password):
            raise UnauthorizedAccessException("Current password is incorrect.")
        if verify_password(request.new_password, user.hashed_password):
            raise ValueError("Choose a new password that differs from your current password.")
        user.hashed_password = get_password_hash(request.new_password)
        user.token_version += 1
        now = datetime.now(timezone.utc)
        self.user_repo.db.query(RefreshSession).filter(
            RefreshSession.user_id == user.id,
            RefreshSession.revoked_at.is_(None),
        ).update({RefreshSession.revoked_at: now}, synchronize_session=False)
        self.user_repo.db.commit()

    def request_password_reset(self, email: str) -> None:
        user = self.user_repo.get_by_email(email.lower().strip())
        if not user or not user.is_active:
            return
        db = self.user_repo.db
        now = datetime.now(timezone.utc)
        recent_count = db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.created_at >= (now - timedelta(hours=1)).replace(tzinfo=None),
        ).count()
        if recent_count >= 3:
            return
        raw_token = secrets.token_urlsafe(32)
        db.add(PasswordResetToken(
            user_id=user.id,
            token_hash=sha256(raw_token.encode("utf-8")).hexdigest(),
            expires_at=now + timedelta(minutes=30),
        ))
        db.commit()
        if not settings.SMTP_HOST or not settings.SMTP_FROM_EMAIL:
            logger.warning("Password reset requested but SMTP is not configured; no email was sent.")
            db.query(PasswordResetToken).filter(
                PasswordResetToken.token_hash == sha256(raw_token.encode("utf-8")).hexdigest(),
                PasswordResetToken.used_at.is_(None),
            ).delete(synchronize_session=False)
            db.commit()
            return
        reset_url = f"{settings.FRONTEND_BASE_URL.rstrip('/')}?reset_token={raw_token}"
        message = EmailMessage()
        message["Subject"] = "Reset your CampusFix password"
        message["From"] = settings.SMTP_FROM_EMAIL
        message["To"] = user.email
        message.set_content(
            "A password reset was requested for your CampusFix account. "
            f"This one-time link expires in 30 minutes: {reset_url}\n\n"
            "If you did not request this, you can ignore this message."
        )
        try:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as smtp:
                if settings.SMTP_STARTTLS:
                    smtp.starttls()
                if settings.SMTP_USERNAME:
                    smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                smtp.send_message(message)
        except (OSError, smtplib.SMTPException) as error:
            logger.error("Password reset email delivery failed for user_id=%s (%s)", user.id, type(error).__name__)
            db.query(PasswordResetToken).filter(
                PasswordResetToken.token_hash == sha256(raw_token.encode("utf-8")).hexdigest(),
                PasswordResetToken.used_at.is_(None),
            ).delete(synchronize_session=False)
            db.commit()

    def reset_password(self, request: ResetPasswordRequest) -> None:
        token_hash = sha256(request.token.encode("utf-8")).hexdigest()
        reset = self.user_repo.db.query(PasswordResetToken).filter(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.used_at.is_(None),
        ).with_for_update().first()
        now = datetime.now(timezone.utc)
        if not reset or (reset.expires_at.replace(tzinfo=timezone.utc) if reset.expires_at.tzinfo is None else reset.expires_at) <= now:
            raise UnauthorizedAccessException("This password reset link is invalid or expired.")
        user = self.user_repo.get_by_id(reset.user_id)
        if not user or not user.is_active:
            raise UnauthorizedAccessException("This password reset link is invalid or expired.")
        reset.used_at = now
        user.hashed_password = get_password_hash(request.new_password)
        user.token_version += 1
        self.user_repo.db.query(RefreshSession).filter(
            RefreshSession.user_id == user.id,
            RefreshSession.revoked_at.is_(None),
        ).update({RefreshSession.revoked_at: now}, synchronize_session=False)
        self.user_repo.db.commit()
