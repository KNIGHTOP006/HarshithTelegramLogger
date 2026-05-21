"""
utils.py
--------
Shared utility functions used across multiple modules.
Formatting, food estimation pipeline, and response helpers.
"""

import logging
from food_db import parse_food_query
from ai import estimate_multiple_foods_gemini

logger = logging.getLogger(__name__)


# ── Nutrition Aggregation ──────────────────────────────────────────────────────

async def estimate_food_nutrition(text: str) -> tuple[dict, str]:
    """
    Two-layer food estimation pipeline.

    Layer 1: Look up foods in local database (instant, free)
    Layer 2: Send unknowns to Gemini API (only if needed)

    Args:
        text: free-form food description e.g. "3 eggs and 2 dosa"

    Returns:
        totals dict: {calories, protein, carbs, fat, description}
        source str:  "local" | "gemini" | "mixed"
    """
    # Layer 1: local lookup
    found_local, unknowns = parse_food_query(text)

    # Layer 2: Gemini fallback for unknowns
    gemini_results = []
    if unknowns:
        logger.info("Sending to Gemini: %s", unknowns)
        gemini_results = await estimate_multiple_foods_gemini(unknowns)

    # Combine results
    all_items = found_local + [
        {
            "food": r["food"],
            "qty": 1,
            "calories": r["calories"],
            "protein":  r["protein"],
            "carbs":    r["carbs"],
            "fat":      r["fat"],
        }
        for r in gemini_results
    ]

    if not all_items:
        # Fallback: nothing recognised at all
        return {
            "calories": 0,
            "protein":  0,
            "carbs":    0,
            "fat":      0,
            "description": text,
        }, "unknown"

    # Sum up totals
    totals = {
        "calories":    round(sum(i["calories"] for i in all_items), 1),
        "protein":     round(sum(i["protein"]  for i in all_items), 1),
        "carbs":       round(sum(i["carbs"]    for i in all_items), 1),
        "fat":         round(sum(i["fat"]      for i in all_items), 1),
        "description": text,
    }

    # Determine source label
    if unknowns and found_local:
        source = "mixed"
    elif unknowns:
        source = "gemini"
    else:
        source = "local"

    return totals, source


# ── Message Formatters ─────────────────────────────────────────────────────────

def format_meal_response(food_text: str, nutrition: dict, source: str) -> str:
    """
    Format the response message after a successful meal log.
    """
    source_label = {"local": "📚 Local DB", "gemini": "🤖 AI Estimate", "mixed": "📚+🤖 Mixed"}.get(source, "")

    return (
        f"✅ *Logged Successfully!* {source_label}\n\n"
        f"🍽 *Meal:* {food_text}\n\n"
        f"🔥 *Calories:* {nutrition['calories']} kcal\n"
        f"💪 *Protein:*  {nutrition['protein']}g\n"
        f"🌾 *Carbs:*    {nutrition['carbs']}g\n"
        f"🧴 *Fat:*      {nutrition['fat']}g"
    )


def format_today_summary(data: dict) -> str:
    """Format the /today command response."""
    remaining = data["remaining_calories"]
    remaining_str = (
        f"🟢 {remaining:.0f} kcal remaining"
        if remaining >= 0
        else f"🔴 {abs(remaining):.0f} kcal over goal"
    )
    weight_str = f"{data['latest_weight']} kg" if data["latest_weight"] else "Not logged today"

    return (
        f"📊 *Today's Summary*\n\n"
        f"🔥 Calories:  {data['total_calories']} / {data['calorie_goal']} kcal\n"
        f"💪 Protein:   {data['total_protein']}g\n"
        f"🌾 Carbs:     {data['total_carbs']}g\n"
        f"🧴 Fat:       {data['total_fat']}g\n"
        f"⚖️  Weight:    {weight_str}\n"
        f"🍽 Meals:     {data['meals_count']}\n\n"
        f"{remaining_str}"
    )


def format_week_summary(data: dict) -> str:
    """Format the /week command response."""
    wc = f"{data['weight_change']:+.2f} kg" if data["weight_change"] is not None else "No weight data"
    return (
        f"📅 *Weekly Summary*\n_{data['period']}_\n\n"
        f"🔥 Avg Calories: {data['avg_calories']} kcal/day\n"
        f"💪 Avg Protein:  {data['avg_protein']}g/day\n"
        f"⚖️  Weight Change: {wc}\n"
        f"📆 Days Logged:  {data['days_logged']} / 7\n"
        f"🎯 Consistency:  {data['consistency_pct']}%"
    )


def format_month_summary(data: dict) -> str:
    """Format the /month command response."""
    sw = f"{data['start_weight']} kg" if data["start_weight"] else "—"
    ew = f"{data['end_weight']} kg"   if data["end_weight"]   else "—"
    wc = f"{data['weight_change']:+.2f} kg" if data["weight_change"] is not None else "—"
    hcd_date, hcd_cal = data["highest_cal_day"]
    lcd_date, lcd_cal = data["lowest_cal_day"]

    return (
        f"🗓 *Monthly Summary – {data['month']}*\n\n"
        f"🔥 Avg Calories:     {data['avg_calories']} kcal/day\n"
        f"💪 Avg Protein:      {data['avg_protein']}g/day\n"
        f"⚖️  Starting Weight:  {sw}\n"
        f"⚖️  Current Weight:   {ew}\n"
        f"📉 Weight Change:    {wc}\n"
        f"📆 Days Logged:      {data['days_logged']}\n"
        f"🎯 Consistency:      {data['consistency_pct']}%\n"
        f"📈 Highest Cal Day:  {hcd_date} ({hcd_cal:.0f} kcal)\n"
        f"📉 Lowest Cal Day:   {lcd_date} ({lcd_cal:.0f} kcal)"
    )


def format_year_summary(data: dict) -> str:
    """Format the /year command response."""
    lw  = f"{data['lowest_weight']} kg"          if data["lowest_weight"]      else "—"
    twc = f"{data['total_weight_change']:+.2f} kg" if data["total_weight_change"] is not None else "—"

    return (
        f"🏆 *Yearly Summary – {data['year']}*\n\n"
        f"🔥 Avg Calories:      {data['avg_calories']} kcal/day\n"
        f"📆 Total Days Logged: {data['total_days_logged']}\n"
        f"🔥 Longest Streak:    {data['longest_streak']} days\n"
        f"🏅 Best Month:        {data['best_month']}\n"
        f"⚖️  Lowest Weight:     {lw}\n"
        f"📉 Total Weight Δ:    {twc}"
    )


def format_streak_message(current: int, best: int) -> str:
    """Format the /streak command response."""
    emoji = "🔥" * min(current, 7)  # show max 7 fire emojis
    return (
        f"🔥 *Streak Tracker*\n\n"
        f"{emoji}\n\n"
        f"📅 Current Streak: *{current} day{'s' if current != 1 else ''}*\n"
        f"🏆 Best Streak:    *{best} day{'s' if best != 1 else ''}*"
    )
