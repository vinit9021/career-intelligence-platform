from collections.abc import AsyncIterator
from pathlib import Path

import pytest_asyncio
from httpx2 import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import Settings, get_settings
from app.db.base import Base
from app.db.session import get_db_session
from app.main import app
from app.models import Profile, RefreshToken, User

REGISTERED_TEST_MODELS = (
    User,
    Profile,
    RefreshToken,
)

SessionFactory = async_sessionmaker[AsyncSession]


@pytest_asyncio.fixture
async def test_session_factory(
    tmp_path: Path,
) -> AsyncIterator[SessionFactory]:
    database_path = tmp_path / "career-intelligence-test.db"

    engine = create_async_engine(f"sqlite+aiosqlite:///{database_path}")

    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        autoflush=False,
        expire_on_commit=False,
    )

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    try:
        yield session_factory
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def auth_client(
    test_session_factory: SessionFactory,
) -> AsyncIterator[AsyncClient]:
    test_settings = Settings.model_validate(
        {
            "app_name": ("Career Intelligence Platform API"),
            "app_env": "test",
            "app_version": "0.1.0",
            "api_v1_prefix": "/api/v1",
            "debug": False,
            "log_level": "INFO",
            "backend_cors_origins": ["http://localhost:3000"],
            "postgres_host": "unused",
            "postgres_port": 5432,
            "postgres_db": "unused",
            "postgres_user": "unused",
            "postgres_password": "unused",
            "jwt_access_secret": "a" * 64,
            "jwt_refresh_secret": "b" * 64,
            "jwt_algorithm": "HS256",
            "jwt_issuer": ("career-intelligence-platform-test"),
            "jwt_audience": ("career-intelligence-platform-api-test"),
            "access_token_expire_minutes": 15,
            "refresh_token_expire_days": 7,
        }
    )

    async def override_db_session() -> AsyncIterator[AsyncSession]:
        async with test_session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db_session] = override_db_session

    app.dependency_overrides[get_settings] = lambda: test_settings

    transport = ASGITransport(app=app)

    try:
        async with AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            yield client
    finally:
        app.dependency_overrides.clear()
