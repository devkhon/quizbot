import asyncio

from bot import bot, set_command_menus
from dispatcher import dp
from scheduler import scheduler, setup_scheduler


async def on_start() -> None:
    await set_command_menus()
    await setup_scheduler()
    scheduler.start()
    print("bot has been started....")


async def main() -> None:
    dp.startup.register(on_start)
    await dp.start_polling(bot)


asyncio.run(main())
