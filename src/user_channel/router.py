from typing import List

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select, insert, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.user_channel.schemas import UserResponse
from src.models import Channels, UserChannels, Role, User
from src.database import get_async_session

router = APIRouter(
    prefix="/channels"
)
@router.get("/{channel_id}/users/" , response_model=List[UserResponse])
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
        users = result.first()

        users_dict = users[0].as_dict()

        response_list.append(users_dict)

    return response_list


