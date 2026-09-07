import os
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set")

# Simple per-user run history stored while the bot is running.
# No external API or API key is required.
runs = {}


def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏃 Log a Run", callback_data="log")],
        [InlineKeyboardButton("📊 My Stats", callback_data="stats")],
        [InlineKeyboardButton("📋 My Runs", callback_data="runs")],
    ])


def format_run(run, number):
    return (
        f"{number}. {run['distance']:.2f} km • {run['minutes']} min\n"
        f"   {run['date']}"
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🏃 <b>G168 Run Bot</b>\n\n"
        "A simple running utility for keeping track of your runs and progress.\n\n"
        "Choose an option below to get started."
    )
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=menu())


async def log_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["awaiting_run"] = True
    await update.message.reply_text(
        "Send your run in this format:\n\n"
        "<code>distance time</code>\n\n"
        "Example: <code>5.2 32</code>\n"
        "That records 5.2 km in 32 minutes.",
        parse_mode="HTML",
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("awaiting_run"):
        return

    parts = update.message.text.strip().split()
    if len(parts) != 2:
        await update.message.reply_text("Please use this format: <code>5.2 32</code>", parse_mode="HTML")
        return

    try:
        distance = float(parts[0].replace(",", "."))
        minutes = int(parts[1])
        if distance <= 0 or minutes <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("Please enter a valid distance and time, for example <code>5.2 32</code>.", parse_mode="HTML")
        return

    user_id = update.effective_user.id
    runs.setdefault(user_id, []).append({
        "distance": distance,
        "minutes": minutes,
        "date": datetime.now().strftime("%d %b %Y"),
    })
    context.user_data["awaiting_run"] = False

    pace = minutes / distance
    pace_min = int(pace)
    pace_sec = round((pace - pace_min) * 60)
    if pace_sec == 60:
        pace_min += 1
        pace_sec = 0

    await update.message.reply_text(
        f"✅ Run saved!\n\n"
        f"Distance: <b>{distance:.2f} km</b>\n"
        f"Time: <b>{minutes} min</b>\n"
        f"Average pace: <b>{pace_min}:{pace_sec:02d} min/km</b>",
        parse_mode="HTML",
        reply_markup=menu(),
    )


async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    history = runs.get(user_id, [])

    if not history:
        await query.message.reply_text("You haven't logged any runs yet. Tap 🏃 Log a Run to add your first one.", reply_markup=menu())
        return

    total_distance = sum(r["distance"] for r in history)
    total_time = sum(r["minutes"] for r in history)
    average_distance = total_distance / len(history)

    await query.message.reply_text(
        "📊 <b>Your Running Stats</b>\n\n"
        f"Runs: <b>{len(history)}</b>\n"
        f"Total distance: <b>{total_distance:.2f} km</b>\n"
        f"Total time: <b>{total_time} min</b>\n"
        f"Average run: <b>{average_distance:.2f} km</b>",
        parse_mode="HTML",
        reply_markup=menu(),
    )


async def show_runs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    history = runs.get(user_id, [])

    if not history:
        await query.message.reply_text("You haven't logged any runs yet.", reply_markup=menu())
        return

    recent = history[-10:][::-1]
    lines = ["📋 <b>Your Recent Runs</b>", ""]
    for index, run in enumerate(recent, 1):
        lines.append(format_run(run, index))

    await query.message.reply_text("\n".join(lines), parse_mode="HTML", reply_markup=menu())


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data == "log":
        context.user_data["awaiting_run"] = True
        await query.answer()
        await query.message.reply_text(
            "Send your run as <code>distance time</code>.\nExample: <code>5.2 32</code>",
            parse_mode="HTML",
        )
    elif query.data == "stats":
        await show_stats(update, context)
    elif query.data == "runs":
        await show_runs(update, context)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "<b>G168 Run Bot</b>\n\n"
        "/start - Open the main menu\n"
        "/log - Log a run\n"
        "/stats - View your running stats\n"
        "/runs - View recent runs\n"
        "/help - Show this help message",
        parse_mode="HTML",
        reply_markup=menu(),
    )


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Reuse the same stats display for the command interface.
    user_id = update.effective_user.id
    history = runs.get(user_id, [])
    if not history:
        await update.message.reply_text("You haven't logged any runs yet. Use /log to add your first run.", reply_markup=menu())
        return

    total_distance = sum(r["distance"] for r in history)
    total_time = sum(r["minutes"] for r in history)
    await update.message.reply_text(
        "📊 <b>Your Running Stats</b>\n\n"
        f"Runs: <b>{len(history)}</b>\n"
        f"Total distance: <b>{total_distance:.2f} km</b>\n"
        f"Total time: <b>{total_time} min</b>",
        parse_mode="HTML",
        reply_markup=menu(),
    )


async def runs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    history = runs.get(user_id, [])
    if not history:
        await update.message.reply_text("You haven't logged any runs yet.", reply_markup=menu())
        return

    recent = history[-10:][::-1]
    lines = ["📋 <b>Your Recent Runs</b>", ""]
    for index, run in enumerate(recent, 1):
        lines.append(format_run(run, index))
    await update.message.reply_text("\n".join(lines), parse_mode="HTML", reply_markup=menu())


app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("log", log_command))
app.add_handler(CommandHandler("stats", stats_command))
app.add_handler(CommandHandler("runs", runs_command))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(CallbackQueryHandler(button_handler))
app.add_handler(MessageHandler if False else __import__('telegram.ext', fromlist=['MessageHandler']).MessageHandler(__import__('telegram.ext', fromlist=['filters']).filters.TEXT & ~__import__('telegram.ext', fromlist=['filters']).filters.COMMAND, handle_message))

app.run_polling(allowed_updates=Update.ALL_TYPES)
