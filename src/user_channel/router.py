from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select, insert, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.channel.schemas import ChannelResponse, ChannelPost, ChannelDelete
from src.models import Channels, UserChannels, Role, User
from src.database import get_async_session

router = APIRouter(
    prefix="/users"
)
@router.get("/users/{user_id}/channels/" , response_model=list[Channels])
async def get_user_channels(user_id: int, session: AsyncSession = Depends(get_async_session)):
    user_channels = select(UserChannels).where(UserChannels.user_id == user_id)
    channels = select(Channels).where(Channels.id == user_channels)
    return channels

