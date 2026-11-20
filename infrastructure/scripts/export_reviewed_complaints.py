"""Export reviewed complaint text for a controlled ML evaluation dataset."""
import argparse
import csv
import hashlib
import re
import sys
from pathlib import Path

repository_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(repository_root / "backend"))
sys.path.insert(0, str(repository_root))

from app.db.session import SessionLocal  # noqa: E402
from app.models.complaint import Complaint  # noqa: E402

EMAIL = re.compile(r"\b[\w.+-]+@[\w.-]+\.\w+\b", re.I)
PHONE = re.compile(r"(?<!\w)(?:\+?\d[\d ().-]{7,}\d)(?!\w)")


def anonymize(text: str) -> str:
    text = EMAIL.sub(" [EMAIL] ", text)
    text = PHONE.sub(" [PHONE] ", text)
    return re.sub(r"\s+", " ", text).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--force", action="store_true", help="Replace an existing output file")
    args = parser.parse_args()
    if args.output.exists() and not args.force:
        parser.error(f"{args.output} already exists; pass --force to replace it")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    db = SessionLocal()
    try:
        records = db.query(Complaint).filter(Complaint.category_reviewed_by_id.isnot(None)).order_by(Complaint.id).all()
        seen = set()
        rows = []
        for record in records:
            text = anonymize(f"{record.title} {record.description}")
            key = hashlib.sha256(text.lower().encode("utf-8")).hexdigest()
            if key in seen or not text:
                continue
            seen.add(key)
            rows.append({"text": text, "category": record.category, "issue_template": key[:16]})
        with args.output.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=["text", "category", "issue_template"])
            writer.writeheader()
            writer.writerows(rows)
        print(f"Exported {len(rows)} reviewed, de-identified records to {args.output}")
        print("Review the output for identifying details before using or sharing it.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
