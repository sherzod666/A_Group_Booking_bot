import datetime
import sqlite3
import asyncio
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import Router, types, F, Bot
from aiogram_calendar import SimpleCalendarCallback, SimpleCalendar
from aiogram.types import ReplyKeyboardRemove, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import or_f, Command, CommandStart, StateFilter
from aiogram.types import InlineQueryResultArticle, InputTextMessageContent, SwitchInlineQueryChosenChat
from aiogram.utils.deep_linking import create_start_link
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from keyboards import *

main_router = Router()

class booking_data():
    def __init__(self, user, number, hall, date, timer_first, timer_second, id, booker_id):
        self.user = user
        self.number = number
        self.hall = hall
        self.date = date
        self.timer_first = timer_first
        self.timer_second = timer_second
        self.id = id
        self.booker_id = booker_id


absolute_data = booking_data(None, None, None, None, None, None, None, None)


class FSM_conference(StatesGroup):
    phone = State()
    hall = State()
    date = State()
    timer_first = State()
    timer_second = State()
    elect = State()
    date_change = State()
    timer_first_change = State()
    timer_second_change = State()
    removing = State()


class id_storage():
    def __init__(self, id):
        self.id = id

id_keeper = id_storage(None)

calendar_keyboard = InlineKeyboardBuilder()

month_list = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
day_list = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', 
           '11', '12', '13', '14', '15', '16', '17', '18', '19', '20',
           '21', '22', '23', '24', '25', '26', '27', '28', '29', '30', '31']

now = datetime.datetime.today().date()
calendar_keyboard.add(InlineKeyboardButton(text=str(now.year), callback_data='year'))

for m in month_list:
    if m != now.strftime('%B'):
        continue
    else:
        calendar_keyboard.add(InlineKeyboardButton(text='<-', callback_data=f'{m}last_month {str(now.year)}'))
        calendar_keyboard.add(InlineKeyboardButton(text=m, callback_data='month'))
        calendar_keyboard.add(InlineKeyboardButton(text='->', callback_data=f'{m}next_month {str(now.year)}'))
        break

count = 0

if m == 'January' or m == 'March' or m == 'May' or m == 'July' or m == 'August' or m == 'October' or m == 'December':
    count = 31
else:
    if m == 'February':
        if int(now.year) % 4 == 0:
            count = 29
        else:
            count = 28
    else:
        count = 30

counter = 0
for d in day_list[0 : day_list.index(str(now.day))]:
    counter += 1
    calendar_keyboard.add(InlineKeyboardButton(text=' ', callback_data=' '))
for d in list(day_list[day_list.index(str(now.day)) : day_list.index(str(count)) + 1]):
    counter += 1
    v = str(now.day)  
    if d == v:
        calendar_keyboard.add(InlineKeyboardButton(text=f'[{d}]', callback_data=f'{str(now.year)}/{m}/{d}'))
    else:
        calendar_keyboard.add(InlineKeyboardButton(text=d, callback_data=f'{str(now.year)}/{m}/{d}'))

while counter % 7 != 0:
    counter += 1
    calendar_keyboard.add(InlineKeyboardButton(text=' ', callback_data=' '))
calendar_keyboard.add(InlineKeyboardButton(text='Главное меню', callback_data='return_to_main_menu'))
calendar_keyboard.adjust(1, 3, 7)

@main_router.callback_query(F.data == 'return_to_main_menu', StateFilter('*'))
async def callback_orderer(callback : CallbackQuery, state : FSMContext):
    await state.clear()
    await callback.answer()
    await callback.message.answer('Добро пожаловать!\nВыберите, что хотите сделать:', reply_markup=start_mark_up.as_markup(
        resize_keyboard=True,
        input_field_placeholder='Что хотите сделать?'
    ))



@main_router.message(F.text == 'Зал Северный', StateFilter(FSM_conference.hall))
async def select_hall(msg: types.Message, state: FSMContext):
    selected_hall = msg.text
    await state.update_data(Зал=selected_hall)
    await msg.answer('Зал выбран', reply_markup=ReplyKeyboardRemove())
    await msg.answer('Выберите дату:', reply_markup=calendar_keyboard.as_markup())
    await state.set_state(FSM_conference.date)






@main_router.message(F.text == 'Забронировать зал', StateFilter(None))
async def contacter(msg: types.Message, state: FSMContext):

    create = sqlite3.connect('datebase.db')
    create_cursor = create.cursor()
    create_query = '''
                       CREATE TABLE IF NOT EXISTS user_booking_data(
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            username TEXT,
                            telephone_number TEXT,
                            hall TEXT,
                            date TEXT,
                            time_of_beginning TEXT,
                            time_of_ending TEXT,
                            participants TEXT DEFAULT ' ',
                            participants_id TEXT DEFAULT ' ',
                            booker_id INTEGER
                       );
                       '''
    create_cursor.execute(create_query)
    create.commit()
    create.close()
    #Создание таблицы


    absolute_data.booker_id = msg.chat.id
    await state.update_data(Забронировал=f'@{msg.from_user.username}')
    connection = sqlite3.connect('datebase.db')
    cursor = connection.cursor()
    query = '''
            SELECT username FROM user_booking_data
            WHERE username = ?
            '''
    cursor.execute(query, (f'@{msg.from_user.username}',))
    result = cursor.fetchall()
    connection.commit()
    connection.close()
    res_list = []
    for q in result:
        for g in q:
            res_list.append(g)
    if f'@{msg.from_user.username}' not in res_list:
        await msg.answer('Отправьте, пожалуйста, свой номер телефона:', reply_markup=contact_asker)
        await state.set_state(FSM_conference.phone)
    else:
        connection = sqlite3.connect('datebase.db')
        cursor = connection.cursor()
        query = '''
                    SELECT telephone_number FROM user_booking_data
                    WHERE username = ?
                    '''
        cursor.execute(query, (f'@{msg.from_user.username}',))
        result_tuple = cursor.fetchone()
        result = ''
        for var in result_tuple:
            result = var
        connection.commit()
        connection.close()
        await state.update_data(Телефон=result)
        await msg.answer('Выберите зал, который хотите забронировать:', reply_markup=conference_booking_mark_up)
        await state.set_state(FSM_conference.hall)


