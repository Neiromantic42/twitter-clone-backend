import aiofiles
import pytest
from app.config import MEDIA_DIR
from app.models import Medias
from sqlalchemy import text
from sqlalchemy.future import select

import os

os.makedirs(MEDIA_DIR, exist_ok=True)

@pytest.mark.medias
@pytest.mark.asyncio
async def test_post_api_medias(async_client, test_session):
    """
    Тест проверяет работу эндпоинта /api/medias,
    отвечающего за загрузку файлов.
    Сам по себе эндпоинт не публикует твит и не формирует публикацию,
    а лишь возвращает ID загруженного медиафайла,
    который затем используется в запросе создания твита.
    """
    # Получить имя sequence для поля id в таблице medias
    result = await test_session.execute(
        text("SELECT pg_get_serial_sequence('medias', 'id')")
    )
    seq_name = result.scalar_one()

    # Сбросить sequence на максимум id из таблицы или 1, если таблица пустая
    await test_session.execute(
        text(f"""
        SELECT setval(
            '{seq_name}',
            COALESCE((SELECT MAX(id) FROM medias), 1),
            (SELECT CASE WHEN EXISTS (SELECT 1 FROM medias) THEN true ELSE false END)
        )
        """)
    )
    await test_session.commit()
    # Читаем тестовый файл перед отправкой
    async with aiofiles.open(
            "tests/test_media_files/осел.jpeg",
            'rb'
    ) as sent_file:
        content = await sent_file.read()
    resp = await async_client.post(
        "/api/medias",
        headers={"api-key": "key3"},
        files={"file": ("осел.jpeg", content, "image/jpeg")}
    )
    media_id = resp.json().get('media_id')
    assert resp.status_code == 200
    assert resp.json().get('result') == True
    assert media_id

    # очищаем за тестом мусорные данные из бд

    async with test_session.begin():
        result = await test_session.execute(
            select(Medias).where(Medias.id == media_id)
        )
        media = result.scalar_one_or_none()
        if media:
            await test_session.delete(media)
        else:
            pass
    # очищаем и сам фаил с диска
    file_path = os.path.join(MEDIA_DIR, media.path_url)
    if os.path.exists(file_path):
        os.remove(file_path)

@pytest.mark.medias
@pytest.mark.asyncio
@pytest.mark.parametrize("api_key, status_code", [('bad-key', 404), ("", 401)])
async def test_negative_api_medias(async_client, api_key, status_code):
    """
    Проверка ответа API при неверном или отсутствующем API-ключе.
    И отсутствующем фале
    """
    async with aiofiles.open(
            "tests/test_media_files/осел.jpeg",
            'rb'
    ) as sent_file:
        content = await sent_file.read()
    resp = await async_client.post(
        "/api/medias",
        headers={"api-key": api_key},
        files={"file": ("осел.jpeg", content, "image/jpeg")})
    assert resp.status_code == status_code
