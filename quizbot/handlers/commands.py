from aiogram import Router
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message
from db import AsyncSessionLocal
from helpers import upsert_user
from messages import Msg

from .quizzes_fsm import router as addquiz_cmd_router
from .settings_fsm import router as settings_cmd_router

router = Router()
router.include_router(addquiz_cmd_router)
router.include_router(settings_cmd_router)


async def handle_start_command(message: Message) -> None:
    async with AsyncSessionLocal() as session:
        await upsert_user(session, message.from_user)
        await session.commit()
    await message.answer(Msg.START, parse_mode=ParseMode.MARKDOWN_V2)


router.message.register(handle_start_command, CommandStart())