@main_router.message(F.contact, StateFilter(FSM_conference.phone))
async def haller(msg: types.Message, state: FSMContext):
    await state.update_data(Телефон=msg.contact.phone_number)
    await msg.answer('Выберите зал, который хотите забронировать:', reply_markup=conference_booking_mark_up)
    await state.set_state(FSM_conference.hall)


@main_router.message(F.text == 'Зал #1', StateFilter(FSM_conference.hall))
async def orderer(msg: types.Message, state: FSMContext):
    await state.update_data(Зал=msg.text)
    await msg.answer('Зал выбран', reply_markup=ReplyKeyboardRemove())
    await msg.answer('Выберите дату:', reply_markup=calendar_keyboard.as_markup())
    await state.set_state(FSM_conference.date)
    
@main_router.callback_query(F.data.lower().contains('next_month'), StateFilter(FSM_conference.date))
async def next_month_func(callback : CallbackQuery, state : FSMContext):
    await callback.answer()
    await state.set_state(FSM_conference.date)
    calendar_keyboard = InlineKeyboardMarkup(inline_keyboard=
                                             [
                                                 []
                                             ])
    calendar_keyboard = InlineKeyboardBuilder()
    await callback.answer()
    res = callback.data.replace('next_month', '') #{m}next_month {y}
    mon = res[0 : res.index(' ')]
    month_list = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
    final_mon = 0
    for i in month_list:
        final_mon += 1
        if i == mon:
            final_mon += 1
            break
    if final_mon == 13:
        await callback.answer()
        return
    else:
        now = datetime.datetime(int(res[res.index(' ')+1:]), final_mon, 1)
        calendar_keyboard.add(InlineKeyboardButton(text=str(now.year), callback_data='year'))

        for m in month_list:
            if m != now.strftime('%B'):
                continue
            else:
                calendar_keyboard.add(InlineKeyboardButton(text='<-', callback_data=f'{m}last_month {str(now.year)}'))
                calendar_keyboard.add(InlineKeyboardButton(text=m, callback_data='month'))
                calendar_keyboard.add(InlineKeyboardButton(text='->', callback_data=f'{m}next_month {str(now.year)}'))
                break

        count = 0
    
        if now.month > datetime.datetime.today().month:
            if m == 'January' or m == 'March' or m == 'May' or m == 'July' or m == 'August' or m == 'October' or m == 'December':
                count = 31
            else:
                if m == 'February':
                    if int(now.year) % 4 == 0:
                        count = 29
                    else:
                        count = 28
                else:
                    count = 30

            counter = 0
            for d in day_list[0 : day_list.index(str(now.day))]:
                counter += 1
                calendar_keyboard.add(InlineKeyboardButton(text=' ', callback_data=' '))
            for d in list(day_list[day_list.index(str(now.day)) : day_list.index(str(count)) + 1]):
                counter += 1
                if d == v:
                    calendar_keyboard.add(InlineKeyboardButton(text=f'[{d}]', callback_data=f'{str(now.year)}/{m}/{d}'))
                else:
                    calendar_keyboard.add(InlineKeyboardButton(text=d, callback_data=f'{str(now.year)}/{m}/{d}'))

            while counter % 7 != 0:
                counter += 1
                calendar_keyboard.add(InlineKeyboardButton(text=' ', callback_data=' '))
            calendar_keyboard.adjust(1, 3, 7)

            await callback.message.edit_text('Календарь:', reply_markup=calendar_keyboard.as_markup())
            return
        elif now.month == datetime.datetime.today().month:
            calendar_keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        
                    ]
                ]
            )
            calendar_keyboard = InlineKeyboardBuilder()
            calendar_keyboard.add(InlineKeyboardButton(text=str(now.year), callback_data='year'))

            for m in month_list:
                if m != now.strftime('%B'):
                    continue
                else:
                    calendar_keyboard.add(InlineKeyboardButton(text='<-', callback_data=f'{m}last_month {str(now.year)}'))
                    calendar_keyboard.add(InlineKeyboardButton(text=m, callback_data='month'))
                    calendar_keyboard.add(InlineKeyboardButton(text='->', callback_data=f'{m}next_month {str(now.year)}'))
                    break

            count = 0

            if m == 'January' or m == 'March' or m == 'May' or m == 'July' or m == 'August' or m == 'October' or m == 'December':
                count = 31
            else:
                if m == 'February':
                    if int(now.year) % 4 == 0:
                        count = 29
                    else:
                        count = 28
                else:
                    count = 30

            counter = 0
            for d in day_list[0 : day_list.index(str(datetime.datetime.today().day))]:
                counter += 1
                calendar_keyboard.add(InlineKeyboardButton(text=' ', callback_data=' '))
            for d in list(day_list[day_list.index(str(datetime.datetime.today().day)) : day_list.index(str(count)) + 1]):
                counter += 1
                if d == v:
                    calendar_keyboard.add(InlineKeyboardButton(text=f'[{d}]', callback_data=f'{str(now.year)}/{m}/{d}'))
                else:
                    calendar_keyboard.add(InlineKeyboardButton(text=d, callback_data=f'{str(now.year)}/{m}/{d}'))

            while counter % 7 != 0:
                counter += 1
                calendar_keyboard.add(InlineKeyboardButton(text=' ', callback_data=' '))
            calendar_keyboard.adjust(1, 3, 7)
            await callback.message.edit_text('Календарь:', reply_markup=calendar_keyboard.as_markup())
            return
        elif now.month < datetime.datetime.today().month:
            for q in range(35):
                calendar_keyboard.add(InlineKeyboardButton(text=' ', callback_data=' '))
            calendar_keyboard.adjust(1, 3, 7)
            await callback.message.edit_text('Календарь:', reply_markup=calendar_keyboard.as_markup())
            return
            
