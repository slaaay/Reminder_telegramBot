from aiogram.filters.state import StatesGroup, State

class EventForm(StatesGroup):
    name = State()
    venue = State()
    action = State()
    date = State()
    time = State()
