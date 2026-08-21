"""Database consistency assertions kept out of test bodies."""

from typing import Any

from sqlalchemy import Select, select
from sqlalchemy.orm import Session


def assert_record_exists(session: Session, model: type[Any], record_id: str) -> Any:
    record = session.get(model, record_id)
    assert record is not None, f"{model.__name__}({record_id}) was not persisted"
    return record


def assert_record_count(session: Session, model: type[Any], expected: int) -> None:
    statement: Select[tuple[Any]] = select(model)
    actual = len(session.scalars(statement).all())
    assert actual == expected, f"Expected {expected} {model.__name__} records, found {actual}"
