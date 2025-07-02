from aiogram import Bot
from aiogram.types import BotCommandScopeAllPrivateChats
from config import settings
from type import CommandInfo

bot = Bot(settings.bot_token)

commands: list[CommandInfo] = [
    CommandInfo(command="start", description="start command"),
    CommandInfo(command="addquiz", description="addquiz command"),
]


async def set_command_menus() -> None:
    await bot.set_my_commands(commands, BotCommandScopeAllPrivateChats())
