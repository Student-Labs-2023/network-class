from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, insert, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from src.database import get_async_session
from src.models import User, UserChannelSetting
from src.user.schemas import UserCreate, UserResponse

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


@router.post("/")
async def create_user(data: UserCreate, session: AsyncSession = Depends(get_async_session)):
    query = select(User).where(User.email == data.email)
    result = await session.execute(query)
    channel = result.first()

    if channel:
        raise HTTPException(status_code=400, detail="Такой пользователь уже существует")

    query = insert(User).values(**data.dict()).returning(User)
    query_result = await session.execute(query)
    await session.commit()

    return query_result.scalars().unique().first()


@router.put("/{user_id}")
async def update_user(user_id: int, data: dict, session: AsyncSession = Depends(get_async_session)):
    query = select(User).where(User.id == user_id)
    result = await session.execute(query)
    user = result.first()

    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    user_info = user[0]

    if data.get("full_name"):
        user_info.full_name = data.get("full_name")
    if data.get("photo_url") is not None:
        user_info.photo_url = data.get("photo_url")

    await session.commit()

    return {"message": "Информация о пользователе обновлена"}

@router.get("/{email}")
async def get_user(email: str, session: AsyncSession = Depends(get_async_session)):
    query = select(User).where(User.email == email)
    result = await session.execute(query)
    user = result.first()

    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    return user[0].as_dict()

@router.put("/{email}/{channel_id}")
async def change_name(email: str, channel_id: int, data: dict, session: AsyncSession = Depends(get_async_session)):
    query = select(User).where(User.email == email)
    result = await session.execute(query)
    user = result.first()

    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    user = user[0]

    query = select(UserChannelSetting).where(and_(UserChannelSetting.user_id == user.id, UserChannelSetting.channel_id == channel_id))
    result = await session.execute(query)
    user_channel_setting = result.scalars().first()

    if user_channel_setting is None:
        raise HTTPException(status_code=404, detail="Настройки пользователя не найдены")

    if data.get("name") is not None:
        user_channel_setting.name = data.get("name")
    await session.commit()

    return {"message": "Имя пользователя изменено"}
