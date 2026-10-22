import pytest
from app.models.subject import Subject
from app.models.unit import Unit

def test_daily_quiz_generation_and_distribution(client, student_headers):
    """
    Requirements:
    - Exactly 30 questions
    - Exactly 10 Easy, 10 Medium, 10 Hard questions
    - Answers and explanations must NOT be exposed in exam session
    """
    response = client.post("/api/v1/quiz/daily/start", json={"date_str": "2026-10-22"}, headers=student_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total_questions"] == 30
    assert len(data["questions"]) == 30

    questions = data["questions"]
    easy_count = sum(1 for q in questions if q["difficulty"] == "easy")
    medium_count = sum(1 for q in questions if q["difficulty"] == "medium")
    hard_count = sum(1 for q in questions if q["difficulty"] == "hard")

    # VERIFY EXACT 10/10/10 DIFFICULTY DISTRIBUTION
    assert easy_count == 10, f"Expected 10 easy questions, got {easy_count}"
    assert medium_count == 10, f"Expected 10 medium questions, got {medium_count}"
    assert hard_count == 10, f"Expected 10 hard questions, got {hard_count}"

    # VERIFY ANSWERS AND EXPLANATIONS ARE NOT EXPOSED BEFORE SUBMISSION
    for q in questions:
        assert "correct_answer" not in q, "Security violation: correct_answer exposed prior to submission!"
        assert "explanation" not in q, "Security violation: explanation exposed prior to submission!"
        assert len(q["options"]) == 4

def test_unit_exam_generation(client, student_headers, db_session):
    unit = db_session.query(Unit).filter(Unit.title == "Test Unit 1 Foundations").first()
    assert unit is not None

    response = client.post(f"/api/v1/quiz/unit/{unit.id}/start", headers=student_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total_questions"] == 30
    assert len(data["questions"]) == 30

    easy_count = sum(1 for q in data["questions"] if q["difficulty"] == "easy")
    medium_count = sum(1 for q in data["questions"] if q["difficulty"] == "medium")
    hard_count = sum(1 for q in data["questions"] if q["difficulty"] == "hard")

    assert easy_count == 10
    assert medium_count == 10
    assert hard_count == 10

def test_subject_exam_generation(client, student_headers, db_session):
    subject = db_session.query(Subject).filter(Subject.code == "TEST-OB").first()
    assert subject is not None

    response = client.post(f"/api/v1/quiz/subject/{subject.id}/start", headers=student_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total_questions"] == 30

def test_insufficient_question_bank_handling(client, student_headers, db_session):
    """
    Requirements:
    - Return a clear error if the question bank is insufficient.
    - Never silently replace missing questions with invented questions.
    """
    sparse_unit = db_session.query(Unit).filter(Unit.title == "Sparse Unit").first()
    assert sparse_unit is not None

    response = client.post(f"/api/v1/quiz/unit/{sparse_unit.id}/start", headers=student_headers)
    # Must fail with 400 Bad Request
    assert response.status_code == 400
    error_msg = response.json()["detail"]
    assert "Insufficient questions" in error_msg
    assert "Required exactly 10" in error_msg
