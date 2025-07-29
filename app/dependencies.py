import asyncio
import logging

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import AsyncSession, get_session
from app.models import Follows, Users

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


async def get_current_user(
    request: Request, session: AsyncSession = Depends(get_session)
) -> Users:
    """Depends - метод для получения текущего пользователя и проверки валидности api_key"""
    logger.info(f"get_current_user loop: {asyncio.get_running_loop()}")
    api_key = request.headers.get("api-key")
    # Проверяем есть ли хедер api_key в запросе клиента
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="API key is missing"
        )
    logger.info(f"api_key: {api_key}")
    # Проверяем зарегистрирован ли такой юзер в бд
    async with session.begin():
        result = await session.execute(
            select(Users)
            .options(
                selectinload(Users.followers).joinedload(Follows.follower),
                selectinload(Users.following).joinedload(Follows.followed),
            )
            .where(Users.api_key == api_key)
        )
        user = result.scalars().first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Invalid API key"
            )

        logger.info(f"user: {user.id}, {user.name}, {user.api_key}")
    return user
