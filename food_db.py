"""
food_db.py
----------
Local food database for common Indian & international foods.
Layer 1 of the two-layer calorie estimation system.

When a user logs food, we first check here. If all foods are found
locally we skip the Gemini API call entirely → zero cost for common foods.

Structure of each entry:
  "food name": {
      "calories": int,   # per standard serving
      "protein":  float, # grams
      "carbs":    float, # grams
      "fat":      float, # grams
      "serving":  str    # description of one serving
  }
"""

# ── Indian Staples ─────────────────────────────────────────────────────────────
FOOD_DATABASE = {
    # ── Breakfast / Tiffin ───────────────────────────────────────────────────
    "idli":          {"calories": 60,  "protein": 2.0, "carbs": 12.0, "fat": 0.4, "serving": "1 piece"},
    "dosa":          {"calories": 120, "protein": 3.0, "carbs": 20.0, "fat": 3.5, "serving": "1 medium dosa"},
    "masala dosa":   {"calories": 220, "protein": 5.0, "carbs": 35.0, "fat": 7.0, "serving": "1 dosa with filling"},
    "poha":          {"calories": 250, "protein": 4.0, "carbs": 45.0, "fat": 5.0, "serving": "1 plate (~150g)"},
    "upma":          {"calories": 230, "protein": 5.0, "carbs": 38.0, "fat": 7.0, "serving": "1 plate (~150g)"},
    "paratha":       {"calories": 260, "protein": 5.0, "carbs": 35.0, "fat": 11.0, "serving": "1 piece"},
    "chapati":       {"calories": 120, "protein": 3.5, "carbs": 20.0, "fat": 3.0, "serving": "1 piece"},
    "roti":          {"calories": 120, "protein": 3.5, "carbs": 20.0, "fat": 3.0, "serving": "1 piece"},
    "puri":          {"calories": 150, "protein": 2.5, "carbs": 18.0, "fat": 7.5, "serving": "1 piece"},
    "samosa":        {"calories": 260, "protein": 4.5, "carbs": 28.0, "fat": 14.0,"serving": "1 piece"},
    "vada":          {"calories": 130, "protein": 4.0, "carbs": 15.0, "fat": 6.0, "serving": "1 piece"},
    "medu vada":     {"calories": 130, "protein": 4.0, "carbs": 15.0, "fat": 6.0, "serving": "1 piece"},
    "uttapam":       {"calories": 180, "protein": 5.0, "carbs": 28.0, "fat": 5.0, "serving": "1 medium"},
    "pesarattu":     {"calories": 140, "protein": 7.0, "carbs": 22.0, "fat": 3.0, "serving": "1 dosa"},

    # ── Rice Dishes ──────────────────────────────────────────────────────────
    "rice":          {"calories": 130, "protein": 2.7, "carbs": 28.0, "fat": 0.3, "serving": "1 cup cooked (~150g)"},
    "white rice":    {"calories": 130, "protein": 2.7, "carbs": 28.0, "fat": 0.3, "serving": "1 cup cooked"},
    "brown rice":    {"calories": 110, "protein": 2.5, "carbs": 23.0, "fat": 0.9, "serving": "1 cup cooked"},
    "biryani":       {"calories": 350, "protein": 18.0,"carbs": 45.0, "fat": 10.0,"serving": "1 plate (~250g)"},
    "chicken biryani":{"calories":400,"protein": 25.0,"carbs": 45.0, "fat": 12.0,"serving": "1 plate (~250g)"},
    "fried rice":    {"calories": 250, "protein": 6.0, "carbs": 40.0, "fat": 8.0, "serving": "1 plate"},
    "pulao":         {"calories": 210, "protein": 5.0, "carbs": 38.0, "fat": 5.0, "serving": "1 plate"},
    "khichdi":       {"calories": 200, "protein": 7.0, "carbs": 35.0, "fat": 4.0, "serving": "1 bowl"},

    # ── Dal / Curries ─────────────────────────────────────────────────────────
    "dal":           {"calories": 150, "protein": 9.0, "carbs": 20.0, "fat": 3.0, "serving": "1 bowl (~200ml)"},
    "dal fry":       {"calories": 180, "protein": 9.5, "carbs": 22.0, "fat": 6.0, "serving": "1 bowl"},
    "rajma":         {"calories": 210, "protein": 12.0,"carbs": 32.0, "fat": 3.0, "serving": "1 bowl"},
    "chole":         {"calories": 270, "protein": 14.0,"carbs": 40.0, "fat": 6.0, "serving": "1 bowl"},
    "paneer":        {"calories": 265, "protein": 18.0,"carbs": 4.0,  "fat": 20.0,"serving": "100g"},
    "paneer butter masala":{"calories":350,"protein":14.0,"carbs":20.0,"fat":24.0,"serving":"1 bowl"},
    "palak paneer":  {"calories": 280, "protein": 14.0,"carbs": 12.0, "fat": 20.0,"serving": "1 bowl"},
    "chicken curry": {"calories": 250, "protein": 22.0,"carbs": 8.0,  "fat": 14.0,"serving": "1 bowl"},
    "fish curry":    {"calories": 200, "protein": 20.0,"carbs": 6.0,  "fat": 10.0,"serving": "1 bowl"},
    "mutton curry":  {"calories": 310, "protein": 26.0,"carbs": 6.0,  "fat": 20.0,"serving": "1 bowl"},
    "sambar":        {"calories": 90,  "protein": 4.0, "carbs": 14.0, "fat": 2.0, "serving": "1 bowl"},

    # ── Proteins ─────────────────────────────────────────────────────────────
    "egg":           {"calories": 70,  "protein": 6.0, "carbs": 0.6,  "fat": 5.0, "serving": "1 large egg"},
    "boiled egg":    {"calories": 70,  "protein": 6.0, "carbs": 0.6,  "fat": 5.0, "serving": "1 egg"},
    "scrambled egg": {"calories": 90,  "protein": 6.5, "carbs": 1.5,  "fat": 7.0, "serving": "1 egg with milk"},
    "omelette":      {"calories": 150, "protein": 12.0,"carbs": 2.0,  "fat": 11.0,"serving": "2-egg omelette"},
    "chicken breast":{"calories": 165, "protein": 31.0,"carbs": 0.0,  "fat": 3.6, "serving": "100g"},
    "grilled chicken":{"calories":165, "protein": 31.0,"carbs": 0.0,  "fat": 3.6, "serving": "100g"},
    "chicken":       {"calories": 200, "protein": 27.0,"carbs": 0.0,  "fat": 10.0,"serving": "100g"},
    "fish":          {"calories": 130, "protein": 22.0,"carbs": 0.0,  "fat": 4.5, "serving": "100g"},
    "salmon":        {"calories": 208, "protein": 20.0,"carbs": 0.0,  "fat": 13.0,"serving": "100g"},
    "tuna":          {"calories": 132, "protein": 28.0,"carbs": 0.0,  "fat": 1.0, "serving": "100g"},
    "tofu":          {"calories": 76,  "protein": 8.0, "carbs": 1.9,  "fat": 4.5, "serving": "100g"},
    "curd":          {"calories": 60,  "protein": 3.5, "carbs": 4.5,  "fat": 3.0, "serving": "100g"},
    "yogurt":        {"calories": 60,  "protein": 3.5, "carbs": 4.5,  "fat": 3.0, "serving": "100g"},
    "greek yogurt":  {"calories": 90,  "protein": 10.0,"carbs": 5.0,  "fat": 2.0, "serving": "100g"},
    "whey protein":  {"calories": 120, "protein": 25.0,"carbs": 3.0,  "fat": 1.5, "serving": "1 scoop (~30g)"},
    "protein shake": {"calories": 120, "protein": 25.0,"carbs": 3.0,  "fat": 1.5, "serving": "1 scoop"},

    # ── Dairy / Beverages ─────────────────────────────────────────────────────
    "milk":          {"calories": 65,  "protein": 3.3, "carbs": 5.0,  "fat": 3.5, "serving": "100ml"},
    "whole milk":    {"calories": 65,  "protein": 3.3, "carbs": 5.0,  "fat": 3.5, "serving": "100ml"},
    "skim milk":     {"calories": 35,  "protein": 3.5, "carbs": 5.0,  "fat": 0.2, "serving": "100ml"},
    "chai":          {"calories": 50,  "protein": 1.5, "carbs": 5.0,  "fat": 2.5, "serving": "1 cup (~150ml)"},
    "tea":           {"calories": 30,  "protein": 1.0, "carbs": 3.0,  "fat": 1.5, "serving": "1 cup"},
    "coffee":        {"calories": 5,   "protein": 0.3, "carbs": 0.5,  "fat": 0.1, "serving": "1 cup black"},
    "black coffee":  {"calories": 5,   "protein": 0.3, "carbs": 0.5,  "fat": 0.1, "serving": "1 cup"},
    "lassi":         {"calories": 180, "protein": 6.0, "carbs": 25.0, "fat": 6.0, "serving": "1 glass (250ml)"},
    "buttermilk":    {"calories": 40,  "protein": 2.0, "carbs": 4.5,  "fat": 1.0, "serving": "1 glass"},

    # ── Bread / Grains ────────────────────────────────────────────────────────
    "bread":         {"calories": 80,  "protein": 2.5, "carbs": 15.0, "fat": 1.0, "serving": "1 slice"},
    "white bread":   {"calories": 80,  "protein": 2.5, "carbs": 15.0, "fat": 1.0, "serving": "1 slice"},
    "brown bread":   {"calories": 70,  "protein": 3.0, "carbs": 13.0, "fat": 1.0, "serving": "1 slice"},
    "oats":          {"calories": 150, "protein": 5.0, "carbs": 27.0, "fat": 3.0, "serving": "40g dry"},
    "oatmeal":       {"calories": 150, "protein": 5.0, "carbs": 27.0, "fat": 3.0, "serving": "1 bowl cooked"},
    "cornflakes":    {"calories": 110, "protein": 2.5, "carbs": 25.0, "fat": 0.5, "serving": "30g"},
    "muesli":        {"calories": 180, "protein": 5.0, "carbs": 33.0, "fat": 4.0, "serving": "50g"},
    "pasta":         {"calories": 220, "protein": 8.0, "carbs": 43.0, "fat": 1.5, "serving": "1 cup cooked"},
    "noodles":       {"calories": 220, "protein": 5.0, "carbs": 40.0, "fat": 4.0, "serving": "1 bowl cooked"},
    "maggi":         {"calories": 380, "protein": 8.0, "carbs": 55.0, "fat": 14.0,"serving": "1 pack (80g)"},

    # ── Fruits ───────────────────────────────────────────────────────────────
    "apple":         {"calories": 80,  "protein": 0.4, "carbs": 21.0, "fat": 0.2, "serving": "1 medium"},
    "banana":        {"calories": 90,  "protein": 1.1, "carbs": 23.0, "fat": 0.3, "serving": "1 medium"},
    "mango":         {"calories": 100, "protein": 0.8, "carbs": 25.0, "fat": 0.4, "serving": "1 cup diced"},
    "orange":        {"calories": 60,  "protein": 1.2, "carbs": 15.0, "fat": 0.2, "serving": "1 medium"},
    "grapes":        {"calories": 70,  "protein": 0.6, "carbs": 18.0, "fat": 0.2, "serving": "1 cup"},
    "watermelon":    {"calories": 45,  "protein": 0.9, "carbs": 11.0, "fat": 0.2, "serving": "1 cup"},
    "papaya":        {"calories": 55,  "protein": 0.6, "carbs": 14.0, "fat": 0.1, "serving": "1 cup"},
    "guava":         {"calories": 68,  "protein": 2.6, "carbs": 14.0, "fat": 1.0, "serving": "1 medium"},

    # ── Vegetables ───────────────────────────────────────────────────────────
    "potato":        {"calories": 80,  "protein": 2.0, "carbs": 17.0, "fat": 0.1, "serving": "1 medium"},
    "sweet potato":  {"calories": 90,  "protein": 2.0, "carbs": 21.0, "fat": 0.1, "serving": "1 medium"},
    "carrot":        {"calories": 40,  "protein": 0.9, "carbs": 9.5,  "fat": 0.2, "serving": "1 medium"},
    "broccoli":      {"calories": 35,  "protein": 2.4, "carbs": 7.0,  "fat": 0.4, "serving": "1 cup"},
    "spinach":       {"calories": 23,  "protein": 2.9, "carbs": 3.6,  "fat": 0.4, "serving": "1 cup"},
    "tomato":        {"calories": 20,  "protein": 0.9, "carbs": 4.2,  "fat": 0.2, "serving": "1 medium"},
    "cucumber":      {"calories": 15,  "protein": 0.6, "carbs": 3.0,  "fat": 0.1, "serving": "1 medium"},
    "onion":         {"calories": 40,  "protein": 0.9, "carbs": 9.0,  "fat": 0.1, "serving": "1 medium"},

    # ── Snacks / Fast Food ────────────────────────────────────────────────────
    "sandwich":      {"calories": 300, "protein": 12.0,"carbs": 38.0, "fat": 10.0,"serving": "1 sandwich"},
    "burger":        {"calories": 500, "protein": 25.0,"carbs": 42.0, "fat": 25.0,"serving": "1 regular"},
    "pizza":         {"calories": 285, "protein": 12.0,"carbs": 36.0, "fat": 10.0,"serving": "1 slice"},
    "french fries":  {"calories": 365, "protein": 4.0, "carbs": 48.0, "fat": 17.0,"serving": "medium (100g)"},
    "chips":         {"calories": 530, "protein": 7.0, "carbs": 52.0, "fat": 34.0,"serving": "100g"},
    "chocolate":     {"calories": 215, "protein": 3.0, "carbs": 26.0, "fat": 12.0,"serving": "40g bar"},
    "biscuit":       {"calories": 70,  "protein": 1.0, "carbs": 11.0, "fat": 2.5, "serving": "2 pieces"},
    "peanut butter": {"calories": 190, "protein": 8.0, "carbs": 6.0,  "fat": 16.0,"serving": "2 tbsp (32g)"},
    "almonds":       {"calories": 164, "protein": 6.0, "carbs": 6.0,  "fat": 14.0,"serving": "28g (~23 nuts)"},
    "peanuts":       {"calories": 160, "protein": 7.0, "carbs": 6.0,  "fat": 14.0,"serving": "28g"},
    "ghee":          {"calories": 112, "protein": 0.0, "carbs": 0.0,  "fat": 12.5,"serving": "1 tsp (14g)"},
    "oil":           {"calories": 120, "protein": 0.0, "carbs": 0.0,  "fat": 14.0,"serving": "1 tbsp"},
    "butter":        {"calories": 102, "protein": 0.1, "carbs": 0.0,  "fat": 11.5,"serving": "1 tbsp (14g)"},

    # ── South Indian Specials ─────────────────────────────────────────────────
    "pongal":        {"calories": 300, "protein": 8.0, "carbs": 50.0, "fat": 8.0, "serving": "1 plate"},
    "chettinad":     {"calories": 320, "protein": 22.0,"carbs": 12.0, "fat": 20.0,"serving": "1 serving"},
    "appam":         {"calories": 100, "protein": 2.0, "carbs": 20.0, "fat": 1.5, "serving": "1 piece"},
    "puttu":         {"calories": 200, "protein": 4.0, "carbs": 40.0, "fat": 2.0, "serving": "1 serving"},
    "rasam":         {"calories": 40,  "protein": 1.5, "carbs": 6.0,  "fat": 1.5, "serving": "1 bowl"},
    "kootu":         {"calories": 150, "protein": 5.0, "carbs": 20.0, "fat": 6.0, "serving": "1 bowl"},
}


