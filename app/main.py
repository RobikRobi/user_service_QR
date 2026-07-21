import logging
from binascii import Error

from fastapi import FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api_response import error_response, success_response
from app.config import config
from app.db import Base, engine
from app.routers.auth_router import router as auth_router
from app.routers.group_router import router as group_router
from app.routers.user_router import router as user_router


logger = logging.getLogger(__name__)


app = FastAPI(
    title="User service",
    version="1.0.0",
    root_path="/users"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.env_data.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(group_router)
app.include_router(user_router)


@app.exception_handler(HTTPException)
async def http_exception_handler(_request: Request, exc: HTTPException):
    detail = exc.detail
    message = detail if isinstance(detail, str) else "HTTP error"

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(exc.status_code, message),
        headers=exc.headers,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content=error_response(
            422,
            "Validation error",
            details=jsonable_encoder(exc.errors()),
        ),
    )


@app.get("/init")
async def create_db():
    async with engine.begin() as conn:
        try:
            await conn.run_sync(Base.metadata.drop_all)
        except Error:
            logger.exception("Failed to drop database tables")
        await conn.run_sync(Base.metadata.create_all)
    return success_response("Database initialized")
