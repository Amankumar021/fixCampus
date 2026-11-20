from app.api.v1.endpoints.ml import predict_category_endpoint
from app.api.v1.endpoints.auth import register_student
from app.api.v1.endpoints.complaints import download_complaint_attachment
from app.core.exceptions import ForbiddenOperationException
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.models import Complaint, User, UserRole, RewardTransaction
from app.schemas.schemas import MLPredictRequest, UserCreate, LoginRequest
from app.schemas.schemas import ComplaintCreate, FeedbackCreate
from app.services.complaint_service import ComplaintService
from app.services.auth_service import AuthService
from app.services.reward_service import RewardService
from app.core.exceptions import UnauthorizedAccessException
from app.models.auth_session import RefreshSession
from app.models.password_reset import PasswordResetToken
from app.models.assignment import StaffAssignment, AssignmentStatus
from app.services.staff_service import StaffService
from app.services.analytics_service import AnalyticsService
from app.schemas.schemas import ResetPasswordRequest
from datetime import datetime, timedelta, timezone
from hashlib import sha256


def user(db, email):
    return db.query(User).filter(User.email == email).one()


def test_student_registration_ignores_role_escalation(db_session, monkeypatch):
    monkeypatch.setattr("app.services.auth_service.get_password_hash", lambda _: "hash")
    created = register_student(UserCreate(email="new@example.edu", password="StrongPass123!", full_name="New User", role="admin"), db_session)
    assert created.role == UserRole.STUDENT


def test_staff_complaint_list_only_includes_assigned(db_session):
    staff = user(db_session, "electrical.staff@campusfix.edu")
    complaint = ComplaintService(db_session).list_complaints(staff)
    assert [item.id for item in complaint] == [1]


def test_staff_cannot_view_unassigned_complaint(db_session):
    complaint = db_session.query(Complaint).one()
    other_staff = user(db_session, "it.staff@campusfix.edu")
    try:
        ComplaintService(db_session).get_complaint(complaint.id, other_staff)
        assert False, "unassigned staff should not have access"
    except ForbiddenOperationException:
        pass


def test_ml_prediction_returns_expected_contract():
    result = predict_category_endpoint(MLPredictRequest(description="The classroom fan has stopped working and sparks at its switch"))
    assert result.predicted_category in {"Electrical", "Other"}
    assert 0 <= result.confidence <= 1
    assert result.method


def test_access_token_is_distinct_from_refresh_token():
    payload = {"sub": "5", "role": "student"}
    assert decode_token(create_access_token(payload))["type"] == "access"
    assert decode_token(create_refresh_token(payload))["type"] == "refresh"


def test_refresh_token_rotates_and_cannot_be_replayed(db_session, monkeypatch):
    student = user(db_session, "student1@campusfix.edu")
    monkeypatch.setattr("app.services.auth_service.verify_password", lambda *_: True)
    tokens = AuthService(db_session).authenticate_user(LoginRequest(email=student.email, password="ok"))
    rotated = AuthService(db_session).refresh_access_token(tokens.refresh_token)
    assert decode_token(rotated.refresh_token)["jti"] != decode_token(tokens.refresh_token)["jti"]
    try:
        AuthService(db_session).refresh_access_token(tokens.refresh_token)
        assert False, "rotated refresh token should not be reusable"
    except UnauthorizedAccessException as error:
        assert "already been used or revoked" in error.detail


def test_public_attachment_download_is_authorized_and_file_is_not_public(tmp_path, monkeypatch, db_session):
    complaint = db_session.query(Complaint).one()
    complaint.attachment_url = "/uploads/evidence.jpg"
    db_session.commit()
    path = tmp_path / "evidence.jpg"
    path.write_bytes(b"evidence")
    monkeypatch.setattr("app.api.v1.endpoints.complaints.settings.UPLOAD_DIR", str(tmp_path))
    student = user(db_session, "student1@campusfix.edu")
    response = download_complaint_attachment("evidence.jpg", student, db_session)
    assert str(response.path).replace("\\", "/") == str(path).replace("\\", "/")
    other = user(db_session, "it.staff@campusfix.edu")
    try:
        download_complaint_attachment("evidence.jpg", other, db_session)
        assert False, "unassigned staff should not download evidence"
    except ForbiddenOperationException:
        pass


def test_student_reward_balance_is_private_and_starts_at_zero(db_session):
    student = user(db_session, "student1@campusfix.edu")
    summary = RewardService(db_session).get_student_rewards(student)
    assert summary["total_points"] == 0
    assert summary["next_milestone"] == 50
    try:
        RewardService(db_session).get_student_rewards(user(db_session, "admin@campusfix.edu"))
        assert False, "reward balance must be student-only"
    except ForbiddenOperationException:
        pass


