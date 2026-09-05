"""Tutor listing/profile tests — verification gating, filters, search, sort."""

from tests.conftest import VALID_PROFILE, auth_header, make_verified_tutor


def _register_only(client, email, role="tutor"):
    r = client.post(
        "/api/auth/register",
        json={"email": email, "full_name": "Some Tutor", "password": "secret123", "role": role},
    )
    return r.json()


def _admin_token(client):
    from app.database import SessionLocal
    from app.models import User

    db = SessionLocal()
    adm = db.query(User).filter(User.role == "admin").first()
    db.close()
    return client.post(
        "/api/auth/login", json={"email": adm.email, "password": "secret123"}
    ).json()["access_token"]


def _verify_all_pending(client):
    h = auth_header(_admin_token(client))
    for p in client.get("/api/admin/tutors/pending", headers=h).json():
        client.post(
            f"/api/admin/tutors/{p['id']}/verify",
            json={"verify": True, "note": "ok"},
            headers=h,
        )


def test_unverified_tutor_not_listed(client):
    reg = _register_only(client, "unver@test.com")
    h = auth_header(reg["access_token"])
    client.put("/api/tutors/mine", json=VALID_PROFILE, headers=h)
    assert client.get("/api/tutors").json() == []
    from app.database import SessionLocal
    from app.models import TutorProfile

    db = SessionLocal()
    pid = db.query(TutorProfile).first().id
    db.close()
    assert client.get(f"/api/tutors/{pid}").status_code == 404


def test_verified_tutor_appears_after_admin_verify(client):
    _token, pid = make_verified_tutor(client)
    lst = client.get("/api/tutors").json()
    assert len(lst) == 1
    assert lst[0]["tutor_id"] == pid
    assert lst[0]["name"] == "Tutor Sir"
    assert lst[0]["fee_per_hour"] == 1500


def test_my_profile_and_edit_resets_verification(client):
    token, _ = make_verified_tutor(client)
    h = auth_header(token)
    mine = client.get("/api/tutors/mine", headers=h)
    assert mine.status_code == 200
    assert mine.json()["is_verified"] is True
    p = dict(VALID_PROFILE)
    p["fee_per_hour"] = 2000
    r = client.put("/api/tutors/mine", json=p, headers=h)
    assert r.status_code == 200
    assert r.json()["is_verified"] is False
    assert r.json()["fee_per_hour"] == 2000
    assert client.get("/api/tutors").json() == []


def test_filter_by_subject(client):
    make_verified_tutor(client)
    assert len(client.get("/api/tutors?subject=Physics").json()) == 1
    assert client.get("/api/tutors?subject=Chemistry").json() == []


def test_filter_by_area_and_class(client):
    make_verified_tutor(client)
    assert len(client.get("/api/tutors?area=Gulshan").json()) == 1
    assert client.get("/api/tutors?area=DHA").json() == []
    assert len(client.get("/api/tutors?student_class=10").json()) == 1
    assert client.get("/api/tutors?student_class=5").json() == []


def test_filter_by_fee_range(client):
    make_verified_tutor(client)
    assert len(client.get("/api/tutors?min_fee=1000&max_fee=2000").json()) == 1
    assert client.get("/api/tutors?min_fee=3000").json() == []


def test_search_query(client):
    make_verified_tutor(client, email="q@test.com", name="Bilal Ahmed")
    assert len(client.get("/api/tutors?q=bilal").json()) == 1
    assert client.get("/api/tutors?q=zzznothing").json() == []


def test_sort_fee_low_high(client):
    make_verified_tutor(client)
    token2, _ = make_verified_tutor(client, email="t2@test.com", name="Second Tutor")
    p = dict(VALID_PROFILE)
    p["fee_per_hour"] = 800
    client.put("/api/tutors/mine", json=p, headers=auth_header(token2))
    _verify_all_pending(client)
    low = client.get("/api/tutors?sort=fee_low").json()
    high = client.get("/api/tutors?sort=fee_high").json()
    assert low[0]["fee_per_hour"] == 800
    assert high[0]["fee_per_hour"] == 1500


def test_public_detail_hides_rejected(client):
    _, pid = make_verified_tutor(client)
    h = auth_header(_admin_token(client))
    client.post(
        f"/api/admin/tutors/{pid}/verify",
        json={"verify": False, "note": "bad docs"},
        headers=h,
    )
    assert client.get(f"/api/tutors/{pid}").status_code == 404
    assert client.get("/api/tutors").json() == []


def test_invalid_profile_validation(client):
    reg = _register_only(client, "badprof@test.com")
    h = auth_header(reg["access_token"])
    bad = dict(VALID_PROFILE)
    bad["fee_per_hour"] = 100000
    assert client.put("/api/tutors/mine", json=bad, headers=h).status_code == 422
    bad2 = dict(VALID_PROFILE)
    bad2["subjects"] = ["Alchemy"]
    assert client.put("/api/tutors/mine", json=bad2, headers=h).status_code == 422
    bad3 = dict(VALID_PROFILE)
    bad3["classes"] = [13]
    assert client.put("/api/tutors/mine", json=bad3, headers=h).status_code == 422
