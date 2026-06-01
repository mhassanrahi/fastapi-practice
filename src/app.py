from fastapi import FastAPI, HTTPException

from .schemas import PostCreate, PostCreateResponse, Post
from .data import text_posts

app = FastAPI()



@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

@app.post("/posts")
def create_post(post: PostCreate) -> PostCreateResponse:
    id = max(text_posts.keys()) + 1 if text_posts else 1
    text_posts[id] = {"title": post.title, "content": post.content}
    return PostCreateResponse(message="Post created successfully.", post=Post(id=id, title=post.title, content=post.content))

# Get All posts
@app.get("/posts")
def get_all_posts(limit: int = None) -> list[Post]:
    if limit is not None:
        return list(text_posts.values())[:limit]
    return [Post(id=id, title=post["title"], content=post["content"]) for id, post in text_posts.items()]

# Get a specific post by ID
@app.get("/posts/{id}")
def get_post(id: int) -> Post:
    post = text_posts.get(id)
    if post:
        return Post(id=id, title=post["title"], content=post["content"])
    else:
        raise HTTPException(status_code=404, detail="Post not found")

# Update a post by ID,
@app.put("/posts/{id}")
def update_post(id: int, title: str = None, content: str = None) -> Post:
    post = text_posts.get(id)
    if post:
        if title:
            post["title"] = title
        if content:
            post["content"] = content
        return Post(id=id, title=post["title"], content=post["content"])
    else:
        raise HTTPException(status_code=404, detail="Post not found")

# Delete a post by ID
@app.delete("/posts/{id}")
def delete_post(id: int) -> dict:
    if id in text_posts:
        del text_posts[id]
        return {"message": f"Post {id} deleted successfully."}
    else:
        raise HTTPException(status_code=404, detail="Post not found")