import asyncio

from bot import bot, set_command_menus
from db import AsyncSessionLocal
from dispatcher import dp
from helpers import setup_scheduler
from scheduler import scheduler


async def on_start() -> None:
    async with AsyncSessionLocal() as session:
        await setup_scheduler(session, scheduler)
    await set_command_menus()
    scheduler.start()
    print("bot has been started....")


async def main() -> None:
    dp.startup.register(on_start)
    await dp.start_polling(bot)


asyncio.run(main())
