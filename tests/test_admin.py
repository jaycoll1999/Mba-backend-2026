import io
import json
import pytest
from app.models.subject import Subject
from app.models.question import Question

def test_admin_stats_authorized(client, admin_headers):
    response = client.get("/api/v1/admin/stats", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_students" in data
    assert "total_subjects" in data
    assert "total_questions" in data
    assert "approved_questions" in data

def test_admin_stats_unauthorized_student(client, student_headers):
    response = client.get("/api/v1/admin/stats", headers=student_headers)
    assert response.status_code == 403
    assert "Admin privileges required" in response.json()["detail"]

def test_import_questions_json_and_approval_flow(client, admin_headers, db_session):
    subject = db_session.query(Subject).filter(Subject.code == "TEST-OB").first()

    raw_json = json.dumps([
        {
            "subject_code_or_id": subject.code,
            "question_text": "What does Emotional Quotient (EQ) measure in managerial leadership?",
            "difficulty": "medium",
            "options": ["Interpersonal and self-regulatory emotional awareness", "Mathematical calculation speed", "Typing accuracy", "Memory of accounting codes"],
            "correct_answer": "Interpersonal and self-regulatory emotional awareness",
            "explanation": "EQ assesses the ability to recognize, understand, and manage personal and others' emotions.",
            "source_reference": "Daniel Goleman Emotional Intelligence"
        }
    ])
    json_file = io.BytesIO(raw_json.encode("utf-8"))
    files = {"file": ("new_questions.json", json_file, "application/json")}

    # 1. Import questions
    import_resp = client.post("/api/v1/questions/import", files=files, headers=admin_headers)
    assert import_resp.status_code == 200
    res = import_resp.json()
    assert res["imported_count"] == 1
    assert res["duplicate_count"] == 0

    # 2. Verify imported question is UNAPPROVED by default
    imported_q = db_session.query(Question).filter(
        Question.question_text == "What does Emotional Quotient (EQ) measure in managerial leadership?"
    ).first()
    assert imported_q is not None
    assert imported_q.is_approved is False, "Requirement: Admin approval required before publishing imported questions!"

    # 3. Duplicate prevention: Import the same question again
    json_file_dup = io.BytesIO(raw_json.encode("utf-8"))
    dup_resp = client.post("/api/v1/questions/import", files={"file": ("dup.json", json_file_dup, "application/json")}, headers=admin_headers)
    assert dup_resp.status_code == 200
    dup_res = dup_resp.json()
    assert dup_res["imported_count"] == 0
    assert dup_res["duplicate_count"] == 1

    # 4. Admin approves the question
    approve_resp = client.put(f"/api/v1/questions/{imported_q.id}/approve", headers=admin_headers)
    assert approve_resp.status_code == 200
    assert approve_resp.json()["is_approved"] is True
