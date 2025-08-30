import os
import sys

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QSettings

from config.logger_config import setup_logging, get_logger, APP_LOGGER_NAME
from utils.config_check import validate_config
from i18n import translator
from ui.main_window import OMRUnifiedApp


def main():
    # Enable high DPI scaling on all platforms (PyQt6 syntax)
    os.environ['QT_ENABLE_HIGHDPI_SCALING'] = '1'
    os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'

    # Initialize logging early
    setup_logging()
    validate_config()
    log = get_logger(APP_LOGGER_NAME)
    log.info("Starting OMR Unified Application")

    app = QApplication(sys.argv)
    app.setApplicationName(translator.t('app_title'))
    app.setOrganizationName('OMR')
    app.setStyle('Fusion')

    # Restore preferences
    settings = QSettings()
    lang = settings.value('language')
    if lang:
        translator.set_language(str(lang))
    # Restore page size/orientation if present
    from config.app_config import AppConfig as _Cfg
    if (ps := settings.value('page_size')):
        try:
            _Cfg.DEFAULT_PAGE_SIZE = _Cfg.PageSize(str(ps).lower())
        except Exception:
            pass
    if (po := settings.value('page_orientation')):
        try:
            _Cfg.DEFAULT_PAGE_ORIENTATION = _Cfg.Orientation(str(po).lower())
        except Exception:
            pass
    validate_config()

    unified_app = OMRUnifiedApp()
    # Restore theme preference
    dm = settings.value('dark_mode')
    if dm is not None:
        val = str(dm).lower() in ('1', 'true', 'yes')
        unified_app.dark_mode = val
        from ui.app_style import get_styles as _styles
        unified_app.setStyleSheet(_styles(unified_app.dark_mode))
    unified_app.show()
    log.info("Application UI displayed")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
