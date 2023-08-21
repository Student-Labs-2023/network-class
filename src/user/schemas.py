from pydantic import BaseModel


class UserCreate(BaseModel):
    full_name: str
    photo_url: str
    email: str


class UserResponse(BaseModel):
    full_name: str
    photo_url: str
    email: str
