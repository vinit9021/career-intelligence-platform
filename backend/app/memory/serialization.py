"""Serialization helpers for memory values."""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel


def to_memory_value(
    value: Any,
) -> Any:
    """Convert a value into JSON-compatible memory data."""

    if value is None:
        return None

    if isinstance(
        value,
        (str, int, float, bool),
    ):
        return value

    if isinstance(value, BaseModel):
        return to_memory_value(value.model_dump(mode="python"))

    if isinstance(value, Enum):
        return to_memory_value(value.value)

    if isinstance(value, UUID):
        return str(value)

    if isinstance(
        value,
        (datetime, date),
    ):
        return value.isoformat()

    if isinstance(value, dict):
        return {str(key): to_memory_value(item) for key, item in value.items()}

    if isinstance(
        value,
        (list, tuple, set),
    ):
        return [to_memory_value(item) for item in value]

    raise TypeError(f"Unsupported memory value type: {type(value).__name__}")
