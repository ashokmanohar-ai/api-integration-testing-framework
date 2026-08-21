"""Customer request and response contracts."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class CreateCustomerRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=50)
    last_name: str = Field(min_length=1, max_length=50)
    email: EmailStr


class UpdateCustomerRequest(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=50)
    last_name: str | None = Field(default=None, min_length=1, max_length=50)
    status: Literal["ACTIVE", "INACTIVE"] | None = None


class CustomerResponse(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    email: EmailStr
    status: Literal["ACTIVE", "INACTIVE"]
    created_at: datetime
