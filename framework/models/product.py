"""Product contracts."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CreateProductRequest(BaseModel):
    sku: str = Field(min_length=3, max_length=32, pattern=r"^[A-Z0-9-]+$")
    name: str = Field(min_length=1, max_length=100)
    price: float = Field(gt=0, le=1_000_000)
    inventory: int = Field(ge=0, le=100_000)


class ProductResponse(BaseModel):
    id: UUID
    sku: str
    name: str
    price: float
    inventory: int
    created_at: datetime
