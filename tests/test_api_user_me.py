import pytest

@pytest.mark.users
@pytest.mark.asyncio
async def test_api_user_me(async_client):
    """
    Тест успешного GET-запроса к /api/users/me с корректным api-key.
    Проверяет статус ответа и наличие ключа 'result' со значением "true"
    в JSON-ответе, а так же присутствие необходимых по контракту полей.
    """
    resp = await async_client.get("/api/users/me", headers={"api-key": "test"})
    assert resp.status_code == 200
    assert resp.json()['result'] == "true"
    user = resp.json().get('user')
    assert user
    for key in ["id", "name", "followers", "following"]:
        assert key in user


@pytest.mark.users
@pytest.mark.asyncio
@pytest.mark.parametrize("api_key, status_code", [('bad-key', 404), ("", 401)])
async def test_negative_api_user_me(async_client, api_key, status_code):
    """
    Проверка ответа API при неверном или отсутствующем API-ключе.
    """
    resp = await async_client.get("/api/users/me",
                                  headers={"api-key": api_key})
    assert resp.status_code == status_code