def test_valid_issue_awards_ten_points_in_same_transaction(db_session, monkeypatch):
    student = user(db_session, "student1@campusfix.edu")
    monkeypatch.setattr("app.services.complaint_service.predict_complaint_category", lambda _: {
        "predicted_category": "Cleanliness", "confidence": .7, "is_confident": True,
    })
    created = ComplaintService(db_session).create_complaint(student, ComplaintCreate(
        title="Overflowing waste bin", description="The bin is overflowing near our lecture hall.",
        location="Main block lecture hall",
    ))
    db_session.refresh(student)
    assert student.reward_points == 10
    assert created.reward_points_awarded == 10
    assert db_session.query(RewardTransaction).filter_by(complaint_id=created.id, reason="ISSUE_REPORTED").one().points == 10


def test_resolution_feedback_awards_five_points_once(db_session):
    student = user(db_session, "student1@campusfix.edu")
    complaint = db_session.query(Complaint).one()
    complaint.status = "RESOLVED"
    db_session.commit()
    service = ComplaintService(db_session)
    service.submit_feedback(complaint.id, student, FeedbackCreate(rating=5, comments="Thank you"))
    db_session.refresh(student)
    assert student.reward_points == 5
    assert db_session.query(RewardTransaction).filter_by(reason="RESOLUTION_FEEDBACK").one().points == 5
    try:
        service.submit_feedback(complaint.id, student, FeedbackCreate(rating=5))
        assert False, "repeat feedback must not award points"
    except ForbiddenOperationException:
        pass
    db_session.refresh(student)
    assert student.reward_points == 5


def test_issue_reward_daily_cap_does_not_block_report(db_session, monkeypatch):
    student = user(db_session, "student1@campusfix.edu")
    monkeypatch.setattr("app.core.config.settings.DAILY_ISSUE_REWARD_LIMIT", 10)
    monkeypatch.setattr("app.services.complaint_service.predict_complaint_category", lambda _: {
        "predicted_category": "Electrical", "confidence": .8, "is_confident": True,
    })
    service = ComplaintService(db_session)
    first = service.create_complaint(student, ComplaintCreate(title="First broken fan", description="The fan stopped working in the west hall.", location="West hall"))
    second = service.create_complaint(student, ComplaintCreate(title="Second broken fan", description="Another fan has stopped working in the east hall.", location="East hall"))
    db_session.refresh(student)
    assert first.reward_points_awarded == 10
    assert second.reward_points_awarded == 0
    assert second.id and student.reward_points == 10


def test_password_reset_token_is_single_use_and_revokes_sessions(db_session, monkeypatch):
    student = user(db_session, "student1@campusfix.edu")
    token = "a" * 40
    db_session.add(PasswordResetToken(user_id=student.id, token_hash=sha256(token.encode()).hexdigest(),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=20)))
    db_session.add(RefreshSession(user_id=student.id, token_jti="old-session", expires_at=datetime.now(timezone.utc) + timedelta(days=1)))
    db_session.commit()
    monkeypatch.setattr("app.services.auth_service.get_password_hash", lambda _: "new-hash")
    AuthService(db_session).reset_password(ResetPasswordRequest(token=token, new_password="BetterPass123!"))
    db_session.refresh(student)
    assert student.hashed_password == "new-hash" and student.token_version == 1
    assert db_session.query(RefreshSession).one().revoked_at is not None
    try:
        AuthService(db_session).reset_password(ResetPasswordRequest(token=token, new_password="AnotherPass123!"))
        assert False, "reset tokens cannot be reused"
    except UnauthorizedAccessException:
        pass


def test_deactivated_staff_is_revoked_and_cannot_receive_assignments(db_session):
    admin = user(db_session, "admin@campusfix.edu")
    staff = user(db_session, "electrical.staff@campusfix.edu")
    complaint = db_session.query(Complaint).one()
    db_session.add(RefreshSession(user_id=staff.id, token_jti="staff-session", expires_at=datetime.now(timezone.utc) + timedelta(days=1)))
    db_session.commit()
    StaffService(db_session).set_staff_active(admin, staff.id, False)
    db_session.refresh(staff)
    assert not staff.is_active and staff.token_version == 1
    assert db_session.query(RefreshSession).one().revoked_at is not None
    try:
        StaffService(db_session).assign_complaint_to_staff(admin, complaint.id, staff.id)
        assert False, "inactive staff cannot be assigned"
    except ForbiddenOperationException:
        pass


def test_admin_analytics_includes_overdue_pending_assignment(db_session, monkeypatch):
    assignment = db_session.query(StaffAssignment).one()
    assignment.assigned_at = datetime.now(timezone.utc) - timedelta(hours=30)
    db_session.commit()
    monkeypatch.setattr("app.services.analytics_service.settings.PENDING_ASSIGNMENT_OVERDUE_HOURS", 24)
    metrics = AnalyticsService(db_session).get_admin_metrics()
    assert metrics["overdue_assignments"] == 1
    assert metrics["overdue_work"][0]["assignment_status"] == "PENDING"


def test_admin_category_update_marks_human_review(db_session):
    admin = user(db_session, "admin@campusfix.edu")
    complaint = db_session.query(Complaint).one()
    updated = ComplaintService(db_session).update_complaint_admin(
        complaint.id, admin, category="Electrical",
    )
    assert updated.category_reviewed_by_id == admin.id
    assert updated.category_reviewed_at is not None
