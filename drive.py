import os
import logging
from pathlib import Path
from datetime import datetime

from config import PHOTOS_DIR

logger = logging.getLogger(__name__)


async def save_telegram_photo(bot, file_id: str, user_id: int) -> str | None:
    """
    Download a Telegram photo to the local photos directory.
    Returns the local file path, or None on failure.
    """
    try:
        photos_path = Path(PHOTOS_DIR)
        photos_path.mkdir(parents=True, exist_ok=True)

        now = datetime.now()
        filename = f"progress_{user_id}_{now.strftime('%Y%m%d_%H%M%S')}.jpg"
        local_path = str(photos_path / filename)

        tg_file = await bot.get_file(file_id)
        await tg_file.download_to_drive(local_path)

        logger.info("Photo saved locally: %s", local_path)
        return local_path

    except Exception as e:
        logger.error("Failed to save Telegram photo: %s", e)
        return None
