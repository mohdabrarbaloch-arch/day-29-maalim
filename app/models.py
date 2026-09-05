"""SQLAlchemy models — users, tutor_profiles, bookings, reviews."""

from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(120))
    phone: Mapped[str] = mapped_column(String(30), default="")
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="parent")  # parent|tutor|admin
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_suspended: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    tutor_profile: Mapped["TutorProfile | None"] = relationship(
        back_populates="user", cascade="all, delete-orphan", uselist=False
    )


class TutorProfile(Base):
    __tablename__ = "tutor_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    headline: Mapped[str] = mapped_column(String(160))
    bio: Mapped[str] = mapped_column(Text, default="")
    qualification: Mapped[str] = mapped_column(String(160), default="")
    institution: Mapped[str] = mapped_column(String(160), default="")
    experience_years: Mapped[int] = mapped_column(Integer, default=0)
    subjects: Mapped[list] = mapped_column(JSON, default=list)  # e.g. ["Mathematics"]
    classes: Mapped[list] = mapped_column(JSON, default=list)  # e.g. [9, 10]
    areas: Mapped[list] = mapped_column(JSON, default=list)  # e.g. ["Gulshan"]
    fee_per_hour: Mapped[int] = mapped_column(Integer)  # PKR
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    admin_note: Mapped[str] = mapped_column(Text, default="")
    is_visible: Mapped[bool] = mapped_column(Boolean, default=False)
    avg_rating: Mapped[float] = mapped_column(Float, default=0.0)
    review_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user: Mapped[User] = relationship(back_populates="tutor_profile")


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tutor_id: Mapped[int] = mapped_column(ForeignKey("tutor_profiles.id"), index=True)
    parent_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    student_name: Mapped[str] = mapped_column(String(120))
    student_class: Mapped[int] = mapped_column(Integer)
    subject: Mapped[str] = mapped_column(String(80))
    area: Mapped[str] = mapped_column(String(80))
    fee_per_hour: Mapped[int] = mapped_column(Integer)  # snapshot at request
    schedule_note: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(
        String(20), default="pending", index=True
    )  # pending|accepted|rejected|completed|cancelled
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    review: Mapped["Review | None"] = relationship(back_populates="booking", uselist=False)


class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = (UniqueConstraint("booking_id", name="uq_review_booking"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    booking_id: Mapped[int] = mapped_column(ForeignKey("bookings.id"), unique=True, index=True)
    tutor_id: Mapped[int] = mapped_column(ForeignKey("tutor_profiles.id"), index=True)
    parent_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    rating: Mapped[int] = mapped_column(Integer)  # 1..5
    comment: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    booking: Mapped[Booking] = relationship(back_populates="review")