@main_router.callback_query(F.data.lower().contains('last_month'), StateFilter(FSM_conference.date))
async def last_month_func(callback : CallbackQuery, state : FSMContext):
    await callback.answer()
    await state.set_state(FSM_conference.date)
    calendar_keyboard = InlineKeyboardMarkup(inline_keyboard=
                                             [
                                                 []
                                             ])
    calendar_keyboard = InlineKeyboardBuilder()
    await callback.answer()
    res = callback.data.replace('last_month', '') 
    mon = res[0 : res.index(' ')]
    month_list = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
    final_mon = 12
    for i in reversed(month_list):
        final_mon -= 1
        if i == mon:
            break
    if final_mon not in range(1, 13):
        await callback.answer()
        return
    else:
        now = datetime.datetime(int(res[res.index(' ')+1:]), final_mon, 1)
        calendar_keyboard.add(InlineKeyboardButton(text=str(now.year), callback_data='year'))

        for m in month_list:
            if m != now.strftime('%B'):
                continue
            else:
                calendar_keyboard.add(InlineKeyboardButton(text='<-', callback_data=f'{m}last_month {str(now.year)}'))
                calendar_keyboard.add(InlineKeyboardButton(text=m, callback_data='month'))
                calendar_keyboard.add(InlineKeyboardButton(text='->', callback_data=f'{m}next_month {str(now.year)}'))
                break

        count = 0

        if now.month > datetime.datetime.today().month:
            if m == 'January' or m == 'March' or m == 'May' or m == 'July' or m == 'August' or m == 'October' or m == 'December':
                count = 31
            else:
                if m == 'February':
                    if int(now.year) % 4 == 0:
                        count = 29
                    else:
                        count = 28
                else:
                    count = 30

            counter = 0
            for d in day_list[0 : day_list.index(str(now.day))]:
                counter += 1
                calendar_keyboard.add(InlineKeyboardButton(text=' ', callback_data=' '))
            for d in list(day_list[day_list.index(str(now.day)) : day_list.index(str(count)) + 1]):
                counter += 1
                if d == v:
                    calendar_keyboard.add(InlineKeyboardButton(text=f'[{d}]', callback_data=f'{str(now.year)}/{m}/{d}'))
                else:
                    calendar_keyboard.add(InlineKeyboardButton(text=d, callback_data=f'{str(now.year)}/{m}/{d}'))

            while counter % 7 != 0:
                counter += 1
                calendar_keyboard.add(InlineKeyboardButton(text=' ', callback_data=' '))
            calendar_keyboard.adjust(1, 3, 7)

            await callback.message.edit_text('Календарь:', reply_markup=calendar_keyboard.as_markup())
            return
        elif now.month == datetime.datetime.today().month:
            calendar_keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        
                    ]
                ]
            )
            calendar_keyboard = InlineKeyboardBuilder()
            calendar_keyboard.add(InlineKeyboardButton(text=str(now.year), callback_data='year'))

            for m in month_list:
                if m != now.strftime('%B'):
                    continue
                else:
                    calendar_keyboard.add(InlineKeyboardButton(text='<-', callback_data=f'{m}last_month {str(now.year)}'))
                    calendar_keyboard.add(InlineKeyboardButton(text=m, callback_data='month'))
                    calendar_keyboard.add(InlineKeyboardButton(text='->', callback_data=f'{m}next_month {str(now.year)}'))
                    break

            count = 0

            if m == 'January' or m == 'March' or m == 'May' or m == 'July' or m == 'August' or m == 'October' or m == 'December':
                count = 31
            else:
                if m == 'February':
                    if int(now.year) % 4 == 0:
                        count = 29
                    else:
                        count = 28
                else:
                    count = 30

            counter = 0
            for d in day_list[0 : day_list.index(str(datetime.datetime.today().day))]:
                counter += 1
                calendar_keyboard.add(InlineKeyboardButton(text=' ', callback_data=' '))
            for d in list(day_list[day_list.index(str(datetime.datetime.today().day)) : day_list.index(str(count)) + 1]):
                counter += 1
                if d == v:
                    calendar_keyboard.add(InlineKeyboardButton(text=f'[{d}]', callback_data=f'{str(now.year)}/{m}/{d}'))
                else:
                    calendar_keyboard.add(InlineKeyboardButton(text=d, callback_data=f'{str(now.year)}/{m}/{d}'))

            while counter % 7 != 0:
                counter += 1
                calendar_keyboard.add(InlineKeyboardButton(text=' ', callback_data=' '))
            calendar_keyboard.adjust(1, 3, 7)
            await callback.message.edit_text('Календарь:', reply_markup=calendar_keyboard.as_markup())
            return
        elif now.month < datetime.datetime.today().month:
            for q in range(35):
                calendar_keyboard.add(InlineKeyboardButton(text=' ', callback_data=' '))
            calendar_keyboard.adjust(1, 3, 7)
            await callback.message.edit_text('Календарь:', reply_markup=calendar_keyboard.as_markup())
            return

@main_router.callback_query(F.data == 'year')
@main_router.callback_query(F.data == 'month')
@main_router.callback_query(F.data == ' ')
async def skipper(callback : CallbackQuery):
    await callback.answer()      

@main_router.callback_query(F.data != ' ', StateFilter(FSM_conference.date))
async def date_getter(callback : CallbackQuery, state : FSMContext):
    await callback.answer()
    res = datetime.datetime.strptime(callback.data, '%Y/%B/%d')
    if res.month > 9:
        if res.day > 9:
            final_res = f'{res.year}/{res.day}/{res.month}'
        else:
            final_res = f'{res.year}/0{res.day}/{res.month}'
    else:
        if res.day > 9:
            final_res = f'{res.year}/{res.day}/0{res.month}'
        else:
            final_res = f'{res.year}/0{res.day}/0{res.month}'
    final_res = final_res[5:]
    await state.update_data(Дата=f'{final_res}')
    final_res_for_sql = datetime.datetime.strptime(final_res, '%d/%m')
    # Получение выбранного зала из состояния
    await state.update_data(Дата=final_res_for_sql.strftime('%d/%m'))
    hall = (await state.get_data()).get('Зал')

        # Get bookings for the selected date and hall
    connection = sqlite3.connect('datebase.db')
    cursor = connection.cursor()
    query = '''
            SELECT username, hall, date, time_of_beginning, time_of_ending 
            FROM user_booking_data
            WHERE date = ? AND hall = ?
        '''
    cursor.execute(query, (final_res_for_sql.strftime('%d/%m'), hall))
    bookings = cursor.fetchall()
    connection.close()

    if bookings:
        bookings_msg = '\n'.join(
            [f'Пользователь: {booking[0]}, Зал: {booking[1]}, Дата: {booking[2]}, С: {booking[3]}, По: {booking[4]}'
             for booking in bookings]
        )
        await callback.message.answer(f'Все брони на {final_res_for_sql.strftime("%d/%m")} для зала {hall}:\n{bookings_msg}')
    else:
        await callback.message.answer(f'На {final_res_for_sql.strftime("%d/%m")} для зала {hall} нет бронирований.')

        # Update time button with booked times
    time_buttons = await generate_time_buttons(final_res_for_sql.strftime('%d/%m'), hall)

    await callback.message.answer('Укажите время, когда начинается встреча:', reply_markup=time_buttons.as_markup())
    await state.set_state(FSM_conference.timer_first)
    