# ── Quantity keyword mapping ───────────────────────────────────────────────────
# Maps English quantity words to numeric multipliers
QUANTITY_MAP = {
    "half": 0.5, "quarter": 0.25, "double": 2.0, "triple": 3.0,
    "a": 1.0, "an": 1.0, "one": 1.0, "two": 2.0, "three": 3.0,
    "four": 4.0, "five": 5.0, "six": 6.0, "seven": 7.0, "eight": 8.0,
    "nine": 9.0, "ten": 10.0,
}


def lookup_food(food_name: str) -> dict | None:
    """
    Case-insensitive lookup in the local database.
    Returns the nutrition dict or None if not found.
    """
    key = food_name.strip().lower()
    return FOOD_DATABASE.get(key)


def parse_food_query(text: str) -> tuple[list[dict], list[str]]:
    """
    Parse a free-text food query like "3 eggs and 2 dosa and salmon".

    Returns:
        found   – list of dicts with keys: food, qty, calories, protein, carbs, fat
        unknown – list of food strings not found locally (needs Gemini fallback)

    Strategy:
        1. Split on 'and', ',' or '+'
        2. For each token, try to extract a leading number or word-number
        3. Lookup remaining words in FOOD_DATABASE
    """
    import re

    # Split on common separators
    tokens = re.split(r"\band\b|,|\+|&", text, flags=re.IGNORECASE)

    found = []
    unknown = []

    for token in tokens:
        token = token.strip()
        if not token:
            continue

        # Try to extract a quantity at the start: "3 eggs", "two dosa", "half sandwich"
        qty = 1.0
        match = re.match(r"^(\d+\.?\d*)\s+(.+)", token)  # numeric quantity
        if match:
            qty = float(match.group(1))
            food_part = match.group(2).strip()
        else:
            # Check for word quantities
            words = token.split()
            if words and words[0].lower() in QUANTITY_MAP:
                qty = QUANTITY_MAP[words[0].lower()]
                food_part = " ".join(words[1:]).strip()
            else:
                food_part = token

        # Try exact match, then each individual word
        nutrition = lookup_food(food_part)
        if nutrition is None:
            # Try matching the last meaningful word (e.g. "boiled egg" → "boiled egg" then "egg")
            words = food_part.split()
            for i in range(len(words)):
                candidate = " ".join(words[i:])
                nutrition = lookup_food(candidate)
                if nutrition:
                    break

        if nutrition:
            found.append({
                "food": food_part,
                "qty": qty,
                "calories": round(nutrition["calories"] * qty, 1),
                "protein":  round(nutrition["protein"]  * qty, 1),
                "carbs":    round(nutrition["carbs"]    * qty, 1),
                "fat":      round(nutrition["fat"]      * qty, 1),
            })
        else:
            # Pass original token to Gemini (include quantity info)
            unknown.append(token)

    return found, unknown
