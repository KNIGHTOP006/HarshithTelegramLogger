"""
sheets.py
---------
All Google Sheets read/write operations.

Google Sheets acts as our free database.
We use the gspread library with a service account for authentication.

Sheet structure (tabs inside one Google Sheet):
  - Meals:   Date | Meal | Calories | Protein | Carbs | Fat
  - Weight:  Date | Weight
  - Photos:  Date | Photo URL
  - Goals:   User | Calorie Goal
  - Streaks: User | Current Streak | Best Streak
"""

import logging
from datetime import date, datetime, timedelta
from functools import lru_cache

import gspread
from google.oauth2.service_account import Credentials
from config import GOOGLE_CREDENTIALS_FILE, GOOGLE_SHEET_ID

logger = logging.getLogger(__name__)

# ── Auth scopes needed by gspread ─────────────────────────────────────────────
SCOPES = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]

# ── Tab (worksheet) names ─────────────────────────────────────────────────────
SHEET_MEALS   = "Meals"
SHEET_WEIGHT  = "Weight"
SHEET_PHOTOS  = "Photos"
SHEET_GOALS   = "Goals"
SHEET_STREAKS = "Streaks"
SHEET_SETTINGS = "Settings"


# ── Connection helper ─────────────────────────────────────────────────────────

def _get_spreadsheet():
    creds = Credentials.from_service_account_file(
        GOOGLE_CREDENTIALS_FILE,
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ],
    )

    client = gspread.authorize(creds)
    return client.open_by_key(GOOGLE_SHEET_ID)

def _get_sheet(sheet_name: str):
    """Return a specific worksheet by name."""
    spreadsheet = _get_spreadsheet()
    try:
        return spreadsheet.worksheet(sheet_name)
    except gspread.exceptions.WorksheetNotFound:
        logger.error("Worksheet '%s' not found. Run setup_sheets() first.", sheet_name)
        raise


# ── One-time setup ────────────────────────────────────────────────────────────

def setup_sheets():
    """
    Create all required worksheets with headers if they don't exist.
    Run this once during bot startup to ensure the sheet structure is ready.
    """
    spreadsheet = _get_spreadsheet()
    existing = [ws.title for ws in spreadsheet.worksheets()]

    sheet_headers = {
        SHEET_MEALS:   ["Date", "Meal", "Calories", "Protein", "Carbs", "Fat"],
        SHEET_WEIGHT:  ["Date", "Weight"],
        SHEET_PHOTOS:  ["Date", "UserID", "FileID"],
        SHEET_GOALS:   ["User", "Calorie Goal"],
        SHEET_STREAKS: ["User", "Current Streak", "Best Streak"],
        SHEET_SETTINGS: ["Key", "Value"],
    }

    for name, headers in sheet_headers.items():
        if name not in existing:
            ws = spreadsheet.add_worksheet(title=name, rows=1000, cols=len(headers))
            ws.append_row(headers)
            logger.info("Created worksheet: %s", name)
        else:
            ws = spreadsheet.worksheet(name)
            existing_headers = ws.row_values(1)
            if existing_headers != headers:
                logger.warning("Recreating '%s' – headers changed from %s to %s", name, existing_headers, headers)
                spreadsheet.del_worksheet(ws)
                ws = spreadsheet.add_worksheet(title=name, rows=1000, cols=len(headers))
                ws.append_row(headers)
            else:
                logger.info("Worksheet already exists: %s", name)


# ── Meals ─────────────────────────────────────────────────────────────────────

def log_meal(meal_name: str, calories: float, protein: float, carbs: float, fat: float):
    """
    Append a meal row to the Meals sheet.

    Args:
        meal_name: human-readable description of the food
        calories, protein, carbs, fat: nutrition values
    """
    sheet = _get_sheet(SHEET_MEALS)
    today = date.today().isoformat()  # e.g. "2024-01-15"
    sheet.append_row([today, meal_name, calories, protein, carbs, fat])
    logger.info("Meal logged: %s – %s kcal", meal_name, calories)


