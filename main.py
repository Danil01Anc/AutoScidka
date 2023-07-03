import pandas as pd
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardRemove, \
    ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher import FSMContext

df = pd.read_excel('C:/Users/Владелец/Desktop/AutoCkidka/katalog.xlsx')
df = df.drop('Доп', axis=1)
bot = Bot(token='6137200510:AAHEz5zbNXbtxmq3SOy1qKXCKoYsnPCdEeM')
# dp = Dispatcher(bot)
admin_chat_id = -1001982899389  # ID администратора
dp = Dispatcher(bot, storage=MemoryStorage())  # Use MemoryStorage
state = {}
user_data = {}

# Define state
class Form(StatesGroup):
    Mark = State()
    Model = State()
    Color = State()
    Year = State()  # New state

# Define buttons
button_pick_car = KeyboardButton('Подобрать автомобиль')
button_contact_manager = KeyboardButton('Связаться с менеджером')
greet_kb = ReplyKeyboardMarkup(resize_keyboard=True).add(button_pick_car, button_contact_manager)

@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    await message.reply("Привет! Я могу помочь вам подобрать автомобиль или связаться с менеджером. "
                        "Что вы хотите сделать?", reply_markup=greet_kb)

@dp.message_handler(state='*', commands='cancel')
@dp.message_handler(Text(equals='cancel', ignore_case=True), state='*')
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.finish()
    await message.reply('Cancelled.', reply_markup=ReplyKeyboardRemove())

@dp.message_handler(lambda message: message.text == 'Подобрать автомобиль')
async def process_pick_car_command(message: types.Message):
    options = df['Марка'].unique().tolist()
    options_kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for option in options:
        options_kb.add(KeyboardButton(option))
    options_kb.add(KeyboardButton("⬅️ Назад"))
    await Form.Mark.set()
    await message.answer("Выберите марку автомобиля:", reply_markup=options_kb)

@dp.message_handler(state=Form.Mark)
async def process_mark(message: types.Message, state: FSMContext):
    chosen_mark = message.text
    if chosen_mark == "⬅️ Назад":
        await message.answer("Привет! Я могу помочь вам подобрать автомобиль или связаться с менеджером. "
                             "Что вы хотите сделать?", reply_markup=greet_kb)
        await state.finish()
        return

    await state.update_data(chosen_mark=chosen_mark)

    models = df[df['Марка'] == chosen_mark]['Модель'].unique().tolist()
    models = [model for model in models if not pd.isna(model)]  # Убираем значения nan

    models_kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for model in models:
        models_kb.add(KeyboardButton(model))
    models_kb.add(KeyboardButton("⬅️ Назад"))

    await Form.Model.set()
    await message.answer("Выберите модель автомобиля:", reply_markup=models_kb)

@dp.message_handler(state=Form.Model)
async def process_model(message: types.Message, state: FSMContext):
    chosen_model = message.text
    if chosen_model == "⬅️ Назад":
        await Form.Mark.set()
        await message.answer("Выберите марку автомобиля:",
                             reply_markup=ReplyKeyboardMarkup([[mark] for mark in df['Марка'].unique().tolist()], one_time_keyboard=True).add("⬅️ Назад"))
        return

    await state.update_data(chosen_model=chosen_model)

    chosen_mark = (await state.get_data())['chosen_mark']
    colors = df[(df['Марка'] == chosen_mark) & (df['Модель'] == chosen_model)]['Цвет'].unique().tolist()
    colors = [color for color in colors if not pd.isna(color)]

    color_kb = ReplyKeyboardMarkup(resize_keyboard=True)
    for color in colors:
        color_kb.add(KeyboardButton(color))
    color_kb.add(KeyboardButton("⬅️ Назад"))

    await Form.Color.set()
    await message.answer("Выберите цвет автомобиля:", reply_markup=color_kb)

