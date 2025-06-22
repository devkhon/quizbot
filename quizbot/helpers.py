from aiogram import types
from constants import ADMIN_ROLES, NON_ADMIN_ROLES
from enums import ChangeType
from models import Admin, Channel, User
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession


def detect_bot_change(update: types.ChatMemberUpdated) -> ChangeType:
    if isinstance(update.new_chat_member, ADMIN_ROLES):
        return ChangeType.BECAME_ADMIN
    elif isinstance(update.new_chat_member, NON_ADMIN_ROLES):
        return ChangeType.LEFT_ADMIN


def detect_user_change(update: types.ChatMemberUpdated) -> ChangeType | None:
    old_member = update.old_chat_member
    new_member = update.new_chat_member

    if isinstance(new_member, ADMIN_ROLES):
        return ChangeType.BECAME_ADMIN
    if isinstance(old_member, ADMIN_ROLES) and isinstance(new_member, NON_ADMIN_ROLES):
        return ChangeType.LEFT_ADMIN

    return None


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