def get_meals_today() -> list[dict]:
    """
    Return all meals logged today.

    Returns:
        List of dicts with keys: date, meal, calories, protein, carbs, fat
    """
    sheet = _get_sheet(SHEET_MEALS)
    today = date.today().isoformat()
    all_rows = sheet.get_all_records()  # list of dicts (uses header row)

    return [row for row in all_rows if str(row.get("Date", "")) == today]


def get_meals_for_period(start_date: date, end_date: date) -> list[dict]:
    """
    Return all meals between start_date and end_date (inclusive).
    """
    sheet = _get_sheet(SHEET_MEALS)
    all_rows = sheet.get_all_records()

    result = []
    for row in all_rows:
        try:
            row_date = date.fromisoformat(str(row.get("Date", "")))
            if start_date <= row_date <= end_date:
                result.append(row)
        except ValueError:
            continue  # skip rows with invalid dates

    return result


def get_all_meals() -> list[dict]:
    """Return every meal row in the sheet."""
    sheet = _get_sheet(SHEET_MEALS)
    return sheet.get_all_records()


# ── Weight ─────────────────────────────────────────────────────────────────────

def log_weight(weight_kg: float):
    """Append today's weight to the Weight sheet."""
    sheet = _get_sheet(SHEET_WEIGHT)
    today = date.today().isoformat()
    sheet.append_row([today, weight_kg])
    logger.info("Weight logged: %s kg", weight_kg)


def get_weight_for_period(start_date: date, end_date: date) -> list[dict]:
    """Return weight entries between two dates."""
    sheet = _get_sheet(SHEET_WEIGHT)
    all_rows = sheet.get_all_records()

    result = []
    for row in all_rows:
        try:
            row_date = date.fromisoformat(str(row.get("Date", "")))
            if start_date <= row_date <= end_date:
                result.append(row)
        except ValueError:
            continue

    return result


def get_latest_weight() -> float | None:
    """Return the most recently logged weight, or None."""
    sheet = _get_sheet(SHEET_WEIGHT)
    all_rows = sheet.get_all_records()
    if not all_rows:
        return None
    # The last row has the most recent entry
    try:
        return float(all_rows[-1].get("Weight", 0))
    except (ValueError, TypeError):
        return None


# ── Photos ─────────────────────────────────────────────────────────────────────
def log_photo(user_id: str, file_id: str):
    sheet = _get_sheet(SHEET_PHOTOS)
    today = datetime.now().isoformat()
    sheet.append_row([today, str(user_id), file_id])
    logger.info("Photo logged for user %s", user_id)


# ── Goals ──────────────────────────────────────────────────────────────────────

def get_calorie_goal(user_id: str) -> int:
    """
    Retrieve the user's calorie goal.
    Returns DEFAULT_CALORIE_GOAL if not set.
    """
    from config import DEFAULT_CALORIE_GOAL
    sheet = _get_sheet(SHEET_GOALS)
    all_rows = sheet.get_all_records()

    for row in all_rows:
        if str(row.get("User", "")) == str(user_id):
            try:
                return int(row.get("Calorie Goal", DEFAULT_CALORIE_GOAL))
            except (ValueError, TypeError):
                return DEFAULT_CALORIE_GOAL

    return DEFAULT_CALORIE_GOAL


def set_calorie_goal(user_id: str, goal: int):
    """
    Set or update the user's calorie goal.
    If the user already has a row, update it; otherwise append.
    """
    sheet = _get_sheet(SHEET_GOALS)
    all_values = sheet.get_all_values()  # includes header row

    # Find if user already has a row (skip header at index 0)
    for i, row in enumerate(all_values[1:], start=2):  # gspread rows are 1-indexed
        if row and str(row[0]) == str(user_id):
            sheet.update_cell(i, 2, goal)  # column 2 = Calorie Goal
            logger.info("Updated calorie goal for user %s: %s", user_id, goal)
            return

    # New user – append a row
    sheet.append_row([str(user_id), goal])
    logger.info("Set calorie goal for user %s: %s", user_id, goal)


