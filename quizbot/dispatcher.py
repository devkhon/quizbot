from aiogram import Dispatcher
from aiogram.filters import CommandStart
from handlers import handle_bot_status_change, handle_user_status_change, start_handler

dp = Dispatcher()


dp.message.register(start_handler, CommandStart())
dp.my_chat_member.register(handle_bot_status_change)
dp.chat_member.register(handle_user_status_change)
