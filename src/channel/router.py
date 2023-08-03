from typing import List

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select, insert, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.channel.schemas import ChannelResponse, ChannelPost, ChannelDelete
from src.models import Channels
from src.database import get_async_session

router = APIRouter(
    prefix="/channels",
    tags=["Health"]
)


@router.get("/", response_model=List[ChannelResponse])
async def get_channels(page: int = 1, page_size: int = 10, session: AsyncSession = Depends(get_async_session)):
    if not is_user_authorized():
        raise HTTPException(status_code=401, detail="Пользователь не авторизован")

    # filters = []

    # if access is not None:
    #     filters.append(Channels.access == access)

    start_index = (page - 1) * page_size
    end_index = start_index + page_size

    query = select(Channels).filter().slice(start_index, end_index)
    result = await session.execute(query)
    channels = result.fetchall()

    # filtered_channels = Channels.query.filter(*filters).slice().all()

    return [channel[0].as_dict() for channel in channels]


@router.post("/")
async def create_channel(data: ChannelPost, session: AsyncSession = Depends(get_async_session)):
    if not is_user_authorized():
        raise HTTPException(status_code=401, detail="Пользователь не авторизован")

    if not data.title or not data.owner:
        raise HTTPException(status_code=403, detail="Неверный фильтр")

    query = select(Channels).where(Channels.title == data.title)
    result = await session.execute(query)
    channel = result.first()

    if channel:
        raise HTTPException(status_code=400, detail="Канал с таким именем уже существует")

    query = insert(Channels).values(**data.dict())
    await session.execute(query)
    await session.commit()

    # user_channel = UserChannels(user_id=owner_id, channel_id=channel.id, role_id=1)
    # session.add(user_channel)
    # session.commit()

    return {"message": "Канал успешно создан"}


@router.delete("/")
async def delete_channel(data: ChannelDelete, session: AsyncSession = Depends(get_async_session)):
    if not is_user_authorized():
        raise HTTPException(status_code=401, detail="Пользователь не авторизован")

    if not data.id:
        raise HTTPException(status_code=403, detail="Неверный фильтр")

    query = delete(Channels).where(Channels.id == data.id)
    await session.execute(query)
    await session.commit()


    # deleted_count_channels = Channels.query.filter_by(id=channel_id).delete()
    # UserChannels.query.filter_by(channel_id=channel_id).delete()
    # session.commit()

    return {"message": f"Канал успешно удалён"}


def is_user_authorized():
    return True


@router.get("/{channel_id}")
async def get_user_channels(channel_id: int, session: AsyncSession = Depends(get_async_session)):

    query = select(Channels).where(Channels.id == channel_id)
    result = await session.execute(query)
    channel = result.first()

    if not is_user_authorized():
        raise HTTPException(status_code=401, detail="Пользователь не авторизован")

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
    if data.get("owner") is not None:
        channel.owner = data.get("owner")
    if data.get("isPublic") is not None:
        channel.isPublic = data.get("isPublic")

    await session.commit()

    return {"message": "Информация о канале обновлена"}
