from typing import List

import aiohttp
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select, insert, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.channel.schemas import ChannelResponse, ChannelPost, ChannelDelete
from src.models import Channels, UserChannels, Role, User, ChannelToken, ChannelSetting, UserChannelSetting
from src.database import get_async_session

router = APIRouter(
    prefix="/channels",
    tags=["Health"]
)


@router.get("/", response_model=List[ChannelResponse])
async def get_channels(page: int = 1, page_size: int = 10, session: AsyncSession = Depends(get_async_session)):
    if not is_user_authorized():
        raise HTTPException(status_code=401, detail="Пользователь не авторизован")

    start_index = (page - 1) * page_size
    end_index = start_index + page_size

    query = select(Channels).filter().slice(start_index, end_index)
    result = await session.execute(query)
    channels = result.fetchall()

    response_list = []
    for channel in channels:
        query = select(UserChannels).where(UserChannels.channel_id == channel[0].id)
        result = await session.execute(query)
        user_id = result.fetchone()

        query = select(User).where(User.id == user_id[0].user_id)
        result = await session.execute(query)
        user_info = result.fetchone()

        channel_dict = channel[0].as_dict()
        channel_dict["owner_email"] = user_info[0].email
        channel_dict["owner_fullname"] = user_info[0].full_name

        response_list.append(channel_dict)

    return response_list


@router.post("/")
async def create_channel(data: ChannelPost, session: AsyncSession = Depends(get_async_session)):
    if not is_user_authorized():
        raise HTTPException(status_code=401, detail="Пользователь не авторизован")

    if not data.title or not data.owner_email:
        raise HTTPException(status_code=403, detail="Неверный фильтр")

    query = select(Channels).where(Channels.title == data.title)
    result = await session.execute(query)
    channel = result.first()

    if channel:
        raise HTTPException(status_code=400, detail="Канал с таким именем уже существует")

    query_channel = insert(Channels).values(title=data.title, url=data.url, photo_url=data.photo_url,
                                            isActive=data.isActive, isPublic=data.isActive).returning(Channels)
    result_channel = await session.execute(query_channel)

    query = select(Role).where(Role.name == "owner")
    result = await session.execute(query)
    role = result.first()

    query = select(User).where(User.email == data.owner_email)
    result = await session.execute(query)
    user = result.first()

    channel_id = result_channel.scalars().unique().first().id

    query = insert(UserChannels).values({
        "user_id": user[0].id,
        "channel_id": channel_id,
        "role_id": int(role[0].id)
    })
    await session.execute(query)

    async with aiohttp.ClientSession() as session_request:
        react_app_auth_url = "https://network-class-server.ru/videosdk"
        url_get_token = f"{react_app_auth_url}/get-token"
        url_create_meeting = f"{react_app_auth_url}/create-meeting"
        async with session_request.get(url_get_token) as resp:
            response = await resp.json()
            token = response.get("token")
        async with session_request.post(url_create_meeting, data={
            "token": token
        }) as resp:
            response = await resp.json()
            meeting_id = response.get("meetingId")
            url_validate_meeting = f"{react_app_auth_url}/validate-meeting/{meeting_id}"
        async with session_request.post(url_validate_meeting, data={
            "token": token
        }) as resp:
            response = await resp.json()
            if response.get("disabled"):
                raise HTTPException(status_code=400, detail="Произошла ошибка при создании meeting_id")

    query = insert(ChannelToken).values(id=channel_id, token=meeting_id)
    await session.execute(query)

    query = insert(ChannelSetting).values(id=channel_id)
    await session.execute(query)

    query = insert(UserChannelSetting).values(user_id=user[0].id, channel_id=channel_id, name=user[0].full_name)
    await session.execute(query)

    await session.commit()

    return {"message": "Канал успешно создан"}


@router.delete("/{channel_id}")
async def delete_channel(channel_id: int, data: ChannelDelete, session: AsyncSession = Depends(get_async_session)):
    if not is_user_authorized():
        raise HTTPException(status_code=401, detail="Пользователь не авторизован")

    if not channel_id or not data.user_email:
        raise HTTPException(status_code=403, detail="Неверный фильтр")

    query = select(UserChannels).where(and_(UserChannels.channel_id == channel_id, UserChannels.role_id == 1))
    result = await session.execute(query)
    channel_permission_user = result.first()

    if channel_permission_user is None:
        raise HTTPException(status_code=404, detail="Данного класса не существует")

    query = select(User).where(User.email == data.user_email)
    result = await session.execute(query)
    user_info = result.first()

    if user_info is None:
        raise HTTPException(status_code=404, detail="Данного пользователя не существует")

    if channel_permission_user[0].user_id == user_info[0].id:
        query = delete(Channels).where(Channels.id == channel_id)
        await session.execute(query)

        query = delete(ChannelToken).where(ChannelToken.id == channel_id)
        await session.execute(query)

        query = delete(UserChannels).where(UserChannels.channel_id == channel_id)
        await session.execute(query)

        query = delete(ChannelSetting).where(ChannelSetting.id == channel_id)
        await session.execute(query)

        await session.commit()
    else:
        raise HTTPException(status_code=403, detail="Недостаточно прав")

    return {"message": f"Канал успешно удалён"}


def is_user_authorized():
    return True


@router.get("/{channel_id}")
async def get_user_channels(channel_id: int, session: AsyncSession = Depends(get_async_session)):
    if not is_user_authorized():
        raise HTTPException(status_code=401, detail="Пользователь не авторизован")

    query = select(Channels).where(Channels.id == channel_id)
    result = await session.execute(query)
    channel = result.first()

    return channel[0].as_dict()


@router.put("/{channel_id}")
async def update_channel(channel_id: int, data: dict, session: AsyncSession = Depends(get_async_session)):
    if not is_user_authorized():
        raise HTTPException(status_code=401, detail="Пользователь не авторизован")

    query = select(Channels).where(Channels.id == channel_id)
    result = await session.execute(query)
    channel = result.first()

    if not channel:
        raise HTTPException(status_code=404, detail="Канал не найден")

    channel = channel[0]

    if data.get("user_email") is not None:
        user_email = data.get("user_email")
    else:
        raise HTTPException(status_code=404, detail="Не указан Email пользователя")

    query = select(UserChannels).where(and_(UserChannels.channel_id == channel_id, UserChannels.role_id == 1))
    result = await session.execute(query)
    channel_permission_user = result.first()

    query = select(User).where(User.email == user_email)
    result = await session.execute(query)
    user_info = result.first()

    if channel_permission_user[0].user_id == user_info[0].id:
        if data.get("title") is not None:
            channel.title = data.get("title")
        if data.get("url") is not None:
            channel.url = data.get("url")
        if data.get("photo_url") is not None:
            channel.photo_url = data.get("photo_url")
        if data.get("isActive") is not None:
            channel.isActive = data.get("isActive")
        if data.get("isPublic") is not None:
            channel.isPublic = data.get("isPublic")
        await session.commit()

        return {"message": "Информация о канале обновлена"}
    else:
        raise HTTPException(status_code=403, detail="Недостаточно прав")
