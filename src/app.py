import asyncio
import uuid

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from .db import create_db_and_tables, get_async_session, Post, User
from .images import imagekit

from .users import auth_backend, current_active_user, fastapi_users
from .schemas import UserCreate, UserRead, UserUpdate


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)

app.include_router(fastapi_users.get_auth_router(
    auth_backend), prefix='/auth/jwt', tags=["auth"])
app.include_router(fastapi_users.get_register_router(
    UserRead, UserCreate), prefix="/auth", tags=["auth"])
app.include_router(fastapi_users.get_reset_password_router(),
                   prefix="/auth", tags=["auth"])
app.include_router(fastapi_users.get_verify_router(
    UserRead), prefix="/auth", tags=["auth"])
app.include_router(fastapi_users.get_users_router(
    UserRead, UserUpdate), prefix="/users", tags=["users"])


@app.post("/upload")
async def upload_file(
        file: UploadFile = File(...),
        caption: str = Form(...),
        user: User = Depends(current_active_user),
        session: AsyncSession = Depends(get_async_session)
):
    MAX_IMAGE_SIZE = 2 * 1024 * 1024   # 2 MB
    MAX_VIDEO_SIZE = 20 * 1024 * 1024  # 20 MB

    content_type = file.content_type or ""
    if content_type.startswith("image/"):
        file_type = "photo"
        max_size = MAX_IMAGE_SIZE
    elif content_type.startswith("video/"):
        file_type = "video"
        max_size = MAX_VIDEO_SIZE
    else:
        raise HTTPException(
            status_code=400, detail="Only image and video files are supported")

    # Read one byte beyond the limit so we can detect oversized files
    # without loading the entire file into memory first.
    file_bytes = await file.read(max_size + 1)
    if len(file_bytes) > max_size:
        limit_mb = max_size // (1024 * 1024)
        raise HTTPException(
            status_code=413,
            detail=f"{file_type.capitalize()} files must be under {limit_mb} MB"
        )

    file_name = file.filename or "upload"
    # generate unique file name to avoid conflicts
    file_name_unique = f"{uuid.uuid4()}_{file_name}"

    loop = asyncio.get_running_loop()
    try:
        upload_response = await loop.run_in_executor(
            None,
            lambda: imagekit.files.upload(
                file=file_bytes,
                file_name=file_name_unique,
                folder="/posts",
            )
        )
    except Exception as e:
        raise HTTPException(
            status_code=502, detail=f"ImageKit upload failed: {e}")

    post = Post(
        caption=caption,
        url=upload_response.url,
        file_type=file_type,
        file_name=file_name_unique,
        user_id=user.id
    )

    session.add(post)
    await session.commit()
    await session.refresh(post)

    return {
        "id": str(post.id),
        "caption": post.caption,
        "url": post.url,
        "file_type": post.file_type,
        "file_name": post.file_name,
        "created_at": post.created_at.isoformat(),
    }


@app.get("/feed")
async def get_feed(
        session: AsyncSession = Depends(get_async_session),
        user: User = Depends(current_active_user)
):
    result = await session.execute(
        select(Post).options(selectinload(Post.user)
                             ).order_by(Post.created_at.desc())
    )
    posts = result.scalars().all()

    posts_data = []
    for post in posts:
        post_data = {
            "id": str(post.id),
            "caption": post.caption,
            "url": post.url,
            "file_type": post.file_type,
            "file_name": post.file_name,
            "created_at": post.created_at.isoformat(),
            "user_id": str(post.user_id),
            "is_owner": post.user_id == user.id,
            "email": post.user.email if post.user else None
        }
        posts_data.append(post_data)
    return posts_data


@app.delete("/posts/{id}")
async def delete_post(
    id: str,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user)
):
    post_id = uuid.UUID(id)
    result = await session.execute(
        select(Post).where(Post.id == post_id)
    )

    post = result.scalar_one_or_none()

    if post is None:
        raise HTTPException(
            status_code=403,
            detail="Post not found"
        )

    if post.user_id != user.id:
        raise HTTPException(
            status_code=404,
            detail="You don't have permission to delete this post."
        )

    await session.delete(post)
    await session.commit()

    return {
        "success": True,
        "message": "Post deleted successfully."
    }
