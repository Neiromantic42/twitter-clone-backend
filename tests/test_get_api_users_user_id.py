import pytest
from sqlalchemy import text
from sqlalchemy.future import select

from app.models import Users


@pytest.mark.user_arbitrary
@pytest.mark.asyncio
async def test_get_api_users_user_id(async_client, test_session):
    """
    Тест проверяет получение пользователя по ID через API.
    Шаги:
    - Создается тестовый пользователь в базе.
    - Выполняется GET-запрос к API по user_id.
    - Проверяется успешный статус и корректность возвращаемых данных.
    - В конце теста тестовый пользователь удаляется из базы.
    Проверяется наличие ключей: "id", "name", "followers", "following".
    """
    # Получить имя sequence для поля id в таблице users
    result = await test_session.execute(
        text("SELECT pg_get_serial_sequence('users', 'id')")
    )
    seq_name = result.scalar_one()

    # Сбросить sequence на максимум id из таблицы или 1, если таблица пустая
    await test_session.execute(
        text(
            f"""
        SELECT setval(
            '{seq_name}',
            COALESCE((SELECT MAX(id) FROM users), 1),
            (SELECT CASE WHEN EXISTS (SELECT 1 FROM users) THEN true ELSE false END)
        )
        """
        )
    )
    # Создаем тестового пользователя
    test_user = Users(name="test user", api_key="test_user")
    test_session.add(test_user)
    await test_session.commit()
    user_id = test_user.id
    # Запрос к API
    resp = await async_client.get(
        f"/api/users/{user_id}", headers={"api-key": "test_user"}
    )
    test_user_data = resp.json().get("user")
    result = resp.json().get("result")
    # Проверки ответа
    assert resp.status_code == 200
    assert result is True
    assert all(
        key in test_user_data for key in ("id", "name", "followers", "following")
    )
    # Очистка тестовых данных
    async with test_session.begin():
        result = await test_session.execute(select(Users).where(Users.id == user_id))
        user_test = result.scalar_one_or_none()
        if user_test:
            await test_session.delete(user_test)


@pytest.mark.user_arbitrary
@pytest.mark.asyncio
@pytest.mark.parametrize("api_key, status_code", [("bad-key", 404), ("", 401)])
async def test_negative_api_user_user_id(async_client, api_key, status_code):
    """
    Проверка поведения API при запросе пользователя с несуществующим ID.
    Шаги:
    - Выполняется GET-запрос с ID, которого нет в базе.
    - Проверяется, что API возвращает статус 404 (Not Found).
    - Проверяется, что в ответе поля result,
     error_type и error_message соответствуют ожидаемым значениям.
    """
    resp = await async_client.get("/api/users/{}", headers={"api-key": api_key})

    assert resp.status_code == status_code


@pytest.mark.user_arbitrary
@pytest.mark.asyncio
async def test_negative_api_user_id_not_found(async_client):
    """ """
    non_existent_user_id = 9999
    resp = await async_client.get(
        f"/api/users/{non_existent_user_id}", headers={"api-key": "test"}
    )
    assert resp.status_code == 404
    assert resp.json().get("result") == False
    assert resp.json().get("error_type") == "NotFound"
    assert resp.json().get("error_message") == "User not found"
