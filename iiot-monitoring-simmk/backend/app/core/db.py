import asyncio
import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.models.db_models import Base

log = logging.getLogger(__name__)

engine = create_async_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncSession:
    async with SessionLocal() as session:
        yield session


async def init_db() -> None:
    retries = 10
    for attempt in range(1, retries + 1):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

                if settings.database_url.startswith("postgresql"):
                    await conn.execute(text("CREATE EXTENSION IF NOT EXISTS timescaledb"))
                    await conn.execute(
                        text(
                            "SELECT create_hypertable('telemetry','ts', if_not_exists => TRUE)"
                        )
                    )
                    await conn.execute(
                        text("SELECT create_hypertable('alarms','ts', if_not_exists => TRUE)")
                    )
            return
        except Exception as exc:
            log.warning("DB init attempt %d/%d failed: %s", attempt, retries, exc)
            if attempt == retries:
                raise
            await asyncio.sleep(2)
