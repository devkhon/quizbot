from enum import Enum
from typing import TypedDict

from aiogram.fsm.state import State, StatesGroup
from models import Channel


class ChangeType(str, Enum):
    BECAME_ADMIN = "became_admin"
    LEFT_ADMIN = "left_admin"


class QuizForm(StatesGroup):
    channel = State()
    question = State()
    options = State()
    correct = State()
    confirm = State()


class QuizData(TypedDict):
    channels: list[Channel]
    titles: list[str]
    channel: Channel
    question: str
    options: list[str]
    correct: int
