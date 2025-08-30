from config.app_config import AppConfig
from pathlib import Path
import platform
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


def get_font():
    """Locate and register a suitable Unicode font for PDF generation.

    Searches configured font paths by platform and registers the first
    available TrueType font with ReportLab. Falls back to Helvetica.
    """
    font_paths = AppConfig.FONT_PATHS.get(platform.system(), [])
    for path in font_paths:
        if Path(path).exists():
            try:
                pdfmetrics.registerFont(TTFont('UnicodeFont', path))
                return 'UnicodeFont'
            except Exception:
                continue
    return 'Helvetica'

FONT = get_font()
