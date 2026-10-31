import re
from datetime import date
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

NonBlank = Annotated[str, Field(min_length=1, max_length=200)]


class StudentFields(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: NonBlank
    date_of_birth: date
    email: str | None = Field(default=None, max_length=254)
    phone: str | None = Field(default=None, max_length=30)
    course: str | None = Field(default=None, max_length=200)
    address: str | None = Field(default=None, max_length=500)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str | None) -> str | None:
        if value is not None:
            value = value.strip()
            if not value or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
                raise ValueError("A valid email address is required")
        return value

    @field_validator("phone", "course", "address")
    @classmethod
    def empty_optional_values_become_none(cls, value: str | None) -> str | None:
        return value.strip() or None if value is not None else None

    @model_validator(mode="after")
    def require_contact_method(self):
        if not self.email and not self.phone:
            raise ValueError("Provide at least an email address or phone number")
        return self


class StudentCreate(StudentFields):
    student_id: Annotated[str, Field(min_length=1, max_length=50)]


class StudentUpdate(StudentFields):
    pass


class Student(StudentCreate):
    model_config = ConfigDict(from_attributes=True)
