from pydantic import BaseModel, Field


class ResponseTweetDelete(BaseModel):
    """Схема для валидации идентификатора удаляемого поста"""

    result: bool = Field(
        ..., title="Query result", description="Флаг успешности операции", example=True
    )
