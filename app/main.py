from fastapi import FastAPI, Request, Path
from fastapi import Depends, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
import logging
import aiofiles
from sqlalchemy import update, delete
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from contextlib import asynccontextmanager

# импорт для теста
from app.config import MEDIA_DIR
from pathlib import Path as PathlibPath

from app.models import Users, Tweets, Medias, Likes, Follows

from app.dependencies import get_current_user
from app.database import async_session, engine, Base, get_session, AsyncSession
from app.schemas.api_users_me import UserMeResponse
from app.schemas.api_tweets import TweetListResponse
from app.schemas.api_medias import ResponseApiMedias
from app.schemas.post_api_tweets import TweetData, AnswerApiTweets
from app.schemas.tweet_delete_schemas import ResponseTweetDelete
from app.schemas.api_likes_add_and_delete import ResponseApiAddLike, ResponseApiDeleteLike
from app.schemas.get_api_users_user_id_schemas import ResponseWithUserData
from app.schemas.api_users_user_id_follow_delete import Response



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
    return templates.TemplateResponse(request, "index.html", {"request": request})

@app.get("/api/users/me", response_model=UserMeResponse)
async def get_api_user_me(user: Users = Depends(get_current_user)):
    """
    конечная точка где пользователю отдается информация
    о его профиле
    """
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
    """
    конечная точка, где на клиент отдается лента твиттера
    """
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
        file: UploadFile = File(
            ...,
            description="Загружаемый файл"
        )
):
    """
    Endpoint для загрузки файлов из твита.
    Загрузка происходит через отправку формы
    """
    # проверяем пришел ли фаил в запросе
    if not file.filename:
        return JSONResponse(
            status_code=400,
            content={
                "result": False,
                "error_type": "BadRequest",
                "error_message": "Missing mandatory parameter,"
                                 " file in request body"
            }
        )
    # читаем входящий файл и пишем его в нисходящий файл в директорию media
    # async with aiofiles.open(f"media/{file.filename}", 'wb') as out_file:
    async with aiofiles.open(MEDIA_DIR / file.filename, 'wb') as out_file:
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

@app.post("/api/tweets", response_model=AnswerApiTweets)
async def get_create_tweet(
        tweet_data: TweetData, # Валидация входных данных
        user: Users = Depends(get_current_user),
        session: AsyncSession = Depends(get_session)
):
    """Конечная точка для создания твита"""
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

        return AnswerApiTweets(
            result=True,
            tweet_id=tweet_id
        )


@app.delete("/api/tweets/{id}", response_model=ResponseTweetDelete)
async def get_tweet_deleted(
        id: int = Path(
            ..., #Обязательное поле
            title="Tweet id",
            description="ID удаляемого твита",
            ge=1, # значение больше или ровно 1
        ),
        user: Users = Depends(get_current_user),
        session: AsyncSession = Depends(get_session)
):
    """Конечная точка для удаления твита"""
    async with session.begin():
        # Запрос на получение твита по id
        result = await session.execute(select(Tweets).where(Tweets.id == id))
        tweet = result.scalar_one_or_none()
        # Проверяем есть ли твит, если нет возвращаем ошибку
        if tweet is None:
            return JSONResponse(
                status_code=404,
                content={
                    "result": False,
                    "error_type": "NotFound",
                    "error_message": "Tweet not found"
                }
            )
        # Сравниваем api-key текущего юзера с api-key юзера удаляемого твита
        api_key_weaving_user = user.api_key # API-ключ текущего пользователя (автор запроса)
        api_key_of_tweet_to_be_removed = tweet.user.api_key # API-ключ владельца твита
        if api_key_weaving_user != api_key_of_tweet_to_be_removed:
            return JSONResponse(
                status_code=403,
                content={
                    "result": False,
                    "error_type": "Forbidden",
                    "error_message": "Access denied"
                }
            )
        # если все окей, удаляем сам твит, и каскад удалит все связные данные
        if tweet:
            await session.delete(tweet)
            return {
                "result": True
            }

@app.post("/api/tweets/{tweet_id}/likes", response_model=ResponseApiAddLike)
async def get_like_mark(
        tweet_id: int = Path(
            ...,
            title="Tweet id",
            description="ID понравившегося твита",
            ge=1, # значение больше или ровно 1
        ),
        user: Users = Depends(get_current_user),
        session: AsyncSession = Depends(get_session)
):
    """Конечная точка для получения лайка"""
    # Проверяем существует ли твит с таким id
    async with session.begin():
        # Запрос на получение твита по id
        result = await session.execute(select(Tweets).where(Tweets.id == tweet_id))
        tweet = result.scalar_one_or_none()
        # Проверяем есть ли твит, если нет возвращаем ошибку
        if tweet is None:
            return JSONResponse(
                status_code=404,
                content={
                    "result": False,
                    "error_type": "NotFound",
                    "error_message": "Tweet not found"
                }
            )
        # Проверка: уже ли поставлен лайк этим пользователем
        current_user_id = user.id
        # Запрос на получение записи о лайке юзера переданному id твита
        result = await session.execute(
            select(Likes)
            .where(
                Likes.user_id==current_user_id,
                Likes.tweet_id==tweet.id
            )
        )
        like = result.scalar_one_or_none()
        logger.info(f"LIKE: {like}")
        if like is not None:
            return JSONResponse(
                status_code=409,
                content={
                    "result": False,
                    "error_type": "Conflict",
                    "error_message": "Already liked"
                }
            )
        # Если все проверки пройдены, создаем лайк
        new_like = Likes(
            user_id=user.id,
            tweet_id=tweet_id
        )
        session.add(new_like)

    return {
        "result": True
    }

