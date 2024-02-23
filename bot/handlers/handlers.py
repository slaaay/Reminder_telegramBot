import re
import pytz
import logging

from os import getenv
from dotenv import load_dotenv

from aiogram import F, Bot, Dispatcher, types, Router
from aiogram.enums import ParseMode
from aiogram.types import CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.markdown import hbold
from aiogram.utils.keyboard import InlineKeyboardButton, InlineKeyboardMarkup

from config import DEFAULT_TIMEZONE
from datetime import datetime

from bot.db import add_event, list_events, delete_event, list_today_events, save_chat_id, delete_chat_id
from bot.states import EventForm
from bot.calendar import create_calendar
from bot.bot_setup import bot, dp
from bot.handlers.reminder import schedule_send_reminder

form_router = Router()

@dp.message(Command("notifications"))
async def cmd_notify(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="ON", callback_data="notify_on")],
        [InlineKeyboardButton(text="OFF", callback_data="notify_off")]
    ])
    await message.answer("Ви хочете включити нагадування?", reply_markup=keyboard)

@dp.callback_query(lambda c: c.data == "notify_on")
async def notifications_on(callback_query: types.CallbackQuery):
    chat_id = callback_query.message.chat.id
    save_chat_id(chat_id)  # Зберігаємо chat_id в базі даних
    await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)
    await callback_query.message.answer("Ви успішно включили нагадування.")
    await callback_query.answer()

@dp.callback_query(lambda c: c.data == "notify_off")
async def notifications_off(callback_query: types.CallbackQuery):
    chat_id = callback_query.message.chat.id
    delete_chat_id(chat_id)  # Видаляємо chat_id з бази даних
    await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)
    await callback_query.message.answer("Ви успішно виключили нагадування.")
    await callback_query.answer()

# Хендлер для команди /start
@dp.message(Command('start'))
async def cmd_start(message: types.Message):
    await message.answer("Вітаю! Я бот для створення подій. Бажаєте створити подію? - скористуйтесь командою /event .")

# Хендлер для команди /cancel
@form_router.message(Command("cancel"))
@form_router.message(F.text.casefold() == "cancel")
async def cancel_handler(message: types.Message, state: FSMContext) -> None:

    current_state = await state.get_state()
    if current_state is None:
        return

    logging.info("Cancelling state %r", current_state)
    await state.clear()
    await message.answer(
        "Відмінено."
    )

# Хендлер для команди /event
@form_router.message(Command('event'))
async def create_event(message: types.Message, state: FSMContext) -> None:
    await state.set_state(EventForm.name)
    await message.answer("Введіть назву події")

# Хендлер для обробки назви події
@form_router.message(EventForm.name)
async def process_name(message: types.Message, state: FSMContext) -> None:
    await state.update_data(name=message.text)
    await state.set_state(EventForm.venue)
    await message.answer("Введіть площу")

# Хендлер для обробки площадки
@form_router.message(EventForm.venue)
async def process_venue(message: types.Message, state: FSMContext) -> None:
    await state.update_data(venue=message.text)
    await state.set_state(EventForm.action)
    await message.answer("Введіть дію")

# Хендлер для обробки дії
@form_router.message(EventForm.action)
async def process_action(message: types.Message, state: FSMContext) -> None:
    await state.update_data(action=message.text)
    await state.set_state(EventForm.date)
    calendar = create_calendar()
    await bot.send_message(chat_id=message.chat.id, text="Будь ласка, оберіть дату", reply_markup=calendar)

# Хендлер для обробки дати
@form_router.message(EventForm.date)
async def process_date(message: types.Message, state: FSMContext) -> None:
    # Створюємо клавіатуру календаря
    calendar = create_calendar()

    # Зберігаємо стан
    await state.set_state(EventForm.time)

    # Надсилаємо клавіатуру календаря
    await bot.send_message(chat_id=message.chat.id, text="Будь ласка, оберіть дату", reply_markup=calendar)

@form_router.callback_query(lambda c: c.data and c.data.startswith('calendar_month:'))
async def process_calendar_month(callback_query: types.CallbackQuery, state: FSMContext):
    # Витягуємо номер року, місяця з callback_data
    year, month = map(int, callback_query.data.split(':')[1:])

    # Перевіряємо, чи місяць виходить за межі 1-12
    if month < 1:
        month = 12
        year -= 1
    elif month > 12:
        month = 1
        year += 1

    # Створюємо нову клавіатуру календаря для вибраного місяця
    calendar = create_calendar(year, month)

    # Надсилаємо клавіатуру календаря
    await bot.edit_message_text(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id, text="Будь ласка, виберіть дату", reply_markup=calendar)


@form_router.callback_query(lambda c: c.data and c.data.startswith('calendar_day:'))
async def process_calendar_date(callback_query: types.CallbackQuery, state: FSMContext):
    # Виводимо інформацію для налагодження
    logging.info(f"Processing calendar date callback query: {callback_query.data}")
    
    # Витягуємо номер року, місяця та дня з callback_data
    data = callback_query.data.split(':')
    if len(data) >= 4:
        year = int(data[1])
        month = int(data[2])
        day = int(data[3])

    # Зберігаємо дату в стані
    await state.update_data(year=year, month=month, day=day)
    data = await state.get_data()

    # Створюємо об'єкт datetime з збереженої дати
    date = datetime(year=data['year'], month=data['month'], day=day)
    await state.update_data(date=date)
    # Форматуємо дату
    formatted_date = date.strftime('%Y-%m-%d')
    
    # Відповідаємо на callback_query
    await bot.answer_callback_query(callback_query.id)
    
    # Відредагуємо існуюче повідомлення, щоб показати вибрану дату і прибрати клавіатуру
    await bot.edit_message_text(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id, text=f"Дата події: {formatted_date}", reply_markup=None)

    # Зберігаємо стан
    await state.set_state(EventForm.time)
    await bot.send_message(chat_id=callback_query.message.chat.id, text="Введіть час у форматі HH:MM (UTC)", reply_markup=types.ReplyKeyboardRemove())


