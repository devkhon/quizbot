from aiogram import Dispatcher, Router
from aiogram.enums import ChatType
from handlers.channels import router as events_router
from handlers.commands import router as commands_router
from helpers import ChatTypeFilter

user_router = Router()
user_router.message.filter(ChatTypeFilter(ChatType.PRIVATE))
user_router.include_router(commands_router)

channel_router = Router()
channel_router.message.filter(ChatTypeFilter(ChatType.CHANNEL))
channel_router.include_router(events_router)

dp = Dispatcher()
dp.include_router(user_router)
dp.include_router(channel_router)
