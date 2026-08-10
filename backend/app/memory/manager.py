"""High-level memory API used by AI agents."""

from __future__ import annotations

from typing import Any

from app.memory.models import (
    MemoryNamespace,
    MemoryRecord,
    MemoryScope,
)
from app.memory.policy import MemoryPolicy
from app.memory.serialization import (
    to_memory_value,
)
from app.memory.store import MemoryStore


class MemoryManager:
    """Coordinates memory validation and persistence."""

    def __init__(
        self,
        store: MemoryStore,
        *,
        policy: MemoryPolicy | None = None,
    ) -> None:
        self.store = store

        self.policy = policy if policy is not None else MemoryPolicy()

    async def remember(
        self,
        *,
        user_id: str,
        scope: MemoryScope,
        namespace: MemoryNamespace,
        key: str,
        value: Any,
        session_id: str | None = None,
        source_agent: str | None = None,
        metadata: (dict[str, str] | None) = None,
    ) -> MemoryRecord:
        """Create or update memory."""

        normalized_value = to_memory_value(value)

        record = MemoryRecord(
            user_id=user_id,
            scope=scope,
            namespace=namespace,
            key=key,
            value=normalized_value,
            session_id=session_id,
            source_agent=source_agent,
            metadata=metadata or {},
        )

        self.policy.validate(record)

        return await self.store.upsert(record)

    async def recall(
        self,
        *,
        user_id: str,
        scope: MemoryScope,
        namespace: MemoryNamespace,
        key: str,
        session_id: str | None = None,
    ) -> Any:
        """Return stored value or None."""

        record = await self.store.get(
            user_id=user_id,
            scope=scope,
            namespace=namespace,
            key=key,
            session_id=session_id,
        )

        if record is None:
            return None

        return record.value

    async def recall_namespace(
        self,
        *,
        user_id: str,
        scope: MemoryScope,
        namespace: MemoryNamespace,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        """Return all values in one namespace."""

        records = await self.store.list(
            user_id=user_id,
            scope=scope,
            namespace=namespace,
            session_id=session_id,
        )

        return {item.key: item.value for item in records}

    async def forget(
        self,
        *,
        user_id: str,
        scope: MemoryScope,
        namespace: MemoryNamespace,
        key: str,
        session_id: str | None = None,
    ) -> bool:
        """Delete one memory value."""

        return await self.store.delete(
            user_id=user_id,
            scope=scope,
            namespace=namespace,
            key=key,
            session_id=session_id,
        )

    async def clear_session(
        self,
        *,
        user_id: str,
        session_id: str,
    ) -> int:
        """Clear all short-term workflow memory."""

        return await self.store.clear_session(
            user_id=user_id,
            session_id=session_id,
        )

    async def build_context(
        self,
        *,
        user_id: str,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        """Build structured memory context for agents."""

        long_term_records = await self.store.list(
            user_id=user_id,
            scope="long_term",
        )

        short_term_records: list[MemoryRecord] = []

        if session_id is not None:
            records = await self.store.list(
                user_id=user_id,
                scope="short_term",
                session_id=session_id,
            )

            short_term_records = list(records)

        long_term: dict[
            str,
            dict[str, Any],
        ] = {}

        for record in long_term_records:
            namespace = long_term.setdefault(
                record.namespace,
                {},
            )

            namespace[record.key] = record.value

        short_term: dict[
            str,
            dict[str, Any],
        ] = {}

        for record in short_term_records:
            namespace = short_term.setdefault(
                record.namespace,
                {},
            )

            namespace[record.key] = record.value

        return {
            "long_term": long_term,
            "short_term": short_term,
        }
