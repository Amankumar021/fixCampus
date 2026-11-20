import sys
from pathlib import Path

# Add backend directory to sys.path
repository_root = Path(__file__).resolve().parents[2]
backend_path = repository_root / "backend"
sys.path.insert(0, str(backend_path))
sys.path.insert(0, str(repository_root))

from app.db.session import SessionLocal, engine
from app.models import Base, User, UserRole, Complaint, ComplaintStatus, ComplaintPriority, StaffAssignment, AssignmentStatus, ComplaintTimeline
from app.core.security import get_password_hash


def seed_database():
    print("Creating tables if not present...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. Admin
        admin_email = "admin@campusfix.edu"
        admin = db.query(User).filter(User.email == admin_email).first()
        if not admin:
            admin = User(
                email=admin_email,
                hashed_password=get_password_hash("Admin@12345"),
                full_name="Chief Campus Administrator",
                role=UserRole.ADMIN,
                department="Central Administration",
                phone_number="+91-9876543210",
                is_active=True,
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)
            print(f"Created Admin: {admin.email} (Password: Admin@12345)")

        # 2. Staff Accounts
        staff_data = [
            ("electrical.staff@campusfix.edu", "Ramesh Sharma", "Electrical", "Staff@12345"),
            ("it.staff@campusfix.edu", "Vikram Patel", "IT", "Staff@12345"),
            ("plumbing.staff@campusfix.edu", "Suresh Kumar", "Plumbing", "Staff@12345"),
        ]
        created_staff = []
        for email, name, dept, pwd in staff_data:
            st = db.query(User).filter(User.email == email).first()
            if not st:
                st = User(
                    email=email,
                    hashed_password=get_password_hash(pwd),
                    full_name=name,
                    role=UserRole.STAFF,
                    department=dept,
                    phone_number="+91-9876543211",
                    is_active=True,
                )
                db.add(st)
                db.commit()
                db.refresh(st)
                print(f"Created Staff: {st.email} (Dept: {dept}, Password: {pwd})")
            created_staff.append(st)

        # 3. Student Accounts
        student_data = [
            ("student1@campusfix.edu", "Aarav Gupta", "Student@12345"),
            ("student2@campusfix.edu", "Ananya Singh", "Student@12345"),
        ]
        created_students = []
        for email, name, pwd in student_data:
            stud = db.query(User).filter(User.email == email).first()
            if not stud:
                stud = User(
                    email=email,
                    hashed_password=get_password_hash(pwd),
                    full_name=name,
                    role=UserRole.STUDENT,
                    department="Computer Science",
                    phone_number="+91-9876543220",
                    is_active=True,
                )
                db.add(stud)
                db.commit()
                db.refresh(stud)
                print(f"Created Student: {stud.email} (Password: {pwd})")
            created_students.append(stud)

        # 4. Sample Complaints
        if db.query(Complaint).count() == 0:
            sample_complaints = [
                {
                    "title": "Air Conditioner not cooling in CS Lab 2",
                    "description": "The split AC in CS Lab 2 is blowing warm air and students are facing difficulty in afternoon lectures.",
                    "location": "Academic Block A - 2nd Floor, CS Lab 2",
                    "category": "Electrical",
                    "predicted_category": "Electrical",
                    "prediction_confidence": 0.88,
                    "priority": ComplaintPriority.HIGH,
                    "status": ComplaintStatus.ASSIGNED,
                    "student_id": created_students[0].id,
                },
                {
                    "title": "WiFi Access Point down in Boys Hostel 3",
                    "description": "The campus wireless router in 2nd floor corridor is not broadcasting the SSID.",
                    "location": "Hostel Block 3 - 2nd Floor Corridor",
                    "category": "IT",
                    "predicted_category": "IT",
                    "prediction_confidence": 0.92,
                    "priority": ComplaintPriority.MEDIUM,
                    "status": ComplaintStatus.IN_PROGRESS,
                    "student_id": created_students[1].id,
                },
                {
                    "title": "Broken washbasin faucet leaking continuously",
                    "description": "Water tap in ground floor washroom is broken and water is overflowing continuously.",
                    "location": "Main Building - Ground Floor Restroom",
                    "category": "Plumbing",
                    "predicted_category": "Plumbing",
                    "prediction_confidence": 0.95,
                    "priority": ComplaintPriority.CRITICAL,
                    "status": ComplaintStatus.SUBMITTED,
                    "student_id": created_students[0].id,
                },
            ]

            for item in sample_complaints:
                comp = Complaint(**item)
                db.add(comp)
                db.commit()
                db.refresh(comp)

                # Add timeline entry
                timeline = ComplaintTimeline(
                    complaint_id=comp.id,
                    actor_id=comp.student_id,
                    action="COMPLAINT_SUBMITTED",
                    new_status=comp.status.value,
                    comment="Initial complaint submitted during campus database seeding.",
                )
                db.add(timeline)
                db.commit()

                # If assigned or in progress, create assignment
                if comp.status in [ComplaintStatus.ASSIGNED, ComplaintStatus.IN_PROGRESS]:
                    target_staff = created_staff[0] if comp.category == "Electrical" else created_staff[1]
                    assign = StaffAssignment(
                        complaint_id=comp.id,
                        staff_id=target_staff.id,
                        assigned_by_id=admin.id,
                        status=AssignmentStatus.ACCEPTED if comp.status == ComplaintStatus.IN_PROGRESS else AssignmentStatus.PENDING,
                    )
                    db.add(assign)
                    db.commit()
            print("Successfully seeded sample complaints, assignments, and timelines.")

        print("Database seeding completed successfully!")
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
