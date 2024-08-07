# custom_calendar.py
from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import datetime

class CustomCalendar(SimpleCalendar):
    def __init__(self, locale: str = 'en_US', min_date: datetime.date = None):
        super().__init__(locale=locale)
        self.min_date = min_date or datetime.date.today()

    def get_month_buttons(self, year: int, month: int) -> InlineKeyboardMarkup:
        keyboard = InlineKeyboardMarkup(row_width=7)
        # Add previous and next month buttons
        keyboard.add(
            InlineKeyboardButton(text='◀️', callback_data=self.get_callback_data('prev_month', year, month)),
            InlineKeyboardButton(text='▶️', callback_data=self.get_callback_data('next_month', year, month))
        )
        # Add weekday headers
        keyboard.add(*[InlineKeyboardButton(day, callback_data='') for day in self.weekdays])

        # Get number of days in month
        days_in_month = (datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)).day

        # Create buttons for each day in the month
        for day in range(1, days_in_month + 1):
            current_date = datetime.date(year, month, day)
            if current_date >= self.min_date:
                keyboard.add(
                    InlineKeyboardButton(text=str(day), callback_data=self.get_callback_data('date', current_date))
                )


        return keyboard
