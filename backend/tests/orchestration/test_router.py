"""Tests for central workflow routing."""

from app.orchestration.router import (
    first_enabled_node,
    next_enabled_node,
    ordered_enabled_nodes,
)


def test_orders_enabled_nodes() -> None:
    result = ordered_enabled_nodes(
        [
            "cover_letter",
            "resume_parser",
            "resume_matching",
        ]
    )

    assert result == [
        "resume_parser",
        "resume_matching",
        "cover_letter",
    ]


def test_returns_first_node() -> None:
    result = first_enabled_node(
        [
            "resume_matching",
            "ats_optimization",
        ]
    )

    assert result == "resume_matching"


def test_returns_next_node() -> None:
    result = next_enabled_node(
        "resume_matching",
        [
            "resume_parser",
            "resume_matching",
            "skill_gap",
        ],
    )

    assert result == "skill_gap"


def test_returns_none_after_last_node() -> None:
    result = next_enabled_node(
        "skill_gap",
        [
            "resume_parser",
            "skill_gap",
        ],
    )

    assert result is None
