from aiogram import types
from constants import BOT_STATUS_MAPPING, USER_STATUS_MAPPING
from enums import (
    BotChangeType,
    BotMemberStatus,
    UserChangeType,
    UserMemberStatus,
)
from models import Admin, Channel, User
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession


def extract_user_new_status(update: types.ChatMemberUpdated) -> UserMemberStatus:
    match update.new_chat_member:
        case types.ChatMemberOwner():
            return UserMemberStatus.OWNER
        case types.ChatMemberAdministrator():
            return UserMemberStatus.ADMIN
        case types.ChatMemberMember():
            return UserMemberStatus.MEMBER
        case types.ChatMemberLeft():
            return UserMemberStatus.LEFT
        case types.ChatMemberBanned():
            return UserMemberStatus.BANNED
        case _:
            raise ValueError(
                f"Unknown chat member type: {type(update.new_chat_member)}"
            )


def extract_bot_new_status(update: types.ChatMemberUpdated) -> BotMemberStatus:
    match update.new_chat_member:
        case types.ChatMemberAdministrator():
            return BotMemberStatus.ADMIN
        case types.ChatMemberLeft():
            return BotMemberStatus.LEFT
        case types.ChatMemberBanned():
            return BotMemberStatus.BANNED
        case _:
            raise ValueError(f"Unknown bot member type: {type(update.new_chat_member)}")


def detect_user_change(new_status: UserMemberStatus) -> UserChangeType:
    return USER_STATUS_MAPPING[new_status]


def detect_bot_change(new_status: BotMemberStatus) -> BotChangeType:
    return BOT_STATUS_MAPPING[new_status]


async def upsert_channel(session: AsyncSession, chat: types.Chat) -> Channel:
    old_channel = await session.get(Channel, chat.id)
    if old_channel:
        old_channel.title = chat.title
        old_channel.username = chat.username
        return old_channel

    new_channel = Channel(id=chat.id, title=chat.title, username=chat.username)
    session.add(new_channel)
    return new_channel


async def upsert_user(session: AsyncSession, user: types.User) -> User:
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
    session: AsyncSession, channel_id: int, admin_users: list[types.User]
) -> None:
    new_admins = []
    for admin_user in admin_users:
        if not admin_user.is_bot:
            user = await upsert_user(session, admin_user)
            new_admin = Admin(user_id=user.id, channel_id=channel_id)
            new_admins.append(new_admin)
    session.add_all(new_admins)


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
