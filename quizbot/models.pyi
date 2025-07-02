from datetime import datetime

from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase): ...

class TimeStamped:
    created_at: datetime
    updated_at: datetime

class User(Base, TimeStamped):
    id: int
    first_name: str
    last_name: str | None
    username: str | None
    admins: list[Admin]
    quizzes: list[Quiz]

    def __init__(
        self,
        id: int,
        first_name: str,
        last_name: str | None = ...,
        username: str | None = ...,
    ) -> None: ...
    def __repr__(self) -> str: ...

class Channel(Base, TimeStamped):
    id: int
    title: str
    username: str | None
    active: bool
    admins: list[Admin]
    quizzes: list[Quiz]

    def __init__(self, id: int, title: str, username: str | None = ...) -> None: ...
    def __repr__(self) -> str: ...

class Admin(Base, TimeStamped):
    id: int
    user_id: int
    channel_id: int
    user: User
    channel: Channel

    def __init__(self, id: int, user_id: int, channel_id: int) -> None: ...
    def __repr__(self) -> str: ...

class Quiz(Base, TimeStamped):
    id: int
    question: str
    correct: int
    explanation: str | None
    user_id: int
    channel_id: int
    channel: Channel
    options: list[Option]

    def __init__(
        self,
        id: int,
        question: str,
        correct: int,
        explanation: str | None,
        user_id: int,
        channel_id: int,
    ) -> None: ...
    def __repr__(self) -> str: ...

class Option(Base, TimeStamped):
    id: int
    option: str
    order: int
    quiz_id: int
    quiz: Quiz

    def __init__(self, id: int, option: str, order: int, quiz_id: int) -> None: ...
    def __repr__(self) -> str: ...
