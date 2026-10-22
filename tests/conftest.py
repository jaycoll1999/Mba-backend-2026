import os
import sys
import json
import pytest

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models.user import User, UserRole
from app.models.subject import Subject, SyllabusSource
from app.models.unit import Unit
from app.models.question import Question, DifficultyLevel
from app.models.resource import Resource, ResourceType
from app.models.reminder import ReminderPreference
from app.core.security import hash_password, create_access_token

# Use in-memory SQLite for test isolation
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    # Seed baseline fixtures
    # 1. Admin & Student
    admin = User(
        email="test_admin@mbahub.edu",
        hashed_password=hash_password("AdminPass123!"),
        full_name="Test Admin Faculty",
        role=UserRole.ADMIN.value,
        is_active=True
    )
    student = User(
        email="test_student@mbahub.edu",
        hashed_password=hash_password("StudentPass123!"),
        full_name="Test Student User",
        role=UserRole.STUDENT.value,
        streak_days=2,
        last_active_date=None,
        is_active=True
    )
    session.add(admin)
    session.add(student)
    session.commit()
    session.refresh(admin)
    session.refresh(student)

    # Reminders
    session.add(ReminderPreference(user_id=student.id, reminder_time="09:00", notification_channel="in_app"))
    session.commit()

    # 2. Complete Subject with sufficient questions (10 Easy, 10 Medium, 10 Hard)
    full_subject = Subject(
        code="TEST-OB",
        name="Test Organizational Behaviour",
        description="Testing Subject with full question bank",
        credits=3,
        semester=1
    )
    session.add(full_subject)
    session.commit()
    session.refresh(full_subject)

    test_unit = Unit(
        subject_id=full_subject.id,
        unit_number=1,
        title="Test Unit 1 Foundations",
        description="Testing unit description"
    )
    session.add(test_unit)
    session.commit()
    session.refresh(test_unit)

    # Add 12 Easy, 12 Medium, 12 Hard questions
    difficulties = [
        (DifficultyLevel.EASY.value, 12),
        (DifficultyLevel.MEDIUM.value, 12),
        (DifficultyLevel.HARD.value, 12)
    ]
    for diff, count in difficulties:
        for i in range(1, count + 1):
            q = Question(
                subject_id=full_subject.id,
                unit_id=test_unit.id,
                question_text=f"Test Question {diff.upper()} #{i}: What is the core principle?",
                difficulty=diff,
                options_json=json.dumps(["Option A", "Option B", "Option C", "Option D"]),
                correct_answer="Option B",
                explanation=f"Explanation for test question {diff} #{i}.",
                source_reference="MBA Test Bank 2026",
                is_active=True,
                is_approved=True,
                created_by_id=admin.id
            )
            session.add(q)
    session.commit()

    # 3. Insufficient Subject (only 3 questions total - insufficient for 30-question 10/10/10 exam)
    sparse_subject = Subject(
        code="TEST-SPARSE",
        name="Sparse Subject Insufficient Questions",
        description="Testing insufficient question bank handling",
        credits=2,
        semester=1
    )
    session.add(sparse_subject)
    session.commit()
    session.refresh(sparse_subject)

    sparse_unit = Unit(
        subject_id=sparse_subject.id,
        unit_number=1,
        title="Sparse Unit",
        description="Has only 2 questions"
    )
    session.add(sparse_unit)
    session.commit()
    session.refresh(sparse_unit)

    for i in range(2):
        q = Question(
            subject_id=sparse_subject.id,
            unit_id=sparse_unit.id,
            question_text=f"Sparse Question {i}",
            difficulty=DifficultyLevel.EASY.value,
            options_json=json.dumps(["A", "B", "C", "D"]),
            correct_answer="A",
            explanation="Sparse explanation",
            is_active=True,
            is_approved=True,
            created_by_id=admin.id
        )
        session.add(q)
    session.commit()

    yield session

    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def admin_headers(db_session):
    admin = db_session.query(User).filter(User.email == "test_admin@mbahub.edu").first()
    token = create_access_token({"sub": str(admin.id), "role": admin.role})
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def student_headers(db_session):
    student = db_session.query(User).filter(User.email == "test_student@mbahub.edu").first()
    token = create_access_token({"sub": str(student.id), "role": student.role})
    return {"Authorization": f"Bearer {token}"}