@dp.message_handler(state=Form.Color)
async def process_color(message: types.Message, state: FSMContext):
    chosen_color = message.text
    if chosen_color == "⬅️ Назад":
        await Form.Model.set()
        chosen_mark = (await state.get_data())['chosen_mark']
        models = df[df['Марка'] == chosen_mark]['Модель'].unique().tolist()
        await message.answer("Выберите модель автомобиля:",
                             reply_markup=ReplyKeyboardMarkup([[model] for model in models], one_time_keyboard=True).add("⬅️ Назад"))
        return

    await state.update_data(chosen_color=chosen_color)

    data = await state.get_data()
    chosen_mark = data['chosen_mark']
    chosen_model = data['chosen_model']

    years = df[(df['Марка'] == chosen_mark) &
               (df['Модель'] == chosen_model) &
               (df['Цвет'] == chosen_color)]['Год выпуска'].unique().tolist()
    years = [year for year in years if not pd.isna(year)]  # Убираем значения nan

    years_kb = ReplyKeyboardMarkup(one_time_keyboard=True)
    for year in years:
        years_kb.add(KeyboardButton(str(int(year))))

    years_kb.add(KeyboardButton("⬅️ Назад"))

    await Form.Year.set()
    await message.answer("Выберите год выпуска автомобиля:", reply_markup=years_kb)

@dp.message_handler(state=Form.Year)
async def process_year(message: types.Message, state: FSMContext):
    chosen_year = message.text
    if chosen_year == "⬅️ Назад":
        await Form.Color.set()
        chosen_color = (await state.get_data())['chosen_color']
        chosen_mark = (await state.get_data())['chosen_mark']
        chosen_model = (await state.get_data())['chosen_model']
        colors = df[(df['Марка'] == chosen_mark) & (df['Модель'] == chosen_model)]['Цвет'].unique().tolist()

        color_kb = ReplyKeyboardMarkup(resize_keyboard=True).add("⬅️ Назад")
        for color in colors:
            color_kb.add(KeyboardButton(color))

        await message.answer("Выберите цвет автомобиля:", reply_markup=color_kb)
        return

    chosen_year = str(int(float(chosen_year)))  # Преобразование в строку без десятичной части
    await state.update_data(chosen_year=chosen_year)

    data = await state.get_data()
    chosen_mark = data['chosen_mark']
    chosen_model = data['chosen_model']
    chosen_color = data['chosen_color']

    filtered_df = df[(df['Марка'] == chosen_mark) &
                     (df['Модель'] == chosen_model) &
                     (df['Цвет'] == chosen_color) &
                     (df['Год выпуска'] == int(chosen_year))]

    car_info = filtered_df.values.tolist()
    car_info_str = '\n''\n'.join([', '.join(map(str, row)) for row in car_info])
    car_info_str = car_info_str.replace('.0', '')

    await message.answer(f"Представлены автомобили по вашим критериям :\n{car_info_str}")

    # Добавляем выбор следующего действия
    await message.answer("Узнать о том, как можно оформить этот автомобиль или подобрать другой", reply_markup=greet_kb)

    await state.finish()

@dp.message_handler(lambda message: message.text == 'Связаться с менеджером')
async def process_contact_manager_command(message: types.Message):
    state[message.chat.id] = "CONTACT_MANAGER"
    await message.reply("Вы выбрали связаться с менеджером. Напишите пожалуйста ваше имя и номер телефона в одном сообщении.")

@dp.message_handler()
async def echo_message(msg: types.Message):
    chat_id = msg.from_user.id
    user_data[chat_id] = user_data.get(chat_id, {})
    state[chat_id] = state.get(chat_id, "START")
    # admin_chat_id = '123456789'  # замените на ваше значение

    if state[chat_id] == "PICK_CAR":
        # Здесь добавьте ваш код для обработки шагов выбора автомобиля
        pass

    elif state[chat_id] == "CONTACT_MANAGER":
        contact_info = f"Передаю ваши данные, скоро с вами свяжется наш менеджер: {msg.text}"
        await bot.send_message(msg.from_user.id, contact_info, reply_markup=greet_kb)
        await bot.send_message(admin_chat_id, contact_info)

    else:
        await bot.send_message(msg.from_user.id, f"Я видел, вы сказали: {msg.text}", reply_markup=greet_kb)

if __name__ == '__main__':
    executor.start_polling(dp)