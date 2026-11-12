import json
import logging
import os
from datetime import datetime
from telegram import ReplyKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from dotenv import load_dotenv 
load_dotenv()
# ЗАМЕНИТЕ ЭТУ СТРОКУ НА ТОКЕН ОТ @BotFather:
TOKEN = os.environ.get('TOKEN')
# Имя файла для сохранения базы данных пользователей
DATA_FILE = "users.json"

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# --- Функции для работы с JSON ---

def load_users() -> dict:
    """Загружает словарь пользователей из файла. Если файла нет — возвращает пустой dict."""
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Ошибка при чтении файла {DATA_FILE}: {e}")
        return {}


def save_users(users_data: dict) -> None:
    """Сохраняет словарь users в JSON (ensure_ascii=False, indent=2)."""
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(users_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Ошибка при записи в файл {DATA_FILE}: {e}")


# Загружаем базу данных при старте бота
users = load_users()


def get_or_create_user(user) -> dict:
    """Возвращает данные пользователя или создает новую анкету (user_id всегда строка)."""
    user_id = str(user.id)  # Ключи в JSON могут быть только строками
    if user_id not in users:
        users[user_id] = {
            "name": user.first_name or "Друг",
            "favorite_movie": "Не указано",
            "comment": "Нет комментариев",
            "remember": "Пока ничего не сохранено.",
            "joined_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "requests_count": 0
        }
        save_users(users)
    return users[user_id]


# --- Списки контента ---
TOP_FILMS = """🎬 *Топ-15 Фильмов:*

1. Побег из Шоушенка (1994)
2. Крёстный отец (1972)
3. Тёмный рыцарь (2008)
4. Список Шиндлера (1993)
5. 12 разгневанных мужчин (1957)
6. Криминальное чтиво (1994)
7. Властелин колец: Возвращение короля (2003)
8. Хороший, плохой, злой (1966)
9. Бойцовский клуб (1999)
10. Форрест Гамп (1994)
11. Начало (2010)
12. Матрица (1999)
13. Интерстеллар (2014)
14. Зеленая миля (1999)
15. Семь (1995)"""

TOP_CARTOONS = """🎨 *Топ-15 Мультфильмов:*

1. Унесённые призраками (2001)
2. Король Лев (1994)
3. Вверх (2009)
4. ВАЛЛ-И (2008)
5. Тайна Коко (2017)
6. Головоломка (2015)
7. Зверополис (2016)
8. Шрек (2001)
9. Как приручить дракона (2010)
10. История игрушек (1995)
11. Ходячий замок (2004)
12. Рататуй (2007)
13. Человек-паук: Через вселенные (2018)
14. Мой сосед Тоторо (1988)
15. Корпорация монстров (2001)"""

TOP_ANIME = """🍥 *Топ-10 Аниме:*

1. Стальной алхимик: Братство (2009)
2. Атака титанов (2013)
3. Тетрадь смерти (2006)
4. Врата Стейна (2011)
5. Охотник х Охотник (2011)
6. Клинок, рассекающий демонов (2019)
7. Моя геройская академия (2016)
8. Магическая битва (2020)
9. Ван Пис (1999)
10. Наруто (2002)"""

TOP_DORAMAS = """🌸 *Топ-10 Дорам:*

1. Потомок солнца (2016)
2. Демон / Токкэби (2016)
3. Силачка До Бон Сун (2017)
4. Истинная красота (2020)
5. Псих, но всё в порядке (2020)
6. Винченцо (2021)
7. Деловой предложение (2022)
8. Мы все мертвы (2022)
9. Игра в кальмара (2021)
10. Слава (2022)"""

HELP_TEXT = """🤖 *Справка по командам бота Ая:*

/start — Главное меню и клавиатура
/profile — Посмотреть свою анкету
/setname <имя> — Изменить имя
/setfav <название> — Указать любимый фильм/сериал
/setcomment <текст> — Оставить отзыв о боте
/remember <текст> — Личная заметка
/help — Показать эту справку"""


# --- Функция создания постоянной Reply-клавиатуры внизу экрана ---
def get_reply_keyboard():
    """Создает постоянную клавиатуру с адаптивным размером (resize_keyboard=True)"""
    keyboard = [
        ["🎬 Топ Фильмов", "🎨 Топ Мультфильмов"],
        ["🍥 Топ Аниме", "🌸 Топ Дорам"],
        ["👤 Профиль", "ℹ️ Помощь"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


# --- Обработчики команд ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start: приветствует пользователя и выводит нижнюю клавиатуру"""
    user_data = get_or_create_user(update.effective_user)
    text = (
        f"Привет, {user_data['name']}! 👋\n"
        "Меня зовут *Ая*, я твой персональный гид по миру кино, аниме и дорам! 🍿\n\n"
        "Используй кнопки на клавиатуре внизу экрана:"
    )
    await update.message.reply_text(
        text, 
        parse_mode=ParseMode.MARKDOWN, 
        reply_markup=get_reply_keyboard()
    )


async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /profile: показывает анкету пользователя"""
    user_data = get_or_create_user(update.effective_user)
    text = (
        f"👤 *Профиль пользователя:* `{user_data['name']}`\n"
        f"🎬 *Любимый фильм/сериал:* _{user_data['favorite_movie']}_\n"
        f"💬 *Комментарий о боте:* _{user_data['comment']}_\n"
        f"📝 *Заметка:* _{user_data['remember']}_\n\n"
        f"📊 *Запросов:* `{user_data['requests_count']}` | 📅 *Регистрация:* `{user_data['joined_at']}`\n\n"
        "🛠 *Как обновить данные через команды:* \n"
        "• `/setname Имя` — изменить имя\n"
        "• `/setfav Название` — любимый фильм/сериал\n"
        "• `/setcomment Текст` — отзыв о боте"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=get_reply_keyboard())


async def setname_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохранение имени в JSON"""
    user_id = str(update.effective_user.id)
    new_name = " ".join(context.args).strip()
    if not new_name:
        await update.message.reply_text("⚠️ Укажите имя после команды, например: `/setname Алексей`", parse_mode=ParseMode.MARKDOWN)
        return
    get_or_create_user(update.effective_user)
    users[user_id]["name"] = new_name
    save_users(users)
    await update.message.reply_text(f"✅ Ваше имя изменено на: *{new_name}*", parse_mode=ParseMode.MARKDOWN, reply_markup=get_reply_keyboard())


async def setfav_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохранение любимого фильма/сериала в JSON"""
    user_id = str(update.effective_user.id)
    fav_movie = " ".join(context.args).strip()
    if not fav_movie:
        await update.message.reply_text("⚠️ Укажите название, например: `/setfav Интерстеллар`", parse_mode=ParseMode.MARKDOWN)
        return
    get_or_create_user(update.effective_user)
    users[user_id]["favorite_movie"] = fav_movie
    save_users(users)
    await update.message.reply_text(f"✅ Любимый фильм/сериал сохранен: *{fav_movie}*", parse_mode=ParseMode.MARKDOWN, reply_markup=get_reply_keyboard())


async def setcomment_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохранение комментария о боте в JSON"""
    user_id = str(update.effective_user.id)
    comment_text = " ".join(context.args).strip()
    if not comment_text:
        await update.message.reply_text("⚠️ Напишите отзыв, например: `/setcomment Отличный бот!`", parse_mode=ParseMode.MARKDOWN)
        return
    get_or_create_user(update.effective_user)
    users[user_id]["comment"] = comment_text
    save_users(users)
    await update.message.reply_text("✅ Спасибо! Ваш комментарий о боте сохранен в JSON.", parse_mode=ParseMode.MARKDOWN, reply_markup=get_reply_keyboard())


async def remember_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохранение личной заметки"""
    user_id = str(update.effective_user.id)
    note_text = " ".join(context.args).strip()
    if not note_text:
        await update.message.reply_text("⚠️ Укажите текст заметки, например: `/remember Посмотреть 2 сезон`", parse_mode=ParseMode.MARKDOWN)
        return
    get_or_create_user(update.effective_user)
    users[user_id]["remember"] = note_text
    save_users(users)
    await update.message.reply_text(f"✅ Заметка сохранена: _{note_text}_", parse_mode=ParseMode.MARKDOWN, reply_markup=get_reply_keyboard())


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    await update.message.reply_text(HELP_TEXT, parse_mode=ParseMode.MARKDOWN, reply_markup=get_reply_keyboard())


# --- Обработчик нажатий на постоянные Reply-кнопки (через if / else) ---

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ловит нажатия на кнопки нижней клавиатуры и выдает ответ через if-else"""
    user_id = str(update.effective_user.id)
    get_or_create_user(update.effective_user)

    # Увеличиваем счетчик запросов пользователя и сразу сохраняем в JSON
    users[user_id]["requests_count"] += 1
    save_users(users)

    text = update.message.text

    if text == "🎬 Топ Фильмов":
        await update.message.reply_text(TOP_FILMS, parse_mode=ParseMode.MARKDOWN, reply_markup=get_reply_keyboard())
        
    elif text == "🎨 Топ Мультфильмов":
        await update.message.reply_text(TOP_CARTOONS, parse_mode=ParseMode.MARKDOWN, reply_markup=get_reply_keyboard())
        
    elif text == "🍥 Топ Аниме":
        await update.message.reply_text(TOP_ANIME, parse_mode=ParseMode.MARKDOWN, reply_markup=get_reply_keyboard())
        
    elif text == "🌸 Топ Дорам":
        await update.message.reply_text(TOP_DORAMAS, parse_mode=ParseMode.MARKDOWN, reply_markup=get_reply_keyboard())
        
    elif text == "👤 Профиль":
        await profile_command(update, context)
        
    elif text == "ℹ️ Помощь":
        await update.message.reply_text(HELP_TEXT, parse_mode=ParseMode.MARKDOWN, reply_markup=get_reply_keyboard())
        
    else:
        # Ответ на любые другие текстовые сообщения от пользователя
        await update.message.reply_text(
            "Я тебя не поняла 😅 Воспользуйся кнопками меню внизу или командой /help.",
            reply_markup=get_reply_keyboard()
        )


# --- Главная функция запуска ---

def main():
    application = Application.builder().token(TOKEN).build()

    # Регистрация команд
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("profile", profile_command))
    application.add_handler(CommandHandler("setname", setname_command))
    application.add_handler(CommandHandler("setfav", setfav_command))
    application.add_handler(CommandHandler("setcomment", setcomment_command))
    application.add_handler(CommandHandler("remember", remember_command))
    application.add_handler(CommandHandler("help", help_command))

    # Регистрация обработчика обычных текстовых сообщений (для Reply-кнопок)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))

    logger.info("Бот Ая успешно запущен с Reply-клавиатурой и JSON-сохранением!")
    application.run_polling()


if __name__ == "__main__":
    main()