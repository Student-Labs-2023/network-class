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

    query = insert(User).values(**data.dict())
    await session.execute(query)
    await session.commit()

    return {"message": "Пользователь создан"}


