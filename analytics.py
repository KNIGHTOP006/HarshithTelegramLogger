"""
analytics.py
------------
Clean analytics layer for Fitness AI Tracker.

Responsibilities:
- Fetch raw data via sheets.py
- Aggregate calories/macros/weights
- Provide stable summary objects for bot.py
"""

import logging
from datetime import date, datetime, timedelta
from collections import defaultdict

import sheets

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def _num(x, default=0.0):
    try:
        return float(x)
    except (ValueError, TypeError):
        return default


def _parse_date(x: str):
    """
    Supports:
    - 'YYYY-MM-DD HH:MM:SS'
    - 'YYYY-MM-DD'
    """
    if not x:
        return None

    try:
        return datetime.fromisoformat(x)
    except ValueError:
        try:
            return datetime.strptime(x, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return None


def _filter_by_date(rows, start_date, end_date):
    """
    Generic filter for any sheet rows containing Date field.
    """
    out = []

    for r in rows:
        dt = _parse_date(r.get("Date"))
        if not dt:
            continue

        if start_date <= dt.date() <= end_date:
            out.append(r)

    return out


# ─────────────────────────────────────────────
# TODAY
# ─────────────────────────────────────────────

def get_today_summary(user_id: str) -> dict:
    today = date.today()

    meals = sheets.get_meals_for_period(today, today)

    total_calories = sum(_num(m.get("Calories")) for m in meals)
    total_protein  = sum(_num(m.get("Protein")) for m in meals)
    total_carbs    = sum(_num(m.get("Carbs")) for m in meals)
    total_fat      = sum(_num(m.get("Fat")) for m in meals)

    goal = sheets.get_calorie_goal(user_id)
    latest_weight = sheets.get_latest_weight()

    return {
        "total_calories": round(total_calories, 1),
        "total_protein": round(total_protein, 1),
        "total_carbs": round(total_carbs, 1),
        "total_fat": round(total_fat, 1),
        "calorie_goal": goal,
        "remaining_calories": round(goal - total_calories, 1),
        "latest_weight": latest_weight,
        "meals_count": len(meals),
    }


# ─────────────────────────────────────────────
# WEEK
# ─────────────────────────────────────────────

def get_week_summary(user_id: str) -> dict:
    today = date.today()
    start = today - timedelta(days=6)

    meals = sheets.get_meals_for_period(start, today)
    weights = sheets.get_weight_for_period(start, today)

    cals_by_day = defaultdict(float)
    protein_by_day = defaultdict(float)

    for m in meals:
        d = str(m.get("Date", ""))[:10]
        cals_by_day[d] += _num(m.get("Calories"))
        protein_by_day[d] += _num(m.get("Protein"))

    days_logged = len(cals_by_day)

    avg_calories = sum(cals_by_day.values()) / days_logged if days_logged else 0
    avg_protein = sum(protein_by_day.values()) / days_logged if days_logged else 0

    consistency = round((days_logged / 7) * 100, 1)

    weight_change = None
    if len(weights) >= 2:
        first = _num(weights[0].get("Weight"))
        last = _num(weights[-1].get("Weight"))
        weight_change = round(last - first, 2)

    return {
        "avg_calories": round(avg_calories, 1),
        "avg_protein": round(avg_protein, 1),
        "weight_change": weight_change,
        "days_logged": days_logged,
        "consistency_pct": consistency,
        "period": f"{start.isoformat()} → {today.isoformat()}",
    }


# ─────────────────────────────────────────────
# MONTH
# ─────────────────────────────────────────────

def get_month_summary(user_id: str) -> dict:
    today = date.today()
    start = today.replace(day=1)

    meals = sheets.get_meals_for_period(start, today)
    weights = sheets.get_weight_for_period(start, today)

    cals_by_day = defaultdict(float)
    protein_by_day = defaultdict(float)

    for m in meals:
        d = str(m.get("Date", ""))[:10]
        cals_by_day[d] += _num(m.get("Calories"))
        protein_by_day[d] += _num(m.get("Protein"))

    days_logged = len(cals_by_day)
    elapsed_days = (today - start).days + 1

    avg_calories = sum(cals_by_day.values()) / days_logged if days_logged else 0
    avg_protein = sum(protein_by_day.values()) / days_logged if days_logged else 0

    consistency = round((days_logged / elapsed_days) * 100, 1)

    highest = max(cals_by_day.items(), key=lambda x: x[1], default=("—", 0))
    lowest = min(cals_by_day.items(), key=lambda x: x[1], default=("—", 0))

    start_w = _num(weights[0].get("Weight")) if weights else None
    end_w = _num(weights[-1].get("Weight")) if weights else None

    weight_change = round(end_w - start_w, 2) if start_w and end_w else None

    return {
        "avg_calories": round(avg_calories, 1),
        "avg_protein": round(avg_protein, 1),
        "days_logged": days_logged,
        "consistency_pct": consistency,
        "highest_cal_day": highest,
        "lowest_cal_day": lowest,
        "start_weight": start_w,
        "end_weight": end_w,
        "weight_change": weight_change,
        "month": today.strftime("%B %Y"),
    }


# ─────────────────────────────────────────────
# YEAR
# ─────────────────────────────────────────────

def get_year_summary(user_id: str) -> dict:
    today = date.today()
    start = today.replace(month=1, day=1)

    meals = sheets.get_meals_for_period(start, today)
    weights = sheets.get_weight_for_period(start, today)

    daily = defaultdict(float)
    monthly = defaultdict(float)

    for m in meals:
        d = str(m.get("Date", ""))[:10]
        daily[d] += _num(m.get("Calories"))
        monthly[d[:7]] += _num(m.get("Calories"))

    total_days = len(daily)
    avg_calories = sum(daily.values()) / total_days if total_days else 0

    # month with highest avg calories
    best_month = max(monthly, key=monthly.get) if monthly else "—"

    # longest streak
    sorted_days = sorted(daily.keys())
    longest_streak = _longest_streak(sorted_days)

    start_w = _num(weights[0].get("Weight")) if weights else None
    end_w = _num(weights[-1].get("Weight")) if weights else None

    weight_change = round(end_w - start_w, 2) if start_w and end_w else None

    lowest_weight = min((_num(w.get("Weight")) for w in weights), default=None)

    return {
        "avg_calories": round(avg_calories, 1),
        "total_days_logged": total_days,
        "longest_streak": longest_streak,
        "best_month": best_month,
        "start_weight": start_w,
        "end_weight": end_w,
        "lowest_weight": lowest_weight,
        "total_weight_change": weight_change,
        "year": today.year,
    }


# ─────────────────────────────────────────────
# STREAK
# ─────────────────────────────────────────────

def _longest_streak(days: list[str]) -> int:
    if not days:
        return 0

    streak = max_streak = 1

    for i in range(1, len(days)):
        try:
            prev = date.fromisoformat(days[i - 1])
            curr = date.fromisoformat(days[i])

            if (curr - prev).days == 1:
                streak += 1
                max_streak = max(max_streak, streak)
            else:
                streak = 1
        except ValueError:
            continue

    return max_streak