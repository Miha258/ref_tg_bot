import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils.exceptions import BadRequest
from db import session, User
import re

API_TOKEN = '7089086031:AAELSrUv4Cwkc6PFyKNTLSUmR4nHo73OJSk'  # Замените на свой API токен

class Features(StatesGroup):
    wallet = State()
    twitter_url = State()


# Включаем логирование для отслеживания ошибок
logging.basicConfig(level=logging.INFO)

# Инициализируем бот и диспетчер
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage = storage)

# Название канала
channel_username = "@not_mell_ton"

# Обработчик команды /start
@dp.message_handler(commands=['start'], state = "*")
async def send_welcome(message: types.Message, state: FSMContext):
    await state.finish()
    if message.chat.type == 'private':
        chat_id = message.chat.id
        ref_start = message.text.split(" ")
        ref_id = int(ref_start[1]) if len(ref_start) == 2 else None

        if ref_id:
            if ref_id != message.from_id:
                ref_user = session.query(User).filter_by(id = ref_id).first()
                ref_user.ref_count = ref_user.ref_count + 1
                ref_user.balance = ref_user.balance + 200
                session.commit()
                await bot.send_message(ref_id, f"Пользователь {message.from_user.username} успешно прошел по вашей ссылке")
        else:
            _bot = await bot.get_me()
            if not session.query(User).filter_by(id = message.from_id).first():
                user = User(id = message.from_id, username = message.from_user.username, ref_url = f"https://t.me/{_bot.username}?start={message.from_id}")
                session.add(user)
        try:
            await bot.get_chat_member(channel_username, chat_id)
            await send_airdrop_info(chat_id)
        except BadRequest:
            user_name = message.from_user.first_name
            await message.reply(f"Привет, {user_name}!👋\n"
                                f"Для участия в AIRDROP, необходимо подписаться на канал NOT MELL: {channel_username}\n"
                                "Нажми кнопку ниже, чтобы проверить подписку.",
                                reply_markup=subscribe_button())

# Функция для создания кнопки "Проверить подписку"
def subscribe_button():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("✅Проверить подписку", callback_data = "subscribe_check"))
    return markup

# Обработчик нажатия на кнопку "Проверить подписку"
@dp.callback_query_handler(lambda query: query.data == 'subscribe_check')
async def check_subscription(query: types.CallbackQuery):
    chat_id = query.message.chat.id
    try:
        await bot.get_chat_member(channel_username, chat_id)
        await query.message.answer("Подписка подтверждена!")
        await send_airdrop_info(chat_id)
    except BadRequest:
        await query.message.answer("ТА НУ НЕЕ, ты все еще не подписался. "
                                                  f"Подпишись сначала на наш канал: {channel_username} 🤝")

# Функция для отправки информации о AIRDROP
async def send_airdrop_info(chat_id):
    # Здесь можно добавить отправку картинки, если у вас есть URL к картинке

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, keyboard = [[
        KeyboardButton("AirDrop Правила📕"),
        KeyboardButton("Мой Баланс💸")
    ],
    [
        KeyboardButton("Добавить кошелек🎒"),
        KeyboardButton("Twitter (ранний мини-дроп)🍿")
    ],[
        KeyboardButton("Персональная ссылка для приглашений 👥")
    ]])
    await bot.send_message(chat_id, "🔝 Главное Меню", reply_markup = keyboard)
    await bot.send_message(chat_id, "AIRDROP NOT MELL СТАРТОВАЛ!\n"
                                    "Получай 200 токенов $NOTMELL за каждого приведенного друга 💰\n"
                                    "Самые легкие условия поучавствовать в большой истории запуска!\n"
                                    "Никаких долгих ожиданий.\n"
                                    "Выпуск мем-токена очень близко.\n"
                                    "Стань частью крутой истории $NOTMELL\n"
                                    "Да начнется воозня!\n"
                                    f"{channel_username}",
                           reply_markup = invite_button(chat_id))

# Функция для создания кнопки "Пригласить друга"
def invite_button(chat_id):
    ref_user = session.query(User).filter_by(id = chat_id).first()
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Пригласить друга 👥", switch_inline_query=ref_user.ref_url))
    return markup

# Обработчик текстовых сообщений
@dp.message_handler(content_types=types.ContentType.TEXT)
async def process_text_messages(message: types.Message, state: FSMContext):
    ref_user = session.query(User).filter_by(id = message.from_id).first() 
    if message.text == "AirDrop Правила📕":
        await message.answer(f"""
Для участия в раздаче токенов $NOTMELL выполни 2 простых правила. 

1.Быть подписаным на оффициальный канал NOTMELL @not_mell_ton

2.Пригласить всех кентов и кентих в нашу историческую возню!

Каждый приглашенный участник дает тебе на баланс +200 токенов $NOTMELL

Можешь приглашать друзей по своей персональной ссылке: {ref_user.ref_url}

Это еще не все!
Что бы поучаствовать в еще одной раздаче $$$$ выполни задания во вкладке Twitter🍿

""")
    elif message.text == "Мой Баланс💸":
        await message.answer(f"""
Твой баланс: {ref_user.balance} $NOTMELL
1 друг = 200 $NOTMELL

Персональная ссылка для приглашений: {ref_user.ref_url}
""", reply_markup = invite_button(message.from_id))
    elif message.text == "Добавить кошелек🎒":
        await message.answer("""
Добавь свой некастодиальный кошелек в сети TON.
К примеру это может быть: Tonkeeper\Tonhub\MyTonWallet

После завершения первой фазы ты автоматически получишь на кошелек токены $NOTMELL 
Сколько получишь? Сколько заработаешь,пока  есть время делай!

Добавь адрес твоего кошелька в сети TON:
        """)
        await state.set_state(Features.wallet)
    elif message.text == "Twitter (ранний мини-дроп)🍿":
        await message.answer("""
Всего один дроп?
АХАХАХ,у нас их два.
Подпишись на наш Twitter и сделай репост любой записи себе.
Ты станешь участником еще одной раздачи. 

Отправь ссылку на репост который сделал в твиттере:
""")
    elif message.text == "Персональная ссылка для приглашений 👥":
        await message.answer("""
Твоя персональная ссылка,по которой можешь приглашать друзей.
Каждый друг +200 $NOTMELL тебе на баланс!

Все в твоих руках!
""", reply_markup = invite_button(message.from_id))
        

@dp.message_handler(state = Features.wallet)
async def set_wallet(message: types.Message, state: FSMContext):
    pattern = r'^[0-9a-fA-F]{64}$'
    wallet_address = message.text
 
    if re.match(pattern, wallet_address):
        await message.answer("Кошелек успешно установлен!")
        ref_user = session.query(User).filter_by(id = message.from_id).first()
        ref_user.wallet = wallet_address
        session.commit()
        await state.finish()
    else:
        await message.answer('Неверный адрес кошелька, повторите попытку:')

@dp.message_handler(state = Features.wallet)
async def twitter_url(message: types.Message, state: FSMContext):
    await message.answer("Ссылка передана на обработку, спасибо")
    await state.finish()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
