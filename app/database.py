import sqlalchemy
from sqlalchemy.ext.asyncio import (  # Импортируем асинхронный движок и сессию
    AsyncSession,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker  # Импортируем фабрику сессий
import logging

logging.basicConfig(level=logging.DEBUG)
logging.getLogger('sqlalchemy.engine').setLevel(logging.DEBUG)

DATABASE_URL = "postgresql+asyncpg://admin:admin@db:5432/admin"

# Создаём асинхронный движок SQLAlchemy
engine = create_async_engine(
    DATABASE_URL,
    echo=True,
)

# Создаём фабрику асинхронных сессий
async_session = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)  # type: ignore

# Создаём базовый класс для описания моделей таблиц
Base = sqlalchemy.orm.declarative_base()

# метод для создания сессии
async def get_session():
    async with async_session() as session:
        yield session
