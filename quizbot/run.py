import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from bot import bot, set_command_menus
from db import AsyncSessionLocal
from dispatcher import dp
from helpers import post_channel_quizzes


async def post_channel_quizzes_job() -> None:
    async with AsyncSessionLocal() as session:
        await post_channel_quizzes(session)


scheduler = AsyncIOScheduler()
scheduler.add_job(post_channel_quizzes_job, "interval", seconds=10)


async def on_start() -> None:
    await set_command_menus()
    scheduler.start()
    print("bot has been started....")


async def main() -> None:
    dp.startup.register(on_start)
    await dp.start_polling(bot)


asyncio.run(main())
