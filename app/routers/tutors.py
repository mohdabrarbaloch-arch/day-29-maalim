"""Tutors router — public browse/search + tutor-owned profile management."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_role
from app.models import Review, TutorProfile, User
from app.schemas import ReviewOut, TutorListItem, TutorProfileIn, TutorProfileOut

router = APIRouter(prefix="/api/tutors", tags=["tutors"])


def _to_list_item(profile: TutorProfile) -> TutorListItem:
    return TutorListItem(
        tutor_id=profile.id,
        name=profile.user.full_name,
        headline=profile.headline,
        qualification=profile.qualification,
        institution=profile.institution,
        experience_years=profile.experience_years,
        subjects=profile.subjects or [],
        classes=profile.classes or [],
        areas=profile.areas or [],
        fee_per_hour=profile.fee_per_hour,
        avg_rating=round(profile.avg_rating, 1),
        review_count=profile.review_count,
    )


@router.get("", response_model=list[TutorListItem])
def list_tutors(
    subject: str | None = Query(default=None),
    area: str | None = Query(default=None),
    student_class: int | None = Query(default=None, ge=1, le=12),
    min_fee: int | None = Query(default=None, ge=0),
    max_fee: int | None = Query(default=None, ge=0),
    q: str | None = Query(default=None, max_length=80),
    sort: str = Query(default="rating", pattern="^(rating|fee_low|fee_high|experience)$"),
    db: Session = Depends(get_db),
):
    """Public listing: only verified + visible + non-suspended tutors."""
    stmt = (
        select(TutorProfile)
        .join(User, TutorProfile.user_id == User.id)
        .where(
            TutorProfile.is_verified.is_(True),
            TutorProfile.is_visible.is_(True),
            User.is_suspended.is_(False),
            TutorProfile.headline != "",
        )
    )
    if min_fee is not None:
        stmt = stmt.where(TutorProfile.fee_per_hour >= min_fee)
    if max_fee is not None:
        stmt = stmt.where(TutorProfile.fee_per_hour <= max_fee)
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(
                TutorProfile.headline.ilike(like),
                TutorProfile.qualification.ilike(like),
                TutorProfile.institution.ilike(like),
                User.full_name.ilike(like),
            )
        )
    if sort == "fee_low":
        stmt = stmt.order_by(TutorProfile.fee_per_hour.asc())
    elif sort == "fee_high":
        stmt = stmt.order_by(TutorProfile.fee_per_hour.desc())
    elif sort == "experience":
        stmt = stmt.order_by(TutorProfile.experience_years.desc())
    else:
        stmt = stmt.order_by(TutorProfile.avg_rating.desc(), TutorProfile.review_count.desc())

    profiles = db.scalars(stmt).all()
    # Python-side JSON filters for cross-dialect portability
    subject_norm = subject.strip().title() if subject else None
    area_norm = area.strip().title() if area else None
    result = []
    for p in profiles:
        subs = set(p.subjects or [])
        ars = set(p.areas or [])
        cls = set(p.classes or [])
        if subject_norm and subject_norm not in subs:
            continue
        if area_norm and area_norm not in ars:
            continue
        if student_class is not None and student_class not in cls:
            continue
        result.append(p)
    return [_to_list_item(p) for p in result]


def _profile_out(profile: TutorProfile) -> TutorProfileOut:
    out = TutorProfileOut.model_validate(profile)
    out.name = profile.user.full_name
    return out


@router.get("/mine", response_model=TutorProfileOut)
def my_profile(
    user: User = Depends(require_role("tutor")),
    db: Session = Depends(get_db),
):
    profile = db.scalar(select(TutorProfile).where(TutorProfile.user_id == user.id))
    if profile is None:
        raise HTTPException(status_code=404, detail="No tutor profile found")
    return _profile_out(profile)


@router.put("/mine", response_model=TutorProfileOut)
def upsert_profile(
    payload: TutorProfileIn,
    user: User = Depends(require_role("tutor")),
    db: Session = Depends(get_db),
):
    profile = db.scalar(select(TutorProfile).where(TutorProfile.user_id == user.id))
    if profile is None:
        profile = TutorProfile(user_id=user.id)
        db.add(profile)
    profile.headline = payload.headline
    profile.bio = payload.bio
    profile.qualification = payload.qualification
    profile.institution = payload.institution
    profile.experience_years = payload.experience_years
    profile.subjects = payload.subjects
    profile.classes = payload.classes
    profile.areas = payload.areas
    profile.fee_per_hour = payload.fee_per_hour
    profile.is_visible = payload.is_visible
    # editing resets verification so admin re-checks the new info
    profile.is_verified = False
    profile.verified_at = None
    profile.admin_note = ""
    db.commit()
    db.refresh(profile)
    return _profile_out(profile)


@router.get("/{profile_id}", response_model=TutorProfileOut)
def tutor_detail(profile_id: int, db: Session = Depends(get_db)):
    """Public detail: only for verified+visible tutors (else 404)."""
    profile = db.get(TutorProfile, profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Tutor not found")
    if not profile.is_verified or not profile.is_visible or profile.user.is_suspended:
        raise HTTPException(status_code=404, detail="Tutor not found")
    return _profile_out(profile)


@router.get("/{profile_id}/reviews", response_model=list[ReviewOut])
def tutor_reviews(profile_id: int, db: Session = Depends(get_db)):
    profile = db.get(TutorProfile, profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Tutor not found")
    reviews = db.scalars(
        select(Review).where(Review.tutor_id == profile_id).order_by(Review.created_at.desc())
    ).all()
    out = []
    for r in reviews:
        parent = db.get(User, r.parent_id)
        item = ReviewOut.model_validate(r)
        item.parent_name = parent.full_name if parent else ""
        out.append(item)
    return out
