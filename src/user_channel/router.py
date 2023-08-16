from typing import List

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select, insert, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.user_channel.schemas import UserResponse
from src.channel.schemas import ChannelResponse
from src.models import Channels, UserChannels, Role, User, UserChannelSetting
from src.database import get_async_session

router = APIRouter(
    prefix="/user_channels",
    tags=["UserChannels"]
)


@router.get("/{channel_id}/users/", response_model=List[UserResponse])
async def get_channel_users(channel_id: int, session: AsyncSession = Depends(get_async_session)):
    query = select(UserChannels).where(UserChannels.channel_id == channel_id)
    result = await session.execute(query)
    user_channels = result.fetchall()

    if len(user_channels) == 0:
        raise HTTPException(status_code=404, detail="Пользователи не найдены")

    response_list = []

    for user in user_channels:
        query = select(User).where(User.id == user[0].user_id)
        result = await session.execute(query)
        user_info = result.scalars().first()

        if user_info is not None:

            query = select(UserChannelSetting).where(UserChannelSetting.user_id == user_info.id)
            result = await session.execute(query)
            user_setting = result.scalars().first()

            query = (select(Role)
                     .join(UserChannels, Role.id == UserChannels.role_id)
                     .filter(UserChannels.user_id == user_info.id)
                     )
            result = await session.execute(query)
            role_info = result.scalars().first()

            users_dict = {
                **user_info.as_dict(),
                "name_channel": user_setting.name,
                "role": role_info.name
            }
            response_list.append(users_dict)

    return response_list


@router.get("/my/{user_id}/", response_model=List[ChannelResponse])
async def get_channel_users(user_id: int, session: AsyncSession = Depends(get_async_session)):
    query = select(User).where(User.id == user_id)
    result = await session.execute(query)
    user_info = result.fetchone()

    if user_info is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    query = select(UserChannels).where(UserChannels.user_id == user_id)
    result = await session.execute(query)
    user_channels = result.fetchall()

    response_list = []

    for user_channel in user_channels:
        query = select(Channels).where(Channels.id == user_channel[0].channel_id)
        result = await session.execute(query)
        channel = result.first()

        channel_dict = channel[0].as_dict()
        channel_dict["owner_email"] = user_info[0].email
        channel_dict["owner_fullname"] = user_info[0].full_name

        response_list.append(channel_dict)

    return response_list


@router.post("/connect")
async def append_user_channel(email: str, channel_id: int, name: str, session: AsyncSession = Depends(get_async_session)):
    query = select(User).where(User.email == email)
    result = await session.execute(query)
    user_info = result.first()

    if user_info is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    query = select(UserChannels).where(
        and_(UserChannels.user_id == user_info[0].id, UserChannels.channel_id == channel_id))
    result = await session.execute(query)
    channel_info = result.first()

    if channel_info is not None:
        raise HTTPException(status_code=500, detail="Пользователь уже подключён")

    query = insert(UserChannels).values(user_id=user_info[0].id, channel_id=channel_id, role_id=2)
    await session.execute(query)

    query = insert(UserChannelSetting).values(user_id=user_info[0].id, channel_id=channel_id, name=name)
    await session.execute(query)
    await session.commit()

    return {"message": "Пользователь добавлен"}


@router.delete("/disconnect")
async def delete_user(user_id: int, channel_id: int, session: AsyncSession = Depends(get_async_session)):
    query = select(User).where(User.id == user_id)
    result = await session.execute(query)
    user_info = result.first()

    if user_info is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    query = delete(UserChannels).where(and_(UserChannels.user_id == user_id, UserChannels.channel_id == channel_id))
    await session.execute(query)
    await session.commit()

    return {"message": "Пользователь удалён"}
