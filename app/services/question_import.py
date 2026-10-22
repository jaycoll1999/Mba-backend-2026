import json
import csv
import io
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from app.models.question import Question, DifficultyLevel
from app.models.subject import Subject
from app.models.unit import Unit
from app.schemas.question import QuestionImportResult

def _find_subject(db: Session, identifier: Any) -> Subject:
    """Find subject by id or code or name."""
    if isinstance(identifier, int) or (isinstance(identifier, str) and identifier.isdigit()):
        subj = db.query(Subject).filter(Subject.id == int(identifier)).first()
        if subj:
            return subj
    return db.query(Subject).filter(
        (Subject.code == str(identifier)) | (Subject.name.ilike(str(identifier)))
    ).first()

def _find_unit(db: Session, subject_id: int, unit_ref: Any) -> Unit:
    """Find unit under subject by id or unit_number."""
    if unit_ref is None or unit_ref == "":
        return None
    if isinstance(unit_ref, int) or (isinstance(unit_ref, str) and unit_ref.isdigit()):
        val = int(unit_ref)
        # Try unit id
        u = db.query(Unit).filter(Unit.id == val, Unit.subject_id == subject_id).first()
        if u:
            return u
        # Try unit_number
        return db.query(Unit).filter(Unit.unit_number == val, Unit.subject_id == subject_id).first()
    return db.query(Unit).filter(Unit.title.ilike(f"%{unit_ref}%"), Unit.subject_id == subject_id).first()

def process_raw_question_item(
    item: Dict[str, Any],
    db: Session,
    imported_by_id: int
) -> Tuple[bool, str, Question]:
    """
    Validate and convert single question dict to Question model instance.
    Returns: (success: bool, message: str, question: Question)
    """
    subject_ref = item.get("subject_code_or_id") or item.get("subject_id") or item.get("subject_code")
    if not subject_ref:
        return False, "Missing subject identifier ('subject_id' or 'subject_code').", None

    subject = _find_subject(db, subject_ref)
    if not subject:
        return False, f"Subject '{subject_ref}' could not be found.", None

    unit_ref = item.get("unit_number_or_id") or item.get("unit_id") or item.get("unit_number")
    unit = _find_unit(db, subject.id, unit_ref) if unit_ref else None

    q_text = str(item.get("question_text", "")).strip()
    if len(q_text) < 5:
        return False, "Question text must be at least 5 characters.", None

    # Duplicate check: check if question with similar text exists under subject
    existing = (
        db.query(Question)
        .filter(
            Question.subject_id == subject.id,
            Question.question_text.ilike(q_text)
        )
        .first()
    )
    if existing:
        return False, f"Duplicate question already exists: '{q_text[:40]}...'", None

    difficulty = str(item.get("difficulty", "medium")).lower().strip()
    if difficulty not in ["easy", "medium", "hard"]:
        difficulty = "medium"

    options = item.get("options", [])
    if isinstance(options, str):
        try:
            options = json.loads(options)
        except Exception:
            # Handle comma-separated or pipe-separated in CSV
            if "|" in options:
                options = [o.strip() for o in options.split("|")]
            else:
                options = [o.strip() for o in options.split(",")]

    if not isinstance(options, list) or len(options) != 4:
        return False, f"Question must have exactly 4 options, found {len(options) if isinstance(options, list) else 0}.", None

    correct_answer = str(item.get("correct_answer", "")).strip()
    if not correct_answer:
        return False, "Missing correct_answer.", None

    letter_map = {"A": 0, "B": 1, "C": 2, "D": 3}
    if correct_answer.upper() in letter_map:
        correct_answer = options[letter_map[correct_answer.upper()]]
    elif correct_answer not in options:
        return False, f"Correct answer '{correct_answer}' is not among the 4 options.", None

    explanation = item.get("explanation", "")
    source_reference = item.get("source_reference", "Imported Faculty Question Bank")

    question = Question(
        subject_id=subject.id,
        unit_id=unit.id if unit else None,
        question_text=q_text,
        difficulty=difficulty,
        options_json=json.dumps(options),
        correct_answer=correct_answer,
        explanation=explanation,
        source_reference=source_reference,
        is_active=True,
        is_approved=False,  # ADMIN APPROVAL REQUIRED BEFORE PUBLISHING
        created_by_id=imported_by_id
    )

    return True, "Valid", question

def import_questions_from_json(
    raw_content: str,
    db: Session,
    imported_by_id: int
) -> QuestionImportResult:
    """Import and validate questions from JSON string."""
    try:
        data = json.loads(raw_content)
    except Exception as e:
        return QuestionImportResult(
            total_parsed=0,
            imported_count=0,
            duplicate_count=0,
            error_count=1,
            errors=[f"Invalid JSON format: {str(e)}"]
        )

    if not isinstance(data, list):
        data = [data]

    total_parsed = len(data)
    imported = []
    duplicate_count = 0
    errors = []

    for idx, item in enumerate(data, start=1):
        success, msg, question = process_raw_question_item(item, db, imported_by_id)
        if success:
            imported.append(question)
            db.add(question)
        else:
            if "Duplicate" in msg:
                duplicate_count += 1
            errors.append(f"Row {idx}: {msg}")

    db.commit()

    return QuestionImportResult(
        total_parsed=total_parsed,
        imported_count=len(imported),
        duplicate_count=duplicate_count,
        error_count=len(errors) - duplicate_count,
        errors=errors[:20]  # Cap top 20 error details
    )

def import_questions_from_csv(
    raw_content: str,
    db: Session,
    imported_by_id: int
) -> QuestionImportResult:
    """Import and validate questions from CSV string."""
    try:
        reader = csv.DictReader(io.StringIO(raw_content))
        rows = list(reader)
    except Exception as e:
        return QuestionImportResult(
            total_parsed=0,
            imported_count=0,
            duplicate_count=0,
            error_count=1,
            errors=[f"Invalid CSV format: {str(e)}"]
        )

    total_parsed = len(rows)
    imported = []
    duplicate_count = 0
    errors = []

    for idx, row in enumerate(rows, start=1):
        # Support option_1..option_4 or options separated by |
        options = []
        if "option_a" in row and "option_b" in row and "option_c" in row and "option_d" in row:
            options = [row["option_a"], row["option_b"], row["option_c"], row["option_d"]]
        elif "option_1" in row and "option_2" in row and "option_3" in row and "option_4" in row:
            options = [row["option_1"], row["option_2"], row["option_3"], row["option_4"]]
        elif "options" in row:
            options = row["options"]

        item = {
            "subject_code_or_id": row.get("subject_code") or row.get("subject_id") or row.get("subject"),
            "unit_number_or_id": row.get("unit_number") or row.get("unit_id"),
            "question_text": row.get("question_text") or row.get("question"),
            "difficulty": row.get("difficulty", "medium"),
            "options": options,
            "correct_answer": row.get("correct_answer") or row.get("answer"),
            "explanation": row.get("explanation"),
            "source_reference": row.get("source_reference") or row.get("source")
        }

        success, msg, question = process_raw_question_item(item, db, imported_by_id)
        if success:
            imported.append(question)
            db.add(question)
        else:
            if "Duplicate" in msg:
                duplicate_count += 1
            errors.append(f"Row {idx}: {msg}")

    db.commit()

    return QuestionImportResult(
        total_parsed=total_parsed,
        imported_count=len(imported),
        duplicate_count=duplicate_count,
        error_count=len(errors) - duplicate_count,
        errors=errors[:20]
    )
