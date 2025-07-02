from typing import TypedDict

from aiogram.fsm.state import State, StatesGroup
from models import Channel


class QuizForm(StatesGroup):
    select_channel = State()
    question = State()
    collect_options = State()
    correct_option = State()
    explanation = State()
    confirmation = State()


class QuizData(TypedDict):
    channels: list[Channel]
    channel: Channel
    question: str
    options: list[str]
    correct_index: int
    explanation: str | None


class CommandInfo(TypedDict):
    command: str
    description: str
