from config.app_config import AppConfig
from reportlab.lib.pagesizes import letter, A4, landscape


def get_page_size_inches() -> tuple[float, float]:
    size = (AppConfig.DEFAULT_PAGE_SIZE.value if hasattr(AppConfig.DEFAULT_PAGE_SIZE, 'value') else str(AppConfig.DEFAULT_PAGE_SIZE)).lower()
    width, height = AppConfig.PAGE_SIZES_INCHES.get(size, AppConfig.PAGE_SIZES_INCHES['letter'])
    orient = (AppConfig.DEFAULT_PAGE_ORIENTATION.value if hasattr(AppConfig.DEFAULT_PAGE_ORIENTATION, 'value') else str(AppConfig.DEFAULT_PAGE_ORIENTATION)).lower()
    if orient == 'landscape':
        width, height = height, width
    return width, height


def get_reportlab_pagesize():
    """Return ReportLab pagesize object matching config size and orientation."""
    size = (AppConfig.DEFAULT_PAGE_SIZE.value if hasattr(AppConfig.DEFAULT_PAGE_SIZE, 'value') else str(AppConfig.DEFAULT_PAGE_SIZE)).lower()
    base = {'a4': A4, 'letter': letter}.get(size, letter)
    orient = (AppConfig.DEFAULT_PAGE_ORIENTATION.value if hasattr(AppConfig.DEFAULT_PAGE_ORIENTATION, 'value') else str(AppConfig.DEFAULT_PAGE_ORIENTATION)).lower()
    return landscape(base) if orient == 'landscape' else base
