# main.py

import asyncio

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.utils import init_db, setup_logging
from bot.config import TOKEN
from bot.handlers import register_handlers
from bot.downloader import set_commands
from bot.utils import dp


init_db()


async def main() -> None:
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    register_handlers(dp)
    await set_commands(bot)
    await dp.start_polling(bot)

if __name__ == "__main__":
    setup_logging()
    asyncio.run(main())
