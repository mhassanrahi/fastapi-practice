from collections.abc import AsyncGenerator
import os
import uuid

from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy import Column, String, DateTime, ForeignKey, UUID
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from datetime import datetime, timezone
from fastapi_users.db import SQLAlchemyUserDatabase, SQLAlchemyBaseUserTableUUID
from fastapi_users_db_sqlalchemy.generics import GUID
from fastapi import Depends

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./test.db")


class Base(DeclarativeBase):
    pass


class User(SQLAlchemyBaseUserTableUUID, Base):
    posts = relationship(
        "Post",
        back_populates="user",
        lazy="selectin",
        cascade="all, delete-orphan"
    )


class Post(Base):
    __tablename__ = "posts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    caption = Column(String(500), nullable=False)
    url = Column(String(2048), nullable=False)
    file_type = Column(String(100), nullable=False)
    file_name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    user_id = Column(GUID, ForeignKey("user.id"), nullable=False)

    user = relationship("User", back_populates="posts", lazy="selectin")


engine = create_async_engine(DATABASE_URL)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User)
