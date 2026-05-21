"""
bot.py
------
Main entry point for Fitness AI Tracker Telegram bot.

Registers all command and message handlers with python-telegram-bot.
Each handler is an async function that:
  1. Receives a Telegram Update (message, photo, voice, etc.)
  2. Processes it (calls AI, Sheets, Drive, etc.)
  3. Sends a response back to the user

Run with:
  python bot.py
"""

import asyncio
import datetime
import logging
import os
import shutil
from pathlib import Path
PORT = int(os.environ.get("PORT", 10000))

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)
from telegram.constants import ParseMode

# Local modules
import config
import sheets
import analytics
import streaks
import drive
import video
from utils import (
    estimate_food_nutrition,
    format_meal_response,
    format_today_summary,
    format_week_summary,
    format_month_summary,
    format_year_summary,
    format_streak_message,
)

# ── Logging setup ─────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# ── /start ────────────────────────────────────────────────────────────────────

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome message shown when user first opens the bot or sends /start."""
    chat_id = update.effective_chat.id
    sheets.save_chat_id(chat_id)

    text = (
        "👋 *Welcome to Fitness AI Tracker!*\n\n"
        "I help you track your calories, macros, weight, and progress photos "
        "– all stored for free in Google Sheets.\n\n"
        "📋 *Quick start:*\n"
        "• Just type what you ate: _3 eggs and 2 dosa_\n"
        "• Log weight: /weight 82.5\n"
        "• Set calorie goal: /goal 1800\n"
        "• View today: /today\n\n"
        "Type /help to see all commands."
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


# ── /help ─────────────────────────────────────────────────────────────────────

async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display all available commands."""
    text = (
        "📖 *Available Commands*\n\n"
        "🍽 *Food Logging*\n"
        "  Just type your meal (e.g. _3 eggs and 2 dosa_)\n"
        "  Or send a 🎤 voice note\n\n"
        "⚖️ *Weight*\n"
        "  /weight 82.4 — log your weight in kg\n\n"
        "📸 *Photo*\n"
        "  Send a photo with caption /photo\n\n"
        "📊 *Analytics*\n"
        "  /today — today's summary\n"
        "  /week  — 7-day summary\n"
        "  /month — monthly summary\n"
        "  /year  — yearly summary\n\n"
        "🎯 *Goal*\n"
        "  /goal 1800 — set daily calorie target\n\n"
        "🔥 *Streak*\n"
        "  /streak — view your current streak\n\n"
        "⏰ *Daily Reminder*\n"
        "  Bot will message you at 7 AM every day\n\n"
        "ℹ️ *Other*\n"
        "  /start — welcome message\n"
        "  /help  — this message\n"
        "  /reset — delete all data (requires confirmation)\n"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


# ── Text food logging ─────────────────────────────────────────────────────────

async def text_food_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle free-text food messages like "3 eggs and 2 dosa".

    Flow:
      1. Send "processing" message so user knows bot is working
      2. Run two-layer nutrition estimation (local DB → Gemini)
      3. Log to Google Sheets
      4. Update streak
      5. Reply with formatted summary
    """
    user_id  = str(update.effective_user.id)
    food_text = update.message.text.strip()

    # Show the user we're working on it
    processing_msg = await update.message.reply_text("⏳ Estimating nutrition…")

    try:
        # Step 1: estimate nutrition
        nutrition, source = await estimate_food_nutrition(food_text)

        if nutrition["calories"] == 0:
            await processing_msg.edit_text(
                "❓ I couldn't identify that food. Try being more specific,\n"
                "e.g. _2 boiled eggs and 1 cup rice_",
                parse_mode=ParseMode.MARKDOWN,
            )
            return

        # Step 2: log to Sheets
        sheets.log_meal(
            meal_name=food_text,
            calories=nutrition["calories"],
            protein=nutrition["protein"],
            carbs=nutrition["carbs"],
            fat=nutrition["fat"],
        )

        # Step 3: update streak
        streaks.update_streak_on_log(user_id)

        # Step 4: send response
        response = format_meal_response(food_text, nutrition, source)
        await processing_msg.edit_text(response, parse_mode=ParseMode.MARKDOWN)

    except Exception as e:
        logger.error("Error in text_food_handler: %s", e)
        await processing_msg.edit_text(
            "❌ Something went wrong. Please try again later."
        )


# ── Voice note food logging ────────────────────────────────────────────────────

async def voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle voice note messages.

    Flow:
      1. Download OGG file from Telegram
      2. Transcribe with local Whisper
      3. Run the same food estimation pipeline as text
      4. Log and respond
    """
    user_id = str(update.effective_user.id)

    processing_msg = await update.message.reply_text(
        "🎤 Transcribing voice note… (this may take 10-30 seconds)"
    )

    try:
        # Download the voice file
        voice  = update.message.voice
        local_path = await speech.download_voice_file(
            context.bot, voice.file_id, user_id
        )

        if not local_path:
            await processing_msg.edit_text("❌ Failed to download voice note.")
            return

        # Transcribe
        await processing_msg.edit_text("🔊 Transcribing…")
        transcribed_text = await speech.transcribe_voice(local_path)

        if not transcribed_text:
            await processing_msg.edit_text(
                "❌ Could not transcribe the voice note. Please try again or type your meal."
            )
            return

        await processing_msg.edit_text(
            f"📝 Heard: _{transcribed_text}_\n\n⏳ Estimating nutrition…",
            parse_mode=ParseMode.MARKDOWN,
        )

        # Estimate nutrition (same pipeline as text)
        nutrition, source = await estimate_food_nutrition(transcribed_text)

        if nutrition["calories"] == 0:
            await processing_msg.edit_text(
                f"📝 Heard: _{transcribed_text}_\n\n"
                "❓ Couldn't identify the food. Please try again.",
                parse_mode=ParseMode.MARKDOWN,
            )
            return

        # Log to Sheets
        sheets.log_meal(
            meal_name=f"[Voice] {transcribed_text}",
            calories=nutrition["calories"],
            protein=nutrition["protein"],
            carbs=nutrition["carbs"],
            fat=nutrition["fat"],
        )

        # Update streak
        streaks.update_streak_on_log(user_id)

        # Send formatted response
        response = (
            f"📝 Heard: _{transcribed_text}_\n\n"
            + format_meal_response(transcribed_text, nutrition, source)
        )
        await processing_msg.edit_text(response, parse_mode=ParseMode.MARKDOWN)

        # Clean up temp file
        try:
            os.remove(local_path)
        except OSError:
            pass

    except Exception as e:
        logger.error("Error in voice_handler: %s", e)
        await processing_msg.edit_text("❌ Failed to process voice note. Please try again.")


# ── /weight ───────────────────────────────────────────────────────────────────

async def weight_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Log body weight. Usage: /weight 82.4
    """
    user_id = str(update.effective_user.id)

    if not context.args:
        await update.message.reply_text(
            "⚠️ Please provide your weight.\nExample: /weight 82.4"
        )
        return

    try:
        weight = float(context.args[0])
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid weight. Please enter a number.\nExample: /weight 82.4"
        )
        return

    if weight < 20 or weight > 500:
        await update.message.reply_text("❌ Weight seems invalid. Enter in kg (e.g. 82.4).")
        return

    try:
        sheets.log_weight(weight)
        streaks.update_streak_on_log(user_id)

        # Get latest streak for motivational message
        current_streak, _ = streaks.get_streak_info(user_id)
        streak_msg = f"\n🔥 Streak: {current_streak} day{'s' if current_streak != 1 else ''}" if current_streak > 1 else ""

        await update.message.reply_text(
            f"✅ *Weight Logged!*\n\n"
            f"⚖️  {weight} kg recorded today.{streak_msg}",
            parse_mode=ParseMode.MARKDOWN,
        )
    except Exception as e:
        logger.error("Weight logging error: %s", e)
        await update.message.reply_text("❌ Failed to log weight. Please try again.")


# ── /photo ─────────────────────────────────────────────────────────────────────

async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = str(update.effective_user.id)

    if not update.message.photo:
        await update.message.reply_text("📸 Please send a valid photo.")
        return

    processing = await update.message.reply_text("💾 Saving progress photo…")

    try:
        photo = update.message.photo[-1]
        tg_file_id = photo.file_id

        # 1. Save photo to local storage
        local_path = await drive.save_telegram_photo(context.bot, tg_file_id, int(user_id))
        if not local_path:
            await processing.edit_text("❌ Failed to save photo.")
            return

        # 2. Store local path in Sheets
        sheets.log_photo(user_id=user_id, file_id=local_path)
        streaks.update_streak_on_log(user_id)

        await processing.edit_text("✅ Progress photo saved locally and ready for transformation videos!")

    except Exception as e:
        logger.error("Photo handler error: %s", e)
        try:
            await processing.edit_text("❌ Failed to save photo.")
        except Exception:
            pass

# ── /today ─────────────────────────────────────────────────────────────────────

async def today_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show today's calorie and macro summary."""
    user_id = str(update.effective_user.id)
    try:
        data = analytics.get_today_summary(user_id)
        await update.message.reply_text(
            format_today_summary(data), parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        logger.error("Today handler error: %s", e)
        await update.message.reply_text("❌ Failed to fetch today's data. Please try again.")


# ── /week ──────────────────────────────────────────────────────────────────────

async def week_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show a 7-day summary."""
    user_id = str(update.effective_user.id)
    try:
        data = analytics.get_week_summary(user_id)
        await update.message.reply_text(
            format_week_summary(data), parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        logger.error("Week handler error: %s", e)
        await update.message.reply_text("❌ Failed to fetch weekly data.")


# ── /month ─────────────────────────────────────────────────────────────────────

async def month_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show the current month's summary with progress video."""
    user_id = str(update.effective_user.id)
    try:
        data = analytics.get_month_summary(user_id)
        await update.message.reply_text(
            format_month_summary(data), parse_mode=ParseMode.MARKDOWN
        )

        file_ids = sheets.get_month_photo_ids(user_id)
        if not file_ids:
            logger.info("No photos found for month video")
            await update.message.reply_text("📸 No progress photos found this month. Send photos to build a monthly transformation video!")
        elif len(file_ids) < 2:
            await update.message.reply_text("📸 Need at least 2 progress photos to make a video. Keep uploading!")
        else:
            await update.message.reply_text(f"🎬 Generating monthly progress video from {len(file_ids)} photos…")
            images = video.load_images(file_ids)
            if len(images) < 2:
                await update.message.reply_text("⚠️ Could only download {} photo(s). Need at least 2.".format(len(images)))
            else:
                video_path = video.images_to_video(images, f"monthly_{user_id}.mp4", fps=1)
                if video_path:
                    caption = (
                        f"🗓 Monthly Transformation\n"
                        f"Avg calories: {data['avg_calories']} kcal\n"
                        f"Consistency: {data['consistency_pct']}%"
                    )
                    await update.message.reply_video(video=open(video_path, "rb"), caption=caption)

    except Exception as e:
        logger.error("Month handler error: %s", e)
        await update.message.reply_text("❌ Failed to fetch monthly data.")


# ── /year ──────────────────────────────────────────────────────────────────────

async def year_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show the current year's summary with progress video."""
    user_id = str(update.effective_user.id)
    try:
        data = analytics.get_year_summary(user_id)
        await update.message.reply_text(
            format_year_summary(data), parse_mode=ParseMode.MARKDOWN
        )

        file_ids = sheets.get_year_photo_ids(user_id)
        if not file_ids:
            logger.info("No photos found for year video")
            await update.message.reply_text("📸 No progress photos found this year. Send photos to build a yearly transformation video!")
        elif len(file_ids) < 2:
            await update.message.reply_text("📸 Need at least 2 progress photos to make a video. Keep uploading!")
        else:
            await update.message.reply_text(f"🎬 Generating yearly progress video from {len(file_ids)} photos…")
            images = video.load_images(file_ids)
            if len(images) < 2:
                await update.message.reply_text("⚠️ Could only download {} photo(s). Need at least 2.".format(len(images)))
            else:
                video_path = video.images_to_video(images, f"yearly_{user_id}.mp4", fps=1)
                if video_path:
                    caption = (
                        f"🏆 Yearly Transformation\n"
                        f"Avg calories: {data['avg_calories']} kcal\n"
                        f"Longest streak: {data['longest_streak']} days\n"
                        f"Total weight Δ: {data.get('total_weight_change', 'N/A')} kg"
                    )
                    await update.message.reply_video(video=open(video_path, "rb"), caption=caption)

    except Exception as e:
        logger.error("Year handler error: %s", e)
        await update.message.reply_text("❌ Failed to fetch yearly data.")


# ── /streak ────────────────────────────────────────────────────────────────────

async def streak_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show the user's current and best streak."""
    user_id = str(update.effective_user.id)
    try:
        current, best = streaks.get_streak_info(user_id)
        await update.message.reply_text(
            format_streak_message(current, best), parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        logger.error("Streak handler error: %s", e)
        await update.message.reply_text("❌ Failed to fetch streak data.")


# ── /goal ──────────────────────────────────────────────────────────────────────

async def goal_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Set the daily calorie goal. Usage: /goal 1800
    """
    user_id = str(update.effective_user.id)

    if not context.args:
        current_goal = sheets.get_calorie_goal(user_id)
        await update.message.reply_text(
            f"🎯 *Current Calorie Goal:* {current_goal} kcal/day\n\n"
            "To change it: /goal 1800",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    try:
        goal = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Please enter a whole number. Example: /goal 1800")
        return

    if not (500 <= goal <= 10000):
        await update.message.reply_text("❌ Goal must be between 500 and 10,000 kcal.")
        return

    try:
        sheets.set_calorie_goal(user_id, goal)
        await update.message.reply_text(
            f"✅ *Calorie Goal Set!*\n\n"
            f"🎯 Your daily target: *{goal} kcal*\n\n"
            "Use /today to track your progress.",
            parse_mode=ParseMode.MARKDOWN,
        )
    except Exception as e:
        logger.error("Goal handler error: %s", e)
        await update.message.reply_text("❌ Failed to save goal. Please try again.")


# ── /log command (alias for text logging) ─────────────────────────────────────

async def log_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /log command – user can write /log 3 eggs as an alternative.
    Joins the args and passes them to the text food pipeline.
    """
    if not context.args:
        await update.message.reply_text(
            "Usage: /log <food>\nExample: /log 3 eggs and 2 dosa\n\n"
            "Or just type your meal without any command!"
        )
        return

    # Replace the message text with the args so text_food_handler can process it
    update.message.text = " ".join(context.args)
    await text_food_handler(update, context)


# ── /reset ──────────────────────────────────────────────────────────────────────

async def reset_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ask for confirmation before deleting all data."""
    keyboard = [
        [InlineKeyboardButton("🗑 Yes, delete everything", callback_data="reset_confirm")],
        [InlineKeyboardButton("Cancel", callback_data="reset_cancel")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "⚠️ *This will permanently delete ALL your data:*\n"
        "• All meals, weight logs, and goals\n"
        "• All progress photos\n"
        "• Your streak and settings\n\n"
        "Are you sure?",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_markup,
    )


# ── Daily reminder quick-action callbacks ──────────────────────────────────────

async def reminder_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "log_weight":
        await query.message.reply_text(
            "⚖️ Use /weight followed by your weight in kg.\n"
            "Example: `/weight 82.5`",
            parse_mode=ParseMode.MARKDOWN,
        )
    elif query.data == "log_photo":
        await query.message.reply_text(
            "📸 Just send me a photo of yourself and I'll save it as your progress photo!"
        )


async def reset_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "reset_cancel":
        await query.message.edit_text("✅ Reset cancelled. Your data is safe.")
        return

    if query.data != "reset_confirm":
        return

    await query.message.edit_text("⏳ Deleting all data…")

    try:
        sheets.reset_all_data()

        photos_path = Path(config.PHOTOS_DIR)
        if photos_path.exists():
            shutil.rmtree(photos_path)
            photos_path.mkdir(parents=True, exist_ok=True)
            logger.info("Cleared local photos directory")

        await query.message.edit_text(
            "✅ *All data has been deleted.*\n\n"
            "Your sheets and photos directory are now empty. "
            "Use /start to begin fresh!",
            parse_mode=ParseMode.MARKDOWN,
        )
    except Exception as e:
        logger.error("Reset failed: %s", e)
        await query.message.edit_text("❌ Failed to reset data. Please try again.")


# ── Unknown command handler ────────────────────────────────────────────────────

async def unknown_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Catch unknown /commands and suggest /help."""
    await update.message.reply_text(
        "❓ Unknown command. Type /help to see all available commands."
    )


# ── Daily 7am reminder ─────────────────────────────────────────────────────────

async def daily_reminder(context: ContextTypes.DEFAULT_TYPE):
    """Send a morning reminder to log weight and photo."""
    chat_id = sheets.get_chat_id()
    if not chat_id:
        logger.warning("No chat_id stored, cannot send daily reminder")
        return

    keyboard = [
        [InlineKeyboardButton("⚖️ Log Weight", callback_data="log_weight")],
        [InlineKeyboardButton("📸 Send Progress Photo", callback_data="log_photo")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(
        chat_id=chat_id,
        text=(
            "🌅 *Good morning! Time for your daily check-in.*\n\n"
            "Please log your weight and send a progress photo today!"
        ),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_markup,
    )


# ── Main: build and run the bot ───────────────────────────────────────────────

def main():
    config.validate_config()

    # Ensure temp directory exists
    Path(config.TEMP_DIR).mkdir(parents=True, exist_ok=True)

    # Set up Google Sheets structure on startup
    logger.info("Setting up Google Sheets…")
    try:
        sheets.setup_sheets()
        logger.info("Google Sheets ready.")
    except Exception as e:
        logger.error("Google Sheets setup failed (bot will still start, but logging won't persist): %s", e)

    # Build the Telegram Application
    app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()

    # Schedule daily 7am reminder
    if app.job_queue:
        app.job_queue.run_daily(
            daily_reminder,
            time=datetime.time(hour=7, minute=0)
        )
        logger.info("Daily reminder scheduled for 07:00")

    # ── Register handlers ─────────────────────────────────────────────────────
    app.add_handler(CommandHandler("start",  start_handler))
    app.add_handler(CommandHandler("help",   help_handler))
    app.add_handler(CommandHandler("log",    log_command_handler))
    app.add_handler(CommandHandler("weight", weight_handler))
    app.add_handler(CommandHandler("today",  today_handler))
    app.add_handler(CommandHandler("week",   week_handler))
    app.add_handler(CommandHandler("month",  month_handler))
    app.add_handler(CommandHandler("year",   year_handler))
    app.add_handler(CommandHandler("streak", streak_handler))
    app.add_handler(CommandHandler("goal",   goal_handler))
    app.add_handler(CommandHandler("reset",  reset_handler))
    app.add_handler(CallbackQueryHandler(reminder_callback_handler, pattern="^log_"))
    app.add_handler(CallbackQueryHandler(reset_callback_handler, pattern="^reset_"))
    app.add_handler(MessageHandler(filters.PHOTO, photo_handler))
    app.add_handler(MessageHandler(filters.VOICE, voice_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_food_handler))
    app.add_handler(MessageHandler(filters.COMMAND, unknown_command_handler))

    logger.info("🤖 Fitness AI Tracker bot is running…")
    logger.info("Press Ctrl+C to stop.")

    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    # Python 3.14+: ensure an event loop exists before calling run_polling()
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())
    main()