@app.delete("/api/tweets/{tweet_id}/likes", response_model=ResponseApiDeleteLike)
async def get_delete_like(
        tweet_id: int = Path(
            ...,
            title="Tweet id",
            description="ID понравившегося твита",
            ge=1, # значение больше или ровно 1
        ),
        user: Users = Depends(get_current_user),
        session: AsyncSession = Depends(get_session)
):
    """Конечная точка для удаления лайка"""
    # Проверяем существует ли твит с таким id
    async with session.begin():
        # Запрос на получение твита по id
        result = await session.execute(select(Tweets).where(Tweets.id == tweet_id))
        tweet = result.scalar_one_or_none()
        # Проверяем есть ли твит, если нет возвращаем ошибку
        if tweet is None:
            return JSONResponse(
                status_code=404,
                content={
                    "result": False,
                    "error_type": "NotFound",
                    "error_message": "Tweet not found"
                }
            )
        # Проверка: уже ли поставлен лайк этим пользователем
        current_user_id = user.id
        # Запрос на получение записи о лайке юзера переданному id твита
        result = await session.execute(
            select(Likes)
            .where(
                Likes.user_id == current_user_id,
                Likes.tweet_id == tweet.id
            )
        )
        like = result.scalar_one_or_none()
        logger.info(f"LIKE: {like}")
        if like is None:
            return JSONResponse(
                status_code=404,
                content={
                    "result": False,
                    "error_type": "NotFound",
                    "error_message": "Like already revoked"
                }
            )
        # Если все проверки пройдены, удаляем лайк
        await session.execute(
            delete(Likes).where(
                Likes.user_id == current_user_id,
                Likes.tweet_id == tweet.id
            )
        )

    return {
        "result": True
    }

@app.get("/api/users/{user_id}", response_model=ResponseWithUserData)
async def get_user_data_by_id(
    user_id: int = Path(
        ...,
        title="User id",
        description="ID текущего пользователя",
        ge=1  # значение больше или равно 1
    ),
    user: Users = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Конечная точка для получения информации о произвольном профиле по его id"""
    # Получаем запрашиваемого юзера
    async with session.begin():
        result = await session.execute(
            select(Users)
            .options(
                selectinload(Users.followers).joinedload(Follows.follower),
                selectinload(Users.following).joinedload(Follows.followed)
            )
            .where(Users.id == user_id))

        requested_user = result.scalars().first()

        # Получаем список подписчиков
        followers = [
            {"id": f.follower.id, "name": f.follower.name}
            for f in requested_user.followers
        ]
        logger.info(f"followers: {followers}")
        # Получаем список подписок (на кого подписан пользователь)
        following = [
            {"id": f.followed.id, "name": f.followed.name}
            for f in requested_user.following
        ]
        logger.info(f"following: {following}")

    return {
        "result": True,
        "user": {
            "id": user_id,
            "name": requested_user.name,
            "followers": followers,
            "following": following
        }
    }

@app.delete("/api/users/{user_id}/follow", response_model=Response)
async def get_unsubscribe(
    user_id: int = Path(
        ...,
        title="User id",
        description="ID текущего пользователя",
        ge=1  # значение больше или равно 1
    ),
    user: Users = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Конечная точка для отписки от другого пользователя"""
    # сперва проверяем существует ли такая подписка
    current_user_id = user.id
    async with session.begin():
        result = await session.execute(
            select(Follows).where(
                Follows.follower_id == current_user_id,
                Follows.followed_id == user_id
            )
        )
        subscription = result.scalar_one_or_none()

        if subscription is None:
            return JSONResponse(
                status_code=404,
                content={
                    "result": False,
                    "error_type": "NotFound",
                    "error_message": "Subscription not found"
                }
            )
        # Если все проверки пройдены и подписка найдена, то удаляем ее
        await session.execute(
            delete(Follows).where(
                Follows.follower_id == current_user_id,
                Follows.followed_id == user_id
            )
        )

    return {
        "result": True
    }

@app.post("/api/users/{user_id}/follow", response_model=Response)
async def get_subscription(
    user_id: int = Path(
        ...,
        title="User id",
        description="ID текущего пользователя",
        ge=1  # значение больше или равно 1
    ),
    user: Users = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Конечная точка для получения подписки на другого пользователя"""
    # сперва проверяем существует ли такая подписка
    current_user_id = user.id
    async with session.begin():
        result = await session.execute(
            select(Follows).where(
                Follows.follower_id == current_user_id,
                Follows.followed_id == user_id
            )
        )
        subscription = result.scalar_one_or_none()
        if subscription is not None:
            return JSONResponse(
                status_code=400,
                content={
                    "result": False,
                    "error_type": "BadRequest",
                    "error_message": "Subscription already made"
                }
            )
        else:
            new_follow = Follows(follower_id = user.id, followed_id = user_id)
            session.add(new_follow)
            return {
                "result": True
            }