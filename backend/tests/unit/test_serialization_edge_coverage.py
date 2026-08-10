"""Coverage for all safe serialization helpers."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date, datetime
from enum import Enum
from typing import Any
from uuid import UUID

import pytest
from pydantic import BaseModel

from app.memory.serialization import (
    to_memory_value,
)
from app.orchestration.serialization import (
    to_checkpoint_value,
)
from app.tool_calling.serialization import (
    to_tool_value,
)

Serializer = Callable[
    [Any],
    Any,
]

SERIALIZERS: tuple[
    Serializer,
    ...,
] = (
    to_checkpoint_value,
    to_memory_value,
    to_tool_value,
)


class SampleEnum(Enum):
    VALUE = "value"


class SampleModel(BaseModel):
    name: str
    created: date


@pytest.mark.parametrize(
    "serializer",
    SERIALIZERS,
)
def test_serializes_primitive_values(
    serializer: Serializer,
) -> None:
    assert serializer(None) is None
    assert serializer("text") == "text"
    assert serializer(10) == 10
    assert serializer(1.5) == 1.5
    assert serializer(True) is True


@pytest.mark.parametrize(
    "serializer",
    SERIALIZERS,
)
def test_serializes_pydantic_model(
    serializer: Serializer,
) -> None:
    value = SampleModel(
        name="example",
        created=date(
            2026,
            8,
            10,
        ),
    )

    assert serializer(value) == {
        "name": "example",
        "created": "2026-08-10",
    }


@pytest.mark.parametrize(
    "serializer",
    SERIALIZERS,
)
def test_serializes_enum_uuid_and_dates(
    serializer: Serializer,
) -> None:
    identifier = UUID("00000000-0000-0000-0000-000000000001")

    assert serializer(SampleEnum.VALUE) == "value"

    assert serializer(identifier) == str(identifier)

    assert (
        serializer(
            date(
                2026,
                8,
                10,
            )
        )
        == "2026-08-10"
    )

    timestamp = datetime(
        2026,
        8,
        10,
        12,
        30,
    )

    assert serializer(timestamp) == timestamp.isoformat()


@pytest.mark.parametrize(
    "serializer",
    SERIALIZERS,
)
def test_serializes_nested_collections(
    serializer: Serializer,
) -> None:
    value = {
        1: (
            SampleEnum.VALUE,
            date(
                2026,
                8,
                10,
            ),
        ),
        "items": [UUID("00000000-0000-0000-0000-000000000002")],
    }

    result = serializer(value)

    assert result["1"] == [
        "value",
        "2026-08-10",
    ]

    assert result["items"] == [("00000000-0000-0000-0000-000000000002")]


@pytest.mark.parametrize(
    "serializer",
    SERIALIZERS,
)
def test_serializes_sets(
    serializer: Serializer,
) -> None:
    result = serializer(
        {
            "Python",
            "FastAPI",
        }
    )

    assert sorted(result) == [
        "FastAPI",
        "Python",
    ]


@pytest.mark.parametrize(
    "serializer",
    SERIALIZERS,
)
def test_rejects_unknown_objects(
    serializer: Serializer,
) -> None:
    with pytest.raises(TypeError):
        serializer(object())
