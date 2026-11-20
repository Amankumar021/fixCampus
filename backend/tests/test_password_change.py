from datetime import datetime
from app.core.exceptions import UnauthorizedAccessException
from app.models.auth_session import RefreshSession
from app.models import User
from app.schemas.schemas import ChangePasswordRequest
from app.services.auth_service import AuthService
from app.schemas.schemas import LoginRequest
from app.core.security import decode_token
from app.dependencies.auth import get_current_user


def test_change_password_updates_hash_and_invalidates_sessions(db_session, monkeypatch):
    user = db_session.query(User).filter_by(email="student1@campusfix.edu").one()
    db_session.add(RefreshSession(user_id=user.id, token_jti="active-session", expires_at=datetime.now()))
    db_session.commit()
    monkeypatch.setattr("app.services.auth_service.verify_password", lambda raw, hashed: raw == "old-secret")
    monkeypatch.setattr("app.services.auth_service.get_password_hash", lambda raw: f"hashed:{raw}")

    AuthService(db_session).change_password(user, ChangePasswordRequest(
        current_password="old-secret", new_password="new-secret-123",
    ))

    db_session.refresh(user)
    session = db_session.query(RefreshSession).filter_by(token_jti="active-session").one()
    assert user.hashed_password == "hashed:new-secret-123"
    assert user.token_version == 1
    assert session.revoked_at is not None


def test_change_password_rejects_wrong_current_password(db_session, monkeypatch):
    user = db_session.query(User).filter_by(email="student1@campusfix.edu").one()
    monkeypatch.setattr("app.services.auth_service.verify_password", lambda *_: False)
    request = ChangePasswordRequest(current_password="wrong-password", new_password="new-secret-123")
    try:
        AuthService(db_session).change_password(user, request)
        assert False, "wrong current password must be rejected"
    except UnauthorizedAccessException:
        pass


def test_password_change_invalidates_existing_access_tokens(db_session, monkeypatch):
    user = db_session.query(User).filter_by(email="student1@campusfix.edu").one()
    monkeypatch.setattr("app.services.auth_service.verify_password", lambda raw, _hashed: raw == "old-secret")
    monkeypatch.setattr("app.services.auth_service.get_password_hash", lambda raw: f"hashed:{raw}")
    tokens = AuthService(db_session).authenticate_user(LoginRequest(email=user.email, password="old-secret"))
    assert decode_token(tokens.access_token)["token_version"] == 0

    AuthService(db_session).change_password(user, ChangePasswordRequest(
        current_password="old-secret", new_password="new-secret-123",
    ))
    try:
        get_current_user(tokens.access_token, db_session)
        assert False, "old access tokens should no longer be accepted"
    except UnauthorizedAccessException:
        pass
