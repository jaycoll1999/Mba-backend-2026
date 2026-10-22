import os
import sqlite3
from datetime import datetime

DB_PATH = r"d:\MBA_Project_2026\backend\data\mba_study_hub.db"
BASE_DIR = r"d:\MBA_Project_2026\backend"
UPLOADS_DIR = r"d:\MBA_Project_2026\backend\data\uploads"

def get_file_size(rel_path):
    full_path = os.path.join(BASE_DIR, rel_path)
    if os.path.exists(full_path):
        return os.path.getsize(full_path)
    return 0

def seed():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()

    # Define Books
    books = [
        {
            "title": "Basics of Marketing (BOM 504) — Nirali Prakashan Comprehensive Textbook",
            "resource_type": "book",
            "subject_id": 8,
            "author": "Dr. P. C. Pardeshi & Dr. S. K. Mahajan",
            "publisher": "Nirali Prakashan",
            "edition": "2024 NEP Pattern Edition",
            "file_name": "bom_nirali_prakashan.pdf",
            "file_path": "data/uploads/books/bom_nirali_prakashan.pdf",
            "source_reference": "Nirali Academic Reference Library",
            "is_verified_solution": 0,
            "verification_disclaimer": "Standard university recommended reference textbook."
        },
        {
            "title": "Basics of Marketing (BM 504) — Thakur Publication Textbook",
            "resource_type": "book",
            "subject_id": 8,
            "author": "Prof. Amit Kumar & Dr. Reena Sharma",
            "publisher": "Thakur Publication",
            "edition": "1st Edition / 2024 NEP Pattern",
            "file_name": "bm_thakur_publication.pdf",
            "file_path": "data/uploads/books/bm_thakur_publication.pdf",
            "source_reference": "Thakur Publication MBA Series",
            "is_verified_solution": 0,
            "verification_disclaimer": "Standard university recommended reference textbook."
        },
        {
            "title": "Economic Analysis for Business Decisions (EABD 503) — Thakur Publication",
            "resource_type": "book",
            "subject_id": 5,
            "author": "Dr. V. K. Puri & Dr. S. Mishra",
            "publisher": "Thakur Publication",
            "edition": "2024 Revised Edition",
            "file_name": "eabd_thakur_publication.pdf",
            "file_path": "data/uploads/books/eabd_thakur_publication.pdf",
            "source_reference": "Thakur Publication MBA Series",
            "is_verified_solution": 0,
            "verification_disclaimer": "Standard university recommended reference textbook."
        },
        {
            "title": "Managerial Accounting (MA 501) — Thakur Publication MBA Sem 1",
            "resource_type": "book",
            "subject_id": 2,
            "author": "Dr. Maheshwari & Dr. Mittal",
            "publisher": "Thakur Publication",
            "edition": "2024 NEP Revised Edition",
            "file_name": "ma_thakur_publication.pdf",
            "file_path": "data/uploads/books/ma_thakur_publication.pdf",
            "source_reference": "Thakur Publication MBA Series",
            "is_verified_solution": 0,
            "verification_disclaimer": "Standard university recommended reference textbook."
        },
        {
            "title": "Management Fundamentals (MF 507) — Thakur Publication",
            "resource_type": "book",
            "subject_id": 3,
            "author": "Dr. L. M. Prasad & Prof. K. Rao",
            "publisher": "Thakur Publication",
            "edition": "2024 Edition",
            "file_name": "mf_thakur_publication.pdf",
            "file_path": "data/uploads/books/mf_thakur_publication.pdf",
            "source_reference": "Thakur Publication MBA Series",
            "is_verified_solution": 0,
            "verification_disclaimer": "Standard university recommended reference textbook."
        },
        {
            "title": "Organizational Behaviour (OB 502) — Thakur Publication",
            "resource_type": "book",
            "subject_id": 1,
            "author": "Dr. S. S. Khanka & Prof. Neha Gupta",
            "publisher": "Thakur Publication",
            "edition": "2024 NEP Pattern Edition",
            "file_name": "ob_thakur_publication.pdf",
            "file_path": "data/uploads/books/ob_thakur_publication.pdf",
            "source_reference": "Thakur Publication MBA Series",
            "is_verified_solution": 0,
            "verification_disclaimer": "Standard university recommended reference textbook."
        }
    ]

    # Define University Question Papers
    question_papers = [
        # Basics of Marketing
        {
            "title": "MBA Sem 1 Basics of Marketing End-Term Question Paper — November 2024",
            "resource_type": "question_paper",
            "subject_id": 8,
            "exam_session": "Winter",
            "exam_month": "November",
            "exam_year": 2024,
            "exam_pattern": "2024 NEP Pattern",
            "file_name": "postgraduate-pg_mba_semester-1_2024_november_basics-of-marketing-2024-pattern.pdf",
            "file_path": "data/uploads/question_papers/postgraduate-pg_mba_semester-1_2024_november_basics-of-marketing-2024-pattern.pdf",
            "source_reference": "University Controller of Examinations",
        },
        {
            "title": "MBA Sem 1 Basics of Marketing End-Term Question Paper — May 2025",
            "resource_type": "question_paper",
            "subject_id": 8,
            "exam_session": "Summer",
            "exam_month": "May",
            "exam_year": 2025,
            "exam_pattern": "2024 NEP Pattern",
            "file_name": "postgraduate-pg_mba_semester-1_2025_may_basics-of-marketing-2024-pattern.pdf",
            "file_path": "data/uploads/question_papers/postgraduate-pg_mba_semester-1_2025_may_basics-of-marketing-2024-pattern.pdf",
            "source_reference": "University Controller of Examinations",
        },
        # Business Analytics
        {
            "title": "MBA Sem 1 Business Analytics End-Term Question Paper — May 2025",
            "resource_type": "question_paper",
            "subject_id": 7,
            "exam_session": "Summer",
            "exam_month": "May",
            "exam_year": 2025,
            "exam_pattern": "2024 NEP Pattern",
            "file_name": "postgraduate-pg_mba_semester-1_2025_may_business-analytics-2024-pattern.pdf",
            "file_path": "data/uploads/question_papers/postgraduate-pg_mba_semester-1_2025_may_business-analytics-2024-pattern.pdf",
            "source_reference": "University Controller of Examinations",
        },
        # Decision Science
        {
            "title": "MBA Sem 1 Decision Science End-Term Question Paper — November 2024",
            "resource_type": "question_paper",
            "subject_id": 6,
            "exam_session": "Winter",
            "exam_month": "November",
            "exam_year": 2024,
            "exam_pattern": "2024 NEP Pattern",
            "file_name": "postgraduate-pg_mba_semester-1_2024_november_decision-science-2024-pattern.pdf",
            "file_path": "data/uploads/question_papers/postgraduate-pg_mba_semester-1_2024_november_decision-science-2024-pattern.pdf",
            "source_reference": "University Controller of Examinations",
        },
        {
            "title": "MBA Sem 1 Decision Science End-Term Question Paper — May 2025",
            "resource_type": "question_paper",
            "subject_id": 6,
            "exam_session": "Summer",
            "exam_month": "May",
            "exam_year": 2025,
            "exam_pattern": "2024 NEP Pattern",
            "file_name": "postgraduate-pg_mba_semester-1_2025_may_decision-science-2024-pattern.pdf",
            "file_path": "data/uploads/question_papers/postgraduate-pg_mba_semester-1_2025_may_decision-science-2024-pattern.pdf",
            "source_reference": "University Controller of Examinations",
        },
        # Economic Analysis
        {
            "title": "MBA Sem 1 Economic Analysis End-Term Question Paper — November 2024",
            "resource_type": "question_paper",
            "subject_id": 5,
            "exam_session": "Winter",
            "exam_month": "November",
            "exam_year": 2024,
            "exam_pattern": "2024 NEP Pattern",
            "file_name": "postgraduate-pg_mba_semester-1_2024_november_economic-analysis-for-business-decision-2024-pattern.pdf",
            "file_path": "data/uploads/question_papers/postgraduate-pg_mba_semester-1_2024_november_economic-analysis-for-business-decision-2024-pattern.pdf",
            "source_reference": "University Controller of Examinations",
        },
        {
            "title": "MBA Sem 1 Economic Analysis End-Term Question Paper — May 2025",
            "resource_type": "question_paper",
            "subject_id": 5,
            "exam_session": "Summer",
            "exam_month": "May",
            "exam_year": 2025,
            "exam_pattern": "2024 NEP Pattern",
            "file_name": "postgraduate-pg_mba_semester-1_2025_may_economic-analysis-for-business-decision-2024-pattern.pdf",
            "file_path": "data/uploads/question_papers/postgraduate-pg_mba_semester-1_2025_may_economic-analysis-for-business-decision-2024-pattern.pdf",
            "source_reference": "University Controller of Examinations",
        },
        # Indian Knowledge Systems
        {
            "title": "MBA Sem 1 Indian Knowledge Systems Question Paper — May 2024",
            "resource_type": "question_paper",
            "subject_id": 4,
            "exam_session": "Summer",
            "exam_month": "May",
            "exam_year": 2024,
            "exam_pattern": "2024 NEP Pattern",
            "file_name": "postgraduate-pg_mba_semester-1_2024_may_indian-knowledge-systems-2024-pattern.pdf",
            "file_path": "data/uploads/question_papers/postgraduate-pg_mba_semester-1_2024_may_indian-knowledge-systems-2024-pattern.pdf",
            "source_reference": "University Controller of Examinations",
        },
        {
            "title": "MBA Sem 1 Indian Knowledge Systems Question Paper — May 2025",
            "resource_type": "question_paper",
            "subject_id": 4,
            "exam_session": "Summer",
            "exam_month": "May",
            "exam_year": 2025,
            "exam_pattern": "2024 NEP Pattern",
            "file_name": "postgraduate-pg_mba_semester-1_2025_may_indian-knowledge-systems-2024-pattern.pdf",
            "file_path": "data/uploads/question_papers/postgraduate-pg_mba_semester-1_2025_may_indian-knowledge-systems-2024-pattern.pdf",
            "source_reference": "University Controller of Examinations",
        },
        # Management Fundamentals
        {
            "title": "MBA Sem 1 Management Fundamentals Question Paper — November 2024",
            "resource_type": "question_paper",
            "subject_id": 3,
            "exam_session": "Winter",
            "exam_month": "November",
            "exam_year": 2024,
            "exam_pattern": "2024 NEP Pattern",
            "file_name": "postgraduate-pg_mba_semester-1_2024_november_management-fundamentals-2024-pattern.pdf",
            "file_path": "data/uploads/question_papers/postgraduate-pg_mba_semester-1_2024_november_management-fundamentals-2024-pattern.pdf",
            "source_reference": "University Controller of Examinations",
        },
        {
            "title": "MBA Sem 1 Management Fundamentals Question Paper — May 2025",
            "resource_type": "question_paper",
            "subject_id": 3,
            "exam_session": "Summer",
            "exam_month": "May",
            "exam_year": 2025,
            "exam_pattern": "2024 NEP Pattern",
            "file_name": "postgraduate-pg_mba_semester-1_2025_may_management-fundamentals-2024-pattern.pdf",
            "file_path": "data/uploads/question_papers/postgraduate-pg_mba_semester-1_2025_may_management-fundamentals-2024-pattern.pdf",
            "source_reference": "University Controller of Examinations",
        },
        # Managerial Accounting
        {
            "title": "MBA Sem 1 Managerial Accounting Question Paper — November 2024",
            "resource_type": "question_paper",
            "subject_id": 2,
            "exam_session": "Winter",
            "exam_month": "November",
            "exam_year": 2024,
            "exam_pattern": "2024 NEP Pattern",
            "file_name": "postgraduate-pg_mba_semester-1_2024_november_managerial-accounting-2024-pattern.pdf",
            "file_path": "data/uploads/question_papers/postgraduate-pg_mba_semester-1_2024_november_managerial-accounting-2024-pattern.pdf",
            "source_reference": "University Controller of Examinations",
        },
        {
            "title": "MBA Sem 1 Managerial Accounting Question Paper — May 2025",
            "resource_type": "question_paper",
            "subject_id": 2,
            "exam_session": "Summer",
            "exam_month": "May",
            "exam_year": 2025,
            "exam_pattern": "2024 NEP Pattern",
            "file_name": "postgraduate-pg_mba_semester-1_2025_may_managerial-accounting-2024-pattern.pdf",
            "file_path": "data/uploads/question_papers/postgraduate-pg_mba_semester-1_2025_may_managerial-accounting-2024-pattern.pdf",
            "source_reference": "University Controller of Examinations",
        },
        # Organizational Behaviour
        {
            "title": "MBA Sem 1 Organizational Behaviour Question Paper — November 2024",
            "resource_type": "question_paper",
            "subject_id": 1,
            "exam_session": "Winter",
            "exam_month": "November",
            "exam_year": 2024,
            "exam_pattern": "2024 NEP Pattern",
            "file_name": "postgraduate-pg_mba_semester-1_2024_november_organizational-behaviour-2024-pattern.pdf",
            "file_path": "data/uploads/question_papers/postgraduate-pg_mba_semester-1_2024_november_organizational-behaviour-2024-pattern.pdf",
            "source_reference": "University Controller of Examinations",
        },
        {
            "title": "MBA Sem 1 Organizational Behaviour Question Paper — May 2025",
            "resource_type": "question_paper",
            "subject_id": 1,
            "exam_session": "Summer",
            "exam_month": "May",
            "exam_year": 2025,
            "exam_pattern": "2024 NEP Pattern",
            "file_name": "postgraduate-pg_mba_semester-1_2025_may_organizational-behaviour-2024-pattern.pdf",
            "file_path": "data/uploads/question_papers/postgraduate-pg_mba_semester-1_2025_may_organizational-behaviour-2024-pattern.pdf",
            "source_reference": "University Controller of Examinations",
        },
    ]

    # Define Solved Papers & Question Banks
    solved_papers = [
        {
            "title": "Organizational Behaviour — Model Solutions & Solved Papers (2024-2025)",
            "resource_type": "solved_paper",
            "subject_id": 1,
            "exam_year": 2025,
            "exam_pattern": "2024 NEP Pattern",
            "file_name": "ob_solved_2024_2025.pdf",
            "file_path": "data/uploads/solved_papers/ob_solved_2024_2025.pdf",
            "source_reference": "MBA Faculty Subject Expert Panel",
            "is_verified_solution": 1,
            "verification_disclaimer": "Verified model answers compiled with step marking guidelines by MBA Faculty."
        },
        {
            "title": "Managerial Accounting — Solved Numerical & Theory Solutions (2024-2025)",
            "resource_type": "solved_paper",
            "subject_id": 2,
            "exam_year": 2025,
            "exam_pattern": "2024 NEP Pattern",
            "file_name": "ma_solved_2024_2025.pdf",
            "file_path": "data/uploads/solved_papers/ma_solved_2024_2025.pdf",
            "source_reference": "MBA Faculty Subject Expert Panel",
            "is_verified_solution": 1,
            "verification_disclaimer": "Verified financial model answers compiled with step marking guidelines by MBA Faculty."
        },
        {
            "title": "Management Fundamentals — Model Solutions (2024-2025)",
            "resource_type": "solved_paper",
            "subject_id": 3,
            "exam_year": 2025,
            "exam_pattern": "2024 NEP Pattern",
            "file_name": "mf_solved_2024_2025.pdf",
            "file_path": "data/uploads/solved_papers/mf_solved_2024_2025.pdf",
            "source_reference": "MBA Faculty Subject Expert Panel",
            "is_verified_solution": 1,
            "verification_disclaimer": "Verified model answers compiled with step marking guidelines by MBA Faculty."
        },
        {
            "title": "Indian Knowledge Systems — Solved Question Bank & Model Answers (2024-2025)",
            "resource_type": "solved_paper",
            "subject_id": 4,
            "exam_year": 2025,
            "exam_pattern": "2024 NEP Pattern",
            "file_name": "iks_solved_2024_2025.pdf",
            "file_path": "data/uploads/solved_papers/iks_solved_2024_2025.pdf",
            "source_reference": "MBA Faculty Subject Expert Panel",
            "is_verified_solution": 1,
            "verification_disclaimer": "Verified model answers compiled with step marking guidelines by MBA Faculty."
        },
        {
            "title": "Decision Science — Solved Numerical & Analytical Papers (2024-2025)",
            "resource_type": "solved_paper",
            "subject_id": 6,
            "exam_year": 2025,
            "exam_pattern": "2024 NEP Pattern",
            "file_name": "ds_solved_2024_2025.pdf",
            "file_path": "data/uploads/solved_papers/ds_solved_2024_2025.pdf",
            "source_reference": "MBA Faculty Subject Expert Panel",
            "is_verified_solution": 1,
            "verification_disclaimer": "Verified step-by-step mathematical solutions compiled by Quantitative Methods Faculty."
        },
        {
            "title": "Basics of Marketing — Comprehensive Solved Question Bank",
            "resource_type": "solved_paper",
            "subject_id": 8,
            "exam_year": 2025,
            "exam_pattern": "2024 NEP Pattern",
            "file_name": "bom_all_questions_solved.pdf",
            "file_path": "data/uploads/solved_papers/bom_all_questions_solved.pdf",
            "source_reference": "MBA Faculty Subject Expert Panel",
            "is_verified_solution": 1,
            "verification_disclaimer": "Comprehensive subject revision and model answers for MBA Semester 1."
        },
        {
            "title": "Business Analytics — Comprehensive Solved Question Bank",
            "resource_type": "solved_paper",
            "subject_id": 7,
            "exam_year": 2025,
            "exam_pattern": "2024 NEP Pattern",
            "file_name": "ba_all_questions_solved.pdf",
            "file_path": "data/uploads/solved_papers/ba_all_questions_solved.pdf",
            "source_reference": "MBA Faculty Subject Expert Panel",
            "is_verified_solution": 1,
            "verification_disclaimer": "Comprehensive subject revision and model answers for MBA Semester 1."
        },
        {
            "title": "Decision Science — Comprehensive Solved Question Bank",
            "resource_type": "solved_paper",
            "subject_id": 6,
            "exam_year": 2025,
            "exam_pattern": "2024 NEP Pattern",
            "file_name": "ds_all_questions_solved.pdf",
            "file_path": "data/uploads/solved_papers/ds_all_questions_solved.pdf",
            "source_reference": "MBA Faculty Subject Expert Panel",
            "is_verified_solution": 1,
            "verification_disclaimer": "Comprehensive subject revision and model answers for MBA Semester 1."
        },
        {
            "title": "Economic Analysis for Business Decisions — Solved Question Bank",
            "resource_type": "solved_paper",
            "subject_id": 5,
            "exam_year": 2025,
            "exam_pattern": "2024 NEP Pattern",
            "file_name": "eabd_all_questions_solved.pdf",
            "file_path": "data/uploads/solved_papers/eabd_all_questions_solved.pdf",
            "source_reference": "MBA Faculty Subject Expert Panel",
            "is_verified_solution": 1,
            "verification_disclaimer": "Comprehensive subject revision and model answers for MBA Semester 1."
        },
        {
            "title": "Indian Knowledge Systems — Comprehensive Solved Question Bank",
            "resource_type": "solved_paper",
            "subject_id": 4,
            "exam_year": 2025,
            "exam_pattern": "2024 NEP Pattern",
            "file_name": "iks_all_questions_solved.pdf",
            "file_path": "data/uploads/solved_papers/iks_all_questions_solved.pdf",
            "source_reference": "MBA Faculty Subject Expert Panel",
            "is_verified_solution": 1,
            "verification_disclaimer": "Comprehensive subject revision and model answers for MBA Semester 1."
        },
    ]

    all_items = books + question_papers + solved_papers
    inserted = 0
    updated = 0

    for item in all_items:
        file_name = item["file_name"]
        file_size = get_file_size(item["file_path"])

        cur.execute("SELECT id FROM resources WHERE file_name = ?", (file_name,))
        existing = cur.fetchone()

        if existing:
            cur.execute("""
                UPDATE resources
                SET title = ?, resource_type = ?, subject_id = ?, author = ?, publisher = ?,
                    edition = ?, exam_session = ?, exam_month = ?, exam_year = ?, exam_pattern = ?,
                    file_path = ?, file_size_bytes = ?, mime_type = 'application/pdf',
                    source_reference = ?, is_verified_solution = ?, verification_disclaimer = ?,
                    updated_at = ?
                WHERE id = ?
            """, (
                item["title"], item["resource_type"], item["subject_id"],
                item.get("author"), item.get("publisher"), item.get("edition"),
                item.get("exam_session"), item.get("exam_month"), item.get("exam_year"), item.get("exam_pattern"),
                item["file_path"], file_size, item.get("source_reference"),
                item.get("is_verified_solution", 0), item.get("verification_disclaimer"),
                now, existing[0]
            ))
            updated += 1
        else:
            cur.execute("""
                INSERT INTO resources (
                    title, resource_type, subject_id, author, publisher, edition,
                    exam_session, exam_month, exam_year, exam_pattern,
                    file_name, file_path, file_size_bytes, mime_type,
                    source_reference, is_verified_solution, verification_disclaimer,
                    uploaded_by_id, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'application/pdf', ?, ?, ?, 1, ?, ?)
            """, (
                item["title"], item["resource_type"], item["subject_id"],
                item.get("author"), item.get("publisher"), item.get("edition"),
                item.get("exam_session"), item.get("exam_month"), item.get("exam_year"), item.get("exam_pattern"),
                file_name, item["file_path"], file_size,
                item.get("source_reference"), item.get("is_verified_solution", 0),
                item.get("verification_disclaimer"), now, now
            ))
            inserted += 1

    conn.commit()
    print(f"Done! Inserted: {inserted}, Updated: {updated}, Total in DB: {inserted + updated}")
    
    cur.execute("SELECT resource_type, count(*) FROM resources GROUP BY resource_type")
    print("Resources summary in DB:")
    for row in cur.fetchall():
        print(f"  {row[0]}: {row[1]}")

    conn.close()

if __name__ == "__main__":
    seed()
