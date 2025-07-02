from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class TimeStamped:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), server_onupdate=func.now()
    )


class User(Base, TimeStamped):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    first_name: Mapped[str] = mapped_column(String(64))
    last_name: Mapped[str | None] = mapped_column(String(64))
    username: Mapped[str | None] = mapped_column(String(32))

    admins: Mapped[list["Admin"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    quizzes: Mapped[list["Quiz"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"User(id={self.id!r}, first_name={self.first_name!r}, "
            f"last_name={self.last_name!r}, username={self.username!r})"
        )


class Channel(Base, TimeStamped):
    __tablename__ = "channels"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    title: Mapped[str] = mapped_column(String(255))
    username: Mapped[str | None] = mapped_column(String(32))

    admins: Mapped[list["Admin"]] = relationship(
        back_populates="channel", cascade="all, delete-orphan"
    )
    quizzes: Mapped[list["Quiz"]] = relationship(
        back_populates="channel", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"Channel(id={self.id!r}, title={self.title!r}, username={self.username!r})"
        )


class Admin(Base, TimeStamped):
    __tablename__ = "admins"
    __table_args__ = (UniqueConstraint("user_id", "channel_id"),)

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    channel_id: Mapped[int] = mapped_column(
        ForeignKey("channels.id", ondelete="CASCADE")
    )

    user: Mapped["User"] = relationship(back_populates="admins")
    channel: Mapped["Channel"] = relationship(back_populates="admins")

    def __repr__(self) -> str:
        return f"Admin(id={self.id!r}, user_id={self.user_id!r}, channel_id={self.channel_id!r})"  # noqa: E501


class Quiz(Base, TimeStamped):
    __tablename__ = "quizzes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    question: Mapped[str] = mapped_column(String(300))
    correct: Mapped[int] = mapped_column(SmallInteger)
    explanation: Mapped[str | None] = mapped_column(String(200))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    channel_id: Mapped[int] = mapped_column(
        ForeignKey("channels.id", ondelete="CASCADE")
    )

    user: Mapped["User"] = relationship(back_populates="quizzes")
    channel: Mapped["Channel"] = relationship(back_populates="quizzes")
    options: Mapped[list["Option"]] = relationship(
        back_populates="quiz", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"Quiz(id={self.id!r}, question={self.question!r}, "
            f"correct={self.correct!r}, channel_id={self.channel_id!r})"
        )


class Option(Base, TimeStamped):
    __tablename__ = "options"
    __table_args__ = (UniqueConstraint("quiz_id", "order"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    option: Mapped[str] = mapped_column(String(100))
    order: Mapped[int] = mapped_column(SmallInteger)
    quiz_id: Mapped[int] = mapped_column(ForeignKey("quizzes.id", ondelete="CASCADE"))

    quiz: Mapped["Quiz"] = relationship(back_populates="options")

    def __repr__(self) -> str:
        return (
            f"Option(id={self.id!r}, option={self.option!r}, "
            f"order={self.order!r}, quiz_id={self.quiz_id!r})"
        )
