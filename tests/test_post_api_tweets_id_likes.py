import pytest
from sqlalchemy.future import select

from app.models import Tweets


@pytest.mark.tweets_likes
@pytest.mark.asyncio
async def test_api_tweets_likes(async_client, test_session):
    """
    Проверяет успешную установку лайка и
    повторную попытку поставить лайк(должна вернуть 409).
    """
    try:
        # Создаем твит для последующего лайка
        resp_tweet = await async_client.post(
            "/api/tweets",
            headers={"api-key": "test"},
            json={"tweet_data": "тестовый текст твита", "tweet_media_ids": []},
        )
        new_tweet_id = resp_tweet.json().get("tweet_id")
        # делаем запрос для получения лайка
        resp_likes = await async_client.post(
            f"/api/tweets/{new_tweet_id}/likes",
            headers={"api-key": "test"},
        )
        assert resp_likes.status_code == 200
        assert resp_likes.json().get("result") == True
        # пытаемся поставить лайк еще раз, ожидаем ошибку
        repeat_request_for_like = await async_client.post(
            f"/api/tweets/{new_tweet_id}/likes",
            headers={"api-key": "test"},
        )
        assert repeat_request_for_like.status_code == 409
        assert repeat_request_for_like.json().get("error_type") == "Conflict"

    finally:
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


@pytest.mark.tweets_likes
@pytest.mark.asyncio
@pytest.mark.parametrize("api_key, status_code", [("bad-key", 404), ("", 401)])
async def test_negative_api_tweets_likes(async_client, api_key, status_code):
    """
    Проверка ответа API при неверном или отсутствующем API-ключе.
    """
    resp = await async_client.post("/api/tweets/{}/likes", headers={"api-key": api_key})

    assert resp.status_code == status_code


@pytest.mark.tweets_likes
@pytest.mark.asyncio
async def test_negative_likes_not_found(async_client, test_session):
    """
    Проверка лайка для несуществующего tweet_id (ожидаем 404 Not Found).
    """
    non_existent_id_tweets = 99999
    resp = await async_client.post(
        f"/api/tweets/{non_existent_id_tweets}/likes", headers={"api-key": "test"}
    )
    assert resp.status_code == 404
    assert resp.json().get("error_type") == "NotFound"
