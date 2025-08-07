import os
import random

import dotenv
from aiogram import Bot
from aiogram.enums import PollType
from aiogram.types import BotCommandScopeAllPrivateChats
from db import AsyncSessionLocal
from models import Quiz
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from type import CommandInfo

dotenv.load_dotenv()

bot = Bot(os.getenv("BOT_TOKEN", ""))

commands: list[CommandInfo] = [
    CommandInfo(command="start", description="start command"),
    CommandInfo(command="addquiz", description="addquiz command"),
    CommandInfo(command="settings", description="settings command"),
]


async def set_command_menu() -> None:
    await bot.set_my_commands(commands, BotCommandScopeAllPrivateChats())


async def get_rand_channel_quizzes(channel_id: int, n: int) -> list[Quiz]:
    stmt = (
        select(Quiz)
        .where(Quiz.channel_id == channel_id)
        .options(joinedload(Quiz.options))
    )

    async with AsyncSessionLocal() as session:
        quizzes = (await session.scalars(stmt)).unique().all()

    return random.sample(quizzes, min(n, len(quizzes)))


async def send_channel_quizzes(channel_id: int, n: int) -> None:
    quizzes = await get_rand_channel_quizzes(channel_id, n)
    for quiz in quizzes:
        await bot.send_poll(
            quiz.channel_id,
            quiz.question,
            [opt.option for opt in quiz.options],
            correct_option_id=quiz.correct_order,
            explanation=quiz.explanation,
            type=PollType.QUIZ,
        )
