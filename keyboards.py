from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

start_mark_up = ReplyKeyboardBuilder()
start_mark_up.add(
    KeyboardButton(text='Забронировать зал'),
    KeyboardButton(text='Перенести бронь'),
    KeyboardButton(text='Отменить бронь'),
    KeyboardButton(text='Мои брони:')
)
start_mark_up.adjust(1, 2, 1)

contact_asker = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Отправить контакт', request_contact=True)]
    ],
    resize_keyboard=True,
)

# conference_booking_mark_up = ReplyKeyboardMarkup(
#     keyboard=[
#         [
#             KeyboardButton(text='Зал Альфа'),
#             KeyboardButton(text='Зал Бета'),
#             KeyboardButton(text='Зал Гамма')
#         ]
#     ],
#     resize_keyboard=True,
#     input_field_placeholder='Бронирование:'
# )

conference_booking_mark_up = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text='Зал Северный')
        ]
    ],
    resize_keyboard=True,
    input_field_placeholder='Бронирование:'
)