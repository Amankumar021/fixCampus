"""Preview or retire old evidence from terminal complaints; dry-run by default."""
import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

repository_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(repository_root / "backend"))
sys.path.insert(0, str(repository_root))

from app.core.config import settings  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.models.activity import ComplaintTimeline  # noqa: E402
from app.models.complaint import Complaint, ComplaintStatus  # noqa: E402
from app.models.user import User, UserRole  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--retention-days", type=int, default=365)
    parser.add_argument("--apply", action="store_true", help="Remove evidence links and files")
    parser.add_argument("--actor-admin-id", type=int, help="Required for --apply; records an audit event")
    args = parser.parse_args()
    if args.retention_days < 1:
        parser.error("--retention-days must be positive")
    if args.apply and not args.actor_admin_id:
        parser.error("--actor-admin-id is required with --apply")
    cutoff = (datetime.now(timezone.utc) - timedelta(days=args.retention_days)).replace(tzinfo=None)
    root = Path(settings.UPLOAD_DIR).expanduser().resolve()
    db = SessionLocal()
    removed_files = []
    try:
        if args.apply:
            actor = db.query(User).filter(User.id == args.actor_admin_id, User.role == UserRole.ADMIN, User.is_active.is_(True)).first()
            if not actor:
                parser.error("--actor-admin-id must identify an active administrator")
        records = db.query(Complaint).filter(
            Complaint.status.in_([ComplaintStatus.CLOSED, ComplaintStatus.REJECTED]),
            Complaint.attachment_url.isnot(None),
            Complaint.updated_at < cutoff,
        ).all()
        print(f"{len(records)} attachment(s) match the {args.retention_days}-day retention rule.")
        for record in records:
            if not record.attachment_url.startswith("/uploads/"):
                print(f"Skipping unexpected attachment reference on {record.ticket_id}")
                continue
            filename = record.attachment_url.removeprefix("/uploads/")
            candidate = (root / filename).resolve()
            if candidate.parent != root or not filename:
                print(f"Skipping unsafe attachment reference on {record.ticket_id}")
                continue
            print(f"{record.ticket_id}: {filename}")
            if args.apply:
                record.attachment_url = None
                db.add(ComplaintTimeline(
                    complaint_id=record.id,
                    actor_id=args.actor_admin_id,
                    action="ATTACHMENT_RETIRED",
                    previous_status=record.status.value,
                    new_status=record.status.value,
                    comment=f"Evidence retired under the {args.retention_days}-day campus retention schedule.",
                ))
                removed_files.append(candidate)
        if args.apply:
            db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
    if args.apply:
        for path in removed_files:
            path.unlink(missing_ok=True)
        print(f"Retired {len(removed_files)} attachment(s).")
    else:
        print("Dry run only. Add --apply --actor-admin-id <admin id> to apply after campus approval.")


if __name__ == "__main__":
    main()
