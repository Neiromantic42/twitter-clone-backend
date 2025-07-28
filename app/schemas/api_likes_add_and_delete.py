from pydantic import BaseModel, Field


class ResponseApiAddLike(BaseModel):
    """Класс схема описывающая ответ клиенту"""

    result: bool = Field(
        ...,
        title="флаг успешности запроса",
        description="булево значение, говорящее об успешности операции: "
        "(поставлен ли лайк)",
        example=True,
    )


class ResponseApiDeleteLike(BaseModel):
    result: bool = Field(
        ...,
        title="флаг успешности выполнения запроса",
        description="булево значение, говорящее об успешности операции: "
        "(удален ли лайк)",
        example=True,
    )
