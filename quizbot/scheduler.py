from collections.abc import Sequence

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from bot import send_channel_quizzes
from constants import POST_TIME, QUIZ_COUNT, TIMEZONE
from db import AsyncSessionLocal, redis
from models import Channel
from sqlalchemy import select
from type import ChannelSettings

scheduler = AsyncIOScheduler()


async def get_all_active_channels() -> Sequence[Channel]:
    async with AsyncSessionLocal() as session:
        stmt = select(Channel).where(Channel.active)
        channels: Sequence[Channel] = (await session.scalars(stmt)).all()
    return channels


async def schedule_channel(channel_id: int) -> None:
    settings: ChannelSettings = await redis.hgetall(channel_id)
    post_time = settings.get("time") if settings.get("time") else POST_TIME
    quiz_count = (
        int(settings.get("quiz_count")) if settings.get("quiz_count") else QUIZ_COUNT
    )

    scheduler.add_job(
        send_channel_quizzes,
        CronTrigger(
            hour=post_time[0:2],
            minute=post_time[3:5],
            timezone=TIMEZONE,
        ),
        args=[channel_id, quiz_count],
        id=str(channel_id),
        replace_existing=True,
    )


async def setup_scheduler() -> None:
    channels = await get_all_active_channels()
    for channel in channels:
        await schedule_channel(channel.id)
