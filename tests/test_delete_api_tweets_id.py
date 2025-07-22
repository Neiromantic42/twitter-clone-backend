import pytest


@pytest.mark.tweets_delete
@pytest.mark.asyncio
async def test_delete_api_tweets_id(async_client, test_session):
    """
    Позитивный тест: создание и последующее удаление твита.

    Шаги:
    1. Отправляется POST-запрос на создание нового твита.
    2. Извлекается `tweet_id` из ответа.
    3. Отправляется DELETE-запрос по полученному `tweet_id`.
    4. Проверяется, что статус 200 и в ответе `result == True`.
    """
    resp_new_tweet = await async_client.post(
        "/api/tweets",
        headers={"api-key": "test"},
        json={
            "tweet_data": "текст твита который затем удалим",
            "tweet_media_ids": []
        }
    )
    # получаем id созданного твита для последующего удаления
    new_tweet_id = resp_new_tweet.json().get('tweet_id')
    resp_new_tweet_delete = await async_client.delete(
        f"/api/tweets/{new_tweet_id}",
        headers={"api-key": "test"}
    )
    assert resp_new_tweet_delete.status_code == 200
    assert resp_new_tweet_delete.json().get('result') == True


@pytest.mark.tweets_delete
@pytest.mark.asyncio
@pytest.mark.parametrize("api_key, status_code", [('bad-key', 404), ("", 401)])
async def test_negative_api_tweets_delete_id(async_client, api_key, status_code):
    """
    Негативный, параметризованный тест:
    Проверка ответа API при неверном или отсутствующем API-ключе.
    """
    resp = await async_client.delete(
        "/api/tweets/{}",
        headers={"api-key": api_key})
    assert resp.status_code == status_code

@pytest.mark.tweets_delete
@pytest.mark.asyncio
async def test_negative_tweet_does_not_exist(async_client):
    """
    Негативный тест: попытка удалить твит с несуществующим `tweet_id`.

    Ожидаем:
    - Статус 404.
    - Ответ с `error_type == "NotFound"`.
    """
    resp = await async_client.delete(
        "/api/tweets/9999",
        headers={"api-key": "test"})
    assert resp.status_code == 404
    assert resp.json().get("error_type") == "NotFound"


@pytest.mark.tweets_delete
@pytest.mark.asyncio
async def test_negative_delete_someone_else_tweet(async_client):
    """
    Негативный тест: попытка удаления чужого твита.

    Шаги:
    1. Создаётся твит от пользователя с API-ключом "test".
    2. Пытаемся удалить этот твит с другим API-ключом ("key2").
    3. Проверяем, что ответ имеет статус 403 и `error_type == "Forbidden"`.
    4. Удаляем созданный твит для очистки тестовых данных.
    """
    resp_new_tweet = await async_client.post(
        "/api/tweets",
        headers={"api-key": "test"},
        json={
            "tweet_data": "текст твита который затем удалим",
            "tweet_media_ids": []
        }
    )
    # получаем id созданного твита для последующего удаления
    new_tweet_id = resp_new_tweet.json().get('tweet_id')
    resp_new_tweet_delete_error = await async_client.delete(
        f"/api/tweets/{new_tweet_id}",
        headers={"api-key": "key2"}
    )
    assert resp_new_tweet_delete_error.status_code == 403
    assert resp_new_tweet_delete_error.json().get("error_type") == "Forbidden"
    # Очищаем тестовые данные из таблицы твитов
    await async_client.delete(
        f"/api/tweets/{new_tweet_id}",
        headers={"api-key": "test"}
    )
