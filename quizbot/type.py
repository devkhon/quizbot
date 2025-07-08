from enum import Enum
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
    user_id: int
    channel: Channel | None
    question: str | None
    options: list[str] | None
    correct_order: int | None
    explanation: str | None


class SettingsForm(StatesGroup):
    select_channel = State()
    sleect_action = State()
    enter_time = State()
    enter_quiz_count = State()
    confirm = State()


class SettingsConfirmType(str, Enum):
    TIME = "time"
    QUIZZES = "quizzes"


class SettingsData(TypedDict):
    channels: list[Channel]
    channel: Channel | None
    pending_time: str | None
    pending_quiz_count: int | None
    confirm_type: SettingsConfirmType | None


class ChannelSettings(TypedDict):
    time: str | None
    quiz_count: str | None


class CommandInfo(TypedDict):
    command: str
    description: str
