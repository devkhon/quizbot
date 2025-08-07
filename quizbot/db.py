import os

import dotenv
import redis.asyncio as redis_py
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

dotenv.load_dotenv()

engine = create_async_engine(os.getenv("POSTGRES_URL", ""))
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

redis = redis_py.from_url(os.getenv("REDIS_URL", ""), decode_responses=True)
