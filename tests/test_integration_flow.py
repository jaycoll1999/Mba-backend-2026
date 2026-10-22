import pytest
import io
import json
from app.models.subject import Subject
from app.models.unit import Unit
from app.models.question import Question, DifficultyLevel
from app.models.resource import Resource, ResourceType

def test_full_student_integration_flow(client, db_session):
    """
    Requirement 10: Integration test covering:
    - User login
    - Quiz generation (30 questions: 10 Easy, 10 Medium, 10 Hard)
    - Verification that answers are NOT revealed before submission
    - Quiz submission & scoring calculation
    - Quiz attempt history & Progress analytics dashboard
    - File listing (books, papers, solved papers) and authorized file access
    """
    # 1. User Login
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "test_student@mbahub.edu", "password": "StudentPass123!"}
    )
    assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
    token_data = login_resp.json()
    assert "access_token" in token_data
    token = token_data["access_token"]
    student_headers = {"Authorization": f"Bearer {token}"}

    # 2. Subject & Unit listing
    subjects_resp = client.get("/api/v1/subjects", headers=student_headers)
    assert subjects_resp.status_code == 200
    subjects = subjects_resp.json()
    assert len(subjects) >= 1
    test_subject = next(s for s in subjects if s["code"] == "TEST-OB")
    subject_id = test_subject["id"]

    units_resp = client.get(f"/api/v1/subjects/{subject_id}/units", headers=student_headers)
    assert units_resp.status_code == 200
    units = units_resp.json()
    assert len(units) >= 1
    unit_id = units[0]["id"]

    # 3. Quiz Generation (Exact 30 questions: 10 Easy, 10 Medium, 10 Hard)
    quiz_resp = client.post(
        "/api/v1/quiz/daily/start",
        json={"date_str": "2026-10-22"},
        headers=student_headers
    )
    assert quiz_resp.status_code == 200
    quiz_data = quiz_resp.json()
    attempt_id = quiz_data["attempt_id"]
    questions = quiz_data["questions"]

    assert len(questions) == 30
    assert quiz_data["total_questions"] == 30

    easy_count = sum(1 for q in questions if q["difficulty"] == "easy")
    medium_count = sum(1 for q in questions if q["difficulty"] == "medium")
    hard_count = sum(1 for q in questions if q["difficulty"] == "hard")

    assert easy_count == 10, f"Expected 10 easy questions, got {easy_count}"
    assert medium_count == 10, f"Expected 10 medium questions, got {medium_count}"
    assert hard_count == 10, f"Expected 10 hard questions, got {hard_count}"

    # Verify answers and explanations are NEVER revealed before submission
    for q in questions:
        assert "correct_answer" not in q, f"Exposed correct answer in question {q['id']}"
        assert "explanation" not in q, f"Exposed explanation in question {q['id']}"
        assert len(q["options"]) == 4

    # 4. Quiz Submission & Scoring Validation
    # Look up correct answers from database for exact test scoring
    q_lookup = {q.id: q.correct_answer for q in db_session.query(Question).all()}

    # Answer 20 questions correctly, 10 incorrectly
    answers = []
    for idx, q in enumerate(questions):
        correct_ans = q_lookup[q["id"]]
        if idx < 20:
            selected = correct_ans
        else:
            selected = next(opt for opt in q["options"] if opt != correct_ans)
        answers.append({"question_id": q["id"], "selected_option": selected})

    submit_payload = {
        "attempt_id": attempt_id,
        "answers": answers,
        "time_taken_seconds": 450
    }
    submit_resp = client.post("/api/v1/quiz/submit", json=submit_payload, headers=student_headers)
    assert submit_resp.status_code == 200
    result = submit_resp.json()

    assert result["score"] == 20.0
    assert result["total_marks"] == 30.0
    assert result["percentage"] == round((20.0 / 30.0) * 100, 2)
    assert result["is_submitted"] is True

    # After submission, explanations and correct answers ARE revealed
    assert len(result["responses"]) == 30
    for resp in result["responses"]:
        assert "correct_answer" in resp
        assert "explanation" in resp
        assert resp["explanation"] is not None

    # 5. Quiz Attempt History Check
    attempts_resp = client.get("/api/v1/quiz/attempts", headers=student_headers)
    assert attempts_resp.status_code == 200
    attempts = attempts_resp.json()
    assert len(attempts) >= 1
    saved_attempt = next(a for a in attempts if a["id"] == attempt_id)
    assert saved_attempt["score"] == 20.0
    assert saved_attempt["total_questions"] == 30
    assert saved_attempt["percentage"] == round((20.0 / 30.0) * 100, 2)

    # 6. Progress & Analytics Dashboard Check
    analytics_resp = client.get("/api/v1/analytics/dashboard", headers=student_headers)
    assert analytics_resp.status_code == 200
    analytics_data = analytics_resp.json()
    assert "total_quizzes_taken" in analytics_data
    assert analytics_data["total_quizzes_taken"] >= 1
    assert "average_percentage" in analytics_data
    assert "recent_attempts" in analytics_data
    assert "streak" in analytics_data

    # 7. File Listing (Books, Question Papers, Solved Papers)
    books_resp = client.get("/api/v1/resources/books", headers=student_headers)
    assert books_resp.status_code == 200
    assert isinstance(books_resp.json(), list)

    papers_resp = client.get("/api/v1/resources/papers", headers=student_headers)
    assert papers_resp.status_code == 200
    assert isinstance(papers_resp.json(), list)

    solved_resp = client.get("/api/v1/resources/solved-papers", headers=student_headers)
    assert solved_resp.status_code == 200
    assert isinstance(solved_resp.json(), list)

    # 8. Reminders Check & Update
    reminders_get = client.get("/api/v1/reminders/preference", headers=student_headers)
    assert reminders_get.status_code == 200
    rem_data = reminders_get.json()
    assert "reminder_time" in rem_data

    reminders_update = client.put(
        "/api/v1/reminders/settings",
        json={"reminder_time": "10:30", "is_enabled": True, "notification_channel": "in_app"},
        headers=student_headers
    )
    assert reminders_update.status_code == 200
    assert reminders_update.json()["reminder_time"] == "10:30"


def test_faculty_admin_integration_flow(client, db_session):
    """
    Requirement 10: Faculty / Admin flow testing
    - Faculty login
    - Overview / admin statistics
    - Subject exam generation
    """
    # 1. Admin Login
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "test_admin@mbahub.edu", "password": "AdminPass123!"}
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {token}"}

    # 2. Admin Stats
    stats_resp = client.get("/api/v1/admin/stats", headers=admin_headers)
    assert stats_resp.status_code == 200
    stats = stats_resp.json()
    assert "total_students" in stats
    assert "total_questions" in stats

    # 3. Subject Exam 30-Question Structure
    subject = db_session.query(Subject).filter(Subject.code == "TEST-OB").first()
    exam_resp = client.post(f"/api/v1/quiz/subject/{subject.id}/start", headers=admin_headers)
    assert exam_resp.status_code == 200
    exam_data = exam_resp.json()
    assert exam_data["total_questions"] == 30
    assert len(exam_data["questions"]) == 30