@main_router.callback_query(StateFilter(FSM_conference.timer_first))
async def beginning(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    try:
        res = datetime.datetime.strptime(callback.data, '%H:%M')
        final_res = res.strftime('%H:%M')
        await state.update_data(С=final_res)
        dictionary = await state.get_data()
        date = dictionary['Дата']
        hall = dictionary['Зал']

        # Update time button with booked times
        time_buttons = await generate_time_buttons(date, hall)
        await callback.message.edit_text('Укажите время, когда встреча заканчивается', reply_markup=time_buttons.as_markup())
        await state.set_state(FSM_conference.timer_second)
    except ValueError:
        await callback.message.answer('Некорректное время. Пожалуйста, выберите снова.')



@main_router.callback_query(StateFilter(FSM_conference.timer_second))
async def ending(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    try:
        res = datetime.datetime.strptime(callback.data, '%H:%M')
        final_res = res.strftime('%H:%M')
        await state.update_data(По=final_res)

        dictionary = await state.get_data()
        date = dictionary['Дата']
        start_time = dictionary['С']
        end_time = dictionary['По']
        hall = dictionary['Зал']

        # Check if the end time is earlier than the start time
        if datetime.datetime.strptime(end_time, '%H:%M') <= datetime.datetime.strptime(start_time, '%H:%M'):
            await callback.message.answer('Время окончания должно быть позже времени начала. Пожалуйста, выберите снова.',
                                         reply_markup=await generate_time_buttons(date, hall).as_markup())
            await state.set_state(FSM_conference.timer_first)  # Return to start time selection
            return

        connection = sqlite3.connect('datebase.db')
        cursor = connection.cursor()

        # Check for time conflicts
        check_conflict_query = '''
            SELECT id, username, telephone_number, time_of_beginning, time_of_ending 
            FROM user_booking_data
            WHERE hall = ? AND date = ? AND (
                (time_of_beginning < ? AND time_of_ending > ?) OR
                (time_of_beginning < ? AND time_of_ending > ?)
            )
        '''
        cursor.execute(check_conflict_query, (hall, date, end_time, start_time, end_time, start_time))
        conflicts = cursor.fetchall()

        if conflicts:
            conflict_messages = '\n'.join(
                [f'Забронировано пользователем {conflict[1]} с {conflict[3]} по {conflict[4]} (ID: {conflict[0]})'
                 for conflict in conflicts]
            )
            await callback.message.answer(
                f'Время уже занято.\nКонфликтующие брони:\n{conflict_messages}\nПожалуйста, выберите другое время.',
                reply_markup=await generate_time_buttons(date, hall).as_markup()
            )
            await callback.message.answer('Укажите время, когда начинается встреча:', reply_markup=await generate_time_buttons(date, hall).as_markup())
            await state.set_state(FSM_conference.timer_first)  # Return to start time selection
            return

        # Add booking to the database
        adding_query = '''
            INSERT INTO user_booking_data (username, telephone_number, hall, date, time_of_beginning, time_of_ending, booker_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        '''
        cursor.execute(adding_query, (dictionary['Забронировал'], dictionary['Телефон'], hall, date, start_time, end_time, absolute_data.booker_id))

        connection.commit()
        connection.close()

        await callback.message.answer(
            f'Забронировал: {dictionary["Забронировал"]}\nТелефонный номер: {dictionary["Телефон"]}\nЗал: {hall}\nДата: {date}\nС: {start_time}\nПо: {end_time}',
            reply_markup=start_mark_up.as_markup(
                resize_keyboard=True,
                input_field_placeholder='Что хотите сделать?'
            ))
        await state.clear()

    except ValueError:
        await callback.message.answer('Некорректное время. Пожалуйста, выберите снова.')




@main_router.message(F.text == 'Перенести бронь', StateFilter(None))
async def select_booking(msg: types.Message, state: FSMContext):
    connection_object = sqlite3.connect('datebase.db')
    cursor_object = connection_object.cursor()
    query = '''
        SELECT username FROM user_booking_data
    '''
    cursor_object.execute(query)
    res = cursor_object.fetchall()

    l = [r for i in res for r in i]

    if f'@{msg.from_user.username}' not in l:
        await msg.answer('Вы пока что ничего не бронировали', reply_markup=ReplyKeyboardRemove())
        return

    searching_query = '''
        SELECT hall, date, time_of_beginning, time_of_ending, id FROM user_booking_data
        WHERE username = ?
    '''
    cursor_object.execute(searching_query, (f'@{msg.from_user.username}',))
    search_res = cursor_object.fetchall()
    connection_object.commit()
    connection_object.close()

    count = 0

    bookings_mark_up = InlineKeyboardBuilder()
    for i in search_res:
        count += 1
        bookings_mark_up.add(
            InlineKeyboardButton(text=f'Зал: {i[0]}, на: {i[1]}, с: {i[2]}, по: {i[3]}', callback_data=f'id: {i[4]}'))
    bookings_mark_up.adjust(1)

    await msg.answer('Выберите бронь, которую хотите перенести:', reply_markup=ReplyKeyboardRemove())
    await msg.answer('Ваши брони:', reply_markup=bookings_mark_up.as_markup())
    await state.set_state(FSM_conference.elect)



@main_router.callback_query(StateFilter(FSM_conference.elect))
async def postpone_booking(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = callback.data.replace('id:', '').replace(' ', '')
    booking_id = int(data)
    id_keeper.id = booking_id
    # Получение данных о бронировании по ID
    connection = sqlite3.connect('datebase.db')
    cursor = connection.cursor()
    query = '''
        SELECT username, hall, date, time_of_beginning, time_of_ending, participants
        FROM user_booking_data
        WHERE id = ?
    '''
    cursor.execute(query, (booking_id,))
    booking = cursor.fetchone()
    connection.close()

    if booking:
        await state.update_data(Зал=booking[1])
        absolute_data.hall = booking[1]  # Сохранение выбранного зала
        absolute_data.id = booking_id  # Установка ID для дальнейшего использования

        await callback.message.answer(f'Вы перенесете бронь для:\nПользователь: {booking[0]}, Зал: {booking[1]}, Дата: {booking[2]}, С: {booking[3]}, По: {booking[4]}\nУчастники: {booking[-1]}')
        await callback.message.answer('Выберите новую дату:', reply_markup=calendar_keyboard.as_markup())
        await state.set_state(FSM_conference.date_change)
    else:
        await callback.message.answer('Ошибка: Бронь не найдена.')


@main_router.callback_query(F.data.lower().contains('next_month'), StateFilter(FSM_conference.date_change))
async def next_month_func(callback : CallbackQuery, state : FSMContext):
    await callback.answer()
    await state.set_state(FSM_conference.date_change)
    calendar_keyboard = InlineKeyboardMarkup(inline_keyboard=
                                             [
                                                 []
                                             ])
    calendar_keyboard = InlineKeyboardBuilder()
    await callback.answer()
    res = callback.data.replace('next_month', '') #{m}next_month {y}
    mon = res[0 : res.index(' ')]
    month_list = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
    final_mon = 0
    for i in month_list:
        final_mon += 1
        if i == mon:
            final_mon += 1
            break
    if final_mon == 13:
        await callback.answer()
        return
    else:
        now = datetime.datetime(int(res[res.index(' ')+1:]), final_mon, 1)
        calendar_keyboard.add(InlineKeyboardButton(text=str(now.year), callback_data='year'))

        for m in month_list:
            if m != now.strftime('%B'):
                continue
            else:
                calendar_keyboard.add(InlineKeyboardButton(text='<-', callback_data=f'{m}last_month {str(now.year)}'))
                calendar_keyboard.add(InlineKeyboardButton(text=m, callback_data='month'))
                calendar_keyboard.add(InlineKeyboardButton(text='->', callback_data=f'{m}next_month {str(now.year)}'))
                break

        count = 0
    
        if now.month > datetime.datetime.today().month:
            if m == 'January' or m == 'March' or m == 'May' or m == 'July' or m == 'August' or m == 'October' or m == 'December':
                count = 31
            else:
                if m == 'February':
                    if int(now.year) % 4 == 0:
                        count = 29
                    else:
                        count = 28
                else:
                    count = 30

            counter = 0
            for d in day_list[0 : day_list.index(str(now.day))]:
                counter += 1
                calendar_keyboard.add(InlineKeyboardButton(text=' ', callback_data=' '))
            for d in list(day_list[day_list.index(str(now.day)) : day_list.index(str(count)) + 1]):
                counter += 1
                if d == v:
                    calendar_keyboard.add(InlineKeyboardButton(text=f'[{d}]', callback_data=f'{str(now.year)}/{m}/{d}'))
                else:
                    calendar_keyboard.add(InlineKeyboardButton(text=d, callback_data=f'{str(now.year)}/{m}/{d}'))

            while counter % 7 != 0:
                counter += 1
                calendar_keyboard.add(InlineKeyboardButton(text=' ', callback_data=' '))
            calendar_keyboard.adjust(1, 3, 7)

            await callback.message.edit_text('Календарь:', reply_markup=calendar_keyboard.as_markup())
            return
        elif now.month == datetime.datetime.today().month:
            calendar_keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        
                    ]
                ]
            )
            calendar_keyboard = InlineKeyboardBuilder()
            calendar_keyboard.add(InlineKeyboardButton(text=str(now.year), callback_data='year'))

            for m in month_list:
                if m != now.strftime('%B'):
                    continue
                else:
                    calendar_keyboard.add(InlineKeyboardButton(text='<-', callback_data=f'{m}last_month {str(now.year)}'))
                    calendar_keyboard.add(InlineKeyboardButton(text=m, callback_data='month'))
                    calendar_keyboard.add(InlineKeyboardButton(text='->', callback_data=f'{m}next_month {str(now.year)}'))
                    break

            count = 0

            if m == 'January' or m == 'March' or m == 'May' or m == 'July' or m == 'August' or m == 'October' or m == 'December':
                count = 31
            else:
                if m == 'February':
                    if int(now.year) % 4 == 0:
                        count = 29
                    else:
                        count = 28
                else:
                    count = 30

            counter = 0
            for d in day_list[0 : day_list.index(str(datetime.datetime.today().day))]:
                counter += 1
                calendar_keyboard.add(InlineKeyboardButton(text=' ', callback_data=' '))
            for d in list(day_list[day_list.index(str(datetime.datetime.today().day)) : day_list.index(str(count)) + 1]):
                counter += 1
                if d == v:
                    calendar_keyboard.add(InlineKeyboardButton(text=f'[{d}]', callback_data=f'{str(now.year)}/{m}/{d}'))
                else:
                    calendar_keyboard.add(InlineKeyboardButton(text=d, callback_data=f'{str(now.year)}/{m}/{d}'))

            while counter % 7 != 0:
                counter += 1
                calendar_keyboard.add(InlineKeyboardButton(text=' ', callback_data=' '))
            calendar_keyboard.adjust(1, 3, 7)
            await callback.message.edit_text('Календарь:', reply_markup=calendar_keyboard.as_markup())
            return
        elif now.month < datetime.datetime.today().month:
            for q in range(35):
                calendar_keyboard.add(InlineKeyboardButton(text=' ', callback_data=' '))
            calendar_keyboard.adjust(1, 3, 7)
            await callback.message.edit_text('Календарь:', reply_markup=calendar_keyboard.as_markup())
            return
            
