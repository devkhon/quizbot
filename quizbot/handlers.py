import asyncio

from aiogram import types
from bot import bot
from db import get_session
from enums import ChangeType
from helpers import (
    add_channel_admins,
    delete_channel_admins,
    detect_bot_change,
    detect_user_change,
    upsert_channel,
)


async def start_handler(message: types.Message) -> None:
    await message.answer("Hello World!")


async def handle_bot_status_change(update: types.ChatMemberUpdated) -> None:
    change_type = detect_bot_change(update)

    async for session in get_session():
        channel = await upsert_channel(session, update.chat)
        if change_type == ChangeType.BECAME_ADMIN:
            await asyncio.sleep(1)
            admins = await bot.get_chat_administrators(channel.id)
            admin_users = [admin.user for admin in admins]
            await add_channel_admins(session, channel.id, admin_users)
        elif change_type == ChangeType.LEFT_ADMIN:
            await delete_channel_admins(session, channel.id)

        await session.commit()


async def handle_user_status_change(update: types.ChatMemberUpdated) -> None:
    change_type = detect_user_change(update)
    user = update.new_chat_member.user

    if change_type is None:
        return

    async for session in get_session():
        if change_type == ChangeType.BECAME_ADMIN:
            await add_channel_admins(session, update.chat.id, [user])
        elif change_type == ChangeType.LEFT_ADMIN:
            await delete_channel_admins(session, update.chat.id, [user.id])

        await session.commit()
