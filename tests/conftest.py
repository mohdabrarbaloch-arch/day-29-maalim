"""Shared pytest fixtures — temp DB, TestClient, helper factories."""

import os
import sys
from pathlib import Path

# Ensure app is importable and point DB at a temp file BEFORE importing app modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ["DATABASE_URL"] = "sqlite:///./test_maalim.db"
os.environ["SECRET_KEY"] = "test-secret-key-not-for-prod"
# TestClient shares one remote address across the whole session, so raise
# auth rate limits far above what the suite consumes (the rate-limiting
# mechanism itself is asserted in test_auth via a dedicated mini-app).
os.environ["RATE_LIMIT_REGISTER"] = "1000/minute"
os.environ["RATE_LIMIT_LOGIN"] = "1000/minute"

import pytest
from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app

VALID_PROFILE = {
    "headline": "O-Level Mathematics tutor with 5 years experience",
    "bio": "NED graduate. Patient and result-focused.",
    "qualification": "B.E. Electrical",
    "institution": "NED University",
    "experience_years": 5,
    "subjects": ["Mathematics", "Physics"],
    "classes": [9, 10, 11, 12],
    "areas": ["Gulshan", "Gulistan-e-Johar"],
    "fee_per_hour": 1500,
    "is_visible": True,
}


@pytest.fixture(autouse=True)
def clean_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


def register(client, email, password="secret123", role="parent", name="Test User"):
    r = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "full_name": name,
            "phone": "+923000000000",
            "password": password,
            "role": role,
        },
    )
    assert r.status_code == 201, r.text
    return r.json()


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def make_verified_tutor(client, email="tutor@test.com", name="Tutor Sir"):
    """Register a tutor, fill profile, admin verifies -> returns (token, profile_id)."""
    reg = register(client, email, role="tutor", name=name)
    token = reg["access_token"]
    r = client.put("/api/tutors/mine", json=VALID_PROFILE, headers=auth_header(token))
    assert r.status_code == 200, r.text
    # our profile id (owner can always read /mine)
    pid = client.get("/api/tutors/mine", headers=auth_header(token)).json()["id"]

    # create + promote a dedicated admin for this test
    admin_email = "admin-" + email
    adm = register(client, admin_email, role="parent", name="Platform Admin")
    from app.database import SessionLocal
    from app.models import User

    db = SessionLocal()
    user = db.query(User).filter(User.email == admin_email).first()
    user.role = "admin"
    db.commit()
    db.close()

    admin_token = adm["access_token"]
    # verify every pending profile (harmless: each test starts with a clean DB)
    for p in client.get("/api/admin/tutors/pending", headers=auth_header(admin_token)).json():
        r = client.post(
            f"/api/admin/tutors/{p['id']}/verify",
            json={"verify": True, "note": "Docs OK"},
            headers=auth_header(admin_token),
        )
        assert r.status_code == 200, r.text
    return token, pid
