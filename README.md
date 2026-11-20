# CampusFix

CampusFix is a role-based campus maintenance platform. Students file and track issues, operations staff accept assignments and record resolutions, and administrators triage requests and review service metrics. A versioned text classifier suggests complaint categories and abstains when its margin is low.

## Product capabilities

- Student issue submission, searchable ticket history, status timeline, optional evidence, resolution feedback, and AI category suggestions.
- Campus Impact rewards: 10 points for issue reports up to a configurable daily cap and 5 points for resolution feedback, with a student-only balance and milestone tracker.
- Staff assignment queues with explicit accept/reject and resolution workflows.
- Admin complaint triage, assignment, staff account creation/deactivation, category and priority management, overdue assignment tracking, and operational metrics.
- Role checked API access, password hashing, rotating and revocable refresh tokens, request validation, upload type/size checks, structured logs, and API health endpoint.
- Alembic database migration path and containerized frontend/backend deployment.

## Repository map

```text
frontend/                 React 19 + Vite application and Nginx deployment
backend/app/api/v1/       Versioned FastAPI routes
backend/app/services/     Complaint, staff, auth, and analytics workflows
backend/app/models/       SQLAlchemy entities
backend/app/db/           Engine, session, and Alembic migrations
backend/tests/            Domain and model regression tests
ml/data/                  Complaint dataset
ml/src/training/          Grouped validation and versioned model training
ml/src/evaluation/        Manual robustness diagnostics
ml/models/                Versioned classifier artifacts and active manifest
ml/reports/               Evaluation reports
infrastructure/scripts/   Seeding, reviewed-label export, and attachment retention
docs/campus-pilot-plan.md Four-week campus pilot and evaluation workflow
```

## Local setup (Windows PowerShell)

Use Python 3.11 or 3.12 and Node.js 22. Run these commands from the repository root:

```powershell
python -m venv backend/venv
./backend/venv/Scripts/Activate.ps1
python -m pip install -r backend/requirements.txt
$env:PYTHONPATH = (Resolve-Path ./backend).Path
Copy-Item .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Set the generated value as `SECRET_KEY` in `.env`. Keep `.env` out of source control. The default local database is `campusfix.db` in the repository root, matching the seeded demo database; migrate it before starting the API:

```powershell
alembic -c backend/alembic.ini upgrade head
python infrastructure/scripts/seed_db.py
uvicorn app.main:app --app-dir backend --reload --port 8000
```

In a second terminal:

```powershell
cd frontend
npm ci
npm run dev
```

Open `http://localhost:5173`. API documentation is at `http://localhost:8000/docs`; health is at `http://localhost:8000/health`.

### Demo credentials

The seed script creates these local demonstration accounts:

| Role | Email | Password |
| --- | --- | --- |
| Admin | `admin@campusfix.edu` | `Admin@12345` |
| Staff | `electrical.staff@campusfix.edu` | `Staff@12345` |
| Staff | `it.staff@campusfix.edu` | `Staff@12345` |
| Staff | `plumbing.staff@campusfix.edu` | `Staff@12345` |
| Student | `student1@campusfix.edu` | `Student@12345` |

These accounts and passwords are for local demos only. Create new accounts and credentials for a real campus.

## Configuration

Copy `.env.example` to `.env`. Important settings:

| Variable | Purpose |
| --- | --- |
| `SECRET_KEY` | Required signing key; production startup fails if missing |
| `ENVIRONMENT` | `development` or `production` |
| `DATABASE_URL` | SQLAlchemy URL; SQLite is suitable for local development |
| `CORS_ORIGINS` | JSON array of trusted frontend origins |
| `ML_MODEL_PATH` | Versioned artifact or `ml/models/active-model.json` |
| `ML_CONFIDENCE_THRESHOLD` | SVM margin abstention threshold (default `0.45`) |
| `MAX_UPLOAD_SIZE_MB` | Attachment limit (default `10`) |
| `UPLOAD_DIR` | Private attachment storage directory |
| `DAILY_ISSUE_REWARD_LIMIT` | Report points per student in a rolling 24 hours (default `30`) |
| `SMTP_*` | Campus email provider used for password recovery |
| `FRONTEND_BASE_URL` | Public app origin used to build recovery links |
| `PENDING_ASSIGNMENT_OVERDUE_HOURS` | Pending assignment alert threshold (default `24`) |
| `ACTIVE_ASSIGNMENT_OVERDUE_HOURS` | Accepted work alert threshold (default `72`) |

