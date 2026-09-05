"""Booking lifecycle tests — request, accept, reject, complete, cancel, guards."""

from tests.conftest import auth_header, make_verified_tutor


def _parent(client, email="parent@test.com"):
    r = client.post(
        "/api/auth/register",
        json={"email": email, "full_name": "Parent", "password": "secret123", "role": "parent"},
    )
    return r.json()


def _book(client, parent_token, tutor_id, **over):
    body = {
        "tutor_id": tutor_id,
        "student_name": "Ali",
        "student_class": 10,
        "subject": "Mathematics",
        "area": "Gulshan",
        "schedule_note": "MWF 5pm",
    }
    body.update(over)
    return client.post("/api/bookings", json=body, headers=auth_header(parent_token))


def _setup(client):
    tutor_token, tutor_id = make_verified_tutor(client)
    parent = _parent(client)
    return tutor_token, tutor_id, parent


def test_parent_books_verified_tutor(client):
    _tutor_token, tutor_id, parent = _setup(client)
    r = _book(client, parent["access_token"], tutor_id)
    assert r.status_code == 201, r.text
    b = r.json()
    assert b["status"] == "pending"
    assert b["fee_per_hour"] == 1500  # snapshot from profile
    assert b["parent_name"] == "Parent"
    assert b["tutor_name"] == "Tutor Sir"


def test_tutor_cannot_book(client):
    tutor_token, tutor_id, _ = _setup(client)
    r = _book(client, tutor_token, tutor_id)
    assert r.status_code == 403


def test_anonymous_cannot_book(client):
    _, tutor_id, _ = _setup(client)
    r = _book(client, "not-a-token", tutor_id)
    assert r.status_code in (401, 403)


def test_booking_unverified_or_missing_tutor_404(client):
    _, _tutor_id, parent = _setup(client)
    # tutor id that doesn't exist
    assert _book(client, parent["access_token"], 99999).status_code == 404


def test_full_lifecycle_accept_complete(client):
    tutor_token, tutor_id, parent = _setup(client)
    bid = _book(client, parent["access_token"], tutor_id).json()["id"]
    # accept
    r = client.post(f"/api/bookings/{bid}/accept", headers=auth_header(tutor_token))
    assert r.status_code == 200
    assert r.json()["status"] == "accepted"
    # reject after accept → 409
    r = client.post(f"/api/bookings/{bid}/reject", headers=auth_header(tutor_token))
    assert r.status_code == 409
    # complete
    r = client.post(f"/api/bookings/{bid}/complete", headers=auth_header(tutor_token))
    assert r.status_code == 200
    assert r.json()["status"] == "completed"
    # double complete → 409
    r = client.post(f"/api/bookings/{bid}/complete", headers=auth_header(tutor_token))
    assert r.status_code == 409


def test_reject_flow(client):
    tutor_token, tutor_id, parent = _setup(client)
    bid = _book(client, parent["access_token"], tutor_id).json()["id"]
    r = client.post(f"/api/bookings/{bid}/reject", headers=auth_header(tutor_token))
    assert r.status_code == 200
    assert r.json()["status"] == "rejected"


def test_wrong_tutor_cannot_act(client):
    _, tutor_id, parent = _setup(client)
    # second tutor
    other_token, _ = make_verified_tutor(client, email="other@test.com", name="Other Sir")
    bid = _book(client, parent["access_token"], tutor_id).json()["id"]
    # other tutor tries accept → 404 (foreign resource masked)
    r = client.post(f"/api/bookings/{bid}/accept", headers=auth_header(other_token))
    assert r.status_code == 404


def test_parent_cannot_accept_own_request(client):
    _, tutor_id, parent = _setup(client)
    bid = _book(client, parent["access_token"], tutor_id).json()["id"]
    r = client.post(f"/api/bookings/{bid}/accept", headers=auth_header(parent["access_token"]))
    assert r.status_code == 403


def test_cancel_by_parent_and_tutor(client):
    tutor_token, tutor_id, parent = _setup(client)
    bid = _book(client, parent["access_token"], tutor_id).json()["id"]
    # parent cancels pending
    r = client.post(f"/api/bookings/{bid}/cancel", headers=auth_header(parent["access_token"]))
    assert r.status_code == 200
    assert r.json()["status"] == "cancelled"
    # completed booking cannot be cancelled
    bid2 = _book(client, parent["access_token"], tutor_id, student_name="Zain").json()["id"]
    client.post(f"/api/bookings/{bid2}/accept", headers=auth_header(tutor_token))
    client.post(f"/api/bookings/{bid2}/complete", headers=auth_header(tutor_token))
    r = client.post(f"/api/bookings/{bid2}/cancel", headers=auth_header(tutor_token))
    assert r.status_code == 409


def test_mine_bookings_scoped(client):
    tutor_token, tutor_id, parent = _setup(client)
    _book(client, parent["access_token"], tutor_id)
    # tutor sees 1
    mine_t = client.get("/api/bookings/mine", headers=auth_header(tutor_token)).json()
    assert len(mine_t) == 1
    # parent sees 1
    mine_p = client.get("/api/bookings/mine", headers=auth_header(parent["access_token"])).json()
    assert len(mine_p) == 1
    # a different parent sees 0
    other_parent = _parent(client, email="parent2@test.com")
    mine_o = client.get(
        "/api/bookings/mine", headers=auth_header(other_parent["access_token"])
    ).json()
    assert mine_o == []


def test_fee_snapshot_locked_at_request(client):
    tutor_token, tutor_id, parent = _setup(client)
    _book(client, parent["access_token"], tutor_id).json()["id"]
    # tutor raises fee after request
    from tests.conftest import VALID_PROFILE

    p = dict(VALID_PROFILE)
    p["fee_per_hour"] = 5000
    client.put("/api/tutors/mine", json=p, headers=auth_header(tutor_token))
    b = client.get("/api/bookings/mine", headers=auth_header(parent["access_token"])).json()[0]
    assert b["fee_per_hour"] == 1500  # unchanged snapshot
