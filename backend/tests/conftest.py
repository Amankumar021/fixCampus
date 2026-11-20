import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.models import User, UserRole, Complaint, ComplaintStatus, ComplaintPriority, RewardTransaction, PasswordResetToken
from app.models.assignment import StaffAssignment, AssignmentStatus
from app.models.activity import ComplaintTimeline, ComplaintFeedback
from app.models.auth_session import RefreshSession
from sqlalchemy import delete
from sqlalchemy import inspect


@pytest.fixture(scope="session")
def test_database():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    yield engine, factory
    engine.dispose()


@pytest.fixture(autouse=True)
def isolated_database(test_database):
    engine, factory = test_database
    if not inspect(engine).has_table("users"):
        Base.metadata.create_all(bind=engine)
    db = factory()
    for model in (PasswordResetToken, RewardTransaction, RefreshSession, ComplaintFeedback, ComplaintTimeline, StaffAssignment, Complaint, User):
        db.execute(delete(model))
    db.commit()
    users = {}
    for email, password, name, role, department in [
        ("admin@campusfix.edu", "Admin@12345", "Campus Administrator", UserRole.ADMIN, None),
        ("electrical.staff@campusfix.edu", "Staff@12345", "Electrical Staff", UserRole.STAFF, "Electrical"),
        ("it.staff@campusfix.edu", "Staff@12345", "IT Staff", UserRole.STAFF, "IT"),
        ("plumbing.staff@campusfix.edu", "Staff@12345", "Plumbing Staff", UserRole.STAFF, "Plumbing"),
        ("student1@campusfix.edu", "Student@12345", "Test Student", UserRole.STUDENT, None),
    ]:
        user = User(email=email, hashed_password="not-used-by-domain-service-tests", full_name=name,
                    role=role, department=department, is_active=True, reward_points=0, token_version=0)
        db.add(user)
        users[email] = user
    db.flush()
    user_ids = {email: user.id for email, user in users.items()}
    complaint = Complaint(title="Broken classroom ceiling fan", description="Ceiling fan is not working in room 12",
                          location="Academic Block 12", category="Electrical", predicted_category="Electrical",
                          prediction_confidence=.9, priority=ComplaintPriority.MEDIUM,
                          status=ComplaintStatus.ASSIGNED, student_id=user_ids["student1@campusfix.edu"])
    db.add(complaint)
    db.flush()
    db.add(StaffAssignment(complaint_id=complaint.id, staff_id=user_ids["electrical.staff@campusfix.edu"], assigned_by_id=user_ids["admin@campusfix.edu"],
                           status=AssignmentStatus.PENDING))
    db.add(ComplaintTimeline(complaint_id=complaint.id, actor_id=user_ids["student1@campusfix.edu"],
                             action="COMPLAINT_SUBMITTED", new_status="SUBMITTED",
                             comment="Seeded isolated test complaint"))
    db.commit()
    db.close()

    yield
@pytest.fixture
def db_session(test_database):
    _, factory = test_database
    session = factory()
    try:
        yield session
    finally:
        session.close()
