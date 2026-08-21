"""Assertions for asynchronous events."""

from collections.abc import Iterable

from framework.models.event import DomainEvent


def find_event(events: Iterable[dict[str, object]], event_type: str) -> DomainEvent:
    for payload in events:
        if payload.get("event_type") == event_type:
            return DomainEvent.model_validate(payload)
    raise AssertionError(f"Event '{event_type}' was not received")


def assert_unique_event_ids(events: Iterable[dict[str, object]]) -> None:
    ids = [str(event.get("event_id")) for event in events]
    assert len(ids) == len(set(ids)), f"Duplicate event IDs detected: {ids}"