# ── Streaks ────────────────────────────────────────────────────────────────────

def get_streak(user_id: str) -> tuple[int, int]:
    """
    Return (current_streak, best_streak) for a user.
    Returns (0, 0) if the user has no streak record yet.
    """
    sheet = _get_sheet(SHEET_STREAKS)
    all_rows = sheet.get_all_records()

    for row in all_rows:
        if str(row.get("User", "")) == str(user_id):
            return (
                int(row.get("Current Streak", 0)),
                int(row.get("Best Streak", 0)),
            )

    return (0, 0)


def update_streak(user_id: str, current: int, best: int):
    """
    Write the updated streak values to the Streaks sheet.
    Creates a new row if the user doesn't exist.
    """
    sheet = _get_sheet(SHEET_STREAKS)
    all_values = sheet.get_all_values()

    for i, row in enumerate(all_values[1:], start=2):
        if row and str(row[0]) == str(user_id):
            sheet.update_cell(i, 2, current)
            sheet.update_cell(i, 3, best)
            return

    # New user
    sheet.append_row([str(user_id), current, best])


# ── Utility: check if user logged today ───────────────────────────────────────

def user_logged_today() -> bool:
    """
    Check if there is at least one meal or weight entry for today.
    Used by the streak system.
    """
    today = date.today().isoformat()

    meals_today = get_meals_today()
    if meals_today:
        return True

    weight_rows = get_weight_for_period(date.today(), date.today())
    return bool(weight_rows)

def _get_photo_ids(user_id: str, days: int) -> list[str]:
    """Return FileID values for a user within the last N days."""
    sheet = _get_sheet(SHEET_PHOTOS)
    values = sheet.get_all_values()
    if not values:
        return []

    # header row is values[0]; data starts at values[1:]
    # columns: 0=Date, 1=UserID, 2=FileID
    cutoff = datetime.now() - timedelta(days=days)
    result = []

    for row in values[1:]:
        if len(row) < 3:
            continue
        if row[1] != str(user_id):
            continue
        try:
            dt = datetime.fromisoformat(row[0])
        except (ValueError, IndexError):
            continue
        if dt >= cutoff:
            result.append(row[2])

    return result


def get_month_photo_ids(user_id: str) -> list[str]:
    return _get_photo_ids(user_id, 30)


def get_year_photo_ids(user_id: str) -> list[str]:
    return _get_photo_ids(user_id, 365)


# ── Reset ──────────────────────────────────────────────────────────────────────

def reset_all_data():
    """Clear all data rows from every sheet while keeping headers."""
    sheet_names = [SHEET_MEALS, SHEET_WEIGHT, SHEET_PHOTOS, SHEET_GOALS, SHEET_STREAKS]
    spreadsheet = _get_spreadsheet()
    for name in sheet_names:
        try:
            ws = spreadsheet.worksheet(name)
            rows = ws.row_count
            if rows > 1:
                ws.delete_rows(2, rows)
            logger.info("Cleared sheet: %s", name)
        except Exception as e:
            logger.error("Failed to clear sheet %s: %s", name, e)


# ── Settings (chat_id, etc.) ───────────────────────────────────────────────────

def save_chat_id(chat_id: int):
    """Persist the user's chat_id so the daily reminder can reach them."""
    sheet = _get_sheet(SHEET_SETTINGS)
    values = sheet.get_all_values()
    for i, row in enumerate(values[1:], start=2):
        if row and row[0] == "chat_id":
            sheet.update_cell(i, 2, str(chat_id))
            return
    sheet.append_row(["chat_id", str(chat_id)])


def get_chat_id() -> int | None:
    """Return the stored chat_id, or None."""
    sheet = _get_sheet(SHEET_SETTINGS)
    values = sheet.get_all_values()
    for row in values[1:]:
        if row and row[0] == "chat_id" and len(row) > 1 and row[1]:
            try:
                return int(row[1])
            except ValueError:
                return None
    return None