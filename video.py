import os
import logging

from moviepy import ImageSequenceClip

from config import TEMP_DIR

logger = logging.getLogger(__name__)


def load_images(local_paths: list[str]) -> list[str]:
    """Return only the paths that still exist on disk."""
    return [p for p in local_paths if os.path.isfile(p)]


def images_to_video(image_paths: list[str], output_name: str, fps: int = 1) -> str:
    if not image_paths:
        return ""

    clip = ImageSequenceClip(image_paths, fps=fps)
    output_path = os.path.join(TEMP_DIR, output_name)
    clip.write_videofile(output_path, codec="libx264", logger=None)
    return output_path
