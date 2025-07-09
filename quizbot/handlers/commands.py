from aiogram import Router
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.types import User as TUser
from db import AsyncSessionLocal
from handlers.quizzes_fsm import router as addquiz_cmd_router
from handlers.settings_fsm import router as settings_cmd_router
from messages import Msg
from models import User
from sqlalchemy.ext.asyncio import AsyncSession

router = Router()
router.include_router(addquiz_cmd_router)
router.include_router(settings_cmd_router)


async def upsert_user(session: AsyncSession, user: TUser) -> User:
    old_user = await session.get(User, user.id)
    if old_user:
        old_user.first_name = user.first_name
        old_user.last_name = user.last_name
        old_user.username = user.username
        return old_user

    new_user = User(
        id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        username=user.username,
    )

    session.add(new_user)
    return new_user


async def handle_start_command(message: Message) -> None:
    if not message.from_user:
        return

    async with AsyncSessionLocal() as session:
        await upsert_user(session, message.from_user)
        await session.commit()
    await message.answer(Msg.START, parse_mode=ParseMode.MARKDOWN_V2)


router.message.register(handle_start_command, CommandStart())
