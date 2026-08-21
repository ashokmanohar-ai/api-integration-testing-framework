"""Small query repositories prevent raw SQL from spreading through tests."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session


class ReadRepository:
    def __init__(self, session: Session, model: type[Any]) -> None:
        self.session = session
        self.model = model

    def get(self, record_id: str) -> Any | None:
        return self.session.get(self.model, record_id)

    def all(self) -> list[Any]:
        return list(self.session.scalars(select(self.model)).all())

    def count(self) -> int:
        return len(self.all())
