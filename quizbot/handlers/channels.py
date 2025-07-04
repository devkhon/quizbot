import asyncio

from aiogram import Router
from aiogram.filters import ChatMemberUpdatedFilter
from aiogram.types import ChatMemberUpdated
from bot import bot
from constants import PROMOTED
from db import AsyncSessionLocal
from helpers import add_channel_admins, delete_channel_admins, upsert_channel

router = Router()


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
