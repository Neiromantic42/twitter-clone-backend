import pytest
from app.models import Users, Follows

@pytest.mark.user_add_follow
@pytest.mark.asyncio
async def test_api_add_follow(async_client, test_session):
    """
    Проверка успешного подписки пользователя.
    """
    # Создаем двух тестовых пользователей
    test_user_1 = Users(id=670, name="user_1", api_key="test_key_1")
    test_user_2 = Users(id=671, name="user_2", api_key="test_key_2")
    test_session.add_all([test_user_1, test_user_2])
    await test_session.commit()
    # запрос на получение подписки
    resp = await async_client.post(
        f"/api/users/{test_user_2.id}/follow",
        headers={"api-key": test_user_1.api_key}
    )
    assert resp.status_code == 200
    assert resp.json().get("result") == True

    # Очистка тестовых данных
    async with test_session.begin():
        user1 = await test_session.get(Users, test_user_1.id)
        user2 = await test_session.get(Users, test_user_2.id)
        if user1:
            await test_session.delete(user1)
        if user2:
            await test_session.delete(user2)
        await test_session.commit()


@pytest.mark.user_add_follow
@pytest.mark.asyncio
async def test_negative_subscription_created(async_client, test_session):
    """
    Негативный тест.
    Проверка сценария: подписка уже создана
    """
    try:
        # Создаем двух тестовых пользователей
        test_user_1 = Users(id=672, name="user_1", api_key="test_key_1")
        test_user_2 = Users(id=673, name="user_2", api_key="test_key_2")
        test_session.add_all([test_user_1, test_user_2])
        await test_session.commit()
        # Подписываем первого пользователя на второго
        subscription = Follows(follower_id=test_user_1.id,
                               followed_id=test_user_2.id
                               )
        test_session.add(subscription)
        await test_session.commit()
        # запрос на получение подписки
        resp = await async_client.post(
            f"/api/users/{test_user_2.id}/follow",
            headers={"api-key": test_user_1.api_key}
        )
        assert resp.status_code == 400
        assert resp.json().get("result") == False
        assert resp.json().get("error_type") == "BadRequest"
        assert resp.json().get("error_message") == "Subscription already made"
    finally:
        # Очистка тестовых данных
        async with test_session.begin():
            user1 = await test_session.get(Users, test_user_1.id)
            user2 = await test_session.get(Users, test_user_2.id)
            if user1:
                await test_session.delete(user1)
            if user2:
                await test_session.delete(user2)
            await test_session.commit()

@pytest.mark.user_add_follow
@pytest.mark.asyncio
@pytest.mark.parametrize("api_key, status_code", [('bad-key', 404), ("", 401)])
async def test_negative_add_follows(async_client, api_key, status_code):
    """
    Проверка ответов при некорректном API-ключе.
    """
    resp = await async_client.post(
        "/api/users/{}/follow",
        headers={"api-key": api_key}
    )

    assert resp.status_code == status_code
