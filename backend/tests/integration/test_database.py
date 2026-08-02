import pytest

from app.db.checks import check_database_connection
from app.db.session import engine


@pytest.mark.asyncio
async def test_database_connection() -> None:
    try:
        assert await check_database_connection() is True
    finally:
        await engine.dispose()
