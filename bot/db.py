import pytz
import logging
import psycopg2

from psycopg2 import sql

from os import getenv
from dotenv import load_dotenv

from datetime import datetime, timedelta

from bot.bot_setup import scheduler

load_dotenv()
WAY = getenv('DB_URL')

# Підключення до бази даних
conn = psycopg2.connect(WAY)

def add_event(chat_id, name, venue, action, date, time):
    from bot.bot_setup import bot

    logging.info(f"Adding event: {name}, chat_id: {chat_id}")
    # Функція для додавання події до бази даних
    with conn.cursor() as cursor:
        insert = sql.SQL("INSERT INTO events (chat_id, name, venue, action, date, time) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id")
        cursor.execute(insert, (chat_id, name, venue, action, date, time))
        event_id = cursor.fetchone()[0]  # Отримуємо ID нової події
    conn.commit()

    return event_id

def save_chat_id(chat_id):
    with conn.cursor() as cursor:
        cursor.execute("INSERT INTO chat_ids (chat_id) VALUES (%s) ON CONFLICT DO NOTHING", (chat_id,))
    conn.commit()

def delete_chat_id(chat_id):
    with conn.cursor() as cursor:
        cursor.execute("DELETE FROM chat_ids WHERE chat_id = %s", (chat_id,))
    conn.commit()

def get_all_chat_ids():
    with conn.cursor() as cursor:
        cursor.execute('SELECT chat_id FROM chat_ids')
        chat_ids = cursor.fetchall()
    return [chat_id[0] for chat_id in chat_ids]

def list_events():
    # Функція для отримання списку всіх подій з бази даних
    try:
        with conn.cursor() as cursor:
            select = sql.SQL("SELECT * FROM events")
            cursor.execute(select)
            events = cursor.fetchall()
        return events
    except psycopg2.InterfaceError:
        conn.rollback()
        logging.error("InterfaceError occurred in list_events function")
        return []
    except Exception as e:
        conn.rollback()
        logging.error(f"An error occurred in list_events function: {e}")
        return []

def delete_event(event_id):
    # Функція для видалення події з бази даних
    with conn.cursor() as cursor:
        delete = sql.SQL("DELETE FROM events WHERE id = %s")
        cursor.execute(delete, (event_id,))
    conn.commit()
    cursor.close()

def list_today_events():
    # Функція для отримання списку подій на сьогоднішній день з бази даних
    try:
        with conn.cursor() as cursor:
            select = sql.SQL("SELECT * FROM events WHERE date = CURRENT_DATE")
            cursor.execute(select)
            events = cursor.fetchall()
        return events
    except psycopg2.OperationalError as e:
        conn.rollback()
        logging.error(f"SSL connection error: {e}")
        return list_today_events()