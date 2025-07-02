import asyncio

from bot import bot, set_command_menus
from routers import dp


async def on_start() -> None:
    await set_command_menus()
    print("bot has been started....")


async def main() -> None:
    dp.startup.register(on_start)
    await dp.start_polling(bot)


asyncio.run(main())
