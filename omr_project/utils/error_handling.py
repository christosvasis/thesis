from PyQt6.QtWidgets import QMessageBox
from typing import Optional

class ErrorHandler:
    """Centralized error and information dialog handling."""

    @staticmethod
    def show_error(parent, title: str, message: str, details: Optional[str] = None):
        msg_box = QMessageBox(parent)
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        if details:
            msg_box.setDetailedText(details)
        return msg_box.exec()

    @staticmethod
    def show_warning(parent, title: str, message: str):
        return QMessageBox.warning(parent, title, message)

    @staticmethod
    def show_info(parent, title: str, message: str):
        return QMessageBox.information(parent, title, message)

    @staticmethod
    def handle_file_error(parent, operation: str, file_path: str, error: Exception, filename_getter):
        filename = filename_getter(file_path)
        title = f"File {operation.title()} Error"
        message = f"Failed to {operation} file: {filename}"
        details = f"Error details: {str(error)}\nFile path: {file_path}"
        ErrorHandler.show_error(parent, title, message, details)

    @staticmethod
    def safe_execute(func, error_callback=None, *args, **kwargs):
        try:
            return func(*args, **kwargs), None
        except Exception as e:  # noqa: BLE001
            if error_callback:
                error_callback(e)
            return None, e

    @staticmethod
    def confirm(parent, title: str, message: str) -> bool:
        """Show a Yes/No confirmation dialog and return True for Yes."""
        reply = QMessageBox.question(
            parent,
            title,
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return reply == QMessageBox.StandardButton.Yes