# Хендлер для обробки часу
@form_router.message(EventForm.time)
async def process_time(message: types.Message, state: FSMContext) -> None:
    # Регулярний вираз для перевірки часу у форматі HH:MM
    time_pattern = re.compile(r'^([01]?[0-9]|2[0-3]):([0-5][0-9])$')
    
    if not time_pattern.match(message.text):
        # Якщо час не відповідає шаблону, просимо користувача ввести час знову
        await message.answer("Неправильний формат часу. Будь ласка, введіть час у форматі HH:MM (UTC).")
        return

    await state.update_data(time=message.text)
    await finalize_event_creation(message, state)


# Assuming this handler is called after all event details have been collected
async def finalize_event_creation(message: types.Message, state: FSMContext):
    from bot.bot_setup import scheduler

    data = await state.get_data()
    chat_id = message.chat.id
    
    # data['date'] вже є об'єктом datetime.date, і data['time'] - це рядок, наприклад "15:30"
    date_part = data['date']
    time_part_str = data['time']
    time_part = datetime.strptime(time_part_str, '%H:%M').time()

    await message.answer("Подія додана! /event_list - переглянути всі події")

    # Комбінування дати і часу в один об'єкт datetime
    event_datetime = datetime.combine(date_part, time_part).replace(tzinfo=DEFAULT_TIMEZONE)
    
    try:
        event_id = add_event(chat_id, data['name'], data['venue'], data['action'], data['date'], data['time'])
        logging.info(f"Event added successfully: {event_id}")
    except Exception as e:
        logging.error(f"Failed to add event for chat_id {chat_id}: {e}")   

    # Додавання події до календаря
    schedule_send_reminder(scheduler, chat_id, event_id, data['name'], data['venue'], data['action'], event_datetime, bot)    
    await state.clear()     

# Хендлер для команди /event_list
@form_router.message(Command('event_list'))
async def list_events_handler(message: types.Message):
    events = list_events()  # Assuming this function returns a list of event tuples
    if not events:
        await message.answer("Список подій порожній. Бажаєте додати подію /event ?")
        return
    for index, event in enumerate(events, start=1):
        # Форматування дати та часу для кожної події
        datetime_with_tz = datetime.combine(event[4], event[5]).replace(tzinfo=DEFAULT_TIMEZONE)
        formatted_datetime = datetime_with_tz.strftime('%Y-%m-%d %H:%M')
        buttons = [
            InlineKeyboardButton(text="Видалити", callback_data=f"delete_{event[0]}")
        ]
        markup = InlineKeyboardMarkup(inline_keyboard=[buttons])
        await message.answer(f"{index}. {hbold('Назва:')} {event[1]} \n{hbold('Площа:')} {event[2]} \n{hbold('Дія:')} {event[3]} \n{hbold('Дата:')} {formatted_datetime} UTC", reply_markup=markup)


@form_router.callback_query(lambda c: c.data and c.data.startswith('delete_'))
async def process_delete(callback_query: types.CallbackQuery):
    event_id = callback_query.data.split('_')[1]
    buttons = [
        InlineKeyboardButton(text="Так", callback_data=f"confirm_delete_{event_id}"),
        InlineKeyboardButton(text="Ні", callback_data=f"cancel_delete_{event_id}")
    ]
    markup = InlineKeyboardMarkup(inline_keyboard=[buttons])
    await bot.send_message(callback_query.from_user.id, "Ви дійсно хочете видалити подію?", reply_markup=markup)

@form_router.callback_query(lambda c: c.data and c.data.startswith('confirm_delete_'))
async def process_confirm_delete(callback_query: types.CallbackQuery):
    event_id = callback_query.data.split('_')[2]
    delete_event(event_id)
    # Видалити попереднє повідомлення
    await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)
    await bot.send_message(callback_query.from_user.id, f"Подія видалена")

@form_router.callback_query(lambda c: c.data and c.data.startswith('cancel_delete_'))
async def process_cancel_delete(callback_query: types.CallbackQuery):
    # Видалити попереднє повідомлення
    await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)
    await bot.send_message(callback_query.from_user.id, "Видалення скасовано")

# Хендлер для команди /event_day
@form_router.message(Command('event_day'))
async def list_today_events_handler(message: types.Message):
    events = list_today_events()
    # Check if there are no events for today
    if not events:
        await message.answer("Список подій на сьогодні порожній.\nБажаєте додати подію /event ?")
        return  # Exit the function early

    for event in events:
        # Форматування дати та часу
        datetime_with_tz = datetime.combine(event[4], event[5]).replace(tzinfo=DEFAULT_TIMEZONE)
        formatted_datetime = datetime_with_tz.strftime('%Y-%m-%d %H:%M')
        await message.answer(f"{hbold("Назва:")} {event[1]} \n{hbold("Площа:")} {event[2]} \n{hbold("Дія:")} {event[3]} \n{hbold("Дата:")} {formatted_datetime} UTC")