@main_router.callback_query(F.data.lower().contains('last_month'), StateFilter(FSM_conference.date_change))
async def last_month_func(callback : CallbackQuery, state : FSMContext):
    await callback.answer()
    await state.set_state(FSM_conference.date_change)
    calendar_keyboard = InlineKeyboardMarkup(inline_keyboard=
                                             [
                                                 []
                                             ])
    calendar_keyboard = InlineKeyboardBuilder()
    await callback.answer()
    res = callback.data.replace('last_month', '') 
    mon = res[0 : res.index(' ')]
    month_list = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
    final_mon = 12
    for i in reversed(month_list):
        final_mon -= 1
        if i == mon:
            break
    if final_mon not in range(1, 13):
        await callback.answer()
        return
    else:
        now = datetime.datetime(int(res[res.index(' ')+1:]), final_mon, 1)
        calendar_keyboard.add(InlineKeyboardButton(text=str(now.year), callback_data='year'))

        for m in month_list:
            if m != now.strftime('%B'):
                continue
            else:
                calendar_keyboard.add(InlineKeyboardButton(text='<-', callback_data=f'{m}last_month {str(now.year)}'))
                calendar_keyboard.add(InlineKeyboardButton(text=m, callback_data='month'))
                calendar_keyboard.add(InlineKeyboardButton(text='->', callback_data=f'{m}next_month {str(now.year)}'))
                break

        count = 0

        if now.month > datetime.datetime.today().month:
            if m == 'January' or m == 'March' or m == 'May' or m == 'July' or m == 'August' or m == 'October' or m == 'December':
                count = 31
            else:
                if m == 'February':
                    if int(now.year) % 4 == 0:
                        count = 29
                    else:
                        count = 28
                else:
                    count = 30

            counter = 0
            for d in day_list[0 : day_list.index(str(now.day))]:
                counter += 1
                calendar_keyboard.add(InlineKeyboardButton(text=' ', callback_data=' '))
            for d in list(day_list[day_list.index(str(now.day)) : day_list.index(str(count)) + 1]):
                counter += 1
                if d == v:
                    calendar_keyboard.add(InlineKeyboardButton(text=f'[{d}]', callback_data=f'{str(now.year)}/{m}/{d}'))
                else:
                    calendar_keyboard.add(InlineKeyboardButton(text=d, callback_data=f'{str(now.year)}/{m}/{d}'))

            while counter % 7 != 0:
                counter += 1
                calendar_keyboard.add(InlineKeyboardButton(text=' ', callback_data=' '))
            calendar_keyboard.adjust(1, 3, 7)

            await callback.message.edit_text('Календарь:', reply_markup=calendar_keyboard.as_markup())
            return
        elif now.month == datetime.datetime.today().month:
            calendar_keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        
                    ]
                ]
            )
            calendar_keyboard = InlineKeyboardBuilder()
            calendar_keyboard.add(InlineKeyboardButton(text=str(now.year), callback_data='year'))

            for m in month_list:
                if m != now.strftime('%B'):
                    continue
                else:
                    calendar_keyboard.add(InlineKeyboardButton(text='<-', callback_data=f'{m}last_month {str(now.year)}'))
                    calendar_keyboard.add(InlineKeyboardButton(text=m, callback_data='month'))
                    calendar_keyboard.add(InlineKeyboardButton(text='->', callback_data=f'{m}next_month {str(now.year)}'))
                    break

            count = 0

            if m == 'January' or m == 'March' or m == 'May' or m == 'July' or m == 'August' or m == 'October' or m == 'December':
                count = 31
            else:
                if m == 'February':
                    if int(now.year) % 4 == 0:
                        count = 29
                    else:
                        count = 28
                else:
                    count = 30

            counter = 0
            for d in day_list[0 : day_list.index(str(datetime.datetime.today().day))]:
                counter += 1
                calendar_keyboard.add(InlineKeyboardButton(text=' ', callback_data=' '))
            for d in list(day_list[day_list.index(str(datetime.datetime.today().day)) : day_list.index(str(count)) + 1]):
                counter += 1
                if d == v:
                    calendar_keyboard.add(InlineKeyboardButton(text=f'[{d}]', callback_data=f'{str(now.year)}/{m}/{d}'))
                else:
                    calendar_keyboard.add(InlineKeyboardButton(text=d, callback_data=f'{str(now.year)}/{m}/{d}'))

            while counter % 7 != 0:
                counter += 1
                calendar_keyboard.add(InlineKeyboardButton(text=' ', callback_data=' '))
            calendar_keyboard.adjust(1, 3, 7)
            await callback.message.edit_text('Календарь:', reply_markup=calendar_keyboard.as_markup())
            return
        elif now.month < datetime.datetime.today().month:
            for q in range(35):
                calendar_keyboard.add(InlineKeyboardButton(text=' ', callback_data=' '))
            calendar_keyboard.adjust(1, 3, 7)
            await callback.message.edit_text('Календарь:', reply_markup=calendar_keyboard.as_markup())
            return


