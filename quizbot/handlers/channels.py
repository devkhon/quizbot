import asyncio

from aiogram import Router
from aiogram.filters import ChatMemberUpdatedFilter
from aiogram.types import Chat, ChatMemberUpdated
from aiogram.types import User as TUser
from bot import bot
from constants import PROMOTED
from db import AsyncSessionLocal
from handlers.commands import upsert_user
from models import Admin, Channel
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

router = Router()


async def upsert_channel(session: AsyncSession, chat: Chat, active: bool) -> Channel:
    old_channel = await session.get(Channel, chat.id)
    if old_channel:
        old_channel.title = chat.title
        old_channel.username = chat.username
        old_channel.active = active
        return old_channel

    new_channel = Channel(
        id=chat.id, title=chat.title, username=chat.username, active=active
    )

    session.add(new_channel)
    return new_channel


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


async def handle_bot_join(event: ChatMemberUpdated) -> None:
    async with AsyncSessionLocal() as session:
        channel = await upsert_channel(session, event.chat, True)
        await asyncio.sleep(1)
        admins = await bot.get_chat_administrators(channel.id)
        admin_users = [admin.user for admin in admins]
        await add_channel_admins(session, channel.id, admin_users)
        await session.commit()


async def handle_bot_leave(event: ChatMemberUpdated) -> None:
    async with AsyncSessionLocal() as session:
        channel = await upsert_channel(session, event.chat, False)
        await delete_channel_admins(session, channel.id)
        await session.commit()


async def handle_user_promote(event: ChatMemberUpdated) -> None:
    user = event.new_chat_member.user
    async with AsyncSessionLocal() as session:
        await add_channel_admins(session, event.chat.id, [user])
        await session.commit()


async def handle_user_demote(event: ChatMemberUpdated) -> None:
    user = event.new_chat_member.user
    async with AsyncSessionLocal() as session:
        await delete_channel_admins(session, event.chat.id, [user.id])
        await session.commit()


router.my_chat_member.register(handle_bot_join, ChatMemberUpdatedFilter(PROMOTED))
router.my_chat_member.register(handle_bot_leave, ChatMemberUpdatedFilter(~PROMOTED))
router.chat_member.register(handle_user_promote, ChatMemberUpdatedFilter(PROMOTED))
router.chat_member.register(handle_user_demote, ChatMemberUpdatedFilter(~PROMOTED))
