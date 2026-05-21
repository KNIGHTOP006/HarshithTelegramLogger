import os
import logging
import asyncio
from pathlib import Path

from config import WHISPER_MODEL_SIZE, TEMP_DIR

logger = logging.getLogger(__name__)

Path(TEMP_DIR).mkdir(parents=True, exist_ok=True)

_WHISPER_MODEL = None
_WHISPER_AVAILABLE = False

try:
    import whisper
    _WHISPER_AVAILABLE = True
except ImportError:
    logger.warning(
        "openai-whisper not installed. Voice transcription disabled. "
        "Install with: pip install openai-whisper"
    )


def _get_model():
    global _WHISPER_MODEL
    if not _WHISPER_AVAILABLE:
        return None
    if _WHISPER_MODEL is None:
        logger.info("Loading Whisper model: %s", WHISPER_MODEL_SIZE)
        _WHISPER_MODEL = whisper.load_model(WHISPER_MODEL_SIZE)
        logger.info("Whisper model loaded.")
    return _WHISPER_MODEL


async def transcribe_voice(file_path: str) -> str | None:
    if not _WHISPER_AVAILABLE:
        logger.error("Cannot transcribe: whisper not installed")
        return None
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, _transcribe, file_path)
        return result
    except Exception as e:
        logger.error("Transcription failed for %s: %s", file_path, e)
        return None


def _transcribe(file_path: str) -> str:
    model = _get_model()
    if model is None:
        return ""
    result = model.transcribe(file_path, fp16=False)
    text = result.get("text", "").strip()
    logger.info("Transcribed: %s", text)
    return text


async def download_voice_file(bot, file_id: str, user_id: int) -> str | None:
    try:
        Path(TEMP_DIR).mkdir(parents=True, exist_ok=True)
        file_path = os.path.join(TEMP_DIR, f"voice_{user_id}.ogg")
        tg_file = await bot.get_file(file_id)
        await tg_file.download_to_drive(file_path)
        logger.info("Voice file saved to: %s", file_path)
        return file_path
    except Exception as e:
        logger.error("Failed to download voice file %s: %s", file_id, e)
        return None
