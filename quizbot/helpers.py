import re

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.types import User as TUser
from models import Admin, Channel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload


async def get_user_channels(session: AsyncSession, user: TUser) -> list[Channel]:
    stmt = (
        select(Admin).where(Admin.user_id == user.id).options(joinedload(Admin.channel))
    )

    admins = (await session.scalars(stmt)).all()
    channels = [admin.channel for admin in admins]

    return channels


def create_keyboard(*button_groups: tuple[list[str], int]) -> ReplyKeyboardMarkup:
    keyboard = []
    for buttons, columns in button_groups:
        rows = [
            [KeyboardButton(text=btn) for btn in buttons[i : i + columns]]
            for i in range(0, len(buttons), columns)
        ]
        keyboard.extend(rows)

    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def escape_markdown(text: str) -> str:
    escape_chars = r"_*[]()~`>#+-=|{}.!\\"
    return re.sub(f"([{re.escape(escape_chars)}])", r"\\\1", text)
