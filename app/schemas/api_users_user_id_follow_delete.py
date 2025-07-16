from pydantic import BaseModel, Field

class Response(BaseModel):
    result: bool = Field(
        ...,
        title="флаг результат выполнения запроса на удаление подписки"
    )