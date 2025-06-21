import asyncio

from aiogram import types
from bot import bot
from db import get_session
from enums import BotChangeType
from helpers import (
    add_channel_admins,
    delete_channel_admins,
    detect_bot_change,
    extract_bot_new_status,
    upsert_channel,
)


async def start_handler(message: types.Message) -> None:
    await message.answer("Hello World!")


async def my_chat_member_handler(update: types.ChatMemberUpdated) -> None:
    new_status = extract_bot_new_status(update)
    change_type = detect_bot_change(new_status)

    async for session in get_session():
        channel = await upsert_channel(session, update.chat)
        if change_type == BotChangeType.BECAME_ADMIN:
            await asyncio.sleep(1)
            admins = await bot.get_chat_administrators(channel.id)
            admin_users = [admin.user for admin in admins]
            await add_channel_admins(session, channel.id, admin_users)
        elif change_type in {BotChangeType.LEFT, BotChangeType.BANNED}:
            await delete_channel_admins(session, channel.id)

        await session.commit()


async def chat_member_handler(update: types.ChatMemberUpdated) -> None:
    async for session in get_session():
        channel = await upsert_channel(session, update.chat)
        admin_members = await bot.get_chat_administrators(channel.id)
        await delete_channel_admins(session, channel)
        await add_channel_admins(session, channel, admin_members)
        await session.commit()
