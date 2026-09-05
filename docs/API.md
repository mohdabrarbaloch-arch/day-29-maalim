# Maalim API Reference

Base URL: `http://localhost:8000` · Auth: `Authorization: Bearer <token>`
Interactive docs at `/docs` (OpenAPI).

## Auth
| Method | Path | Body | Access |
|---|---|---|---|
| POST | `/api/auth/register` | email, full_name, phone, password, role (`parent`\|`tutor`) | public · 5/min |
| POST | `/api/auth/login` | email, password | public · 10/min |

**Responses:** `200/201` → `{access_token, token_type, role, name}`. Errors: `401` bad credentials, `403` suspended/deactivated, `409` email exists, `429` rate limit.

## Tutors
| Method | Path | Access |
|---|---|---|
| GET | `/api/tutors` | public — verified+visible only |
| GET | `/api/tutors/{id}` | public — verified+visible only (else 404) |
| GET | `/api/tutors/{id}/reviews` | public |
| GET | `/api/tutors/mine` | tutor |
| PUT | `/api/tutors/mine` | tutor — body: profile fields |

**List query params:** `subject`, `area`, `student_class` (1–12), `min_fee`, `max_fee`, `q` (search), `sort` (`rating`\|`fee_low`\|`fee_high`\|`experience`).
**Profile body:** `headline`, `bio`, `qualification`, `institution`, `experience_years`, `subjects[]`, `classes[]`, `areas[]`, `fee_per_hour` (50–50,000 PKR), `is_visible`.
**Validation:** subjects whitelisted; classes 1–12; saving resets verification.

## Bookings
| Method | Path | Access |
|---|---|---|
| POST | `/api/bookings` | parent — `{tutor_id, student_name, student_class, subject, area, schedule_note}` |
| GET | `/api/bookings/mine` | parent or tutor |
| POST | `/api/bookings/{id}/accept` | owning tutor |
| POST | `/api/bookings/{id}/reject` | owning tutor |
| POST | `/api/bookings/{id}/complete` | owning tutor (accepted only) |
| POST | `/api/bookings/{id}/cancel` | parent or owning tutor |

**Rules:** booking snapshots the tutor's current `fee_per_hour`; only verified+visible tutors can be booked (404 otherwise); illegal transitions → `409`; foreign bookings → `404`.

## Reviews
| Method | Path | Access |
|---|---|---|
| POST | `/api/reviews` | parent — `{booking_id, rating 1–5, comment}` |

**Rules:** only the booking's parent; only `completed` bookings; one review per booking (`409`); updates tutor's avg rating + count.

## Admin
| Method | Path | Access |
|---|---|---|
| GET | `/api/admin/stats` | admin |
| GET | `/api/admin/tutors/pending` | admin |
| GET | `/api/admin/tutors` | admin |
| POST | `/api/admin/tutors/{id}/verify` | admin — `{verify: bool, note}` |
| GET | `/api/admin/users` | admin |
| POST | `/api/admin/users/{id}/suspend` | admin — `{suspend: bool}` |

## Error format
```json
{ "detail": "human-readable message" }
```
Status codes: `400` validation/rule, `401` unauthenticated, `403` forbidden/suspended, `404` not found (foreign resources are masked as 404), `409` state conflict, `429` rate limited.
