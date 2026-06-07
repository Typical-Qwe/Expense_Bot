from dotenv import load_dotenv
import os
import telebot
from telebot import types

from expense_logic import (
    add_expense,
    get_total,
    clear_expenses,
    get_expenses,
    set_budget,
    get_budget,
    get_month_total,
    get_stats
)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в .env")

bot = telebot.TeleBot(BOT_TOKEN)

waiting_budget = {}

CATEGORIES = [
    "Еда",
    "Транспорт",
    "Подписки",
    "Развлечения",
    "Одежда",
    "Здоровье",
    "Образование",
    "Дом",
    "Игровые гаджеты",
    "Акксесуары",
    "Бытовая техника",
    "Косметика",
    "Мебель",
    "Услуги",
    "Другое"
]


def main_keyboard():

    keyboard = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    keyboard.row("➕ Добавить расход")
    keyboard.row("📋 Список", "💰 Итого")
    keyboard.row("💵 Лимит", "📊 Статистика")
    keyboard.row("🗑 Очистить", "❓ Помощь")

    return keyboard


@bot.message_handler(commands=["start", "help"])
def start(message):

    bot.send_message(
        message.chat.id,
        "💸 Трекер расходов\n\n"
        "Формат:\n"
        "<сумма> <описание> <категория>\n\n"
        "Пример:\n"
        "1499 Spotify Premium Подписки\n\n"
        "Категории:\n"
        + "\n".join(CATEGORIES),
        reply_markup=main_keyboard()
    )


@bot.message_handler(func=lambda m: m.text == "❓ Помощь")
def help_button(message):
    start(message)


# ---------- ЛИСТ ----------

@bot.message_handler(commands=["list"])
@bot.message_handler(func=lambda m: m.text == "📋 Список")
def list_expenses(message):

    user_id = message.from_user.id

    expenses = get_expenses(user_id)

    if not expenses:

        bot.send_message(
            message.chat.id,
            "📭 Расходов пока нет."
        )
        return

    text = "📋 Ваши расходы:\n\n"

    for i, expense in enumerate(expenses, start=1):

        text += (
            f"{i}. 💰 {expense['amount']} ₽\n"
            f"📝 {expense['description']}\n"
            f"📂 {expense['category']}\n"
            f"📅 {expense['date']}\n\n"
        )

    bot.send_message(message.chat.id, text)


# ---------- ИТОГО ----------

@bot.message_handler(commands=["total"])
@bot.message_handler(func=lambda m: m.text == "💰 Итого")
def total(message):

    user_id = message.from_user.id

    total_sum = get_total(user_id)

    bot.send_message(
        message.chat.id,
        f"💰 Общая сумма:\n{total_sum} ₽"
    )


# ---------- ЛИМИТ ----------

@bot.message_handler(commands=["setlimit"])
@bot.message_handler(func=lambda m: m.text == "💵 Лимит")
def budget_menu(message):

    user_id = message.from_user.id

    current = get_budget(user_id)

    if current:

        bot.send_message(
            message.chat.id,
            f"💵 Текущий лимит:\n{current} ₽\n\n"
            f"Введите новый лимит:"
        )

    else:

        bot.send_message(
            message.chat.id,
            "Введите месячный лимит:"
        )

    waiting_budget[user_id] = True


@bot.message_handler(commands=["limit"])
def show_limit(message):

    user_id = message.from_user.id

    limit = get_budget(user_id)

    if not limit:

        bot.send_message(
            message.chat.id,
            "❌ Лимит не установлен."
        )
        return

    spent = get_month_total(user_id)

    left = limit - spent

    bot.send_message(
        message.chat.id,
        f"💵 Лимит месяца: {limit} ₽\n"
        f"💸 Потрачено: {spent} ₽\n"
        f"📉 Осталось: {left} ₽"
    )


# ---------- СТАТИСТИКА ----------

@bot.message_handler(commands=["stats"])
@bot.message_handler(func=lambda m: m.text == "📊 Статистика")
def statistics(message):

    user_id = message.from_user.id

    stats = get_stats(user_id)

    if not stats:

        bot.send_message(
            message.chat.id,
            "📭 Нет данных."
        )
        return

    total_sum = get_total(user_id)

    text = "📊 Статистика за всё время\n\n"

    for category, amount in stats:

        percent = round(
            amount / total_sum * 100,
            1
        )

        text += (
            f"📂 {category} — "
            f"{amount} ₽ "
            f"({percent}%)\n"
        )

    text += f"\n💰 Всего: {total_sum} ₽"

    bot.send_message(
        message.chat.id,
        text
    )


# ---------- ОЧИСТКА ----------

@bot.message_handler(commands=["clear"])
@bot.message_handler(func=lambda m: m.text == "🗑 Очистить")
def clear_all(message):

    user_id = message.from_user.id

    clear_expenses(user_id)

    bot.send_message(
        message.chat.id,
        "🗑 Все расходы удалены."
    )


# ---------- ПОДСКАЗКА ----------

@bot.message_handler(func=lambda m: m.text == "➕ Добавить расход")
def add_help(message):

    bot.send_message(
        message.chat.id,
        "Введите расход:\n\n"
        "<сумма> <описание> <категория>"
    )


# ---------- ТЕКСТ ----------

@bot.message_handler(content_types=["text"])
def create_expense(message):

    user_id = message.from_user.id

    # установка лимита

    if waiting_budget.get(user_id):

        try:

            limit = float(message.text)

            set_budget(
                user_id,
                limit
            )

            waiting_budget.pop(user_id)

            bot.send_message(
                message.chat.id,
                f"✅ Лимит установлен:\n{limit} ₽"
            )

        except:

            bot.send_message(
                message.chat.id,
                "❌ Введите число."
            )

        return

    if message.text.startswith("/"):
        return

    if message.text in [
        "➕ Добавить расход",
        "📋 Список",
        "💰 Итого",
        "💵 Лимит",
        "📊 Статистика",
        "🗑 Очистить",
        "❓ Помощь"
    ]:
        return

    try:

        parts = message.text.split()

        if len(parts) < 3:

            bot.send_message(
                message.chat.id,
                "❌ Формат:\n"
                "<сумма> <описание> <категория>"
            )
            return

        amount = float(parts[0])

        category = parts[-1]

        description = " ".join(
            parts[1:-1]
        )

        if category not in CATEGORIES:

            bot.send_message(
                message.chat.id,
                "❌ Неизвестная категория."
            )
            return

        add_expense(
            user_id,
            amount,
            description,
            category
        )

        text = (
            f"✅ Расход добавлен\n\n"
            f"💰 {amount} ₽\n"
            f"📝 {description}\n"
            f"📂 {category}"
        )

        # проверка лимита

        limit = get_budget(user_id)

        if limit:

            month_total = get_month_total(
                user_id
            )

            if month_total > limit:

                over = month_total - limit

                text += (
                    f"\n\n🚨 Лимит превышен!\n"
                    f"Лимит: {limit} ₽\n"
                    f"Потрачено: {month_total} ₽\n"
                    f"Перерасход: {over} ₽"
                )

            else:

                left = limit - month_total

                text += (
                    f"\n\n💵 Лимит: {limit} ₽\n"
                    f"📉 Осталось: {left} ₽"
                )

        bot.send_message(
            message.chat.id,
            text
        )

    except ValueError:

        bot.send_message(
            message.chat.id,
            "❌ Сумма должна быть числом."
        )

    except Exception as e:

        bot.send_message(
            message.chat.id,
            f"❌ Ошибка:\n{e}"
        )


print("Бот запущен...")
bot.infinity_polling()