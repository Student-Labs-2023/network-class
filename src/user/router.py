from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, insert, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from src.database import get_async_session
from src.error_codes import ERROR_CODE_CONFLICT_CREATE, ERROR_CODE_NOT_FOUND
from src.models import User, UserChannelSetting, Role, UserChannels
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

    if channel is None:
        raise HTTPException(status_code=ERROR_CODE_CONFLICT_CREATE, detail="Такой пользователь уже существует")

    query = insert(User).values(**data.dict()).returning(User)
    query_result = await session.execute(query)
    await session.commit()

    return query_result.scalars().unique().first()


@router.put("/{user_id}")
async def update_user(user_id: int, data: dict, session: AsyncSession = Depends(get_async_session)):
    query = select(User).where(User.id == user_id)
    result = await session.execute(query)
    user = result.first()

    if user is None:
        raise HTTPException(status_code=ERROR_CODE_NOT_FOUND, detail="Пользователь не найден")

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

    if user is None:
        raise HTTPException(status_code=ERROR_CODE_NOT_FOUND, detail="Пользователь не найден")

    return user[0].as_dict()


@router.get("/setting_user_channel/{email}")
async def get_info_setting_user_channel(email: str, channel_id: int,
                                        session: AsyncSession = Depends(get_async_session)):
    query = select(User).where(User.email == email)
    result = await session.execute(query)
    user_info = result.scalars().first()

    if user_info is None:
        raise HTTPException(status_code=ERROR_CODE_NOT_FOUND, detail="Пользователь не найден")

    query = select(Role).join(UserChannels, Role.id == UserChannels.role_id).filter(
        and_(UserChannels.channel_id == channel_id,
             UserChannels.user_id == user_info.id))
    result = await session.execute(query)
    role_info = result.scalars().first()

    query = select(UserChannelSetting).where(and_(UserChannelSetting.user_id == user_info.id,
                                                  UserChannelSetting.channel_id == channel_id))
    result = await session.execute(query)
    user_setting_info = result.scalars().first()

    if user_setting_info is None:
        raise HTTPException(status_code=ERROR_CODE_NOT_FOUND, detail="Класс не найден")

    return {
        **user_info.as_dict(),
        "name_channel": user_setting_info.name,
        "role": role_info.name
    }


@router.put("/{email}/{channel_id}")
async def change_name(email: str, channel_id: int, data: dict, session: AsyncSession = Depends(get_async_session)):
    query = select(User).where(User.email == email)
    result = await session.execute(query)
    user = result.first()

    if user is None:
        raise HTTPException(status_code=ERROR_CODE_NOT_FOUND, detail="Пользователь не найден")

    user = user[0]

    query = select(UserChannelSetting).where(
        and_(UserChannelSetting.user_id == user.id, UserChannelSetting.channel_id == channel_id))
    result = await session.execute(query)
    user_channel_setting = result.scalars().first()

    if user_channel_setting is None:
        raise HTTPException(status_code=ERROR_CODE_NOT_FOUND, detail="Настройки пользователя не найдены")

    if data.get("name") is not None:
        user_channel_setting.name = data.get("name")
    await session.commit()

    return {"message": "Имя пользователя изменено"}
