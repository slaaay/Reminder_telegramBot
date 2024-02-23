import asyncio
import logging

from aiogram import Dispatcher

from config import DEFAULT_TIMEZONE
from bot.bot_setup import bot, dp, scheduler

from bot.handlers import handlers
from bot.handlers.handlers import form_router
from bot.handlers.reminder import daily_reminder, schedule_send_reminder

from datetime import datetime

# Планувальник подій
scheduler.configure(timezone=DEFAULT_TIMEZONE)

def register_routers(dp: Dispatcher) -> None:
    dp.include_router(form_router)

async def main() -> None:

    # Додавання задач в планувальник
    scheduler.add_job(daily_reminder, 'cron', hour=6, minute=0, second=0)
    # Запуск планувальника
    scheduler.start()

    # Реєстрація роутерів
    register_routers(dp)

    #start bot polling
    await dp.start_polling(bot)

    # Keep the bot running indefinitely
    try:
        while True:
            await asyncio.sleep(60)
    except KeyboardInterrupt:
        print('Bot is stopping...')
    finally:
        print('Bot has stopped')

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
