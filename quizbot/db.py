import redis.asyncio as redis_py
from config import settings
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

engine = create_async_engine(settings.postgres_url)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

redis = redis_py.from_url(settings.redis_url)
