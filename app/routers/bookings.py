"""Bookings router — parent requests, tutor accepts/rejects/completes."""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, require_role
from app.models import Booking, TutorProfile, User
from app.schemas import BookingIn, BookingOut

router = APIRouter(prefix="/api/bookings", tags=["bookings"])

VALID_TRANSITIONS = {
    "pending": {"accepted", "rejected", "cancelled"},
    "accepted": {"completed", "cancelled"},
}


def _serialize(b: Booking, db: Session) -> BookingOut:
    out = BookingOut.model_validate(b)
    tutor = db.get(TutorProfile, b.tutor_id)
    parent = db.get(User, b.parent_id)
    out.tutor_name = tutor.user.full_name if tutor else ""
    out.parent_name = parent.full_name if parent else ""
    return out


def _booking_or_404(bid: int, db: Session) -> Booking:
    b = db.get(Booking, bid)
    if b is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    return b


@router.post("", response_model=BookingOut, status_code=status.HTTP_201_CREATED)
def create_booking(
    payload: BookingIn,
    user: User = Depends(require_role("parent")),
    db: Session = Depends(get_db),
):
    tutor = db.get(TutorProfile, payload.tutor_id)
    if tutor is None or not tutor.is_verified or not tutor.is_visible:
        raise HTTPException(status_code=404, detail="Tutor not found")
    if tutor.user.is_suspended:
        raise HTTPException(status_code=404, detail="Tutor not found")
    if user.is_suspended:
        raise HTTPException(status_code=403, detail="Account suspended")

    b = Booking(
        tutor_id=tutor.id,
        parent_id=user.id,
        student_name=payload.student_name,
        student_class=payload.student_class,
        subject=payload.subject,
        area=payload.area,
        fee_per_hour=tutor.fee_per_hour,  # snapshot of current fee
        schedule_note=payload.schedule_note,
        status="pending",
    )
    db.add(b)
    db.commit()
    db.refresh(b)
    return _serialize(b, db)


@router.get("/mine", response_model=list[BookingOut])
def my_bookings(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Parents see their requests; tutors see bookings on their profile."""
    if user.role == "tutor":
        profile = db.scalar(select(TutorProfile).where(TutorProfile.user_id == user.id))
        if profile is None:
            return []
        rows = db.scalars(
            select(Booking)
            .where(Booking.tutor_id == profile.id)
            .order_by(Booking.created_at.desc())
        ).all()
    else:
        rows = db.scalars(
            select(Booking).where(Booking.parent_id == user.id).order_by(Booking.created_at.desc())
        ).all()
    return [_serialize(b, db) for b in rows]


@router.post("/{bid}/accept", response_model=BookingOut)
def accept_booking(
    bid: int,
    user: User = Depends(require_role("tutor")),
    db: Session = Depends(get_db),
):
    b = _booking_or_404(bid, db)
    _ensure_owner_tutor(b, user, db)
    if b.status != "pending":
        raise HTTPException(status_code=409, detail=f"Cannot accept a {b.status} booking")
    b.status = "accepted"
    b.decided_at = datetime.now(UTC)
    db.commit()
    db.refresh(b)
    return _serialize(b, db)


@router.post("/{bid}/reject", response_model=BookingOut)
def reject_booking(
    bid: int,
    user: User = Depends(require_role("tutor")),
    db: Session = Depends(get_db),
):
    b = _booking_or_404(bid, db)
    _ensure_owner_tutor(b, user, db)
    if b.status != "pending":
        raise HTTPException(status_code=409, detail=f"Cannot reject a {b.status} booking")
    b.status = "rejected"
    b.decided_at = datetime.now(UTC)
    db.commit()
    db.refresh(b)
    return _serialize(b, db)


@router.post("/{bid}/complete", response_model=BookingOut)
def complete_booking(
    bid: int,
    user: User = Depends(require_role("tutor")),
    db: Session = Depends(get_db),
):
    b = _booking_or_404(bid, db)
    _ensure_owner_tutor(b, user, db)
    if b.status != "accepted":
        raise HTTPException(status_code=409, detail="Only accepted bookings can be completed")
    b.status = "completed"
    b.decided_at = datetime.now(UTC)
    db.commit()
    db.refresh(b)
    return _serialize(b, db)


@router.post("/{bid}/cancel", response_model=BookingOut)
def cancel_booking(
    bid: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    b = _booking_or_404(bid, db)
    # either the parent who created it or the owning tutor may cancel
    if user.role == "parent" and b.parent_id != user.id:
        raise HTTPException(status_code=404, detail="Booking not found")
    if user.role == "tutor":
        _ensure_owner_tutor(b, user, db)
    if b.status not in ("pending", "accepted"):
        raise HTTPException(status_code=409, detail=f"Cannot cancel a {b.status} booking")
    b.status = "cancelled"
    b.decided_at = datetime.now(UTC)
    db.commit()
    db.refresh(b)
    return _serialize(b, db)


def _ensure_owner_tutor(b: Booking, user: User, db: Session) -> None:
    profile = db.scalar(select(TutorProfile).where(TutorProfile.user_id == user.id))
    if profile is None or profile.id != b.tutor_id:
        raise HTTPException(status_code=404, detail="Booking not found")
