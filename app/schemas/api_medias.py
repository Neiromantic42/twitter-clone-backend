from pydantic import BaseModel, Field


class ResponseApiMedias(BaseModel):
    """Схема описывающая ответ от Endpoint /api/medias
    (Endpoint для загрузки файлов из твита)"""

    result: bool = Field(
        ...,
        title="флаг успешности запроса",
        description="булево значение, говорящее об успешности операции",
    )
    media_id: int = Field(
        ...,
        title="уникальный идентификатор загруженного медиафайла",
        description="id записи в таблице бд medias",
    )
