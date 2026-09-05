"""Admin tests — verify/reject, suspension, stats, guard rules."""

from tests.conftest import VALID_PROFILE, auth_header, make_verified_tutor


def _admin(client):
    return client.post(
        "/api/auth/register",
        json={
            "email": "adm@test.com",
            "full_name": "Adm",
            "password": "secret123",
            "role": "parent",
        },
    ).json()


def _promote_to_admin(client, email="adm@test.com"):
    from app.database import SessionLocal
    from app.models import User

    db = SessionLocal()
    u = db.query(User).filter(User.email == email).first()
    u.role = "admin"
    db.commit()
    db.close()


def _register_tutor(client, email):
    r = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "full_name": "Tutor Person",
            "password": "secret123",
            "role": "tutor",
        },
    )
    return r.json()


def test_admin_stats(client):
    adm = _admin(client)
    _promote_to_admin(client)
    h = auth_header(adm["access_token"])
    make_verified_tutor(client)
    r = client.get("/api/admin/stats", headers=h)
    assert r.status_code == 200
    s = r.json()
    assert s["total_users"] >= 3  # admins + tutor
    assert s["tutors_verified"] >= 1
    assert "gmv_pkr" in s


def test_admin_verify_and_reject_with_note(client):
    reg = _register_tutor(client, "pending@test.com")
    th = auth_header(reg["access_token"])
    client.put("/api/tutors/mine", json=VALID_PROFILE, headers=th)
    adm = _admin(client)
    _promote_to_admin(client)
    h = auth_header(adm["access_token"])
    pend = client.get("/api/admin/tutors/pending", headers=h).json()
    assert len(pend) == 1
    pid = pend[0]["id"]
    r = client.post(
        f"/api/admin/tutors/{pid}/verify", json={"verify": True, "note": "ID checked"}, headers=h
    )
    assert r.status_code == 200
    assert r.json()["is_verified"] is True
    assert r.json()["is_visible"] is True
    r = client.post(
        f"/api/admin/tutors/{pid}/verify", json={"verify": False, "note": "fake degree"}, headers=h
    )
    assert r.status_code == 200
    assert r.json()["is_verified"] is False
    assert r.json()["admin_note"] == "fake degree"
    assert r.json()["is_visible"] is False


def test_suspend_hides_profile_and_blocks_login(client):
    _tutor_token, tutor_id = make_verified_tutor(client, email="susp@test.com")
    adm = _admin(client)
    _promote_to_admin(client)
    h = auth_header(adm["access_token"])
    users = client.get("/api/admin/users", headers=h).json()
    tutor_user = next(u for u in users if u["email"] == "susp@test.com")
    r = client.post(
        f"/api/admin/users/{tutor_user['id']}/suspend", json={"suspend": True}, headers=h
    )
    assert r.status_code == 200
    assert client.get("/api/tutors").json() == []
    assert client.get(f"/api/tutors/{tutor_id}").status_code == 404
    r = client.post("/api/auth/login", json={"email": "susp@test.com", "password": "secret123"})
    assert r.status_code == 403


def test_cannot_suspend_admin(client):
    adm = _admin(client)
    _promote_to_admin(client)
    h = auth_header(adm["access_token"])
    users = client.get("/api/admin/users", headers=h).json()
    admin_user = next(u for u in users if u["email"] == "adm@test.com")
    r = client.post(
        f"/api/admin/users/{admin_user['id']}/suspend", json={"suspend": True}, headers=h
    )
    assert r.status_code == 400


def test_pending_list_only_has_content(client):
    reg = _register_tutor(client, "emptyprof@test.com")
    adm = _admin(client)
    _promote_to_admin(client)
    h = auth_header(adm["access_token"])
    # empty-headline tutor should NOT appear in pending list
    pend = client.get("/api/admin/tutors/pending", headers=h).json()
    assert all(p["headline"] for p in pend)
    assert reg["access_token"]


def test_pending_list_excludes_verified(client):
    make_verified_tutor(client)
    reg2 = _register_tutor(client, "pend2@test.com")
    th = auth_header(reg2["access_token"])
    client.put("/api/tutors/mine", json=VALID_PROFILE, headers=th)
    adm = _admin(client)
    _promote_to_admin(client)
    h = auth_header(adm["access_token"])
    pend = client.get("/api/admin/tutors/pending", headers=h).json()
    assert len(pend) == 1
    assert all(p["is_verified"] is False for p in pend)
