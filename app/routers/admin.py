"""Admin router — verify/reject tutor profiles, suspend users, platform stats."""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_role
from app.models import Booking, TutorProfile, User
from app.schemas import AdminSuspendIn, AdminVerifyIn, StatsOut, TutorProfileOut

router = APIRouter(prefix="/api/admin", tags=["admin"])

admin_only = require_role("admin")


@router.get("/tutors/pending", response_model=list[TutorProfileOut])
def pending_tutors(
    _: User = Depends(admin_only),
    db: Session = Depends(get_db),
):
    rows = db.scalars(
        select(TutorProfile)
        .where(TutorProfile.is_verified.is_(False), TutorProfile.headline != "")
        .order_by(TutorProfile.created_at.desc())
    ).all()
    return rows


@router.get("/tutors", response_model=list[TutorProfileOut])
def all_tutors(
    _: User = Depends(admin_only),
    db: Session = Depends(get_db),
):
    rows = db.scalars(select(TutorProfile).order_by(TutorProfile.created_at.desc())).all()
    return rows


@router.post("/tutors/{profile_id}/verify", response_model=TutorProfileOut)
def verify_tutor(
    profile_id: int,
    payload: AdminVerifyIn,
    _: User = Depends(admin_only),
    db: Session = Depends(get_db),
):
    profile = db.get(TutorProfile, profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Tutor profile not found")
    if not profile.headline:
        raise HTTPException(status_code=400, detail="Tutor has not completed their profile")
    if payload.verify:
        profile.is_verified = True
        profile.verified_at = datetime.now(UTC)
        profile.admin_note = payload.note or "Approved"
        profile.is_visible = True
    else:
        profile.is_verified = False
        profile.verified_at = None
        profile.is_visible = False
        profile.admin_note = payload.note or "Rejected — please update your profile"
    db.commit()
    db.refresh(profile)
    return profile


@router.post("/users/{uid}/suspend")
def suspend_user(
    uid: int,
    payload: AdminSuspendIn,
    _: User = Depends(admin_only),
    db: Session = Depends(get_db),
):
    user = db.get(User, uid)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if user.role == "admin":
        raise HTTPException(status_code=400, detail="Cannot suspend an admin")
    user.is_suspended = payload.suspend
    if payload.suspend:
        # hide their tutor profile from public while suspended
        profile = db.scalar(select(TutorProfile).where(TutorProfile.user_id == uid))
        if profile:
            profile.is_visible = False
            profile.is_verified = False
    db.commit()
    return {"id": user.id, "suspended": user.is_suspended}


@router.get("/users", response_model=list[dict])
def list_users(
    _: User = Depends(admin_only),
    db: Session = Depends(get_db),
):
    rows = db.scalars(select(User).order_by(User.created_at.desc())).all()
    return [
        {
            "id": u.id,
            "email": u.email,
            "full_name": u.full_name,
            "role": u.role,
            "is_suspended": u.is_suspended,
            "created_at": u.created_at.isoformat(),
        }
        for u in rows
    ]


@router.get("/stats", response_model=StatsOut)
def stats(
    _: User = Depends(admin_only),
    db: Session = Depends(get_db),
):
    total_users = db.scalar(select(func.count(User.id))) or 0
    total_parents = db.scalar(select(func.count(User.id)).where(User.role == "parent")) or 0
    total_tutors = db.scalar(select(func.count(User.id)).where(User.role == "tutor")) or 0
    tutors_pending = (
        db.scalar(
            select(func.count(TutorProfile.id)).where(
                TutorProfile.is_verified.is_(False), TutorProfile.headline != ""
            )
        )
        or 0
    )
    tutors_verified = (
        db.scalar(select(func.count(TutorProfile.id)).where(TutorProfile.is_verified.is_(True)))
        or 0
    )
    bookings_total = db.scalar(select(func.count(Booking.id))) or 0
    bookings_pending = (
        db.scalar(select(func.count(Booking.id)).where(Booking.status == "pending")) or 0
    )
    bookings_completed = (
        db.scalar(select(func.count(Booking.id)).where(Booking.status == "completed")) or 0
    )
    gmv = (
        db.scalar(
            select(func.coalesce(func.sum(Booking.fee_per_hour), 0)).where(
                Booking.status == "completed"
            )
        )
        or 0
    )
    return StatsOut(
        total_users=total_users,
        total_parents=total_parents,
        total_tutors=total_tutors,
        tutors_pending=tutors_pending,
        tutors_verified=tutors_verified,
        bookings_total=bookings_total,
        bookings_pending=bookings_pending,
        bookings_completed=bookings_completed,
        gmv_pkr=int(gmv),
    )
