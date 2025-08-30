from config.app_config import AppConfig
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QTableWidget
from i18n import translator


class TableManager:
    """
    Making tables look nice and behave properly.

    Tables are everywhere in this app, and they all need to look consistent.
    Rather than copy-pasting the same setup code everywhere, it lives here.
    """

    @staticmethod
    def configure_students_table(table: QTableWidget):
        """
        Set up a table for showing student results.

        This creates a nice-looking table with proper column widths,
        sorting, and all the visual polish that makes users happy.

        Args:
            table (QTableWidget): The table widget to configure
        """
        # Basic setup - 6 columns should be enough for anyone
        table.setColumnCount(6)  # Name, ID, Score, Total, Percentage, Grade
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)  # Select whole rows (less confusing)
        table.setAlternatingRowColors(True)  # Zebra stripes make it easier to read
        table.setSortingEnabled(True)  # Let people sort by clicking headers

        # Header configuration
        header = table.horizontalHeader()
        header.setStretchLastSection(True)  # Last column fills leftover space

        # Set column widths that actually make sense for the content
        header.resizeSection(0, AppConfig.COLUMN_WIDTHS['student_name'])
        header.resizeSection(1, AppConfig.COLUMN_WIDTHS['student_id'])
        header.resizeSection(2, AppConfig.COLUMN_WIDTHS['score'])
        header.resizeSection(3, AppConfig.COLUMN_WIDTHS['total'])
        header.resizeSection(4, AppConfig.COLUMN_WIDTHS['percentage'])

        # Make the header look important (bold text, decent height)
        header_font = QFont()
        header_font.setPointSize(11)
        header_font.setBold(True)
        header.setFont(header_font)
        header.setDefaultSectionSize(80)
        header.setMinimumSectionSize(60)
        header.setFixedHeight(AppConfig.TABLE_HEADER_HEIGHT)

    @staticmethod
    def get_translated_headers():
        """
        Get column headers in whatever language the user picked.

        Grabs the translated text for column headers and cleans them up
        (removes trailing colons and stuff). Has fallbacks in case
        translations are missing.

        Returns:
            list: Column header strings in the right language
        """
        headers = [
            translator.t('student_name_field').replace(':', ''),  # Clean up the colons
            translator.t('student_id_field').replace(':', ''),
            translator.t('score_label').replace(':', ''),
            translator.t('total_label').replace(':', ''),
            translator.t('percentage_label').replace(':', ''),
            translator.t('grade_label').replace(':', '')
        ]

        # If translations are missing, fall back to English
        fallback_headers = ["Name", "ID", "Score", "Total", "Percentage", "Grade"]
        return [h.strip() if h.strip() else fallback_headers[i] for i, h in enumerate(headers)]
