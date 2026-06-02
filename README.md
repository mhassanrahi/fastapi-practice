# FastAPI Practice

A social media-style REST API built with FastAPI, featuring user authentication and media post management.

## Features

- **User auth** — registration, JWT login, email verification, password reset via `fastapi-users`
- **Upload posts** — accepts images (≤ 2 MB) and videos (≤ 20 MB), stored via ImageKit
- **Feed** — paginated list of all posts with ownership info
- **Delete posts** — owners can delete their own posts

## Tech Stack

- **FastAPI** + **Uvicorn**
- **SQLAlchemy** (async) + **SQLite** (`aiosqlite`)
- **fastapi-users** for auth
- **ImageKit** for media storage
- **uv** for dependency management

## Setup

1. **Clone and install dependencies**

   ```bash
   uv sync
   ```

2. **Configure environment** — create a `.env` file:

   ```env
   JWT_SECRET=your-secret-key
   IMAGEKIT_PRIVATE_KEY=your-imagekit-private-key
   IMAGEKIT_PUBLIC_KEY=your-imagekit-public-key
   IMAGEKIT_URL_ENDPOINT=https://ik.imagekit.io/your-id
   DATABASE_URL=sqlite+aiosqlite:///./test.db   # optional, defaults to this
   ```

3. **Run**

   ```bash
   python main.py
   ```

   API available at `http://localhost:8000`. Interactive docs at `/docs`.

## API Overview

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/auth/register` | — | Register a new user |
| `POST` | `/auth/jwt/login` | — | Login, returns JWT |
| `POST` | `/upload` | Required | Upload image or video post |
| `GET` | `/feed` | Required | Get all posts |
| `DELETE` | `/posts/{id}` | Required | Delete own post |
