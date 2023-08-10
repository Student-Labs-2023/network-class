from typing import List

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select, insert, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.channel.schemas import ChannelResponse, ChannelPost, ChannelDelete
from src.models import Channels, UserChannels, Role, User
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
    await session.commit()

    query = select(Role).where(Role.name == "owner")
    result = await session.execute(query)
    role = result.first()

    query = select(User).where(User.email == data.owner_email)
    result = await session.execute(query)
    user = result.first()

    query = insert(UserChannels).values({
        "user_id": user[0].id,
        "channel_id": result_channel.scalars().unique().first().id,
        "role_id": int(role[0].id)
    })
    await session.execute(query)
    await session.commit()

    return {"message": "Канал успешно создан"}


@router.delete("/")
async def delete_channel(data: ChannelDelete, session: AsyncSession = Depends(get_async_session)):
    if not is_user_authorized():
        raise HTTPException(status_code=401, detail="Пользователь не авторизован")

    if not data.channel_id or not data.user_id:
        raise HTTPException(status_code=403, detail="Неверный фильтр")

    query = select(UserChannels).where(and_(UserChannels.channel_id == data.channel_id, UserChannels.role_id == 1))
    result = await session.execute(query)
    channel_permission_user = result.first()

    if channel_permission_user is None:
        raise HTTPException(status_code=404, detail="Данного класса не существует")

    if channel_permission_user[0].user_id == data.user_id:
        query = delete(Channels).where(Channels.id == data.id)
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
    channel = result.first()[0]

    if not channel:
        raise HTTPException(status_code=404, detail="Канал не найден")

    if data.get("title"):
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
