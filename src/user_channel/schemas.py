from pydantic import BaseModel

class UserResponse(BaseModel):
    full_name: str
    photo_url: str
    email: str