@main_router.callback_query(F.data != ' ', StateFilter(FSM_conference.date_change))
async def date_getter(callback : CallbackQuery, state : FSMContext):
    await callback.answer()
    res = datetime.datetime.strptime(callback.data, '%Y/%B/%d')
    if res.month > 9:
        if res.day > 9:
            final_res = f'{res.year}/{res.day}/{res.month}'
        else:
            final_res = f'{res.year}/0{res.day}/{res.month}'
    else:
        if res.day > 9:
            final_res = f'{res.year}/{res.day}/0{res.month}'
        else:
            final_res = f'{res.year}/0{res.day}/0{res.month}'
    final_res = final_res[5:]
    await state.update_data(Дата=f'{final_res}')
    final_res_for_sql = datetime.datetime.strptime(final_res, '%d/%m')
    await state.update_data(Дата=final_res_for_sql.strftime('%d/%m'))
    hall = absolute_data.hall
    time_buttons = await generate_time_buttons_for_change(final_res_for_sql.strftime('%d/%m'), hall, id_keeper.id)
    await callback.message.answer('Укажите время, когда начинается встреча:', reply_markup=time_buttons.as_markup())
    await state.set_state(FSM_conference.timer_first_change)


@main_router.callback_query(StateFilter(FSM_conference.timer_first_change))
async def beginning_change(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    try:
        res = datetime.datetime.strptime(callback.data, '%H:%M')
        final_res = res.strftime('%H:%M')
        await state.update_data(С=final_res)
        dictionary = await state.get_data()
        date = dictionary['Дата']
        hall = absolute_data.hall
        time_buttons = await generate_time_buttons_for_change(date, hall, id_keeper.id)
        await callback.message.edit_text('Укажите время, когда встреча заканчивается', reply_markup=time_buttons.as_markup())
        await state.set_state(FSM_conference.timer_second_change)
    except ValueError:
        await callback.message.answer('Некорректное время. Пожалуйста, выберите снова.')



import logging

logging.basicConfig(level=logging.DEBUG)


@main_router.callback_query(StateFilter(FSM_conference.timer_second_change))
async def ending_change(callback: CallbackQuery, state: FSMContext, bot : Bot):
    await callback.answer()
    try:
        res = datetime.datetime.strptime(callback.data, '%H:%M')
        final_res = res.strftime('%H:%M')
        await state.update_data(По=final_res)

        dictionary = await state.get_data()
        date = dictionary['Дата']
        start_time = dictionary['С']
        end_time = dictionary['По']
        hall = absolute_data.hall
        booking_id = absolute_data.id

        #Получение участников
        additional_conn = sqlite3.connect('datebase.db')
        additional_cursor = additional_conn.cursor()
        get_patrticipants = '''
                            SELECT participants FROM user_booking_data
                            WHERE id = ?
                            '''
        additional_cursor.execute(get_patrticipants, (booking_id, ))
        result = additional_cursor.fetchall()
        additional_conn.commit()
        additional_conn.close()
        res_list = ''
        for i in result:
            for g in i:
                res_list += g
        #Получение участников

        # Проверка значений
        if not booking_id:
            await callback.message.answer('Ошибка: ID брони не установлен.')
            return

        connection = sqlite3.connect('datebase.db')
        cursor = connection.cursor()

        # Проверка на конфликты времени
        check_conflict_query = '''
            SELECT id, username, telephone_number, time_of_beginning, time_of_ending 
            FROM user_booking_data
            WHERE hall = ? AND date = ? AND (
                (time_of_beginning < ? AND time_of_ending > ?) OR
                (time_of_beginning < ? AND time_of_ending > ?)
            ) AND id != ?
        '''
        cursor.execute(check_conflict_query, (hall, date, end_time, start_time, end_time, start_time, booking_id))
        conflicts = cursor.fetchall()

        if conflicts:
            # Gather all occupied start and end times
            occupied_start_times = [conflict[3] for conflict in conflicts]
            occupied_end_times = [conflict[4] for conflict in conflicts]

            # Generate available time buttons considering occupied times
            start_time_buttons = await generate_time_buttons_for_change(date, hall, id_keeper.id, is_start_time=True,
                                                             occupied_times=occupied_start_times)
            end_time_buttons = await generate_time_buttons_for_change(date, hall, id_keeper.id, is_start_time=False,
                                                           occupied_times=occupied_end_times)

            # Notify user and request new time choices
            conflict_messages = '\n'.join(
                [f'Забронировано пользователем {conflict[1]} с {conflict[3]} по {conflict[4]} (ID: {conflict[0]})'
                 for conflict in conflicts]
            )
            await callback.message.answer(
                f'Время уже занято.\nКонфликтующие брони:\n{conflict_messages}\nПожалуйста, выберите другое время.',
                reply_markup=start_time_buttons
            )
            await callback.message.answer('Укажите время, когда заканчивается встреча:', reply_markup=end_time_buttons)
            await state.set_state(FSM_conference.timer_first_change)  # Возврат к выбору времени начала
            return


        #уведомление
        alarm = sqlite3.connect('datebase.db')
        alarm_cursor = alarm.cursor()
        alarm_query = '''
                      SELECT hall, date, time_of_beginning, time_of_ending, username, participants_id FROM user_booking_data
                      WHERE id = ?
                      '''
        alarm_cursor.execute(alarm_query, (booking_id, ))
        req = alarm_cursor.fetchall()
        alarm.commit()
        alarm.close()
        for i in req:
            l = list(v.strip() for v in i[-1].split(','))
            if not '' in l:
                for w in l:
                    await bot.send_message(chat_id=w, text=f'Внимание, бронь зала {i[0]}, забронированная пользователем {i[4]} на {i[1]} с {i[2]} по {i[3]} перенесена на {date} с {start_time} по {end_time}')
        #уведомление


        # Обновление записи в базе данных
        update_query = '''
            UPDATE user_booking_data
            SET date = ?, time_of_beginning = ?, time_of_ending = ?
            WHERE id = ?
        '''
        cursor.execute(update_query, (date, start_time, end_time, booking_id))

        # Проверка успешности обновления
        connection.commit()
        cursor.execute('SELECT * FROM user_booking_data WHERE id = ?', (booking_id,))
        updated_booking = cursor.fetchone()
        connection.close()

        if updated_booking:
            await callback.message.answer(
                f'Бронь успешно перенесена.\nЗал: {hall}\nДата: {date}\nС: {start_time}\nПо: {end_time}\nУчастники: {res_list}',
                reply_markup=start_mark_up.as_markup(
                    resize_keyboard=True,
                    input_field_placeholder='Что хотите сделать?'
                ))
            
        else:
            await callback.message.answer(f'Ошибка: Не удалось обновить бронь. ID: {booking_id}',
                                          reply_markup=start_mark_up.as_markup(
                                              resize_keyboard=True,
                                              input_field_placeholder='Что хотите сделать?'
                                          ))
        await state.clear()

    except Exception as e:
        await callback.message.answer(f'Произошла ошибка: {str(e)}', reply_markup=start_mark_up.as_markup(
            resize_keyboard=True,
            input_field_placeholder='Что хотите сделать?'
        ))


@main_router.message(F.text == 'Отменить бронь', StateFilter(None))
async def remove_booking(msg: types.Message, state: FSMContext):
    connection_object = sqlite3.connect('datebase.db')
    cursor_object = connection_object.cursor()
    query = '''
        SELECT username FROM user_booking_data
    '''
    cursor_object.execute(query)
    res = cursor_object.fetchall()

    l = [r for i in res for r in i]

    if f'@{msg.from_user.username}' not in l:
        await msg.answer('Вы пока что ничего не бронировали', reply_markup=ReplyKeyboardRemove())
        return

    searching_query = '''
        SELECT hall, date, time_of_beginning, time_of_ending, id FROM user_booking_data
        WHERE username = ?
    '''
    cursor_object.execute(searching_query, (f'@{msg.from_user.username}',))
    search_res = cursor_object.fetchall()
    connection_object.commit()
    connection_object.close()

    count = 0

    bookings_mark_up = InlineKeyboardBuilder()
    for i in search_res:
        count += 1
        bookings_mark_up.add(
            InlineKeyboardButton(text=f'Зал: {i[0]}, на: {i[1]}, с: {i[2]}, по: {i[3]}', callback_data=f'id: {i[4]}'))
    bookings_mark_up.adjust(1)

    await msg.answer('Выберите бронь, которую хотите отменить:', reply_markup=ReplyKeyboardRemove())
    await msg.answer('Ваши брони:', reply_markup=bookings_mark_up.as_markup())
    await state.set_state(FSM_conference.removing)


@main_router.callback_query(StateFilter(FSM_conference.removing))
async def remove_booking_action(callback: CallbackQuery, state: FSMContext, bot : Bot):
    await callback.answer()
    data = callback.data.replace('id:', '').replace(' ', '')
    booking_id = int(data)


    alarm = sqlite3.connect('datebase.db')
    alarm_cursor = alarm.cursor()
    alarm_query = '''
                  SELECT hall, date, time_of_beginning, time_of_ending, username, participants_id FROM user_booking_data
                  WHERE id = ?
                  '''
    alarm_cursor.execute(alarm_query, (booking_id, ))
    req = alarm_cursor.fetchall()
    alarm.commit()
    alarm.close()
    for i in req:
        l = list(v.strip() for v in i[-1].split(','))
        if not '' in l:
            for w in l:
                await bot.send_message(chat_id=w, text=f'Внимание, бронь зала {i[0]}, забронированная пользователем {i[4]} на {i[1]} с {i[2]} по {i[3]} отменена')


    connection = sqlite3.connect('datebase.db')
    cursor = connection.cursor()

    # Удаление записи из базы данных
    delete_query = 'DELETE FROM user_booking_data WHERE id = ?'
    cursor.execute(delete_query, (booking_id,))

    connection.commit()
    connection.close()

    await callback.message.answer('Бронь успешно отменена.', reply_markup=start_mark_up.as_markup(
        resize_keyboard=True,
        input_field_placeholder='Что хотите сделать?'
    ))
    await state.clear()


async def generate_time_buttons(date: str, hall: str):
    connection = sqlite3.connect('datebase.db')
    cursor = connection.cursor()
    query = '''
        SELECT time_of_beginning, time_of_ending
        FROM user_booking_data
        WHERE date = ? AND hall = ?
    '''
    cursor.execute(query, (date, hall))
    bookings = cursor.fetchall()
    connection.close()

    # Create a set of all occupied times
    occupied_times = set()
    for booking in bookings:
        start_time = datetime.datetime.strptime(booking[0], '%H:%M')
        end_time = datetime.datetime.strptime(booking[1], '%H:%M')
        while start_time < end_time:
            occupied_times.add(start_time.strftime('%H:%M'))
            start_time += datetime.timedelta(minutes=30)

    # Generate time buttons
    time_buttons = InlineKeyboardBuilder()
    start_time = datetime.datetime.strptime('07:00', '%H:%M')
    end_time = datetime.datetime.strptime('23:00', '%H:%M')

    while start_time < end_time:
        time_str = start_time.strftime('%H:%M')
        if time_str in occupied_times:
            time_buttons.add(InlineKeyboardButton(text=f'❌ {time_str}', callback_data='occupied'))
        else:
            time_buttons.add(InlineKeyboardButton(text=time_str, callback_data=time_str))
        start_time += datetime.timedelta(minutes=30)
    time_buttons.add(InlineKeyboardButton(text = 'Главное меню', callback_data='return_to_main_menu'))
    time_buttons.adjust(4)  # Adjust to 4 columns
    return time_buttons

async def generate_time_buttons_for_change(date: str, hall: str, id : int):
    connection = sqlite3.connect('datebase.db')
    cursor = connection.cursor()
    query = '''
        SELECT time_of_beginning, time_of_ending
        FROM user_booking_data
        WHERE date = ? AND hall = ? AND id != ?
    '''
    cursor.execute(query, (date, hall, id))
    bookings = cursor.fetchall()
    connection.close()

    # Create a set of all occupied times
    occupied_times = set()
    for booking in bookings:
        start_time = datetime.datetime.strptime(booking[0], '%H:%M')
        end_time = datetime.datetime.strptime(booking[1], '%H:%M')
        while start_time < end_time:
            occupied_times.add(start_time.strftime('%H:%M'))
            start_time += datetime.timedelta(minutes=30)

    # Generate time buttons
    time_buttons = InlineKeyboardBuilder()
    start_time = datetime.datetime.strptime('07:00', '%H:%M')
    end_time = datetime.datetime.strptime('23:00', '%H:%M')

    while start_time < end_time:
        time_str = start_time.strftime('%H:%M')
        if time_str in occupied_times:
            time_buttons.add(InlineKeyboardButton(text=f'❌ {time_str}', callback_data='occupied'))
        else:
            time_buttons.add(InlineKeyboardButton(text=time_str, callback_data=time_str))
        start_time += datetime.timedelta(minutes=30)
    time_buttons.add(InlineKeyboardButton(text = 'Главное меню', callback_data='return_to_main_menu'))
    time_buttons.adjust(4)  # Adjust to 4 columns
    return time_buttons