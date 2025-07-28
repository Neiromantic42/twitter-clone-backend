import os

import aiofiles
import pytest
from sqlalchemy import and_
from sqlalchemy.future import select

from app.config import MEDIA_DIR
from app.models import Medias, Tweets

os.makedirs(MEDIA_DIR, exist_ok=True)


@pytest.mark.tweets_post
@pytest.mark.asyncio
async def test_post_api_tweets(async_client, test_session):
    """
    Интеграционный тест: загрузка медиа + создание твита
    с привязкой к этому медиафайлу.
    Проверяет успешную вставку и связь между таблицами Medias и Tweets.
    """
    # Читаем тестовый файл перед отправкой
    async with aiofiles.open("tests/test_media_files/осел.jpeg", "rb") as sent_file:
        content = await sent_file.read()
    resp_media = await async_client.post(
        "/api/medias",
        headers={"api-key": "test"},
        files={"file": ("осел.jpeg", content, "image/jpeg")},
    )
    # получаем id вновь созданного медиафала
    media_id = resp_media.json().get("media_id")
    # делаем запрос к /api/tweets и подаем данные для твита
    resp_tweet = await async_client.post(
        "/api/tweets",
        headers={"api-key": "test"},
        json={
            "tweet_data": "текст теста test_post_api_tweets",
            "tweet_media_ids": [media_id],
        },
    )
    # проверяем ответы эндпоинта
    new_tweet_id = resp_tweet.json().get("tweet_id")
    assert resp_tweet.status_code == 200
    assert resp_tweet.json().get("result") == True
    assert new_tweet_id
    # проверяем связь медиа -> твит
    async with test_session.begin():
        result = await test_session.execute(
            select(Medias).where(
                and_(Medias.id == media_id, Medias.tweet_id == new_tweet_id)
            )
        )
        # получаем запись если она есть тест пройден связь установлена
        media_tweet = result.scalar_one_or_none()
        assert media_tweet

    # очищаем за тестом мусорные данные из таблицы медиа
    async with test_session.begin():
        result = await test_session.execute(select(Medias).where(Medias.id == media_id))
        media = result.scalar_one_or_none()
        if media:
            await test_session.delete(media)
        else:
            pass
    # очищаем и сам фаил с диска
    file_path = os.path.join(MEDIA_DIR, media.path_url)
    if os.path.exists(file_path):
        os.remove(file_path)

    # очищаем за тестом мусорные данные из таблицы твитов
    async with test_session.begin():
        result = await test_session.execute(
            select(Tweets).where(Tweets.id == new_tweet_id)
        )
        tweet_test = result.scalar_one_or_none()
        if tweet_test:
            await test_session.delete(tweet_test)
        else:
            pass


@pytest.mark.tweets_post
@pytest.mark.asyncio
@pytest.mark.parametrize("api_key, status_code", [("bad-key", 404), ("", 401)])
async def test_negative_api_tweets(async_client, api_key, status_code):
    """
    Проверка ответа API при неверном или отсутствующем API-ключе.
    """
    resp = await async_client.post("/api/tweets", headers={"api-key": api_key}, json={})
    assert resp.status_code == status_code
