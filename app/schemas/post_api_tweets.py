from pydantic import BaseModel, Field


class TweetData(BaseModel):
    """Схема для валидации входных данных
    (текст твита и списка с id медиафайлов)"""

    tweet_data: str = Field(
        ...,
        title="текст твита",
        description="Входные данные запроса, содержащие текст твита",
        examples=[{"value": "не поверите что со мной сегодня случилось..."}],
    )
    tweet_media_ids: list[int] = Field(
        title="Идентификаторы медиафайлов",
        description="Входные данные запроса, список с id медиафайлов",
        examples=[{"value": [1, 2, 3]}],
    )


class AnswerApiTweets(BaseModel):
    """Схема для валидации ответа клиенту"""

    result: bool = Field(
        ...,
        title="Булево значение",
        description="Флаг успешности выполнения запроса",
        examples=[{"value": True}],
    )
    tweet_id: int = Field(
        ...,
        title="Идентификатор твита",
        description="id вновь созданного твита с картинкой или без",
        examples=[{"value": 7}],
    )
