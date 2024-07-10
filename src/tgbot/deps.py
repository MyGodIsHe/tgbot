from contextlib import asynccontextmanager
from typing import AsyncIterator
from aiohttp import ClientSession
import asyncpg
import httpx
from simple_settings import settings
from openai import AsyncOpenAI
from statsd import StatsClient

from tgbot.registry import RegistryValue


db = RegistryValue[asyncpg.Pool]()
http_client = RegistryValue[ClientSession]()
openai_client = RegistryValue[AsyncOpenAI]()
telemetry = RegistryValue[StatsClient]()


@asynccontextmanager
async def use_db() -> AsyncIterator[asyncpg.Pool]:
    async with asyncpg.create_pool(settings.POSTGRES_DSN) as pool:
        db.set(pool)
        yield pool


@asynccontextmanager
async def use_http_client() -> AsyncIterator[ClientSession]:
    async with ClientSession() as client:
        http_client.set(client)
        yield client


@asynccontextmanager
async def use_openai_client() -> AsyncIterator[AsyncOpenAI]:
    client = AsyncOpenAI(
        api_key=settings.OPENAI_API_KEY,
        http_client=httpx.AsyncClient(
            base_url=settings.OPENAI_BASE_URL,
            proxy=settings.PROXY,
            follow_redirects=True,
            timeout=httpx.Timeout(timeout=60.0),
        )
    )
    openai_client.set(client)
    try:
        yield client
    finally:
        await client.close()


@asynccontextmanager
async def use_telemetry() -> AsyncIterator[StatsClient]:
    c = StatsClient(host=settings.STATSD_HOST, prefix=settings.STATSD_PREFIX)
    telemetry.set(c)
    try:
        yield c
    finally:
        c.close()


@asynccontextmanager
async def use_all() -> AsyncIterator[None]:
    async with (use_db(), use_http_client(), use_openai_client(), use_telemetry()):
        yield
