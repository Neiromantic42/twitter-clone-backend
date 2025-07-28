import pytest

@pytest.mark.tweets_get
@pytest.mark.asyncio
async def test_get_api_tweets(async_client):
    """
    Тест эндпоинта GET /api/tweets —
    получение ленты твитов текущего пользователя.
    Проверяется:
    - Успешный статус ответа (200)
    - Флаг результата "result" == True
    - Что возвращается список твитов
    - Если список не пустой, у каждого твита проверяется наличие ключей:
        id, content, attachments, author, likes
    - attachments — список строк (путей к медиа)
    - author — словарь с ключами "id" и "name"
    - likes — список словарей, каждый с ключами "user_id" и "name"
    - Если список пустой, проверяется, что он именно пустой
    """
    resp = await async_client.get("/api/tweets",
                                  headers={"api-key": "test"})
    assert resp.status_code == 200
    assert resp.json().get('result') == True
    tweets_data = resp.json().get('tweets')
    assert isinstance(tweets_data, list)
    if tweets_data:
        for tweet in tweets_data:
            assert "id" in tweet
            assert "attachments" in tweet
            assert "author" in tweet
            assert "likes" in tweet
            assert "content" in tweet
            assert isinstance(tweet['attachments'], list)
            assert isinstance(tweet['author'], dict)
            assert "id" in tweet['author']
            assert "name" in tweet['author']
            assert isinstance(tweet['likes'], list)
            for likes in tweet['likes']:
                assert "user_id" in likes
                assert "name" in likes
    else:
        assert tweets_data == []


@pytest.mark.tweets_get
@pytest.mark.asyncio
@pytest.mark.parametrize("api_key, status_code", [('bad-key', 404), ("", 401)])
async def test_negative_api_tweets(async_client, api_key, status_code):
    """
    Проверка ответа API при неверном или отсутствующем API-ключе.
    """
    resp = await async_client.get("/api/tweets",
                                  headers={"api-key": api_key})
    assert resp.status_code == status_code