import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils.exceptions import BadRequest
from db import session, User

API_TOKEN = '7089086031:AAELSrUv4Cwkc6PFyKNTLSUmR4nHo73OJSk' 

class Features(StatesGroup):
    WALLET = State()


# Включаем логирование для отслеживания ошибок
logging.basicConfig(level=logging.INFO)

# Инициализируем бот и диспетчер
bot = Bot(token=API_TOKEN, parse_mode = "html")
storage = MemoryStorage()
dp = Dispatcher(bot, storage = storage)

# Название канала
channel_username = "@not_mell_ton"

# Обработчик команды /start
@dp.message_handler(commands = ['start'], state = "*")
async def send_welcome(message: types.Message, state: FSMContext):
    if message.chat.type == 'private':
        await state.finish()
        _bot = await bot.get_me()
        if not session.query(User).filter_by(id = message.from_id).first():
            user = User(id = message.from_id, username = message.from_user.username, ref_url = f"https://t.me/{_bot.username}?start={message.from_id}")
            session.add(user)

        chat_id = message.chat.id
        try:
            user = await bot.get_chat_member(channel_username, chat_id)
            if user.status == 'left' or user.status == 'kicked':
                raise BadRequest("Member has left")
            else:
                await send_airdrop_info(chat_id)
        except BadRequest as e:
            user_name = message.from_user.first_name
            return await message.answer(f"""
Привет {user_name}👋
Для участия в AIRDROP,необходимо подписаться на канал NOT MELL: {channel_username}
        """, reply_markup=subscribe_button())
            
        ref_start = message.text.split(" ")
        ref_id = int(ref_start[1]) if len(ref_start) == 2 else None

        if ref_id:
            if ref_id != message.from_id:
                ref_user = session.query(User).filter_by(id = ref_id).first()
                ref_user.ref_count = ref_user.ref_count + 1
                ref_user.balance = ref_user.balance + 200
                session.commit()
                await bot.send_message(ref_id, f"Пользователь {message.from_user.username} успешно прошел по вашей ссылке")

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
        user = await bot.get_chat_member(channel_username, chat_id)
        if user.status == 'left' or user.status == 'kicked':
            raise BadRequest("Member has left")
        await query.message.answer("Подписка подтверждена!")
        await send_airdrop_info(chat_id)
    except BadRequest:
        await query.message.answer(f"ТА НУ НЕЕ,ты все еще не подписался. Подпишись сначала на наш канал: {channel_username} 🤝")

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
    await bot.send_photo(chat_id, photo = types.InputFile('pictures/main.jpg'), caption = f"""
<strong>AIRDROP NOT MELL СТАРТОВАЛ!</strong>

Получай 200 токенов  $NOTMELL за каждого приведенного друга 💰
Самые легкие условия поучавствовать в большой истории запуска!

<strong>Никаких долгих ожиданий.
Выпуск мем-токена очень близко.
</strong>
Стань частью крутой истории $NOTMELL

<strong>Да начнется воозня!</strong>
{channel_username}
""", reply_markup = invite_button(chat_id))

# Функция для создания кнопки "Пригласить друга"
def invite_button(chat_id):
    ref_user = session.query(User).filter_by(id = chat_id).first()
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Пригласить друга 👥", url = "https://t.me/share/url?url=" + ref_user.ref_url))
    return markup

@dp.message_handler(content_types=types.ContentType.TEXT, state = Features.WALLET)
async def set_wallet(message: types.Message, state: FSMContext):
    await message.answer("Кошелек успешно установлен!✅")
    wallet_address = message.text
    ref_user = session.query(User).filter_by(id = message.from_id).first()
    ref_user.wallet = wallet_address
    session.commit()
    await state.finish()

# Обработчик текстовых сообщений
@dp.message_handler(content_types=types.ContentType.TEXT, state = "*")
async def process_text_messages(message: types.Message, state: FSMContext):
    await state.finish()
    ref_user = session.query(User).filter_by(id = message.from_id).first() 
    if message.text == "AirDrop Правила📕":
        await message.answer_photo(types.InputFile('pictures/terms.jpg'), caption = f"""
Для участия в раздаче токенов $NOTMELL выполни 2 простых правила. 

1.Быть подписаным на оффициальный канал NOTMELL {channel_username}

2.Пригласить всех кентов и кентих в нашу историческую возню!

Каждый приглашенный участник дает тебе на баланс +200 токенов $NOTMELL

Можешь приглашать друзей по своей персональной ссылке: {ref_user.ref_url}

<strong>
Это еще не все!
Что бы поучаствовать в еще одной раздаче $$$$ выполни задания во вкладке Twitter🍿
</strong>

""")
    elif message.text == "Мой Баланс💸":
        await message.answer_photo(types.InputFile('pictures/balance.jpg'), caption = f"""
Твой баланс: {ref_user.balance} $NOTMELL
<strong>1 друг = 200 $NOTMELL</strong>

Персональная ссылка для приглашений: {ref_user.ref_url}
""", reply_markup = invite_button(message.from_id))
    elif message.text == "Добавить кошелек🎒":
        await message.answer_photo(types.InputFile('pictures/wallet.jpg'), caption = """
<strong>Куда будешь дроп получать?</strong>                    

Добавь свой некастодиальный кошелек в сети TON.
К примеру это может быть: Tonkeeper\Tonhub\MyTonWallet

После завершения первой фазы ты автоматически получишь на кошелек токены $NOTMELL 
Сколько получишь? Сколько заработаешь,пока  есть время делай!

Добавь адрес твоего кошелька в сети TON:
        """)
        await state.set_state(Features.WALLET)
    elif message.text == "Twitter (ранний мини-дроп)🍿":
        await message.answer_photo(types.InputFile('pictures/twitter.jpg'), caption = """
<strong>Всего один дроп?</strong>
АХАХАХ,у нас их два.
Подпишись на наш Twitter и сделай репост любой записи себе.
Ты станешь участником еще одной раздачи. 

Отправь ссылку на репост который сделал в твиттере:
""", reply_markup = types.InlineKeyboardMarkup(inline_keyboard = [[
    types.InlineKeyboardButton('Наш Twitter🕊️', url = 'https://twitter.com/NotMellTon')
]]))
    elif message.text == "Персональная ссылка для приглашений 👥":
        await message.answer_photo(types.InputFile('pictures/refs.jpg'), f"""
Твоя персональная ссылка,по которой можешь приглашать друзей.
Каждый друг +200 $NOTMELL тебе на баланс!
Можешь приглашать друзей по своей персональной ссылке: {ref_user.ref_url}

Все в твоих руках!
""", reply_markup = invite_button(message.from_id))

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
