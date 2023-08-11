from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_async_session
from src.models import User
from src.user.schemas import UserCreate

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


@router.post("/")
async def create_user(data: UserCreate, session: AsyncSession = Depends(get_async_session)):

    query = select(User).where(User.email == data.email)
    result = await session.execute(query)
    channel = result.first()

    if channel:
        raise HTTPException(status_code=400, detail="Такой пользователь уже существует")

    query = insert(User).values(**data.dict()).returning(User)
    query_result = await session.execute(query)
    await session.commit()

    return query_result.scalars().unique().first()

@router.put("/{user_id}")
async def update_user(user_id: int, data: dict, session: AsyncSession = Depends(get_async_session)):

    query = select(User).where(User.id == user_id)
    result = await session.execute(query)
    user = result.first()[0]

    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    if data.get("full_name"):
        user.full_name = data.get("full_name")
    if data.get("photo_url") is not None:
        user.photo_url = data.get("photo_url")

    await session.commit()

    return {"message": "Информация о пользователе обновлена"}


