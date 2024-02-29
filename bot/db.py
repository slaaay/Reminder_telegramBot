import pytz
import asyncio
import asyncpg
import logging
import psycopg2

from psycopg2 import sql

from time import sleep
from datetime import datetime, timedelta

from bot.bot_setup import scheduler, WAY

class DatabaseManager:
    def __init__(self, WAY):
        self.WAY = WAY
        self.conn = None

    async def create_connection(self):
        self.conn = await asyncpg.connect(self.WAY)

    async def add_event(self, chat_id, name, venue, action, date, time_part_str):        
        time_part = datetime.strptime(time_part_str, '%H:%M').time()

        query = "INSERT INTO events (chat_id, name, venue, action, date, time) VALUES ($1, $2, $3, $4, $5, $6) RETURNING id"
        event_id = await self.conn.fetchval(query, chat_id, name, venue, action, date, time_part)
        return event_id

    # Функція для отримання усього списку подій з бази даних
    async def list_events(self):
        if self.conn is None:
            await self.create_connection()
        try:
            events = await self.conn.fetch("SELECT * FROM events")
            return events
        except Exception as e:
            logging.error(f"An error occurred in list_events function: {e}")
            return []

    async def save_chat_id(self, chat_id):
        if self.conn is None:
            await self.create_connection()  # Ensure connection is established
        async with self.conn.transaction():
            await self.conn.execute("INSERT INTO chat_ids (chat_id) VALUES ($1) ON CONFLICT DO NOTHING", chat_id)

    async def delete_chat_id(self, chat_id):
        if self.conn is None:
            await self.create_connection()  # Ensure connection is established
        async with self.conn.transaction():
            await self.conn.execute("DELETE FROM chat_ids WHERE chat_id = $1", chat_id)

    async def get_all_chat_ids(self):
        if self.conn is None:
            await self.create_connection()  # Ensure connection is established
        async with self.conn.transaction():
            rows = await self.conn.fetch('SELECT chat_id FROM chat_ids')
            return [row['chat_id'] for row in rows]

    async def delete_event(self, event_id):
        if self.conn is None:
            await self.create_connection()  # Ensure connection is established
        async with self.conn.transaction():
            await self.conn.execute("DELETE FROM events WHERE id = $1", event_id)

    # Функція для отримання списку подій на сьогоднішній день з бази даних
    async def list_today_events(self):
        if self.conn is None:
            await self.create_connection()
        try:
            events = await self.conn.fetch("SELECT * FROM events WHERE date = CURRENT_DATE")
            return events
        except Exception as e:
            logging.error(f"An error occurred in list_today_events function: {e}")
            return []
            
# Ініціалізація DatabaseManager
db_manager = DatabaseManager(WAY)

# Продовжуємо операцію для list_events , list_today_events
async def check_events_periodically():
    while True:
        today_events = await db_manager.list_today_events()
        events = await db_manager.list_events()
        print(today_events)
        print(events)
        await asyncio.sleep(3600)  # Check for events every hour
