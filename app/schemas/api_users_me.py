from pydantic import BaseModel, Field


class UserShort(BaseModel):
    """Схема описывающая подписчиков или подписки"""

    id: int = Field(
        ...,
        title="уникальный идентификатор подписки",
    )
    name: str = Field(..., title="имя подписки")


class UserData(BaseModel):
    """Схема описывающая пользователя с подписками и подписчиками"""

    id: int = Field(..., title="Уникальный идентификатор пользователя")
    name: str = Field(
        ...,
        title="Имя пользователя",
        min_length=2,
    )
    followers: list[UserShort] = Field(
        title="(подписчики) - это пользователи,\
         которые подписались на ваш аккаунт и следят за вашими обновлениями"
    )
    following: list[UserShort] = Field(
        title="(подписки) - это список пользователей,\
         на которых подписаны вы, и чьи обновления вы видите в своей ленте"
    )


class UserMeResponse(BaseModel):
    """Схема описывающая ответ клиенту"""

    result: str = Field(..., title="строка результата")
    user: UserData = Field(..., title="словарь с данными о текущем пользователе")
