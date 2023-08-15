from typing import Optional

from pydantic import BaseModel
from pydantic.v1.main import ModelMetaclass


class AllOptional(ModelMetaclass):
    def __new__(self, name, bases, namespaces, **kwargs):
        annotations = namespaces.get('__annotations__', {})
        for base in bases:
            annotations.update(base.__annotations__)
        for field in annotations:
            if not field.startswith('__'):
                annotations[field] = Optional[annotations[field]]
        namespaces['__annotations__'] = annotations
        return super().__new__(self, name, bases, namespaces, **kwargs)


class ChannelResponse(BaseModel):
    id: int
    title: str
    url: str
    photo_url: str
    isActive: bool
    owner_fullname: str
    isPublic: bool
    owner_email: str


class ChannelPost(BaseModel):
    title: str
    url: str
    photo_url: str
    isActive: bool = True
    isPublic: bool = True
    owner_email: str


class ChannelDelete(BaseModel):
    user_email: str


class UserChannel(BaseModel):
    user_id: int
    channel_id: int
    role_id: int
