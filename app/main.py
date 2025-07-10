from fastapi import FastAPI, HTTPException, Request
from fastapi import Depends, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from typing import Dict, List
import logging
import aiofiles
from sqlalchemy import update
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload, joinedload
from contextlib import asynccontextmanager

from app.models import Users, Tweets, Medias, Likes, Follows
from app.dependencies import get_current_user
from app.database import async_session, engine, Base, get_session, AsyncSession
from app.schemas.api_users_me import UserMeResponse
from app.schemas.api_tweets import TweetListResponse
from app.schemas.api_medias import ResponseApiMedias
from app.schemas.post_api_tweets import TweetData

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """механизм жизненного цикла приложения"""
    # Создаём подключение к базе данных и начинаем транзакцию
    # Логируем названия таблиц, которые должны создаться
    logger.debug(f"Tables to create: {list(Base.metadata.tables.keys())}")
    async with engine.begin() as conn:
        # Создаём все таблицы, определённые в моделях, если они ещё не созданы
        await conn.run_sync(Base.metadata.create_all)
    # yield ставит точку паузы. Весь код до yield выполняется при старте
    yield
    await engine.dispose() # Очищаем ресурсы и закрываем соединения

# Создаём экземпляр приложения FastAPI и передаём ему механизм жизненного цикла
app = FastAPI(
    lifespan=lifespan
)
# Монтируем статику для js, css
app.mount("/css", StaticFiles(directory="app/templates/static/css"), name="css")
app.mount("/js", StaticFiles(directory="app/templates/static/js"), name="js")
app.mount("/favicon.ico", StaticFiles(directory="app/templates"), name="favicon")
app.mount("/media", StaticFiles(directory="media"), name="media")

templates = Jinja2Templates(directory="app/templates")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """
    Отдаёт HTML-страницу клиенту.
    Используется для фронтенда, не требует API key.
    """
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/users/me", response_model=UserMeResponse)
async def get_api_user_me(user: Users = Depends(get_current_user)):
    """конечная точка где пользователю отдается информация о его профиле"""
    # Получаем список подписчиков
    followers = [
        {"id": f.follower.id, "name": f.follower.name}
        for f in user.followers
    ]
    logger.info(f"followers: {followers}")
    # Получаем список подписок (на кого подписан пользователь)
    following = [
        {"id": f.followed.id, "name": f.followed.name}
        for f in user.following
    ]

    logger.info(f"following: {following}")

    return {
  "result": "true",
  "user": {
    "id": user.id,
    "name": user.name,
    "followers": followers,
    "following": following
  }
}

@app.get("/api/tweets", response_model=TweetListResponse)
async def get_twitter_feed(
        user: Users = Depends(get_current_user),
        session: AsyncSession = Depends(get_session)
):
    """конечная точка, где на клиент отдается лента твиттера"""
    logger.info(f"Обьект юзера: {user}")
    # возвращаем список id всех пользователей, на которых подписан текущий пользователь [2,3]
    following_ids = [f.followed_id for f in user.following]
    logger.info(f"список id всех пользователей, на которых подписан текущий пользователь: {following_ids}")
    author_ids = [user.id] + following_ids
    logger.info(f'Список id юзеров для ленты, кого показывать: {author_ids}')
    # Запрос на получение всех твитов указанных пользователей
    tweets_query = (
        select(Tweets)
        .where(Tweets.user_id.in_(author_ids))
        .options(
        selectinload(Tweets.likes).joinedload(Likes.user),
                selectinload(Tweets.medias),
        )
        .order_by(Tweets.created_at.desc()))

    async with session.begin():
        result = await session.execute(tweets_query)
        tweets = result.scalars().all()
        for tweet in tweets:
            logger.info({
                "id": tweet.id,
                "content": tweet.content,
                "user_id": tweet.user_id,
                "created_at": tweet.created_at,
                "media_links": tweet.medias,
                "likes": tweet.likes
            })

    return {
  "result": True,
  "tweets": [
    {
      "id": tweet.id,
      "content": tweet.content,
      "attachments": [f"media/{media.path_url}" for media in tweet.medias],
      "author": {
        "id": tweet.user.id,
        "name": tweet.user.name
      },
      "likes": [
        {
          "user_id": like.user.id,
          "name": like.user.name
        }
          for like in tweet.likes
      ]
    }
      for tweet in tweets
  ]
}


@app.post("/api/medias", response_model=ResponseApiMedias)
async def get_media_download(
        user: Users = Depends(get_current_user),
        session: AsyncSession = Depends(get_session),
        file: UploadFile = File(..., description="Загружаемый файл")
):
    """Endpoint для загрузки файлов из твита.\
     Загрузка происходит через отправку формы"""
    # читаем входящий файл и пишем его в нисходящий файл в директорию media
    async with aiofiles.open(f"media/{file.filename}", 'wb') as out_file:
        content = await file.read()
        await out_file.write(content)

    # вносим данные в бд(ссылку на файл, id)
    async with session.begin():
        # создаём запрос на запись в бд
        new_media = Medias(path_url=file.filename)
        session.add(new_media)


    return {
        "result": True,
        "media_id": new_media.id
    }

@app.post("/api/tweets")
async def get_create_tweet(
        tweet_data: TweetData,
        user: Users = Depends(get_current_user),
        session: AsyncSession = Depends(get_session)
):
    # Проверяем подается ли список идентификаторов медиафайлов
    if tweet_data.tweet_media_ids == []:
        async with session.begin():
            new_tweet = Tweets(
                content=tweet_data.tweet_data,
                user_id = user.id
            )
            session.add(new_tweet)
            await session.flush()
            tweet_id = new_tweet.id
            logger.info(f"tweet_id: {tweet_id}")
        return {
            "result": True,
            "tweet_id": tweet_id
        }
    # если же список идентификаторов медиафайлов не пустой
    else:
        async with session.begin():
            new_tweet = Tweets(
                content=tweet_data.tweet_data,
                user_id = user.id
            )
            session.add(new_tweet)
            await session.flush()
            tweet_id = new_tweet.id
            # привязываем id твита к медиафайлам
            update_query = (
                update(Medias)
                .where(Medias.id.in_(tweet_data.tweet_media_ids))
                .values(tweet_id=tweet_id)
            )
            await session.execute(update_query)

        return {
            "result": True,
            "tweet_id": tweet_id
        }
