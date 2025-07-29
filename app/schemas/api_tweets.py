from pydantic import BaseModel, Field


class TweetAuthor(BaseModel):
    """Схема описывающая автора поста"""

    id: int = Field(..., title="уникальный идентификатор автора поста")
    name: str = Field(..., title="Имя автора поста")


class TweetLikes(BaseModel):
    """Схема описывающая лайки к посту"""

    user_id: int = Field(title="идентификатор пользователя поставившего лайк")
    name: str = Field(title="имя пользователя оставившего лайк")


class Tweet(BaseModel):
    """Схема описывающая твит"""

    id: int = Field(..., title="идентификатор твита")
    content: str = Field(..., title="текст твита")
    attachments: list[str] = Field(title="Ссылки на медиафайлы")
    author: TweetAuthor = Field(..., title="данные автора поста")
    likes: list[TweetLikes] = Field(title="Данные пользователя поставившего лайк")


class TweetListResponse(BaseModel):
    """Схема описывающая основной возвращаемый объект"""

    result: bool = Field(..., title="булево значения, результат выполнения запроса")
    tweets: list[Tweet] = Field(title="список твитов в ленте пользователя")
