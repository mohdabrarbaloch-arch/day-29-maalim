"""Pydantic v2 schemas — request/response validation."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator

Role = Literal["parent", "tutor"]
BookingStatus = Literal["pending", "accepted", "rejected", "completed", "cancelled"]

VALID_SUBJECTS = {
    "Mathematics",
    "Physics",
    "Chemistry",
    "Biology",
    "English",
    "Urdu",
    "Islamiat",
    "Computer Science",
    "Accounting",
    "Economics",
}
VALID_AREAS = {
    "Gulshan",
    "Gulistan-e-Johar",
    "DHA",
    "Clifton",
    "Saddar",
    "North Nazimabad",
    "Nazimabad",
    "Korangi",
    "Malir",
    "Landhi",
    "Shah Faisal",
    "PECHS",
    "Bahadurabad",
    "F.B. Area",
    "Defence",
}
TUTOR_ROLES = {"parent", "tutor"}


def _canonicalize(values: list[str], allowed: set[str], label: str) -> list[str]:
    """Case-insensitive match against the allowed set, returning canonical forms."""
    by_lower = {a.lower(): a for a in allowed}
    out = []
    for v in values:
        key = v.strip().lower()
        if key not in by_lower:
            raise ValueError(f"Unknown {label}: {v.strip()!r}")
        out.append(by_lower[key])
    return sorted(set(out))


class RegisterIn(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=120)
    phone: str = Field(default="", max_length=30)
    password: str = Field(min_length=8, max_length=128)
    role: Literal["parent", "tutor"] = "parent"

    @field_validator("full_name")
    @classmethod
    def name_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("full_name cannot be blank")
        return v.strip()


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    name: str


class TutorProfileIn(BaseModel):
    headline: str = Field(min_length=5, max_length=160)
    bio: str = Field(default="", max_length=2000)
    qualification: str = Field(default="", max_length=160)
    institution: str = Field(default="", max_length=160)
    experience_years: int = Field(ge=0, le=50)
    subjects: list[str] = Field(min_length=1, max_length=10)
    classes: list[int] = Field(min_length=1, max_length=12)
    areas: list[str] = Field(min_length=1, max_length=10)
    fee_per_hour: int = Field(ge=50, le=50000)
    is_visible: bool = False

    @field_validator("subjects")
    @classmethod
    def check_subjects(cls, v: list[str]) -> list[str]:
        return _canonicalize(v, VALID_SUBJECTS, "subjects")

    @field_validator("classes")
    @classmethod
    def check_classes(cls, v: list[int]) -> list[int]:
        for c in v:
            if c < 1 or c > 12:
                raise ValueError("class must be between 1 and 12")
        return sorted(set(v))

    @field_validator("areas")
    @classmethod
    def check_areas(cls, v: list[str]) -> list[str]:
        return _canonicalize(v, VALID_AREAS, "areas")


class TutorProfileOut(BaseModel):
    id: int
    user_id: int
    name: str = ""
    headline: str
    bio: str
    qualification: str
    institution: str
    experience_years: int
    subjects: list[str]
    classes: list[int]
    areas: list[str]
    fee_per_hour: int
    is_verified: bool
    verified_at: datetime | None
    admin_note: str
    is_visible: bool
    avg_rating: float
    review_count: int

    class Config:
        from_attributes = True


class TutorListItem(BaseModel):
    tutor_id: int
    name: str
    headline: str
    qualification: str
    institution: str
    experience_years: int
    subjects: list[str]
    classes: list[int]
    areas: list[str]
    fee_per_hour: int
    avg_rating: float
    review_count: int

    class Config:
        from_attributes = True


class BookingIn(BaseModel):
    tutor_id: int
    student_name: str = Field(min_length=2, max_length=120)
    student_class: int = Field(ge=1, le=12)
    subject: str = Field(min_length=2, max_length=80)
    area: str = Field(min_length=2, max_length=80)
    schedule_note: str = Field(default="", max_length=1000)

    @field_validator("subject")
    @classmethod
    def title_subject(cls, v: str) -> str:
        return v.strip().title()

    @field_validator("area")
    @classmethod
    def title_area(cls, v: str) -> str:
        return v.strip().title()


class BookingOut(BaseModel):
    id: int
    tutor_id: int
    parent_id: int
    tutor_name: str = ""
    parent_name: str = ""
    student_name: str
    student_class: int
    subject: str
    area: str
    fee_per_hour: int
    schedule_note: str
    status: str
    created_at: datetime
    decided_at: datetime | None

    class Config:
        from_attributes = True


class ReviewIn(BaseModel):
    booking_id: int
    rating: int = Field(ge=1, le=5)
    comment: str = Field(default="", max_length=1000)


class ReviewOut(BaseModel):
    id: int
    booking_id: int
    tutor_id: int
    parent_id: int
    parent_name: str = ""
    rating: int
    comment: str
    created_at: datetime

    class Config:
        from_attributes = True


class AdminVerifyIn(BaseModel):
    verify: bool
    note: str = Field(default="", max_length=500)


class AdminSuspendIn(BaseModel):
    suspend: bool


class StatsOut(BaseModel):
    total_users: int
    total_parents: int
    total_tutors: int
    tutors_pending: int
    tutors_verified: int
    bookings_total: int
    bookings_pending: int
    bookings_completed: int
    gmv_pkr: int  # sum of completed booking fees (platform value metric)
