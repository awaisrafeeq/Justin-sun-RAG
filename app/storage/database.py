from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Create base class for models
Base = declarative_base()

# Database engine and session
engine = create_async_engine(settings.postgres_dsn, echo=False, future=True)
AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

# Export Base for models to use
__all__ = ['Base', 'engine', 'AsyncSessionLocal', 'get_session']