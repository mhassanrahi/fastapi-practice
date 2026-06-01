import asyncio
import uuid

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager
from sqlalchemy import select

from .db import create_db_and_tables, get_async_session, Post
from .images import imagekit


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)


@app.post("/upload")
async def upload_file(
        file: UploadFile = File(...),
        caption: str = Form(...),
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
        session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(select(Post).order_by(Post.created_at.desc()))
    posts = [row[0] for row in result.all()]

    posts_data = []
    for post in posts:
        post_data = {
            "id": str(post.id),
            "caption": post.caption,
            "url": post.url,
            "file_type": post.file_type,
            "file_name": post.file_name,
            "created_at": post.created_at.isoformat()
        }
        posts_data.append(post_data)
    return posts_data


@app.delete("/posts/{id}")
async def delete_post(
    id: str,
    session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(
        select(Post).where(Post.id == id)
    )

    post = result.scalar_one_or_none()

    if post is None:
        raise HTTPException(
            status_code=404,
            detail="Post not found"
        )

    await session.delete(post)
    await session.commit()

    return {
        "success": True,
        "message": "Post deleted successfully."
    }
