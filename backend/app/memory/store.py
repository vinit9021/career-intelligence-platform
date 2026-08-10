"""Memory storage abstraction and in-memory backend."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Protocol

from app.memory.models import (
    MemoryNamespace,
    MemoryRecord,
    MemoryScope,
)


class MemoryStore(Protocol):
    """Storage interface for agent memory."""

    async def upsert(
        self,
        record: MemoryRecord,
    ) -> MemoryRecord:
        """Create or update memory."""
        ...

    async def get(
        self,
        *,
        user_id: str,
        scope: MemoryScope,
        namespace: MemoryNamespace,
        key: str,
        session_id: str | None = None,
    ) -> MemoryRecord | None:
        """Retrieve one memory item."""
        ...

    async def list(
        self,
        *,
        user_id: str,
        scope: MemoryScope | None = None,
        namespace: (MemoryNamespace | None) = None,
        session_id: str | None = None,
    ) -> Sequence[MemoryRecord]:
        """List matching memories."""
        ...

    async def delete(
        self,
        *,
        user_id: str,
        scope: MemoryScope,
        namespace: MemoryNamespace,
        key: str,
        session_id: str | None = None,
    ) -> bool:
        """Delete one memory item."""
        ...

    async def clear_session(
        self,
        *,
        user_id: str,
        session_id: str,
    ) -> int:
        """Delete short-term session memory."""
        ...


class InMemoryMemoryStore:
    """Simple store suitable for tests and development."""

    def __init__(self) -> None:
        self._records: dict[
            tuple[
                str,
                MemoryScope,
                str,
                MemoryNamespace,
                str,
            ],
            MemoryRecord,
        ] = {}

    def _storage_session(
        self,
        *,
        scope: MemoryScope,
        session_id: str | None,
    ) -> str:
        if scope == "long_term":
            return ""

        return session_id or ""

    def _key(
        self,
        *,
        user_id: str,
        scope: MemoryScope,
        namespace: MemoryNamespace,
        key: str,
        session_id: str | None,
    ) -> tuple[
        str,
        MemoryScope,
        str,
        MemoryNamespace,
        str,
    ]:
        return (
            user_id,
            scope,
            self._storage_session(
                scope=scope,
                session_id=session_id,
            ),
            namespace,
            key,
        )

    async def upsert(
        self,
        record: MemoryRecord,
    ) -> MemoryRecord:
        storage_key = self._key(
            user_id=record.user_id,
            scope=record.scope,
            namespace=record.namespace,
            key=record.key,
            session_id=record.session_id,
        )

        existing = self._records.get(storage_key)

        now = datetime.now(UTC)

        if existing is not None:
            stored = record.model_copy(
                update={
                    "id": existing.id,
                    "created_at": (existing.created_at),
                    "updated_at": now,
                },
                deep=True,
            )

        else:
            stored = record.model_copy(
                update={
                    "updated_at": now,
                },
                deep=True,
            )

        self._records[storage_key] = stored

        return stored.model_copy(deep=True)

    async def get(
        self,
        *,
        user_id: str,
        scope: MemoryScope,
        namespace: MemoryNamespace,
        key: str,
        session_id: str | None = None,
    ) -> MemoryRecord | None:
        storage_key = self._key(
            user_id=user_id,
            scope=scope,
            namespace=namespace,
            key=key,
            session_id=session_id,
        )

        record = self._records.get(storage_key)

        if record is None:
            return None

        return record.model_copy(deep=True)

    async def list(
        self,
        *,
        user_id: str,
        scope: MemoryScope | None = None,
        namespace: (MemoryNamespace | None) = None,
        session_id: str | None = None,
    ) -> Sequence[MemoryRecord]:
        result: list[MemoryRecord] = []

        for record in self._records.values():
            if record.user_id != user_id:
                continue

            if scope is not None and record.scope != scope:
                continue

            if namespace is not None and record.namespace != namespace:
                continue

            if (
                record.scope == "short_term"
                and session_id is not None
                and record.session_id != session_id
            ):
                continue

            result.append(record.model_copy(deep=True))

        result.sort(
            key=lambda item: (
                item.updated_at,
                item.key,
            )
        )

        return result

    async def delete(
        self,
        *,
        user_id: str,
        scope: MemoryScope,
        namespace: MemoryNamespace,
        key: str,
        session_id: str | None = None,
    ) -> bool:
        storage_key = self._key(
            user_id=user_id,
            scope=scope,
            namespace=namespace,
            key=key,
            session_id=session_id,
        )

        return (
            self._records.pop(
                storage_key,
                None,
            )
            is not None
        )

    async def clear_session(
        self,
        *,
        user_id: str,
        session_id: str,
    ) -> int:
        keys = [
            key
            for key, record in self._records.items()
            if (
                record.user_id == user_id
                and record.scope == "short_term"
                and record.session_id == session_id
            )
        ]

        for key in keys:
            del self._records[key]

        return len(keys)
