# MBA Study Hub — Backend API

Production-grade, asynchronous backend REST API for the **MBA Semester 1 Study Platform** built using Python 3.13, FastAPI, SQLAlchemy 2.0, Pydantic v2, Alembic, and Pytest.

---

## 🌟 Tech Stack

- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python 3.13)
- **ORM**: [SQLAlchemy 2.0](https://www.sqlalchemy.org/)
- **Data Validation & Schemas**: [Pydantic v2](https://docs.pydantic.dev/)
- **Database**:
  - Local Development: **SQLite** (`data/mba_study_hub.db`)
  - Production: **PostgreSQL** (Connection string configurable via `.env`)
- **Database Migrations**: [Alembic](https://alembic.sqlalchemy.org/)
- **Authentication**: JWT Access Tokens (`PyJWT`) with `bcrypt` password hashing
- **Background Tasks & Reminders**: [APScheduler](https://apscheduler.readthedocs.io/)
- **Automated Testing**: [Pytest](https://docs.pytest.org/) & `pytest-asyncio`

---

## 📂 Project Architecture

```
backend/
├── alembic/                  # Alembic migration scripts and environment
│   ├── versions/             # Auto-generated database migration versions
│   └── env.py                # Alembic configuration linking SQLAlchemy Base
├── app/
│   ├── config.py             # Pydantic BaseSettings environment configuration
│   ├── database.py           # Engine, SessionLocal, and get_db dependency
│   ├── main.py               # FastAPI application entrypoint with CORS & lifespans
│   ├── core/
│   │   ├── dependencies.py   # Auth and RBAC dependencies (get_current_user, require_admin)
│   │   ├── rate_limiter.py   # Sliding-window rate limiter for auth endpoints
│   │   ├── scheduler.py      # APScheduler background reminder worker
│   │   └── security.py       # Bcrypt hashing & PyJWT token generator
│   ├── models/               # SQLAlchemy Declarative Models
│   │   ├── user.py           # users table (student/admin, streak tracking)
│   │   ├── subject.py        # subjects and syllabus_sources tables
│   │   ├── unit.py           # units table
│   │   ├── question.py       # questions table (Easy, Medium, Hard, JSON options)
│   │   ├── quiz.py           # quiz_attempts and quiz_responses tables
│   │   ├── resource.py       # resources table (books, question papers, solved papers)
│   │   └── reminder.py       # reminder_preferences table
│   ├── routers/              # REST Endpoints under /api/v1
│   │   ├── auth.py           # Registration, login, rate-limiting, and profile
│   │   ├── subjects.py       # Subject CRUD, unit listing, verified syllabus sources
│   │   ├── questions.py      # Question filtering, CRUD, JSON/CSV imports, admin approval
│   │   ├── quiz.py           # Daily 30Q quiz, unit exam, subject exam, scoring & idempotency
│   │   ├── resources.py      # PDF upload validation, preview, download, solved papers
│   │   ├── reminders.py      # Reminder preferences and verified delivery trigger
│   │   ├── analytics.py      # Streak, subject & difficulty accuracy, weak topic analysis
│   │   └── admin.py          # Admin metrics, pending question approval, batch approval
│   ├── schemas/              # Pydantic v2 validation models
│   ├── seed/                 # Database seeding script
│   └── services/             # Core business logic
│       ├── quiz_service.py   # 30Q 10/10/10 generator, deterministic rotation, anti-repeat
│       ├── scoring_service.py# 1 mark/Q scoring, post-submit explanations, duplicate check
│       ├── storage_service.py# Safe PDF file validation (<=50MB) and storage
│       ├── question_import.py# JSON & CSV parsing with duplicate detection
│       └── notification_service.py # Verified notification delivery integration
├── data/
│   ├── samples/              # Sample JSON and CSV question import files
│   └── uploads/              # Local uploaded PDFs (books, papers, solved papers)
├── tests/                    # 20 Automated Pytest tests
│   ├── conftest.py           # In-memory test DB, client fixtures, mock tokens
│   ├── test_auth.py          # Auth tests
│   ├── test_quiz.py          # Quiz generation, 10/10/10 distribution, pool errors
│   ├── test_scoring.py       # Scoring calculation, post-submit review, duplicate block
│   ├── test_resources.py     # PDF validation, solved paper separation & disclaimer
│   └── test_admin.py         # Admin RBAC, JSON import, duplicate check, approvals
├── .env.example              # Sample environment configuration template
├── pytest.ini                # Pytest configuration
├── requirements.txt          # Python package requirements
└── README.md
```

---

## 🚀 Step-by-Step Setup Guide

### 1. Prerequisites
- Python 3.10+ (Tested on Python 3.13)
- Git

### 2. Create and Activate Virtual Environment
```bash
cd backend
python -m venv venv

# On Windows:
venv\Scripts\activate

# On Linux / macOS:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Default `.env` configuration uses SQLite (`sqlite:///./data/mba_study_hub.db`). To use PostgreSQL in production, set:
```env
DATABASE_URL=postgresql://user:password@localhost:5432/mba_study_hub_db
```

### 5. Apply Database Migrations
```bash
alembic upgrade head
```

### 6. Seed Baseline Data
Seeds the 8 Semester 1 subjects, verified syllabus units, 30+ categorized MCQs across Easy/Medium/Hard, default Admin & Student accounts, and sample PDF files:
```bash
python -m app.seed.seed_data
```

### Default Credentials:
- **Admin**:
  - Email: `admin@mbahub.edu`
  - Password: `AdminPass123!`
- **Student**:
  - Email: `student@mbahub.edu`
  - Password: `StudentPass123!`

---

## 🏃 Running the Server

Start the FastAPI application with Uvicorn:
```bash
uvicorn app.main:app --reload --port 8000
```

- API Base URL: `http://localhost:8000`
- Interactive Swagger UI Docs: `http://localhost:8000/docs`
- ReDoc Documentation: `http://localhost:8000/redoc`

---

## 🧪 Running Automated Tests

Run the full automated test suite (all 20 unit and integration tests):
```bash
pytest -v
```

### Test Coverage Highlights:
- ✅ Authentication, password hashing, JWT issue & expiration
- ✅ Role-Based Access Control (Admin vs Student enforcement)
- ✅ 30-Question Quiz Generation with **exact 10 Easy, 10 Medium, 10 Hard** distribution
- ✅ Security: Correct answers and explanations are **hidden** prior to submission
- ✅ Insufficient question bank handling: Returns descriptive 400 error and never invents fake questions
- ✅ 1 mark per question scoring (out of 30)
- ✅ Prevention of duplicate submissions for the same quiz attempt
- ✅ PDF file upload validation (rejects non-PDFs and files exceeding 50MB)
- ✅ Separation of official question papers and solved papers with disclaimers
- ✅ JSON/CSV question import with duplicate prevention and admin approval flow

---

## 📑 Core API Reference (`/api/v1`)

### Authentication (`/api/v1/auth`)
| Method | Endpoint | Access | Description |
|---|---|---|---|
| `POST` | `/api/v1/auth/register` | Public | Register new student account |
| `POST` | `/api/v1/auth/login` | Public (Rate-limited) | Login and receive JWT access token |
| `GET` | `/api/v1/auth/me` | Authenticated | Retrieve authenticated user profile |
| `PUT` | `/api/v1/auth/me` | Authenticated | Update user profile |

### Subjects & Units (`/api/v1/subjects`)
| Method | Endpoint | Access | Description |
|---|---|---|---|
| `GET` | `/api/v1/subjects` | Authenticated | List all 8 Semester 1 subjects with metrics |
| `POST` | `/api/v1/subjects` | Admin | Create new subject |
| `GET` | `/api/v1/subjects/{id}` | Authenticated | Get subject details |
| `PUT` | `/api/v1/subjects/{id}` | Admin | Update subject |
| `DELETE`| `/api/v1/subjects/{id}` | Admin | Delete subject |
| `GET` | `/api/v1/subjects/{id}/units` | Authenticated | List verified units under subject |
| `POST` | `/api/v1/subjects/{id}/units` | Admin | Add verified unit under subject |
| `GET` | `/api/v1/subjects/{id}/syllabus-sources` | Authenticated | View official university syllabus provenance |

### Question Bank (`/api/v1/questions`)
| Method | Endpoint | Access | Description |
|---|---|---|---|
| `GET` | `/api/v1/questions` | Authenticated | List/filter questions by subject, unit, difficulty |
| `POST` | `/api/v1/questions` | Admin | Create single question with 4 options |
| `POST` | `/api/v1/questions/import`| Admin | Import questions from JSON or CSV file |
| `PUT` | `/api/v1/questions/{id}/approve` | Admin | Approve imported question for publishing |

### Quiz & Examination Engine (`/api/v1/quiz`)
| Method | Endpoint | Access | Description |
|---|---|---|---|
| `POST` | `/api/v1/quiz/daily/start` | Student/Admin | Generate 30Q daily quiz (10/10/10, answers hidden) |
| `POST` | `/api/v1/quiz/unit/{unit_id}/start` | Student/Admin | Generate 30Q unit exam (validates 10/10/10) |
| `POST` | `/api/v1/quiz/subject/{subject_id}/start` | Student/Admin | Generate 30Q subject exam (validates 10/10/10) |
| `POST` | `/api/v1/quiz/submit` | Student/Admin | Submit answers, calculate score out of 30, reveal explanations |
| `GET` | `/api/v1/quiz/attempts` | Student/Admin | List user's quiz attempt history |
| `GET` | `/api/v1/quiz/attempts/{id}`| Student/Admin | View full attempt review with explanations |

### Library Resources (`/api/v1/resources`)
| Method | Endpoint | Access | Description |
|---|---|---|---|
| `POST` | `/api/v1/resources/upload`| Admin | Upload verified PDF (book, question paper, solved paper) |
| `GET` | `/api/v1/resources/books` | Authenticated | List reference textbooks |
| `GET` | `/api/v1/resources/papers` | Authenticated | List original university question papers |
| `GET` | `/api/v1/resources/solved-papers` | Authenticated | List solved papers with faculty verification status |
| `GET` | `/api/v1/resources/{id}/preview` | Authenticated | Authenticated inline PDF preview |
| `GET` | `/api/v1/resources/{id}/download`| Authenticated | Authenticated PDF download |

### Reminders & Analytics (`/api/v1/reminders`, `/api/v1/analytics`)
| Method | Endpoint | Access | Description |
|---|---|---|---|
| `GET` | `/api/v1/reminders/preference` | Authenticated | Get student practice reminder preferences |
| `PUT` | `/api/v1/reminders/preference` | Authenticated | Update preferred time, timezone, and channel |
| `POST` | `/api/v1/reminders/test-trigger` | Authenticated | Test notification dispatch with provider confirmation |
| `GET` | `/api/v1/analytics/dashboard` | Authenticated | Get streak, subject accuracy, difficulty accuracy, weak topics |
