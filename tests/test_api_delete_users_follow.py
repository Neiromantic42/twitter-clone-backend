import pytest
from app.models import Users, Follows


@pytest.mark.user_delete_follow
@pytest.mark.asyncio
async def test_api_delete_follow(async_client, test_session):
    """
    Проверка успешного удаления подписки пользователя.
    """
    # Создаем двух тестовых пользователей
    test_user_1 = Users(id=666, name="user_1", api_key="test_key_1")
    test_user_2 = Users(id=667, name="user_2", api_key="test_key_2")
    test_session.add_all([test_user_1, test_user_2])
    await test_session.commit()

    # Подписываем первого пользователя на второго
    subscription = Follows(follower_id=test_user_1.id, followed_id=test_user_2.id)
    test_session.add(subscription)
    await test_session.commit()

    # Удаляем подписку через API
    resp = await async_client.delete(
        f"/api/users/{test_user_2.id}/follow",
        headers={"api-key": test_user_1.api_key}
    )

    assert resp.status_code == 200
    assert resp.json().get("result") is True

    # Очистка тестовых данных
    async with test_session.begin():
        user1 = await test_session.get(Users, test_user_1.id)
        user2 = await test_session.get(Users, test_user_2.id)
        if user1:
            await test_session.delete(user1)
        if user2:
            await test_session.delete(user2)
        await test_session.commit()


@pytest.mark.user_delete_follow
@pytest.mark.asyncio
async def test_negative_api_delete_follow(async_client, test_session):
    """
    Проверка ошибки при удалении несуществующей подписки.
    """
    # Создаем двух тестовых пользователей без подписки
    test_user_1 = Users(id=668, name="user_1", api_key="test_key_1")
    test_user_2 = Users(id=669, name="user_2", api_key="test_key_2")
    test_session.add_all([test_user_1, test_user_2])
    await test_session.commit()

    # Пытаемся удалить подписку, которой нет
    resp = await async_client.delete(
        f"/api/users/{test_user_2.id}/follow",
        headers={"api-key": test_user_1.api_key}
    )

    assert resp.status_code == 404
    json_resp = resp.json()
    assert json_resp.get("result") is False
    assert json_resp.get("error_type") == "NotFound"
    assert json_resp.get("error_message") == "Subscription not found"

    # Очистка тестовых данных
    async with test_session.begin():
        user1 = await test_session.get(Users, test_user_1.id)
        user2 = await test_session.get(Users, test_user_2.id)
        if user1:
            await test_session.delete(user1)
        if user2:
            await test_session.delete(user2)
        await test_session.commit()


@pytest.mark.user_delete_follow
@pytest.mark.asyncio
@pytest.mark.parametrize("api_key, status_code", [('bad-key', 404), ("", 401)])
async def test_negative_api_user_user_id(async_client, api_key, status_code):
    """
    Проверка ответов при некорректном API-ключе.
    """
    resp = await async_client.delete(
        "/api/users/{}/follow",
        headers={"api-key": api_key}
    )

    assert resp.status_code == status_code