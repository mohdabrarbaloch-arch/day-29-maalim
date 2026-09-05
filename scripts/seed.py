"""Seed script — demo admin, parents, verified tutors, bookings, reviews."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.database import Base, SessionLocal, engine
from app.models import Booking, Review, TutorProfile, User
from app.security import hash_password

Base.metadata.create_all(bind=engine)


def get_or_create_user(db, email, full_name, phone, password, role):
    user = db.scalar(select(User).where(User.email == email))
    if user:
        return user
    user = User(
        email=email,
        full_name=full_name,
        phone=phone,
        password_hash=hash_password(password),
        role=role,
    )
    db.add(user)
    db.flush()
    return user


def upsert_profile(db, user, **kw):
    profile = db.scalar(select(TutorProfile).where(TutorProfile.user_id == user.id))
    if profile is None:
        profile = TutorProfile(user_id=user.id)
        db.add(profile)
    for k, v in kw.items():
        setattr(profile, k, v)
    db.flush()
    return profile


def main():
    db = SessionLocal()

    # --- admin ---
    admin = get_or_create_user(
        db, "admin@maalim.pk", "Platform Admin", "+923000000000", "admin12345", "admin"
    )
    admin.is_active = True
    admin.is_suspended = False

    # --- parents ---
    parent1 = get_or_create_user(
        db, "fatima@example.com", "Fatima Khan", "+923011111111", "parent1234", "parent"
    )
    parent2 = get_or_create_user(
        db, "ahmed@example.com", "Ahmed Raza", "+923022222222", "parent1234", "parent"
    )

    # --- tutors (all verified so the marketplace feels alive) ---
    t1 = get_or_create_user(
        db, "sir.bilal@example.com", "Bilal Ahmed", "+923033333333", "tutor1234", "tutor"
    )
    p1 = upsert_profile(
        db,
        t1,
        headline="O/A-Level Mathematics & Physics tutor, 6 yrs experience",
        bio="NED University graduate. Specialise in O/A-Level Mathematics and Physics.",
        qualification="B.E. Electrical (NED)",
        institution="NED University",
        experience_years=6,
        subjects=["Mathematics", "Physics"],
        classes=[9, 10, 11, 12],
        areas=["Gulshan", "Gulistan-e-Johar"],
        fee_per_hour=1500,
        is_verified=True,
        verified_at=datetime.now(UTC),
        is_visible=True,
    )

    t2 = get_or_create_user(
        db, "miss.aisha@example.com", "Aisha Siddiqui", "+923044444444", "tutor1234", "tutor"
    )
    p2 = upsert_profile(
        db,
        t2,
        headline="English & Urdu language expert — Matric to Inter",
        bio="MA English (University of Karachi). Patient, result-focused tutor for Matric & Inter.",
        qualification="MA English (UoK)",
        institution="University of Karachi",
        experience_years=4,
        subjects=["English", "Urdu"],
        classes=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        areas=["DHA", "Clifton", "PECHS"],
        fee_per_hour=1200,
        is_verified=True,
        verified_at=datetime.now(UTC),
        is_visible=True,
    )

    t3 = get_or_create_user(
        db, "sir.danish@example.com", "Danish Ali", "+923055555555", "tutor1234", "tutor"
    )
    p3 = upsert_profile(
        db,
        t3,
        headline="FSc Biology & Chemistry — Medical entry-test prep",
        bio="MBBS student (Dow). Help FSc students build concepts + entry-test strategies.",
        qualification="MBBS (Dow University)",
        institution="Dow University of Health Sciences",
        experience_years=2,
        subjects=["Biology", "Chemistry"],
        classes=[11, 12],
        areas=["Saddar", "Bahadurabad", "North Nazimabad"],
        fee_per_hour=1800,
        is_verified=True,
        verified_at=datetime.now(UTC),
        is_visible=True,
    )

    t4 = get_or_create_user(
        db, "sir.umair@example.com", "Umair Farooq", "+923066666666", "tutor1234", "tutor"
    )
    p4 = upsert_profile(
        db,
        t4,
        headline="Computer Science + Accounting (IGCSE/O-Level)",
        bio="ACCA qualified, teaches Computer Science & Accounting for IGCSE. Practical, code-first lessons.",
        qualification="ACCA",
        institution="ACCA UK",
        experience_years=7,
        subjects=["Computer Science", "Accounting"],
        classes=[9, 10, 11, 12],
        areas=["F.B. Area", "Nazimabad", "Gulshan"],
        fee_per_hour=2000,
        is_verified=True,
        verified_at=datetime.now(UTC),
        is_visible=True,
    )

    t5 = get_or_create_user(
        db, "sir.hamza@example.com", "Hamza Sheikh", "+923077777777", "tutor1234", "tutor"
    )
    p5 = upsert_profile(
        db,
        t5,
        headline="Primary & middle-school all subjects",
        bio="B.Ed (Hamdard). Warm, patient with young kids. Urdu/English medium both.",
        qualification="B.Ed",
        institution="Hamdard University",
        experience_years=5,
        subjects=["Mathematics", "English", "Urdu", "Islamiat"],
        classes=[1, 2, 3, 4, 5, 6, 7, 8],
        areas=["Korangi", "Landhi", "Shah Faisal"],
        fee_per_hour=800,
        is_verified=True,
        verified_at=datetime.now(UTC),
        is_visible=True,
    )

    t6 = get_or_create_user(
        db, "tutor.pending@example.com", "Sana Javed", "+923088888888", "tutor1234", "tutor"
    )
    upsert_profile(
        db,
        t6,
        headline="Economics & Mathematics for FSc/Inter",
        bio="Just submitted — awaiting admin verification.",
        qualification="M.Sc Economics",
        institution="University of Karachi",
        experience_years=1,
        subjects=["Economics", "Mathematics"],
        classes=[11, 12],
        areas=["Malir", "Gulistan-e-Johar"],
        fee_per_hour=1300,
        is_verified=False,
        verified_at=None,
        is_visible=False,
    )

    # --- demo bookings with history ---
    def booking(
        tutor_profile, parent, status, student_name, student_class, subject, area, days_ago
    ):
        existing = db.scalar(
            select(Booking).where(
                Booking.tutor_id == tutor_profile.id,
                Booking.parent_id == parent.id,
                Booking.student_name == student_name,
            )
        )
        if existing:
            return existing
        created = datetime.now(UTC) - timedelta(days=days_ago)
        b = Booking(
            tutor_id=tutor_profile.id,
            parent_id=parent.id,
            student_name=student_name,
            student_class=student_class,
            subject=subject,
            area=area,
            fee_per_hour=tutor_profile.fee_per_hour,
            schedule_note="Mon/Wed/Fri 5-6pm",
            status=status,
        )
        b.created_at = created
        if status in ("accepted", "rejected", "completed", "cancelled"):
            b.decided_at = created + timedelta(hours=6)
        db.add(b)
        db.flush()
        return b

    b1 = booking(p1, parent1, "completed", "Hamza Khan", 11, "Mathematics", "Gulshan", 6)
    booking(p2, parent1, "accepted", "Hamza Khan", 5, "English", "DHA", 1)
    booking(p3, parent2, "pending", "Zainab Raza", 12, "Chemistry", "Saddar", 0)
    booking(p4, parent2, "rejected", "Zainab Raza", 10, "Accounting", "F.B. Area", 3)
    booking(p5, parent1, "cancelled", "Hamza Khan", 4, "Mathematics", "Korangi", 5)

    # review on the completed booking b1
    existing_review = db.scalar(select(Review).where(Review.booking_id == b1.id))
    if existing_review is None and b1.status == "completed":
        db.add(
            Review(
                booking_id=b1.id,
                tutor_id=b1.tutor_id,
                parent_id=parent1.id,
                rating=5,
                comment="Sir Bilal is excellent! My son's Maths improved from 62 to 84 in one term. Highly recommended.",
            )
        )
        # update p1 aggregates manually
        p1.avg_rating = 5.0
        p1.review_count = 1

    db.commit()
    db.close()
    print("Seed complete.")
    print("  Admin : admin@maalim.pk / admin12345")
    print("  Parent: fatima@example.com / parent1234  (or ahmed@example.com)")
    print("  Tutor : sir.bilal@example.com / tutor1234 (verified tutor)")


if __name__ == "__main__":
    main()
