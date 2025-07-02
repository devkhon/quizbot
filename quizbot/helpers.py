import re

from aiogram.enums import ChatType
from aiogram.filters import BaseFilter
from aiogram.types import BotCommand, Chat, KeyboardButton, Message, ReplyKeyboardMarkup
from aiogram.types import User as TUser
from models import Admin, Channel, Option, Quiz, User
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from type import CommandInfo, QuizData


class ChatTypeFilter(BaseFilter):
    def __init__(self, chat_type: ChatType):
        self.chat_type = chat_type

    async def __call__(self, message: Message) -> bool:
        return message.chat.type == self.chat_type


async def upsert_channel(session: AsyncSession, chat: Chat) -> Channel:
    old_channel = await session.get(Channel, chat.id)
    if old_channel:
        old_channel.title = chat.title
        old_channel.username = chat.username
        return old_channel

    new_channel = Channel(id=chat.id, title=chat.title, username=chat.username)
    session.add(new_channel)
    return new_channel


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


async def add_channel_admins(
    session: AsyncSession, channel_id: int, admin_users: list[TUser]
) -> None:
    admins_to_add = []
    for admin_user in admin_users:
        if not admin_user.is_bot:
            user = await upsert_user(session, admin_user)
            new_admin = Admin(user_id=user.id, channel_id=channel_id)
            admins_to_add.append(new_admin)
    session.add_all(admins_to_add)


async def delete_channel_admins(
    session: AsyncSession, channel_id: int, admin_ids: list[int] | None = None
) -> None:
    if admin_ids is not None and not admin_ids:
        return

    if admin_ids:
        stmt = delete(Admin).where(
            (Admin.channel_id == channel_id) & (Admin.user_id.in_(admin_ids))
        )
    else:
        stmt = delete(Admin).where(Admin.channel_id == channel_id)

    await session.execute(stmt)


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


async def save_quiz_to_db(session: AsyncSession, data: QuizData) -> Quiz:
    quiz = Quiz(
        question=data["question"],
        correct=data["correct_index"],
        explanation=data["explanation"],
        user_id=data["user_id"],
        channel_id=data["channel"].id,
    )
    session.add(quiz)
    await session.flush()

    session.add_all(
        [
            Option(option=op, order=i, quiz_id=quiz.id)
            for i, op in enumerate(data["options"])
        ]
    )

    return quiz


def escape_markdown(text: str) -> str:
    escape_chars = r"_*[]()~`>#+-=|{}.!\\"
    return re.sub(f"([{re.escape(escape_chars)}])", r"\\\1", text)


def create_command_menu(commands: list[CommandInfo]) -> list[BotCommand]:
    return [
        BotCommand(command=cmd.command, description=cmd.description) for cmd in commands
    ]
