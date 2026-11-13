import pytest

def test_register_student(client):
    payload = {
        "email": "new_student@mbahub.edu",
        "password": "SecretPass123!",
        "full_name": "Priya Sharma",
        "role": "student",
        "college": "IIM Ahmedabad",
        "roll_number": "IIMA-2024-101"
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "new_student@mbahub.edu"
    assert data["full_name"] == "Priya Sharma"
    assert data["role"] == "student"
    assert "hashed_password" not in data

def test_register_duplicate_email(client):
    payload = {
        "email": "test_student@mbahub.edu",
        "password": "Password123!",
        "full_name": "Duplicate Student"
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]

def test_login_success(client):
    payload = {
        "email": "test_student@mbahub.edu",
        "password": "StudentPass123!"
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "test_student@mbahub.edu"

def test_login_invalid_password(client):
    payload = {
        "email": "test_student@mbahub.edu",
        "password": "WrongPassword!"
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]

def test_login_nonexistent_user(client):
    payload = {
        "email": "ghost@mbahub.edu",
        "password": "SomePassword123!"
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401

def test_get_current_user_profile(client, student_headers):
    response = client.get("/api/v1/auth/me", headers=student_headers)
    assert response.status_code == 200
    assert response.json()["email"] == "test_student@mbahub.edu"

def test_unauthorized_access_denied(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
