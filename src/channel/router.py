from typing import List

import aiohttp

from fastapi import APIRouter, HTTPException, Depends

from sqlalchemy import select, insert, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.channel.schemas import ChannelResponse, ChannelPost, ChannelDelete
from src.models import Channels, UserChannels, Role, User, ChannelToken, ChannelSetting, UserChannelSetting
from src.database import get_async_session
from src.error_codes import ERROR_CODE_USER_NOT_AUTHORIZED, ERROR_CODE_ACCESS_FORBIDDEN, ERROR_CODE_NOT_FOUND, \
    ERROR_CODE_ON_SERVER, ERROR_CODE_CONFLICT_CREATE, ERROR_CODE_BAD_FILTER

router = APIRouter(
    prefix="/channels",
    tags=["Channels"]
)


@router.get("/", response_model=List[ChannelResponse])
async def get_all_channels(page: int = 1, page_size: int = 10, session: AsyncSession = Depends(get_async_session)):
    # await check_auth(token) # Validation

    start_index = (page - 1) * page_size
    end_index = start_index + page_size

    query = select(Channels).filter().slice(start_index, end_index)
    result = await session.execute(query)
    channels = result.scalars().fetchall()

    response_list = []
    for channel in channels:
        query = (select(User)
                 .join(UserChannels, User.id == UserChannels.user_id)
                 .filter(and_(UserChannels.channel_id == channel.id, UserChannels.role_id == 1))
                 )
        result = await session.execute(query)
        user_info: User = result.scalars().first()
        response_list.append({
            **channel.as_dict(),
            "owner_email": "test@gmail.com" if user_info is None else user_info.email,
            "owner_fullname": "test@gmail.com" if user_info is None else user_info.full_name
        })
    return response_list


@router.post("/")
async def create_channel(data: ChannelPost, session: AsyncSession = Depends(get_async_session)):
    if not is_user_authorized():
        raise HTTPException(status_code=ERROR_CODE_USER_NOT_AUTHORIZED, detail="Пользователь не авторизован")

    query = select(Channels).where(Channels.title == data.title)
    result = await session.execute(query)
    channel = result.first()

    if channel:
        raise HTTPException(status_code=ERROR_CODE_CONFLICT_CREATE, detail="Канал с таким именем уже существует")

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
                raise HTTPException(status_code=ERROR_CODE_ON_SERVER, detail="Произошла ошибка при создании meeting_id")

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
        raise HTTPException(status_code=ERROR_CODE_USER_NOT_AUTHORIZED, detail="Пользователь не авторизован")

    if not channel_id or not data.user_email:
        raise HTTPException(status_code=ERROR_CODE_BAD_FILTER, detail="Неверный фильтр")

    query = select(UserChannels).where(and_(UserChannels.channel_id == channel_id, UserChannels.role_id == 1))
    result = await session.execute(query)
    channel_permission_user = result.first()

    if channel_permission_user is None:
        raise HTTPException(status_code=ERROR_CODE_NOT_FOUND, detail="Данного класса не существует")

    query = select(User).where(User.email == data.user_email)
    result = await session.execute(query)
    user_info = result.first()

    if user_info is None:
        raise HTTPException(status_code=ERROR_CODE_NOT_FOUND, detail="Данного пользователя не существует")

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
        raise HTTPException(status_code=ERROR_CODE_ACCESS_FORBIDDEN, detail="Недостаточно прав")

    return {"message": f"Канал успешно удалён"}


def is_user_authorized():
    return True


@router.get("/{channel_id}")
async def get_info_current_channel(channel_id: int, session: AsyncSession = Depends(get_async_session)):
    if not is_user_authorized():
        raise HTTPException(status_code=ERROR_CODE_USER_NOT_AUTHORIZED, detail="Пользователь не авторизован")

    query = select(Channels).where(Channels.id == channel_id)
    result = await session.execute(query)
    channel = result.scalars().first()

    if channel is None:
        raise HTTPException(status_code=ERROR_CODE_NOT_FOUND, detail="Указанный класс не найден")

    query = select(ChannelSetting).where(ChannelSetting.id == channel_id)
    result = await session.execute(query)
    channel_setting: ChannelSetting = result.scalars().first()

    query = select(ChannelToken).where(ChannelToken.id == channel_id)
    result = await session.execute(query)
    channel_token_info: ChannelToken = result.scalars().first()

    query = (select(User)
             .join(UserChannels, User.id == UserChannels.user_id)
             .filter(and_(UserChannels.channel_id == channel_id, UserChannels.role_id == 1))
             )
    result = await session.execute(query)
    user_info = result.scalars().first()

    return {
        **channel.as_dict(),
        "webcam_for": channel_setting.webcam_for,
        "screenshare_for": channel_setting.screenshare_for,
        "screenrecord_for": channel_setting.screenrecord_for,
        "micro_for": channel_setting.micro_for,
        "meeting_id": channel_token_info.token,
        "owner_email": user_info.email,
        "presenter_id": channel_setting.presenter_id
    }


