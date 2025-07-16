from pydantic import BaseModel, Field

class UserShort(BaseModel):
    """Схема описывающая подписчиков или подписки"""
    id: int = Field(
        ...,
        title='уникальный идентификатор подписки',
    )
    name: str = Field(
        ...,
        title='имя подписки'
    )

class UserData(BaseModel):
    """Схема описывающая возвращаемые данные юзера"""
    id: int = Field(
        ...,
        title='User id',
        description="Уникальный идентификатор пользователя",
        example = 2
    )
    name: str = Field(
        ...,
        title="User name",
        description= "Имя пользователя",
        example="Alexander"
    )
    followers: list[UserShort] = Field(
        title='(подписчики) - это пользователи,\
         которые подписались на ваш аккаунт и следят за вашими обновлениями'
    )
    following: list[UserShort] = Field(
        title='(подписки) - это список пользователей,\
         на которых подписаны вы, и чьи обновления вы видите в своей ленте'
    )


class ResponseWithUserData(BaseModel):
    """Схема описывающая ответ клиенту"""
    result: bool = Field(
        ...,
        title='Булево значение',
        description='Флаг успешности выполнения запроса',
        example=True
    )
    user: UserData = Field(
        ...,
        title="словарь с данными о текущем пользователе"
    )
