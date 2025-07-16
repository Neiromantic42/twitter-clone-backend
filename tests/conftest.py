import sys
import os
import pytest_asyncio
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)

from app.main import app
from app.database import get_session

# учебная база с нужными таблицами и данными
# #для раболты тестов внутри контейнера строка подключения к бд
# DATABASE_URL = "postgresql+asyncpg://admin:admin@db:5432/admin"
DATABASE_URL = "postgresql+asyncpg://admin:admin@localhost:5432/admin"
# Создаём асинхронный движок SQLAlchemy
test_engine = create_async_engine(
    DATABASE_URL,
    echo=True,
)
# Создаём фабрику асинхронных сессий
TestSessionLocal = async_sessionmaker(
    test_engine,
    expire_on_commit=False
)

async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        yield session

# Подменяем оригинальную сессию на тестовую
app.dependency_overrides[get_session] = override_get_session

# Создаем фикстуру клиента (эмуляция работы браузера)
@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
