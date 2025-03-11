import logging
import asyncio
import requests
import os
import psycopg2
from urllib.parse import urlparse
from aiogram import Bot, Dispatcher, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Загружаем переменные окружения
load_dotenv()

# Подключение к PostgreSQL
DB_PARAMS = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST")
}

# Проверка подключения к БД
def test_connection():
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()
        cur.execute("SELECT version();")
        db_version = cur.fetchone()
        print(f"Успешное подключение к БД: {db_version}")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Ошибка подключения: {e}")

test_connection()

# Подключаем бота
TOKEN = "Токен телеграм бота"
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Логирование
logging.basicConfig(level=logging.INFO)

# RSS-источники
NEWS_SOURCES = {
    "Kommersant": "https://www.kommersant.ru/RSS/news.xml",
    "IXBT": "https://www.ixbt.com/export/news.rss",
    "Investing": "https://ru.investing.com/rss/news.rss",
}

# Главное меню с кнопками
def main_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📢 Подписаться"), KeyboardButton(text="📰 Последние новости")],
            [KeyboardButton(text="📋 Мои подписки")]
        ],
        resize_keyboard=True
    )
    return keyboard

# Создаем состояния для выбора источника
class UserState(StatesGroup):
    choosing_subscription = State()
    choosing_news = State()

# Команда /start
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer("Привет! Выберите действие:", reply_markup=main_keyboard())

# Функция парсинга новостей
def fetch_rss_news(url):
    response = requests.get(url)
    if response.status_code != 200:
        return "Ошибка при получении новостей."

    soup = BeautifulSoup(response.content, "xml")
    items = soup.find_all("item", limit=3)  # Берем 3 последних новости
    news_list = [f"🔹 [{item.title.text}]({item.link.text})" for item in items]

    return "\n\n".join(news_list) if news_list else "Новостей нет."

# Функция для добавления подписки в БД
def add_subscription(user_id, source):
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()
    cur.execute("SELECT source FROM subscriptions WHERE user_id = %s AND source = %s", (user_id, source))
    existing = cur.fetchone()

    if not existing:
        cur.execute("INSERT INTO subscriptions (user_id, source) VALUES (%s, %s)", (user_id, source))
        conn.commit()

    cur.close()
    conn.close()


# Обработчик кнопки "📢 Подписаться"
@dp.message(F.text == "📢 Подписаться")
async def subscribe_cmd(message: types.Message, state: FSMContext):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📢 Kommersant"), KeyboardButton(text="🖥 IXBT")],
            [KeyboardButton(text="📊 Investing"), KeyboardButton(text="🔙 Назад")]
        ],
        resize_keyboard=True
    )
    await state.set_state(UserState.choosing_subscription)
    await message.answer("Выберите источник для подписки:", reply_markup=keyboard)


# Обработчик выбора источника подписки
@dp.message(UserState.choosing_subscription, F.text.in_(["📢 Kommersant", "🖥 IXBT", "📊 Investing"]))
async def confirm_subscription(message: types.Message, state: FSMContext):
    source_map = {
        "📢 Kommersant": "Kommersant",
        "🖥 IXBT": "IXBT",
        "📊 Investing": "Investing"
    }

    source = source_map[message.text]
    add_subscription(message.from_user.id, source)
    await message.answer(f"Вы подписались на {source}! Раз в сутки вам будет приходить новая статья.", reply_markup=main_keyboard())
    await state.clear()  # Выходим из состояния подписки


# Обработчик кнопки "📰 Последние новости"
@dp.message(F.text == "📰 Последние новости")
async def latest_news_cmd(message: types.Message, state: FSMContext):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📢 Kommersant"), KeyboardButton(text="🖥 IXBT")],
            [KeyboardButton(text="📊 Investing"), KeyboardButton(text="🔙 Назад")]
        ],
        resize_keyboard=True
    )
    await state.set_state(UserState.choosing_news)
    await message.answer("Выберите источник:", reply_markup=keyboard)


# Обработчик выбора источника для просмотра новостей
@dp.message(UserState.choosing_news, F.text.in_(["📢 Kommersant", "🖥 IXBT", "📊 Investing"]))
async def show_latest_news(message: types.Message, state: FSMContext):
    source_map = {
        "📢 Kommersant": "Kommersant",
        "🖥 IXBT": "IXBT",
        "📊 Investing": "Investing"
    }

    source = source_map[message.text]
    news = fetch_rss_news(NEWS_SOURCES[source])
    await message.answer(f"📰 Новости {source}:\n\n{news}",
    parse_mode="Markdown",
    disable_web_page_preview=True,
    reply_markup=main_keyboard())
    await state.clear()  # Выходим из состояния выбора новостей


