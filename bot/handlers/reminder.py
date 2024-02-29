import logging

from bot.db import DatabaseManager
from bot.bot_setup import scheduler, WAY

from config import DEFAULT_TIMEZONE
from datetime import datetime, timedelta

from aiogram.utils.markdown import hbold

from apscheduler.triggers.cron import CronTrigger

scheduler.configure(timezone=DEFAULT_TIMEZONE)

db_manager = DatabaseManager(WAY)

# Функція, яку ми хочемо виконувати щодня
async def daily_reminder():
    from bot.bot_setup import bot
    logging.info("Daily reminder function is called")
    
    chat_ids = await db_manager.get_all_chat_ids()  # Функція, яка отримує всі chat_id з бази даних

    for chat_id in chat_ids:
        try:
            # Отримуємо список подій для конкретного chat_id
            events = await db_manager.list_today_events()
            for event in events:
                # Надсилаємо повідомлення
                await bot.send_message(chat_id, f"{hbold("Назва:")} {event[1]} \n{hbold("Площа:")} {event[2]} \n{hbold("Дія:")} {event[3]} \n{hbold("Дата:")} {event[4]} {event[5]}")
        except Exception as e:
            logging.info(f"An error occurred: {e}")

def schedule_send_reminder(scheduler, chat_id, event_id, name, venue, action, event_datetime, bot):
        
    # Планувальник події на заданий час та дату
    scheduler.add_job(send_reminder, 'date', run_date=event_datetime, args=[chat_id, event_id, name, venue, action, event_datetime, bot])
    
    # Врахування відправленни за годину до 
    one_hour_before = event_datetime - timedelta(hours=1)
    
    # Планувальник події за годину до дати
    scheduler.add_job(send_reminder, 'date', run_date=one_hour_before, args=[chat_id, event_id, name, venue, action, event_datetime, bot])

    logging.info(f"Adding reminder job with args: chat_id={chat_id}, event_id={event_id}, name={name}, venue={venue}, action={action}, event_datetime={event_datetime}")

async def send_reminder(chat_id, event_id, name, venue, action, event_datetime, bot):
    logging.info(f"Trying to send a reminder for event: {name}, chat_id: {chat_id}, event_id: {event_id}")
    chat_ids = await db_manager.get_all_chat_ids()  # Получаем список всех chat_id

    # Конвертуємо у формат без часового поясу для виводу
    naive_datetime = event_datetime.replace(tzinfo=None)
    formatted_datetime = naive_datetime.strftime('%Y-%m-%d %H:%M:%S')
    reminder_message = f"<b>Нагадування про подію!</b> \n\n<b>Назва:</b> {name} \n<b>Площа:</b> {venue} \n<b>Дія:</b> {action} \n<b>Дата:</b> {formatted_datetime} UTC"

    for chat_id in chat_ids:
        try:
            await bot.send_message(chat_id, reminder_message, parse_mode='HTML')
            logging.info(f"Message sent successfully to chat_id: {chat_id}")
        except Exception as e:
            logging.error(f"Failed to send message to chat_id {chat_id}: {e}")

