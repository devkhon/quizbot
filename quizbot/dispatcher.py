from aiogram import Dispatcher
from aiogram.filters import CommandStart
from handlers import command_start, handle_bot_status_change, handle_user_status_change

dp = Dispatcher()


dp.message.register(command_start, CommandStart())
dp.my_chat_member.register(handle_bot_status_change)
dp.chat_member.register(handle_user_status_change)
