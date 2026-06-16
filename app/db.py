from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession, AsyncAttrs
from sqlalchemy.orm import DeclarativeBase
from app.config import config


engine = create_async_engine(url= config.env_data.DB_URl_ASYNC, echo=True)

async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_sessiion():
    async with async_session() as session:
        yield session
        await session.commit()

class Base(AsyncAttrs, DeclarativeBase):
    pass