"""Reviews router — parent reviews a completed booking once."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_role
from app.models import Booking, Review, TutorProfile, User
from app.schemas import ReviewIn, ReviewOut

router = APIRouter(prefix="/api/reviews", tags=["reviews"])


@router.post("", response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
def create_review(
    payload: ReviewIn,
    user: User = Depends(require_role("parent")),
    db: Session = Depends(get_db),
):
    booking = db.get(Booking, payload.booking_id)
    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.parent_id != user.id:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.status != "completed":
        raise HTTPException(
            status_code=409,
            detail="Only completed bookings can be reviewed",
        )
    existing = db.scalar(select(Review).where(Review.booking_id == booking.id))
    if existing:
        raise HTTPException(status_code=409, detail="This booking has already been reviewed")

    review = Review(
        booking_id=booking.id,
        tutor_id=booking.tutor_id,
        parent_id=user.id,
        rating=payload.rating,
        comment=payload.comment.strip(),
    )
    db.add(review)
    db.flush()
    _recompute_tutor_rating(booking.tutor_id, db)
    db.commit()
    db.refresh(review)
    out = ReviewOut.model_validate(review)
    out.parent_name = user.full_name
    return out


def _recompute_tutor_rating(tutor_id: int, db: Session) -> None:
    avg, cnt = db.execute(
        select(func.avg(Review.rating), func.count(Review.id)).where(Review.tutor_id == tutor_id)
    ).one()
    profile = db.get(TutorProfile, tutor_id)
    if profile:
        profile.avg_rating = float(avg or 0.0)
        profile.review_count = int(cnt or 0)
