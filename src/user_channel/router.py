from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select, insert, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.channel.schemas import ChannelResponse, ChannelPost, ChannelDelete
from src.models import Channels, UserChannels, Role, User
from src.database import get_async_session

router = APIRouter(
    prefix="/users"
)
@router.get("/{user_id}/channels/" , response_model=list[ChannelResponse])
async def get_user_channels(user_id: int, session: AsyncSession = Depends(get_async_session)):
    query = select(User).where(UserChannels.id == user_id)
    result = await session.execute(query)
    user_info = result.first()

    if user_info:
        raise HTTPException(status_code=400, detail="Такого пользователя не существует")

    query = select(UserChannels).where(UserChannels.user_id == user_id)
    result = await session.execute(query)
    user_channels = result.fetchall()

    response_list = []

    for channel in user_channels:
        query = select(Channels).where(Channels.id == user_channels[0].channel_id)
        result = await session.execute(query)
        channels = result.first()

        channels_dict = channels.as_dict()

        channels_dict["owner_fullname"] = user_info[0].full_name
        channels_dict["owner_email"] = user_info[0].email

        response_list.append(channels_dict)

    return response_list