# Обработчик кнопки "🔙 Назад"
@dp.message(F.text == "🔙 Назад")
async def back_to_menu(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Вы вернулись в главное меню.", reply_markup=main_keyboard())


# Функция получения подписок пользователя
def get_user_subscriptions(user_id):
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()
    cur.execute("SELECT source FROM subscriptions WHERE user_id = %s", (user_id,))
    subscriptions = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return subscriptions

# Функция удаления подписки
def remove_subscription(user_id, source):
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()
    cur.execute("DELETE FROM subscriptions WHERE user_id = %s AND source = %s", (user_id, source))
    conn.commit()
    cur.close()
    conn.close()

# Функция удаления всех подписок
def remove_all_subscriptions(user_id):
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()
    cur.execute("DELETE FROM subscriptions WHERE user_id = %s", (user_id,))
    conn.commit()
    cur.close()
    conn.close()

# Обработчик кнопки "📋 Мои подписки"
@dp.message(F.text == "📋 Мои подписки")
async def my_subscriptions(message: types.Message):
    user_id = message.from_user.id
    subscriptions = get_user_subscriptions(user_id)

    if subscriptions:
        text = "Вы подписаны на следующие источники:\n" + "\n".join([f"🔹 {s}" for s in subscriptions])
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="❌ Отписаться")], [KeyboardButton(text="🔙 Назад")]],
            resize_keyboard=True
        )
    else:
        text = "Вы пока не подписаны ни на один источник."
        keyboard = main_keyboard()

    await message.answer(text, reply_markup=keyboard)

# Обработчик кнопки "❌ Отписаться"
@dp.message(F.text == "❌ Отписаться")
async def unsubscribe_menu(message: types.Message):
    user_id = message.from_user.id
    subscriptions = get_user_subscriptions(user_id)

    if not subscriptions:
        await message.answer("Вы не подписаны ни на один источник.", reply_markup=main_keyboard())
        return

    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=f"❌ {s}")] for s in subscriptions] +
                 [[KeyboardButton(text="❌ Отписаться от всех")], [KeyboardButton(text="🔙 Назад")]],
        resize_keyboard=True
    )
    await message.answer("Выберите источник, от которого хотите отписаться:", reply_markup=keyboard)

# Обработчик отписки от всех источников
@dp.message(F.text == "❌ Отписаться от всех")
async def unsubscribe_all(message: types.Message):
    user_id = message.from_user.id
    subscriptions = get_user_subscriptions(user_id)

    if subscriptions:
        remove_all_subscriptions(user_id)
        await message.answer("Вы отписались от всех источников.", reply_markup=main_keyboard())
    else:
        await message.answer("Вы не подписаны ни на один источник.", reply_markup=main_keyboard())

# Обработчик отписки от конкретного источника
@dp.message(F.text.startswith("❌ "))
async def unsubscribe_source(message: types.Message):
    user_id = message.from_user.id
    source = message.text.replace("❌ ", "").strip()

    subscriptions = get_user_subscriptions(user_id)

    if source in subscriptions:
        remove_subscription(user_id, source)
        await message.answer(f"Вы отписались от {source}.", reply_markup=main_keyboard())
    else:
        await message.answer("Некорректный источник или вы на него не подписаны.", reply_markup=main_keyboard())


# Функция получения подписок
def get_subscriptions():
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()
    cur.execute("SELECT user_id, source FROM subscriptions")
    subscriptions = cur.fetchall()
    cur.close()
    conn.close()
    return subscriptions

# Функция отправки новостей подписчикам
async def send_daily_news():
    subscriptions = get_subscriptions()
    for user_id, source in subscriptions:
        news = fetch_rss_news(NEWS_SOURCES[source])
        if news:
            try:
                await bot.send_message(user_id, f"📰 Новости {source}:\n\n{news}",
                disable_web_page_preview=True,
                parse_mode="Markdown")
            except Exception as e:
                logging.error(f"Ошибка при отправке новостей пользователю {user_id}: {e}")

# Настройка планировщика
scheduler = AsyncIOScheduler()
scheduler.add_job(send_daily_news, "interval", hours=24)  # Раз в сутки

# Запуск бота
async def main():
    scheduler.start()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
