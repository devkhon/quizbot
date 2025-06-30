from typing import TypedDict

from aiogram.fsm.state import State, StatesGroup
from models import Channel


class QuizForm(StatesGroup):
    channel = State()
    question = State()
    options = State()
    correct = State()
    confirmation = State()


class QuizData(TypedDict):
    channels: list[Channel]
    titles: list[str]
    channel: Channel
    question: str
    options: list[str]
    correct: int
