from fastapi import FastAPI, HTTPException

from .schemas import PostCreate, PostCreateResponse, Post
from .data import text_posts
from .db import create_db_and_tables, get_async_session
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)



