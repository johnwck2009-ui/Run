import os
from datetime import datetime

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set")

# Simple per-user run history stored while the bot is running.
# No external API or API key is required.
runs = {}


def menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🏃 Log a Run", callback_data="log")],
            [
                InlineKeyboardButton("📊 My Stats", callback_data="stats"),
                InlineKeyboardButton("📋 My Runs", callback_data="runs"),
            ],
            [InlineKeyboardButton("ℹ️ How It Works", callback_data="help")],
        ]
    )


def back_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("⬅️ Main Menu", callback_data="home")]]
    )


def format_pace(distance: float, minutes: int) -> str:
    pace = minutes / distance
    pace_min = int(pace)
    pace_sec = round((pace - pace_min) * 60)
    if pace_sec == 60:
        pace_min += 1
        pace_sec = 0
    return f"{pace_min}:{pace_sec:02d} min/km"


def format_run(run: dict, number: int) -> str:
    return (
        f"{number}. {run['distance']:.2f} km • {run['minutes']} min\n"
        f"   Pace: {run['pace']}\n"
        f"   {run['date']}"
    )


def home_text() -> str:
    return (
        "🏃 <b>G168 Run Bot</b>\n\n"
        "A simple running tracker for recording your runs and checking your progress.\n\n"
        "Log your distance and time to calculate your pace, view your running stats, and see your recent runs.\n\n"
        "Choose an option below to get started."
    )


