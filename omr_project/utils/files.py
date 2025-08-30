from datetime import datetime
from config.app_config import AppConfig


def build_timestamped_filename(stem: str, ext: str, fmt: str = AppConfig.TIMESTAMP_FMT) -> str:
    ts = datetime.now().strftime(fmt)
    return f"{stem}_{ts}.{ext}"

