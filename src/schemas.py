from pydantic import BaseModel

class Post(BaseModel):
    id: int
    title: str
    content: str


class PostCreate(BaseModel):
    title: str
    content: str

class PostUpdate(BaseModel):
    title: str = None
    content: str = None

class PostCreateResponse(BaseModel):
    message: str
    post: Post