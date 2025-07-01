import asyncio

from bot import bot
from routers import dp


def on_start() -> None:
    print("bot has been started....")


async def main() -> None:
    dp.startup.register(on_start)
    await dp.start_polling(bot)


asyncio.run(main())
