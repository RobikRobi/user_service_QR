from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession, AsyncAttrs
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool
from app.config import config
from uuid import uuid4


database_url = config.env_data.USERS_DATABASE_URL
if database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

connect_args = {
    "statement_cache_size": 0,
    "prepared_statement_name_func": lambda: f"__asyncpg_{uuid4()}__",
}
url = make_url(database_url)
query = dict(url.query)
sslmode = query.pop("sslmode", None)
query.pop("channel_binding", None)
query.setdefault("prepared_statement_cache_size", "0")

if sslmode and sslmode != "disable":
    connect_args["ssl"] = True

database_url = url.set(query=query)

engine = create_async_engine(
    url=database_url,
    echo=True,
    connect_args=connect_args,
    poolclass=NullPool,
)

async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_session():
    async with async_session() as session:
        yield session
        await session.commit()

class Base(AsyncAttrs, DeclarativeBase):
    pass


async def init_db():
    await engine.dispose()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
