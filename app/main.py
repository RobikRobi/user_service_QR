from binascii import Error

from fastapi import FastAPI

from app.db import Base, engine
from app.routers.auth_router import router as auth_router
from app.routers.group_router import router as group_router
from app.routers.user_router import router as user_router


app = FastAPI(
    title="User service",
    version="1.0.0",
    root_path="/users"
)

app.include_router(auth_router)
app.include_router(group_router)
app.include_router(user_router)


@app.get("/init")
async def create_db():
    async with engine.begin() as conn:
        try:
            await conn.run_sync(Base.metadata.drop_all)
        except Error as e:
            print(e)
        await conn.run_sync(Base.metadata.create_all)
    return {"msg": "db creat! =)"}
