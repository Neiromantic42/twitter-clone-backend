from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class Users(Base):
    """Класс - модель описывающий таблицу юзеров"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    api_key = Column(String(100), nullable=False, unique=True)
    tweets = relationship("Tweets", back_populates="user", cascade="all, delete-orphan")
    likes = relationship("Likes", back_populates="user", cascade="all, delete-orphan")
    following = relationship(
        "Follows",
        back_populates="follower",
        foreign_keys="[Follows.follower_id]",
        cascade="all, delete-orphan",
    )
    followers = relationship(
        "Follows",
        back_populates="followed",
        foreign_keys="[Follows.followed_id]",
        cascade="all, delete-orphan",
    )


class Tweets(Base):
    """Класс - модель описывающий таблицу твитов с внешним ключом к таблице users"""

    __tablename__ = "tweets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    content = Column(String(280), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    medias = relationship("Medias", backref="tweet", cascade="all, delete-orphan")
    likes = relationship("Likes", backref="tweet", cascade="all, delete-orphan")
    user = relationship("Users", back_populates="tweets")


class Medias(Base):
    """Класс - модель описывающий таблицу с медиафайлами(картинками)"""

    __tablename__ = "medias"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    tweet_id = Column(Integer, ForeignKey("tweets.id", ondelete="CASCADE"))
    path_url = Column(String(255), nullable=False, index=True, unique=True)


class Likes(Base):
    """Класс - модель описывающий таблицу лайков с двумя внешними ключами к users и tweets"""

    __tablename__ = "likes"

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    tweet_id = Column(
        Integer,
        ForeignKey("tweets.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    user = relationship("Users", back_populates="likes")


class Follows(Base):
    """Класс модель описывающая таблицу подписок (follower и followed - пользователи)"""

    __tablename__ = "follows"

    follower_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    followed_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )

    follower = relationship(
        "Users", foreign_keys=[follower_id], back_populates="following"
    )
    followed = relationship(
        "Users", foreign_keys=[followed_id], back_populates="followers"
    )
