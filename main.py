#часть обработчиков перенёс в main потому что для создания deep link и обработки моих броней с кнопками приглашения нужно было в функцию создания ссылки передать бота как аргумент, а при импортировании в файл routers возникала ошибка, тут крч сохраняются юзеры участников
import time
import os
import pytz
import asyncio
import sqlite3
import base64
import datetime
from aiogram.filters import CommandStart, StateFilter
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import types, F
from aiogram.types import BotCommandScopeAllPrivateChats, InlineKeyboardButton
from aiogram.client.default import DefaultBotProperties
from aiogram import Bot, Dispatcher
from aiogram.enums.parse_mode import ParseMode
from aiogram.types import InlineQueryResultArticle, InputTextMessageContent, SwitchInlineQueryChosenChat
from aiogram.utils.deep_linking import create_start_link
from aiogram.fsm.strategy import FSMStrategy
from dotenv import load_dotenv, find_dotenv
from routers import main_router
from cmds import listt_private
from keyboards import *
from custom_calendar import CustomCalendar  # Ensure you import your custom calendar if needed

# Initialize the bot and dispatcher
bot = Bot(token='7488397512:AAHDWX4hukDGIV12QjBOK_2idSEPk5B-ZJY', default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(fsm_strategy=FSMStrategy.USER_IN_CHAT)

class username_storage():
    def __init__(self, participant_user, participant_id, booking_id):
        self.participant_user = participant_user
        self.participant_id = participant_id
        self.booking_id = booking_id

absolute_username_keeper = username_storage(None, None, None)



async def check_bookings():
    while True:
        notification = sqlite3.connect('datebase.db')
        notification_cursor = notification.cursor()
        notification_query = '''
                            SELECT hall, date, time_of_beginning, time_of_ending, booker_id, participants_id, username FROM user_booking_data
                        '''
        notification_cursor.execute(notification_query)
        notif_res = notification_cursor.fetchall()
        notification.commit()
        notification.close()
        print(notif_res)
        now = datetime.datetime.now()
        if now.month > 9:
            if now.day > 9:
                date = f'{now.day}/{now.month}'
            else:
                date = f'0{now.day}/{now.month}'
        else:
            if now.day > 9:
                date = f'{now.day}/0{now.month}'
            else:
                date = f'0{now.day}/0{now.month}'
        time = f'{now.hour}:{now.minute}'

        for i in notif_res:
            if date == i[1]:
                time_res = datetime.datetime.strptime(i[2], '%H:%M') - datetime.datetime.strptime(time, '%H:%M')
                fin_time_res = int(time_res.total_seconds())
                l = list(q.strip() for q in i[5].split(','))
                #Если до брони 2 часа либо 15 минут
                if fin_time_res == 7200 or fin_time_res == 900:
                    await bot.send_message(i[4], f'Напоминаю, у вас бронь:\nЗал: {i[0]} на {i[1]} с {i[2]} по {i[3]}')
                    if len(l) != 0:
                        for m in l:
                            await bot.send_message(chat_id=int(m), text=f'Напоминаю, вы приглашены на конференцию:\nЗал: {i[0]} на {i[1]} с {i[2]} по {i[3]} забронировал: {i[-1]}')
                else:
                    continue
            else:
                continue
        # Проверяем базу данных каждые 60 секунд
        await asyncio.sleep(60)



async def get_deep_link(payload):
    return await create_start_link(bot, payload, encode=True)

def decode_payload(payload):
    decoded_bytes = base64.urlsafe_b64decode(payload + '=' * (4 - len(payload) % 4))
    return decoded_bytes.decode('utf-8')

@dp.message(CommandStart(), StateFilter(None))
async def send_welcome(message: types.Message, command: CommandStart):
    if command.args:  # Проверка наличия аргументов
        await handle_deep_link(message, command.args)
        connection = sqlite3.connect('datebase.db')
        cursor = connection.cursor()
        query = '''
                SELECT participants FROM user_booking_data
                WHERE id = ?
                '''
        cursor.execute(query, (absolute_username_keeper.booking_id, ))
        result = cursor.fetchall()
        final_res = []
        for i in result:
            for g in i:
                final_res.append(g)
        if ' ' in final_res:
            query = '''
                    UPDATE user_booking_data 
                    SET participants = ?
                    WHERE id = ?
                    '''
            cursor.execute(query, (f'@{message.from_user.username}', absolute_username_keeper.booking_id))
            connection.commit()
            connection.close()
        else:
            s = ''
            for q in final_res:
                s += f'{q}, '
            query = '''
                    UPDATE user_booking_data
                    SET participants = ?
                    WHERE id = ?
                    '''
            cursor.execute(query, (f'{s} @{message.from_user.username}', absolute_username_keeper.booking_id))
            connection.commit()
            connection.close()

        id_conn = sqlite3.connect('datebase.db')
        id_cursor = id_conn.cursor()
        id_query = '''
                   SELECT participants_id FROM user_booking_data
                   WHERE id = ?
                   '''
        id_cursor.execute(id_query, (absolute_username_keeper.booking_id, ))
        id_res = id_cursor.fetchall()
        id_conn.commit()
        id_conn.close()
        id_res_list = []
        for s in id_res:
            for d in s:
                id_res_list.append(d)

        print(id_res_list)

        if ' ' in id_res_list:
            adding = sqlite3.connect('datebase.db')
            adding_cursor = adding.cursor()
            adding_query = '''
                           UPDATE user_booking_data
                           SET participants_id = ?
                           WHERE id = ?
                           '''
            adding_cursor.execute(adding_query, (str(message.chat.id), absolute_username_keeper.booking_id))
            adding.commit()
            adding.close()
        else:
            r = ''
            for t in id_res_list:
                r += f'{t},'
                print(r)
            ad = sqlite3.connect('datebase.db')
            ad_cursor = ad.cursor()
            ad_query = '''
                       UPDATE user_booking_data
                       SET participants_id = ?
                       WHERE id = ?
                       '''
            a = f'{r} {message.chat.id}'
            ad_cursor.execute(ad_query, (a, absolute_username_keeper.booking_id))
            ad.commit()
            ad.close()
        #столбец с участниками уже создан. Есть код чатгпт, его взять за основу, проверять, есть ли участники, если есть, то компоновать все в список, а потом в строку и сохранять в sql. Уведомления делать по айди, айди получать в этом же хэндлере через message. Создать еще один столбец с айди приглашенного. Сохранять и добавлять айди по такой же схеме, как и юзеры. Подправить запрос sql везде с выводом участников(это не сложно, нужно просто запросить еще один столбец и во время распаковки списка указать последний индекс эдемента и сохранить там как нибудь)
    else:
        await message.answer('Добро пожаловать!\nВыберите, что хотите сделать:', reply_markup=start_mark_up.as_markup(
        resize_keyboard=True,
        input_field_placeholder='Что хотите сделать?'
    ))

@dp.message(F.text == 'Мои брони:', StateFilter(None))
async def illustration_of_bookings(msg: types.Message):
    searching_query_showing = '''
                      SELECT hall, date, time_of_beginning, time_of_ending, id, participants FROM user_booking_data
                      WHERE username = ?
                      '''
    illustrate_connection = sqlite3.connect('datebase.db')
    cursor_showing_object = illustrate_connection.cursor()
    cursor_showing_object.execute(searching_query_showing, (f'@{msg.from_user.username}',))
    search_res = cursor_showing_object.fetchall()
    illustrate_connection.commit()
    illustrate_connection.close()

    if search_res:
        await msg.answer('Ваши брони:')
        for i in search_res:
            link = await get_deep_link(f'{i[4]}')
            keyboard = InlineKeyboardBuilder()
            keyboard.add(
                InlineKeyboardButton(
                    text='Пригласить участника',
                    switch_inline_query_chosen_chat=SwitchInlineQueryChosenChat(query=link, allow_user_chats=True, allow_bot_chats=True, allow_group_chats=True, allow_channel_chats=False))
                )
            await msg.answer(f'Зал: {i[0]}, на: {i[1]}, с: {i[2]}, по: {i[3]}\nУчастники: {i[-1]}', reply_markup=keyboard.as_markup())
    else:
        await msg.answer('У вас нет бронирований.')

async def handle_deep_link(message: types.Message, payload: str):
    decoded_payload = decode_payload(payload)
    identity = int(decoded_payload)
    absolute_username_keeper.booking_id = identity
    set_connection = sqlite3.connect('datebase.db')
    cursor = set_connection.cursor()
    query = '''
            SELECT hall, date, time_of_beginning, time_of_ending, username FROM user_booking_data
            WHERE id = ?
            '''
    cursor.execute(query, (identity, ))
    info = cursor.fetchall()
    set_connection.commit()
    set_connection.close()
    info_list = []
    for i in info:
        for g in i:
            info_list.append(g)
    await message.answer(f"Вы стали участником конференции:\nЗал: {info_list[0]}, На: {info_list[1]}, С: {info_list[2]}, По: {info_list[3]}, Забронировал: {info_list[4]}")

@dp.inline_query()
async def inline_query_handler(inline_query: types.InlineQuery):
    query_text = inline_query.query

    if query_text.startswith('http'):
        payload = query_text.split('start=')[1]
        decoded_payload = decode_payload(payload)
        results = [
            InlineQueryResultArticle(
                id='1',
                title=decoded_payload,
                input_message_content=InputTextMessageContent(message_text=query_text)
            )
        ]
        print(f"Results: {results}")
        await inline_query.answer(results)
    else:
        await inline_query.answer([])  # Отправить пустой ответ, если запрос не соответствует

# Include routers
dp.include_router(main_router)

async def main_func():
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.delete_my_commands(scope=BotCommandScopeAllPrivateChats())
    await bot.set_my_commands(commands=listt_private, scope=BotCommandScopeAllPrivateChats())
    asyncio.create_task(check_bookings())
    await dp.start_polling(bot)  # Start polling

if __name__ == '__main__':
    asyncio.run(main_func())