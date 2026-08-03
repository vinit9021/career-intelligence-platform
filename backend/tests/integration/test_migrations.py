import pytest
from sqlalchemy import inspect, text
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings


def get_table_names(connection: Connection) -> set[str]:
    return set(inspect(connection).get_table_names())


@pytest.mark.asyncio
async def test_latest_migration_is_applied() -> None:
    engine = create_async_engine(
        get_settings().database_url,
        poolclass=NullPool,
    )

    try:
        async with engine.connect() as connection:
            table_names = await connection.run_sync(get_table_names)
            revision = await connection.scalar(text("SELECT version_num FROM alembic_version"))
    finally:
        await engine.dispose()

    assert {
        "alembic_version",
        "users",
        "profiles",
        "refresh_tokens",
        "resumes",
        "resume_parse_results",
    }.issubset(table_names)
    assert revision == "20260803_0003"