def help_text() -> str:
    return (
        "ℹ️ <b>How G168 Run Bot works</b>\n\n"
        "1. Tap <b>Log a Run</b>.\n"
        "2. Enter your distance in kilometres and your time in minutes.\n"
        "3. Your average pace is calculated automatically.\n"
        "4. Use <b>My Stats</b> to see your totals and <b>My Runs</b> to review recent entries.\n\n"
        "Example: <code>5.2 32</code> means 5.2 km in 32 minutes."
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data["awaiting_run"] = False
    await update.message.reply_text(
        home_text(), parse_mode="HTML", reply_markup=menu()
    )


async def log_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data["awaiting_run"] = True
    await update.message.reply_text(
        "🏃 <b>Log a Run</b>\n\n"
        "Send your distance and time in this format:\n\n"
        "<code>distance time</code>\n\n"
        "Example: <code>5.2 32</code>\n"
        "This records 5.2 km in 32 minutes.",
        parse_mode="HTML",
        reply_markup=back_menu(),
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return

    if not context.user_data.get("awaiting_run"):
        await update.message.reply_text(
            "Use the buttons below to log a run or view your stats.",
            reply_markup=menu(),
        )
        return

    parts = update.message.text.strip().replace(",", ".").split()
    if len(parts) != 2:
        await update.message.reply_text(
            "Please use this format: <code>5.2 32</code>",
            parse_mode="HTML",
            reply_markup=back_menu(),
        )
        return

    try:
        distance = float(parts[0])
        minutes = int(parts[1])
        if distance <= 0 or minutes <= 0 or distance > 1000 or minutes > 1440:
            raise ValueError
    except ValueError:
        await update.message.reply_text(
            "Please enter a valid distance and time, for example <code>5.2 32</code>.",
            parse_mode="HTML",
            reply_markup=back_menu(),
        )
        return

    user_id = update.effective_user.id
    pace = format_pace(distance, minutes)
    runs.setdefault(user_id, []).append(
        {
            "distance": distance,
            "minutes": minutes,
            "pace": pace,
            "date": datetime.now().strftime("%d %b %Y"),
        }
    )
    context.user_data["awaiting_run"] = False

    await update.message.reply_text(
        "✅ <b>Run saved</b>\n\n"
        f"Distance: <b>{distance:.2f} km</b>\n"
        f"Time: <b>{minutes} min</b>\n"
        f"Average pace: <b>{pace}</b>",
        parse_mode="HTML",
        reply_markup=menu(),
    )


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    history = runs.get(user_id, [])

    if not history:
        await update.message.reply_text(
            "You haven't logged any runs yet. Tap 🏃 Log a Run to add your first one.",
            reply_markup=menu(),
        )
        return

    total_distance = sum(item["distance"] for item in history)
    total_time = sum(item["minutes"] for item in history)
    average_distance = total_distance / len(history)
    overall_pace = format_pace(total_distance, total_time)

    await update.message.reply_text(
        "📊 <b>Your Running Stats</b>\n\n"
        f"Runs: <b>{len(history)}</b>\n"
        f"Total distance: <b>{total_distance:.2f} km</b>\n"
        f"Total time: <b>{total_time} min</b>\n"
        f"Average run: <b>{average_distance:.2f} km</b>\n"
        f"Overall pace: <b>{overall_pace}</b>",
        parse_mode="HTML",
        reply_markup=menu(),
    )


async def runs_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    history = runs.get(user_id, [])

    if not history:
        await update.message.reply_text(
            "You haven't logged any runs yet. Tap 🏃 Log a Run to add your first one.",
            reply_markup=menu(),
        )
        return

    recent = history[-10:][::-1]
    lines = ["📋 <b>Your Recent Runs</b>", ""]
    for index, run in enumerate(recent, 1):
        lines.append(format_run(run, index))

    await update.message.reply_text(
        "\n".join(lines), parse_mode="HTML", reply_markup=menu()
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == "home":
        context.user_data["awaiting_run"] = False
        await query.edit_message_text(
            home_text(), parse_mode="HTML", reply_markup=menu()
        )
        return

    if query.data == "log":
        context.user_data["awaiting_run"] = True
        await query.edit_message_text(
            "🏃 <b>Log a Run</b>\n\n"
            "Send your distance and time in this format:\n\n"
            "<code>distance time</code>\n\n"
            "Example: <code>5.2 32</code>\n"
            "This records 5.2 km in 32 minutes.",
            parse_mode="HTML",
            reply_markup=back_menu(),
        )
        return

    if query.data == "stats":
        user_id = query.from_user.id
        history = runs.get(user_id, [])

        if not history:
            await query.edit_message_text(
                "📊 <b>Your Running Stats</b>\n\n"
                "You haven't logged any runs yet.\n\n"
                "Tap <b>Log a Run</b> to add your first run.",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [InlineKeyboardButton("🏃 Log a Run", callback_data="log")],
                        [InlineKeyboardButton("⬅️ Main Menu", callback_data="home")],
                    ]
                ),
            )
            return

        total_distance = sum(item["distance"] for item in history)
        total_time = sum(item["minutes"] for item in history)
        average_distance = total_distance / len(history)
        overall_pace = format_pace(total_distance, total_time)

        await query.edit_message_text(
            "📊 <b>Your Running Stats</b>\n\n"
            f"Runs: <b>{len(history)}</b>\n"
            f"Total distance: <b>{total_distance:.2f} km</b>\n"
            f"Total time: <b>{total_time} min</b>\n"
            f"Average run: <b>{average_distance:.2f} km</b>\n"
            f"Overall pace: <b>{overall_pace}</b>",
            parse_mode="HTML",
            reply_markup=back_menu(),
        )
        return

    if query.data == "runs":
        user_id = query.from_user.id
        history = runs.get(user_id, [])

        if not history:
            await query.edit_message_text(
                "📋 <b>Your Recent Runs</b>\n\n"
                "You haven't logged any runs yet.",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [InlineKeyboardButton("🏃 Log a Run", callback_data="log")],
                        [InlineKeyboardButton("⬅️ Main Menu", callback_data="home")],
                    ]
                ),
            )
            return

        recent = history[-10:][::-1]
        lines = ["📋 <b>Your Recent Runs</b>", ""]
        for index, run in enumerate(recent, 1):
            lines.append(format_run(run, index))

        await query.edit_message_text(
            "\n".join(lines), parse_mode="HTML", reply_markup=back_menu()
        )
        return

    if query.data == "help":
        await query.edit_message_text(
            help_text(), parse_mode="HTML", reply_markup=back_menu()
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        help_text(), parse_mode="HTML", reply_markup=menu()
    )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    print(f"Bot error: {context.error}")


app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("log", log_command))
app.add_handler(CommandHandler("stats", stats_command))
app.add_handler(CommandHandler("runs", runs_command))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(CallbackQueryHandler(button_handler))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_error_handler(error_handler)

app.run_polling(allowed_updates=Update.ALL_TYPES)
