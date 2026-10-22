import pytest
from app.models.user import User

from app.models.question import Question

def test_quiz_scoring_and_explanations(client, student_headers, db_session):
    # 1. Start a daily quiz
    start_resp = client.post("/api/v1/quiz/daily/start", json={"date_str": "2026-10-22"}, headers=student_headers)
    assert start_resp.status_code == 200
    quiz_data = start_resp.json()
    attempt_id = quiz_data["attempt_id"]
    questions = quiz_data["questions"]

    # Look up correct answers from database for exact test scoring
    q_lookup = {q.id: q.correct_answer for q in db_session.query(Question).all()}

    # Intentionally answer exactly 25 correctly and 5 incorrectly
    answers = []
    for idx, q in enumerate(questions):
        correct_ans = q_lookup[q["id"]]
        if idx < 25:
            selected = correct_ans
        else:
            selected = next(opt for opt in q["options"] if opt != correct_ans)
        answers.append({"question_id": q["id"], "selected_option": selected})

    submit_payload = {
        "attempt_id": attempt_id,
        "answers": answers,
        "time_taken_seconds": 650
    }

    # 3. Submit
    submit_resp = client.post("/api/v1/quiz/submit", json=submit_payload, headers=student_headers)
    assert submit_resp.status_code == 200
    result = submit_resp.json()

    # Verify score: exactly 25 correct answers = 25.0 marks, total 30 marks
    assert result["score"] == 25.0
    assert result["total_marks"] == 30.0
    assert result["percentage"] == round((25.0 / 30.0) * 100, 2)
    assert result["is_submitted"] is True
    assert result["time_taken_seconds"] == 650

    # Verify answer explanations are revealed after submission
    assert len(result["responses"]) == 30
    for resp in result["responses"]:
        assert "correct_answer" in resp
        assert "explanation" in resp
        assert resp["explanation"] is not None
        assert "is_correct" in resp

def test_duplicate_submission_rejected(client, student_headers):
    """
    Requirement: Validate that the same attempt cannot be submitted repeatedly to manipulate results.
    """
    # Start quiz
    start_resp = client.post("/api/v1/quiz/daily/start", json={"date_str": "2026-10-22"}, headers=student_headers)
    quiz_data = start_resp.json()
    attempt_id = quiz_data["attempt_id"]

    submit_payload = {
        "attempt_id": attempt_id,
        "answers": [{"question_id": quiz_data["questions"][0]["id"], "selected_option": "Option B"}],
        "time_taken_seconds": 120
    }

    # First submission -> succeeds
    first_resp = client.post("/api/v1/quiz/submit", json=submit_payload, headers=student_headers)
    assert first_resp.status_code == 200

    # Second submission with different answers -> must fail with 400 Bad Request
    duplicate_payload = {
        "attempt_id": attempt_id,
        "answers": [{"question_id": quiz_data["questions"][0]["id"], "selected_option": "Option A"}],
        "time_taken_seconds": 200
    }
    second_resp = client.post("/api/v1/quiz/submit", json=duplicate_payload, headers=student_headers)
    assert second_resp.status_code == 400
    assert "already been submitted and scored" in second_resp.json()["detail"]
