import io
import pytest
from app.models.subject import Subject

def test_file_upload_validation_non_pdf(client, admin_headers, db_session):
    subject = db_session.query(Subject).filter(Subject.code == "TEST-OB").first()
    
    # Try uploading a text file
    fake_txt = io.BytesIO(b"This is a plain text file, not a PDF.")
    files = {"file": ("malicious_doc.txt", fake_txt, "text/plain")}
    data = {
        "title": "Invalid Document",
        "resource_type": "book",
        "subject_id": subject.id
    }

    response = client.post("/api/v1/resources/upload", data=data, files=files, headers=admin_headers)
    assert response.status_code == 400
    assert "Invalid file extension" in response.json()["detail"]

def test_file_upload_valid_pdf_admin(client, admin_headers, db_session):
    subject = db_session.query(Subject).filter(Subject.code == "TEST-OB").first()

    # Valid minimal PDF structure
    pdf_bytes = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\nxref\n0 2\n0000000000 65535 f\n0000000010 00000 n\ntrailer\n<< /Root 1 0 R >>\n%%EOF"
    pdf_file = io.BytesIO(pdf_bytes)
    files = {"file": ("reference_handbook.pdf", pdf_file, "application/pdf")}
    data = {
        "title": "Test Managerial Handbook",
        "resource_type": "book",
        "subject_id": subject.id,
        "author": "Test Author",
        "publisher": "Academic Press",
        "edition": "2026 Edition"
    }

    response = client.post("/api/v1/resources/upload", data=data, files=files, headers=admin_headers)
    assert response.status_code == 201
    res_data = response.json()
    assert res_data["title"] == "Test Managerial Handbook"
    assert res_data["resource_type"] == "book"
    assert res_data["mime_type"] == "application/pdf"

def test_student_upload_forbidden(client, student_headers, db_session):
    subject = db_session.query(Subject).filter(Subject.code == "TEST-OB").first()
    pdf_file = io.BytesIO(b"%PDF-1.4 test")
    files = {"file": ("student_upload.pdf", pdf_file, "application/pdf")}
    data = {
        "title": "Unauthorized Upload",
        "resource_type": "book",
        "subject_id": subject.id
    }

    # Student cannot upload
    response = client.post("/api/v1/resources/upload", data=data, files=files, headers=student_headers)
    assert response.status_code == 403

def test_solved_papers_separation_and_disclaimer(client, admin_headers, student_headers, db_session):
    subject = db_session.query(Subject).filter(Subject.code == "TEST-OB").first()

    # Upload original question paper
    qp_bytes = io.BytesIO(b"%PDF-1.4 Question Paper")
    client.post(
        "/api/v1/resources/upload",
        data={"title": "Official Exam Paper", "resource_type": "question_paper", "subject_id": subject.id, "exam_year": 2024},
        files={"file": ("qp_2024.pdf", qp_bytes, "application/pdf")},
        headers=admin_headers
    )

    # Upload solved paper
    solved_bytes = io.BytesIO(b"%PDF-1.4 Model Solved Answer")
    client.post(
        "/api/v1/resources/upload",
        data={
            "title": "Model Solved Paper",
            "resource_type": "solved_paper",
            "subject_id": subject.id,
            "exam_year": 2024,
            "is_verified_solution": True
        },
        files={"file": ("solved_2024.pdf", solved_bytes, "application/pdf")},
        headers=admin_headers
    )

    # Fetch papers list -> must contain original question paper
    papers_resp = client.get("/api/v1/resources/papers", headers=student_headers)
    assert papers_resp.status_code == 200
    papers = papers_resp.json()
    assert any(p["title"] == "Official Exam Paper" for p in papers)
    assert not any(p["title"] == "Model Solved Paper" for p in papers)

    # Fetch solved papers list -> must contain solved paper with disclaimer
    solved_resp = client.get("/api/v1/resources/solved-papers", headers=student_headers)
    assert solved_resp.status_code == 200
    solved_list = solved_resp.json()
    assert any(s["title"] == "Model Solved Paper" for s in solved_list)
    assert not any(s["title"] == "Official Exam Paper" for s in solved_list)

    solved_item = next(s for s in solved_list if s["title"] == "Model Solved Paper")
    assert solved_item["is_verified_solution"] is True
    assert solved_item["verification_disclaimer"] is not None
