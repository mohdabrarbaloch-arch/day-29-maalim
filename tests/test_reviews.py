"""Review tests — completed-only, owner-only, once-only, rating aggregation."""

from tests.conftest import auth_header, make_verified_tutor


def _parent(client, email="parent@test.com"):
    return client.post(
        "/api/auth/register",
        json={
            "email": email,
            "full_name": "Reviewer Parent",
            "password": "secret123",
            "role": "parent",
        },
    ).json()


def _completed_booking(client):
    """Returns (tutor_token, tutor_id, parent, bid) with a completed booking."""
    tutor_token, tutor_id = make_verified_tutor(client, email="revt@test.com", name="Rev Tutor")
    parent = _parent(client)
    bid = client.post(
        "/api/bookings",
        json={
            "tutor_id": tutor_id,
            "student_name": "Ali",
            "student_class": 10,
            "subject": "Mathematics",
            "area": "Gulshan",
        },
        headers=auth_header(parent["access_token"]),
    ).json()["id"]
    client.post(f"/api/bookings/{bid}/accept", headers=auth_header(tutor_token))
    client.post(f"/api/bookings/{bid}/complete", headers=auth_header(tutor_token))
    return tutor_token, tutor_id, parent, bid


def test_review_after_completed_booking(client):
    _, tutor_id, parent, bid = _completed_booking(client)
    r = client.post(
        "/api/reviews",
        json={"booking_id": bid, "rating": 5, "comment": "Excellent tutor!"},
        headers=auth_header(parent["access_token"]),
    )
    assert r.status_code == 201, r.text
    assert r.json()["rating"] == 5
    # tutor aggregates updated
    detail = client.get(f"/api/tutors/{tutor_id}").json()
    assert detail["avg_rating"] == 5.0
    assert detail["review_count"] == 1
    # public reviews endpoint shows parent name
    reviews = client.get(f"/api/tutors/{tutor_id}/reviews").json()
    assert reviews[0]["parent_name"] == "Reviewer Parent"


def test_cannot_review_pending_booking(client):
    _tutor_token, tutor_id, parent, _bid = _completed_booking(client)
    # create a fresh pending booking
    bid2 = client.post(
        "/api/bookings",
        json={
            "tutor_id": tutor_id,
            "student_name": "Sara",
            "student_class": 9,
            "subject": "Mathematics",
            "area": "Gulshan",
        },
        headers=auth_header(parent["access_token"]),
    ).json()["id"]
    r = client.post(
        "/api/reviews",
        json={"booking_id": bid2, "rating": 4, "comment": "too soon"},
        headers=auth_header(parent["access_token"]),
    )
    assert r.status_code == 409


def test_only_booking_parent_can_review(client):
    _, _tutor_id, _booking_parent, bid = _completed_booking(client)
    other = _parent(client, email="otherparent@test.com")
    r = client.post(
        "/api/reviews",
        json={"booking_id": bid, "rating": 1, "comment": "not mine"},
        headers=auth_header(other["access_token"]),
    )
    assert r.status_code == 404  # masked


def test_one_review_per_booking(client):
    _, _tutor_id, parent, bid = _completed_booking(client)
    h = auth_header(parent["access_token"])
    assert (
        client.post("/api/reviews", json={"booking_id": bid, "rating": 5}, headers=h).status_code
        == 201
    )
    r = client.post("/api/reviews", json={"booking_id": bid, "rating": 2}, headers=h)
    assert r.status_code == 409


def test_rating_validation(client):
    _, _tutor_id, parent, bid = _completed_booking(client)
    h = auth_header(parent["access_token"])
    assert (
        client.post("/api/reviews", json={"booking_id": bid, "rating": 9}, headers=h).status_code
        == 422
    )
    assert (
        client.post("/api/reviews", json={"booking_id": bid, "rating": 0}, headers=h).status_code
        == 422
    )


def test_multiple_reviews_average(client):
    t1 = make_verified_tutor(client, email="avg@test.com", name="Avg Tutor")[0]
    tid = client.get("/api/tutors?q=Avg").json()[0]["tutor_id"]
    for i, (email, rating) in enumerate(
        [("p1@test.com", 5), ("p2@test.com", 3), ("p3@test.com", 4)]
    ):
        parent = _parent(client, email=email)
        bid = client.post(
            "/api/bookings",
            json={
                "tutor_id": tid,
                "student_name": f"S{i}",
                "student_class": 9,
                "subject": "Mathematics",
                "area": "Gulshan",
            },
            headers=auth_header(parent["access_token"]),
        ).json()["id"]
        client.post(f"/api/bookings/{bid}/accept", headers=auth_header(t1))
        client.post(f"/api/bookings/{bid}/complete", headers=auth_header(t1))
        client.post(
            "/api/reviews",
            json={"booking_id": bid, "rating": rating, "comment": "ok"},
            headers=auth_header(parent["access_token"]),
        )
    detail = client.get(f"/api/tutors/{tid}").json()
    assert detail["review_count"] == 3
    assert abs(detail["avg_rating"] - 4.0) < 0.01  # (5+3+4)/3 = 4.0
