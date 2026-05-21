import json
import logging

from config import GEMINI_API_KEY

logger = logging.getLogger(__name__)

_GENAI_AVAILABLE = False
_CLIENT = None

try:
    from google import genai
    _GENAI_AVAILABLE = True
except ImportError:
    logger.warning(
        "google-genai not installed. Gemini AI features disabled. "
        "Install with: pip install google-genai"
    )


if _GENAI_AVAILABLE:
    _CLIENT = genai.Client(api_key=GEMINI_API_KEY)
    _MODEL = "gemini-2.0-flash"


SINGLE_FOOD_PROMPT = """
You are a nutrition expert. The user described this food: "{food_text}"

Return ONLY a JSON object with this exact schema (no markdown, no explanation):
{{
  "food": "<cleaned food name>",
  "calories": <integer>,
  "protein": <float in grams>,
  "carbs": <float in grams>,
  "fat": <float in grams>
}}

Rules:
- Estimate for a typical single serving unless a quantity is mentioned.
- If quantity is mentioned (e.g. "3 eggs"), multiply accordingly.
- Use realistic Indian/global nutrition values.
- Return ONLY the JSON object, nothing else.
"""


async def estimate_calories_gemini(food_text: str) -> dict | None:
    if not _GENAI_AVAILABLE:
        logger.error("Gemini AI not available: google-genai not installed")
        return None
    try:
        prompt = SINGLE_FOOD_PROMPT.format(food_text=food_text)
        response = _CLIENT.models.generate_content(model=_MODEL, contents=prompt)

        raw = response.text.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()

        data = json.loads(raw)

        required_keys = {"food", "calories", "protein", "carbs", "fat"}
        if not required_keys.issubset(data.keys()):
            logger.warning("Gemini response missing keys: %s", data)
            return None

        return {
            "food":     str(data["food"]),
            "calories": int(data["calories"]),
            "protein":  float(data["protein"]),
            "carbs":    float(data["carbs"]),
            "fat":      float(data["fat"]),
        }

    except json.JSONDecodeError as e:
        logger.error("Failed to parse Gemini JSON: %s | Raw: %s", e, response.text if 'response' in dir() else "N/A")
        return None
    except Exception as e:
        logger.error("Gemini API error: %s", e)
        return None


MULTI_FOOD_PROMPT = """
You are a nutrition expert. The user logged these foods: {food_list}

Return ONLY a JSON array where each element has this exact schema:
[
  {{
    "food": "<cleaned food name>",
    "calories": <integer>,
    "protein": <float in grams>,
    "carbs": <float in grams>,
    "fat": <float in grams>
  }}
]

Rules:
- One element per food item listed.
- Estimate for the quantity mentioned or a single serving if no quantity given.
- Use realistic nutrition values.
- Return ONLY the JSON array, nothing else.
"""


async def estimate_multiple_foods_gemini(food_texts: list[str]) -> list[dict]:
    if not _GENAI_AVAILABLE:
        logger.error("Gemini AI not available: google-genai not installed")
        return []

    if not food_texts:
        return []

    try:
        food_list = ", ".join(f'"{f}"' for f in food_texts)
        prompt = MULTI_FOOD_PROMPT.format(food_list=food_list)
        response = _CLIENT.models.generate_content(model=_MODEL, contents=prompt)

        raw = response.text.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()

        data = json.loads(raw)

        if not isinstance(data, list):
            logger.warning("Expected JSON array from Gemini, got: %s", type(data))
            return []

        results = []
        for item in data:
            try:
                results.append({
                    "food":     str(item["food"]),
                    "calories": int(item["calories"]),
                    "protein":  float(item["protein"]),
                    "carbs":    float(item["carbs"]),
                    "fat":      float(item["fat"]),
                })
            except (KeyError, ValueError) as e:
                logger.warning("Skipping malformed Gemini item %s: %s", item, e)

        return results

    except json.JSONDecodeError as e:
        logger.error("Failed to parse Gemini multi-food JSON: %s", e)
        return []
    except Exception as e:
        logger.error("Gemini batch API error: %s", e)
        return []
