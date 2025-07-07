import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from bot import bot, set_command_menus
from constants import POST_TIME, QUIZ_COUNT
from db import AsyncSessionLocal, redis
from dispatcher import dp
from helpers import get_all_active_channels, send_channel_quizzes
from sqlalchemy.ext.asyncio import AsyncSession
from type import ChannelSettings

scheduler = AsyncIOScheduler()


async def schedule_channel(sesssion: AsyncSession, channel_id: int) -> None:
    settings: ChannelSettings = await redis.hgetall(channel_id)
    post_time = settings.get("time") if settings.get("time") else POST_TIME
    quiz_count = (
        int(settings.get("quiz_count")) if settings.get("quiz_count") else QUIZ_COUNT
    )

    scheduler.add_job(
        send_channel_quizzes,
        CronTrigger(hour=post_time[0:2], minute=post_time[3:5]),
        args=[sesssion, channel_id, quiz_count],
        id=str(channel_id),
        replace_existing=True,
    )


async def on_start() -> None:
    await set_command_menus()

    async with AsyncSessionLocal() as session:
        channels = await get_all_active_channels(session)
        for channel in channels:
            await schedule_channel(session, channel.id)

    print("bot has been started....")


async def main() -> None:
    dp.startup.register(on_start)
    await dp.start_polling(bot)


asyncio.run(main())
