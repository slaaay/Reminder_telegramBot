from os import getenv
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Створюємо планувальник
scheduler = AsyncIOScheduler()

# Ініціалізація бота
load_dotenv()
TOKEN = getenv("BOT_TOKEN")

dp = Dispatcher(storage=MemoryStorage())
bot = Bot(TOKEN, parse_mode=ParseMode.HTML)
