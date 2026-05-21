"""
config.py
---------
Central configuration file for Fitness AI Tracker bot.
Loads all environment variables from .env file.
Every secret/config value should be read from here.
"""

import os
from dotenv import load_dotenv

# Load variables from .env file into the environment
load_dotenv()


# ── Telegram ──────────────────────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# ── Gemini AI ─────────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# ── Google Sheets ─────────────────────────────────────────────────────────────
# The ID is the long string in the Google Sheets URL:
# https://docs.google.com/spreadsheets/d/<SHEET_ID>/edit
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "")

# Path to the service-account JSON credentials file (downloaded from GCP)
GOOGLE_CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")

# ── Google Drive ──────────────────────────────────────────────────────────────
# Folder ID where progress photos will be stored (from Drive URL)
GOOGLE_DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID", "")

# ── Whisper (local speech-to-text) ────────────────────────────────────────────
# Model size: "tiny", "base", "small", "medium", "large"
# "base" is a good balance of speed vs accuracy for free usage
WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "base")

# ── App Settings ──────────────────────────────────────────────────────────────
# Default daily calorie target (used before user sets their own)
DEFAULT_CALORIE_GOAL = int(os.getenv("DEFAULT_CALORIE_GOAL", "2000"))

# Temporary directory for downloaded voice notes / images
TEMP_DIR = os.getenv("TEMP_DIR", "/tmp/fitness_bot")

# Persistent directory for progress photos
PHOTOS_DIR = os.getenv("PHOTOS_DIR", "photos")


def validate_config():
    """
    Check that all required environment variables are set.
    Raises ValueError if any required key is missing.
    Call this once at startup (in bot.py).
    """
    required = {
        "TELEGRAM_BOT_TOKEN": TELEGRAM_BOT_TOKEN,
        "GEMINI_API_KEY": GEMINI_API_KEY,
        "GOOGLE_SHEET_ID": GOOGLE_SHEET_ID,
    }
    missing = [k for k, v in required.items() if not v]
    if missing:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing)}\n"
            "Please copy .env.example → .env and fill in your keys."
        )