Uploaded attachments are served through an authenticated endpoint and checked against complaint visibility. Do not mount the upload directory as public static content. For multi-instance production, use private object storage with equivalent authorization.

Password recovery uses hashed, one-time 30-minute tokens, a generic response to avoid exposing whether an email is registered, and a per-account request limit. Configure SMTP and `FRONTEND_BASE_URL` to deliver reset links; without SMTP, reset links are not returned in API responses. Preview evidence cleanup with `python infrastructure/scripts/attachments_retention.py --retention-days 365`. It is dry-run by default; after policy approval it can apply with `--apply --actor-admin-id <active-admin-id>` and writes an audit event.

## Machine learning evaluation and training

The training script removes exact duplicate complaint text, splits by `issue_template` to reduce near-duplicate leakage, compares word and character TF-IDF models, selects by macro F1, writes a timestamped artifact and evaluation report, then updates the hash-checked active-model manifest. Existing model artifacts remain intact.

```powershell
$env:PYTHONPATH = (Resolve-Path ./backend).Path
python -m ml.src.training.train_classifier
python -m ml.src.evaluation.evaluate_robustness
```

The current best grouped holdout result is **62.4% accuracy and 0.653 macro F1** (character n-gram LinearSVC). The separate hand-written 19-case in-category diagnostic suite reached **89.5% accuracy** with a 0.45 margin abstention threshold. Neither result is a production accuracy guarantee: the dataset is templated and the diagnostic set is small. The inference response's score is an uncalibrated ranking signal, not a probability. Collect and label real campus complaints before setting an operational SLA or using these predictions without human review. Admin-confirmed categories are stored separately from model suggestions. To prepare a controlled evaluation export, run `python infrastructure/scripts/export_reviewed_complaints.py ml/data/reviewed-campus.csv`; it strips common email/phone patterns, deduplicates text, and refuses to overwrite by default. Review for identifying details before use; this is not complete de-identification. Follow [the pilot plan](docs/campus-pilot-plan.md) for reviewer agreement and held-out evaluation.

## Checks

```powershell
$env:PYTHONPATH = (Resolve-Path ./backend).Path
python -m pytest backend/tests
Push-Location frontend
npm ci
npm run build
npm run lint
Pop-Location
```

## Docker

Set a strong `SECRET_KEY` in the shell or `.env`, then run:

```powershell
docker compose up --build
```

Copy `.env.example` to `.env` first, replace `SECRET_KEY`, `POSTGRES_PASSWORD`, and the password embedded in `DATABASE_URL` with matching strong values, and add SMTP credentials if password recovery email is needed. URL-encode special characters in the database URL password.

The frontend is served on port 80 and the backend on port 8000. Compose uses PostgreSQL, applies Alembic migrations at backend startup, and persists the database and uploads in named volumes. Replace example passwords in `.env`, configure SMTP, and set a unique strong `SECRET_KEY`. Before public production use, add managed database backups and restore drills, private object storage for multi-instance deployments, TLS termination, monitoring/alerting, and a shared rate limiter. This is a single-host deployment foundation, not a complete managed production environment.

## API groups

- `/api/v1/auth` — registration, login, rotating refresh, revocation, current session, and email recovery
- `POST /api/v1/auth/change-password` — change a password after verifying the current password and invalidate active sessions
- `POST /api/v1/auth/forgot-password` and `/reset-password` — request and consume a one-time email reset link
- `/api/v1/complaints` — complaints, status timeline, feedback, and authorized evidence download
- `/api/v1/staff` — assignments and work queue
- `/api/v1/admin` — staff accounts and activation, assignment, and triage updates
- `/api/v1/analytics` — operational overview
- `/api/v1/ml/predict` — category suggestions
- `/api/v1/rewards/me` — signed-in student's impact points and milestone progress
- `/health` — service health
