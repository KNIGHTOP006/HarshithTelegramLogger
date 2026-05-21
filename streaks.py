"""
streaks.py
----------
Manages the user's daily logging streak.

A streak counts if the user logs food OR weight on a given day.
Streak is updated every time a meal or weight is logged.

Logic:
  - If user already logged today → streak unchanged (don't double-count)
  - If user logged yesterday → increment streak
  - If user skipped a day → reset streak to 1 (they just logged today)
"""

import logging
from datetime import date, timedelta

import sheets

logger = logging.getLogger(__name__)


def update_streak_on_log(user_id: str):
    """
    Call this every time a meal or weight is successfully logged.

    Reads the current streak from Sheets, decides whether to increment/reset,
    then writes the updated values back.
    """
    current_streak, best_streak = sheets.get_streak(str(user_id))
    today = date.today()

    # Check if user already has a meal/weight logged today
    # (We don't increment more than once per day)
    today_meals   = sheets.get_meals_today()
    today_weights = sheets.get_weight_for_period(today, today)

    # Count total entries today (this call happens AFTER the new log, so ≥1)
    total_today = len(today_meals) + len(today_weights)

    if total_today <= 1:
        # This is the FIRST log of today – decide whether to extend or reset streak

        if current_streak == 0:
            # First ever log
            new_streak = 1
        else:
            # Check if they logged yesterday
            yesterday_start = today - timedelta(days=1)
            yesterday_meals   = sheets.get_meals_for_period(yesterday_start, yesterday_start)
            yesterday_weights = sheets.get_weight_for_period(yesterday_start, yesterday_start)

            if yesterday_meals or yesterday_weights:
                # Consecutive day → extend streak
                new_streak = current_streak + 1
            else:
                # Missed yesterday → reset
                new_streak = 1
    else:
        # Already logged today → no change
        new_streak = current_streak

    new_best = max(best_streak, new_streak)

    sheets.update_streak(str(user_id), new_streak, new_best)
    logger.info("Streak updated for user %s: current=%d, best=%d", user_id, new_streak, new_best)

    return new_streak, new_best


def get_streak_info(user_id: str) -> tuple[int, int]:
    """
    Return (current_streak, best_streak) for display.
    """
    return sheets.get_streak(str(user_id))
