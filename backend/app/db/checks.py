from sqlalchemy import text

from app.db.session import engine


async def check_database_connection() -> bool:
    async with engine.connect() as connection:
        result = await connection.execute(text("SELECT 1"))

    return bool(result.scalar_one() == 1)
