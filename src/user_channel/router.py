from typing import List

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select, insert, delete, and_, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.error_codes import ERROR_CODE_NOT_FOUND, ERROR_CODE_ACCESS_FORBIDDEN
from src.user_channel.schemas import UserResponse, SettingChannel
from src.channel.schemas import ChannelResponse
from src.models import Channels, UserChannels, Role, User, UserChannelSetting, ChannelSetting
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
        raise HTTPException(status_code=ERROR_CODE_NOT_FOUND, detail="Пользователи не найдены")

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


@router.get("/my/{email}/", response_model=List[ChannelResponse])
async def get_channel_users(email: str, session: AsyncSession = Depends(get_async_session)):
    query = select(User).where(User.email == email)
    result = await session.execute(query)
    user_info: User = result.scalars().first()

    if user_info is None:
        raise HTTPException(status_code=ERROR_CODE_NOT_FOUND, detail="Пользователь не найден")

    query = (select(Channels)
             .join(UserChannels, Channels.id == UserChannels.channel_id)
             .filter(and_(UserChannels.role_id == 1, UserChannels.user_id == user_info.id))
             )
    result = await session.execute(query)
    user_channels: List[Channels] = result.scalars().unique().fetchall()

    return [{
        **channel.as_dict(),
        "owner_email": user_info.email,
        "owner_fullname": user_info.full_name
    } for channel in user_channels]


@router.post("/connect")
async def append_user_channel(email: str, channel_id: int, session: AsyncSession = Depends(get_async_session)):
    query = select(User).where(User.email == email)
    result = await session.execute(query)
    user_info: User = result.scalars().first()

    if user_info is None:
        raise HTTPException(status_code=ERROR_CODE_NOT_FOUND, detail="Пользователь не найден")

    query = select(UserChannels).where(
        and_(UserChannels.user_id == user_info.id, UserChannels.channel_id == channel_id))
    result = await session.execute(query)
    channel_info = result.first()

    if channel_info is not None:
        query = (select(UserChannelSetting)
                 .where(and_(UserChannelSetting.user_id == user_info.id,
                             UserChannelSetting.channel_id == channel_id))
                 )
        result = await session.execute(query)
        user_channel_setting: UserChannelSetting = result.scalars().first()
        return {
            "name_channel": user_channel_setting.name
        }

    query = insert(UserChannels).values(user_id=user_info.id, channel_id=channel_id, role_id=2)
    await session.execute(query)

    query = (insert(UserChannelSetting)
             .values(user_id=user_info.id, channel_id=channel_id, name=user_info.full_name)
             .returning(UserChannelSetting)
             )
    result = await session.execute(query)
    user_channel_setting_created: UserChannelSetting = result.scalars().first()

    await session.commit()

    return {
        "name_channel": user_channel_setting_created.name
    }


@router.delete("/disconnect")
async def delete_user(email: str, channel_id: int, session: AsyncSession = Depends(get_async_session)):
    query = select(User).where(User.email == email)
    result = await session.execute(query)
    user_info: User = result.scalars().first()

    if user_info is None:
        raise HTTPException(status_code=ERROR_CODE_NOT_FOUND, detail="Пользователь не найден")

    query = delete(UserChannels).where(
        and_(UserChannels.user_id == user_info.user_id, UserChannels.channel_id == channel_id))
    await session.execute(query)
    await session.commit()

    return {"message": "Пользователь удалён"}


@router.get("/available/{email}")
async def get_available_channels(email: str, session: AsyncSession = Depends(get_async_session)):
    query = select(User).where(User.email == email)
    result = await session.execute(query)
    user_info: User = result.scalars().first()

    if user_info is None:
        raise HTTPException(status_code=ERROR_CODE_NOT_FOUND, detail="Пользователь не найден")

    query = (select(Channels)
             .join(UserChannels, Channels.id == UserChannels.channel_id)
             .filter(UserChannels.user_id == user_info.id)
             )
    result = await session.execute(query)
    response_list = []
    channels_list: List[Channels] = result.scalars().unique().fetchall()
    for channel in channels_list:
        query = (select(User)
                 .join(UserChannels, User.id == UserChannels.user_id)
                 .filter(and_(UserChannels.channel_id == channel.id, UserChannels.role_id == 1))
                 )
        result = await session.execute(query)
        user_channel_info: User = result.scalars().first()
        response_list.append({
            **channel.as_dict(),
            "owner_email": "test@gmail.com" if user_channel_info is None else user_channel_info.email,
            "owner_fullname": "test@gmail.com" if user_channel_info is None else user_channel_info.full_name
        })

    return response_list


@router.put("/setting/{channel_id}/{email}")
async def setting_channel_edit(channel_id: int, email: str, data: SettingChannel,
                               session: AsyncSession = Depends(get_async_session)):
    response = {
        "detail": ""
    }

    if data.user_channel_name:
        query = select(User).where(User.email == email)
        result = await session.execute(query)
        user_info: User = result.scalars().first()

        if user_info is None:
            raise HTTPException(status_code=ERROR_CODE_NOT_FOUND, detail="Пользователь не найден")

        query = (
            update(UserChannelSetting)
            .where(and_(UserChannelSetting.user_id == user_info.id, UserChannelSetting.channel_id == channel_id))
            .values(name=data.user_channel_name)  # Замените на соответствующее поле для обновления
            .returning(UserChannelSetting)
        )

        result = await session.execute(query)
        edit_setting_channel: List[UserChannelSetting] = result.scalars().unique().fetchall()
        updated_rows = len(edit_setting_channel)

        await session.commit()

        response = {
            "detail": f"Вы изменили имя у {updated_rows} количества пользователей в классе.",
            **edit_setting_channel[0].as_dict()
        }

    if data.micro_for or data.screenrecord_for or data.webcam_for or data.screenshare_for:
        query = (select(ChannelSetting)
                 .join(UserChannels, ChannelSetting.id == UserChannels.channel_id)
                 .join(User, UserChannels.user_id == User.id)
                 .filter(and_(UserChannels.channel_id == channel_id, User.email == email, UserChannels.role_id == 1))
                 )

        result = await session.execute(query)
        channel_setting: ChannelSetting = result.scalars().first()

        if channel_setting is None:
            raise HTTPException(status_code=ERROR_CODE_NOT_FOUND, detail="Класс не найден")

        if data.micro_for:
            channel_setting.micro_for = data.micro_for
        if data.webcam_for:
            channel_setting.webcam_for = data.webcam_for
        if data.screenshare_for:
            channel_setting.screenshare_for = data.screenshare_for
        if data.screenrecord_for:
            channel_setting.screenrecord_for = data.screenrecord_for

        await session.commit()

        response["detail"] += " Вы изменили настройки класса."
        response["micro_for"] = channel_setting.micro_for
        response["webcam_for"] = channel_setting.webcam_for
        response["screenshare_for"] = channel_setting.screenshare_for
        response["screenrecord_for"] = channel_setting.screenrecord_for

    response["detail"] = "Вы не передали нужных данных" if response["detail"] == "" else response["detail"]

    return response
