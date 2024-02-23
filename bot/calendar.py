import calendar
from datetime import datetime, timedelta
from aiogram.types import (
    InlineKeyboardMarkup, 
    InlineKeyboardButton 
    )

def create_calendar(year=None, month=None):
    # Якщо рік або місяць не вказані, використовуємо поточний рік або місяць
    if year is None: year = datetime.now().year
    if month is None: month = datetime.now().month

    # Створюємо клавіатуру
    inline_kb = []

    # Додаємо кнопки для зміни місяця
    inline_kb.insert(0, [InlineKeyboardButton(text="<<", callback_data=f"calendar_month:{year}:{month-1}"),
                         InlineKeyboardButton(text=f"{calendar.month_name[month]} {year}", callback_data="ignore"),
                         InlineKeyboardButton(text=">>", callback_data=f"calendar_month:{year}:{month+1}")])

    # Додаємо кнопки для днів тижня
    days_of_week = ['пн', 'вт', 'ср', 'чт', 'пт', 'сб', 'нд']
    inline_kb.append([InlineKeyboardButton(text=day, callback_data="ignore") for day in days_of_week])

    # Визначаємо день тижня для першого числа місяця
    weekday_of_first, num_days_in_month = calendar.monthrange(year, month)
    # Враховуємо, що понеділок - це 1, а не 0
    weekday_of_first = (weekday_of_first) % 7  

    # Список для першого тижня місяця
    week = []

    # Додаємо пусті клітини для днів перед першим числом місяця
    for _ in range(weekday_of_first):
        week.append(InlineKeyboardButton(text=" ", callback_data="ignore"))

    # Додаємо кнопки для днів місяця
    for day in range(1, num_days_in_month+1):
        # Якщо день належить поточному місяцю, додаємо його до клавіатури
        text = f"({day})" if datetime(year, month, day).date() == datetime.now().date() else str(day)
        week.append(InlineKeyboardButton(text=text, callback_data=f"calendar_day:{year}:{month}:{day}"))
        
        # Якщо день належить поточному місяцю, додаємо його до клавіатури
        if len(week) == 7:
            inline_kb.append(week)
            week = []

    # Додаємо останній тиждень, якщо він не пустий
    if week:
        # Додаємо пусті кнопки для днів після останнього числа місяця
        week += [InlineKeyboardButton(text=" ", callback_data="ignore")]*(7-len(week))
        inline_kb.append(week)

    markup = InlineKeyboardMarkup(inline_keyboard=inline_kb)
    return markup
