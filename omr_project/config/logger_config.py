import logging
import sys

# Central logging configuration
# Call setup_logging() once at application startup (e.g., in main.main())

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%H:%M:%S"

_DEFAULT_LEVEL = logging.INFO

# Exposed loggers names for consistency
APP_LOGGER_NAME = "omr.app"
SCAN_LOGGER_NAME = "omr.scanner"
PDF_LOGGER_NAME = "omr.pdf"
GRADING_LOGGER_NAME = "omr.grading"
UI_LOGGER_NAME = "omr.ui"

_configured = False

def setup_logging(level: int = _DEFAULT_LEVEL):
    global _configured
    if _configured:
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(handler)
    # Reduce noise from external libraries if needed
    logging.getLogger("PIL").setLevel(logging.WARNING)
    logging.getLogger("reportlab").setLevel(logging.WARNING)
    _configured = True


def get_logger(name: str):
    if not _configured:
        setup_logging()
    return logging.getLogger(name)