@router.put("/setting/{channel_id}")
async def update_channel_setting(channel_id: int, email: str, data: dict,
                                 session: AsyncSession = Depends(get_async_session)):
    if not is_user_authorized():
        raise HTTPException(status_code=ERROR_CODE_USER_NOT_AUTHORIZED, detail="Пользователь не авторизован")

    query = select(ChannelSetting).where(ChannelSetting.id == channel_id)
    result = await session.execute(query)
    channel_setting = result.scalars().first()

    if not channel_setting:
        raise HTTPException(status_code=ERROR_CODE_NOT_FOUND, detail="Класс не найден")

    query = select(UserChannels).where(and_(UserChannels.channel_id == channel_id, UserChannels.role_id == 1))
    result = await session.execute(query)
    channel_permission_user = result.first()

    query = select(User).where(User.email == email)
    result = await session.execute(query)
    user_info = result.first()

    if user_info is None:
        raise HTTPException(status_code=ERROR_CODE_NOT_FOUND, detail="Пользователь не найден")

    if channel_permission_user[0].user_id == user_info[0].id:
        if data.get("webcam_for") is not None:
            channel_setting.webcam_for = data.get("webcam_for")
        if data.get("screenshare_for") is not None:
            channel_setting.screenshare_for = data.get("screenshare_for")
        if data.get("screenrecord_for") is not None:
            channel_setting.screenrecord_for = data.get("screenrecord_for")
        if data.get("micro_for") is not None:
            channel_setting.micro_for = data.get("micro_for")
        await session.commit()

        return {"message": "Настройки канала обновлены"}
    else:
        raise HTTPException(status_code=ERROR_CODE_ACCESS_FORBIDDEN, detail="Недостаточно прав")


@router.put("/{channel_id}")
async def update_channel_info(channel_id: int, data: dict, session: AsyncSession = Depends(get_async_session)):
    if not is_user_authorized():
        raise HTTPException(status_code=ERROR_CODE_USER_NOT_AUTHORIZED, detail="Пользователь не авторизован")

    query = select(Channels).where(Channels.id == channel_id)
    result = await session.execute(query)
    channel = result.scalars().first()

    if not channel:
        raise HTTPException(status_code=ERROR_CODE_NOT_FOUND, detail="Класс не найден")

    if data.get("user_email") is not None:
        user_email = data.get("user_email")
    else:
        raise HTTPException(status_code=ERROR_CODE_NOT_FOUND, detail="Не указан Email пользователя")

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
        raise HTTPException(status_code=ERROR_CODE_ACCESS_FORBIDDEN, detail="Недостаточно прав")


@router.get("/{channel_id}/{user_id}")
async def get_settings(channel_id: int, user_id: int, session: AsyncSession = Depends(get_async_session)):
    query = select(UserChannelSetting).where(
        and_(UserChannelSetting.user_id == user_id, UserChannelSetting.channel_id == channel_id))
    result = await session.execute(query)
    user_setting_channel = result.scalars().first()

    query = select(ChannelSetting).where(ChannelSetting.id == channel_id)
    result = await session.execute(query)
    channel_setting: ChannelSetting = result.scalars().first()

    query = select(UserChannels).where(and_(UserChannels.channel_id == channel_id, UserChannels.user_id == user_id))
    result = await session.execute(query)
    user_info = result.scalars().first()

    if user_info.role_id == 1:
        return {
            "user_channel_name": user_setting_channel.name,
            "webcam_for": channel_setting.webcam_for,
            "screenshare_for": channel_setting.screenshare_for,
            "screenrecord_for": channel_setting.screenrecord_for,
            "micro_for": channel_setting.micro_for,
            "presenter_id": channel_setting.presenter_id
        }
    else:
        return {
            "user_channel_name": user_setting_channel.name
        }


@router.put("/{channel_id}/presenter")
async def change_presenter(channel_id: int, email: str, data: dict, session: AsyncSession = Depends(get_async_session)):
    query = select(User).where(User.email == email)
    result = await session.execute(query)
    userx: User = result.scalar()
    query = select(ChannelSetting).where(ChannelSetting.id == channel_id)
    result = await session.execute(query)
    channel_setting: ChannelSetting = result.scalar()

    query = select(UserChannels).where(
        and_(UserChannels.channel_id == channel_id, UserChannels.user_id == userx.user_id))
    result = await session.execute(query)
    user_info: UserChannels = result.scalar()

    if user_info.role_id == 1:
        if data.get("presenter_id") is not None:
            channel_setting.presenter_id = data.get("presenter_id")
        await session.commit()
        return {
            "webcam_for": channel_setting.webcam_for,
            "screenshare_for": channel_setting.screenshare_for,
            "screenrecord_for": channel_setting.screenrecord_for,
            "micro_for": channel_setting.micro_for,
            "presenter_id": channel_setting.presenter_id
        }
    else:
        raise HTTPException(status_code=ERROR_CODE_ACCESS_FORBIDDEN,
                            detail="Переключать демонстрации может только уполномоченный пользователь")
