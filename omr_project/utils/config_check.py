from config.app_config import AppConfig
from config.logger_config import get_logger, APP_LOGGER_NAME


def validate_config() -> None:
    """Validate and normalize AppConfig settings at startup.

    - Ensures DEFAULT_PAGE_SIZE and DEFAULT_PAGE_ORIENTATION are supported.
    - Falls back to safe defaults and logs a warning if invalid.
    """
    log = get_logger(APP_LOGGER_NAME)

    size = (AppConfig.DEFAULT_PAGE_SIZE.value if hasattr(AppConfig.DEFAULT_PAGE_SIZE, 'value') else str(AppConfig.DEFAULT_PAGE_SIZE)).lower()
    if size not in AppConfig.SUPPORTED_PAGE_SIZES:
        log.warning(
            "Invalid DEFAULT_PAGE_SIZE '%s'. Falling back to 'letter'. Supported: %s",
            AppConfig.DEFAULT_PAGE_SIZE,
            ", ".join(AppConfig.SUPPORTED_PAGE_SIZES),
        )
        AppConfig.DEFAULT_PAGE_SIZE = AppConfig.PageSize.LETTER  # type: ignore[attr-defined]

    orient = (AppConfig.DEFAULT_PAGE_ORIENTATION.value if hasattr(AppConfig.DEFAULT_PAGE_ORIENTATION, 'value') else str(AppConfig.DEFAULT_PAGE_ORIENTATION)).lower()
    if orient not in AppConfig.SUPPORTED_PAGE_ORIENTATIONS:
        log.warning(
            "Invalid DEFAULT_PAGE_ORIENTATION '%s'. Falling back to 'portrait'. Supported: %s",
            AppConfig.DEFAULT_PAGE_ORIENTATION,
            ", ".join(AppConfig.SUPPORTED_PAGE_ORIENTATIONS),
        )
        AppConfig.DEFAULT_PAGE_ORIENTATION = AppConfig.Orientation.PORTRAIT  # type: ignore[attr-defined]

