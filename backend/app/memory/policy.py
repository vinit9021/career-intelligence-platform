"""Validation rules controlling agent memory writes."""

from __future__ import annotations

import json
from typing import Any

from app.memory.models import MemoryRecord


class MemoryPolicyError(ValueError):
    """Raised when memory violates storage policy."""


class MemoryPolicy:
    """Protect memory from unsafe or invalid writes."""

    BLOCKED_KEY_PARTS = {
        "password",
        "passwd",
        "secret",
        "api_key",
        "apikey",
        "access_token",
        "refresh_token",
        "authorization",
        "bearer_token",
    }

    def __init__(
        self,
        *,
        max_value_bytes: int = 512_000,
    ) -> None:
        if max_value_bytes <= 0:
            raise ValueError("max_value_bytes must be positive.")

        self.max_value_bytes = max_value_bytes

    def validate(
        self,
        record: MemoryRecord,
    ) -> None:
        """Validate one memory record."""

        if record.scope == "short_term" and not record.session_id:
            raise MemoryPolicyError("Short-term memory requires a session_id.")

        if record.scope == "long_term" and record.namespace == "workflow":
            raise MemoryPolicyError("Workflow execution data cannot be stored as long-term memory.")

        if self._contains_blocked_key(record.key):
            raise MemoryPolicyError("Sensitive credential-like keys cannot be stored in memory.")

        self._validate_nested_keys(record.value)

        encoded = json.dumps(
            record.value,
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")

        if len(encoded) > self.max_value_bytes:
            raise MemoryPolicyError(
                f"Memory value exceeds maximum size of {self.max_value_bytes} bytes."
            )

    def _contains_blocked_key(
        self,
        key: str,
    ) -> bool:
        normalized = key.lower()

        return any(part in normalized for part in self.BLOCKED_KEY_PARTS)

    def _validate_nested_keys(
        self,
        value: Any,
    ) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                if self._contains_blocked_key(str(key)):
                    raise MemoryPolicyError(
                        "Sensitive credential-like data cannot be stored in memory."
                    )

                self._validate_nested_keys(item)

            return

        if isinstance(value, list):
            for item in value:
                self._validate_nested_keys(item)
